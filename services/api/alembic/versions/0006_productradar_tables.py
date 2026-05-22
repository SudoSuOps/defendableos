"""productradar tables · runs after enum additions commit

Revision ID: 0006_productradar_tables
Revises: 0005_productradar_enum_additions
Create Date: 2026-05-22

Creates the 10 ProductRadar tables. The new enum values added in
0005 are usable here because that migration committed first.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_productradar_tables"
down_revision = "0005_productradar_enum_additions"
branch_labels = None
depends_on = None


def _enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(name=name, create_type=False)


def upgrade() -> None:
    # 1. product_opportunities
    op.create_table(
        "product_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", sa.String(120), unique=True, nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("canonical_search_query", sa.String(255), nullable=False),
        sa.Column("category", _enum("product_category_enum"), nullable=False,
                  server_default="OTHER"),
        sa.Column("status", _enum("opportunity_status_enum"), nullable=False,
                  server_default="WATCHLIST"),
        sa.Column("recommendation", _enum("opportunity_recommendation_enum")),
        sa.Column("notes", sa.Text),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("latest_score", sa.Float),
        sa.Column("latest_score_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 2. keyword_demand_signals
    op.create_table(
        "keyword_demand_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("product_opportunities.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("provider", sa.String(64), nullable=False, server_default="AHREFS"),
        sa.Column("keyword", sa.String(255), nullable=False),
        sa.Column("country", sa.String(8)),
        sa.Column("monthly_search_volume", sa.Integer),
        sa.Column("keyword_difficulty", sa.Integer),
        sa.Column("clicks_per_search", sa.Float),
        sa.Column("cpc_usd", sa.Numeric(10, 2)),
        sa.Column("volume_trend", _enum("keyword_search_volume_trend_enum"), nullable=False,
                  server_default="UNKNOWN"),
        sa.Column("trend_growth_pct", sa.Float),
        sa.Column("volume_history_json", postgresql.JSONB),
        sa.Column("serp_snapshot_json", postgresql.JSONB),
        sa.Column("signal_class", _enum("signal_class_enum"), nullable=False,
                  server_default="SEARCH_DEMAND_SIGNAL"),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 3. shopping_popularity_signals
    op.create_table(
        "shopping_popularity_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("product_opportunities.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("provider", sa.String(64), nullable=False, server_default="GOOGLE_MERCHANT_CENTER"),
        sa.Column("google_product_category", sa.String(255)),
        sa.Column("product_title_observed", sa.Text),
        sa.Column("brand_observed", sa.String(255)),
        sa.Column("rank_in_category", sa.Integer),
        sa.Column("popularity_band", sa.String(32)),
        sa.Column("country", sa.String(8)),
        sa.Column("connected_merchant_carries", sa.Boolean),
        sa.Column("signal_class", _enum("signal_class_enum"), nullable=False,
                  server_default="GOOGLE_SHOPPING_POPULARITY"),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 4. social_trend_signals
    op.create_table(
        "social_trend_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("product_opportunities.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("provider", sa.String(64), nullable=False, server_default="TIKTOK_CREATIVE_CENTER"),
        sa.Column("product_title_observed", sa.Text),
        sa.Column("region", sa.String(64)),
        sa.Column("ad_creative_count", sa.Integer),
        sa.Column("audience_signal_summary", sa.Text),
        sa.Column("momentum_score", sa.Float),
        sa.Column("related_videos_json", postgresql.JSONB),
        sa.Column("signal_class", _enum("signal_class_enum"), nullable=False,
                  server_default="SOCIAL_COMMERCE_TREND_SIGNAL"),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 5. store_intelligence_observations
    op.create_table(
        "store_intelligence_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("product_opportunities.id", ondelete="SET NULL"), index=True),
        sa.Column("provider", sa.String(64), nullable=False, server_default="SIMILARWEB"),
        sa.Column("store_domain", sa.String(255), nullable=False),
        sa.Column("store_name", sa.String(255)),
        sa.Column("category_overlap", sa.String(255)),
        sa.Column("estimated_monthly_visits", sa.Integer),
        sa.Column("estimated_conversion_rate", sa.Float),
        sa.Column("estimated_monthly_revenue_band", sa.String(64)),
        sa.Column("competitive_rank", sa.Integer),
        sa.Column("estimate_basis", sa.Text),
        sa.Column("signal_class", _enum("signal_class_enum"), nullable=False,
                  server_default="RETAIL_INTELLIGENCE_ESTIMATE"),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 6. marketplace_sales_researches
    op.create_table(
        "marketplace_sales_researches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("product_opportunities.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("provider", sa.String(64), nullable=False, server_default="EBAY_PRODUCT_RESEARCH"),
        sa.Column("research_query", sa.String(255), nullable=False),
        sa.Column("lookback_days", sa.Integer),
        sa.Column("average_sold_price_usd", sa.Numeric(14, 2)),
        sa.Column("sold_price_band_min_usd", sa.Numeric(14, 2)),
        sa.Column("sold_price_band_max_usd", sa.Numeric(14, 2)),
        sa.Column("sales_trend_summary", sa.Text),
        sa.Column("units_sold_estimate", sa.Integer),
        sa.Column("analyst_review_status", sa.String(64), nullable=False,
                  server_default="ANALYST_REVIEW_REQUIRED"),
        sa.Column("analyst_notes", sa.Text),
        sa.Column("rights_status", sa.String(64), nullable=False,
                  server_default="EBAY_SELLER_TOOLING_ONLY"),
        sa.Column("signal_class", _enum("signal_class_enum"), nullable=False,
                  server_default="MARKETPLACE_SOLD_RESEARCH"),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 7. supplier_candidates
    op.create_table(
        "supplier_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("product_opportunities.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("supplier_name", sa.String(255), nullable=False),
        sa.Column("supplier_url", sa.String(500)),
        sa.Column("landed_cost_usd", sa.Numeric(10, 2)),
        sa.Column("minimum_order_quantity", sa.Integer),
        sa.Column("estimated_lead_time_days", sa.Integer),
        sa.Column("shipping_burden_summary", sa.Text),
        sa.Column("feasibility", _enum("supplier_feasibility_enum"), nullable=False,
                  server_default="NOT_REVIEWED"),
        sa.Column("review_notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 8. margin_scenarios
    op.create_table(
        "margin_scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("product_opportunities.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("supplier_candidate_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("supplier_candidates.id", ondelete="SET NULL")),
        sa.Column("scenario_label", sa.String(120), nullable=False),
        sa.Column("target_retail_price_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("landed_cost_usd", sa.Numeric(10, 2)),
        sa.Column("platform_fee_pct", sa.Float),
        sa.Column("shipping_cost_usd", sa.Numeric(10, 2)),
        sa.Column("return_rate_estimate_pct", sa.Float),
        sa.Column("gross_margin_per_unit_usd", sa.Numeric(10, 2)),
        sa.Column("gross_margin_pct", sa.Float),
        sa.Column("assumptions_json", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 9. connected_store_outcomes
    op.create_table(
        "connected_store_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("product_opportunities.id", ondelete="SET NULL"), index=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="SET NULL")),
        sa.Column("provider", _enum("connected_store_provider_enum"), nullable=False),
        sa.Column("store_domain", sa.String(255)),
        sa.Column("product_handle", sa.String(255)),
        sa.Column("units_sold", sa.Integer),
        sa.Column("gross_revenue_usd", sa.Numeric(14, 2)),
        sa.Column("period_start", sa.DateTime(timezone=True)),
        sa.Column("period_end", sa.DateTime(timezone=True)),
        sa.Column("rights_status", sa.String(64), nullable=False,
                  server_default="PERMISSIONED_CLIENT_OWNED"),
        sa.Column("signal_class", _enum("signal_class_enum"), nullable=False,
                  server_default="PERMISSIONED_CONNECTED_SALE"),
        sa.Column("raw_artifact_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("artifact_registry.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 10. opportunity_score_receipts
    op.create_table(
        "opportunity_score_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("product_opportunities.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="v1"),
        sa.Column("total_score", sa.Float, nullable=False),
        sa.Column("component_breakdown_json", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("competition_level", _enum("competition_level_enum"), nullable=False,
                  server_default="UNKNOWN"),
        sa.Column("policy_risk_flag", _enum("policy_risk_flag_enum"), nullable=False,
                  server_default="NONE"),
        sa.Column("signals_used_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("confirmed_sale_signals_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("recommendation", _enum("opportunity_recommendation_enum"), nullable=False,
                  server_default="GATHER_MORE_SIGNALS"),
        sa.Column("receipt_sha256", sa.String(64)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "opportunity_score_receipts",
        "connected_store_outcomes",
        "margin_scenarios",
        "supplier_candidates",
        "marketplace_sales_researches",
        "store_intelligence_observations",
        "social_trend_signals",
        "shopping_popularity_signals",
        "keyword_demand_signals",
        "product_opportunities",
    ]:
        op.drop_table(table)
