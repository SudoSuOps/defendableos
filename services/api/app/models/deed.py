from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk


class DeedStatus(str, enum.Enum):
    DRAFT_REVIEW_RECORD = "DRAFT_REVIEW_RECORD"
    PASSED_FOR_PACKAGING = "PASSED_FOR_PACKAGING"
    APPROVED_FOR_PUBLIC = "APPROVED_FOR_PUBLIC"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"


class DefendableDeed(Base, TimestampMixin):
    __tablename__ = "defendable_deeds"
    __table_args__ = (
        UniqueConstraint("asset_id", "version", name="uq_deed_asset_version"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deed_reference: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[DeedStatus] = mapped_column(
        Enum(DeedStatus, name="deed_status_enum"),
        default=DeedStatus.DRAFT_REVIEW_RECORD,
        nullable=False,
    )
    deed_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    record_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    public_slug: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    issued_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    asset = relationship("Asset", back_populates="deeds")
