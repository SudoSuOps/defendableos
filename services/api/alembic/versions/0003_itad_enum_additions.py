"""itad enum additions only · safe in own transaction

Revision ID: 0003_itad_enum_additions
Revises: 0002_goods_intelligence
Create Date: 2026-05-22

Adds new values to EXISTING enums + creates the 10 new ITAD-specific
enums. PostgreSQL refuses to USE a newly-added enum value in the
same transaction it was added (UnsafeNewEnumValueUsage), so this
migration is intentionally split from 0004_itad_tables which is the
one that consumes the new values.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_itad_enum_additions"
down_revision = "0002_goods_intelligence"
branch_labels = None
depends_on = None


EXISTING_ENUM_ADDITIONS: dict[str, tuple[str, ...]] = {
    "provider_name_enum": ("ITAD_PARTNER_FEED",),
    "provider_status_enum": (
        "RESEARCH_VERIFIED",
        "OUTREACH_PENDING",
        "OUTREACH_READY",
        "IN_CONVERSATION",
        "AGREEMENT_REQUIRED",
    ),
    "source_type_enum": ("PERMISSIONED_PARTNER_TRANSACTION",),
    "rights_status_enum": ("AGREEMENT_REQUIRED",),
}


NEW_ENUMS: dict[str, tuple[str, ...]] = {
    "itad_partnership_status_enum": (
        "RESEARCH_VERIFIED", "OUTREACH_READY", "OUTREACH_PENDING",
        "IN_CONVERSATION", "PILOT_AGREEMENT", "PRODUCTION_PARTNER", "DECLINED",
    ),
    "itad_feed_format_enum": (
        "UNKNOWN", "CSV", "JSON", "API", "MANUAL_EXPORT",
    ),
    "itad_agreement_status_enum": (
        "NONE", "NDA_SIGNED", "PILOT_AGREEMENT", "PRODUCTION_AGREEMENT",
    ),
    "itad_contact_status_enum": (
        "NOT_CONTACTED", "EMAIL_SENT", "RESPONSE_RECEIVED",
        "IN_CONVERSATION", "NO_RESPONSE",
    ),
    "itad_asset_type_enum": (
        "GPU", "GPU_SERVER", "DGX_HGX", "WORKSTATION", "COMPONENT",
        "NETWORKING", "STORAGE", "OTHER",
    ),
    "itad_form_factor_enum": (
        "PCIE", "SXM", "SYSTEM", "UNKNOWN",
    ),
    "itad_condition_class_enum": (
        "TESTED", "REFURBISHED", "AS_IS", "PULL", "UNKNOWN",
    ),
    "itad_transaction_type_enum": (
        "DIRECT_BUYBACK", "REMARKETING_SALE", "AUCTION_SALE", "UNKNOWN",
    ),
    "itad_amount_disclosure_type_enum": (
        "EXACT", "RANGE", "INDEXED", "REDACTED",
    ),
    "itad_feed_import_status_enum": (
        "PENDING", "IMPORTING", "IMPORTED", "FAILED",
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    for enum_name, values in EXISTING_ENUM_ADDITIONS.items():
        for v in values:
            bind.execute(sa.text(
                f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{v}'"
            ))
    for name, values in NEW_ENUMS.items():
        vlist = ", ".join(f"'{v}'" for v in values)
        bind.execute(sa.text(f"CREATE TYPE {name} AS ENUM ({vlist})"))


def downgrade() -> None:
    for enum_name in list(NEW_ENUMS.keys()):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
    # ALTER TYPE DROP VALUE is not supported in PostgreSQL · added
    # values stay (harmless if unused).
