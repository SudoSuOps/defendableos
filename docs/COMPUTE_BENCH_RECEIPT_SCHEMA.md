# Compute Bench Receipt Schema

The canonical structure for a `defendable-compute` bench run. Every
run produces a self-contained directory at
`compute-bench/runs/<run_id>/` with structured JSON files plus a
SHA-256 manifest covering the bundle.

## Run-bundle layout

```
compute-bench/
└── runs/
    └── <run_id>/
        ├── asset_identity.json
        ├── private_identity_reference.json
        ├── system_manifest.json
        ├── runtime_environment.json
        ├── health_diagnostic.json
        ├── thermal_power_trace.jsonl
        ├── benchmark_plan.json
        ├── benchmark_results.json
        ├── workload_compatibility.json
        ├── evidence_classification.json
        ├── validator_flags.json
        ├── best_next_use_inputs.json
        ├── manifest.sha256
        └── public_safe_attestation.json
```

`<run_id>` format: `cb-<yyyymmddTHHMMSSZ>-<short_random>` (e.g.,
`cb-20260522T193045Z-9f2c`).

## File-by-file contract

### `asset_identity.json` · public-safe

What the platform may say *about* the asset. Never includes raw
serial numbers, internal serials, or operator-private fields.

```json
{
  "asset_class": "COMPUTE_HARDWARE",
  "asset_tier": "E6",
  "manufacturer": "NVIDIA",
  "model": "RTX PRO 6000 Blackwell",
  "vram_gb": 96,
  "form_factor": "DISCRETE_CARD",
  "host_role": "INSTITUTIONAL_WORKSTATION",
  "identity_confidence_grade": "A",
  "identity_capture_method": "nvidia-smi + lspci",
  "captured_at": "2026-05-22T19:30:45Z"
}
```

### `private_identity_reference.json` · PRIVATE_EVIDENCE only

The raw identifiers that anchor the identity bundle. Stays in the
PRIVATE_EVIDENCE vault. Never copied into `public_safe_attestation.json`.

```json
{
  "raw_serial": "0123456789AB",
  "device_uuid": "GPU-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "pci_bus_id": "0000:01:00.0",
  "vbios_version": "...",
  "board_part_number": "...",
  "host_machine_hostname": "swarmrails-01",
  "host_dmi_uuid": "...",
  "capture_environment": "operator-attested"
}
```

### `system_manifest.json` · DERIVED + summary public-safe

The full system context the asset is operating in.

```json
{
  "host": {
    "platform": "Linux",
    "kernel": "6.17.0-23-generic",
    "os": {"id": "ubuntu", "version_id": "25.10"},
    "cpu_model": "AMD Ryzen Threadripper PRO 7995WX",
    "cpu_cores": 96,
    "ram_gb": 256,
    "storage_devices": [
      {"name": "nvme0n1", "model": "Samsung 990 PRO 4TB", "size_gb": 4096, "rotational": false}
    ],
    "network_interfaces": [
      {"name": "enp1s0", "link": "UP", "speed_mbps": 10000}
    ]
  },
  "accelerators": [
    {"index": 0, "manufacturer": "NVIDIA", "model": "RTX PRO 6000 Blackwell", "vram_gb": 96}
  ]
}
```

### `runtime_environment.json` · public-safe

Driver, runtime, and container state at capture time.

```json
{
  "nvidia_driver_version": "595.71",
  "cuda_runtime_version": "12.4",
  "nvml_version": "12.4",
  "docker_version": "29.4.0",
  "python_version": "3.13.7",
  "container_runtime_ready": true,
  "selinux_or_apparmor": "apparmor",
  "captured_at": "2026-05-22T19:30:46Z"
}
```

### `health_diagnostic.json` · DERIVED summary · raw private

The output of the health checks for the asset's tier.

```json
{
  "health_grade": "PASS",
  "diagnostic_method": ["nvidia-smi --query", "dcgmi diag -r 1 (skipped · DCGM not present)"],
  "runtime_seconds": 18,
  "temperatures_c": {"idle": 38, "sustained": 62, "peak": 68},
  "power_w": {"idle": 22, "sustained": 280, "peak": 340},
  "ecc_status": "ENABLED · 0 errors",
  "throttling_events": 0,
  "memory_check": "PASS",
  "pcie_link": {"gen": 5, "width": 16, "status": "NOMINAL"},
  "limitations": ["DCGM full diag not run · not installed in environment"]
}
```

### `thermal_power_trace.jsonl` · PRIVATE · streaming

One JSON object per line, captured every N seconds during the run.

```jsonl
{"t": "2026-05-22T19:30:46Z", "gpu_temp_c": 38, "gpu_power_w": 22, "gpu_util_pct": 0}
{"t": "2026-05-22T19:30:47Z", "gpu_temp_c": 41, "gpu_power_w": 145, "gpu_util_pct": 65}
```

### `benchmark_plan.json` · public-safe

The plan that was executed (what the operator agreed to).

```json
{
  "profile": "e6-institutional-accelerator",
  "test_scope": "standard",
  "workloads": [
    {"id": "ai-inference-13b-q4", "expected_duration_s": 120},
    {"id": "sustained-fp16-tensor", "expected_duration_s": 90}
  ],
  "stress_intent": "moderate",
  "safety_acknowledgments": ["not_on_rented_workload", "operator_owned"]
}
```

### `benchmark_results.json` · DERIVED summary · raw private

The actual numeric output of the workload tests.

```json
{
  "workload_results": [
    {
      "id": "ai-inference-13b-q4",
      "status": "COMPLETED",
      "tokens_per_sec": 142.7,
      "peak_vram_gb": 11.8,
      "sustained_power_w": 295,
      "runtime_s": 124,
      "source_classification": "FIRST_PARTY_BENCHMARK_RECEIPT"
    }
  ],
  "anomalies": [],
  "test_version": "compute-bench-0.1.0"
}
```

### `workload_compatibility.json` · public-safe

Plain-English statements about what this card demonstrated capability
for, with no embedded resale or yield claims.

```json
{
  "demonstrated": [
    "13B-class model inference at Q4 in single-GPU mode",
    "sustained FP16 tensor workload at 295W for 90s+"
  ],
  "not_tested": [
    "multi-GPU NVLink coordination",
    "training-class FP8 sustained over 1h+",
    "concurrent rental tenant scenarios"
  ]
}
```

### `evidence_classification.json` · doctrine

Every artifact in the bundle paired with its `RightsStatus` and
vault class. The platform can mechanically verify which fields are
publishable.

```json
{
  "items": [
    {"artifact": "asset_identity.json", "vault": "PUBLIC_ASSETS", "rights": "PUBLIC_DISPLAY_ALLOWED"},
    {"artifact": "private_identity_reference.json", "vault": "PRIVATE_EVIDENCE", "rights": "RESTRICTED_DO_NOT_EXPORT"},
    {"artifact": "thermal_power_trace.jsonl", "vault": "PRIVATE_EVIDENCE", "rights": "INTERNAL_RESEARCH_ONLY"},
    {"artifact": "benchmark_results.json", "vault": "DERIVED_DATASETS", "rights": "INTERNAL_RESEARCH_ONLY"},
    {"artifact": "public_safe_attestation.json", "vault": "PUBLIC_ASSETS", "rights": "PUBLIC_DISPLAY_ALLOWED"}
  ]
}
```

### `validator_flags.json` · internal

Anything the local CLI noticed that the validator chain should
re-check.

```json
{
  "flags": [
    {"severity": "info", "id": "DCGM_NOT_AVAILABLE", "detail": "DCGM diag was skipped"},
    {"severity": "warn", "id": "DRIVER_NVML_MISMATCH", "detail": "Reported by nvidia-smi at capture"}
  ]
}
```

### `best_next_use_inputs.json` · DERIVED

Inputs the Best Next Use Decision needs, captured at bench time.

```json
{
  "owner_objective": "RENTAL_REVENUE",
  "deployment_context": "INSTITUTIONAL_FLEET",
  "operating_cost_usd_per_month_estimate": 38,
  "current_workload": "Qwen3.5-27B drafting + Qwen3.5-9B judge",
  "rental_intent": "OPEN_TO_BOTH",
  "captured_owner_attestations": [
    "Operator-owned · not rented at time of bench",
    "WRX90 host · ECC RAM · validated PSU"
  ]
}
```

### `manifest.sha256` · the integrity anchor

Sorted-key compact JSON keyed by relative filename → SHA-256, then
SHA-256 over the manifest itself appears as the **bundle hash**.

```
asset_identity.json                  a1b2c3...
benchmark_plan.json                  b3c4d5...
benchmark_results.json               c5d6e7...
evidence_classification.json         d7e8f9...
health_diagnostic.json               e9f0a1...
private_identity_reference.json      f1a2b3...
public_safe_attestation.json         a3b4c5...
runtime_environment.json             b5c6d7...
system_manifest.json                 c7d8e9...
thermal_power_trace.jsonl            d9e0f1...
validator_flags.json                 e1f2a3...
workload_compatibility.json          f3a4b5...
best_next_use_inputs.json            a5b6c7...
```

The bundle hash is what gets published as
`benchmark_attestation_hash` on the downstream deed JSON.

### `public_safe_attestation.json` · the publication artifact

Produced by passing the full bundle through
`public_export_or_refuse()`. Only the public-safe fields appear.

```json
{
  "run_id": "cb-20260522T193045Z-9f2c",
  "asset_class": "COMPUTE_HARDWARE",
  "asset_tier": "E6",
  "model": "NVIDIA RTX PRO 6000 Blackwell",
  "vram_gb": 96,
  "form_factor": "DISCRETE_CARD",
  "captured_at": "2026-05-22T19:30:45Z",
  "captured_by": "swarm-and-bee",
  "grades": {
    "identity_confidence": "A · PRIVATE_IDENTIFIER_CAPTURED_AND_HASHED",
    "health": "PASS",
    "utility": "E6_INSTITUTIONAL_ACCELERATOR_UTILITY_MEASURED",
    "evidence": "B · FIRST_PARTY_OPERATIONAL_EVIDENCE_ONLY"
  },
  "demonstrated_workloads": [
    "13B-class model inference at Q4 in single-GPU mode",
    "sustained FP16 tensor workload at 295W for 90s+"
  ],
  "manifest_hash": "sha256:...",
  "bundle_hash": "sha256:...",
  "limitations": [
    "DCGM full diag was not run · not present in capture environment",
    "Buyer-side re-attestation required for transfer assurance"
  ],
  "re_attestation_trigger": "OWNERSHIP_TRANSFER · HARDWARE_RELOCATION · DRIVER_MAJOR_UPGRADE"
}
```

## Required metadata fields (run-level)

Every bundle's `asset_identity.json` + `benchmark_plan.json` together
must populate these fields:

| Field | Source file | Notes |
|---|---|---|
| `run_id` | filename | `cb-<ts>-<rand>` |
| `asset_record_id` | benchmark_plan.json | maps to platform `assets.id` when synced |
| `captured_at` | asset_identity.json | ISO 8601 UTC |
| `captured_by` | asset_identity.json | org slug |
| `asset_tier` | asset_identity.json | E0–E7 |
| `asset_category` | asset_identity.json | COMPUTE_HARDWARE today |
| `test_scope` | benchmark_plan.json | quick · standard · extended |
| `test_version` | benchmark_results.json | CLI semver |
| `tool_versions` | runtime_environment.json | dict of tool → version |
| `host_environment` | system_manifest.json | full host context |
| `power_mode` | benchmark_plan.json | nominal · power-capped · server-default |
| `evidence_visibility` | evidence_classification.json | per-artifact vault map |
| `hash_algorithm` | manifest.sha256 | always `SHA-256` |
| `manifest_hash` | manifest.sha256 + computed | bundle integrity anchor |
| `attestation_status` | public_safe_attestation.json | BENCHMARK_ATTESTED on success |
| `limitations` | public_safe_attestation.json | honest list |
| `re_attestation_trigger` | public_safe_attestation.json | when buyer must re-run |

## Receipt truth classes

Every artifact's `source_classification` field carries one of:

```
FIRST_PARTY_IDENTITY_CAPTURE
FIRST_PARTY_SYSTEM_MANIFEST
FIRST_PARTY_HEALTH_DIAGNOSTIC
FIRST_PARTY_BENCHMARK_RECEIPT
FIRST_PARTY_THERMAL_POWER_TRACE
FIRST_PARTY_WORKLOAD_TEST
PUBLIC_MARKET_OBSERVATION
PUBLIC_RENTAL_RATE_OBSERVATION
FIRST_PARTY_RENTAL_RECEIPT
VERIFIED_SOLD_COMP
PARTNER_TRANSACTION_EVIDENCE
DERIVED_UTILITY_GRADE
DERIVED_BEST_NEXT_USE_DECISION
VALIDATOR_APPROVED_PUBLIC_EXPORT
```

These align 1:1 with the `RightsStatus` and `ArtifactPrivacyClass`
mappings in [`EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md`](./EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md).

## Hard rule

**`private_identity_reference.json` is never automatically included
in `public_safe_attestation.json`.** The export path explicitly
ignores PRIVATE_EVIDENCE artifacts. If a future export needs to
include redacted identity confirmation, the redacted form must be
generated separately and re-classified PUBLIC_ASSETS before
publication.
