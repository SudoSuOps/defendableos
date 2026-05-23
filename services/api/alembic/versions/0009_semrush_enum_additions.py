"""semrush enum additions only · safe in own transaction

Revision ID: 0009_semrush_enum_additions
Revises: 0008_brand_outlet_tables
Create Date: 2026-05-22

Adds Semrush provider + 2 new signal classes + the
PLAN_VERIFICATION_REQUIRED provider-status state.
Split from 0010 per PostgreSQL UnsafeNewEnumValueUsage rule.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0009_semrush_enum_additions"
down_revision = "0008_brand_outlet_tables"
branch_labels = None
depends_on = None


EXISTING_ENUM_ADDITIONS: dict[str, tuple[str, ...]] = {
    "provider_name_enum": ("SEMRUSH",),
    "provider_status_enum": ("PLAN_VERIFICATION_REQUIRED",),
    "signal_class_enum": (
        "ECOMMERCE_PRODUCT_CLICK_SIGNAL",
        "COMPETITOR_VISIBILITY_SIGNAL",
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    for enum_name, values in EXISTING_ENUM_ADDITIONS.items():
        for v in values:
            bind.execute(sa.text(
                f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{v}'"
            ))


def downgrade() -> None:
    # ALTER TYPE DROP VALUE not supported in PostgreSQL · additions stay.
    pass
