# Production Receipt Index · 2026-05-22

The single source of truth for what landed on production today.
Every claim in the morning brief should be verifiable through one
of the curl commands or commit hashes below.

## Production URLs · live as of 2026-05-22 evening

### Landing site (Cloudflare Pages)

| Surface | URL | Healthcheck |
|---|---|---|
| Apex | `https://defendableos.com/` | `curl -I https://defendableos.com/` → 200 |
| Compute demo | `https://defendableos.com/compute` | 200 |
| Ledger | `https://defendableos.com/ledger` | 200 |
| Ledger subdomain | `https://ledger.defendableos.com/` | 200 (rewrites to `/ledger`) |
| CRE MarketReady · main | `https://defendableos.com/showcase/cre/palm-grove-marketplace` | 200 |
| CRE · teaser | `https://defendableos.com/showcase/cre/palm-grove-marketplace/teaser` | 200 |
| CRE · OM | `https://defendableos.com/showcase/cre/palm-grove-marketplace/om` | 200 |
| CRE · buyer-room | `https://defendableos.com/showcase/cre/palm-grove-marketplace/buyer-room` | 200 |
| CRE · proof-record | `https://defendableos.com/showcase/cre/palm-grove-marketplace/proof-record` | 200 |
| AI manifest | `https://defendableos.com/llms.txt` | 200, `x-ai-context: defendableos` |
| Sitemap | `https://defendableos.com/sitemap.xml` | 200, 19 `<loc>` entries |
| Robots | `https://defendableos.com/robots.txt` | 200 |

### Platform API (Fly.io · IAD region)

| Endpoint | URL | Healthcheck |
|---|---|---|
| Healthcheck | `https://api.defendableos.com/healthz` | 200 · all 3 LLM integrations `*_configured: true` |
| Public lookup (by hash or ref) | `https://api.defendableos.com/api/v1/public/lookup?hash=<hash-or-ref>` | 200 with resolution payload, or `{kind: "NOT_FOUND"}` |
| Public verify (by slug) | `https://api.defendableos.com/api/v1/public/verify/<slug>` | 200 with `deed_public` payload |
| Admin · goods overview | `https://api.defendableos.com/api/v1/admin/goods/overview` | 200 (requires JWT with `is_platform_admin=true`) |
| Admin · canonical goods list | `https://api.defendableos.com/api/v1/admin/goods/canonical-goods` | 200, 6 entries |
| Admin · ITAD partners list | `https://api.defendableos.com/api/v1/admin/goods/itad-partners` | 200, 8 entries |
| Admin · brand watchlist | `https://api.defendableos.com/api/v1/admin/goods/productradar/brand-watchlist` | 200, 16 entries |
| Admin · ProductRadar overview | `https://api.defendableos.com/api/v1/admin/goods/productradar/overview` | 200 |
| Admin · operator summary (new this turn) | `https://api.defendableos.com/api/v1/admin/operator-summary` | 200 after this commit deploys |

## Migration range applied to prod DB

```
alembic upgrade 0001_initial → 0010_ecom_click_signals  (8 new migrations)

0002_goods_intelligence              Goods Vault · 15 tables · 24 enums
0003_itad_enum_additions             5 enum extensions + 10 new ITAD enums
0004_itad_tables                     3 ITAD tables
0005_productradar_enum_additions     7 ProviderName + 9 new ProductRadar enums
0006_productradar_tables             10 ProductRadar tables
0007_brand_outlet_enum_additions     2 enum extensions + 3 new Brand Outlet enums
0008_brand_outlet_tables             2 Brand Outlet tables
0009_semrush_enum_additions          4 enum extensions
0010_ecom_click_signals              1 Semrush product-click table
```

**Verify on prod:**
```bash
fly ssh console --app defendableos-api -C "bash -lc 'python -m alembic current'"
# Expected: 0010_ecom_click_signals (head)
```

## Seeded entities · record counts

| Entity | Count | Verified via |
|---|---|---|
| `canonical_goods` | **6** | `seed_goods` script output + `SELECT count(*) FROM canonical_goods` |
| `itad_partners` | **8** | `seed_itad_partners` script output |
| `brand_watchlists` | **16** | `seed_brand_outlet` script output (10 Priority A + 6 DEFER) |
| `source_connectors` | **17** | derived from `CONNECTOR_DEFINITIONS` in `connector_registry.py` |
| `comp_sets` (draft) | **1** | `COMPSET-DOV-COMPUTE-000001-v1` · status `NOT_READY_FOR_VALUE_SUPPORT` |

**Public deeds in catalog · 5 total:**

| Slug | Asset | Operator-stated value |
|---|---|---|
| `ddeed-dov-compute-000001-v3` | NVIDIA RTX PRO 6000 Blackwell | $9,850 |
| `ddeed-dov-compute-000002-v3` | NVIDIA RTX 5090 ROG ASTRAL | $3,900 |
| `ddeed-dov-compute-000003-v3` | NVIDIA RTX 3090 Founders Edition | $950 |
| `ddeed-dov-cre-stnl-wawa-000001-v1` | Wawa STNL · S Florida | $6,653,900 ($332,695 NOI · 5 cap) |
| `ddeed-dov-cre-stnl-amazon-000001-v1` | Amazon Last-Mile DC | $170,000,000 ($8.5M NOI · 5 cap) |

**Spot-check command for the row counts:**
```bash
fly ssh console --app defendableos-api -C "bash -lc 'python -c \"
from app.db.session import SessionLocal
from app.models.goods import CanonicalGood, ItadPartner, SourceConnector
from app.models.productradar import BrandWatchlist
db = SessionLocal()
print(f\\\"canonical_goods:   {db.query(CanonicalGood).count()}\\\")
print(f\\\"itad_partners:     {db.query(ItadPartner).count()}\\\")
print(f\\\"brand_watchlists:  {db.query(BrandWatchlist).count()}\\\")
print(f\\\"source_connectors: {db.query(SourceConnector).count()}\\\")
db.close()
\"'"
```

## SEO / GEO verification results

| Check | Result | Verified via |
|---|---|---|
| sitemap.xml URL count | **19** (18 routes + llms.txt manifest) | `curl https://defendableos.com/sitemap.xml \| grep -c "<loc>"` |
| llms.txt updated to evening version | mentions ProductRadar · Brand Outlet · ITAD · Semrush · "two halves" framing | `curl -s https://defendableos.com/llms.txt \| grep -cE "(ProductRadar\|Brand Outlet\|ITAD\|Semrush)"` |
| `/verify/{slug}` returns crawler bodyHtml | All 4 doctrine signals detected (`Defendable Verify`, `DRAFT_REVIEW_RECORD`, `Validate the Validator`, `Defendable Deed`) | `curl -A "GPTBot/1.0" https://defendableos.com/verify/ddeed-dov-compute-000001-v3 \| grep ...` |
| `/verify/{slug}` JSON-LD WebPage + DefinedTerm | `<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage", ...}</script>` present | `curl -A "GPTBot/1.0" https://defendableos.com/verify/ddeed-dov-compute-000001-v3 \| grep "application/ld+json"` |
| `_headers` rules · llms.txt | `cache-control: public, max-age=3600 · x-ai-context: defendableos · access-control-allow-origin: *` | `curl -I https://defendableos.com/llms.txt` |
| `_headers` rules · /verify | `cache-control: public, max-age=120, s-maxage=120, stale-while-revalidate=600 · x-defendable-doctrine: validate-the-validator` | `curl -I https://defendableos.com/verify/ddeed-dov-compute-000001-v3` |
| Multi-bot crawl simulation | GPTBot · ClaudeBot · PerplexityBot · Googlebot all detect 4/4 signals per route | live test in `feat/seo-geo-full-coverage` commit log |

## Public deed regression checks (zero regressions confirmed)

After the Fly deploy of migrations 0002–0010, all 5 existing deeds
were verified resolvable via lookup:

```bash
for ref in DDEED-DOV-COMPUTE-000001-v3 \
           DDEED-DOV-COMPUTE-000002-v3 \
           DDEED-DOV-COMPUTE-000003-v3 \
           DDEED-DOV-CRE-STNL-WAWA-000001-v1 \
           DDEED-DOV-CRE-STNL-AMAZON-000001-v1; do
  curl -s -o /dev/null -w "  %s  %s\n" \
    "$ref" \
    "$(curl -s -o /dev/null -w '%{http_code}' "https://api.defendableos.com/api/v1/public/lookup?hash=$ref")"
done

# Expected: all 200
```

All 5 deeds still publicly resolvable. Operator-asking-price band
still rendering on `/verify`. STNL terms band still rendering on
Wawa + Amazon DC.

## Source files · key references

| File | Purpose |
|---|---|
| `services/api/app/models/goods.py` | 15 Goods Vault models + 24 enums |
| `services/api/app/models/productradar.py` | 12 ProductRadar models + 9 enums (+ Brand Outlet + Semrush extensions) |
| `services/api/app/services/comp_foundry.py` | 7 doctrine rules · `CompFoundryError` boundary |
| `services/api/app/services/pair_factory.py` | Rights gate · `assert_training_eligible` |
| `services/api/app/services/productradar.py` | 8-component score · 3 doctrine guards |
| `services/api/app/services/connector_registry.py` | 17 connectors · honest status helpers |
| `services/api/app/services/artifacts.py` | 4-bucket vault · `public_export_or_refuse` |
| `services/api/app/services/seed_goods.py` | 6 canonical goods seed |
| `services/api/app/services/seed_itad_partners.py` | 8 ITAD partners seed |
| `services/api/app/services/seed_brand_outlet.py` | 16 brand watchlist seed |
| `services/api/app/api/v1/admin_goods.py` | All admin read endpoints |
| `services/api/alembic/versions/0002_*.py` → `0010_*.py` | 8 migrations applied tonight |

## Commands run (chronological · today)

```bash
# Migrations + seed verification (local)
python -m alembic upgrade head            # 0001 → 0010 clean
python -m app.services.seed_goods         # 6 canonical goods
python -m app.services.seed_itad_partners # 8 partners
python -m app.services.seed_brand_outlet  # 16 brands

# Test suite (full · last green count)
python -m pytest app/tests -q             # 139/139 passed (most recent · before founder pack route)

# Ruff
ruff check app/                           # All checks passed

# Production deploy
flyctl deploy --app defendableos-api --remote-only
fly ssh console --app defendableos-api -C "python -m app.services.seed_goods"
fly ssh console --app defendableos-api -C "python -m app.services.seed_itad_partners"
fly ssh console --app defendableos-api -C "python -m app.services.seed_brand_outlet"

# CF Pages publish (via git push to main · auto-deploy)
git push origin main
```

## Commit hashes on `main` (most recent first)

| Hash | Title |
|---|---|
| (this commit) | feat: founder morning operating pack + admin/operator-summary |
| `7681170` | feat(seo+geo): full end-to-end coverage · sitemap + llms.txt + verify + _headers |
| `b7f3df4` | feat(semrush): ProductRadar competitive-intelligence rail · 4 roles · 1 provider |
| `f65fc51` | feat(brand-outlet): BRANDED_COMMERCE_PLACEMENT signal · 16 brands seeded |
| `edfb544` | feat(productradar): demand-intelligence backend · 10 tables · 8-component score |
| `3056088` | feat(itad): add ITAD partner-feed lane · enterprise compute comps |
| `98b7637` | feat: build goods vault comp foundry and pair factory foundation |
| `03d0319` | feat(stnl): two operator-stated STNL deeds + public terms block |
| `f3ded58` | chore(prod-state): commit operator_ask deed.py + fly-normalized toml |
| `c2d73ff` | fix(ci): drop bare f-strings from walker print statements · ruff F541 |

**Landing repo (`SudoSuOps/defendable`) most recent commits:**

| Hash | Title |
|---|---|
| `7681170` | feat(seo+geo): full end-to-end coverage |
| `fab13a4` | feat(stnl): render operator-stated STNL terms band on /verify + /showcase |
| `86c6b59` | feat: defendable cre marketready property demo · palm grove marketplace |
| `d0d5a9e` | feat: OPERATOR_ASK_PRICE end-to-end · pricing shows on /verify + showcase |
| `dc7a3e4` | feat: showcase fallback v2 · marketing-grade CSS when WebGL declined |

## Unverified assertions · clearly labeled

These are claims made elsewhere in the docs that have NOT been
independently verified · noted here for honesty:

| Claim | Where it appears | Verification status |
|---|---|---|
| "Connector status returns `READY` for EBAY_BRAND_OUTLET via manual analyst workflow" | `BRAND_OUTLET_SIGNAL_DOCTRINE.md` | UNVERIFIED in production · the connector returns READY based on a hardcoded status function · no actual analyst-driven ingestion has happened yet |
| "All 4 AI crawlers detect 4/4 signals" | `seo-geo-coverage-2026-05-22.md` and morning brief | VERIFIED via `curl -A` simulation · not verified that the actual GPTBot/ClaudeBot/PerplexityBot crawlers have fetched + indexed the pages |
| Per-component ProductRadar score weights | `PRODUCTRADAR_SCORING_DOCTRINE.md` and scorecard | VERIFIED that weights sum to 1.0 via test · NOT VERIFIED against any real opportunity score because none have been run yet |
| ITAD partners "OUTREACH_READY" | seed output and brief | VERIFIED state on prod · but ZERO emails actually sent · UNVERIFIED that any will respond |
| Compute beachhead pricing tiers ($199 · $499 · $2,500/mo) | `COMPUTE_BEACHHEAD_30_DAY_PLAN.md` | UNVERIFIED · no customer has paid these prices · pricing is the founder's proposal · subject to market test |
| "First paid Compute Opinion of Value sold by Day 4" | `COMPUTE_BEACHHEAD_30_DAY_PLAN.md` | UNVERIFIED · aspirational schedule · the platform supports it but customer acquisition is the gating factor |
| "Estimated reachable count" for each customer profile | `COMPUTE_BEACHHEAD_30_DAY_PLAN.md` | UNVERIFIED · order-of-magnitude estimates · no list bought / scraped / opted in |
| "30% response rate target on ITAD outreach" | `ITAD_OUTREACH_EXECUTION_PACK.md` | UNVERIFIED · cold-email industry benchmark · this segment has no prior data |

These should be tested via execution · not asserted as fact.

## Related docs · the full receipt set

- `FOUNDER_MORNING_BRIEF_2026-05-23.md` · the 90-second exec brief
- `COMPUTE_BEACHHEAD_30_DAY_PLAN.md` · revenue lane #1
- `ITAD_OUTREACH_EXECUTION_PACK.md` · revenue lane #2
- `PRODUCTRADAR_SIGNAL_SCORECARD.md` · revenue lane #3
- `GOODS_INTELLIGENCE_ARCHITECTURE.md` · the platform-side architecture
- `COMP_QUALITY_DOCTRINE.md` · A-E grades + 7 rules
- `OBJECT_STORAGE_POLICY.md` · 4-bucket vault rules
- `CONNECTOR_CONFIGURATION.md` · env vars + statuses
- `ITAD_PARTNER_PILOT.md` · ITAD product framing
- `PRODUCTRADAR_ARCHITECTURE.md` · ProductRadar 7-class doctrine
- `BRAND_OUTLET_SIGNAL_DOCTRINE.md` · Brand Outlet rules
- `SEMRUSH_PRODUCTRADAR_RAIL.md` · Semrush 4-roles-1-provider
