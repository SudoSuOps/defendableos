# ProductRadar Signal Scorecard

The intelligence-engine spec for the 16-brand watchlist. Defines
what ProductRadar measures, how each signal is graded, and which
brands move from `WATCHLIST` to `MARKETREADY_CANDIDATE`.

## What ProductRadar is measuring

ProductRadar answers one question per brand / category /
product-opportunity:

> Should a client consider building a store around this?

It does NOT answer:
- "Is this product selling?" (only `PERMISSIONED_CONNECTED_SALE` /
  `FIRST_PARTY_DEFENDABLE_SALE` can answer that)
- "How much will it sell for?" (no signal class derives this)
- "Will it be profitable for this specific seller?" (requires
  supplier review · not in the score)

It DOES answer:
- "Is there observable demand?" (`SEARCH_DEMAND_SIGNAL`)
- "Are shoppers clicking?" (`ECOMMERCE_PRODUCT_CLICK_SIGNAL`)
- "Is the lane oversaturated?" (`RETAIL_INTELLIGENCE_ESTIMATE`)
- "Is the brand merchandised by major platforms?" (`BRANDED_COMMERCE_PLACEMENT`)
- "Can a reasonable margin be modeled?" (`MarginScenario` + `SupplierCandidate`)
- "Is there policy/compliance risk?" (`PolicyRiskFlag`)
- "Has anyone actually completed a sale?" (only if connected store data exists)

## Signal categories · what each one captures

| Category | Source | Provider examples | Truth class |
|---|---|---|---|
| **Brand placement** | Curated marketplace merchandising | eBay Brand Outlet | `BRANDED_COMMERCE_PLACEMENT` |
| **Search demand** | Keyword search volume + trend | Ahrefs · Semrush SEO API | `SEARCH_DEMAND_SIGNAL` |
| **Sell-through proxy** | Ecommerce product-page clicks after search | Semrush Retail Keywords | `ECOMMERCE_PRODUCT_CLICK_SIGNAL` |
| **Marketplace activity** | Sold-history research · analyst-reviewed | eBay Product Research (Terapeak) | `MARKETPLACE_SOLD_RESEARCH` |
| **Price movement** | Listed-price trend + dispersion | Brave LLM Context · eBay Browse · price history aggregators | derived from `SEARCH_DEMAND_SIGNAL` + `MARKETPLACE_SOLD_RESEARCH` |
| **Availability** | Supplier presence + lead time | manual SupplierCandidate review · future supplier-catalog connectors | `SupplierFeasibility` enum |
| **Verified transaction depth** | Permissioned completed sales | Connected Shopify/eBay client store · ITAD partner pilots | `PERMISSIONED_CONNECTED_SALE` (only confirmed-sale class) |
| **Margin opportunity** | Cost vs target retail vs platform fees vs returns | manual MarginScenario × SupplierCandidate | derived |
| **Defensibility** | Competition + barriers + brand authorization | Similarweb Trends · Semrush Domain Research · BrandWatchlist sourcing status | `RETAIL_INTELLIGENCE_ESTIMATE` + `COMPETITOR_VISIBILITY_SIGNAL` |

## The 8-component score · current weights (LOCKED)

```
search_demand_growth          20%   Keyword volume × trend (Ahrefs/Semrush)
social_trend_velocity         15%   TikTok Creative Center momentum
marketplace_sold_signal       20%   eBay Product Research analyst-reviewed
competitive_saturation        10%   inverted · Similarweb / Semrush Trends
gross_margin_feasibility      15%   Best-case MarginScenario %
shipping_returns_risk         10%   inverted · ship cost + return rate
brand_creative_fit             5%   Category-coded brandability
policy_compliance_risk         5%   inverted · regulatory + platform
─────────────────────────────────
total                        100%   sum to 1.0 (test-enforced)
```

Total score ∈ [0.0, 1.0]. Receipt SHA-256-hashes the
{scoring_version, breakdown, weights, recommendation} payload.

## How to interpret each component

| Score | Component reading |
|---|---|
| 0.0–0.20 | Component is essentially zero · either no signal collected or strongly negative |
| 0.20–0.40 | Weak signal · won't move the needle alone |
| 0.40–0.60 | Moderate signal · contributes to opportunity but needs corroboration |
| 0.60–0.80 | Strong signal · meaningful pull for the opportunity |
| 0.80–1.00 | Top-decile signal · should be a major driver of the recommendation |

### Total score → recommendation

```
≥ 0.70  AND  confirmed_sale_count ≥ 1   →  LAUNCH_READY
≥ 0.55  AND  supplier_feasibility=FEASIBLE  →  PROCEED_TO_SUPPLIER_REVIEW
≥ 0.35                                    →  GATHER_MORE_SIGNALS
<  0.35                                   →  DEPRIORITIZE
policy_risk_flag = REJECTED               →  REJECT (overrides any score)
competition_level = OVERSATURATED         →  REJECT (overrides any score)
```

The `LAUNCH_READY` gate is hard-doctrine: a confirmed-sale signal
(`PERMISSIONED_CONNECTED_SALE` or `FIRST_PARTY_DEFENDABLE_SALE`)
MUST exist. `assert_launch_ready_safe()` raises
`ProductRadarError` if a caller tries to ship `LAUNCH_READY`
without it. Tested.

## Priority A versus DEFER criteria

### Priority A (research now · 10 brands seeded)

Criteria · all of:
- Brand has clear merchandising presence on a major surface
  (eBay Brand Outlet · Google Shopping)
- Search demand is observable for at least one product term
- Margin model can plausibly clear 25%+ gross at typical retail
- No regulated-good / authenticated-good / supply-chain
  authorization gate
- Defendable can produce a credible MarketReady package without
  brand trademark issues

Current Priority A:

| Brand | Lane | Why A |
|---|---|---|
| EcoFlow | HOME_POWER_EQUIPMENT | premium ticket · SwarmEnergy adjacency · Brand Outlet promotion |
| Anker | LATEST_TECH | charging + portable power · ecommerce creative fit |
| CyberPower | LATEST_TECH | UPS · compute continuity adjacency |
| Seagate | ELITE_TECH | storage · workstation + NAS adjacency |
| Western Digital | ELITE_TECH | storage · workstation + NAS adjacency |
| Logitech | LATEST_TECH | workstation accessories · easy branded research |
| DJI | LATEST_TECH | cameras / drones · visual MarketReady win |
| DEWALT | TOOLS_EQUIPMENT | tools · Jupiter Power Wash adjacency |
| Milwaukee | TOOLS_EQUIPMENT | tools · contractor vertical |
| Makita | TOOLS_EQUIPMENT | tools · contractor vertical |

### DEFER (6 luxury brands · NOT pursue without authenticated supply)

Criteria · any of:
- Authentication chain required (luxury goods)
- Authorized-supply gate from the brand (vs. open marketplace)
- Trademark / counterfeit risk if mis-handled
- Capital intensity (high MOQ · slow turn)
- Long sourcing cycle relative to first-revenue target

Current DEFER:

| Brand | Lane | Why DEFER |
|---|---|---|
| Gucci | LUXURY_HANDBAGS | authentication + authorized supply risk |
| Louis Vuitton | LUXURY_HANDBAGS | authentication + authorized supply risk |
| Chanel | LUXURY_HANDBAGS | authentication + authorized supply risk |
| Rolex | LUXURY_WATCHES_JEWELRY | authentication + capital + condition risk |
| Omega | LUXURY_WATCHES_JEWELRY | authentication risk |
| Cartier | LUXURY_WATCHES_JEWELRY | authentication risk |

## Why luxury is deferred until verifiable paid comps exist

Luxury could be the highest-ticket lane on the platform. The defer
isn't about market quality · it's about doctrine.

Luxury goods on secondary markets have a counterfeit base-rate
problem · the only safe Defendable claim path is:
1. Authenticated supply chain (authorized dealer / brand
   partnership / RealReal-grade authentication workflow)
2. Confirmed-sale evidence (`PERMISSIONED_CONNECTED_SALE` from a
   client store with authentication built in)
3. First-party verified-sale workflow (Defendable physically
   verifies + photographs + serializes before selling)

Without one of those three, the platform cannot put a luxury
asset deed on `/verify` without risking false-authenticity claims.
`policy_risk_flag=TRADEMARK_RISK` is the default · 6 luxury brands
sit at this default until an authorized supply path is signed.

If/when that signed path exists:
- Promote the brand from `DEFER` to `B` (research with caution)
- Add `authentication_workflow_id` field to the deed JSON (future)
- Add `LUXURY_AUTHENTICATION` step to the AIOV draft pipeline
- Run validator with a new check: `LUXURY_AUTHENTICATION_PRESENT_AND_VALIDATED`

None of that is built today. Luxury stays at DEFER.

## Signal providers · per metric · today vs pending

| Metric | Provider | Status today |
|---|---|---|
| Brand placement | EBAY_BRAND_OUTLET | ✅ READY (manual analyst workflow · no key needed) |
| Search demand | AHREFS_KEYWORDS_EXPLORER | ⏸ NOT_CONFIGURED |
| Search demand | SEMRUSH (via SEO API) | ⏸ PLAN_VERIFICATION_REQUIRED if key set, else NOT_CONFIGURED |
| Sell-through proxy | SEMRUSH (Ecommerce Keyword Analytics) | ⏸ PLAN_VERIFICATION_REQUIRED |
| Marketplace activity | EBAY_PRODUCT_RESEARCH | ⏸ NOT_CONFIGURED |
| Marketplace activity (auxiliary) | EBAY_BROWSE | ⏸ NOT_CONFIGURED (biz approval pending) |
| Price movement | Derived from Brave + future eBay sources | ⏸ partial |
| Availability | SUPPLIER_CATALOG_FUTURE | 🔒 FUTURE_DISABLED |
| Verified transaction depth | CONNECTED_SHOPIFY_STORE | ✅ READY (waits on first client store connection) |
| Verified transaction depth | ITAD partner feeds | ⏳ pilot agreements pending |
| Margin opportunity | Manual MarginScenario × SupplierCandidate | ✅ READY (analyst workflow) |
| Defensibility | SIMILARWEB_SHOPPER_INTELLIGENCE | ⏸ NOT_CONFIGURED (enterprise contract) |
| Defensibility (auxiliary) | SEMRUSH (Trends + Domain Research) | ⏸ PLAN_VERIFICATION_REQUIRED |
| Brand creative fit | Coded heuristic by category | ✅ READY |
| Policy compliance | Coded heuristic + manual override | ✅ READY |
| Social trend velocity | TIKTOK_CREATIVE_CENTER | ⏸ NOT_CONFIGURED |
| Google Shopping popularity | GOOGLE_MERCHANT_CENTER_BEST_SELLERS | ⏸ NOT_CONFIGURED |

### What is real today

- **5 components** can score with the current configuration:
  brand_creative_fit · policy_compliance_risk ·
  shipping_returns_risk (with MarginScenario inputs) ·
  gross_margin_feasibility (with MarginScenario inputs) ·
  competitive_saturation (with manual StoreIntelligenceObservation
  entries from Brave research)
- **2 components** require connector configuration:
  search_demand_growth · social_trend_velocity
- **1 component** requires analyst workflow + eBay seller access:
  marketplace_sold_signal

**Implication for tomorrow:** ProductRadar can grade a couple of
opportunities today using brand_creative_fit + manual margin
modeling + Brave-grounded competitive saturation. The score won't
have the polish of the full 8-component output until at least
Semrush comes online · but it's not zero.

### Manual-first scoring workflow (pre-Semrush)

1. Admin picks a brand from the watchlist (start with EcoFlow)
2. Manually creates 1 `ProductOpportunity` via DB or admin POST
   (POST endpoint deferred · use direct insert for now)
3. Brave grounds 1 "EcoFlow portable power station market" query ·
   results inform `StoreIntelligenceObservation` entries
4. Operator codes `brand_creative_fit` based on category bias (built in)
5. Operator codes `gross_margin_feasibility` via a `MarginScenario`
   row with target retail + estimated cost
6. `compute_score(db, opportunity)` returns the partial score
7. Receipt is hashed and stored

The receipt explicitly captures the partial-coverage state in
`signals_used_count` and `confirmed_sale_signals_count`. No
`LAUNCH_READY` recommendation will fire because the gate refuses
without a confirmed-sale signal.

## Scoring example · what a partial score looks like

Manual run on EcoFlow with what's available today:

```json
{
  "opportunity_id": "OPP-ECOFLOW-PORTABLE-POWER-001",
  "scoring_version": "v1",
  "total_score": 0.34,
  "component_breakdown": {
    "search_demand_growth": 0.00,           // no Semrush yet
    "social_trend_velocity": 0.00,          // no TikTok connector
    "marketplace_sold_signal": 0.00,        // no eBay Product Research
    "competitive_saturation_inverted": 0.55, // 2 high-rev stores observed
    "gross_margin_feasibility": 0.60,        // 30% margin scenario
    "shipping_returns_risk_inverted": 0.45,  // shipping is non-trivial
    "brand_creative_fit": 0.85,              // HOME_ORGANIZATION lane
    "policy_compliance_risk_inverted": 1.00  // no risk flagged
  },
  "competition_level": "MEDIUM",
  "policy_risk_flag": "NONE",
  "signals_used_count": 4,
  "confirmed_sale_signals_count": 0,
  "recommendation": "GATHER_MORE_SIGNALS"
}
```

`0.34` lands the opportunity in `GATHER_MORE_SIGNALS` ·
correctly so · we don't have enough data to recommend launch.

## How the scorecard guides commercial work

| Score band | What the founder does |
|---|---|
| 0.70+ with confirmed sale | Build the MarketReady package · launch · capture connected-store sales |
| 0.55–0.70 with feasible supplier | Pitch the brand as a candidate to a client · gather more signals |
| 0.35–0.55 | Add to active research · run Semrush queries when account exists |
| < 0.35 | Park · re-evaluate in 90 days unless a signal moves |
| REJECT (policy or oversaturation) | Mark and never re-evaluate without doctrine change |

## What changes when Semrush + eBay Product Research come online

Once both connectors are READY:
- 3 currently-zero components start producing real numbers ·
  scores will move
- Brands that scored 0.34 might jump to 0.55–0.75 (the missing 35%
  of the weight matrix becomes addressable)
- Receipt diff vs prior score becomes auditable evidence of why
  the recommendation changed
- The scorecard's commercial utility goes from "research aid" to
  "deal-flow signal"

Until then · score what we can · advance brands with strong partial
scores into supplier review · don't claim more than the data
supports.

## Related docs

- `PRODUCTRADAR_ARCHITECTURE.md` · the 7-class doctrine (now 9 with
  Brand Outlet + Semrush extensions)
- `BRAND_OUTLET_SIGNAL_DOCTRINE.md` · the watchlist generator rules
- `SEMRUSH_PRODUCTRADAR_RAIL.md` · the 4-roles-1-provider summary
- `COMPUTE_BEACHHEAD_30_DAY_PLAN.md` · the asset-side revenue lane
