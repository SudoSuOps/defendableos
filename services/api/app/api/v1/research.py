from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_membership, get_current_user
from app.db.session import get_db
from app.integrations import brave_llm_context
from app.integrations.model_gateway import get_model_gateway
from app.models.ai import AIOutput, AIOutputStatus, WorkflowType
from app.models.asset import Asset
from app.models.organization import OrganizationMembership
from app.models.research import (
    EvidenceClassification,
    ResearchSession,
    ResearchSource,
    ResearchStatus,
    SourceLane,
)
from app.models.user import User
from app.schemas.research import (
    PrivateResearchRequest,
    PublicResearchRequest,
    ResearchSessionOut,
    ResearchSourceOut,
)
from app.services.audit import record as audit_record
from app.services.extraction import private_search
from app.services.hashing import sha256_bytes, sha256_json
from app.services.tool_contracts import RESEARCH_CLASSIFY_TOOL

router = APIRouter()


def _require_asset(db: Session, asset_id: uuid.UUID, org_id: uuid.UUID) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.organization_id != org_id:
        raise HTTPException(status_code=404, detail="asset not found")
    return asset


@router.post("/assets/{asset_id}/research/private", response_model=ResearchSessionOut)
def search_private(
    asset_id: uuid.UUID,
    body: PrivateResearchRequest,
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResearchSessionOut:
    asset = _require_asset(db, asset_id, membership.organization_id)
    session = ResearchSession(
        id=uuid.uuid4(),
        organization_id=asset.organization_id,
        asset_id=asset.id,
        initiated_by=user.id,
        query=body.query,
        source_lane=SourceLane.PRIVATE_EVIDENCE,
        provider="defendableos_private_search",
        status=ResearchStatus.COMPLETED,
    )
    db.add(session)

    matches = private_search(db, asset.organization_id, asset.id, body.query)
    for m in matches:
        excerpt = m["excerpt"]
        src = ResearchSource(
            id=uuid.uuid4(),
            research_session_id=session.id,
            source_type="PRIVATE_EVIDENCE",
            title=m["filename"],
            source_url=None,
            publisher_domain=None,
            retrieved_at=None,
            evidence_classification=EvidenceClassification.UNKNOWN,
            content_excerpt=excerpt,
            source_hash=m.get("sha256"),
            validator_status=None,
            extra_metadata={
                "evidence_item_id": m["evidence_item_id"],
                "locator": m["locator"],
                "evidence_type": m["evidence_type"],
            },
        )
        db.add(src)

    audit_record(
        db,
        organization_id=asset.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="research.private",
        entity_type="ResearchSession",
        entity_id=str(session.id),
        metadata={"asset_id": str(asset.id)},
    )
    db.commit()
    db.refresh(session)
    return ResearchSessionOut(
        id=session.id,
        query=session.query,
        source_lane=session.source_lane.value,
        provider=session.provider,
        model_used=session.model_used,
        status=session.status.value,
        created_at=session.created_at,
        sources=[ResearchSourceOut.model_validate(s) for s in session.sources],
    )


@router.post("/assets/{asset_id}/research/public", response_model=ResearchSessionOut)
def search_public(
    asset_id: uuid.UUID,
    body: PublicResearchRequest,
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResearchSessionOut:
    asset = _require_asset(db, asset_id, membership.organization_id)

    result = brave_llm_context.search(
        query=body.query,
        maximum_number_of_urls=body.maximum_number_of_urls,
        maximum_number_of_tokens=body.maximum_number_of_tokens,
        context_threshold_mode=body.context_threshold_mode,
    )

    status_map = {
        "COMPLETED": ResearchStatus.COMPLETED,
        "NOT_CONFIGURED": ResearchStatus.FAILED,
        "FAILED": ResearchStatus.FAILED,
    }
    session = ResearchSession(
        id=uuid.uuid4(),
        organization_id=asset.organization_id,
        asset_id=asset.id,
        initiated_by=user.id,
        query=body.query,
        source_lane=SourceLane.PUBLIC_WEB,
        provider=result.provider,
        status=status_map.get(result.status, ResearchStatus.FAILED),
    )
    db.add(session)

    # First create the source rows · classifications start UNKNOWN.
    db_sources: list[ResearchSource] = []
    for s in result.sources:
        excerpt = (s.excerpt or "")[:4000]
        source_hash = sha256_bytes((s.url or "" + "|" + (s.title or "")).encode("utf-8"))
        row = ResearchSource(
            id=uuid.uuid4(),
            research_session_id=session.id,
            source_type="PUBLIC_WEB",
            title=s.title,
            source_url=s.url,
            publisher_domain=s.domain,
            retrieved_at=s.retrieved_at,
            evidence_classification=EvidenceClassification.UNKNOWN,
            content_excerpt=excerpt,
            source_hash=source_hash,
            validator_status="UNREVIEWED",
        )
        db.add(row)
        db_sources.append(row)
    db.flush()

    # Model-assisted classification · enums in the tool schema make it
    # impossible to relabel a listing as a confirmed sale, etc. Skipped
    # cleanly when no provider is configured · UNKNOWN sources just stay
    # UNKNOWN and the validator flags them.
    gateway = get_model_gateway()
    if db_sources and gateway.provider.is_configured():
        prompt_payload = {
            "asset_reference": asset.public_asset_reference,
            "asset_name": asset.name,
            "asset_class": asset.asset_class.value,
            "sources_to_classify": [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "url": row.source_url,
                    "domain": row.publisher_domain,
                    "excerpt": (row.content_excerpt or "")[:800],
                }
                for row in db_sources
            ],
        }
        gw_result = gateway.generate_structured(
            workflow_type=WorkflowType.RESEARCH_SYNTHESIS,
            prompt_version="research_synthesis_v1",
            input_reference={
                "asset_id": str(asset.id),
                "session_id": str(session.id),
            },
            prompt_payload=prompt_payload,
            tools=[RESEARCH_CLASSIFY_TOOL],
        )
        db.add(
            AIOutput(
                id=uuid.uuid4(),
                organization_id=asset.organization_id,
                asset_id=asset.id,
                workflow_type=WorkflowType.RESEARCH_SYNTHESIS,
                model_provider=gw_result.provider,
                model_name=gw_result.model,
                prompt_version="research_synthesis_v1",
                input_reference_json={
                    "asset_id": str(asset.id),
                    "session_id": str(session.id),
                },
                output_text=gw_result.output_text,
                output_json={
                    "tool_calls": [
                        {"name": tc.name, "arguments": tc.arguments}
                        for tc in gw_result.tool_calls
                    ]
                },
                output_sha256=sha256_json(
                    {
                        "tool_calls": [
                            {"name": tc.name, "arguments": tc.arguments}
                            for tc in gw_result.tool_calls
                        ]
                    }
                ),
                status=(
                    AIOutputStatus.GENERATED
                    if gw_result.status == "GENERATED"
                    else AIOutputStatus.FAILED
                ),
                error_message=gw_result.error,
            )
        )

        # Apply classifications · only typed enum values land.
        by_id: dict[str, ResearchSource] = {str(r.id): r for r in db_sources}
        for tc in gw_result.tool_calls:
            if tc.name != "classify_source":
                continue
            args = tc.arguments or {}
            sid = args.get("source_id")
            classification = args.get("classification")
            rationale = args.get("rationale")
            if not sid or sid not in by_id:
                continue
            try:
                cls_enum = EvidenceClassification(classification)
            except ValueError:
                continue
            # Server-side doctrine guard · NEVER let model relabel listing→sale.
            if cls_enum == EvidenceClassification.CONFIRMED_SALE_PRICE:
                # Refuse the call unless rationale explicitly cites a confirmed
                # sale signal · until a stronger evidence link exists, downgrade.
                text = (rationale or "").lower()
                if "confirmed sale" not in text and "completed sale" not in text and "sold for" not in text:
                    cls_enum = EvidenceClassification.MARKET_COMMENTARY
            row = by_id[sid]
            row.evidence_classification = cls_enum
            row.validator_status = "MODEL_CLASSIFIED"

    audit_record(
        db,
        organization_id=asset.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="research.public",
        entity_type="ResearchSession",
        entity_id=str(session.id),
        metadata={
            "asset_id": str(asset.id),
            "status": result.status,
            "provider": result.provider,
        },
    )
    db.commit()
    db.refresh(session)
    return ResearchSessionOut(
        id=session.id,
        query=session.query,
        source_lane=session.source_lane.value,
        provider=session.provider,
        model_used=session.model_used,
        status=session.status.value,
        created_at=session.created_at,
        sources=[ResearchSourceOut.model_validate(s) for s in session.sources],
    )


@router.get("/assets/{asset_id}/research/sessions", response_model=list[ResearchSessionOut])
def list_sessions(
    asset_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> list[ResearchSessionOut]:
    asset = _require_asset(db, asset_id, membership.organization_id)
    sessions = (
        db.query(ResearchSession)
        .filter(ResearchSession.asset_id == asset.id)
        .order_by(ResearchSession.created_at.desc())
        .all()
    )
    return [
        ResearchSessionOut(
            id=s.id,
            query=s.query,
            source_lane=s.source_lane.value,
            provider=s.provider,
            model_used=s.model_used,
            status=s.status.value,
            created_at=s.created_at,
            sources=[ResearchSourceOut.model_validate(x) for x in s.sources],
        )
        for s in sessions
    ]


@router.get("/research/sessions/{research_session_id}", response_model=ResearchSessionOut)
def get_session(
    research_session_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> ResearchSessionOut:
    s = db.get(ResearchSession, research_session_id)
    if s is None or s.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail="session not found")
    return ResearchSessionOut(
        id=s.id,
        query=s.query,
        source_lane=s.source_lane.value,
        provider=s.provider,
        model_used=s.model_used,
        status=s.status.value,
        created_at=s.created_at,
        sources=[ResearchSourceOut.model_validate(x) for x in s.sources],
    )
