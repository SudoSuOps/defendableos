# Benchmark Validation Protocol · v0.1

> What constitutes valid benchmark evidence for a Defendable Compute Proof
> Receipt, and how each test class maps to claim boundaries.

## Hierarchy of evidence

Tests are ordered by signal strength. Receipts may include any subset; the
Tribunal gate weights higher-rank tests more heavily.

| rank | origin | examples | weight |
| ---: | --- | --- | --- |
| 1 | `OEM` | NVIDIA Field Diagnostics, vendor-issued health reports | highest |
| 2 | `platform_remote` | Vast.ai validator suite, RunPod machine-test, Coreweave preflight | high |
| 3 | `third_party` | Independent benchmark harness with reproducible artifacts (e.g., MLPerf, gpu-burn run by named third-party) | medium |
| 4 | `local` | Operator-run local benchmarks | lowest (medium confidence at best) |

## Required tests per use case

### use_case = `rental_readiness`

- Minimum:
  - 1 `runtime_visibility` test (proves runtime sees the GPU)
  - 1 `functional_inference` test (proves the GPU computes)
  - 1 `stress_combined` test ≥ 60s (proves it holds load briefly)
- Strongly recommended:
  - 1 `ecc_health` test
  - 1 `distributed_communication` test (even single-GPU NCCL is useful)

The smash example contains all of the above via the Vast.ai remote validator.

### use_case = `resale_readiness`

- Same as `rental_readiness` PLUS:
  - 1 `thermal_response` test of ≥ 5 minutes sustained load (resale buyers
    need to see beyond the 60s smoke test)
  - 1 `memory_inventory` test confirming `vram_total_mib` matches OEM spec
    (counterfeit GPU detection)

### use_case = `disposition_intake`

- Minimum:
  - 1 `runtime_visibility` test (confirms the GPU is functional enough for re-use)
  - 1 `ecc_health` test (confirms memory not silently degrading)
- Stress tests are optional for ITAD intake because the asset's next-life path
  may not require sustained operation.

### use_case = `fleet_audit`

- Minimum:
  - 1 `identity_check` test per host
- Benchmark validation may be empty if the audit is identity-only.

## Test_scope semantics

| test_scope | what it establishes |
| --- | --- |
| `identity_check` | Asset is what it claims to be (model, vram, driver). |
| `runtime_visibility` | The named runtime can see the GPU. |
| `memory_inventory` | Reported VRAM matches OEM spec; no silent memory loss. |
| `process_inventory` | No unintended processes are using the GPU. |
| `functional_inference` | The GPU computes a known workload to a known output. |
| `stress_compute` | Sustained compute load at high utilization. |
| `stress_memory` | Sustained memory bandwidth load. |
| `stress_combined` | Concurrent CPU + GPU load. |
| `network_throughput` | Host network reaches expected bandwidth. |
| `storage_throughput` | Host storage reaches expected bandwidth. |
| `ecc_health` | Memory ECC error counters within policy. |
| `thermal_response` | GPU thermal behavior under sustained load. |
| `power_response` | GPU draws expected power; cap enforcement working. |
| `distributed_communication` | NCCL / collective communication functional. |

## Limitations field is mandatory

Every benchmark observation MUST carry a `limitations` plain-text statement
naming what the test does NOT establish. Example:

> "Single-pass ResNet18 functional check confirms inference path works;
> does NOT establish sustained throughput, accuracy at scale, or fitness for
> production workloads."

Receipts where any benchmark observation has empty `limitations` are
Tribunal-rejected as `CLAIM_EXCEEDS_EVIDENCE`.

## Evidence preservation

Every benchmark result MUST point at an evidence artifact via
`evidence_locator`. The artifact may be:

- A stdout log file with full timestamps
- A JSON output from the test harness
- A signed report from the platform validator
- A screenshot (PNG) with operator timestamp

Evidence artifacts are stored under `receipts/{receipt_id}/evidence/` and
sha256'd. The hash appears in `generated_artifact_hashes`.

## Anti-patterns to refuse

- A benchmark observation with `result=pass` but empty `observed_output`.
  → Tribunal rejects as inadequate evidence.
- A benchmark observation with `test_origin=local` but `confidence=high`.
  → Local tests cannot achieve high confidence without third-party
  reproducibility evidence.
- A `stress_combined` test with `duration_seconds_if_known < 60`.
  → 60 seconds is the v0.1 minimum stress duration for `rental_readiness`.
- A test result claiming "passed all NCCL collectives" when only one collective
  was actually run.
  → Use the exact collective name(s) tested.

## Reproducibility expectations

Platform-remote tests are not generally reproducible by third parties; the
trust anchor is the platform's own attestation. Operators publishing receipts
on platforms with no API attestation should run a `third_party` independent
benchmark to anchor at least one test result.
