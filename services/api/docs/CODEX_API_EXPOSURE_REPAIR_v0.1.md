# Codex API/Fly Exposure Repair v0.1

Audit: api_surface_audit/2026-05-26_defendableos_api_fly_v0.1 · Verdict: REPAIR_REQUIRED
App: defendableos-api (Fly.io) · Baseline commit 8c806d34091419ffc1c799568d34780a15c7094c
Repaired release: Fly v46.

## Public route policy
PUBLIC_ALLOWED (intentional, synthetic/safe, no integration leakage):
- GET /healthz (liveness only: status, service, version)
- GET /api/v1/public/lookup (existing public ledger lookup, leakage-guarded)
- GET /api/v1/claw-bakery/{healthcheck,public-metrics,seeded-fixtures}  (aggregate synthetic)
- GET /api/v1/compute-claw/{categories,readiness-statuses}              (static reference)
- POST /api/v1/compute-claw/intake                                      (synthetic owner-attested intake; no value opinion, no deed)
- GET /api/v1/agent-swarm/{healthcheck,roles}                           (demo team status; no provider/secret)
- POST /api/v1/agent-swarm/clawcheck/intake                             (synthetic intake)

AUTH_REQUIRED (now boundary-gated; unauth -> 401, never 422):
- /api/v1/admin/ebay/*  (oauth/readiness, oauth/token-refresh, browse/search, sold-comps/ingest-compute, marketplace-insights/search)
- /api/v1/compute-claw/admin/*  (readiness, market-observations/ebay/search, benchmark-evidence/attach, utility-evidence/attach, aiov-draft/compose)
- existing tenant/admin: /api/v1/me, /api/v1/assets, /api/v1/admin/goods/overview, claw-bakery/admin/* (unchanged, still gated)

## No-auth route classification (Codex-flagged)
| route | before | classification | after |
|---|---|---|---|
| /api/v1/admin/ebay/oauth/readiness | public 200 (leaked booleans) | AUTH_REQUIRED | 401 |
| /api/v1/admin/ebay/browse/search | 422 unauth | AUTH_REQUIRED | 401 |
| /api/v1/admin/ebay/oauth/token-refresh | inline-checked | AUTH_REQUIRED | 401 |
| /api/v1/admin/ebay/sold-comps/ingest-compute | inline-checked | AUTH_REQUIRED | 401 |
| /api/v1/admin/ebay/marketplace-insights/search | inline-checked | AUTH_REQUIRED | 401 |
| /api/v1/compute-claw/admin/readiness | public 200 (leaked ebay/driver) | AUTH_REQUIRED | 401 |
| /api/v1/compute-claw/admin/aiov-draft/compose | 422 unauth | AUTH_REQUIRED | 401 |
| /api/v1/compute-claw/admin/market-observations/ebay/search | inline | AUTH_REQUIRED | 401 |
| /api/v1/compute-claw/admin/benchmark-evidence/attach | inline | AUTH_REQUIRED | 401 |
| /api/v1/compute-claw/admin/utility-evidence/attach | inline | AUTH_REQUIRED | 401 |
| /api/v1/compute-claw/intake | public 200 | PUBLIC_ALLOWED (synthetic intake) | 200 (kept) |
| /api/v1/compute-claw/categories, /readiness-statuses | public 200 | PUBLIC_ALLOWED (reference) | 200 (kept) |
| /api/v1/agent-swarm/clawcheck/intake, /healthcheck, /roles | public 200 | PUBLIC_ALLOWED (synthetic) | 200 (de-leaked) |
| /api/v1/claw-bakery/healthcheck, public-metrics, seeded-fixtures | public 200 | PUBLIC_ALLOWED (synthetic) | 200 (de-leaked) |

## OpenAPI before/after
- Before: /openapi.json + /docs public; 78 paths; 28 operations declared no HTTPBearer.
- After (production): /openapi.json, /docs, /redoc -> 404 (disabled). Full operational API no
  longer anonymously browsable. Admin-adjacent no-auth operations eliminated at the boundary.

## Public write endpoint decision table
| route | decision | controls |
|---|---|---|
| /api/v1/compute-claw/intake | KEEP PUBLIC (synthetic) | owner-attested synthetic record; no value opinion; no deed issuance; returns intake id + readiness snapshot only |
| /api/v1/agent-swarm/clawcheck/intake | KEEP PUBLIC (synthetic) | synthetic intake; deterministic fallback; no external side effects beyond controlled artifact write |
Rate/abuse: documented as a follow-up (no per-IP limiter yet) — flagged in Known Limitations.

## Runtime leakage reduction
- /healthz: integration block removed.
- claw-swarm healthcheck: removed kimi_configured / kimi_model / intake_status(LIVE).
- claw-bakery healthcheck: removed storage driver + internal dir tree.
- All detailed readiness (ebay oauth, compute-claw marketscout, storage driver) now behind admin gate.

## Tigris / object storage inventory
- BUCKET_NAME is configured as a Fly secret (value NOT printed).
- Exact object inventory (count/size/prefixes) requires the storage credentials, which are
  app secrets. Per owner rule, not handled here. BLOCKER: secure inventory path needed —
  recommend owner-run `fly ssh console -a defendableos-api` + an inventory script using the
  in-machine creds that prints counts/sizes only (no keys/values). Not performed in this repair.
