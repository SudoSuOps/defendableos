"""eBay OAuth + Browse + admin route tests.

All tests mock the network · no live eBay calls.
"""
from __future__ import annotations

import base64
import json
import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient


FIXTURE_APP_ID = "swarmbee-defendab-SBX-fixture123-abcdef"
FIXTURE_CERT_ID = "SBX-fixturecertabc123-fixtureghi456-fakefake"  # noqa: S105 · test fixture
FIXTURE_DEV_ID = "74766bca-0489-41ab-9b25-fixturedevid"
FIXTURE_ADMIN_TOKEN = "test_admin_token_64chars_0123456789abcdef0123456789abcdef"  # noqa: S105


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch):
    """Fresh settings + cleared token cache per test."""
    monkeypatch.setenv("EBAY_APP_ID", FIXTURE_APP_ID)
    monkeypatch.setenv("EBAY_CERT_ID", FIXTURE_CERT_ID)
    monkeypatch.setenv("EBAY_DEV_ID", FIXTURE_DEV_ID)
    monkeypatch.setenv("EBAY_ENVIRONMENT", "sandbox")
    monkeypatch.setenv("EBAY_MARKETPLACE_ID", "EBAY_US")
    monkeypatch.setenv("EBAY_ADMIN_TOKEN", FIXTURE_ADMIN_TOKEN)
    from app.core import config
    from app.integrations.ebay import oauth
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    oauth.reset_cache_for_tests()
    yield
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    oauth.reset_cache_for_tests()


class _MockResponse:
    def __init__(self, status_code: int, payload: Any, reason: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.reason_phrase = reason

    def json(self) -> Any:
        return self._payload

    @property
    def text(self) -> str:
        return json.dumps(self._payload) if not isinstance(self._payload, str) else self._payload


class _MockClient:
    """Records every request · returns scripted responses in order."""

    def __init__(self, scripted: list[_MockResponse]):
        self._scripted = list(scripted)
        self.calls: list[dict[str, Any]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def _record(self, method: str, url: str, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._scripted:
            raise AssertionError(f"unexpected extra {method} {url}")
        return self._scripted.pop(0)

    def post(self, url: str, **kwargs):
        return self._record("POST", url, **kwargs)

    def get(self, url: str, **kwargs):
        return self._record("GET", url, **kwargs)


class _MultiMockClient:
    """URL-dispatching mock · token-endpoint POSTs vs Browse GETs return
    different scripted responses. Both oauth.py and browse_api.py import
    `httpx` as the same module · a single patch site serves both."""

    def __init__(
        self,
        *,
        token_responses: list[_MockResponse],
        browse_responses: list[_MockResponse],
    ):
        self._token = list(token_responses)
        self._browse = list(browse_responses)
        self.token_calls: list[dict[str, Any]] = []
        self.browse_calls: list[dict[str, Any]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def post(self, url: str, **kwargs):
        if "/identity/v1/oauth2/token" in url:
            self.token_calls.append({"method": "POST", "url": url, **kwargs})
            if not self._token:
                raise AssertionError(f"unexpected extra token POST {url}")
            return self._token.pop(0)
        raise AssertionError(f"unexpected POST to non-token URL: {url}")

    def get(self, url: str, **kwargs):
        if "/buy/browse/v1/" in url:
            self.browse_calls.append({"method": "GET", "url": url, **kwargs})
            if not self._browse:
                raise AssertionError(f"unexpected extra browse GET {url}")
            return self._browse.pop(0)
        raise AssertionError(f"unexpected GET to non-browse URL: {url}")


# ─── OAuth token fetch ───────────────────────────────────────────────


def test_oauth_token_fetch_uses_basic_auth_with_correct_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the Authorization header is Basic base64(APP_ID:CERT_ID)."""
    from app.integrations.ebay import oauth

    mock = _MockClient([
        _MockResponse(200, {
            "access_token": "test_token_AAAA1234567890",
            "expires_in": 7200,
            "token_type": "Bearer",
        })
    ])
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: mock)

    token = oauth.get_application_token()

    # Verify the request payload
    call = mock.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
    auth_header = call["headers"]["Authorization"]
    expected = "Basic " + base64.b64encode(
        f"{FIXTURE_APP_ID}:{FIXTURE_CERT_ID}".encode("utf-8")
    ).decode("ascii")
    assert auth_header == expected
    assert call["data"]["grant_type"] == "client_credentials"
    assert call["data"]["scope"] == oauth.DEFAULT_SCOPE

    # Verify the returned token
    assert token.access_token == "test_token_AAAA1234567890"
    assert token.token_type == "Bearer"
    assert token.environment == "sandbox"
    assert token.is_fresh()


def test_oauth_token_is_cached_across_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Second call within freshness window must NOT hit the network."""
    from app.integrations.ebay import oauth

    mock = _MockClient([
        _MockResponse(200, {
            "access_token": "cached_token_xyz",
            "expires_in": 7200,
            "token_type": "Bearer",
        })
    ])
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: mock)

    a = oauth.get_application_token()
    b = oauth.get_application_token()
    assert a is b
    assert len(mock.calls) == 1


def test_oauth_token_endpoint_switches_for_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EBAY_ENVIRONMENT", "production")
    from app.core import config
    from app.integrations.ebay import oauth
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    oauth.reset_cache_for_tests()

    mock = _MockClient([
        _MockResponse(200, {
            "access_token": "prod_token", "expires_in": 7200, "token_type": "Bearer",
        })
    ])
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: mock)

    oauth.get_application_token()
    assert mock.calls[0]["url"] == "https://api.ebay.com/identity/v1/oauth2/token"


def test_oauth_raises_config_missing_when_app_id_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EBAY_APP_ID", "")
    from app.core import config
    from app.integrations.ebay import oauth
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    with pytest.raises(oauth.EbayOAuthConfigMissing):
        oauth.get_application_token()


def test_oauth_does_not_log_cert_id_or_token(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from app.integrations.ebay import oauth

    mock = _MockClient([
        _MockResponse(200, {
            "access_token": "sensitive_token_full_value_should_never_log",
            "expires_in": 7200,
            "token_type": "Bearer",
        })
    ])
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: mock)

    caplog.set_level(logging.DEBUG)
    oauth.get_application_token()

    log_blob = "\n".join(r.getMessage() for r in caplog.records)
    assert FIXTURE_CERT_ID not in log_blob
    assert "sensitive_token_full_value_should_never_log" not in log_blob


def test_oauth_readiness_returns_safe_booleans_no_secrets() -> None:
    from app.integrations.ebay.oauth import readiness_status
    r = readiness_status()
    assert r["integration"] == "ebay_oauth_client_credentials"
    assert r["app_id_configured"] is True
    assert r["cert_id_configured"] is True
    assert r["dev_id_configured"] is True
    assert r["ready_for_token_fetch"] is True
    assert r["environment"] == "sandbox"
    assert r["cached_token_count"] == 0
    assert r["cached_scopes"] == []
    # No secret bits
    blob = json.dumps(r)
    assert FIXTURE_CERT_ID not in blob


def test_oauth_per_scope_cache_is_independent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Browse and Marketplace Insights tokens must cache + refresh independently."""
    from app.integrations.ebay import oauth

    # Two scoped fetches expected · cache keyed by scope
    mock = _MockClient([
        _MockResponse(200, {"access_token": "browse_tok", "expires_in": 7200, "token_type": "Bearer"}),
        _MockResponse(200, {"access_token": "insights_tok", "expires_in": 7200, "token_type": "Bearer"}),
    ])
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: mock)

    a = oauth.get_application_token(scope=oauth.DEFAULT_SCOPE)
    b = oauth.get_application_token(scope=oauth.SCOPE_MARKETPLACE_INSIGHTS)
    # Hit again · should be cache hits · no new POSTs
    a2 = oauth.get_application_token(scope=oauth.DEFAULT_SCOPE)
    b2 = oauth.get_application_token(scope=oauth.SCOPE_MARKETPLACE_INSIGHTS)

    assert a is a2
    assert b is b2
    assert a is not b
    assert a.scope == oauth.DEFAULT_SCOPE
    assert b.scope == oauth.SCOPE_MARKETPLACE_INSIGHTS
    assert len(mock.calls) == 2  # only the two initial fetches


def test_invalidate_one_scope_keeps_others(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.integrations.ebay import oauth

    mock = _MockClient([
        _MockResponse(200, {"access_token": "browse_tok", "expires_in": 7200, "token_type": "Bearer"}),
        _MockResponse(200, {"access_token": "insights_tok", "expires_in": 7200, "token_type": "Bearer"}),
        _MockResponse(200, {"access_token": "browse_tok_2", "expires_in": 7200, "token_type": "Bearer"}),
    ])
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: mock)

    oauth.get_application_token(scope=oauth.DEFAULT_SCOPE)
    insights_tok = oauth.get_application_token(scope=oauth.SCOPE_MARKETPLACE_INSIGHTS)

    oauth.invalidate_cache(scope=oauth.DEFAULT_SCOPE)
    # Insights still cached
    assert oauth.get_application_token(scope=oauth.SCOPE_MARKETPLACE_INSIGHTS) is insights_tok
    # Browse refetched (third POST)
    oauth.get_application_token(scope=oauth.DEFAULT_SCOPE)
    assert len(mock.calls) == 3


# ─── Browse API ──────────────────────────────────────────────────────


def test_browse_search_sends_bearer_token_and_marketplace_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.integrations.ebay import oauth, browse_api

    multi = _MultiMockClient(
        token_responses=[_MockResponse(200, {
            "access_token": "tok_browse_test", "expires_in": 7200, "token_type": "Bearer",
        })],
        browse_responses=[_MockResponse(200, {
            "total": 3, "href": "..",
            "itemSummaries": [
                {"itemId": "v1|1", "title": "drone alpha", "price": {"value": "10", "currency": "USD"}},
                {"itemId": "v1|2", "title": "drone beta",  "price": {"value": "20", "currency": "USD"}},
                {"itemId": "v1|3", "title": "drone gamma", "price": {"value": "30", "currency": "USD"}},
            ],
        })],
    )
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: multi)

    result = browse_api.search_item_summaries(q="drone", limit=3)

    call = multi.browse_calls[0]
    assert call["url"].endswith("/buy/browse/v1/item_summary/search")
    assert call["headers"]["Authorization"] == "Bearer tok_browse_test"
    assert call["headers"]["X-EBAY-C-MARKETPLACE-ID"] == "EBAY_US"
    assert call["params"]["q"] == "drone"
    assert call["params"]["limit"] == 3
    assert result.total == 3
    assert len(result.item_summaries) == 3
    assert result.environment == "sandbox"


def test_browse_search_retries_once_on_401(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.integrations.ebay import oauth, browse_api

    multi = _MultiMockClient(
        # Two token fetches expected (initial + after-401 invalidation)
        token_responses=[
            _MockResponse(200, {"access_token": "first_tok", "expires_in": 7200, "token_type": "Bearer"}),
            _MockResponse(200, {"access_token": "second_tok", "expires_in": 7200, "token_type": "Bearer"}),
        ],
        # First browse call 401 · second succeeds
        browse_responses=[
            _MockResponse(401, {"errors": [{"errorId": 1100}]}, reason="Unauthorized"),
            _MockResponse(200, {"total": 1, "href": "..", "itemSummaries": [{"itemId": "v1|9"}]}),
        ],
    )
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: multi)

    result = browse_api.search_item_summaries(q="drone", limit=1)
    assert result.total == 1
    # Token cache was invalidated · second token used on retry
    assert multi.browse_calls[1]["headers"]["Authorization"] == "Bearer second_tok"


def test_browse_search_requires_q_or_categories() -> None:
    from app.integrations.ebay import browse_api
    with pytest.raises(browse_api.EbayBrowseAPIError):
        browse_api.search_item_summaries(limit=3)


def test_safe_summarize_drops_seller_internals(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.integrations.ebay import browse_api

    summary_input = browse_api.BrowseSearchResult(
        total=1, href="..", next_href=None,
        item_summaries=[{
            "itemId": "v1|1",
            "title": "Test Item",
            "price": {"value": "99.99", "currency": "USD"},
            "condition": "NEW",
            "itemWebUrl": "https://example.com/i/1",
            "seller": {"username": "secret_seller", "feedbackScore": 12345},
            "internalDebugFields": {"shouldNotLeak": True},
        }],
        captured_at_epoch=0.0, environment="sandbox",
    )
    safe = browse_api.safe_summarize_results(summary_input, max_items=3)
    assert safe["sample"][0]["itemId"] == "v1|1"
    assert "seller" not in safe["sample"][0]
    assert "internalDebugFields" not in safe["sample"][0]
    assert json.dumps(safe).find("secret_seller") == -1


# ─── Admin route tests (via TestClient) ──────────────────────────────


def _client() -> TestClient:
    from app.main import app
    return TestClient(app)


def test_admin_readiness_is_public_and_safe() -> None:
    resp = _client().get("/api/v1/admin/ebay/oauth/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["integration"] == "ebay_oauth_client_credentials"
    assert body["app_id_configured"] is True
    # No secret values
    assert FIXTURE_CERT_ID not in resp.text


def test_admin_token_refresh_requires_admin_header() -> None:
    # No header → 401
    resp = _client().post("/api/v1/admin/ebay/oauth/token-refresh")
    assert resp.status_code == 401
    # Wrong value → 401
    resp = _client().post(
        "/api/v1/admin/ebay/oauth/token-refresh",
        headers={"X-Ebay-Admin-Token": "wrong"},
    )
    assert resp.status_code == 401


def test_admin_token_refresh_503_when_admin_token_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EBAY_ADMIN_TOKEN", "")
    from app.core import config
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    resp = _client().post(
        "/api/v1/admin/ebay/oauth/token-refresh",
        headers={"X-Ebay-Admin-Token": "anything"},
    )
    assert resp.status_code == 503


# ─── Marketplace Insights API ────────────────────────────────────────


class _MultiMockClientWithInsights:
    """URL-dispatching mock for token + browse + insights endpoints."""

    def __init__(
        self,
        *,
        token_responses: list[_MockResponse],
        browse_responses: list[_MockResponse] | None = None,
        insights_responses: list[_MockResponse] | None = None,
    ):
        self._token = list(token_responses)
        self._browse = list(browse_responses or [])
        self._insights = list(insights_responses or [])
        self.token_calls: list[dict[str, Any]] = []
        self.browse_calls: list[dict[str, Any]] = []
        self.insights_calls: list[dict[str, Any]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def post(self, url: str, **kwargs):
        if "/identity/v1/oauth2/token" in url:
            self.token_calls.append({"method": "POST", "url": url, **kwargs})
            if not self._token:
                raise AssertionError(f"unexpected extra token POST {url}")
            return self._token.pop(0)
        raise AssertionError(f"unexpected POST to {url}")

    def get(self, url: str, **kwargs):
        if "/marketplace_insights/" in url:
            self.insights_calls.append({"method": "GET", "url": url, **kwargs})
            if not self._insights:
                raise AssertionError(f"unexpected extra insights GET {url}")
            return self._insights.pop(0)
        if "/buy/browse/v1/" in url:
            self.browse_calls.append({"method": "GET", "url": url, **kwargs})
            if not self._browse:
                raise AssertionError(f"unexpected extra browse GET {url}")
            return self._browse.pop(0)
        raise AssertionError(f"unexpected GET to {url}")


def test_insights_search_uses_correct_scope_token_and_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.integrations.ebay import marketplace_insights, oauth

    multi = _MultiMockClientWithInsights(
        # Insights scope token fetch
        token_responses=[_MockResponse(200, {
            "access_token": "insights_tok_xyz", "expires_in": 7200, "token_type": "Bearer",
        })],
        insights_responses=[_MockResponse(200, {
            "total": 2, "href": "..",
            "itemSales": [
                {"itemId": "v1|s1", "title": "Used RTX 3090",
                 "lastSoldDate": "2026-05-20T18:00:00Z",
                 "lastSoldPrice": {"value": "740", "currency": "USD"},
                 "condition": "Used"},
                {"itemId": "v1|s2", "title": "RTX 3090 Founders",
                 "lastSoldDate": "2026-05-21T12:00:00Z",
                 "lastSoldPrice": {"value": "920", "currency": "USD"},
                 "condition": "Used"},
            ],
        })],
    )
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: multi)

    result = marketplace_insights.search_item_sales(q="rtx 3090", limit=2)

    # The token POST asked for the marketplace.insights scope
    assert multi.token_calls[0]["data"]["scope"] == oauth.SCOPE_MARKETPLACE_INSIGHTS
    # The GET hit the insights endpoint (NOT browse)
    call = multi.insights_calls[0]
    assert "/marketplace_insights/v1_beta/item_sales/search" in call["url"]
    assert call["headers"]["Authorization"] == "Bearer insights_tok_xyz"
    assert call["headers"]["X-EBAY-C-MARKETPLACE-ID"] == "EBAY_US"
    assert call["params"]["q"] == "rtx 3090"
    assert result.total == 2
    assert len(result.item_sales) == 2


def test_insights_403_raises_scope_denied(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.integrations.ebay import marketplace_insights, oauth

    multi = _MultiMockClientWithInsights(
        token_responses=[_MockResponse(200, {
            "access_token": "ins_tok", "expires_in": 7200, "token_type": "Bearer",
        })],
        insights_responses=[_MockResponse(403, {
            "errors": [{"errorId": 1100, "domain": "API_OAUTH",
                        "message": "Application is not authorized for marketplace.insights scope"}],
        }, reason="Forbidden")],
    )
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: multi)

    with pytest.raises(marketplace_insights.EbayMarketplaceInsightsScopeDenied) as exc_info:
        marketplace_insights.search_item_sales(q="rtx 3090", limit=1)
    assert "Limited Release" in str(exc_info.value)


def test_insights_safe_summarize_drops_seller_internals() -> None:
    from app.integrations.ebay import marketplace_insights

    result = marketplace_insights.ItemSalesSearchResult(
        total=1, href="..", next_href=None,
        item_sales=[{
            "itemId": "v1|i1",
            "title": "Test Sold Item",
            "lastSoldDate": "2026-05-22T10:00:00Z",
            "lastSoldPrice": {"value": "100", "currency": "USD"},
            "condition": "Used",
            "conditionId": "3000",
            "categories": [{"categoryId": "27386", "categoryName": "Graphics Cards"}],
            "itemWebUrl": "https://example.com/i/1",
            "seller": {"username": "secret_seller_username", "feedbackScore": 99},
            "internalDebug": "should_not_leak",
        }],
        captured_at_epoch=0.0, environment="sandbox",
    )
    safe = marketplace_insights.safe_summarize_sales(result)
    assert safe["sample"][0]["lastSoldPrice"]["value"] == "100"
    assert safe["sample"][0]["categories"][0]["categoryName"] == "Graphics Cards"
    blob = json.dumps(safe)
    assert "secret_seller_username" not in blob
    assert "internalDebug" not in blob


def test_admin_marketplace_insights_search_route_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.integrations.ebay import oauth

    multi = _MultiMockClientWithInsights(
        token_responses=[_MockResponse(200, {
            "access_token": "admin_ins_tok", "expires_in": 7200, "token_type": "Bearer",
        })],
        insights_responses=[_MockResponse(200, {
            "total": 1, "href": "..",
            "itemSales": [{
                "itemId": "v1|admin-ins-1",
                "title": "admin-insights-test",
                "lastSoldDate": "2026-05-23T00:00:00Z",
                "lastSoldPrice": {"value": "500", "currency": "USD"},
                "condition": "Used",
            }],
        })],
    )
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: multi)

    resp = _client().get(
        "/api/v1/admin/ebay/marketplace-insights/search?q=rtx+3090&limit=1",
        headers={"X-Ebay-Admin-Token": FIXTURE_ADMIN_TOKEN},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["sample_size"] == 1
    assert body["sample"][0]["itemId"] == "v1|admin-ins-1"
    assert body["sample"][0]["lastSoldPrice"]["value"] == "500"
    assert "doctrine_note" in body


def test_admin_marketplace_insights_route_503_on_scope_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.integrations.ebay import oauth

    multi = _MultiMockClientWithInsights(
        token_responses=[_MockResponse(200, {
            "access_token": "tok", "expires_in": 7200, "token_type": "Bearer",
        })],
        insights_responses=[_MockResponse(403, {
            "errors": [{"errorId": 1100, "message": "Insufficient permissions"}],
        }, reason="Forbidden")],
    )
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: multi)

    resp = _client().get(
        "/api/v1/admin/ebay/marketplace-insights/search?q=rtx+3090&limit=1",
        headers={"X-Ebay-Admin-Token": FIXTURE_ADMIN_TOKEN},
    )
    # Scope denial maps to 503 (operator config issue · not a transient 502)
    assert resp.status_code == 503
    assert "Limited Release" in resp.text


# ─── Admin route tests (browse) ──────────────────────────────────────


def test_admin_browse_search_succeeds_with_admin_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.integrations.ebay import oauth

    multi = _MultiMockClient(
        token_responses=[_MockResponse(200, {
            "access_token": "admin_tok", "expires_in": 7200, "token_type": "Bearer",
        })],
        browse_responses=[_MockResponse(200, {
            "total": 1, "href": "..",
            "itemSummaries": [
                {"itemId": "v1|admin-1", "title": "admin-test", "price": {"value": "1", "currency": "USD"}}
            ],
        })],
    )
    monkeypatch.setattr(oauth.httpx, "Client", lambda **_k: multi)

    resp = _client().get(
        "/api/v1/admin/ebay/browse/search?q=drone&limit=1",
        headers={"X-Ebay-Admin-Token": FIXTURE_ADMIN_TOKEN},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["sample_size"] == 1
    assert body["sample"][0]["itemId"] == "v1|admin-1"
    assert body["environment"] == "sandbox"
