"""CLI smoke test · run via `python -m app.integrations.ebay.smoke`.

Fetches an OAuth Application Token, calls Browse search, prints a safe
summary. Designed to be run server-side on the Fly machine:

    flyctl ssh console --app defendableos-api \\
        --command 'python -m app.integrations.ebay.smoke'

NEVER prints the token value · only first-8-chars + expiry.
"""
from __future__ import annotations

import json
import sys

from app.integrations.ebay.browse_api import safe_summarize_results, search_item_summaries
from app.integrations.ebay.oauth import (
    EbayOAuthConfigMissing,
    EbayOAuthError,
    get_application_token,
    readiness_status,
)


def run(query: str = "drone", limit: int = 3) -> int:
    print("=== eBay OAuth + Browse smoke test ===")
    print(json.dumps({"readiness": readiness_status()}, indent=2))

    try:
        tok = get_application_token()
    except EbayOAuthConfigMissing as exc:
        print(f"[FAIL] config missing · {exc}")
        return 2
    except EbayOAuthError as exc:
        print(f"[FAIL] token fetch failed · {exc}")
        return 3

    print()
    print("--- token (safe metadata only · never the value) ---")
    print(json.dumps(tok.safe_metadata(), indent=2))

    print()
    print(f"--- browse search · q={query!r} limit={limit} ---")
    try:
        result = search_item_summaries(q=query, limit=limit)
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] browse search failed · {type(exc).__name__}: {exc}")
        return 4

    print(json.dumps(safe_summarize_results(result, max_items=limit), indent=2))
    print()
    print("[OK] eBay OAuth + Browse search round-trip successful")
    return 0


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "drone"
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    sys.exit(run(query=q, limit=lim))
