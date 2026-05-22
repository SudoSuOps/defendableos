from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk


class EnrollmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    ENROLLED = "ENROLLED"
    ENROLLED_DEMO = "ENROLLED_DEMO"
    STALE = "STALE"
    REVOKED = "REVOKED"


class EdgeNode(Base, TimestampMixin):
    __tablename__ = "edge_nodes"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    node_name: Mapped[str] = mapped_column(String(128), nullable=False)
    node_slug: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ens_identity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ens_identities.id", ondelete="SET NULL")
    )
    enrollment_status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus, name="enrollment_status_enum"),
        default=EnrollmentStatus.PENDING,
        nullable=False,
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    software_version: Mapped[str | None] = mapped_column(String(64))
    hardware_summary_json: Mapped[dict | None] = mapped_column(JSONB)
    public_key_or_device_fingerprint: Mapped[str | None] = mapped_column(String(512))


class EdgeUploadEvent(Base, TimestampMixin):
    __tablename__ = "edge_upload_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    edge_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("edge_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence_items.id", ondelete="SET NULL")
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String(64))
    claimed_hash: Mapped[str | None] = mapped_column(String(64))
    verified_hash: Mapped[str | None] = mapped_column(String(64))
    hash_match: Mapped[bool | None] = mapped_column(Boolean)
    sync_status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACCEPTED")


class EdgeEnrollmentToken(Base, TimestampMixin):
    __tablename__ = "edge_enrollment_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    node_name_hint: Mapped[str | None] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_by_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("edge_nodes.id", ondelete="SET NULL")
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
