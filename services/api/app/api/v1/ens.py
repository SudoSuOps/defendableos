from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_membership, get_current_user
from app.db.session import get_db
from app.models.ens import ENSIdentity, IdentityType
from app.models.organization import OrganizationMembership
from app.models.user import User
from app.schemas.ens import ENSIdentityOut, ENSReservationRequest
from app.services.audit import record as audit_record
from app.services.ens import ReservationRequest, get_adapter

router = APIRouter()


@router.get("/ens/identities", response_model=list[ENSIdentityOut])
def list_identities(
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> list[ENSIdentityOut]:
    rows = (
        db.query(ENSIdentity)
        .filter(ENSIdentity.organization_id == membership.organization_id)
        .order_by(ENSIdentity.created_at.desc())
        .all()
    )
    return [ENSIdentityOut.model_validate(r) for r in rows]


@router.post("/ens/reserve", response_model=ENSIdentityOut)
def reserve(
    body: ENSReservationRequest,
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ENSIdentityOut:
    if body.organization_id != membership.organization_id:
        raise HTTPException(status_code=403, detail="organization mismatch")
    try:
        identity_type = IdentityType(body.identity_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid identity_type")

    adapter = get_adapter()
    try:
        result = adapter.reserve(
            db,
            ReservationRequest(
                label=body.label,
                parent=settings.ens_parent_name,
                identity_type=identity_type,
                organization_id=body.organization_id,
                asset_id=body.asset_id,
                deed_id=body.deed_id,
                edge_node_id=body.edge_node_id,
                public_metadata=body.public_metadata,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    audit_record(
        db,
        organization_id=membership.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="ens.reserve",
        entity_type="ENSIdentity",
        entity_id=str(result.identity.id),
        metadata={"ens_name": result.identity.ens_name, "issuance_mode": result.identity.issuance_mode.value},
    )
    db.commit()
    db.refresh(result.identity)
    return ENSIdentityOut.model_validate(result.identity)


@router.get("/ens/identities/{identity_id}", response_model=ENSIdentityOut)
def get_identity(
    identity_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> ENSIdentityOut:
    identity = db.get(ENSIdentity, identity_id)
    if identity is None or identity.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail="identity not found")
    return ENSIdentityOut.model_validate(identity)


@router.post("/ens/identities/{identity_id}/prepare-public-records", response_model=ENSIdentityOut)
def prepare_public_records(
    identity_id: uuid.UUID,
    membership: OrganizationMembership = Depends(get_current_membership),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ENSIdentityOut:
    identity = db.get(ENSIdentity, identity_id)
    if identity is None or identity.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail="identity not found")

    # Build a privacy-safe metadata payload appropriate to the identity type.
    payload = identity.public_metadata_json or {}
    payload.setdefault("com.defendable.type", identity.identity_type.value)
    payload.setdefault("com.defendable.status", "PUBLIC_RECORD_PROPOSED")
    identity.public_metadata_json = payload

    audit_record(
        db,
        organization_id=membership.organization_id,
        actor_type="USER",
        actor_id=str(user.id),
        action="ens.prepare_public_records",
        entity_type="ENSIdentity",
        entity_id=str(identity.id),
    )
    db.commit()
    db.refresh(identity)
    return ENSIdentityOut.model_validate(identity)
