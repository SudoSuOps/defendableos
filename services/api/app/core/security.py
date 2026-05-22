"""Password hashing + JWT issuance.

MVP-grade: HS256 JWT for the portal session, bcrypt password hashing.
Edge devices use a separate enrollment-secret-signed token (see edge.py).
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(password, hashed)
    except Exception:
        return False


def create_access_token(subject: str, claims: dict[str, Any] | None = None) -> str:
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(minutes=settings.jwt_expires_minutes)).timestamp()
        ),
        "iss": "defendableos",
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "iat", "sub"]},
    )


def create_edge_token(node_id: str) -> str:
    """Edge-node tokens use a separate secret + a longer-lived claim shape."""
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": node_id,
        "kind": "edge_node",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=365)).timestamp()),
        "iss": "defendableos",
    }
    return jwt.encode(payload, settings.edge_enrollment_secret, algorithm="HS256")


def decode_edge_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.edge_enrollment_secret,
        algorithms=["HS256"],
        options={"require": ["exp", "iat", "sub"]},
    )


def new_enrollment_token() -> str:
    return secrets.token_urlsafe(32)
