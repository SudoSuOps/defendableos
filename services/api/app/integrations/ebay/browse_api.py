"""eBay Browse API · thin wrapper around /buy/browse/v1/item_summary/search.

Pulls public-data listings using the cached Application Token. Auto-retries
ONCE on 401 (token may have expired between cache check and request) by
invalidating the cache and fetching fresh.

Doctrine:
  · Public-data only (no user-account-linked queries)
  · NO writes · this client is read-only
  · NO Bearer token logged
  · Marketplace-ID header defaults to operator's configured marketplace
    (EBAY_US by default · settable per-call)

Reference: https://developer.ebay.com/api-docs/buy/browse/resources/methods
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings
from app.integrations.ebay.oauth import (
    DEFAULT_SCOPE,
    get_application_token,
    invalidate_cache,
)


_log = logging.getLogger("integrations.ebay.browse_api")


SANDBOX_BASE = "https://api.sandbox.ebay.com/buy/browse/v1"
PRODUCTION_BASE = "https://api.ebay.com/buy/browse/v1"


class EbayBrowseAPIError(RuntimeError):
    pass


@dataclass
class BrowseSearchResult:
    total: int
    href: str
    next_href: str | None
    item_summaries: list[dict[str, Any]]
    captured_at_epoch: float
    environment: str


def _base_url() -> str:
    env = get_settings().ebay_environment.lower()
    return PRODUCTION_BASE if env == "production" else SANDBOX_BASE


def _marketplace_id() -> str:
    return get_settings().ebay_marketplace_id or "EBAY_US"


def search_item_summaries(
    *,
    q: str | None = None,
    category_ids: str | None = None,
    filter: str | None = None,  # noqa: A002 · eBay's parameter name
    limit: int = 10,
    offset: int = 0,
    marketplace_id: str | None = None,
    timeout: float = 30.0,
) -> BrowseSearchResult:
    """Search Browse API · returns parsed BrowseSearchResult.

    `q` (free-text search) OR `category_ids` (comma-separated leaf cat IDs)
    must be provided · per eBay's API contract.

    `filter` can include eBay filter expressions like
    'sellers:{the_seller}' or 'conditionIds:{1000|1500}'.
    """
    if not q and not category_ids:
        raise EbayBrowseAPIError(
            "Browse search requires either q or category_ids"
        )
    if not (1 <= limit <= 200):
        raise EbayBrowseAPIError("limit must be 1..200")

    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if q:
        params["q"] = q
    if category_ids:
        params["category_ids"] = category_ids
    if filter:
        params["filter"] = filter

    mp = marketplace_id or _marketplace_id()
    url = f"{_base_url()}/item_summary/search"

    def _do_request() -> httpx.Response:
        token = get_application_token(scope=DEFAULT_SCOPE)
        # OAuth 2.0 standard · always 'Bearer' regardless of what eBay's
        # token_type field says. eBay returns 'Application Access Token'
        # as the token_type label but their API requires 'Bearer' in the
        # Authorization header. (Confirmed via 400-not-401 on sandbox when
        # we used token_type verbatim · auth was accepted but request was
        # malformed elsewhere · standardizing to Bearer eliminates ambiguity.)
        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "X-EBAY-C-MARKETPLACE-ID": mp,
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
        }
        with httpx.Client(timeout=timeout) as client:
            return client.get(url, headers=headers, params=params)

    resp = _do_request()
    # Auto-retry once on 401 · drop ONLY the browse scope's cache and re-fetch
    if resp.status_code == 401:
        _log.warning("ebay browse search got 401 · invalidating browse-scope token + retrying once")
        invalidate_cache(scope=DEFAULT_SCOPE)
        resp = _do_request()

    if resp.status_code >= 400:
        # Log eBay's actual error body server-side · helps debug 400s where
        # eBay tells us exactly which field was wrong. NOT included in the
        # HTTP response to the caller (since the body may contain debug
        # metadata that's not appropriate for an admin probe).
        body_excerpt = (resp.text or "")[:500]
        _log.error(
            "ebay browse search failed · status=%d reason=%s q=%r limit=%d body=%s",
            resp.status_code, resp.reason_phrase, q, limit, body_excerpt,
        )
        # Surface a safe error · do NOT include response body verbatim
        raise EbayBrowseAPIError(
            f"Browse API returned HTTP {resp.status_code}"
        )

    try:
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        raise EbayBrowseAPIError("Browse API response was not valid JSON") from exc

    summaries = data.get("itemSummaries") or []
    total = int(data.get("total") or len(summaries))
    href = data.get("href") or url
    next_href = data.get("next")

    import time as _time
    env = get_settings().ebay_environment.lower()
    return BrowseSearchResult(
        total=total,
        href=href,
        next_href=next_href,
        item_summaries=summaries,
        captured_at_epoch=_time.time(),
        environment="production" if env == "production" else "sandbox",
    )


def safe_summarize_results(result: BrowseSearchResult, max_items: int = 5) -> dict[str, Any]:
    """Return a JSON-safe summary suitable for an admin probe response.

    Includes per-item title + itemId + price + condition · drops everything
    that could be considered seller-private (e.g. seller account internals).
    """
    sample = []
    for it in result.item_summaries[:max_items]:
        price = it.get("price") or {}
        sample.append({
            "itemId": it.get("itemId"),
            "title": (it.get("title") or "")[:160],
            "price": {
                "value": price.get("value"),
                "currency": price.get("currency"),
            },
            "condition": it.get("condition"),
            "itemWebUrl": it.get("itemWebUrl"),
        })
    return {
        "environment": result.environment,
        "total_reported": result.total,
        "returned_count": len(result.item_summaries),
        "sample_size": len(sample),
        "sample": sample,
    }
