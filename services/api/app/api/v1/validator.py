from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_membership, get_current_user
from app.db.session import get_db
from app.models.ai import AIOVAnalysis
from app.models.asset import Asset
from app.models.organization import OrganizationMembership
from app.models.user import User
from app.models.validator import ValidatorReview, ValidatorStatus
from app.schemas.validator import ValidatorReviewOut
from app.services.audit import record as audit_record
from app.services.validator_checks import (
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
        metadata={"status": status_value, "receipt_sha256": receipt["receipt_sha256"]},
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
