from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str | None
    is_platform_admin: bool

    model_config = {"from_attributes": True}


class MembershipOut(BaseModel):
    organization_id: uuid.UUID
    role: str


class MeOut(BaseModel):
    user: UserOut
    memberships: list[MembershipOut]
