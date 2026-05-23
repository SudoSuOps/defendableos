"""CLI smoke test · run via `python -m app.integrations.ebay.smoke`.

Modes:
  · python -m app.integrations.ebay.smoke browse [query] [limit]    (default)
  · python -m app.integrations.ebay.smoke insights [query] [limit]
  · python -m app.integrations.ebay.smoke both [query] [limit]

NEVER prints token values · only first-8-chars + expiry.
"""
from __future__ import annotations

import json
import sys

from app.integrations.ebay.browse_api import safe_summarize_results, search_item_summaries
from app.integrations.ebay.marketplace_insights import (
    EbayMarketplaceInsightsScopeDenied,
    safe_summarize_sales,
    search_item_sales,
)
from app.integrations.ebay.oauth import (
    DEFAULT_SCOPE,
    SCOPE_MARKETPLACE_INSIGHTS,
    EbayOAuthConfigMissing,
    EbayOAuthError,
    get_application_token,
    readiness_status,
)


def _smoke_browse(query: str, limit: int) -> int:
    print()
    print(f"--- BROWSE search · q={query!r} limit={limit} ---")
    try:
        tok = get_application_token(scope=DEFAULT_SCOPE)
    except (EbayOAuthConfigMissing, EbayOAuthError) as exc:
        print(f"[FAIL] browse token fetch · {exc}")
        return 3
    print(json.dumps({"token": tok.safe_metadata()}, indent=2))
    try:
        result = search_item_summaries(q=query, limit=limit)
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] browse search · {type(exc).__name__}: {exc}")
        return 4
    print(json.dumps(safe_summarize_results(result, max_items=limit), indent=2))
    print("[OK] browse round-trip successful")
    return 0


def _smoke_insights(query: str, limit: int) -> int:
    print()
    print(f"--- MARKETPLACE INSIGHTS sold-comp search · q={query!r} limit={limit} ---")
    try:
        tok = get_application_token(scope=SCOPE_MARKETPLACE_INSIGHTS)
    except EbayOAuthConfigMissing as exc:
        print(f"[FAIL] insights token config · {exc}")
        return 3
    except EbayOAuthError as exc:
        print(f"[FAIL] insights token fetch · {exc}")
        print("[NOTE] If status 401: app may not be granted Marketplace Insights scope.")
        return 3
    print(json.dumps({"token": tok.safe_metadata()}, indent=2))
    try:
        result = search_item_sales(q=query, limit=limit)
    except EbayMarketplaceInsightsScopeDenied as exc:
        print(f"[FAIL] insights scope denied · {exc}")
        return 5
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] insights search · {type(exc).__name__}: {exc}")
        return 4
    print(json.dumps(safe_summarize_sales(result, max_items=limit), indent=2))
    print("[OK] marketplace_insights round-trip successful")
    return 0


def run(mode: str = "browse", query: str = "drone", limit: int = 3) -> int:
    print("=== eBay OAuth smoke test ===")
    print(json.dumps({"readiness": readiness_status()}, indent=2))
    if mode == "browse":
        return _smoke_browse(query, limit)
    if mode == "insights":
        return _smoke_insights(query, limit)
    if mode == "both":
        b = _smoke_browse(query, limit)
        i = _smoke_insights(query, limit)
        return 0 if (b == 0 and i == 0) else max(b, i)
    print(f"[ERR] unknown mode {mode!r} · use browse|insights|both")
    return 2


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("browse", "insights", "both"):
        mode = sys.argv[1]
        rest = sys.argv[2:]
    else:
        mode = "browse"
        rest = sys.argv[1:]
    q = rest[0] if len(rest) > 0 else "drone"
    lim = int(rest[1]) if len(rest) > 1 else 3
    sys.exit(run(mode=mode, query=q, limit=lim))
