"""ProductRadar doctrine boundary tests.

Pure-Python checks for the signal-class doctrine, the weighted
scoring formula, and the confirmed-sale-aggregation refusal.
"""
import pytest

from app.models.productradar import (
    CompetitionLevel,
    OpportunityRecommendation,
    OpportunityStatus,
    PolicyRiskFlag,
    ProductCategory,
    ProductOpportunity,
    SignalClass,
)
from app.services.productradar import (
    CONFIRMED_SALE_SIGNAL_CLASSES,
    OpportunityScore,
    ProductRadarError,
    SCORING_VERSION,
    WEIGHTS,
    _score_brand_creative_fit,
    _score_policy_risk_inverted,
    _score_search_demand,
    _score_social_trend,
    assert_launch_ready_safe,
    assert_no_confirmed_sale_aggregation,
)
from app.services.connector_registry import CONNECTOR_DEFINITIONS, resolve_status
from app.models.goods import ProviderName, ProviderStatus


# ════════════════════════════════════════════════════════════════════
# Signal class enum + confirmed-sale class set
# ════════════════════════════════════════════════════════════════════


def test_signal_class_enum_complete():
    assert SignalClass.SEARCH_DEMAND_SIGNAL.value == "SEARCH_DEMAND_SIGNAL"
    assert SignalClass.SOCIAL_COMMERCE_TREND_SIGNAL.value == "SOCIAL_COMMERCE_TREND_SIGNAL"
    assert SignalClass.GOOGLE_SHOPPING_POPULARITY.value == "GOOGLE_SHOPPING_POPULARITY"
    assert SignalClass.RETAIL_INTELLIGENCE_ESTIMATE.value == "RETAIL_INTELLIGENCE_ESTIMATE"
    assert SignalClass.MARKETPLACE_SOLD_RESEARCH.value == "MARKETPLACE_SOLD_RESEARCH"
    assert SignalClass.PERMISSIONED_CONNECTED_SALE.value == "PERMISSIONED_CONNECTED_SALE"
    assert SignalClass.FIRST_PARTY_DEFENDABLE_SALE.value == "FIRST_PARTY_DEFENDABLE_SALE"


def test_only_two_classes_count_as_confirmed_sale():
    """Doctrine · confirmed-sale set is locked at exactly 2 classes."""
    assert CONFIRMED_SALE_SIGNAL_CLASSES == {
        SignalClass.PERMISSIONED_CONNECTED_SALE,
        SignalClass.FIRST_PARTY_DEFENDABLE_SALE,
    }
    assert len(CONFIRMED_SALE_SIGNAL_CLASSES) == 2


def test_search_demand_is_not_confirmed_sale():
    assert SignalClass.SEARCH_DEMAND_SIGNAL not in CONFIRMED_SALE_SIGNAL_CLASSES


def test_social_trend_is_not_confirmed_sale():
    assert SignalClass.SOCIAL_COMMERCE_TREND_SIGNAL not in CONFIRMED_SALE_SIGNAL_CLASSES


def test_marketplace_sold_research_is_not_confirmed_sale():
    """Even eBay Product Research (analyst-reviewed) is NOT a confirmed sale ·
    only PERMISSIONED_CONNECTED_SALE / FIRST_PARTY_DEFENDABLE_SALE are."""
    assert SignalClass.MARKETPLACE_SOLD_RESEARCH not in CONFIRMED_SALE_SIGNAL_CLASSES


def test_similarweb_estimate_is_not_confirmed_sale():
    assert SignalClass.RETAIL_INTELLIGENCE_ESTIMATE not in CONFIRMED_SALE_SIGNAL_CLASSES


# ════════════════════════════════════════════════════════════════════
# Weights · doctrine constant
# ════════════════════════════════════════════════════════════════════


def test_weights_sum_to_one():
    total = sum(WEIGHTS.values())
    assert abs(total - 1.0) < 0.001, f"Weights sum to {total}, must be 1.0"


def test_scoring_version_pinned():
    assert SCORING_VERSION == "v1"


# ════════════════════════════════════════════════════════════════════
# Component scorers · range invariants
# ════════════════════════════════════════════════════════════════════


def test_search_demand_zero_with_no_signals():
    assert _score_search_demand([]) == 0.0


def test_social_trend_zero_with_no_signals():
    assert _score_social_trend([]) == 0.0


def test_brand_creative_fit_in_range_for_all_categories():
    for cat in ProductCategory:
        opp = ProductOpportunity(
            opportunity_id="OPP-FAKE",
            product_name="Fake",
            canonical_search_query="fake",
            category=cat,
        )
        score = _score_brand_creative_fit(opp)
        assert 0.0 <= score <= 1.0


def test_policy_risk_inverted_rejected_returns_zero():
    assert _score_policy_risk_inverted(PolicyRiskFlag.REJECTED) == 0.0


def test_policy_risk_inverted_none_returns_one():
    assert _score_policy_risk_inverted(PolicyRiskFlag.NONE) == 1.0


# ════════════════════════════════════════════════════════════════════
# Doctrine refusals
# ════════════════════════════════════════════════════════════════════


def test_assert_launch_ready_refuses_no_confirmed_sale():
    """LAUNCH_READY without confirmed sale signals must raise."""
    score = OpportunityScore(
        total=0.85,
        component_breakdown={},
        competition_level=CompetitionLevel.LOW,
        policy_risk_flag=PolicyRiskFlag.NONE,
        signals_used_count=10,
        confirmed_sale_signals_count=0,
        recommendation=OpportunityRecommendation.LAUNCH_READY,
    )
    with pytest.raises(ProductRadarError, match="LAUNCH_READY recommendation requires"):
        assert_launch_ready_safe(score)


def test_assert_launch_ready_accepts_with_confirmed_sale():
    """LAUNCH_READY with at least one confirmed sale signal is allowed."""
    score = OpportunityScore(
        total=0.85,
        component_breakdown={},
        competition_level=CompetitionLevel.LOW,
        policy_risk_flag=PolicyRiskFlag.NONE,
        signals_used_count=11,
        confirmed_sale_signals_count=1,
        recommendation=OpportunityRecommendation.LAUNCH_READY,
    )
    # Does not raise
    assert_launch_ready_safe(score)


def test_assert_no_confirmed_sale_aggregation_refuses_mixed():
    """Aggregating only non-confirmed signal classes can never imply
    a confirmed-sale claim."""
    classes = [
        SignalClass.SEARCH_DEMAND_SIGNAL,
        SignalClass.SOCIAL_COMMERCE_TREND_SIGNAL,
        SignalClass.MARKETPLACE_SOLD_RESEARCH,
    ]
    with pytest.raises(ProductRadarError, match="refuse to derive a confirmed-sale claim"):
        assert_no_confirmed_sale_aggregation(classes)


def test_assert_no_confirmed_sale_aggregation_allows_confirmed():
    """Once a PERMISSIONED_CONNECTED_SALE is in the mix, aggregation is OK."""
    classes = [
        SignalClass.SEARCH_DEMAND_SIGNAL,
        SignalClass.PERMISSIONED_CONNECTED_SALE,
    ]
    # Does not raise
    assert_no_confirmed_sale_aggregation(classes)


# ════════════════════════════════════════════════════════════════════
# Schema defaults
# ════════════════════════════════════════════════════════════════════


def test_product_opportunity_default_status_is_watchlist():
    col = ProductOpportunity.__table__.c.status
    assert col.default.arg == OpportunityStatus.WATCHLIST


def test_product_opportunity_default_category_is_other():
    col = ProductOpportunity.__table__.c.category
    assert col.default.arg == ProductCategory.OTHER


# ════════════════════════════════════════════════════════════════════
# Connector registry · 15 connectors (8 prior + 7 new)
# ════════════════════════════════════════════════════════════════════


def test_connector_definitions_count_now_fifteen():
    """8 → 15 connectors · 7 new ProductRadar entries."""
    assert len(CONNECTOR_DEFINITIONS) == 15
    names = {d["provider_name"] for d in CONNECTOR_DEFINITIONS}
    assert ProviderName.AHREFS_KEYWORDS_EXPLORER in names
    assert ProviderName.GOOGLE_MERCHANT_CENTER_BEST_SELLERS in names
    assert ProviderName.TIKTOK_CREATIVE_CENTER in names
    assert ProviderName.EBAY_PRODUCT_RESEARCH in names
    assert ProviderName.SIMILARWEB_SHOPPER_INTELLIGENCE in names
    assert ProviderName.CONNECTED_SHOPIFY_STORE in names
    assert ProviderName.SUPPLIER_CATALOG_FUTURE in names


def test_supplier_catalog_is_future_disabled():
    assert resolve_status(ProviderName.SUPPLIER_CATALOG_FUTURE) == ProviderStatus.FUTURE_DISABLED


def test_connected_shopify_store_is_ready():
    """The only ProductRadar connector that's READY by default · once a
    client connects a store, the platform can receive permissioned
    completed-sale records (PERMISSIONED_CONNECTED_SALE signal class)."""
    assert resolve_status(ProviderName.CONNECTED_SHOPIFY_STORE) == ProviderStatus.READY


def test_ahrefs_is_not_configured_until_keys_added():
    assert resolve_status(ProviderName.AHREFS_KEYWORDS_EXPLORER) == ProviderStatus.NOT_CONFIGURED


def test_similarweb_is_not_configured():
    assert resolve_status(ProviderName.SIMILARWEB_SHOPPER_INTELLIGENCE) == ProviderStatus.NOT_CONFIGURED
