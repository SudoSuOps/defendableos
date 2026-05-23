# Semrush · ProductRadar Competitive-Intelligence Rail

Semrush is the broader competitive-intelligence rail beside Ahrefs.
Where Ahrefs is mostly about keyword demand, Semrush serves **4
distinct ProductRadar roles** under one provider:

| Semrush role | Signal class | Defendable table |
|---|---|---|
| SEO / Keyword API | `SEARCH_DEMAND_SIGNAL` | `keyword_demand_signals` (provider=SEMRUSH) |
| Ecommerce Keyword Analytics (product clicks) | `ECOMMERCE_PRODUCT_CLICK_SIGNAL` ⭐ NEW | `ecommerce_product_click_signals` ⭐ NEW |
| Domain/Advertising Research (paid + organic visibility) | `COMPETITOR_VISIBILITY_SIGNAL` ⭐ NEW | (logged via opportunity context) |
| Trends API (traffic estimates) | `RETAIL_INTELLIGENCE_ESTIMATE` | `store_intelligence_observations` (provider=SEMRUSH) |

The Semrush guard `assert_semrush_signal_safe()` refuses
`sales_confirmed=True` on ANY of the 4 classes. **Semrush is never a
sales-confirmation source.**

## Connector state machine

```
NOT_CONFIGURED              no SEMRUSH_API_KEY
PLAN_VERIFICATION_REQUIRED  key present · no endpoints enabled yet
CONFIGURED_DISABLED         key + endpoints enabled · live calls off
READY                       all preconditions met
ERROR                       runtime failure
```

`PLAN_VERIFICATION_REQUIRED` is a NEW provider status (added 2026-05-22)
that acknowledges Semrush's tiered access: the founder might have a
working API key but only some endpoints are in the plan tier. The
state forces an explicit per-endpoint enable before any call fires.

## Configuration

```bash
SEMRUSH_API_KEY=                                  # required for any status above NOT_CONFIGURED
SEMRUSH_LIVE_CALLS_ENABLED=false                  # global kill switch
SEMRUSH_MAX_CALLS_PER_RUN=1                       # default cap
SEMRUSH_SEO_API_ENABLED=false                     # keyword/CPC/trend endpoints
SEMRUSH_TRENDS_API_ENABLED=false                  # traffic estimate endpoints
SEMRUSH_ECOMMERCE_KEYWORD_ANALYTICS_ENABLED=false # retail keywords / product clicks
SEMRUSH_RIGHTS_STATUS=TERMS_REVIEW_PENDING        # rights ledger default
SEMRUSH_DATA_USE=INTERNAL_RESEARCH_ONLY
SEMRUSH_MODEL_TRAINING_EXPORT_ENABLED=false       # NEVER true without rights review
```

## The 4 Semrush roles · in detail

### 1. SEO / Keyword API → `SEARCH_DEMAND_SIGNAL`
Goes through the existing `keyword_demand_signals` table with
`provider="SEMRUSH"`. Same shape as Ahrefs entries: keyword,
country, monthly_search_volume, CPC, trend, history.

### 2. Ecommerce Keyword Analytics → `ECOMMERCE_PRODUCT_CLICK_SIGNAL`
NEW class. Goes into the new `ecommerce_product_click_signals` table.
Captures Semrush's Retail Keywords data:
- `retail_keyword`
- `estimated_search_requests` across analyzed ecommerce domains
- `product_clicks` (visits to product pages after search)
- `month_over_month_change_pct`
- `top_clicked_domains_json` (which stores capture the clicks)
- `measurement_period_start/end`

This is **closer to shopper intent than raw search volume** because
the user actually clicked a product page. Still NOT a completed sale.

### 3. Domain/Advertising Research → `COMPETITOR_VISIBILITY_SIGNAL`
NEW class. Currently no separate table · logged via the
ProductOpportunity's notes/lineage. Captures:
- organic visibility for a domain
- paid keyword competition
- which competing stores rank for our target keywords

Distinct from `RETAIL_INTELLIGENCE_ESTIMATE` because it's about
keyword-level visibility, not traffic estimates.

### 4. Trends API → `RETAIL_INTELLIGENCE_ESTIMATE`
Reuses existing `store_intelligence_observations` table with
`provider="SEMRUSH"`. Captures Semrush Trends data:
- estimated monthly visits
- conversion rate estimate
- monthly revenue band estimate
- competitive rank
- estimate basis

## Why Semrush before Ahrefs

| Need | Ahrefs | Semrush | Winner |
|---|---|---|---|
| Keyword demand | Strong | Strong | Tie |
| Competitor organic visibility | Strong | Strong | Tie |
| Paid search competitor intel | Useful | Strongly positioned | Semrush |
| Store traffic estimates | Limited | Trends API built for this | Semrush |
| Ecommerce product clicks | Not the thesis | Ecommerce Keyword Analytics | Semrush |
| AI / agentic shopping visibility | Not central | Semrush actively building | Semrush |
| Confirmed units sold | NO | NO | Neither (need Connected Store) |

The cracked ProductRadar discovery flow is:

```
eBay Brand Outlet                  what eBay spotlights
        ↓
Semrush                            demand + clicks + competitor stores + traffic
        ↓
eBay Product Research              sold-market activity (analyst-reviewed)
        ↓
Supplier + Margin Review           lawful + profitable to source
        ↓
Defendable MarketReady             brand · page · listing · media
        ↓
Connected Store Sales              what actually converted
        ↓
Defendable Deed                    proof record of the sale
```

## Doctrine guards

`assert_semrush_signal_safe(sales_confirmed, signal_class)` raises
`ProductRadarError` when `sales_confirmed=True` is paired with any
of the 4 Semrush classes. Tests in
`test_semrush_doctrine.py` (23 of them) defend:

- Semrush provider registered
- `PLAN_VERIFICATION_REQUIRED` status exists
- Both new signal classes registered
- Neither new signal class is in `CONFIRMED_SALE_SIGNAL_CLASSES`
- `EcommerceProductClickSignal` defaults all doctrine booleans False
- Service refuses sales_confirmed=True on ALL 4 Semrush classes
- Service ignores non-Semrush classes (PERMISSIONED_CONNECTED_SALE
  has its own write path)
- Aggregation refusal still fires with Semrush-only signal set
- Connector status defaults to NOT_CONFIGURED · all 9 env vars present
  · all live flags default False · rights_status default
  TERMS_REVIEW_PENDING

## What we may / may not say publicly

| Allowed | Forbidden |
|---|---|
| "Search demand observed via Semrush" | "Top selling product confirmed" |
| "Estimated competitor traffic" | "Competitor store revenue: $X" |
| "Product clicks observed in ecommerce keyword research" | "Units sold: X" |
| "Visibility signal across paid/organic" | "Verified sales of [brand]" |

## File map

```
services/api/app/models/goods.py                       + SEMRUSH + PLAN_VERIFICATION_REQUIRED
services/api/app/models/productradar.py                + 2 SignalClass values + EcommerceProductClickSignal table
services/api/alembic/versions/0009_semrush_enum_additions.py
services/api/alembic/versions/0010_ecom_click_signals.py
services/api/app/core/config.py                        + 9 Semrush env vars
services/api/app/services/connector_registry.py        + _semrush_status() helper + SEMRUSH registered
services/api/app/services/productradar.py              + assert_semrush_signal_safe()
services/api/app/tests/test_semrush_doctrine.py        23 boundary tests
docs/SEMRUSH_PRODUCTRADAR_RAIL.md                      this file
```

## Brand line

> Find the demand. Validate the product. Build the store. Remember the sale.

Semrush gives us the first three signals · Connected Store + Goods
Vault close the loop with confirmed sales evidence and Defendable
Deed proof records.
