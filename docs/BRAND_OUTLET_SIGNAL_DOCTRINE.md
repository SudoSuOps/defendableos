# Brand Outlet Signal Doctrine

eBay Brand Outlet tells ProductRadar **which brands eBay is actively
merchandising**. It does NOT tell us what is selling, and it does
NOT authorize us to resell anything.

## The signal class

```
SignalClass.BRANDED_COMMERCE_PLACEMENT
  ProviderName.EBAY_BRAND_OUTLET
  default sales_confirmed = False           (refused if set True)
  default supplier_authorization_confirmed = False  (refused if set True)
  default rights_status = INTERNAL_RESEARCH_ONLY
  default training_eligible = False
```

The service-layer guard `assert_brand_placement_signal_safe()` raises
`ProductRadarError` if any caller tries to flip `sales_confirmed=True`
or `supplier_authorization_confirmed=True` while declaring
BRANDED_COMMERCE_PLACEMENT. Tests in
`test_brand_outlet_doctrine.py` defend this.

## What Brand Outlet IS

- A live view of which brands eBay is putting premium shopping real
  estate behind
- A watchlist generator that feeds the rest of ProductRadar's
  research pipeline
- A directional signal that demand may exist for a brand/category

## What Brand Outlet IS NOT

- ❌ NOT confirmed unit sales
- ❌ NOT supplier authorization (us appearing in research ≠ eBay
  authorizing Swarm & Bee to resell the brand)
- ❌ NOT margin proof
- ❌ NOT a license to use the brand's logos or imply we're a
  dealer
- ❌ NOT a guarantee any individual SKU is selling

## The Brand Outlet → ProductRadar pipeline

```
Brand Outlet observation                  (BRANDED_COMMERCE_PLACEMENT)
        ↓
BrandWatchlist entry                      (priority A/B/C/DEFER)
        ↓
Ahrefs keyword-demand analysis            (SEARCH_DEMAND_SIGNAL)
        ↓
eBay Product Research sold validation     (MARKETPLACE_SOLD_RESEARCH)
        ↓
Supplier/authorization/margin review      (SupplierCandidate)
        ↓
Shipping + return risk check              (MarginScenario)
        ↓
OpportunityScoreReceipt                   (deterministic SHA-256)
        ↓
MarketReady package                       (for LAUNCH_READY only)
```

Each downstream step adds its own signal class. The Brand Outlet
observation alone never advances an opportunity past `RESEARCH_CANDIDATE`.

## The Priority A watchlist (seeded today)

**Track A · research now** (10 brands · all `NOT_REVIEWED` sourcing)

| Brand | Merchandising lane | Defendable angle |
|---|---|---|
| EcoFlow | HOME_POWER_EQUIPMENT | SwarmEnergy adjacency · premium ticket |
| Anker | LATEST_TECH | Charging / portable power / tech accessories |
| CyberPower | LATEST_TECH | UPS + power protection · compute continuity |
| Seagate | ELITE_TECH | Storage · workstation + NAS adjacency |
| Western Digital | ELITE_TECH | Storage · workstation + NAS adjacency |
| Logitech | LATEST_TECH | Workstation accessories |
| DJI | LATEST_TECH | Cameras / drones · visual MarketReady win |
| DEWALT | TOOLS_EQUIPMENT | Tools · Jupiter Power Wash adjacency |
| Milwaukee | TOOLS_EQUIPMENT | Tools · contractor vertical |
| Makita | TOOLS_EQUIPMENT | Tools · contractor vertical |

**Track DEFER · do NOT pursue without authorized supply + authentication** (6 luxury brands)

Gucci · Louis Vuitton · Chanel · Rolex · Omega · Cartier ·
all `priority_tier=DEFER` · `policy_risk_flag=TRADEMARK_RISK`.

## The first pilot lane · Portable Energy + Compute Protection

The strongest convergence in the Priority A list:

- EcoFlow (portable power)
- CyberPower (UPS)
- Anker (charging + portable power)
- Seagate / WD (storage)
- Netgear (networking · add later)

**Product collection candidates:**
- AI Workstation Power Kit
- Creator Backup Power Kit
- Home Office Continuity Kit
- Edge Compute Backup Kit
- Mobile Capture / Storage Kit

Brand line: *"Power your work. Protect your compute. Preserve the evidence."*

Avoids regulated products and counterfeit-heavy luxury · perfect
first lane for ProductRadar's first cycle.

## eBay Refurbished · documented future lane

eBay's Refurbished program (Certified + vetted condition grades,
1-2 year warranties, 30-day returns minimum) is a long-term
candidate for **Defendable Refurbished Compute**. Not built this
turn. Documented here as the future:

```
Defendable Refurbished Compute
Tested GPUs, workstations and edge devices packaged with
evidence and buyer-ready records.
```

Capabilities that align:
- Condition grading · already covered by EvidenceItem + ValidatorReview
- Testing · BenchmarkOutput evidence type already exists
- Free shipping + returns · Swarm & Bee policies being configured
- Premium product media · MarketReady will produce this
- Clear product identity · CanonicalGood already covers this

Requires eBay seller qualification before we ship anything.

## What the platform may say publicly

| Allowed statement | Forbidden statement |
|---|---|
| "Brand X is currently featured in eBay's Brand Outlet" | "Brand X is selling out" |
| "We are researching opportunities in [merchandising lane]" | "We have a partnership with [brand]" |
| "Authorized sourcing path under review" | "We have authorization to resell [brand]" |
| "MarketReady package available for approved products" | "Top-selling [brand] product confirmed" |

## File map

```
services/api/app/models/productradar.py         + BrandWatchlist + BrandPlacementSignal
services/api/alembic/versions/0007_*.py         + 3 new enums + 2 enum additions
services/api/alembic/versions/0008_*.py         + 2 new tables
services/api/app/services/connector_registry.py + EBAY_BRAND_OUTLET registered READY
services/api/app/services/productradar.py       + assert_brand_placement_signal_safe()
services/api/app/services/seed_brand_outlet.py  10 Priority A + 6 DEFER brands
services/api/app/tests/test_brand_outlet_doctrine.py · 17 boundary tests
docs/BRAND_OUTLET_SIGNAL_DOCTRINE.md            this file
```
