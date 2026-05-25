# Object Storage Record Layout · v0.1

> How Defendable Compute Proof Receipts and their evidence artifacts are
> laid out in the existing `streetledger/` Tigris object-storage namespace
> used by `defendableos-api`.

## Top-level namespace

The compute receipt domain lives under `streetledger/compute/`. This is a
sibling of the existing receipt rails (`streetledger/runs/`,
`streetledger/swarmjelly/`, `streetledger/ledger/`).

```
streetledger/
  compute/
    assets/
      {asset_id}/
        identity/
        observations/
        benchmarks/
        receipts/
        hashes/
        valuation_future/        ← reserved for AIOV product, not populated by DCPR
```

## `identity/`

One file per identity observation:

```
streetledger/compute/assets/{asset_id}/identity/
  {YYYYMMDDTHHMMSSZ}_compute_asset_identity.json
```

Each file is the standalone `compute_asset_identity` JSON object from the
schema. Multiple identity observations over time form a history; the latest
one is referenced by the active receipt.

## `observations/`

Per-receipt service-state observations:

```
streetledger/compute/assets/{asset_id}/observations/
  {receipt_id}/
    precheck.json
    post_remediation.json
```

Each file is a standalone `service_state_observation` JSON object.

## `benchmarks/`

Per-receipt benchmark observations + raw evidence:

```
streetledger/compute/assets/{asset_id}/benchmarks/
  {receipt_id}/
    benchmarks.json
    evidence/
      {YYYYMMDDTHHMMSSZ}_{phase}_{tool}.{ext}
```

`benchmarks.json` is the `benchmark_validation_results[]` array. The
`evidence/` directory holds the raw command/platform output that backs
each observation.

## `receipts/`

The canonical Proof Receipts:

```
streetledger/compute/assets/{asset_id}/receipts/
  {receipt_id}.json     ← compute_proof_receipt
  {receipt_id}.md       ← human-readable twin
  {receipt_id}.manifest.json
```

Plus a small `index.json` at the asset root listing every receipt:

```
streetledger/compute/assets/{asset_id}/receipts/
  index.json   ← [{receipt_id, created_at, use_case, verdict, supersedes}, ...]
```

The index is what consumers (Vast listing renderer, AIOV indexer) hit first.

## `hashes/`

Tamper-evidence:

```
streetledger/compute/assets/{asset_id}/hashes/
  {receipt_id}.SHA256SUMS.txt
```

Each row is `{sha256}  {relative_path_within_asset}`. Independent
verifiers fetch this file and recompute hashes over the named artifacts.

## `valuation_future/`

**Empty for DCPR v0.1.** Reserved for AIOV product artifacts when AIOV ships.
The namespace exists so the AIOV product can publish into a sibling of
condition records, with the same `asset_id` linkage and the same hash
discipline, but with its own schema family.

## Cross-references with existing rails

The existing `defendableos-api` ledger publisher (PR #7 on defendableos)
publishes deeds under:

```
streetledger/records/deeds/{slug}.json
streetledger/records/index.json
```

The smash spine publishes receipts/verdicts/pairs/audits under:

```
streetledger/runs/{run_id}/...
streetledger/swarmjelly/{tier}/...
streetledger/ledger/defendable_ledger.jsonl
```

The compute rail is a sibling, not a child, of those. They share the same
storage backend, the same hash discipline, and the same DefendableLedger
anchoring pattern.

## Publication contract

Once a HONEY receipt is produced and the operator chooses to publish:

1. The receipt files are uploaded via the existing GitHub Contents API
   publisher pattern (`defendableos/services/api/app/services/ledger_publisher.py`).
2. A `DLR-{YYYYMMDD}-{ULID}` ledger record is appended to
   `streetledger/ledger/defendable_ledger.jsonl` with `record_type=DCPR`
   (extending the existing GENESIS/RECEIPT/VERDICT/PAIR/AUDIT taxonomy
   from the smash ledger).
3. The new ledger record's `payload_hash` is the sha256 of the
   `compute_proof_receipt.json` file.
4. The `parent_hash` is the previous ledger record's `record_sha256`, per
   the existing hash-chain doctrine.

## Privacy treatment in storage

Receipts published with `privacy_treatment=full` carry their hardware
identifiers in cleartext. Receipts published with `salted_hash` carry
salted SHA-256 of identifiers; the salt is stored ONLY in the operator's
local environment, never in the published artifact.

Operators publishing for customer-facing use cases (Vast listing, eBay,
ITAD intake) should default to `redacted` for any field that does not
help the customer evaluate the asset.

## Retention

Object storage records inherit the retention policy from
`protocol/evidence_capture_requirements.md`:

- HONEY: ≥ 7 years
- JELLY: ≥ 1 year or until superseded
- PROPOLIS: ≥ 7 years (failure training data)

Once published to DefendableLedger, records are append-only and cannot be
modified — a correction is a new receipt with `supersedes` pointing at the
prior receipt_id.
