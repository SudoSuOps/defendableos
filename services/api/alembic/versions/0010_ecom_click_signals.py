"""ecommerce_product_click_signals table · runs after enum commit

Revision ID: 0010_ecommerce_product_click_signals
Revises: 0009_semrush_enum_additions
Create Date: 2026-05-22

Creates the EcommerceProductClickSignal table (Semrush Retail
Keywords / product-click intelligence). Other Semrush roles reuse
existing tables (KeywordDemandSignal with provider=SEMRUSH ·
StoreIntelligenceObservation with provider=SEMRUSH).
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0010_ecom_click_signals"
down_revision = "0009_semrush_enum_additions"
branch_labels = None
depends_on = None


def _enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(name=name, create_type=False)


def upgrade() -> None:
    op.create_table(
        "ecommerce_product_click_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("product_opportunities.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("provider", sa.String(64), nullable=False, server_default="SEMRUSH"),
        sa.Column("retail_keyword", sa.String(255), nullable=False),
        sa.Column("country", sa.String(8)),
        sa.Column("estimated_search_requests", sa.Integer),
        sa.Column("product_clicks", sa.Integer),
        sa.Column("month_over_month_change_pct", sa.Float),
        sa.Column("top_clicked_domains_json", postgresql.JSONB),
        sa.Column("measurement_period_start", sa.DateTime(timezone=True)),
        sa.Column("measurement_period_end", sa.DateTime(timezone=True)),
        # Doctrine pins · application layer refuses to flip.
        sa.Column("sales_confirmed", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("rights_status", sa.String(64), nullable=False,
                  server_default="INTERNAL_RESEARCH_ONLY"),
        sa.Column("training_eligible", sa.Boolean, nullable=False, server_default=sa.text("false")),
        # signal_class default uses an EXISTING enum value
        # (SEARCH_DEMAND_SIGNAL) to avoid the PostgreSQL session-cache
        # rule on newly-added enum values. Python model default still
        # writes ECOMMERCE_PRODUCT_CLICK_SIGNAL at INSERT time.
        sa.Column("signal_class", _enum("signal_class_enum"), nullable=False,
                  server_default="SEARCH_DEMAND_SIGNAL"),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ecommerce_product_click_signals")
