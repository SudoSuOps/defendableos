# INFRA_REGISTER

## service: defendableos-api
- provider: Fly.io
- environment: prototype_backend / staging (APP_ENV=production flag; NOT production-cleared)
- public_urls:
  - https://api.defendableos.com
  - https://defendableos-api.fly.dev
- purpose:
  - AIOV / Proof of Value backend
  - ComputeClaw
  - Claw Bakery
  - Agent-swarm intake
  - evidence / deed / edge APIs
- owner: Mr D
- risk_level: HIGH
- secrets_level: HIGH
- kill_switch: `fly scale count 0 -a defendableos-api`
- do_not_stop_without:
  - DB backup
  - Tigris/object inventory
  - endpoint dependency review
- next_review: 2026-05-27
- decision: KEEP_AND_RESTRICT

### Exposure repair applied (Codex api_surface_audit/2026-05-26_defendableos_api_fly_v0.1)
- `/healthz` reduced to `{status, service, version}` (no integration booleans / provider / driver / ENS mode).
- Public `/docs`, `/redoc`, `/openapi.json` DISABLED when `APP_ENV=production` (kept in dev/test).
- Admin-adjacent routes boundary-gated with `require_ebay_admin` (X-Ebay-Admin-Token): all of
  `/api/v1/admin/ebay/*` (incl. oauth/readiness) and `/api/v1/compute-claw/admin/*` (incl. admin/readiness).
  Unauthenticated → 401 (or 503 if token unset), never 422.
- Public probe leakage removed: claw-swarm healthcheck (kimi configured/model) and claw-bakery
  healthcheck (storage driver / dir tree) no longer expose integration/storage internals.
- Preserved synthetic public demo surfaces: `/healthz`, claw-bakery `public-metrics` / `seeded-fixtures` /
  `healthcheck`, compute-claw `intake` / `categories` / `readiness-statuses`, agent-swarm `clawcheck/intake` / `healthcheck` / `roles`.
