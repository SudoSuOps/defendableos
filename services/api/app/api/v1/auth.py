from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.organization import OrganizationMembership
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MeOut,
    MembershipOut,
    TokenResponse,
    UserOut,
)

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == req.email).first()
    if user is None or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    token = create_access_token(
        subject=str(user.id),
        claims={"is_platform_admin": user.is_platform_admin},
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MeOut:
    memberships = (
        db.query(OrganizationMembership)
        .filter(OrganizationMembership.user_id == user.id)
        .all()
    )
    return MeOut(
        user=UserOut.model_validate(user),
        memberships=[MembershipOut(organization_id=m.organization_id, role=m.role.value) for m in memberships],
    )
