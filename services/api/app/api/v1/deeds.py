from __future__ import annotations

import uuid

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
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
from app.services.ledger_publisher import get_ledger_publisher
from app.services.storage import get_object_store, public_verify_key

logger = logging.getLogger(__name__)

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
    background_tasks: BackgroundTasks,
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

    # DefendableLedger public publisher · single canonical surface at
    # defendableledger.com. Runs as a background task so the publish endpoint
    # returns immediately. Best-effort · the DB row is the source of truth ·
    # publish failures don't block the response.
    publisher = get_ledger_publisher()
    if publisher.is_configured():
        background_tasks.add_task(
            _publish_to_defendable_ledger,
            slug=slug,
            deed_reference=deed.deed_reference,
            deed_json=deed.deed_json,
            public_payload=public_payload,
            record_hash=deed.record_hash,
            deed_version=deed.version,
        )

    audit_record(
        db,
        organization_id=deed.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="deed.publish",
        entity_type="DefendableDeed",
        entity_id=str(deed.id),
        metadata={
            "asset_id": str(deed.asset_id),
            "public_slug": slug,
            "defendable_ledger_queued": publisher.is_configured(),
        },
    )
    db.commit()
    db.refresh(deed)
    return DeedOut.model_validate(deed)


def _publish_to_defendable_ledger(
    *,
    slug: str,
    deed_reference: str,
    deed_json: dict,
    public_payload: dict,
    record_hash: str | None,
    deed_version: int,
) -> None:
    """Background task wrapper · isolates exceptions so they never bubble up to
    request handling. Logs but never raises."""
    publisher = get_ledger_publisher()
    try:
        result = publisher.publish_deed(
            slug=slug,
            deed_reference=deed_reference,
            deed_json=deed_json,
            public_payload=public_payload,
            record_hash=record_hash,
            deed_version=deed_version,
        )
        if result.ok:
            logger.info(
                "defendable-ledger publish ok · slug=%s · public_url=%s · commit=%s",
                slug,
                result.public_url,
                result.commit_sha,
            )
        else:
            logger.warning(
                "defendable-ledger publish failed · slug=%s · error=%s",
                slug,
                result.error,
            )
    except Exception:  # noqa: BLE001
        logger.exception("defendable-ledger publish · unexpected exception · slug=%s", slug)
