"""Admin · eBay OAuth + Browse smoke endpoints.

  GET  /api/v1/admin/ebay/oauth/readiness  · public-safe readiness (booleans only)
  POST /api/v1/admin/ebay/oauth/token-refresh  · admin-gated · forces a token re-fetch
  GET  /api/v1/admin/ebay/browse/search?q=...&limit=...  · admin-gated · Browse search

Admin gate (v1 · header-token until JWT lands):
  · Set EBAY_ADMIN_TOKEN as a Fly secret · any value of your choice
  · Send header `X-Ebay-Admin-Token: <value>` on the gated routes
  · Returns 401 when header missing/mismatch · 503 when env var unset
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Query, status

from app.core.config import get_settings
from app.integrations.ebay.browse_api import (
    EbayBrowseAPIError,
    safe_summarize_results,
    search_item_summaries,
)
from app.integrations.ebay.oauth import (
    EbayOAuthConfigMissing,
    EbayOAuthError,
    get_application_token,
    invalidate_cache,
    readiness_status,
)


_log = logging.getLogger("api.admin.ebay")

router = APIRouter(prefix="/admin/ebay", tags=["admin-ebay"])


def _require_admin_token(x_ebay_admin_token: str | None) -> None:
    """Simple shared-token admin gate. NEVER logs or echoes the token."""
    expected = get_settings().ebay_admin_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "EBAY_ADMIN_TOKEN is not configured on the server. "
                "Set it as a Fly secret to enable the admin eBay routes."
            ),
        )
    if not x_ebay_admin_token or x_ebay_admin_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing X-Ebay-Admin-Token header",
        )


@router.get("/oauth/readiness")
def oauth_readiness():
    """Booleans only · no secret bits · safe for unauthenticated probe."""
    return readiness_status()


@router.post("/oauth/token-refresh")
def force_token_refresh(
    x_ebay_admin_token: str | None = Header(default=None),
):
    """Drop the cache and fetch a fresh token. Returns safe metadata only."""
    _require_admin_token(x_ebay_admin_token)
    invalidate_cache()
    try:
        token = get_application_token()
    except EbayOAuthConfigMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except EbayOAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"refreshed": True, **token.safe_metadata()}


@router.get("/browse/search")
def admin_browse_search(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(3, ge=1, le=10),
    marketplace_id: str | None = Query(default=None, max_length=20),
    x_ebay_admin_token: str | None = Header(default=None),
):
    """Run a Browse API search end-to-end · returns a SAFE summary.

    Limited to 10 items max to keep response small and avoid leaking
    bulk catalog data via a misconfigured admin token.
    """
    _require_admin_token(x_ebay_admin_token)
    try:
        result = search_item_summaries(q=q, limit=limit, marketplace_id=marketplace_id)
    except EbayOAuthConfigMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except EbayOAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except EbayBrowseAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return safe_summarize_results(result, max_items=limit)
