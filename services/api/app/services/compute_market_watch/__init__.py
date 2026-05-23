"""Compute Market Watch · sold-comp evidence rail for compute hardware.

Pipeline:
  eBay Marketplace Insights · search_item_sales(q="<compute SKU>")
    → sold_comp_tribunal.classify() · rule-based · DETERMINISTIC · no LLM
       → HONEY     · clean confirmed-sale · usable comp evidence
       → JELLY     · price-suspect or partial-data · review queue
       → PROPOLIS  · invalid (zero price · missing fields · test data)
       → QUARANTINED · uncertain category match (different chassis / generation)
    → Immutable bakery write under compute-market-watch/sold-comps/<label>/
       with SHA-256 receipt + per-run aggregate ingest log

Use cases:
  · Compute Market Watch product · live GPU/accelerator sold prices
  · Defendable Asset valuation backing · "what did this hash actually sell for"
  · ProductRadar PERMISSIONED_CONNECTED_SALE class for compute SKUs

Doctrine guarantees:
  · No agent labels its own Honey · the classify() rules are pure code
  · Raw eBay payload immutable · receipt is over the raw bytes
  · Sandbox runs are marked synthetic=true · cannot poison production stats
  · PROPOLIS sold-comps are preserved as adversarial evidence · NEVER promoted
"""
