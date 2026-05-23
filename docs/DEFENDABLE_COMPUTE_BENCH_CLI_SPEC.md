# Defendable Compute Bench · CLI Specification

The bench CLI lives under the existing `defendable-box` package at
`services/edge-agent/`. The Phase A MVP **extends** the existing CLI
rather than introducing a new binary · this keeps the install
footprint small (`pip install -e services/edge-agent/`) and reuses
the existing SHA-256 + evidence-upload plumbing.

## Command surface (Phase A · this turn)

```bash
defendable-compute inspect \
  --profile auto \
  --output ./runs \
  [--gpu 0] \
  [--scope quick|standard|extended]
```

Captures hardware identity · system manifest · runtime environment ·
basic telemetry snapshot · generates the structured JSON receipt
bundle · writes `manifest.sha256` and `public_safe_attestation.json`.
**Phase A is read-only · no diagnostics tests · no workload tests ·
no system mutation.**

## Future commands (Phase B / Phase C · documented · not implemented)

```bash
defendable-compute diagnose --asset <id> --level quick
defendable-compute benchmark --asset <id> --profile e6-institutional
defendable-compute attest --run <run_id>
defendable-compute validate --run <run_id>
defendable-compute export-public-safe --run <run_id>
defendable-compute best-next-use --asset <id> --run <run_id>
```

Optional future:

```bash
defendable-compute reattest --asset <id>
defendable-compute vast-import --asset <id> --receipt-path <path>
defendable-compute deed-draft --asset <id> --run <run_id>
```

## Phase A · `inspect` semantics

### Invocation

```bash
defendable-compute inspect --output ./runs --scope quick
```

### What it does

1. Generates a `<run_id>` of the form `cb-<UTC ISO compact>-<short rand>`
2. Creates `./runs/<run_id>/` directory
3. Discovers asset class from the host:
   - GPU present? → captures per-GPU identity via `nvidia-smi`
   - No GPU? → E0 CPU-only node profile
4. Captures and writes the bundle files:
   - `asset_identity.json` · public-safe identity
   - `private_identity_reference.json` · raw serial / UUID / PCI bus ID (PRIVATE)
   - `system_manifest.json` · CPU + RAM + storage + network
   - `runtime_environment.json` · OS + kernel + driver + runtime versions
   - `health_diagnostic.json` · telemetry snapshot (idle · no load)
   - `evidence_classification.json` · per-artifact vault + rights map
   - `validator_flags.json` · any warnings the local capture noted
   - `best_next_use_inputs.json` · placeholders for operator-attested fields
   - `manifest.sha256` · sorted-key JSON manifest, hashed
   - `public_safe_attestation.json` · derived via the same
     public_export_or_refuse() guard the rest of the platform uses
5. Prints the run_id, bundle path, manifest hash, and the four
   grades (Identity · Health · Utility · Evidence)

### What it does NOT do (Phase A)

- Run any workload test
- Run any sustained-load diagnostic (no DCGM full diag · no FP16 burn)
- Change any system setting · clock · power cap · driver
- Upload anything · the bundle stays local
- Touch GPU 1 on swarmrails (or any occupied GPU on any host)
- Issue a deed
- Mark anything `BENCHMARK_ATTESTED` (that's Phase B/C with workload)

### Safety pre-flight (always runs)

Before writing any file:

1. **Detect occupied GPUs** via `nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv`
2. If the chosen `--gpu` index has an active process, raise `BenchSafetyError` with the process list
3. To bypass, the operator must pass `--force-occupied-gpu` AND retype the GPU's PCI Bus ID as confirmation
4. Even with bypass, Phase A only reads identity · it never runs workloads

### Output to stdout

```
defendable-compute inspect · cb-20260523T024500Z-9f2c

  Asset class       COMPUTE_HARDWARE
  Asset tier        E6
  Model             NVIDIA RTX PRO 6000 Blackwell
  VRAM              96 GB
  Host              swarmrails · Xeon Sapphire Rapids
  Driver            590.48.01 · CUDA 13.1

  IDENTITY    A · PRIVATE_IDENTIFIER_CAPTURED_AND_HASHED
  HEALTH      PASS_WITH_OBSERVATIONS  (idle snapshot only · Phase A)
  UTILITY     UTILITY_NOT_YET_MEASURED
  EVIDENCE    C · IDENTITY_AND_RUNTIME_ONLY

  Bundle      ./runs/cb-20260523T024500Z-9f2c/
  Manifest    sha256:a1b2c3d4e5f6...
  Public safe ./runs/cb-20260523T024500Z-9f2c/public_safe_attestation.json

  ⚠  Phase A · UTILITY grade requires Phase B/C workload tests.
     This bundle is an identity + runtime + health snapshot only.
     Run `defendable-compute benchmark --profile e6-institutional --gpu 0`
     when a safe maintenance window is confirmed.
```

## CLI design requirements

- **Read-only by default** · Phase A enforces this in code · Phase B/C add explicit operator confirmations
- **Never change GPU clocks · power limits · runtime configuration** unless a future explicit operator mode is designed (documented as `--unsafe-clock-edit` · NOT implemented this turn)
- **Warn before stress/load tests** · Phase B/C
- **Test scopes** · `quick` · `standard` · `extended` · per-profile durations from `COMPUTE_BENCH_PROFILE_MATRIX.md`
- **Tool versions captured** · every external command's version goes into `runtime_environment.json`
- **Every run timestamped** · `captured_at` ISO 8601 UTC · `run_id` carries the timestamp
- **Local first** · artifacts on disk before any upload is considered
- **All artifacts hashed** · `manifest.sha256` covers the bundle · bundle hash anchors deed JSON
- **Public-safe export redacts private fields** · `public_safe_attestation.json` produced via `public_export_or_refuse()`
- **Offline execution supported** · no network calls in Phase A
- **No automatic deed issuance** · the operator must explicitly route a bundle to the deed pipeline
- **Validator / founder approval required** before any public-safe issued output

## Integration with `defendable-box`

The `defendable-compute` CLI is implemented as a sibling typer app
under the same package:

```
services/edge-agent/
├── defendable_box/
│   ├── cli.py              # existing · defendable-box
│   ├── compute_cli.py      # new · defendable-compute
│   ├── compute/
│   │   ├── __init__.py
│   │   ├── capture.py      # identity · system · runtime capture
│   │   ├── manifest.py     # SHA-256 bundle hashing
│   │   ├── classify.py     # per-artifact vault + rights mapping
│   │   ├── public_safe.py  # public-safe export
│   │   └── safety.py       # occupied-GPU detection · bench-safety guards
│   └── client.py
├── pyproject.toml          # adds defendable-compute entry-point
```

Entry-point added to `pyproject.toml`:

```toml
[project.scripts]
defendable-box = "defendable_box.cli:app"
defendable-compute = "defendable_box.compute_cli:app"
```

## Founder-run commands (target: swarmrails)

After the MVP CLI lands on swarmrails:

```bash
# 1 · Install the CLI on swarmrails
cd ~/Desktop/defendableos/services/edge-agent
pip install -e .

# 2 · Run the read-only inspect on GPU 0 (founder-approved)
defendable-compute inspect --gpu 0 --output ~/compute-bench --scope quick

# 3 · Inspect the bundle
ls ~/compute-bench/cb-*/

# 4 · Read the public-safe attestation
cat ~/compute-bench/cb-*/public_safe_attestation.json
```

**Never** target GPU 1 · python3 PID 1335108 is serving production
Qwen3.5 workloads. The CLI refuses by default · `--force-occupied-gpu`
would require explicit PCI Bus ID confirmation.

## Related docs

- [`DEFENDABLE_COMPUTE_BENCH.md`](./DEFENDABLE_COMPUTE_BENCH.md) · umbrella
- [`COMPUTE_BENCH_RECEIPT_SCHEMA.md`](./COMPUTE_BENCH_RECEIPT_SCHEMA.md) · what gets written
- [`COMPUTE_BENCH_PROFILE_MATRIX.md`](./COMPUTE_BENCH_PROFILE_MATRIX.md) · per-tier profiles
- [`COMPUTE_BENCH_TOOLING_AUDIT.md`](./COMPUTE_BENCH_TOOLING_AUDIT.md) · what's installed where
