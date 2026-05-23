# Compute Bench Receipts

Public-safe subset of `defendable-compute` bench bundles. The full
bundles (including PRIVATE_EVIDENCE + DERIVED_DATASETS artifacts)
live in the operator's local Evidence Vault and are **never**
committed to this repo.

See [`docs/EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md`](../../docs/EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md)
for the doctrine. See `.gitignore` in this directory for the
enforcement list.

## What's tracked here

Per bundle:

- `asset_identity.json` · public-safe identity (no raw serial)
- `runtime_environment.json` · OS · driver · CUDA · tool versions
- `benchmark_plan.json` · what would run / did run
- `workload_compatibility.json` · what the asset demonstrated
- `public_safe_attestation.json` · the canonical public record · 4 grades + bundle hash
- `manifest.sha256` · per-file hashes + bundle hash (anchors the chain)
- `ddeed-*.json` · the Defendable Deed JSON referencing the bundle

## What's NEVER tracked here

- `private_identity_reference.json` · raw serials · UUIDs · PCI bus IDs · hostnames
- `system_manifest.json` · full host context including private fields
- `health_diagnostic.json` · capture-time telemetry detail
- `thermal_power_trace.jsonl` · streaming power/thermal samples
- `benchmark_results.json` · raw workload outputs
- `validator_flags.json` · internal capture warnings
- `best_next_use_inputs.json` · operator-attested deployment context
- `evidence_classification.json` · internal vault map

## Bundles indexed here

| Bundle | Host | Asset | Captured | Bundle Hash | Deed |
|---|---|---|---|---|---|
| `swarmrails/cb-20260523T025801Z-2d4e/` | swarmrails | NVIDIA RTX PRO 6000 Blackwell (E6 · GPU 0) | 2026-05-23T02:58:01Z | `sha256:3a5717285f1de11d5adec2c77300e3505c3395f2074532d6b1d3b067e1075747` | `DDEED-DOV-COMPUTE-000001-BENCH-v1` |

## Verification

Operators verify a tracked public-safe attestation by:

1. Pulling the full bundle from their local Evidence Vault
2. Running `python3 -m defendable_box.compute.manifest <bundle_dir>` (or recomputing per-file SHA-256)
3. Confirming the recomputed `bundle_sha256` matches the `bundle_hash` in the tracked `public_safe_attestation.json`

The deed JSON's `bench_attestation.bundle_hash` and `evidence_packet.manifest_sha256`
both must match the bundle's `manifest.sha256` `bundle_sha256` field.
