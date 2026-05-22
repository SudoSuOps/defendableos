from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_membership, get_current_user
from app.db.session import get_db
from app.models.asset import Asset
from app.models.evidence import (
    EvidenceItem,
    EvidenceType,
    IngestionStatus,
    Visibility,
)
from app.models.organization import OrganizationMembership
from app.models.user import User
from app.schemas.evidence import EvidenceItemOut, EvidenceManifestOut
from app.services.audit import record as audit_record
from app.services.extraction import extract_evidence
from app.services.hashing import sha256_bytes
from app.services.manifest import get_current_manifest, regenerate_manifest
from app.services.storage import evidence_key, get_object_store

router = APIRouter()


_MAX_BYTES = 50 * 1024 * 1024  # 50 MB default upload ceiling
_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/json",
    "text/plain",
    "text/csv",
    "application/csv",
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/octet-stream",
}


def _require_asset(db: Session, asset_id: uuid.UUID, org_id: uuid.UUID) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.organization_id != org_id:
        raise HTTPException(status_code=404, detail="asset not found")
    return asset


@router.get("/assets/{asset_id}/evidence", response_model=list[EvidenceItemOut])
def list_evidence(
    asset_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> list[EvidenceItemOut]:
    _require_asset(db, asset_id, membership.organization_id)
    rows = (
        db.query(EvidenceItem)
        .filter(EvidenceItem.asset_id == asset_id)
        .order_by(EvidenceItem.created_at.desc())
        .all()
    )
    return [EvidenceItemOut.model_validate(r) for r in rows]


@router.post(
    "/assets/{asset_id}/evidence/upload",
    response_model=EvidenceItemOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence(
    asset_id: uuid.UUID,
    file: UploadFile = File(...),
    evidence_type: str = Form("OTHER"),
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvidenceItemOut:
    asset = _require_asset(db, asset_id, membership.organization_id)

    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="empty file")
    if len(raw) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="file too large")
    content_type = (file.content_type or "application/octet-stream").lower()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail=f"unsupported content type {content_type!r}")

    try:
        ev_type = EvidenceType(evidence_type)
    except ValueError:
        ev_type = EvidenceType.OTHER

    new_id = uuid.uuid4()
    storage_key = evidence_key(asset.organization_id, asset.id, new_id, file.filename or "evidence.bin")
    digest = sha256_bytes(raw)

    store = get_object_store()
    store.put_private(key=storage_key, body=raw, content_type=content_type)

    evidence = EvidenceItem(
        id=new_id,
        organization_id=asset.organization_id,
        asset_id=asset.id,
        filename=file.filename or "evidence.bin",
        storage_key=storage_key,
        content_type=content_type,
        byte_size=len(raw),
        evidence_type=ev_type,
        visibility=Visibility.PRIVATE,
        ingestion_status=IngestionStatus.UPLOADED,
        sha256_hash=digest,
        uploaded_by=user.id,
        provenance="USER_UPLOAD",
    )
    db.add(evidence)
    db.flush()

    # Synchronous text extraction for the MVP · keeps the flow demo-friendly.
    try:
        extract_evidence(db, evidence, raw)
    except Exception:
        # Extraction failure should not block the upload itself.
        evidence.ingestion_status = IngestionStatus.EXTRACTION_FAILED

    regenerate_manifest(db, asset)
    audit_record(
        db,
        organization_id=asset.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="evidence.upload",
        entity_type="EvidenceItem",
        entity_id=str(evidence.id),
        metadata={"sha256": digest, "evidence_type": ev_type.value},
    )
    db.commit()
    db.refresh(evidence)
    return EvidenceItemOut.model_validate(evidence)


@router.get("/assets/{asset_id}/manifest", response_model=EvidenceManifestOut | None)
def current_manifest(
    asset_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> EvidenceManifestOut | None:
    asset = _require_asset(db, asset_id, membership.organization_id)
    manifest = get_current_manifest(db, asset.id)
    if manifest is None:
        return None
    return EvidenceManifestOut(
        id=manifest.id,
        version=manifest.version,
        manifest_sha256=manifest.manifest_sha256,
        status=manifest.status.value,
        item_count=len(manifest.manifest_json.get("items", [])),
        created_at=manifest.created_at,
    )


@router.post("/assets/{asset_id}/manifest/regenerate", response_model=EvidenceManifestOut)
def regenerate(
    asset_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvidenceManifestOut:
    asset = _require_asset(db, asset_id, membership.organization_id)
    manifest = regenerate_manifest(db, asset)
    audit_record(
        db,
        organization_id=asset.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="evidence.manifest.regenerate",
        entity_type="EvidenceManifest",
        entity_id=str(manifest.id),
        metadata={"manifest_sha256": manifest.manifest_sha256},
    )
    db.commit()
    return EvidenceManifestOut(
        id=manifest.id,
        version=manifest.version,
        manifest_sha256=manifest.manifest_sha256,
        status=manifest.status.value,
        item_count=len(manifest.manifest_json.get("items", [])),
        created_at=manifest.created_at,
    )
