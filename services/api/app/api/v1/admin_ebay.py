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

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.core.config import get_settings
from app.core.deps import require_ebay_admin
from app.integrations.ebay.browse_api import (
    EbayBrowseAPIError,
    safe_summarize_results,
    search_item_summaries,
)
from app.integrations.ebay.marketplace_insights import (
    EbayMarketplaceInsightsError,
    EbayMarketplaceInsightsScopeDenied,
    safe_summarize_sales,
    search_item_sales,
)
from app.integrations.ebay.oauth import (
    EbayOAuthConfigMissing,
    EbayOAuthError,
    get_application_token,
    invalidate_cache,
    readiness_status,
)


_log = logging.getLogger("api.admin.ebay")

# Boundary-level admin gate on the whole router (Codex exposure repair): every admin/ebay route
# — including oauth/readiness — now requires X-Ebay-Admin-Token and returns 401/503 (never 422)
# when unauthenticated, and no longer leaks integration readiness to anonymous callers.
router = APIRouter(prefix="/admin/ebay", tags=["admin-ebay"], dependencies=[Depends(require_ebay_admin)])


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


@router.post("/sold-comps/ingest-compute")
def admin_ingest_compute_sold_comps(
    sku_aliases: list[str] | None = Query(default=None),
    limit_per_sku: int = Query(default=5, ge=1, le=50),
    dry_run: bool = Query(default=True),
    x_ebay_admin_token: str | None = Header(default=None),
):
    """Run a Compute Market Watch sold-comp ingest pass.

    Pulls Marketplace Insights for each compute SKU · runs each return
    through the deterministic Tribunal · writes immutable artifacts
    under compute-market-watch/sold-comps/<label>/ in the bakery vault.

    Defaults to dry_run=true · returns counts only · no artifacts written.
    Set dry_run=false to actually persist.

    `sku_aliases` defaults to the operator's DEFAULT_INGEST_SKUS list
    (RTX 3090 · 4090 · A6000 · 4500 Ada · PRO 6000 Blackwell · H100 · A100).
    """
    _require_admin_token(x_ebay_admin_token)
    # Lazy import to keep admin route imports cheap when ingest unused
    from app.services.compute_market_watch.ingest import (
        run_compute_sold_comp_ingest,
    )
    try:
        result = run_compute_sold_comp_ingest(
            sku_aliases=sku_aliases,
            limit_per_sku=limit_per_sku,
            dry_run=dry_run,
        )
    except EbayOAuthConfigMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except EbayOAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    # SAFE summary · counts only · no seller/raw bodies
    return {
        "run_id": result.run_id,
        "environment": result.environment,
        "dry_run": result.dry_run,
        "started_at": result.started_at,
        "completed_at": result.completed_at,
        "skus_requested": result.skus_requested,
        "total_processed": result.total_processed,
        "total_by_label": result.total_by_label,
        "per_sku": [
            {
                "sku_alias": s.sku_alias,
                "total_from_ebay": s.total_from_ebay,
                "by_label": s.by_label,
                "errors": s.errors,
            } for s in result.per_sku_stats
        ],
        "manifest_artifact_key": result.manifest_artifact_key if not result.dry_run else None,
        "bundle_sha256": result.bundle_sha256,
    }


@router.get("/marketplace-insights/search")
def admin_marketplace_insights_search(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(3, ge=1, le=10),
    sort: str | None = Query(default=None, max_length=40),
    filter: str | None = Query(default=None, max_length=400, alias="filter"),  # noqa: A002
    marketplace_id: str | None = Query(default=None, max_length=20),
    x_ebay_admin_token: str | None = Header(default=None),
):
    """Marketplace Insights sold-comp search · admin-gated · returns SAFE summary.

    Returns 503 with a clear scope-denied message when eBay has not yet
    granted Limited Release access to Marketplace Insights for this app.
    """
    _require_admin_token(x_ebay_admin_token)
    try:
        result = search_item_sales(
            q=q, limit=limit, sort=sort, filter=filter,
            marketplace_id=marketplace_id,
        )
    except EbayOAuthConfigMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except EbayOAuthError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except EbayMarketplaceInsightsScopeDenied as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except EbayMarketplaceInsightsError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return safe_summarize_sales(result, max_items=limit)
