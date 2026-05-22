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
from app.schemas.aiov import AIOVAnalysisOut, AIOVGenerateRequest
from app.services.aiov import generate_aiov
from app.services.audit import record as audit_record

router = APIRouter()


def _require_asset(db: Session, asset_id: uuid.UUID, org_id: uuid.UUID) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.organization_id != org_id:
        raise HTTPException(status_code=404, detail="asset not found")
    return asset


@router.post("/assets/{asset_id}/aiov/generate", response_model=AIOVAnalysisOut)
def generate(
    asset_id: uuid.UUID,
    body: AIOVGenerateRequest,
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIOVAnalysisOut:
    asset = _require_asset(db, asset_id, membership.organization_id)
    analysis = generate_aiov(
        db,
        asset,
        included_evidence_item_ids=body.included_evidence_item_ids,
        included_research_source_ids=body.included_research_source_ids,
        notes=body.notes,
    )
    audit_record(
        db,
        organization_id=asset.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="aiov.generate",
        entity_type="AIOVAnalysis",
        entity_id=str(analysis.id),
        metadata={"version": analysis.version},
    )
    db.commit()
    db.refresh(analysis)
    return AIOVAnalysisOut.model_validate(analysis)


@router.get("/assets/{asset_id}/aiov", response_model=list[AIOVAnalysisOut])
def list_analyses(
    asset_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> list[AIOVAnalysisOut]:
    _require_asset(db, asset_id, membership.organization_id)
    rows = (
        db.query(AIOVAnalysis)
        .filter(AIOVAnalysis.asset_id == asset_id)
        .order_by(AIOVAnalysis.version.desc())
        .all()
    )
    return [AIOVAnalysisOut.model_validate(r) for r in rows]


@router.get("/assets/{asset_id}/aiov/{analysis_id}", response_model=AIOVAnalysisOut)
def get_analysis(
    asset_id: uuid.UUID,
    analysis_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> AIOVAnalysisOut:
    _require_asset(db, asset_id, membership.organization_id)
    analysis = db.get(AIOVAnalysis, analysis_id)
    if analysis is None or analysis.asset_id != asset_id:
        raise HTTPException(status_code=404, detail="analysis not found")
    return AIOVAnalysisOut.model_validate(analysis)
