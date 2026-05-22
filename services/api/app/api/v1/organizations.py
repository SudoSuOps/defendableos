from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_membership
from app.db.session import get_db
from app.models.organization import Organization, OrganizationMembership
from app.schemas.organization import OrganizationOut

router = APIRouter()


@router.get("/organizations/current", response_model=OrganizationOut)
def current_organization(
    membership: OrganizationMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> OrganizationOut:
    org = db.get(Organization, membership.organization_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="organization not found")
    return OrganizationOut.model_validate(org)
