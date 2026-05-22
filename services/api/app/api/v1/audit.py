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
    # Include events directly on the asset PLUS events on child entities
    # (evidence, manifests, AIOV, validator, deed) that were tagged with this
    # asset_id in metadata. The metadata-tagging happens at audit_record() sites
    # for downstream queries; for now we accept "entity is the asset OR
    # metadata.asset_id matches" so old + new events both surface.
    from sqlalchemy import or_

    rows = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.organization_id == membership.organization_id,
            or_(
                AuditEvent.entity_id == str(asset_id),
                AuditEvent.extra_metadata["asset_id"].astext == str(asset_id),
            ),
        )
        .order_by(AuditEvent.created_at.desc())
        .limit(200)
        .all()
    )
    return [AuditEventOut.model_validate(r) for r in rows]
