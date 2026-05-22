from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_membership, get_current_user
from app.db.session import get_db
from app.integrations.model_gateway import get_model_gateway
from app.models.ai import AIOutput, AIOutputStatus, AIOVAnalysis, WorkflowType
from app.models.asset import Asset
from app.models.evidence import EvidenceItem
from app.models.organization import OrganizationMembership
from app.models.research import ResearchSession, ResearchSource
from app.models.user import User
from app.models.validator import ValidatorReview, ValidatorStatus
from app.schemas.validator import ValidatorReviewOut
from app.services.audit import record as audit_record
from app.services.hashing import sha256_json
from app.services.tool_contracts import VALIDATOR_FLAG_TOOL
from app.services.validator_checks import (
    CHECKS,
    CheckResult,
    build_receipt,
    run_deterministic_checks,
    summarise,
)

router = APIRouter()


def _require_asset(db: Session, asset_id: uuid.UUID, org_id: uuid.UUID) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.organization_id != org_id:
        raise HTTPException(status_code=404, detail="asset not found")
    return asset


@router.post("/assets/{asset_id}/validator/run", response_model=ValidatorReviewOut)
def run_validator(
    asset_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ValidatorReviewOut:
    asset = _require_asset(db, asset_id, membership.organization_id)

    aiov = (
        db.query(AIOVAnalysis)
        .filter(AIOVAnalysis.asset_id == asset.id)
        .order_by(AIOVAnalysis.version.desc())
        .first()
    )

    results = run_deterministic_checks(db, asset, aiov)

    # ── Optional model-assist · only runs when the gateway is configured ──
    # The model can flag findings the deterministic rules miss (e.g. a
    # manufacturer-spec source that contradicts the supplied benchmark). All
    # findings come back through a typed tool call · severity is enum-bound,
    # check IDs must match the canonical list, so the model cannot invent
    # categories.
    gateway = get_model_gateway()
    if gateway.provider.is_configured() and aiov is not None:
        evidence_items = (
            db.query(EvidenceItem).filter(EvidenceItem.asset_id == asset.id).all()
        )
        sources = (
            db.query(ResearchSource)
            .join(ResearchSession, ResearchSource.research_session_id == ResearchSession.id)
            .filter(ResearchSession.asset_id == asset.id)
            .all()
        )
        prompt_payload = {
            "asset_reference": asset.public_asset_reference,
            "aiov_status": aiov.status.value,
            "aiov_missing_evidence": (aiov.missing_evidence_json or {}).get(
                "missing_evidence_types", []
            ),
            "aiov_narrative_excerpt": (aiov.narrative or "")[:2000],
            "deterministic_results": [
                {
                    "check": r.check,
                    "status": r.status,
                    "severity": r.severity,
                    "finding": r.finding,
                }
                for r in results
            ],
            "evidence_items": [
                {
                    "id": str(e.id),
                    "type": e.evidence_type.value,
                    "filename": e.filename,
                    "sha256": e.sha256_hash,
                    "provenance": e.provenance,
                }
                for e in evidence_items
            ],
            "research_sources": [
                {
                    "id": str(s.id),
                    "title": s.title,
                    "url": s.source_url,
                    "domain": s.publisher_domain,
                    "classification": s.evidence_classification.value,
                    "retrieved_at": s.retrieved_at.isoformat() if s.retrieved_at else None,
                    "excerpt": (s.content_excerpt or "")[:600],
                }
                for s in sources
            ],
        }
        gw_result = gateway.generate_structured(
            workflow_type=WorkflowType.VALIDATOR_ASSIST,
            prompt_version="validator_compute_v1",
            input_reference={
                "asset_id": str(asset.id),
                "aiov_id": str(aiov.id) if aiov else None,
            },
            prompt_payload=prompt_payload,
            tools=[VALIDATOR_FLAG_TOOL],
        )
        # Persist the AI output (success or failure) for audit / receipt traceability.
        ai_out = AIOutput(
            id=uuid.uuid4(),
            organization_id=asset.organization_id,
            asset_id=asset.id,
            workflow_type=WorkflowType.VALIDATOR_ASSIST,
            model_provider=gw_result.provider,
            model_name=gw_result.model,
            prompt_version="validator_compute_v1",
            input_reference_json={
                "asset_id": str(asset.id),
                "aiov_id": str(aiov.id),
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
                if gw_result.status == "FAILED"
                else AIOutputStatus.NOT_CONFIGURED
            ),
            error_message=gw_result.error,
        )
        db.add(ai_out)

        # Translate each tool call into a CheckResult appended to the receipt.
        for tc in gw_result.tool_calls:
            if tc.name != "flag_finding":
                continue
            args = tc.arguments or {}
            check = args.get("check")
            severity = args.get("severity")
            finding = args.get("finding") or ""
            evidence_refs = args.get("evidence_refs") or []
            # Enforce server-side · refuse out-of-band check or severity.
            if check not in CHECKS:
                continue
            if severity not in {"INFO", "LOW", "MEDIUM", "HIGH", "BLOCKING"}:
                continue
            results.append(
                CheckResult(
                    check=check,
                    status="PASS_WITH_FLAG" if severity in {"INFO", "LOW", "MEDIUM"} else "FAIL",
                    severity=severity,
                    finding=f"[model-assist · {gw_result.provider}] {finding}",
                    evidence_reference=evidence_refs,
                )
            )

    status_value = summarise(results)
    receipt = build_receipt(asset, aiov.version if aiov else None, results, status_value)

    latest = (
        db.query(ValidatorReview)
        .filter(ValidatorReview.asset_id == asset.id)
        .order_by(ValidatorReview.version.desc())
        .first()
    )
    version = (latest.version + 1) if latest else 1

    review = ValidatorReview(
        id=uuid.uuid4(),
        asset_id=asset.id,
        aiov_analysis_id=aiov.id if aiov else None,
        version=version,
        status=ValidatorStatus(status_value),
        protocol="VALIDATE_THE_VALIDATOR",
        findings_json=receipt.get("blocking_findings", []),
        checks_json=receipt["checks"],
        receipt_sha256=receipt["receipt_sha256"],
        reviewed_by=user.id,
    )
    db.add(review)
    audit_record(
        db,
        organization_id=asset.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="validator.run",
        entity_type="ValidatorReview",
        entity_id=str(review.id),
        metadata={
            "asset_id": str(asset.id),
            "status": status_value,
            "receipt_sha256": receipt["receipt_sha256"],
        },
    )
    db.commit()
    db.refresh(review)
    return ValidatorReviewOut.model_validate(review)


@router.get("/assets/{asset_id}/validator/latest", response_model=ValidatorReviewOut | None)
def latest_validator(
    asset_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> ValidatorReviewOut | None:
    _require_asset(db, asset_id, membership.organization_id)
    review = (
        db.query(ValidatorReview)
        .filter(ValidatorReview.asset_id == asset_id)
        .order_by(ValidatorReview.version.desc())
        .first()
    )
    return ValidatorReviewOut.model_validate(review) if review else None
