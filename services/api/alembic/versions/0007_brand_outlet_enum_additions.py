"""brand outlet enum additions only

Revision ID: 0007_brand_outlet_enum_additions
Revises: 0006_productradar_tables
Create Date: 2026-05-22

Adds EBAY_BRAND_OUTLET to provider_name_enum + BRANDED_COMMERCE_
PLACEMENT to signal_class_enum + creates 3 new Brand Outlet enums.
Split from 0008 for PostgreSQL UnsafeNewEnumValueUsage safety.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_brand_outlet_enum_additions"
down_revision = "0006_productradar_tables"
branch_labels = None
depends_on = None


EXISTING_ENUM_ADDITIONS: dict[str, tuple[str, ...]] = {
    "provider_name_enum": ("EBAY_BRAND_OUTLET",),
    "signal_class_enum": ("BRANDED_COMMERCE_PLACEMENT",),
}


NEW_ENUMS: dict[str, tuple[str, ...]] = {
    "brand_priority_tier_enum": ("A", "B", "C", "DEFER"),
    "brand_sourcing_status_enum": (
        "NOT_REVIEWED", "AUTHORIZED_RESELLER_KNOWN",
        "DIRECT_SOURCE_KNOWN", "RESTRICTED", "NOT_AVAILABLE",
    ),
    "merchandising_lane_enum": (
        "ELITE_TECH", "LATEST_TECH", "HOME_POWER_EQUIPMENT",
        "HOME_KITCHEN", "TOOLS_EQUIPMENT", "LUXURY_HANDBAGS",
        "LUXURY_WATCHES_JEWELRY", "FASHION_FOOTWEAR",
        "REFURBISHED_ELECTRONICS", "OTHER",
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
