"""Defendable ProductRadar · demand intelligence schema.

Sits BEFORE MarketReady. Where the Goods Vault answers
"what is THIS thing worth?", ProductRadar answers "what should we
SELL next?". The two halves connect via OpportunityScoreReceipt →
(eventually) MarketReady launch package → connected store sale →
back into Goods Vault as confirmed first-party transaction evidence.

Truth doctrine encoded as SignalClass enum · every signal carries
its own epistemic weight:

  · SEARCH_DEMAND_SIGNAL           · Ahrefs · keyword interest
  · SOCIAL_COMMERCE_TREND_SIGNAL   · TikTok · creative momentum
  · GOOGLE_SHOPPING_POPULARITY     · Google Merchant Center
  · RETAIL_INTELLIGENCE_ESTIMATE   · Similarweb (estimate · not truth)
  · MARKETPLACE_SOLD_RESEARCH      · eBay Product Research · analyst-reviewed
  · PERMISSIONED_CONNECTED_SALE    · Shopify/eBay client orders · CONFIRMED
  · FIRST_PARTY_DEFENDABLE_SALE    · Defendable-managed sale · CONFIRMED

The platform service layer (productradar.py service) refuses to roll
multiple low-truth signals into a confirmed-sale claim · the
OpportunityScoreReceipt declares exactly which signals contributed
and at what weight. No "top selling product confirmed" unless
authorized completed-sale evidence supports it.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk


# ────────────────────────────────────────────────────────────────────
#  ENUMS · 7 signal classes + supporting state machines
# ────────────────────────────────────────────────────────────────────


class SignalClass(str, enum.Enum):
    """Epistemic weight of each demand/sales signal · doctrine pinned."""
    SEARCH_DEMAND_SIGNAL = "SEARCH_DEMAND_SIGNAL"
    SOCIAL_COMMERCE_TREND_SIGNAL = "SOCIAL_COMMERCE_TREND_SIGNAL"
    GOOGLE_SHOPPING_POPULARITY = "GOOGLE_SHOPPING_POPULARITY"
    RETAIL_INTELLIGENCE_ESTIMATE = "RETAIL_INTELLIGENCE_ESTIMATE"
    MARKETPLACE_SOLD_RESEARCH = "MARKETPLACE_SOLD_RESEARCH"
    PERMISSIONED_CONNECTED_SALE = "PERMISSIONED_CONNECTED_SALE"
    FIRST_PARTY_DEFENDABLE_SALE = "FIRST_PARTY_DEFENDABLE_SALE"
    # Brand Outlet · merchandising-placement watchlist signal · added 2026-05-22.
    # NEVER confirmed sale · NEVER supplier authorization · informs the
    # discovery pipeline only · doctrine refuses any sold-claim derivation.
    BRANDED_COMMERCE_PLACEMENT = "BRANDED_COMMERCE_PLACEMENT"


class OpportunityStatus(str, enum.Enum):
    WATCHLIST = "WATCHLIST"
    RESEARCH_CANDIDATE = "RESEARCH_CANDIDATE"
    RESEARCH_MORE = "RESEARCH_MORE"
    SUPPLIER_REVIEW_READY = "SUPPLIER_REVIEW_READY"
    MARKETREADY_CANDIDATE = "MARKETREADY_CANDIDATE"
    LAUNCHED = "LAUNCHED"
    REJECT_MARGIN_RISK = "REJECT_MARGIN_RISK"
    REJECT_POLICY_RISK = "REJECT_POLICY_RISK"
    REJECT_OVERSATURATED = "REJECT_OVERSATURATED"
    REJECT_LOW_SIGNAL = "REJECT_LOW_SIGNAL"


class ProductCategory(str, enum.Enum):
    """Brand-safe categories the platform supports for product discovery."""
    HOME_ORGANIZATION = "HOME_ORGANIZATION"
    PET_ACCESSORIES = "PET_ACCESSORIES"
    KITCHEN_LIFESTYLE = "KITCHEN_LIFESTYLE"
    TRAVEL_ORGANIZATION = "TRAVEL_ORGANIZATION"
    OUTDOOR_RECREATION = "OUTDOOR_RECREATION"
    HOME_OFFICE = "HOME_OFFICE"
    NON_MEDICAL_WELLNESS = "NON_MEDICAL_WELLNESS"
    SPECIALTY_STORAGE = "SPECIALTY_STORAGE"
    OTHER = "OTHER"


class OpportunityRecommendation(str, enum.Enum):
    LAUNCH_READY = "LAUNCH_READY"
    PROCEED_TO_SUPPLIER_REVIEW = "PROCEED_TO_SUPPLIER_REVIEW"
    GATHER_MORE_SIGNALS = "GATHER_MORE_SIGNALS"
    DEPRIORITIZE = "DEPRIORITIZE"
    REJECT = "REJECT"


class KeywordSearchVolumeTrend(str, enum.Enum):
    RISING = "RISING"
    STEADY = "STEADY"
    DECLINING = "DECLINING"
    UNKNOWN = "UNKNOWN"


class CompetitionLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    OVERSATURATED = "OVERSATURATED"
    UNKNOWN = "UNKNOWN"


class SupplierFeasibility(str, enum.Enum):
    NOT_REVIEWED = "NOT_REVIEWED"
    PENDING_QUOTES = "PENDING_QUOTES"
    INFEASIBLE_MARGIN = "INFEASIBLE_MARGIN"
    INFEASIBLE_SHIPPING = "INFEASIBLE_SHIPPING"
    FEASIBLE = "FEASIBLE"


class PolicyRiskFlag(str, enum.Enum):
    NONE = "NONE"
    PLATFORM_RESTRICTED = "PLATFORM_RESTRICTED"
    REGULATED_GOOD = "REGULATED_GOOD"
    TRADEMARK_RISK = "TRADEMARK_RISK"
    SHIPPING_RESTRICTED = "SHIPPING_RESTRICTED"
    REJECTED = "REJECTED"


class ConnectedStoreProvider(str, enum.Enum):
    SHOPIFY = "SHOPIFY"
    EBAY = "EBAY"
    AMAZON = "AMAZON"
    WOOCOMMERCE = "WOOCOMMERCE"
    OTHER = "OTHER"


# ── Brand Outlet · ProductRadar watchlist generator (added 2026-05-22) ──


class BrandPriorityTier(str, enum.Enum):
    """Operator-set research priority for a brand on the watchlist."""
    A = "A"  # research now
    B = "B"  # research next
    C = "C"  # backlog
    DEFER = "DEFER"  # explicitly deferred (e.g. luxury without authorization)


class BrandSourcingStatus(str, enum.Enum):
    NOT_REVIEWED = "NOT_REVIEWED"
    AUTHORIZED_RESELLER_KNOWN = "AUTHORIZED_RESELLER_KNOWN"
    DIRECT_SOURCE_KNOWN = "DIRECT_SOURCE_KNOWN"
    RESTRICTED = "RESTRICTED"           # brand will not authorize / counterfeit risk
    NOT_AVAILABLE = "NOT_AVAILABLE"     # no path identified


class MerchandisingLane(str, enum.Enum):
    """Brand Outlet merchandising buckets · keep aligned with eBay's lanes."""
    ELITE_TECH = "ELITE_TECH"
    LATEST_TECH = "LATEST_TECH"
    HOME_POWER_EQUIPMENT = "HOME_POWER_EQUIPMENT"
    HOME_KITCHEN = "HOME_KITCHEN"
    TOOLS_EQUIPMENT = "TOOLS_EQUIPMENT"
    LUXURY_HANDBAGS = "LUXURY_HANDBAGS"
    LUXURY_WATCHES_JEWELRY = "LUXURY_WATCHES_JEWELRY"
    FASHION_FOOTWEAR = "FASHION_FOOTWEAR"
    REFURBISHED_ELECTRONICS = "REFURBISHED_ELECTRONICS"
    OTHER = "OTHER"


# ────────────────────────────────────────────────────────────────────
#  1 · ProductOpportunity · the central discovery entity
# ────────────────────────────────────────────────────────────────────


class ProductOpportunity(Base, TimestampMixin):
    __tablename__ = "product_opportunities"

    id: Mapped[uuid.UUID] = uuid_pk()
    opportunity_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_search_query: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[ProductCategory] = mapped_column(
        Enum(ProductCategory, name="product_category_enum"),
        nullable=False,
        default=ProductCategory.OTHER,
    )
    status: Mapped[OpportunityStatus] = mapped_column(
        Enum(OpportunityStatus, name="opportunity_status_enum"),
        nullable=False,
        default=OpportunityStatus.WATCHLIST,
        index=True,
    )
    recommendation: Mapped[OpportunityRecommendation | None] = mapped_column(
        Enum(OpportunityRecommendation, name="opportunity_recommendation_enum")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # Latest opportunity score · denormalized for fast list display
    latest_score: Mapped[float | None] = mapped_column(Float)
    latest_score_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ────────────────────────────────────────────────────────────────────
#  2 · KeywordDemandSignal · Ahrefs Keywords Explorer output
# ────────────────────────────────────────────────────────────────────


class KeywordDemandSignal(Base, TimestampMixin):
    __tablename__ = "keyword_demand_signals"

    id: Mapped[uuid.UUID] = uuid_pk()
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="AHREFS")
    keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(8))
    monthly_search_volume: Mapped[int | None] = mapped_column(Integer)
    keyword_difficulty: Mapped[int | None] = mapped_column(Integer)
    clicks_per_search: Mapped[float | None] = mapped_column(Float)
    cpc_usd: Mapped[float | None] = mapped_column(Numeric(10, 2))
    volume_trend: Mapped[KeywordSearchVolumeTrend] = mapped_column(
        Enum(KeywordSearchVolumeTrend, name="keyword_search_volume_trend_enum"),
        nullable=False,
        default=KeywordSearchVolumeTrend.UNKNOWN,
    )
    trend_growth_pct: Mapped[float | None] = mapped_column(Float)
    volume_history_json: Mapped[list | None] = mapped_column(JSONB)
    serp_snapshot_json: Mapped[dict | None] = mapped_column(JSONB)
    signal_class: Mapped[SignalClass] = mapped_column(
        Enum(SignalClass, name="signal_class_enum"),
        nullable=False,
        default=SignalClass.SEARCH_DEMAND_SIGNAL,
    )
    raw_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ────────────────────────────────────────────────────────────────────
#  3 · ShoppingPopularitySignal · Google Merchant Center Best Sellers
# ────────────────────────────────────────────────────────────────────


class ShoppingPopularitySignal(Base, TimestampMixin):
    __tablename__ = "shopping_popularity_signals"

    id: Mapped[uuid.UUID] = uuid_pk()
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(64), nullable=False, default="GOOGLE_MERCHANT_CENTER"
    )
    google_product_category: Mapped[str | None] = mapped_column(String(255))
    product_title_observed: Mapped[str | None] = mapped_column(Text)
    brand_observed: Mapped[str | None] = mapped_column(String(255))
    rank_in_category: Mapped[int | None] = mapped_column(Integer)
    popularity_band: Mapped[str | None] = mapped_column(String(32))
    country: Mapped[str | None] = mapped_column(String(8))
    connected_merchant_carries: Mapped[bool | None] = mapped_column(Boolean)
    signal_class: Mapped[SignalClass] = mapped_column(
        Enum(SignalClass, name="signal_class_enum"),
        nullable=False,
        default=SignalClass.GOOGLE_SHOPPING_POPULARITY,
    )
    raw_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ────────────────────────────────────────────────────────────────────
#  4 · SocialTrendSignal · TikTok Creative Center Top Products
# ────────────────────────────────────────────────────────────────────


class SocialTrendSignal(Base, TimestampMixin):
    __tablename__ = "social_trend_signals"

    id: Mapped[uuid.UUID] = uuid_pk()
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(64), nullable=False, default="TIKTOK_CREATIVE_CENTER"
    )
    product_title_observed: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(String(64))
    ad_creative_count: Mapped[int | None] = mapped_column(Integer)
    audience_signal_summary: Mapped[str | None] = mapped_column(Text)
    momentum_score: Mapped[float | None] = mapped_column(Float)
    related_videos_json: Mapped[list | None] = mapped_column(JSONB)
    signal_class: Mapped[SignalClass] = mapped_column(
        Enum(SignalClass, name="signal_class_enum"),
        nullable=False,
        default=SignalClass.SOCIAL_COMMERCE_TREND_SIGNAL,
    )
    raw_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ────────────────────────────────────────────────────────────────────
#  5 · StoreIntelligenceObservation · Similarweb-style estimates
# ────────────────────────────────────────────────────────────────────


class StoreIntelligenceObservation(Base, TimestampMixin):
    __tablename__ = "store_intelligence_observations"

    id: Mapped[uuid.UUID] = uuid_pk()
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_opportunities.id", ondelete="SET NULL"),
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(64), nullable=False, default="SIMILARWEB"
    )
    store_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    store_name: Mapped[str | None] = mapped_column(String(255))
    category_overlap: Mapped[str | None] = mapped_column(String(255))
    estimated_monthly_visits: Mapped[int | None] = mapped_column(Integer)
    estimated_conversion_rate: Mapped[float | None] = mapped_column(Float)
    estimated_monthly_revenue_band: Mapped[str | None] = mapped_column(String(64))
    competitive_rank: Mapped[int | None] = mapped_column(Integer)
    estimate_basis: Mapped[str | None] = mapped_column(Text)
    signal_class: Mapped[SignalClass] = mapped_column(
        Enum(SignalClass, name="signal_class_enum"),
        nullable=False,
        default=SignalClass.RETAIL_INTELLIGENCE_ESTIMATE,
    )
    raw_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ────────────────────────────────────────────────────────────────────
#  6 · MarketplaceSalesResearch · eBay Product Research (analyst-reviewed)
# ────────────────────────────────────────────────────────────────────


class MarketplaceSalesResearch(Base, TimestampMixin):
    __tablename__ = "marketplace_sales_researches"

    id: Mapped[uuid.UUID] = uuid_pk()
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(64), nullable=False, default="EBAY_PRODUCT_RESEARCH"
    )
    research_query: Mapped[str] = mapped_column(String(255), nullable=False)
    lookback_days: Mapped[int | None] = mapped_column(Integer)
    average_sold_price_usd: Mapped[float | None] = mapped_column(Numeric(14, 2))
    sold_price_band_min_usd: Mapped[float | None] = mapped_column(Numeric(14, 2))
    sold_price_band_max_usd: Mapped[float | None] = mapped_column(Numeric(14, 2))
    sales_trend_summary: Mapped[str | None] = mapped_column(Text)
    units_sold_estimate: Mapped[int | None] = mapped_column(Integer)
    analyst_review_status: Mapped[str] = mapped_column(
        String(64), nullable=False, default="ANALYST_REVIEW_REQUIRED"
    )
    analyst_notes: Mapped[str | None] = mapped_column(Text)
    rights_status: Mapped[str] = mapped_column(
        String(64), nullable=False, default="EBAY_SELLER_TOOLING_ONLY"
    )
    signal_class: Mapped[SignalClass] = mapped_column(
        Enum(SignalClass, name="signal_class_enum"),
        nullable=False,
        default=SignalClass.MARKETPLACE_SOLD_RESEARCH,
    )
    raw_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ────────────────────────────────────────────────────────────────────
#  7 · SupplierCandidate · sourcing feasibility per opportunity
# ────────────────────────────────────────────────────────────────────


class SupplierCandidate(Base, TimestampMixin):
    __tablename__ = "supplier_candidates"

    id: Mapped[uuid.UUID] = uuid_pk()
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_url: Mapped[str | None] = mapped_column(String(500))
    landed_cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 2))
    minimum_order_quantity: Mapped[int | None] = mapped_column(Integer)
    estimated_lead_time_days: Mapped[int | None] = mapped_column(Integer)
    shipping_burden_summary: Mapped[str | None] = mapped_column(Text)
    feasibility: Mapped[SupplierFeasibility] = mapped_column(
        Enum(SupplierFeasibility, name="supplier_feasibility_enum"),
        nullable=False,
        default=SupplierFeasibility.NOT_REVIEWED,
    )
    review_notes: Mapped[str | None] = mapped_column(Text)


# ────────────────────────────────────────────────────────────────────
#  8 · MarginScenario · what the client could actually make
# ────────────────────────────────────────────────────────────────────


class MarginScenario(Base, TimestampMixin):
    __tablename__ = "margin_scenarios"

    id: Mapped[uuid.UUID] = uuid_pk()
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    supplier_candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier_candidates.id", ondelete="SET NULL")
    )
    scenario_label: Mapped[str] = mapped_column(String(120), nullable=False)
    target_retail_price_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    landed_cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 2))
    platform_fee_pct: Mapped[float | None] = mapped_column(Float)
    shipping_cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 2))
    return_rate_estimate_pct: Mapped[float | None] = mapped_column(Float)
    gross_margin_per_unit_usd: Mapped[float | None] = mapped_column(Numeric(10, 2))
    gross_margin_pct: Mapped[float | None] = mapped_column(Float)
    assumptions_json: Mapped[dict | None] = mapped_column(JSONB)


# ────────────────────────────────────────────────────────────────────
#  9 · ConnectedStoreOutcome · the only confirmed-sale signal class
# ────────────────────────────────────────────────────────────────────


class ConnectedStoreOutcome(Base, TimestampMixin):
    __tablename__ = "connected_store_outcomes"

    id: Mapped[uuid.UUID] = uuid_pk()
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_opportunities.id", ondelete="SET NULL"),
        index=True,
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL")
    )
    provider: Mapped[ConnectedStoreProvider] = mapped_column(
        Enum(ConnectedStoreProvider, name="connected_store_provider_enum"),
        nullable=False,
    )
    store_domain: Mapped[str | None] = mapped_column(String(255))
    product_handle: Mapped[str | None] = mapped_column(String(255))
    units_sold: Mapped[int | None] = mapped_column(Integer)
    gross_revenue_usd: Mapped[float | None] = mapped_column(Numeric(14, 2))
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rights_status: Mapped[str] = mapped_column(
        String(64), nullable=False, default="PERMISSIONED_CLIENT_OWNED"
    )
    signal_class: Mapped[SignalClass] = mapped_column(
        Enum(SignalClass, name="signal_class_enum"),
        nullable=False,
        default=SignalClass.PERMISSIONED_CONNECTED_SALE,
    )
    raw_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )


# ────────────────────────────────────────────────────────────────────
#  10 · OpportunityScoreReceipt · the deterministic, auditable score
# ────────────────────────────────────────────────────────────────────


class OpportunityScoreReceipt(Base, TimestampMixin):
    __tablename__ = "opportunity_score_receipts"

    id: Mapped[uuid.UUID] = uuid_pk()
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1")
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    component_breakdown_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    competition_level: Mapped[CompetitionLevel] = mapped_column(
        Enum(CompetitionLevel, name="competition_level_enum"),
        nullable=False,
        default=CompetitionLevel.UNKNOWN,
    )
    policy_risk_flag: Mapped[PolicyRiskFlag] = mapped_column(
        Enum(PolicyRiskFlag, name="policy_risk_flag_enum"),
        nullable=False,
        default=PolicyRiskFlag.NONE,
    )
    signals_used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmed_sale_signals_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recommendation: Mapped[OpportunityRecommendation] = mapped_column(
        Enum(OpportunityRecommendation, name="opportunity_recommendation_enum"),
        nullable=False,
        default=OpportunityRecommendation.GATHER_MORE_SIGNALS,
    )
    receipt_sha256: Mapped[str | None] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text)


# ────────────────────────────────────────────────────────────────────
#  11 · BrandWatchlist · brand-level entity tracked for ProductRadar
# ────────────────────────────────────────────────────────────────────


class BrandWatchlist(Base, TimestampMixin):
    __tablename__ = "brand_watchlists"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    merchandising_lane: Mapped[MerchandisingLane] = mapped_column(
        Enum(MerchandisingLane, name="merchandising_lane_enum"),
        nullable=False,
        default=MerchandisingLane.OTHER,
    )
    priority_tier: Mapped[BrandPriorityTier] = mapped_column(
        Enum(BrandPriorityTier, name="brand_priority_tier_enum"),
        nullable=False,
        default=BrandPriorityTier.B,
    )
    sourcing_status: Mapped[BrandSourcingStatus] = mapped_column(
        Enum(BrandSourcingStatus, name="brand_sourcing_status_enum"),
        nullable=False,
        default=BrandSourcingStatus.NOT_REVIEWED,
    )
    # Reuses existing policy_risk_flag_enum from ProductRadar.
    policy_risk_flag: Mapped[PolicyRiskFlag] = mapped_column(
        Enum(PolicyRiskFlag, name="policy_risk_flag_enum"),
        nullable=False,
        default=PolicyRiskFlag.NONE,
    )
    notes: Mapped[str | None] = mapped_column(Text)


# ────────────────────────────────────────────────────────────────────
#  12 · BrandPlacementSignal · one Brand Outlet observation per brand
# ────────────────────────────────────────────────────────────────────


class BrandPlacementSignal(Base, TimestampMixin):
    __tablename__ = "brand_placement_signals"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_watchlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_watchlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_opportunities.id", ondelete="SET NULL"),
        index=True,
    )
    source_provider: Mapped[str] = mapped_column(
        String(64), nullable=False, default="EBAY_BRAND_OUTLET"
    )
    marketplace: Mapped[str] = mapped_column(String(32), nullable=False, default="EBAY_US")
    merchandising_lane: Mapped[MerchandisingLane] = mapped_column(
        Enum(MerchandisingLane, name="merchandising_lane_enum"),
        nullable=False,
        default=MerchandisingLane.OTHER,
    )
    promotional_language: Mapped[str | None] = mapped_column(Text)
    signal_status: Mapped[str] = mapped_column(
        String(64), nullable=False, default="MERCHANDISED_BRAND_WATCHLIST"
    )
    # DOCTRINE GUARDS · these must stay False on this signal class
    # forever. The service-layer ingester refuses to set them to True.
    sales_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    supplier_authorization_confirmed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    rights_status: Mapped[str] = mapped_column(
        String(64), nullable=False, default="INTERNAL_RESEARCH_ONLY"
    )
    training_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    signal_class: Mapped[SignalClass] = mapped_column(
        Enum(SignalClass, name="signal_class_enum"),
        nullable=False,
        default=SignalClass.BRANDED_COMMERCE_PLACEMENT,
    )
    recommended_next_steps_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    raw_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_registry.id", ondelete="SET NULL")
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


__all__ = [
    # enums
    "SignalClass",
    "OpportunityStatus",
    "ProductCategory",
    "OpportunityRecommendation",
    "KeywordSearchVolumeTrend",
    "CompetitionLevel",
    "SupplierFeasibility",
    "PolicyRiskFlag",
    "ConnectedStoreProvider",
    "BrandPriorityTier",
    "BrandSourcingStatus",
    "MerchandisingLane",
    # models
    "ProductOpportunity",
    "KeywordDemandSignal",
    "ShoppingPopularitySignal",
    "SocialTrendSignal",
    "StoreIntelligenceObservation",
    "MarketplaceSalesResearch",
    "SupplierCandidate",
    "MarginScenario",
    "ConnectedStoreOutcome",
    "OpportunityScoreReceipt",
    "BrandWatchlist",
    "BrandPlacementSignal",
]
