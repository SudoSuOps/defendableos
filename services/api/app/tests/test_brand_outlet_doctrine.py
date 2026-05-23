"""Brand Outlet · BRANDED_COMMERCE_PLACEMENT doctrine boundary tests."""
import pytest

from app.models.goods import ProviderName, ProviderStatus
from app.models.productradar import (
    BrandPlacementSignal,
    BrandPriorityTier,
    BrandSourcingStatus,
    BrandWatchlist,
    MerchandisingLane,
    SignalClass,
)
from app.services.connector_registry import resolve_status
from app.services.productradar import (
    CONFIRMED_SALE_SIGNAL_CLASSES,
    ProductRadarError,
    assert_brand_placement_signal_safe,
    assert_no_confirmed_sale_aggregation,
)


# ════════════════════════════════════════════════════════════════════
# Enum + connector registration
# ════════════════════════════════════════════════════════════════════


def test_branded_commerce_placement_in_signal_class_enum():
    assert SignalClass.BRANDED_COMMERCE_PLACEMENT.value == "BRANDED_COMMERCE_PLACEMENT"


def test_brand_outlet_provider_registered():
    assert ProviderName.EBAY_BRAND_OUTLET.value == "EBAY_BRAND_OUTLET"


def test_brand_outlet_connector_is_ready():
    """Manual analyst-workflow source · no API key required · READY by default."""
    assert resolve_status(ProviderName.EBAY_BRAND_OUTLET) == ProviderStatus.READY


def test_brand_placement_is_not_confirmed_sale():
    """Doctrine · Brand Outlet placement is NEVER a confirmed sale class."""
    assert SignalClass.BRANDED_COMMERCE_PLACEMENT not in CONFIRMED_SALE_SIGNAL_CLASSES


# ════════════════════════════════════════════════════════════════════
# Schema defaults · BrandWatchlist + BrandPlacementSignal
# ════════════════════════════════════════════════════════════════════


def test_brand_watchlist_default_sourcing_is_not_reviewed():
    """No brand starts with claimed supply · NOT_REVIEWED default."""
    col = BrandWatchlist.__table__.c.sourcing_status
    assert col.default.arg == BrandSourcingStatus.NOT_REVIEWED


def test_brand_watchlist_default_priority_is_b():
    """Default priority B · explicit A/DEFER requires operator decision."""
    col = BrandWatchlist.__table__.c.priority_tier
    assert col.default.arg == BrandPriorityTier.B


def test_brand_placement_signal_default_sales_confirmed_false():
    col = BrandPlacementSignal.__table__.c.sales_confirmed
    default = col.default.arg
    assert default is False or str(default).lower() in {"false", "f", "0"}


def test_brand_placement_signal_default_supplier_authorization_false():
    col = BrandPlacementSignal.__table__.c.supplier_authorization_confirmed
    default = col.default.arg
    assert default is False or str(default).lower() in {"false", "f", "0"}


def test_brand_placement_signal_default_training_eligible_false():
    col = BrandPlacementSignal.__table__.c.training_eligible
    default = col.default.arg
    assert default is False or str(default).lower() in {"false", "f", "0"}


def test_brand_placement_signal_default_class_is_branded_commerce_placement():
    col = BrandPlacementSignal.__table__.c.signal_class
    assert col.default.arg == SignalClass.BRANDED_COMMERCE_PLACEMENT


# ════════════════════════════════════════════════════════════════════
# Service-boundary doctrine refusals
# ════════════════════════════════════════════════════════════════════


def test_brand_placement_refuses_sales_confirmed_true():
    """Brand Outlet placement may NEVER claim sales_confirmed=True."""
    with pytest.raises(ProductRadarError, match="sales_confirmed=False"):
        assert_brand_placement_signal_safe(
            sales_confirmed=True,
            supplier_authorization_confirmed=False,
            signal_class=SignalClass.BRANDED_COMMERCE_PLACEMENT,
        )


def test_brand_placement_refuses_supplier_authorization_true():
    """Brand Outlet placement may NEVER claim supplier authorization."""
    with pytest.raises(ProductRadarError, match="supplier_authorization_confirmed=False"):
        assert_brand_placement_signal_safe(
            sales_confirmed=False,
            supplier_authorization_confirmed=True,
            signal_class=SignalClass.BRANDED_COMMERCE_PLACEMENT,
        )


def test_brand_placement_accepts_both_false():
    """Happy path · doctrine-safe defaults pass through."""
    # Does not raise
    assert_brand_placement_signal_safe(
        sales_confirmed=False,
        supplier_authorization_confirmed=False,
        signal_class=SignalClass.BRANDED_COMMERCE_PLACEMENT,
    )


def test_assert_aggregation_refuses_brand_placement_alone():
    """A signal set containing ONLY brand placements cannot derive
    a confirmed-sale claim."""
    with pytest.raises(ProductRadarError, match="refuse to derive a confirmed-sale claim"):
        assert_no_confirmed_sale_aggregation([
            SignalClass.BRANDED_COMMERCE_PLACEMENT,
            SignalClass.SEARCH_DEMAND_SIGNAL,
        ])


# ════════════════════════════════════════════════════════════════════
# Connector count · 15 → 16
# ════════════════════════════════════════════════════════════════════


def test_brand_outlet_in_connector_definitions():
    from app.services.connector_registry import CONNECTOR_DEFINITIONS
    names = {d["provider_name"] for d in CONNECTOR_DEFINITIONS}
    assert ProviderName.EBAY_BRAND_OUTLET in names
    # Connector count grows over time as new lanes land · just assert
    # the EBAY_BRAND_OUTLET registration and a sensible minimum.
    assert len(CONNECTOR_DEFINITIONS) >= 16


# ════════════════════════════════════════════════════════════════════
# Merchandising lane enum · matches eBay's surfaces
# ════════════════════════════════════════════════════════════════════


def test_merchandising_lanes_cover_ebay_surfaces():
    lanes = {m.value for m in MerchandisingLane}
    assert "ELITE_TECH" in lanes
    assert "LATEST_TECH" in lanes
    assert "HOME_POWER_EQUIPMENT" in lanes
    assert "TOOLS_EQUIPMENT" in lanes
    assert "LUXURY_HANDBAGS" in lanes
    assert "LUXURY_WATCHES_JEWELRY" in lanes
    assert "REFURBISHED_ELECTRONICS" in lanes


def test_luxury_brands_should_be_deferred_by_doctrine():
    """The seed places luxury brands at DEFER · this is the doctrine,
    not optional. Test asserts the enum allows DEFER as a first-class
    priority tier so the seed can express it."""
    assert BrandPriorityTier.DEFER.value == "DEFER"
