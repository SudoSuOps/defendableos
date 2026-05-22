# Defendable ProductRadar · Demand Intelligence Architecture

ProductRadar is the **second product** in DefendableOS. Where the
Goods Vault answers *"what is THIS thing worth?"*, ProductRadar
answers *"what should we SELL next?"*. The two halves connect via
the OpportunityScoreReceipt → (eventually) MarketReady launch
package → connected store sale → back into Goods Vault as
confirmed first-party transaction evidence.

> **Find what sells. Build what converts. Prove what matters.**

## The product line

```
PRODUCTRADAR             FIND what may sell    (this product)
        ↓
SUPPLIER REVIEW          CHOOSE what can be sold profitably
        ↓
MARKETREADY              BUILD the brand + page + media
        ↓
CONNECTED STORE          PUBLISH and sell
        ↓
FIRST-PARTY SALES        PROVE what actually converted
```

## The 7-class signal doctrine

Every demand/sales signal carries an explicit `SignalClass` that
declares its epistemic weight. The platform NEVER collapses these
into one "top selling product confirmed" line unless authorized
completed-sale evidence is in the mix.

| Signal class | Provider example | Truth weight | Confirmed sale? |
|---|---|---|---|
| `SEARCH_DEMAND_SIGNAL` | Ahrefs Keywords Explorer | Demand observation | NO |
| `SOCIAL_COMMERCE_TREND_SIGNAL` | TikTok Creative Center | Creative momentum | NO |
| `GOOGLE_SHOPPING_POPULARITY` | Google Merchant Center Best Sellers | Platform popularity | NO |
| `RETAIL_INTELLIGENCE_ESTIMATE` | Similarweb Shopper Intelligence | Estimate only | NO |
| `MARKETPLACE_SOLD_RESEARCH` | eBay Product Research (analyst-reviewed) | Strong sold context | NO (analyst-reviewed) |
| `PERMISSIONED_CONNECTED_SALE` | Connected client Shopify/eBay store | Confirmed | **YES** |
| `FIRST_PARTY_DEFENDABLE_SALE` | Defendable-managed sale | Confirmed | **YES** |

Only the bottom 2 classes count as confirmed-sale evidence. They
form `CONFIRMED_SALE_SIGNAL_CLASSES` · the set the LAUNCH_READY
recommendation gate checks.

## The 10 tables

```
product_opportunities          central discovery entity · status + recommendation
keyword_demand_signals         Ahrefs · per-keyword demand snapshots
shopping_popularity_signals    Google Merchant Center Best Sellers entries
social_trend_signals           TikTok Creative Center top-products entries
store_intelligence_observations Similarweb store-level estimates
marketplace_sales_researches   eBay Product Research analyst entries
supplier_candidates            sourcing feasibility per opportunity
margin_scenarios               price × cost × shipping × returns scenarios
connected_store_outcomes       PERMISSIONED first-party completed sales
opportunity_score_receipts     deterministic SHA-256-hashed score records
```

## The 8-component opportunity score

```
search_demand_growth          20%   Ahrefs trend × volume
social_trend_velocity         15%   TikTok momentum_score
marketplace_sold_signal       20%   eBay analyst-reviewed sold context
competitive_saturation        10%   inverted · Similarweb store density
gross_margin_feasibility      15%   best-case margin %
shipping_returns_risk         10%   inverted · ship cost + returns
brand_creative_fit             5%   category-coded brandability
policy_compliance_risk         5%   inverted · regulatory + platform
─────────────────────────────────
total                        100%
```

`WEIGHTS` constant + the 8 component scorers live in
`app/services/productradar.py`. Tests in
`test_productradar_doctrine.py` (24 of them) defend:
- The weight sum is exactly 1.0
- Every component scorer returns [0, 1]
- The confirmed-sale class set is locked at exactly 2 classes
- `assert_launch_ready_safe()` refuses LAUNCH_READY without a
  PERMISSIONED_CONNECTED_SALE / FIRST_PARTY_DEFENDABLE_SALE signal
- `assert_no_confirmed_sale_aggregation()` refuses to derive a
  confirmed-sale claim from non-confirmed-class signals

## The 7 new connectors

| Provider | Status today | Future state |
|---|---|---|
| `AHREFS_KEYWORDS_EXPLORER` | `NOT_CONFIGURED` | Permissioned API access |
| `GOOGLE_MERCHANT_CENTER_BEST_SELLERS` | `NOT_CONFIGURED` | Merchant Center connection |
| `TIKTOK_CREATIVE_CENTER` | `NOT_CONFIGURED` | Manual research workflow first |
| `EBAY_PRODUCT_RESEARCH` | `NOT_CONFIGURED` | Seller-account analyst workflow |
| `SIMILARWEB_SHOPPER_INTELLIGENCE` | `NOT_CONFIGURED` | Enterprise data partnership |
| `CONNECTED_SHOPIFY_STORE` | **`READY`** | Already available · per-org Shopify auth |
| `SUPPLIER_CATALOG_FUTURE` | `FUTURE_DISABLED` | Future capability |

`CONNECTED_SHOPIFY_STORE` is the only connector that's READY by
default because it doesn't require external credentials beyond
the per-org Shopify auth · once a client connects a store, the
platform can receive PERMISSIONED_CONNECTED_SALE records.

## What ProductRadar can claim vs. what it cannot

**CAN say:**
- "Search demand observed."
- "Social/creative product trend observed."
- "Popular product/brand signal observed in Google Shopping reporting."
- "Estimated ecommerce/store performance intelligence."
- "Marketplace sales research shown through authorized seller tooling," subject to use rights.
- "Permissioned completed sale record," after review.
- "First-party transaction evidence," after receipt and validator review.

**CANNOT say:**
- "Top selling product confirmed" (unless connected store + permissioned data)
- "Competitor store sold X units" (Similarweb is estimate)
- "This product will sell" (we have demand signals, not sales forecasts)
- "Verified sale price" (without authorized completed-sale evidence)
- "Guaranteed marketability"

## The flywheel

```
Discover what appears to sell
   ↓
Connect to a client's store
   ↓
Launch approved products
   ↓
Capture what actually sells (PERMISSIONED_CONNECTED_SALE)
   ↓
Improve future opportunity scoring
   ↓
The platform learns demand · honestly · with receipts.
```

## File map

```
services/api/app/models/productradar.py             10 models · 9 enums
services/api/alembic/versions/0005_*.py             enum additions + new enums
services/api/alembic/versions/0006_*.py             10 new tables
services/api/app/services/productradar.py           8-component scorer + doctrine
services/api/app/services/connector_registry.py     7 new connectors registered
services/api/app/tests/test_productradar_doctrine.py 24 boundary tests
docs/PRODUCTRADAR_ARCHITECTURE.md                   this file
```

## Brand line

> Defendable ProductRadar identifies emerging product opportunities
> using search demand, marketplace research, social-commerce trends
> and connected store performance — then turns approved products
> into market-ready brands, pages and sales packages.
>
> **Find what sells. Build what converts. Prove what matters.**
