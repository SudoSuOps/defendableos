# API Reference

FastAPI mounts at `http://localhost:8000`. OpenAPI / Swagger UI lives at `/docs`.

All `/api/v1/*` endpoints (except `/auth/login`, `/public/verify/*`, and edge endpoints) require:

```
Authorization: Bearer <jwt>
```

Edge endpoints (under `/edge/`) require an **edge** bearer token issued by `POST /edge/enroll`.

## Auth + identity

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Email + password → access_token |
| `GET` | `/api/v1/me` | Current user + memberships |
| `GET` | `/api/v1/organizations/current` | Active organization |

## Assets

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/assets` | List org assets |
| `POST` | `/api/v1/assets` | Create asset (+ compute profile) |
| `GET` | `/api/v1/assets/{asset_id}` | Read asset |
| `PATCH` | `/api/v1/assets/{asset_id}` | Update name/description/category |

## Evidence

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/assets/{asset_id}/evidence` | List items |
| `POST` | `/api/v1/assets/{asset_id}/evidence/upload` | Multipart upload · SHA-256 server-side |
| `GET` | `/api/v1/assets/{asset_id}/manifest` | Current manifest |
| `POST` | `/api/v1/assets/{asset_id}/manifest/regenerate` | Force regen |

## Research

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/assets/{asset_id}/research/private` | Lexical search over org+asset chunks |
| `POST` | `/api/v1/assets/{asset_id}/research/public` | Brave LLM Context · public market |
| `GET` | `/api/v1/assets/{asset_id}/research/sessions` | All sessions for the asset |
| `GET` | `/api/v1/research/sessions/{id}` | Single session |

## AIOV

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/assets/{asset_id}/aiov/generate` | Generate / regenerate a draft (Kimi when configured) |
| `GET` | `/api/v1/assets/{asset_id}/aiov` | All versions |
| `GET` | `/api/v1/assets/{asset_id}/aiov/{analysis_id}` | One version |

## Validator

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/assets/{asset_id}/validator/run` | Run the 12 deterministic checks |
| `GET` | `/api/v1/assets/{asset_id}/validator/latest` | Latest review |

## Deeds

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/assets/{asset_id}/deeds` | Generate a new deed version (requires manifest + validator) |
| `GET` | `/api/v1/assets/{asset_id}/deeds` | All versions |
| `GET` | `/api/v1/deeds/{deed_id}` | Read a single deed |
| `POST` | `/api/v1/deeds/{deed_id}/publish` | ORG_ADMIN+ · publish to `/verify/{slug}` |

## ENS

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/ens/identities` | List org reservations |
| `POST` | `/api/v1/ens/reserve` | Mock reservation under `defendable.eth` |
| `GET` | `/api/v1/ens/identities/{id}` | Read |
| `POST` | `/api/v1/ens/identities/{id}/prepare-public-records` | Compose privacy-safe text-record payload |

## Edge

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/edge/nodes` | List org devices |
| `POST` | `/api/v1/edge/enrollment-tokens` | ORG_ADMIN+ · create one-time token |
| `POST` | `/api/v1/edge/enroll` | Device-side · swap token for edge_token + node ID |
| `POST` | `/api/v1/edge/heartbeat` | Device · update last_heartbeat_at |
| `POST` | `/api/v1/edge/assets/{asset_id}/evidence` | Device · upload evidence (hash-verified) |
| `POST` | `/api/v1/edge/assets/{asset_id}/benchmark-receipts` | Device · alias for BENCHMARK_OUTPUT |

## Public verification

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/public/verify/{slug}` | Privacy-filtered deed view |
| `GET` | `/api/v1/public/verify/{slug}.json` | Same payload as raw JSON |

## Audit

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/assets/{asset_id}/audit` | Audit events for the asset |

## Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/healthz` | Service + integration status (`brave_configured`, `kimi_configured`, `ens_mode`) |
