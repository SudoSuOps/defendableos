from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_membership, get_current_user
from app.db.session import get_db
from app.models.asset import Asset
from app.models.deed import DeedStatus, DefendableDeed
from app.models.organization import OrganizationMembership
from app.models.user import User
from app.schemas.deed import DeedOut, PublishDeedRequest
from app.services.audit import record as audit_record
from app.services.deed import (
    DeedPrerequisiteError,
    create_deed,
    filter_public_payload,
    publish_public,
)
from app.services.storage import get_object_store, public_verify_key

router = APIRouter()


def _require_asset(db: Session, asset_id: uuid.UUID, org_id: uuid.UUID) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.organization_id != org_id:
        raise HTTPException(status_code=404, detail="asset not found")
    return asset


@router.post("/assets/{asset_id}/deeds", response_model=DeedOut)
def create(
    asset_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeedOut:
    asset = _require_asset(db, asset_id, membership.organization_id)
    try:
        deed = create_deed(db, asset, issued_by_user_id=user.id)
    except DeedPrerequisiteError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    audit_record(
        db,
        organization_id=asset.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="deed.create",
        entity_type="DefendableDeed",
        entity_id=str(deed.id),
        metadata={
            "asset_id": str(asset.id),
            "version": deed.version,
            "record_hash": deed.record_hash,
        },
    )
    db.commit()
    db.refresh(deed)
    return DeedOut.model_validate(deed)


@router.get("/assets/{asset_id}/deeds", response_model=list[DeedOut])
def list_deeds(
    asset_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> list[DeedOut]:
    _require_asset(db, asset_id, membership.organization_id)
    rows = (
        db.query(DefendableDeed)
        .filter(DefendableDeed.asset_id == asset_id)
        .order_by(DefendableDeed.version.desc())
        .all()
    )
    return [DeedOut.model_validate(r) for r in rows]


@router.get("/deeds/{deed_id}", response_model=DeedOut)
def get_deed(
    deed_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> DeedOut:
    deed = db.get(DefendableDeed, deed_id)
    if deed is None or deed.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail="deed not found")
    return DeedOut.model_validate(deed)


@router.post("/deeds/{deed_id}/publish", response_model=DeedOut)
def publish(
    deed_id: uuid.UUID,
    _body: PublishDeedRequest | None = None,
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeedOut:
    # Publication is gated to ORG_ADMIN or PLATFORM_ADMIN.
    if membership.role.value not in {"ORG_ADMIN", "PLATFORM_ADMIN"} and not user.is_platform_admin:
        raise HTTPException(status_code=403, detail="publication requires org admin")

    deed = db.get(DefendableDeed, deed_id)
    if deed is None or deed.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail="deed not found")
    if deed.status == DeedStatus.SUPERSEDED:
        raise HTTPException(status_code=409, detail="cannot publish a superseded deed")

    slug = publish_public(deed)
    public_payload = filter_public_payload(deed.deed_json)
    try:
        store = get_object_store()
        store.put_public_json(
            key=public_verify_key(slug),
            payload=public_payload,
        )
    except Exception:
        # Object-storage write is best-effort · DB row is source of truth.
        pass

    audit_record(
        db,
        organization_id=deed.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="deed.publish",
        entity_type="DefendableDeed",
        entity_id=str(deed.id),
        metadata={"asset_id": str(deed.asset_id), "public_slug": slug},
    )
    db.commit()
    db.refresh(deed)
    return DeedOut.model_validate(deed)
