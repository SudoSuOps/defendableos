"""productradar enum additions only · safe in own transaction

Revision ID: 0005_productradar_enum_additions
Revises: 0004_itad_tables
Create Date: 2026-05-22

Adds 5 new ProductRadar provider names to provider_name_enum and
creates the 9 new ProductRadar-specific enums. Split from
0006_productradar_tables to satisfy PostgreSQL's
UnsafeNewEnumValueUsage rule.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_productradar_enum_additions"
down_revision = "0004_itad_tables"
branch_labels = None
depends_on = None


EXISTING_ENUM_ADDITIONS: dict[str, tuple[str, ...]] = {
    "provider_name_enum": (
        "AHREFS_KEYWORDS_EXPLORER",
        "GOOGLE_MERCHANT_CENTER_BEST_SELLERS",
        "TIKTOK_CREATIVE_CENTER",
        "EBAY_PRODUCT_RESEARCH",
        "SIMILARWEB_SHOPPER_INTELLIGENCE",
        "CONNECTED_SHOPIFY_STORE",
        "SUPPLIER_CATALOG_FUTURE",
    ),
}


NEW_ENUMS: dict[str, tuple[str, ...]] = {
    "signal_class_enum": (
        "SEARCH_DEMAND_SIGNAL",
        "SOCIAL_COMMERCE_TREND_SIGNAL",
        "GOOGLE_SHOPPING_POPULARITY",
        "RETAIL_INTELLIGENCE_ESTIMATE",
        "MARKETPLACE_SOLD_RESEARCH",
        "PERMISSIONED_CONNECTED_SALE",
        "FIRST_PARTY_DEFENDABLE_SALE",
    ),
    "opportunity_status_enum": (
        "WATCHLIST", "RESEARCH_CANDIDATE", "RESEARCH_MORE",
        "SUPPLIER_REVIEW_READY", "MARKETREADY_CANDIDATE", "LAUNCHED",
        "REJECT_MARGIN_RISK", "REJECT_POLICY_RISK",
        "REJECT_OVERSATURATED", "REJECT_LOW_SIGNAL",
    ),
    "product_category_enum": (
        "HOME_ORGANIZATION", "PET_ACCESSORIES", "KITCHEN_LIFESTYLE",
        "TRAVEL_ORGANIZATION", "OUTDOOR_RECREATION", "HOME_OFFICE",
        "NON_MEDICAL_WELLNESS", "SPECIALTY_STORAGE", "OTHER",
    ),
    "opportunity_recommendation_enum": (
        "LAUNCH_READY", "PROCEED_TO_SUPPLIER_REVIEW",
        "GATHER_MORE_SIGNALS", "DEPRIORITIZE", "REJECT",
    ),
    "keyword_search_volume_trend_enum": (
        "RISING", "STEADY", "DECLINING", "UNKNOWN",
    ),
    "competition_level_enum": (
        "LOW", "MEDIUM", "HIGH", "OVERSATURATED", "UNKNOWN",
    ),
    "supplier_feasibility_enum": (
        "NOT_REVIEWED", "PENDING_QUOTES", "INFEASIBLE_MARGIN",
        "INFEASIBLE_SHIPPING", "FEASIBLE",
    ),
    "policy_risk_flag_enum": (
        "NONE", "PLATFORM_RESTRICTED", "REGULATED_GOOD",
        "TRADEMARK_RISK", "SHIPPING_RESTRICTED", "REJECTED",
    ),
    "connected_store_provider_enum": (
        "SHOPIFY", "EBAY", "AMAZON", "WOOCOMMERCE", "OTHER",
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
