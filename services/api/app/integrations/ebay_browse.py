"""eBay public-comp connector · server-side only.

Two evidence lanes are surfaced through eBay:

  · BROWSE API           → active listings → LISTING_PRICE evidence (always)
  · MARKETPLACE INSIGHTS → recently sold items → CONFIRMED_SALE_PRICE evidence
                          (requires business-tier API approval)

We use the OAuth2 client_credentials flow with the Swarm & Bee business app
credentials (`EBAY_APP_ID` + `EBAY_CERT_ID`). No user consent required, no
user-bound token. When the keys are absent the connector returns
NOT_CONFIGURED · the UI shows that honestly.
"""
from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

from app.core.config import settings


# ── token cache · access tokens are short-lived (~7200s) · cheap to reuse ──
_token_cache: dict[str, tuple[str, float]] = {}


@dataclass
class EbayItem:
    item_id: str
    title: str
    price_value: float | None
    price_currency: str | None
    url: str | None
    image_url: str | None
    condition: str | None
    seller_username: str | None
    item_location_country: str | None
    listing_type: str  # "active" or "sold"
    sold_at: datetime | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class EbayResult:
    status: str  # COMPLETED | NOT_CONFIGURED | FAILED
    items: list[EbayItem]
    error: str | None = None
    raw: dict[str, Any] | None = None


def is_configured() -> bool:
    return settings.ebay_configured


def _base_url() -> str:
    if settings.ebay_environment == "sandbox":
        return "https://api.sandbox.ebay.com"
    return "https://api.ebay.com"


def _get_access_token() -> str:
    """OAuth2 client_credentials flow · cached for ~2 hours."""
    cache_key = f"{settings.ebay_environment}:{settings.ebay_app_id}"
    cached = _token_cache.get(cache_key)
    if cached and cached[1] > time.time() + 30:
        return cached[0]

    creds = base64.b64encode(
        f"{settings.ebay_app_id}:{settings.ebay_cert_id}".encode("utf-8")
    ).decode("ascii")

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            f"{_base_url()}/identity/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
                # Browse scope covers active listings · Marketplace Insights uses
                # a separate scope that requires explicit approval.
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
        )
        if resp.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"eBay token error {resp.status_code}: {resp.text[:300]}",
                request=resp.request,
                response=resp,
            )
        body = resp.json()

    token = body["access_token"]
    ttl = int(body.get("expires_in", 7200))
    _token_cache[cache_key] = (token, time.time() + ttl)
    return token


def _parse_browse_item(node: dict) -> EbayItem:
    price = node.get("price") or {}
    img = (node.get("image") or {}).get("imageUrl")
    loc = (node.get("itemLocation") or {}).get("country")
    return EbayItem(
        item_id=node.get("itemId") or "",
        title=node.get("title") or "",
        price_value=float(price["value"]) if "value" in price else None,
        price_currency=price.get("currency"),
        url=node.get("itemWebUrl"),
        image_url=img,
        condition=node.get("condition"),
        seller_username=(node.get("seller") or {}).get("username"),
        item_location_country=loc,
        listing_type="active",
    )


def search_active_listings(
    query: str,
    limit: int = 10,
    marketplace_id: str | None = None,
    filters: list[str] | None = None,
) -> EbayResult:
    """Browse API · public · active listings. Maps to LISTING_PRICE evidence."""
    if not is_configured():
        return EbayResult(
            status="NOT_CONFIGURED",
            items=[],
            error="EBAY_APP_ID and EBAY_CERT_ID are required",
        )
    try:
        token = _get_access_token()
    except Exception as exc:
        return EbayResult(status="FAILED", items=[], error=str(exc))

    params = {
        "q": query,
        "limit": str(max(1, min(limit, 50))),
    }
    if filters:
        params["filter"] = ",".join(filters)

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": marketplace_id or settings.ebay_marketplace_id,
        "Accept": "application/json",
    }
    url = f"{_base_url()}/buy/browse/v1/item_summary/search"

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url, headers=headers, params=params)
            if resp.status_code >= 400:
                return EbayResult(
                    status="FAILED",
                    items=[],
                    error=f"eBay {resp.status_code}: {resp.text[:400]}",
                )
            body = resp.json()
    except Exception as exc:
        return EbayResult(status="FAILED", items=[], error=str(exc))

    items = [_parse_browse_item(n) for n in body.get("itemSummaries", [])]
    return EbayResult(status="COMPLETED", items=items, raw=body)


def search_sold_comparables(
    query: str,
    limit: int = 10,
    marketplace_id: str | None = None,
) -> EbayResult:
    """Marketplace Insights API · requires business-tier approval.

    Returns recently sold items with sale prices · maps to CONFIRMED_SALE_PRICE
    evidence. When the API is not yet approved for the account, returns FAILED
    with a clear "requires approval" message · we never fake sold data.
    """
    if not is_configured():
        return EbayResult(
            status="NOT_CONFIGURED",
            items=[],
            error="EBAY_APP_ID and EBAY_CERT_ID are required",
        )
    try:
        token = _get_access_token()
    except Exception as exc:
        return EbayResult(status="FAILED", items=[], error=str(exc))

    params = {
        "q": query,
        "limit": str(max(1, min(limit, 50))),
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": marketplace_id or settings.ebay_marketplace_id,
        "Accept": "application/json",
    }
    url = f"{_base_url()}/buy/marketplace_insights/v1_beta/item_sales/search"

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url, headers=headers, params=params)
            if resp.status_code == 403:
                return EbayResult(
                    status="FAILED",
                    items=[],
                    error=(
                        "Marketplace Insights requires business-tier approval · "
                        "apply at developer.ebay.com → My Account → Application "
                        "Keysets → Request Production Access for "
                        "buy.marketplace.insights scope."
                    ),
                )
            if resp.status_code >= 400:
                return EbayResult(
                    status="FAILED",
                    items=[],
                    error=f"eBay sold-comps {resp.status_code}: {resp.text[:400]}",
                )
            body = resp.json()
    except Exception as exc:
        return EbayResult(status="FAILED", items=[], error=str(exc))

    items: list[EbayItem] = []
    for n in body.get("itemSales", []):
        price = n.get("lastSoldPrice") or n.get("price") or {}
        sold_at_str = n.get("lastSoldDate") or n.get("soldDate")
        sold_at = None
        if sold_at_str:
            try:
                sold_at = datetime.fromisoformat(sold_at_str.replace("Z", "+00:00"))
            except Exception:
                sold_at = None
        items.append(
            EbayItem(
                item_id=n.get("itemId") or "",
                title=n.get("title") or "",
                price_value=float(price["value"]) if "value" in price else None,
                price_currency=price.get("currency"),
                url=n.get("itemWebUrl"),
                image_url=(n.get("image") or {}).get("imageUrl"),
                condition=n.get("condition"),
                seller_username=(n.get("seller") or {}).get("username"),
                item_location_country=(n.get("itemLocation") or {}).get("country"),
                listing_type="sold",
                sold_at=sold_at,
            )
        )
    return EbayResult(status="COMPLETED", items=items, raw=body)
