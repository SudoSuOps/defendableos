"""Audit log helpers. Approval/publication/issuance/edge actions write here."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


def record(
    db: Session,
    *,
    organization_id: uuid.UUID | None,
    actor_type: str,
    actor_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        id=uuid.uuid4(),
        organization_id=organization_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        extra_metadata=metadata or {},
    )
    db.add(event)
    return event
