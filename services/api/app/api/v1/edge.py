from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import (
    get_current_edge_node,
    get_current_membership,
    get_current_user,
)
from app.core.security import create_edge_token, new_enrollment_token
from app.db.session import get_db
from app.models.asset import Asset
from app.models.edge import (
    EdgeEnrollmentToken,
    EdgeNode,
    EdgeUploadEvent,
    EnrollmentStatus,
)
from app.models.evidence import (
    EvidenceItem,
    EvidenceType,
    IngestionStatus,
    Visibility,
)
from app.models.organization import OrganizationMembership, OrgRole
from app.models.user import User
from app.schemas.edge import (
    EdgeEnrollmentTokenCreate,
    EdgeEnrollmentTokenOut,
    EdgeEnrollRequest,
    EdgeEnrollResponse,
    EdgeHeartbeatRequest,
    EdgeNodeOut,
)
from app.services.audit import record as audit_record
from app.services.hashing import sha256_bytes
from app.services.manifest import regenerate_manifest
from app.services.storage import evidence_key, get_object_store

router = APIRouter()


def _hash_token(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


# ── ORG_ADMIN side: create enrollment tokens, list nodes ───────────────────
@router.get("/edge/nodes", response_model=list[EdgeNodeOut])
def list_nodes(
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> list[EdgeNodeOut]:
    rows = (
        db.query(EdgeNode)
        .filter(EdgeNode.organization_id == membership.organization_id)
        .order_by(EdgeNode.created_at.desc())
        .all()
    )
    return [EdgeNodeOut.model_validate(r) for r in rows]


@router.post("/edge/enrollment-tokens", response_model=EdgeEnrollmentTokenOut)
def create_token(
    body: EdgeEnrollmentTokenCreate,
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EdgeEnrollmentTokenOut:
    if membership.role not in {OrgRole.ORG_ADMIN, OrgRole.PLATFORM_ADMIN}:
        raise HTTPException(status_code=403, detail="org admin required")

    ttl = body.ttl_minutes or settings.edge_token_ttl_minutes
    plaintext = new_enrollment_token()
    record_id = uuid.uuid4()
    expires = datetime.now(tz=timezone.utc) + timedelta(minutes=ttl)
    record = EdgeEnrollmentToken(
        id=record_id,
        organization_id=membership.organization_id,
        token_hash=_hash_token(plaintext),
        node_name_hint=body.node_name_hint,
        expires_at=expires,
        consumed_at=None,
        created_by=user.id,
    )
    db.add(record)
    audit_record(
        db,
        organization_id=membership.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="edge.enrollment_token.create",
        entity_type="EdgeEnrollmentToken",
        entity_id=str(record_id),
    )
    db.commit()
    return EdgeEnrollmentTokenOut(
        id=record_id,
        token=plaintext,
        node_name_hint=body.node_name_hint,
        expires_at=expires,
    )


# ── Edge-device side: exchange token for an edge_token + node identity ────
@router.post("/edge/enroll", response_model=EdgeEnrollResponse)
def enroll(body: EdgeEnrollRequest, db: Session = Depends(get_db)) -> EdgeEnrollResponse:
    token_record = (
        db.query(EdgeEnrollmentToken)
        .filter(EdgeEnrollmentToken.token_hash == _hash_token(body.token))
        .first()
    )
    if token_record is None or token_record.consumed_at is not None:
        raise HTTPException(status_code=401, detail="invalid or consumed enrollment token")
    if token_record.expires_at < datetime.now(tz=timezone.utc):
        raise HTTPException(status_code=401, detail="enrollment token expired")

    slug = body.node_name.lower().replace(" ", "-")
    node = EdgeNode(
        id=uuid.uuid4(),
        organization_id=token_record.organization_id,
        node_name=body.node_name,
        node_slug=slug,
        enrollment_status=EnrollmentStatus.ENROLLED,
        software_version=body.software_version,
        hardware_summary_json=body.hardware_summary,
        public_key_or_device_fingerprint=body.public_key_or_device_fingerprint,
    )
    db.add(node)
    token_record.consumed_at = datetime.now(tz=timezone.utc)
    token_record.consumed_by_node_id = node.id
    db.flush()

    edge_token = create_edge_token(str(node.id))
    audit_record(
        db,
        organization_id=token_record.organization_id,
        actor_type="EDGE_NODE",
        actor_id=str(node.id),
        action="edge.enroll",
        entity_type="EdgeNode",
        entity_id=str(node.id),
    )
    db.commit()
    return EdgeEnrollResponse(node_id=node.id, edge_token=edge_token, ens_name=None)


@router.post("/edge/heartbeat")
def heartbeat(
    body: EdgeHeartbeatRequest,
    node: EdgeNode = Depends(get_current_edge_node),
    db: Session = Depends(get_db),
) -> dict:
    node.last_heartbeat_at = datetime.now(tz=timezone.utc)
    if body.software_version:
        node.software_version = body.software_version
    if body.hardware_summary:
        node.hardware_summary_json = body.hardware_summary
    if node.enrollment_status == EnrollmentStatus.STALE:
        node.enrollment_status = EnrollmentStatus.ENROLLED
    db.commit()
    return {"ok": True, "node_id": str(node.id), "received_at": node.last_heartbeat_at.isoformat()}


@router.post("/edge/assets/{asset_id}/evidence")
async def edge_upload_evidence(
    asset_id: uuid.UUID,
    file: UploadFile = File(...),
    evidence_type: str = Form("BENCHMARK_OUTPUT"),
    claimed_sha256: str = Form(""),
    node: EdgeNode = Depends(get_current_edge_node),
    db: Session = Depends(get_db),
) -> dict:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.organization_id != node.organization_id:
        raise HTTPException(status_code=404, detail="asset not found for this edge node")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="empty file")

    server_hash = sha256_bytes(raw)
    hash_match: bool | None = None
    if claimed_sha256:
        hash_match = claimed_sha256.lower().strip() == server_hash
        if not hash_match:
            # Record the mismatch but reject the upload to keep the manifest honest.
            db.add(
                EdgeUploadEvent(
                    id=uuid.uuid4(),
                    edge_node_id=node.id,
                    asset_id=asset.id,
                    event_type="EVIDENCE_UPLOAD_HASH_MISMATCH",
                    claimed_hash=claimed_sha256,
                    verified_hash=server_hash,
                    hash_match=False,
                    sync_status="REJECTED",
                )
            )
            db.commit()
            raise HTTPException(status_code=400, detail="hash mismatch · upload rejected")

    try:
        ev_type = EvidenceType(evidence_type)
    except ValueError:
        ev_type = EvidenceType.OTHER

    evidence_id = uuid.uuid4()
    storage_key = evidence_key(asset.organization_id, asset.id, evidence_id, file.filename or "edge.bin")
    store = get_object_store()
    store.put_private(key=storage_key, body=raw, content_type=file.content_type)

    evidence = EvidenceItem(
        id=evidence_id,
        organization_id=asset.organization_id,
        asset_id=asset.id,
        filename=file.filename or "edge.bin",
        storage_key=storage_key,
        content_type=file.content_type,
        byte_size=len(raw),
        evidence_type=ev_type,
        visibility=Visibility.PRIVATE,
        ingestion_status=IngestionStatus.INDEXED,
        sha256_hash=server_hash,
        provenance="EDGE_CAPTURED",
        edge_node_id=node.id,
    )
    db.add(evidence)
    db.add(
        EdgeUploadEvent(
            id=uuid.uuid4(),
            edge_node_id=node.id,
            asset_id=asset.id,
            evidence_item_id=evidence.id,
            event_type="EVIDENCE_UPLOAD",
            claimed_hash=claimed_sha256 or None,
            verified_hash=server_hash,
            hash_match=hash_match,
            sync_status="ACCEPTED",
        )
    )
    regenerate_manifest(db, asset)
    audit_record(
        db,
        organization_id=asset.organization_id,
        actor_type="EDGE_NODE",
        actor_id=str(node.id),
        action="evidence.upload.edge",
        entity_type="EvidenceItem",
        entity_id=str(evidence.id),
        metadata={"sha256": server_hash, "hash_match": hash_match},
    )
    db.commit()
    return {
        "ok": True,
        "evidence_item_id": str(evidence.id),
        "sha256": server_hash,
        "hash_match": hash_match,
    }


@router.post("/edge/assets/{asset_id}/benchmark-receipts")
async def edge_upload_benchmark(
    asset_id: uuid.UUID,
    file: UploadFile = File(...),
    claimed_sha256: str = Form(""),
    node: EdgeNode = Depends(get_current_edge_node),
    db: Session = Depends(get_db),
) -> dict:
    # Convenience alias · benchmark JSON is just evidence with type BENCHMARK_OUTPUT.
    return await edge_upload_evidence(
        asset_id=asset_id,
        file=file,
        evidence_type=EvidenceType.BENCHMARK_OUTPUT.value,
        claimed_sha256=claimed_sha256,
        node=node,
        db=db,
    )
