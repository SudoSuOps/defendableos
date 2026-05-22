from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk


class ValidatorStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_REVIEW = "IN_REVIEW"
    FAILED_REQUIRES_REPAIR = "FAILED_REQUIRES_REPAIR"
    PASSED_FOR_PACKAGING = "PASSED_FOR_PACKAGING"
    APPROVED_FOR_PUBLIC_VERIFICATION = "APPROVED_FOR_PUBLIC_VERIFICATION"


class ValidatorReview(Base, TimestampMixin):
    __tablename__ = "validator_reviews"

    id: Mapped[uuid.UUID] = uuid_pk()
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    aiov_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("aiov_analyses.id", ondelete="SET NULL")
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[ValidatorStatus] = mapped_column(
        Enum(ValidatorStatus, name="validator_status_enum"),
        default=ValidatorStatus.NOT_STARTED,
        nullable=False,
    )
    protocol: Mapped[str] = mapped_column(String(64), nullable=False, default="VALIDATE_THE_VALIDATOR")
    findings_json: Mapped[list[dict] | None] = mapped_column(JSONB)
    checks_json: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    receipt_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
