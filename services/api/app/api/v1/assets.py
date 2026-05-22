from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_membership, get_current_user
from app.db.session import get_db
from app.models.asset import (
    Asset,
    AssetClass,
    AssetStatus,
    ComputeAssetProfile,
    ConditionStatus,
    IntendedUse,
)
from app.models.organization import OrganizationMembership
from app.models.user import User
from app.schemas.asset import (
    AssetCreateRequest,
    AssetOut,
    AssetSummary,
    ComputeProfileIn,
)
from app.services.audit import record as audit_record

router = APIRouter()


def _serialise(asset: Asset) -> AssetOut:
    profile_payload: ComputeProfileIn | None = None
    if asset.compute_profile is not None:
        p = asset.compute_profile
        profile_payload = ComputeProfileIn(
            manufacturer=p.manufacturer,
            model=p.model,
            gpu_count=p.gpu_count,
            vram_per_gpu_gb=p.vram_per_gpu_gb,
            cpu=p.cpu,
            ram_gb=p.ram_gb,
            storage_description=p.storage_description,
            networking_description=p.networking_description,
            operating_system=p.operating_system,
            condition_status=p.condition_status.value if p.condition_status else None,
            operational_status=p.operational_status,
            intended_use=p.intended_use.value if p.intended_use else None,
            purchase_date=p.purchase_date,
            purchase_cost_private=float(p.purchase_cost_private) if p.purchase_cost_private is not None else None,
        )
    return AssetOut(
        id=asset.id,
        public_asset_reference=asset.public_asset_reference,
        name=asset.name,
        asset_class=asset.asset_class.value,
        category=asset.category,
        status=asset.status.value,
        created_at=asset.created_at,
        organization_id=asset.organization_id,
        description=asset.description,
        compute_profile=profile_payload,
    )


def _next_compute_reference(db: Session, organization_id: uuid.UUID) -> str:
    existing = (
        db.query(Asset)
        .filter(Asset.organization_id == organization_id)
        .filter(Asset.asset_class == AssetClass.COMPUTE_HARDWARE)
        .count()
    )
    n = existing + 1
    return f"DOV-COMPUTE-{n:06d}"


@router.get("/assets", response_model=list[AssetSummary])
def list_assets(
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> list[AssetSummary]:
    rows = (
        db.query(Asset)
        .filter(Asset.organization_id == membership.organization_id)
        .order_by(Asset.created_at.desc())
        .all()
    )
    return [AssetSummary.model_validate(a) for a in rows]


@router.post("/assets", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset(
    body: AssetCreateRequest,
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssetOut:
    try:
        asset_class = AssetClass(body.asset_class)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"unsupported asset_class {body.asset_class!r}")

    public_ref = body.public_asset_reference or (
        _next_compute_reference(db, membership.organization_id)
        if asset_class == AssetClass.COMPUTE_HARDWARE
        else f"DOV-ASSET-{uuid.uuid4().hex[:8].upper()}"
    )

    asset = Asset(
        id=uuid.uuid4(),
        organization_id=membership.organization_id,
        public_asset_reference=public_ref,
        asset_class=asset_class,
        category=body.category,
        name=body.name,
        description=body.description,
        status=AssetStatus.EVIDENCE_INTAKE,
        private_serial_number=body.private_serial_number,
        client_internal_reference=body.client_internal_reference,
        created_by=user.id,
    )
    db.add(asset)
    db.flush()

    if body.compute_profile:
        profile = body.compute_profile
        condition = None
        if profile.condition_status:
            try:
                condition = ConditionStatus(profile.condition_status)
            except ValueError:
                condition = None
        intended = None
        if profile.intended_use:
            try:
                intended = IntendedUse(profile.intended_use)
            except ValueError:
                intended = None
        cap = ComputeAssetProfile(
            id=uuid.uuid4(),
            asset_id=asset.id,
            manufacturer=profile.manufacturer,
            model=profile.model,
            gpu_count=profile.gpu_count,
            vram_per_gpu_gb=profile.vram_per_gpu_gb,
            cpu=profile.cpu,
            ram_gb=profile.ram_gb,
            storage_description=profile.storage_description,
            networking_description=profile.networking_description,
            operating_system=profile.operating_system,
            condition_status=condition,
            operational_status=profile.operational_status,
            intended_use=intended,
            purchase_date=profile.purchase_date,
            purchase_cost_private=profile.purchase_cost_private,
        )
        db.add(cap)

    audit_record(
        db,
        organization_id=membership.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="asset.create",
        entity_type="Asset",
        entity_id=str(asset.id),
        metadata={"public_asset_reference": public_ref},
    )
    db.commit()
    db.refresh(asset)
    return _serialise(asset)


@router.get("/assets/{asset_id}", response_model=AssetOut)
def get_asset(
    asset_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> AssetOut:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail="asset not found")
    return _serialise(asset)


@router.patch("/assets/{asset_id}", response_model=AssetOut)
def patch_asset(
    asset_id: uuid.UUID,
    body: AssetCreateRequest,
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssetOut:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail="asset not found")
    if body.name:
        asset.name = body.name
    if body.description is not None:
        asset.description = body.description
    if body.category is not None:
        asset.category = body.category
    audit_record(
        db,
        organization_id=membership.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="asset.update",
        entity_type="Asset",
        entity_id=str(asset.id),
    )
    db.commit()
    db.refresh(asset)
    return _serialise(asset)
