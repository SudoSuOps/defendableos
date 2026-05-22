"""FastAPI dependencies · auth, current user, current org, role checks."""
from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, decode_edge_token
from app.db.session import get_db
from app.models.edge import EdgeNode
from app.models.organization import OrganizationMembership, OrgRole
from app.models.user import User

bearer = HTTPBearer(auto_error=False)
edge_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="auth required")
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid subject")
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid subject")
    user = db.get(User, uid)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    return user


def get_current_membership(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMembership:
    """Resolve the user's active org membership. MVP: pick the first one.

    A future iteration will honor an X-Organization-Id header for multi-org users.
    """
    membership = (
        db.query(OrganizationMembership)
        .filter(OrganizationMembership.user_id == user.id)
        .order_by(OrganizationMembership.created_at.asc())
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no organization membership")
    return membership


def require_role(*allowed: OrgRole):
    def _checker(
        membership: OrganizationMembership = Depends(get_current_membership),
    ) -> OrganizationMembership:
        if membership.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role {membership.role.value} not permitted",
            )
        return membership

    return _checker


def require_platform_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="platform admin required")
    return user


def get_current_edge_node(
    credentials: HTTPAuthorizationCredentials | None = Depends(edge_bearer),
    db: Session = Depends(get_db),
) -> EdgeNode:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="edge auth required")
    try:
        payload = decode_edge_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid edge token")
    if payload.get("kind") != "edge_node":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not an edge token")
    try:
        node_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad edge subject")
    node = db.get(EdgeNode, node_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="edge node not registered")
    if node.enrollment_status.value == "REVOKED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="edge node revoked")
    return node
