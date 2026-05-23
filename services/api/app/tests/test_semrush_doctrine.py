"""Semrush · ProductRadar competitive-intelligence rail doctrine tests."""
import os

import pytest

from app.models.goods import ProviderName, ProviderStatus
from app.models.productradar import (
    EcommerceProductClickSignal,
    SignalClass,
)
from app.services.connector_registry import (
    CONNECTOR_DEFINITIONS,
    resolve_status,
    _semrush_status,
)
from app.services.productradar import (
    CONFIRMED_SALE_SIGNAL_CLASSES,
    ProductRadarError,
    assert_no_confirmed_sale_aggregation,
    assert_semrush_signal_safe,
)


# ════════════════════════════════════════════════════════════════════
# Enum + connector registration
# ════════════════════════════════════════════════════════════════════


def test_semrush_provider_registered():
    assert ProviderName.SEMRUSH.value == "SEMRUSH"


def test_plan_verification_required_status_exists():
    assert ProviderStatus.PLAN_VERIFICATION_REQUIRED.value == "PLAN_VERIFICATION_REQUIRED"


def test_ecommerce_product_click_signal_in_enum():
    assert SignalClass.ECOMMERCE_PRODUCT_CLICK_SIGNAL.value == "ECOMMERCE_PRODUCT_CLICK_SIGNAL"


def test_competitor_visibility_signal_in_enum():
    assert SignalClass.COMPETITOR_VISIBILITY_SIGNAL.value == "COMPETITOR_VISIBILITY_SIGNAL"


def test_semrush_in_connector_definitions():
    names = {d["provider_name"] for d in CONNECTOR_DEFINITIONS}
    assert ProviderName.SEMRUSH in names


# ════════════════════════════════════════════════════════════════════
# Semrush is NEVER a confirmed-sale class
# ════════════════════════════════════════════════════════════════════


def test_ecommerce_product_click_is_not_confirmed_sale():
    """Even product clicks · which are richer than search volume · are
    NOT confirmed sales. Only PERMISSIONED_CONNECTED_SALE +
    FIRST_PARTY_DEFENDABLE_SALE qualify."""
    assert SignalClass.ECOMMERCE_PRODUCT_CLICK_SIGNAL not in CONFIRMED_SALE_SIGNAL_CLASSES


def test_competitor_visibility_is_not_confirmed_sale():
    assert SignalClass.COMPETITOR_VISIBILITY_SIGNAL not in CONFIRMED_SALE_SIGNAL_CLASSES


# ════════════════════════════════════════════════════════════════════
# EcommerceProductClickSignal · schema defaults
# ════════════════════════════════════════════════════════════════════


def test_click_signal_default_sales_confirmed_false():
    col = EcommerceProductClickSignal.__table__.c.sales_confirmed
    default = col.default.arg
    assert default is False or str(default).lower() in {"false", "f", "0"}


def test_click_signal_default_training_eligible_false():
    col = EcommerceProductClickSignal.__table__.c.training_eligible
    default = col.default.arg
    assert default is False or str(default).lower() in {"false", "f", "0"}


def test_click_signal_default_signal_class_is_ecommerce_click():
    col = EcommerceProductClickSignal.__table__.c.signal_class
    assert col.default.arg == SignalClass.ECOMMERCE_PRODUCT_CLICK_SIGNAL


def test_click_signal_default_provider_is_semrush():
    col = EcommerceProductClickSignal.__table__.c.provider
    assert col.default.arg == "SEMRUSH"


# ════════════════════════════════════════════════════════════════════
# Service-boundary refusals
# ════════════════════════════════════════════════════════════════════


def test_semrush_search_demand_refuses_sales_confirmed():
    with pytest.raises(ProductRadarError, match="MUST have sales_confirmed=False"):
        assert_semrush_signal_safe(
            sales_confirmed=True,
            signal_class=SignalClass.SEARCH_DEMAND_SIGNAL,
        )


def test_semrush_ecommerce_click_refuses_sales_confirmed():
    with pytest.raises(ProductRadarError, match="ECOMMERCE_PRODUCT_CLICK_SIGNAL"):
        assert_semrush_signal_safe(
            sales_confirmed=True,
            signal_class=SignalClass.ECOMMERCE_PRODUCT_CLICK_SIGNAL,
        )


def test_semrush_competitor_visibility_refuses_sales_confirmed():
    with pytest.raises(ProductRadarError, match="COMPETITOR_VISIBILITY_SIGNAL"):
        assert_semrush_signal_safe(
            sales_confirmed=True,
            signal_class=SignalClass.COMPETITOR_VISIBILITY_SIGNAL,
        )


def test_semrush_retail_intelligence_refuses_sales_confirmed():
    with pytest.raises(ProductRadarError, match="RETAIL_INTELLIGENCE_ESTIMATE"):
        assert_semrush_signal_safe(
            sales_confirmed=True,
            signal_class=SignalClass.RETAIL_INTELLIGENCE_ESTIMATE,
        )


def test_semrush_guard_accepts_sales_confirmed_false():
    """Happy path · default-safe value passes through."""
    # Does not raise
    assert_semrush_signal_safe(
        sales_confirmed=False,
        signal_class=SignalClass.ECOMMERCE_PRODUCT_CLICK_SIGNAL,
    )


def test_semrush_guard_ignores_non_semrush_classes():
    """Semrush guard does NOT apply to confirmed-sale classes · their
    own dedicated paths handle them."""
    # Does not raise even though sales_confirmed=True · the
    # PERMISSIONED_CONNECTED_SALE class has its own write path.
    assert_semrush_signal_safe(
        sales_confirmed=True,
        signal_class=SignalClass.PERMISSIONED_CONNECTED_SALE,
    )


def test_aggregation_refuses_semrush_only_signal_set():
    """A signal set of only Semrush-class signals cannot derive a
    confirmed-sale claim."""
    with pytest.raises(ProductRadarError, match="refuse to derive a confirmed-sale claim"):
        assert_no_confirmed_sale_aggregation([
            SignalClass.SEARCH_DEMAND_SIGNAL,
            SignalClass.ECOMMERCE_PRODUCT_CLICK_SIGNAL,
            SignalClass.COMPETITOR_VISIBILITY_SIGNAL,
        ])


# ════════════════════════════════════════════════════════════════════
# Connector status state machine
# ════════════════════════════════════════════════════════════════════


def _set_env(**kwargs):
    """Helper · returns a context-manager-like restore dict."""
    saved = {}
    for k, v in kwargs.items():
        saved[k] = os.environ.get(k)
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    return saved


def _restore_env(saved):
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_semrush_no_key_is_not_configured():
    """Status helper checks settings · settings reads env at import time.
    We verify the helper logic by direct invocation when the import-time
    settings reflect no key (which is the test default · CI runs without
    SEMRUSH_API_KEY)."""
    # In test env SEMRUSH_API_KEY is empty by default.
    from app.core.config import settings
    assert settings.semrush_api_key == ""
    assert _semrush_status() == ProviderStatus.NOT_CONFIGURED


def test_resolve_status_for_semrush():
    """resolve_status delegates to the same helper."""
    assert resolve_status(ProviderName.SEMRUSH) == ProviderStatus.NOT_CONFIGURED


# ════════════════════════════════════════════════════════════════════
# Settings · all 9 Semrush env vars present
# ════════════════════════════════════════════════════════════════════


def test_semrush_settings_present():
    from app.core.config import settings
    assert hasattr(settings, "semrush_api_key")
    assert hasattr(settings, "semrush_live_calls_enabled")
    assert hasattr(settings, "semrush_max_calls_per_run")
    assert hasattr(settings, "semrush_seo_api_enabled")
    assert hasattr(settings, "semrush_trends_api_enabled")
    assert hasattr(settings, "semrush_ecommerce_keyword_analytics_enabled")
    assert hasattr(settings, "semrush_rights_status")
    assert hasattr(settings, "semrush_data_use")
    assert hasattr(settings, "semrush_model_training_export_enabled")


def test_semrush_all_live_flags_default_false():
    from app.core.config import settings
    assert settings.semrush_live_calls_enabled is False
    assert settings.semrush_seo_api_enabled is False
    assert settings.semrush_trends_api_enabled is False
    assert settings.semrush_ecommerce_keyword_analytics_enabled is False
    assert settings.semrush_model_training_export_enabled is False


def test_semrush_default_rights_status_is_terms_review_pending():
    from app.core.config import settings
    assert settings.semrush_rights_status == "TERMS_REVIEW_PENDING"
