# GPU Host Post-Rental Protocol · v0.1

> Codified version of the actual smash RTX 5090 lifecycle on 2026-05-25.
> The CLI in v0.2+ will execute this protocol in read-only observation mode
> by default; remediation requires explicit operator confirmation.

## Scope

Applies to any GPU host that has just completed a rental cycle (Vast.ai,
RunPod, Coreweave-equivalent) and must be re-validated as rental-ready,
resale-ready, or fleet-audited.

## Pre-conditions

- Renter has confirmed exit OR the platform reports tenancy completed.
- Operator has SSH or equivalent shell access to the host.
- The platform-side validation harness (e.g., Vast.ai remote validator) is
  available for end-of-protocol use.

## Phase 1 · Identity capture (READ-ONLY)

1. `hostname` · capture host identifier.
2. `nvidia-smi --query-gpu=name,driver_version,memory.total,uuid,serial --format=csv,noheader`
   → record into `evidence/{timestamp}_nvidia_smi_identity.csv`.
3. `nvidia-smi --query-gpu=persistence_mode,power.max_limit --format=csv,noheader`
   → record into `evidence/{timestamp}_nvidia_smi_baseline.csv`.
4. Resolve identity to a stable `asset_id` (operator-assigned ULID or UUID).
5. Apply privacy treatment per `doctrine/terminology_and_claim_boundaries.md` §Identity privacy treatment.

Output: a `compute_asset_identity` JSON object.

## Phase 2 · Service state precheck (READ-ONLY)

1. **Docker:**
   - `docker ps -a` → expect zero containers.
   - `docker images` → expect zero images attributable to renter.
   - `docker info` → confirm `runc` and `nvidia` runtimes configured; storage driver healthy; CDI devices present.
2. **Model servers:**
   - `pgrep -fa 'vllm|ollama|llama_cpp|vllm.entrypoints'`
   - For each match, record `name`, `pid`, `vram_held_mib`, `command_line`, `owner`.
   - First-party model servers are findings (need remediation before rental-ready) but **not** PROPOLIS by themselves — see `gpu_host_post_rental_protocol.md` §Phase 5 for remediation flow.
3. **Rental platform services:**
   - `systemctl status vastai vast_metrics` (or equivalents for other platforms).
   - All expected services MUST be active; service-down conditions are PROPOLIS.
4. **GPU state:**
   - `nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw,power.max_limit,persistence_mode --format=csv,noheader`.
   - `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`.
5. **Storage mounts:** `df -h` → record critical mount health.
6. **Runtime liveness:** verify `nvidia_runtime_available`, `cdi_device_available`, `driver_loaded`, `nvml_responsive`.

Output: a `service_state_observation` JSON object reflecting precheck state.

## Phase 3 · Finding enumeration (DERIVED · NO EXECUTION)

Apply `protocol/failure_taxonomy.md` rules to the precheck state. For each
finding:

- record `finding_code`
- assign `severity` (informational / warning / blocker)
- name the `evidence_locator` artifact that surfaces the finding

Output: `contamination_or_residual_workload_findings` array.

If any finding has `severity = blocker` and `finding_code = UNVERIFIED_ASSET_IDENTITY` or
`finding_code = GPU_MEMORY_HELD_BY_UNKNOWN_PROCESS`, **STOP** the protocol and
issue a PROPOLIS receipt. Do not proceed to remediation.

## Phase 4 · Remediation plan (OPERATOR CONFIRMS BEFORE EXECUTION)

For each blocker finding the operator wishes to remediate:

1. Display the proposed action.
2. Require explicit operator confirmation (`y/N` prompt in CLI, or signed
   operator approval in CI).
3. Execute the action.
4. Capture stdout/stderr/exit status into `evidence/{timestamp}_remediation_{finding_code}.txt`.
5. Record a `remediation_actions[]` entry with `result` ∈
   {`resolved`, `partially_resolved`, `unresolved`}.

**Critical invariants:**

- Rental platform services (e.g., `vastai`, `vast_metrics`) are **never**
  touched by remediation. Touching them is a protocol violation.
- Docker daemon is not restarted unless an explicit `--allow-docker-restart`
  operator flag is supplied. v0.1 does not support this flag.
- No NVIDIA driver / power-limit / persistence change without an explicit
  operator-confirmed baseline-restore step.

## Phase 5 · Post-remediation state (READ-ONLY)

Re-run Phase 2 in full. Compare against the operating baseline:

- VRAM used ≤ `expected_idle_vram_mib_max`
- Utilization ≤ `expected_idle_utilization_percent_max`
- Power draw ≤ `expected_idle_power_w_max`
- Temperature ≤ `thermal_policy_c_warning`
- Persistence mode == documented baseline

If any baseline parameter is out of policy, **STOP** and either re-remediate
or issue JELLY/PROPOLIS.

Output: a second `service_state_observation` JSON object reflecting post-remediation state.

## Phase 6 · Platform-remote validation

Trigger the rental platform's own validation suite. For Vast.ai, this is the
sequence observed on smash:

- system requirements test
- ResNet18 GPU functional test
- ECC test
- NCCL distributed test (with the host's actual GPU count)
- simultaneous stress-ng + gpu-burn test (default 60s)
- test instance destroyed

Capture the full output (typically a platform-side console log + final
verdict) into `evidence/{timestamp}_platform_remote_validation.txt`.

For each test, populate a `benchmark_observation` with:
- `test_origin = platform_remote`
- `evidence_locator` pointing at the captured artifact
- `executed_by` naming the platform validator

If any test fails, the verdict cannot be HONEY.

## Phase 7 · Tribunal gating

Apply `doctrine/tribunal_gate.md` finding-class mapping rules. Refuse to
issue HONEY unless:

- All blocker findings resolved with operator-confirmed remediation
- Post-remediation state inside baseline policy
- All Phase 6 platform-remote tests passed
- Linter passes (no banned vocabulary in any field)

## Phase 8 · Receipt assembly

Combine:
- `compute_asset_identity` (Phase 1)
- `service_state_observation` precheck (Phase 2)
- findings (Phase 3)
- remediations (Phase 4)
- `service_state_observation` post (Phase 5)
- `benchmark_observation[]` (Phase 6)
- service_state_results summary
- operating_baseline
- tribunal_verdict (Phase 7)
- claim_boundaries (constant from doctrine)

Compute sha256 over every evidence artifact in `evidence/` and populate
`generated_artifact_hashes`.

Set `created_at` to current UTC.

Output: a `compute_proof_receipt` JSON object validated against
`schemas/compute_proof_receipt.schema.json`.

## Phase 9 · Manifest + sha256sums

Produce:
- `receipts/{receipt_id}/receipt.json`
- `receipts/{receipt_id}/receipt.md` (human-readable twin)
- `receipts/{receipt_id}/manifest.json` (validated against `schemas/receipt_manifest.schema.json`)
- `receipts/{receipt_id}/SHA256SUMS.txt`

## Phase 10 · Optional ledger publication

If `--publish-to-ledger` is set and the receipt is HONEY:
- Use the existing `defendableos/services/api/app/services/ledger_publisher.py`
  pattern (PR #7 on defendableos) to publish to `streetledger/compute/assets/{asset_id}/receipts/{receipt_id}.json`.
- Populate `ledger_publication` with `ledger_record_id`, `ledger_url`, and
  `record_sha256`.

JELLY and PROPOLIS receipts are kept local by default; publishing them
requires `--publish-jelly` or `--publish-propolis` operator flags.
