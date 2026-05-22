from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk


class IdentityType(str, enum.Enum):
    ORGANIZATION = "ORGANIZATION"
    ASSET = "ASSET"
    DEED = "DEED"
    EDGE_NODE = "EDGE_NODE"


class IssuanceMode(str, enum.Enum):
    RESERVED = "RESERVED"
    MOCK = "MOCK"
    OFFCHAIN_CCIP = "OFFCHAIN_CCIP"
    ONCHAIN_WRAPPED = "ONCHAIN_WRAPPED"


class IdentityStatus(str, enum.Enum):
    RESERVED_NOT_ISSUED = "RESERVED_NOT_ISSUED"
    ISSUED = "ISSUED"
    REVOKED = "REVOKED"


class ENSIdentity(Base, TimestampMixin):
    __tablename__ = "ens_identities"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL")
    )
    deed_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("defendable_deeds.id", ondelete="SET NULL")
    )
    edge_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("edge_nodes.id", ondelete="SET NULL")
    )
    ens_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    parent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    identity_type: Mapped[IdentityType] = mapped_column(
        Enum(IdentityType, name="identity_type_enum"), nullable=False
    )
    issuance_mode: Mapped[IssuanceMode] = mapped_column(
        Enum(IssuanceMode, name="issuance_mode_enum"),
        default=IssuanceMode.MOCK,
        nullable=False,
    )
    status: Mapped[IdentityStatus] = mapped_column(
        Enum(IdentityStatus, name="identity_status_enum"),
        default=IdentityStatus.RESERVED_NOT_ISSUED,
        nullable=False,
    )
    public_metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    transaction_hash: Mapped[str | None] = mapped_column(String(128))
