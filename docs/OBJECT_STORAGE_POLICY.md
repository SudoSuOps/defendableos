# Object Storage Policy · MinIO local · Tigris production

The Goods Vault stores objects in FOUR logically separated buckets,
each with its own privacy boundary. The same boto3 client speaks to
MinIO (local) and Tigris (production) because both are S3-sigv4.
The doctrine boundary is enforced at the SERVICE layer in
`app/services/artifacts.py`, not at the bucket policy alone.

## The 4 buckets

```
defendable-private-evidence-prod      ← PRIVATE_EVIDENCE
defendable-market-observations-prod   ← MARKET_OBSERVATIONS
defendable-derived-datasets-prod      ← DERIVED_DATASETS
defendable-public-assets-prod         ← PUBLIC_ASSETS
```

The bucket names live in environment variables · production
deployments override `S3_PRIVATE_EVIDENCE_BUCKET` etc. to whatever
the Tigris bucket is actually called.

## Privacy boundaries

| Privacy class | What's in it | Public reachable? |
|---|---|---|
| `PRIVATE_EVIDENCE` | Client uploads, deed evidence, founder transaction proofs | NEVER |
| `MARKET_OBSERVATIONS` | Brave raw responses, eBay raw responses, normalized observation batches | NEVER |
| `DERIVED_DATASETS` | Pair JSONL, eval pack, manifest, SHA256SUMS | NEVER |
| `PUBLIC_ASSETS` | Privacy-filtered `/verify/{slug}/deed-public.json`, MarketReady media after approval | YES, after privacy filter |

`public_export_or_refuse()` in `app/services/artifacts.py` raises
`PermissionError` if asked to return bytes from anything other than
`PUBLIC_ASSETS`. There is no exception path. Tests
`test_public_export_refuses_*` in `test_goods_doctrine.py` are the
canary.

## Object key layout

### Private evidence
```
org/{org_id}/asset/{asset_id}/raw/{artifact_id}/{filename}
org/{org_id}/asset/{asset_id}/normalized/{artifact_id}.json
org/{org_id}/asset/{asset_id}/manifests/{manifest_id}.json
org/{org_id}/asset/{asset_id}/validator/{receipt_id}.json
org/{org_id}/asset/{asset_id}/deeds/{deed_id}.json
```

### Market observations
```
provider/brave/{yyyy}/{mm}/{dd}/{run_id}/raw-response.json
provider/brave/{yyyy}/{mm}/{dd}/{run_id}/normalized-signals.json
provider/ebay/{yyyy}/{mm}/{dd}/{run_id}/raw-response.json
provider/ebay/{yyyy}/{mm}/{dd}/{run_id}/normalized-observations.json
goods/{goods_id}/observations/{observation_id}.json
comp-sets/{comp_set_id}/comp-set.json
receipts/{receipt_id}.json
```

### Derived datasets
```
pairs/{goods_class}/{batch_id}/candidates.jsonl
pairs/{goods_class}/{batch_id}/approved-eval.jsonl
pairs/{goods_class}/{batch_id}/approved-training.jsonl
manifests/{dataset_id}/manifest.json
manifests/{dataset_id}/SHA256SUMS.txt
receipts/{dataset_id}/validator-receipt.json
deeded/{dataset_id}/deed.json
```

### Public assets
```
verify/{public_slug}/deed-public.json
marketing/{asset_id}/images/
marketing/{asset_id}/videos/
marketing/{asset_id}/booklets/
marketing/{asset_id}/channel-exports/
showcase/{asset_id}/
```

## The ArtifactRegistry table

Every write goes through `artifacts.put_artifact()`, which:

1. Computes SHA-256 over the bytes.
2. Picks the bucket via `_bucket_for_privacy_class()`.
3. Writes the object (only if `OBJECT_STORAGE_LIVE_ENABLED=true`).
4. Inserts an `artifact_registry` row capturing bucket, key,
   sha256, byte_size, privacy_class, rights_status, owner_org,
   asset_id, goods_id, discovery_run_id, pair_batch_id, mime_type,
   retention_policy.

The registry is the single source of truth · queries like "list
every pair-candidate JSONL produced in 2026-05" go through it.

## Provider toggle

```bash
OBJECT_STORAGE_PROVIDER=minio   # local dev
OBJECT_STORAGE_PROVIDER=tigris  # Fly production
S3_ENDPOINT_URL=...             # provider-specific
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_REGION=us-east-1
OBJECT_STORAGE_LIVE_ENABLED=false   # default · flip to true in prod
S3_PRESIGNED_URL_TTL_SECONDS=900
```

When `OBJECT_STORAGE_LIVE_ENABLED=false`, all writes hash + register
WITHOUT a network PUT. This is the safe default for tests and local
dev · no surprise object writes during pytest runs.

## Local dev

The existing `infrastructure/docker-compose.yml` already runs MinIO
with `minioadmin/minioadmin` and exposes ports 9000/9001. The 4
buckets need to be created once · run from any host:

```bash
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/defendable-private-evidence-prod
mc mb local/defendable-market-observations-prod
mc mb local/defendable-derived-datasets-prod
mc mb local/defendable-public-assets-prod
```

Or set the env vars to your existing legacy bucket names if you
prefer.

## Production setup (Fly + Tigris)

Documented in `docs/FLY_DEPLOYMENT_PREPARATION.md` (next session).
TL;DR:

1. `flyctl storage create` for each of the 4 buckets.
2. Capture the access keys.
3. `flyctl secrets set S3_ENDPOINT_URL=... S3_ACCESS_KEY_ID=... ...`.
4. `OBJECT_STORAGE_PROVIDER=tigris OBJECT_STORAGE_LIVE_ENABLED=true`.
5. NO BUCKET MAY BE PUBLIC UNTIL the privacy-filter audit passes.
