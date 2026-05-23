"""eBay Marketplace Insights API · sold-comp evidence rail.

Endpoint: `/buy/marketplace_insights/v1_beta/item_sales/search`

Returns SOLD/COMPLETED items from the last 90 days · the only public eBay
API that exposes confirmed-sale prices. The cornerstone of Defendable
Compute Market Watch's sold-comp evidence rail (and any other lane that
needs transaction-confirmed price points rather than asking prices).

⚠️ This is a Limited Release API. Access must be requested from eBay's
Developer Program (https://developer.ebay.com/marketplace-insights-api).
Until approved, eBay returns 403 with a scope-denial message · we
surface that as EbayMarketplaceInsightsScopeDenied so the caller can
distinguish "not approved yet" from "transient error".

Doctrine:
  · Sold-comp data IS confirmed-sale evidence per existing
    ProductRadar PERMISSIONED_CONNECTED_SALE / FIRST_PARTY_DEFENDABLE_SALE
    doctrine class · highest-grade signal class
  · Still read-only · no writes through this client
  · Bearer token NEVER logged
  · Sold-comp payload may include seller usernames · safe_summarize
    strips those before returning a public-safe summary

Reference: https://developer.ebay.com/api-docs/buy/marketplace-insights/resources/methods
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings
from app.integrations.ebay.oauth import (
    SCOPE_MARKETPLACE_INSIGHTS,
    get_application_token,
    invalidate_cache,
)


_log = logging.getLogger("integrations.ebay.marketplace_insights")


SANDBOX_BASE = "https://api.sandbox.ebay.com/buy/marketplace_insights/v1_beta"
PRODUCTION_BASE = "https://api.ebay.com/buy/marketplace_insights/v1_beta"


class EbayMarketplaceInsightsError(RuntimeError):
    pass


class EbayMarketplaceInsightsScopeDenied(EbayMarketplaceInsightsError):
    """Raised when eBay refuses the marketplace.insights scope · means the
    app has not been granted Marketplace Insights access yet · operator
    needs to submit the Limited Release application."""


@dataclass
class ItemSalesSearchResult:
    total: int
    href: str
    next_href: str | None
    item_sales: list[dict[str, Any]]
    captured_at_epoch: float
    environment: str


def _base_url() -> str:
    env = get_settings().ebay_environment.lower()
    return PRODUCTION_BASE if env == "production" else SANDBOX_BASE


def _marketplace_id() -> str:
    return get_settings().ebay_marketplace_id or "EBAY_US"


def search_item_sales(
    *,
    q: str | None = None,
    category_ids: str | None = None,
    filter: str | None = None,  # noqa: A002
    aspect_filter: str | None = None,
    limit: int = 10,
    offset: int = 0,
    sort: str | None = None,
    marketplace_id: str | None = None,
    timeout: float = 30.0,
) -> ItemSalesSearchResult:
    """Search Marketplace Insights item_sales · returns ItemSalesSearchResult.

    At least one of `q` / `category_ids` must be provided.

    Filter examples:
      · `lastSoldDate:[2026-01-01T00:00:00Z..2026-05-23T00:00:00Z]`
      · `price:[100..500],priceCurrency:USD`
      · `conditionIds:{3000|2750}` (used / very-good · for refurb-comp queries)

    Sort examples: `price`, `-price`, `endingSoonest`.
    """
    if not q and not category_ids:
        raise EbayMarketplaceInsightsError(
            "Item-sales search requires either q or category_ids"
        )
    if not (1 <= limit <= 100):
        raise EbayMarketplaceInsightsError("limit must be 1..100")

    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if q:
        params["q"] = q
    if category_ids:
        params["category_ids"] = category_ids
    if filter:
        params["filter"] = filter
    if aspect_filter:
        params["aspect_filter"] = aspect_filter
    if sort:
        params["sort"] = sort

    mp = marketplace_id or _marketplace_id()
    url = f"{_base_url()}/item_sales/search"

    def _do_request() -> httpx.Response:
        token = get_application_token(scope=SCOPE_MARKETPLACE_INSIGHTS)
        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "X-EBAY-C-MARKETPLACE-ID": mp,
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
        }
        with httpx.Client(timeout=timeout) as client:
            return client.get(url, headers=headers, params=params)

    resp = _do_request()

    if resp.status_code == 401:
        _log.warning("marketplace_insights got 401 · invalidating insights-scope token + retrying once")
        invalidate_cache(scope=SCOPE_MARKETPLACE_INSIGHTS)
        resp = _do_request()

    # 403 with a scope-related body means the app isn't granted insights access yet
    if resp.status_code == 403:
        body_excerpt = (resp.text or "")[:500]
        _log.warning(
            "marketplace_insights 403 · likely scope/access-not-granted · body=%s",
            body_excerpt,
        )
        raise EbayMarketplaceInsightsScopeDenied(
            "eBay returned 403 for Marketplace Insights · the application "
            "has not been granted access yet. Apply for the Limited Release: "
            "https://developer.ebay.com/marketplace-insights-api"
        )

    if resp.status_code >= 400:
        body_excerpt = (resp.text or "")[:500]
        _log.error(
            "marketplace_insights search failed · status=%d reason=%s q=%r limit=%d body=%s",
            resp.status_code, resp.reason_phrase, q, limit, body_excerpt,
        )
        raise EbayMarketplaceInsightsError(
            f"Marketplace Insights API returned HTTP {resp.status_code}"
        )

    try:
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        raise EbayMarketplaceInsightsError(
            "Marketplace Insights response was not valid JSON"
        ) from exc

    sales = data.get("itemSales") or []
    total = int(data.get("total") or len(sales))
    href = data.get("href") or url
    next_href = data.get("next")

    env = get_settings().ebay_environment.lower()
    return ItemSalesSearchResult(
        total=total,
        href=href,
        next_href=next_href,
        item_sales=sales,
        captured_at_epoch=time.time(),
        environment="production" if env == "production" else "sandbox",
    )


def safe_summarize_sales(
    result: ItemSalesSearchResult,
    max_items: int = 5,
) -> dict[str, Any]:
    """JSON-safe summary for admin probe responses.

    Strips seller usernames + feedback + internal debug fields. Preserves
    the core sold-comp evidence fields: itemId · title · lastSoldDate ·
    lastSoldPrice · condition · category.
    """
    sample = []
    for it in result.item_sales[:max_items]:
        sold_price = it.get("lastSoldPrice") or {}
        sample.append({
            "itemId": it.get("itemId"),
            "title": (it.get("title") or "")[:160],
            "lastSoldDate": it.get("lastSoldDate"),
            "lastSoldPrice": {
                "value": sold_price.get("value"),
                "currency": sold_price.get("currency"),
            },
            "condition": it.get("condition"),
            "conditionId": it.get("conditionId"),
            "categories": [
                {"categoryId": c.get("categoryId"), "categoryName": c.get("categoryName")}
                for c in (it.get("categories") or [])
            ],
            "itemWebUrl": it.get("itemWebUrl"),
        })
    return {
        "environment": result.environment,
        "total_reported": result.total,
        "returned_count": len(result.item_sales),
        "sample_size": len(sample),
        "sample": sample,
        "doctrine_note": (
            "Marketplace Insights returns CONFIRMED-SALE evidence · "
            "PERMISSIONED_CONNECTED_SALE class per ProductRadar doctrine. "
            "Bind to sold-comp tables · safe to use as transaction evidence "
            "in MarketReady receipts (NOT as 'asking price observation')."
        ),
    }
