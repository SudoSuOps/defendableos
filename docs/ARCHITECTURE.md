# Architecture

DefendableOS is an evidence-backed asset intelligence platform built around a single doctrine:

> **Evidence is the permanent record. AI analysis is not the source of truth.**

This document describes how the services compose, where data lives, and how a single asset moves from intake to a public verification record.

## Service boundaries

```
   ┌───────────────────────────────────────────────────────────────────────┐
   │  apps/web · Next.js 14 portal · Tailwind · TypeScript                 │
   │  └──── browser ── lib/api.ts ── Bearer JWT (localStorage)             │
   └────────────────────────────────┬──────────────────────────────────────┘
                                    │  HTTPS · CORS to WEB_BASE_URL
   ┌────────────────────────────────▼──────────────────────────────────────┐
   │  services/api · FastAPI · Pydantic v2 · SQLAlchemy 2 · Alembic        │
   │  ┌───────────────────────────────────────────────────────────────┐    │
   │  │ /api/v1/ ── auth · organizations · assets · evidence ·        │    │
   │  │              research · aiov · validator · deeds · ens ·     │    │
   │  │              edge · public · audit                            │    │
   │  └──────────────┬───────────────┬──────────────────┬──────────────┘    │
   │  ┌──────────────▼──────┐  ┌─────▼────────┐  ┌─────▼─────────────┐    │
   │  │ services/storage     │  │ integrations  │  │ services/ens     │    │
   │  │ MinIO S3 wrapper     │  │ brave +       │  │ mock · ccip ·    │    │
   │  │ SHA-256 on every put │  │ model gateway │  │ wrapped adapters │    │
   │  └──────────────┬──────┘  │ (Kimi K2.6)   │  └──────────────────┘    │
   │                 │         └───────┬───────┘                            │
   └─────────────────┼─────────────────┼────────────────────────────────────┘
                     │                 │
            ┌────────▼────────┐  ┌─────▼───────────────┐
            │ Postgres 16     │  │ Brave LLM Context   │  ┌─────────────┐
            │ pgvector-ready  │  │ Moonshot (Kimi)     │  │ Defendable  │
            │ + JSONB         │  └─────────────────────┘  │ Box edge    │
            └─────────────────┘                            │ (Python CLI)│
            ┌─────────────────┐                            └─────┬───────┘
            │ MinIO buckets:  │                                  │
            │  defendable-private (raw, manifests, deeds)        │
            │  defendable-public  (deed-public.json on publish)  │
            └─────────────────────────────────────────────────────┘
```

## Data flow · one asset, end-to-end

1. **Asset intake** (`POST /api/v1/assets`) creates an `Asset` + `ComputeAssetProfile`
2. **Evidence upload** (`POST /api/v1/assets/{id}/evidence/upload`):
   - Validates content-type + size
   - Computes SHA-256 server-side
   - Stores raw bytes in `defendable-private/organizations/{org}/assets/{id}/raw/`
   - Synchronously extracts text (PDF / JSON / CSV / TXT) → `evidence_chunks`
   - Regenerates the current `EvidenceManifest` and writes JSON to `…/manifests/manifest_vN.json`
3. **Research** captures both lanes:
   - `research/private` → lexical search over `evidence_chunks` scoped to (org_id, asset_id)
   - `research/public` → Brave LLM Context API → sources stored with retrieved_at + UNKNOWN classification
4. **AIOV draft** (`POST /api/v1/assets/{id}/aiov/generate`):
   - Selected evidence + sources passed through `services/aiov.py`
   - Model gateway (Kimi K2.6 when configured) returns prose + structured JSON
   - Local scaffold backs the analysis when no model is configured, ensuring no fake "live" results
5. **Validator run** (`POST /api/v1/assets/{id}/validator/run`):
   - Deterministic 12-check suite (see `services/validator_checks.py`)
   - Builds a receipt JSON with `receipt_sha256`
   - Status: `PASSED_FOR_PACKAGING` or `FAILED_REQUIRES_REPAIR`
6. **Deed generation** (`POST /api/v1/assets/{id}/deeds`):
   - Requires manifest + validator (and non-failed status)
   - Versions monotonically; older versions become `SUPERSEDED`
   - `deed_json.record_hash` is deterministic over the payload
7. **Public publication** (`POST /api/v1/deeds/{id}/publish`, ORG_ADMIN+):
   - `filter_public_payload` strips serial numbers, purchase costs, narratives, private filenames
   - Mirror to `defendable-public/verification/{slug}/deed-public.json`
   - `/verify/{slug}` reads the filtered payload only
8. **ENS reservation** (mock by default) attaches an identity name; live writes require explicit opt-in
9. **Defendable Box** (edge agent) hashes locally → uploads → backend re-hashes → mismatch rejects the upload

Every state-changing action records an `AuditEvent`.

## Storage strategy

- **Postgres** holds all transactional state. UUID PKs internally, human public references separately.
- **JSONB** on `manifest_json`, `analysis_json`, `deed_json`, `extra_metadata` keeps schemas flexible.
- **pgvector** is reserved for future semantic retrieval; MVP uses lexical search for predictable behaviour.
- **MinIO** holds raw evidence and the published deed-public.json. The private bucket is never anonymous-readable.

## Tenancy

Every query that touches private state filters by `organization_id` derived from the current membership. Edge-node uploads are double-gated: the token authenticates the node and the asset must belong to the node's organization.
