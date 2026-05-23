"""Compute Market Watch · sold-comp tribunal + ingest tests.

Covers the deterministic Tribunal rules + bakery integration.
NO live network · Insights calls mocked.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CLAW_BAKERY_STORAGE_DRIVER", "local")
    monkeypatch.setenv("CLAW_BAKERY_LOCAL_ROOT", str(tmp_path / "bakery"))
    monkeypatch.setenv("EBAY_APP_ID", "swarmbee-defendab-SBX-test")
    monkeypatch.setenv("EBAY_CERT_ID", "SBX-testcert" + "x" * 24)
    monkeypatch.setenv("EBAY_DEV_ID", "test-dev-id")
    monkeypatch.setenv("EBAY_ENVIRONMENT", "sandbox")
    monkeypatch.setenv("EBAY_MARKETPLACE_ID", "EBAY_US")
    from app.core import config
    from app.integrations.ebay import oauth
    from app.services.claw_bakery import bakery_storage
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    oauth.reset_cache_for_tests()
    bakery_storage._store = None  # noqa: SLF001
    yield
    oauth.reset_cache_for_tests()
    bakery_storage._store = None  # noqa: SLF001


# ─── Tribunal rules ───────────────────────────────────────────────────


def _sale(
    *, item_id="v1|test|0", title="NVIDIA RTX 3090 24GB",
    price="900", currency="USD", sold_date="2026-05-22T18:00:00Z",
    condition="Used", categories=None,
) -> dict:
    return {
        "itemId": item_id, "title": title,
        "lastSoldPrice": {"value": price, "currency": currency},
        "lastSoldDate": sold_date, "condition": condition,
        "categories": categories or [{"categoryId": "27386", "categoryName": "Graphics Cards"}],
        "itemWebUrl": "https://example.com/i/" + item_id,
    }


def test_tribunal_clean_rtx_3090_is_honey() -> None:
    from app.services.compute_market_watch.sold_comp_tribunal import classify, LABEL_HONEY
    v = classify(_sale())
    assert v.label == LABEL_HONEY
    assert v.failed_checks == []
    assert v.matched_sku is not None and v.matched_sku.canonical == "NVIDIA RTX 3090"
    assert v.normalized_price_usd == 900.0


def test_tribunal_rejects_zero_price_as_propolis() -> None:
    from app.services.compute_market_watch.sold_comp_tribunal import classify, LABEL_PROPOLIS
    v = classify(_sale(price="0"))
    assert v.label == LABEL_PROPOLIS
    assert any("price_zero_or_negative" in fc for fc in v.failed_checks)


def test_tribunal_rejects_missing_price_value_as_propolis() -> None:
    from app.services.compute_market_watch.sold_comp_tribunal import classify, LABEL_PROPOLIS
    sale = _sale()
    sale["lastSoldPrice"] = {"currency": "USD"}  # value missing
    v = classify(sale)
    assert v.label == LABEL_PROPOLIS


def test_tribunal_rejects_sandbox_test_marker_in_title_as_propolis() -> None:
    from app.services.compute_market_watch.sold_comp_tribunal import classify, LABEL_PROPOLIS
    v = classify(_sale(title="Drone for Promotion Test 1776960094163"))
    # Sandbox test marker triggers PROPOLIS regardless of other fields
    assert v.label == LABEL_PROPOLIS


def test_tribunal_rejects_price_above_sanity_ceiling_as_propolis() -> None:
    from app.services.compute_market_watch.sold_comp_tribunal import classify, LABEL_PROPOLIS
    v = classify(_sale(price="500000"))
    assert v.label == LABEL_PROPOLIS


def test_tribunal_downgrades_to_jelly_on_non_usd_currency() -> None:
    from app.services.compute_market_watch.sold_comp_tribunal import classify, LABEL_JELLY
    v = classify(_sale(price="800", currency="EUR"))
    assert v.label == LABEL_JELLY
    assert any("non_usd_currency_EUR" in fc for fc in v.failed_checks)


def test_tribunal_downgrades_to_jelly_when_price_outside_sku_band() -> None:
    from app.services.compute_market_watch.sold_comp_tribunal import classify, LABEL_JELLY
    # RTX 3090 band is $400-$2500 · $200 is below
    v = classify(_sale(price="200"))
    assert v.label == LABEL_JELLY
    assert any("outside_sku_band" in fc for fc in v.failed_checks)


def test_tribunal_quarantines_title_with_no_known_sku() -> None:
    from app.services.compute_market_watch.sold_comp_tribunal import classify, LABEL_QUARANTINED
    v = classify(_sale(title="Toaster Oven Model TX-9000 stainless steel"))
    assert v.label == LABEL_QUARANTINED


def test_tribunal_distinguishes_3090_from_3090_ti() -> None:
    from app.services.compute_market_watch.sold_comp_tribunal import classify, LABEL_HONEY
    v_plain = classify(_sale(title="EVGA NVIDIA GeForce RTX 3090 24GB FTW3"))
    assert v_plain.matched_sku.canonical == "NVIDIA RTX 3090"
    v_ti = classify(_sale(title="EVGA NVIDIA GeForce RTX 3090 Ti 24GB FTW3", price="1800"))
    assert v_ti.matched_sku.canonical == "NVIDIA RTX 3090 Ti"
    assert v_ti.label == LABEL_HONEY


def test_tribunal_matches_rtx_pro_6000_blackwell() -> None:
    from app.services.compute_market_watch.sold_comp_tribunal import classify, LABEL_HONEY
    v = classify(_sale(
        title="NVIDIA RTX PRO 6000 Blackwell Workstation Edition · 95GB",
        price="9500",
    ))
    assert v.matched_sku.canonical == "NVIDIA RTX PRO 6000 Blackwell"
    assert v.label == LABEL_HONEY


# ─── Ingest orchestrator with mocked Insights ────────────────────────


class _FakeInsightsResult:
    """Minimal stand-in for ItemSalesSearchResult."""
    def __init__(self, sales, environment="sandbox"):
        self.item_sales = sales
        self.environment = environment
        self.total = len(sales)


def test_ingest_dry_run_writes_no_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    """dry_run=True classifies but does NOT write artifacts."""
    from app.services.compute_market_watch import ingest
    from app.services.claw_bakery.bakery_storage import get_bakery_store

    fake_calls: list[str] = []

    def _fake_search(*, q, limit, **_kw):
        fake_calls.append(q)
        return _FakeInsightsResult([
            _sale(item_id="v1|d1|0", title="NVIDIA RTX 3090 FE", price="900"),
            _sale(item_id="v1|d2|0", title="NVIDIA RTX 3090 EVGA", price="0"),
        ])

    monkeypatch.setattr(
        "app.services.compute_market_watch.ingest.search_item_sales",
        _fake_search,
        raising=False,
    )
    # The function is imported lazily inside run · need to patch at the
    # module path where it's looked up
    import app.integrations.ebay.marketplace_insights as mi
    monkeypatch.setattr(mi, "search_item_sales", _fake_search)

    res = ingest.run_compute_sold_comp_ingest(
        sku_aliases=["RTX 3090"], limit_per_sku=5, dry_run=True,
    )
    assert res.dry_run is True
    assert res.total_processed == 2
    assert res.total_by_label["HONEY"] == 1
    assert res.total_by_label["PROPOLIS"] == 1

    # Verify NO artifacts written (dry_run)
    store = get_bakery_store()
    assert store.list_under("compute-market-watch/sold-comps") == []
    assert store.list_under("compute-market-watch/ingest-runs") == []


def test_ingest_full_run_writes_sorted_artifacts_with_receipts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Full ingest writes per-comp artifacts under the correct label bucket
    + a per-sale SHA-256 receipt + a per-run manifest."""
    from app.services.compute_market_watch import ingest
    from app.services.claw_bakery.bakery_storage import get_bakery_store

    def _fake_search(*, q, limit, **_kw):
        return _FakeInsightsResult([
            _sale(item_id="v1|honey1|0", title="NVIDIA RTX 3090 24GB", price="900"),
            _sale(item_id="v1|jelly1|0", title="NVIDIA RTX 3090 24GB", price="800", currency="GBP"),
            _sale(item_id="v1|propolis1|0", title="RTX 3090 Test Promotion", price="500"),
        ])

    import app.integrations.ebay.marketplace_insights as mi
    monkeypatch.setattr(mi, "search_item_sales", _fake_search)

    res = ingest.run_compute_sold_comp_ingest(
        sku_aliases=["RTX 3090"], limit_per_sku=10, dry_run=False,
    )
    assert res.dry_run is False
    assert res.total_processed == 3
    assert res.total_by_label["HONEY"] == 1
    assert res.total_by_label["JELLY"] == 1
    assert res.total_by_label["PROPOLIS"] == 1

    store = get_bakery_store()
    # Each comp lands in the right bucket
    honey_keys = store.list_under("compute-market-watch/sold-comps/honey")
    jelly_keys = store.list_under("compute-market-watch/sold-comps/jelly")
    propolis_keys = store.list_under("compute-market-watch/sold-comps/propolis")
    assert len(honey_keys) == 1
    assert len(jelly_keys) == 1
    assert len(propolis_keys) == 1

    # The HONEY artifact has doctrine.training_eligible_as_positive=True
    honey_envelope = json.loads(store.driver.read(honey_keys[0]).decode("utf-8"))
    assert honey_envelope["tribunal_label"] == "HONEY"
    assert honey_envelope["doctrine"]["training_eligible_as_positive"] is True
    assert honey_envelope["doctrine"]["data_class"] == "PERMISSIONED_CONNECTED_SALE"

    # The PROPOLIS artifact has training_eligible_as_positive=False
    propolis_envelope = json.loads(store.driver.read(propolis_keys[0]).decode("utf-8"))
    assert propolis_envelope["tribunal_label"] == "PROPOLIS"
    assert propolis_envelope["doctrine"]["training_eligible_as_positive"] is False

    # Per-comp receipts written (one per sale)
    receipt_keys = store.list_under("receipts/sha256")
    assert len(receipt_keys) >= 3

    # Per-run manifest written
    manifest_keys = store.list_under("compute-market-watch/ingest-runs")
    assert len(manifest_keys) == 1
    manifest = json.loads(store.driver.read(manifest_keys[0]).decode("utf-8"))
    assert manifest["rail"] == "compute_market_watch.sold_comp_ingest"
    assert manifest["total_processed"] == 3
    assert manifest["total_by_label"]["HONEY"] == 1


def test_ingest_unknown_sku_alias_records_error_skips_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An operator typo in sku_aliases must NOT trigger an eBay call."""
    from app.services.compute_market_watch import ingest

    call_count = {"n": 0}
    def _fake_search(*, q, limit, **_kw):
        call_count["n"] += 1
        return _FakeInsightsResult([])

    import app.integrations.ebay.marketplace_insights as mi
    monkeypatch.setattr(mi, "search_item_sales", _fake_search)

    res = ingest.run_compute_sold_comp_ingest(
        sku_aliases=["RTX 99999 Made Up"], limit_per_sku=5, dry_run=True,
    )
    assert call_count["n"] == 0  # never called
    assert any("unknown_sku_alias" in e for s in res.per_sku_stats for e in s.errors)


def test_ingest_admin_route_dry_run_returns_safe_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Admin route returns the safe-summary shape · no seller/raw bodies."""
    from fastapi.testclient import TestClient
    import app.integrations.ebay.marketplace_insights as mi
    from app.main import app
    from app.core import config

    monkeypatch.setenv("EBAY_ADMIN_TOKEN", "test_admin_64chars_" + "x" * 46)
    config.get_settings.cache_clear()
    config.settings = config.get_settings()

    def _fake_search(*, q, limit, **_kw):
        return _FakeInsightsResult([
            _sale(item_id="v1|admin-h|0", title="NVIDIA RTX 4090 FE", price="2000"),
        ])
    monkeypatch.setattr(mi, "search_item_sales", _fake_search)

    client = TestClient(app)
    resp = client.post(
        "/api/v1/admin/ebay/sold-comps/ingest-compute"
        "?sku_aliases=RTX%204090&limit_per_sku=1&dry_run=true",
        headers={"X-Ebay-Admin-Token": "test_admin_64chars_" + "x" * 46},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dry_run"] is True
    assert body["total_processed"] == 1
    assert body["total_by_label"]["HONEY"] == 1
    # Manifest key should be None for dry_run
    assert body["manifest_artifact_key"] is None
    # Safe summary · no raw seller / itemWebUrl details
    blob = json.dumps(body)
    assert "https://example.com" not in blob
