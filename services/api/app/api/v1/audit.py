from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_membership
from app.db.session import get_db
from app.models.asset import Asset
from app.models.audit import AuditEvent
from app.models.organization import OrganizationMembership
from app.schemas.audit import AuditEventOut

router = APIRouter()


@router.get("/assets/{asset_id}/audit", response_model=list[AuditEventOut])
def list_audit(
    asset_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> list[AuditEventOut]:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail="asset not found")
    rows = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.organization_id == membership.organization_id,
            AuditEvent.entity_id == str(asset_id),
        )
        .order_by(AuditEvent.created_at.desc())
        .limit(200)
        .all()
    )
    return [AuditEventOut.model_validate(r) for r in rows]
