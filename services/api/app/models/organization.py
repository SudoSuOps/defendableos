from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk


class OrgRole(str, enum.Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    ORG_ADMIN = "ORG_ADMIN"
    ORG_ANALYST = "ORG_ANALYST"
    ORG_VIEWER = "ORG_VIEWER"


class ENSStatus(str, enum.Enum):
    UNRESERVED = "UNRESERVED"
    RESERVED_NOT_ISSUED = "RESERVED_NOT_ISSUED"
    ISSUED_OFFCHAIN = "ISSUED_OFFCHAIN"
    ISSUED_ONCHAIN = "ISSUED_ONCHAIN"
    REVOKED = "REVOKED"


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped = uuid_pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    ens_label: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    ens_name: Mapped[str | None] = mapped_column(String(255))
    ens_status: Mapped[ENSStatus] = mapped_column(
        Enum(ENSStatus, name="ens_status_enum"),
        default=ENSStatus.UNRESERVED,
        nullable=False,
    )

    memberships = relationship(
        "OrganizationMembership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    assets = relationship("Asset", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMembership(Base, TimestampMixin):
    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),
    )

    id: Mapped = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[OrgRole] = mapped_column(
        Enum(OrgRole, name="org_role_enum"), nullable=False
    )

    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="memberships")
