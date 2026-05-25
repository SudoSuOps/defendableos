# Defendable Compute CLI · v0.1 Specification

> Specification only. **No hardware execution is implemented in v0.1.**
> The v0.2 implementation will follow this contract exactly.

## Binary

`defendable-compute`

## Global flags

| flag | default | purpose |
| --- | --- | --- |
| `--receipt-dir` | `./receipts` | Where receipt artifacts are written. |
| `--evidence-dir` | `{receipt-dir}/{receipt_id}/evidence` | Where raw evidence artifacts are written. |
| `--asset-id` | derived from hostname + GPU UUID hash | Override the asset_id for this run. |
| `--operator-name` | `$USER` on the host | Operator name to embed in receipts. |
| `--operator-role` | `host_operator` | One of: `host_operator`, `fleet_owner`, `audit_agent`, `itad_intake`, `broker`. |
| `--privacy` | `salted_hash` | One of: `full`, `salted_hash`, `redacted`. |
| `--platform` | `vast_ai` | Rental platform context: `vast_ai`, `runpod`, `coreweave`, `lambda_labs`, `crusoe`, `none`. |
| `--no-color` | false | Disable ANSI in stdout. |
| `--verbose` | false | Verbose stdout. |

## Subcommands

### `defendable-compute intake`

Bootstraps a new receipt run. Creates `{receipt-dir}/{receipt_id}/` with
empty `evidence/` and a stub `receipt.json` marked
`tribunal_verdict.verdict=null`.

```
defendable-compute intake \
  --use-case rental_readiness \
  --power-cap-w 550 \
  --thermal-warning-c 80 \
  --thermal-shutdown-c 90
```

Produces:
- `receipts/{receipt_id}/intake.json` (intake parameters)
- `receipts/{receipt_id}/receipt.json` (stub)

### `defendable-compute observe`

Executes Phase 1 + Phase 2 (READ-ONLY) and populates
`asset_identity` + `precheck_state` + `findings`.

```
defendable-compute observe --receipt-id DCPR-...
```

Default mode is **read-only**. The CLI will refuse to execute any state-changing command in this subcommand.

Produces:
- `receipts/{receipt_id}/evidence/*.txt|csv|json`
- Updated `receipts/{receipt_id}/receipt.json` with precheck and findings populated.

### `defendable-compute remediate-plan`

Generates a remediation plan from findings without executing it.

```
defendable-compute remediate-plan --receipt-id DCPR-...
```

Output: `receipts/{receipt_id}/remediation_plan.md` listing each finding,
proposed action, expected outcome, and required operator confirmation.

### `defendable-compute remediate`

Executes remediation. **Requires operator confirmation per finding.**

```
defendable-compute remediate --receipt-id DCPR-... \
  --finding GPU_MEMORY_HELD_BY_LOCAL_PROCESS \
  --confirm
```

If `--confirm` is absent, the CLI prompts interactively. In non-interactive
contexts (CI) the run aborts without `--confirm`.

The CLI refuses to remediate findings classified PROPOLIS-only without
`--allow-propolis-remediation` (an escape hatch for operators who know what
they are doing).

Rental-platform services are never touched. Docker daemon is never
restarted without `--allow-docker-restart` (not supported in v0.1).

### `defendable-compute validate`

Triggers Phase 6 platform-remote validation. Captures the platform's
output stream and produces `benchmark_observation[]` entries.

```
defendable-compute validate --receipt-id DCPR-... --platform vast_ai
```

For `vast_ai`, this is a thin wrapper that invokes the vast.ai validation
command and captures its output. For other platforms it requires a custom
adapter.

Produces:
- `receipts/{receipt_id}/evidence/{timestamp}_platform_remote_validation.txt`
- Updated `receipt.json` with `benchmark_validation_results` and
  `service_state_results` populated.

### `defendable-compute receipt`

Finalizes the receipt: applies the Tribunal gate, lints for banned
vocabulary, computes all artifact hashes, and writes the final
`receipt.json` + `receipt.md` + `manifest.json` + `SHA256SUMS.txt`.

```
defendable-compute receipt --receipt-id DCPR-... [--lint] [--format both]
```

Sub-flags:
- `--lint` runs the receipt-linter without finalizing (read-only).
- `--format both` (default) emits both JSON and Markdown.
- `--format json` emits JSON only.
- `--format md` emits Markdown only.
- `--no-honey` forces verdict to JELLY or PROPOLIS (for operator override).

If the linter fails, the CLI refuses to write the receipt and exits non-zero.

### `defendable-compute verify-hashes`

Recomputes sha256 over every artifact named in `manifest.json` and
compares to the recorded hashes. Exits 0 if all match, non-zero if any
mismatch.

```
defendable-compute verify-hashes --receipt-id DCPR-...
```

This is what an independent consumer would run to verify a published receipt.

## Hard contracts

The CLI enforces these invariants regardless of flags:

1. **Default read-only.** `observe` is the only subcommand that runs in
   read-only mode by default. All others require explicit confirmation.
2. **Operator confirmation for remediation.** No remediation runs without
   per-finding `--confirm` or interactive confirmation.
3. **Raw output preserved as evidence.** Stdout/stderr of every executed
   command is captured to disk before any parsing.
4. **Hash on capture.** Every artifact is hashed immediately after
   creation, before the next phase runs.
5. **No valuation conversion.** No CLI path converts a benchmark result
   directly into a value statement. Banned terms in any output field cause
   the CLI to exit non-zero.
6. **Dual output.** Final receipt is written in both JSON (schema-validated)
   and Markdown (human-readable).
7. **No platform-service mutation.** The CLI refuses to start, stop,
   restart, or reconfigure rental-platform services (`vastai`,
   `vast_metrics`, RunPod equivalents).
8. **No Docker daemon restart.** Not supported in v0.1.
9. **No NVIDIA driver / power-limit change** without an explicit
   `--allow-baseline-restore` flag and per-change operator confirmation.

## Exit codes

| code | meaning |
| --- | --- |
| 0 | success |
| 1 | generic failure |
| 2 | finding(s) classified PROPOLIS by default; receipt cannot be HONEY |
| 3 | banned vocabulary detected in receipt fields |
| 4 | hash drift detected (verify-hashes) |
| 5 | operator confirmation missing in non-interactive mode |
| 6 | platform-remote validation not available for the configured platform |
| 7 | required evidence artifact missing |
| 8 | schema validation failed |
