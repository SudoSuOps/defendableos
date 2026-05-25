# Defendable Compute Proof Receipt · smash RTX 5090 · 2026-05-25

> **receipt_id:** `DCPR-20260525-EXAMPLE0SMASHRTX509000A`
> **schema_version:** `v0.1`
> **use_case:** `rental_readiness`
> **tribunal_verdict:** 🍯 **HONEY**

## Asset

| field | value |
| --- | --- |
| asset_id | `smash-rtx5090-host-001` |
| hostname | `smash` |
| asset_type | gpu_workstation |
| manufacturer | NVIDIA |
| model | NVIDIA GeForce RTX 5090 |
| gpu_count | 1 |
| vram_total | 32,607 MiB |
| cuda_reported | 13.1 |
| host_runtime | visible |
| container_runtime | visible_via_cdi |
| rental_platform_runtime | visible (vast_ai) |
| serial / UUID | [redacted] (privacy_treatment=redacted) |
| operator | `claude-code-swarm-research-intake` (audit_agent) |
| observed_at | `2026-05-25T10:57:00Z` |

## Precheck state (before remediation)

| measure | value |
| --- | --- |
| Docker containers | 0 |
| Docker images | 0 |
| Docker residual artifacts | none |
| Model servers running | yes (vllm, llama.cpp, defendablerouter) |
| Vast services (vastai, vast_metrics) | active |
| GPU VRAM used | **28,114 MiB** (of 32,607) |
| GPU utilization | 0% |
| GPU temperature | 51 C |
| GPU power draw | 21.55 W |
| GPU power cap | 550 W |
| Persistence mode | enabled |
| Compute processes | `VLLM::EngineCore` PID 75037 holding 28,104 MiB |

**Precheck pass/fail:** `pass_with_observations` — Docker was clean but local
SwarmCurator vLLM was holding VRAM and needed to be stopped before the host
could be presented as rental-ready idle.

## Findings

### Finding 1 · `GPU_MEMORY_HELD_BY_LOCAL_PROCESS` · blocker

Local SwarmCurator vLLM process (PID 75037) was holding 28,104 MiB of VRAM at
observation time. This is **NOT renter contamination** — it is a first-party
workload that must be stopped before the host can be presented as rental-ready
idle.

Evidence: `receipts/evidence/2026-05-25T10-57-00Z_nvidia_smi_compute_apps.txt`

## Remediation

Operator gracefully shut down the three local model services:
- vLLM swarmcurator-9b on port 8088
- llama.cpp swarmjelly-4b on port 8089
- DefendableRouter on port 8080

without touching Vast services. `vastai` and `vast_metrics` remained active
throughout. Docker containers remained at zero.

**Result:** `resolved` · operator-confirmed.

## Post-remediation state

| measure | value |
| --- | --- |
| Docker containers | 0 |
| Model servers running | none |
| Vast services | active |
| GPU VRAM used | **2 MiB** (idle) |
| GPU utilization | 0% |
| GPU temperature | 51 C |
| GPU power draw | 21.55 W |
| GPU power cap | 550 W |
| Persistence mode | enabled |
| Compute processes | none |

**Post-remediation pass/fail:** `pass`

## Benchmark validation (Vast.ai platform-remote)

| test_id | test | scope | result | confidence |
| --- | --- | --- | --- | --- |
| TEST-001 | System requirements test | identity_check | pass | high |
| TEST-002 | ResNet18 GPU functional test | functional_inference | pass | high |
| TEST-003 | ECC test | ecc_health | pass | high |
| TEST-004 | NCCL distributed test (1 GPU) | distributed_communication | pass | high |
| TEST-005 | Combined stress-ng + gpu-burn 60s | stress_combined | pass | high |
| TEST-006 | Test instance teardown | runtime_visibility | pass | high |

All tests executed by `vast_ai remote validator`. Combined stress-ng + gpu-burn
held for 60 seconds with no thermal trip and no NCCL error.

## Operating baseline

| parameter | value |
| --- | --- |
| power_cap_w | 550.0 |
| persistence_mode | enabled |
| thermal_policy_c_warning | 80.0 |
| thermal_policy_c_shutdown | 90.0 |
| expected_idle_vram_mib_max | 50 |
| expected_idle_utilization_percent_max | 5 |
| expected_idle_power_w_max | 50.0 |
| documented_owner_state | idle, persistence enabled, 550W rental cap, no local model servers running, Vast services active |

## Tribunal verdict · 🍯 HONEY

> Asset returned to verified idle state (2 MiB VRAM, 0% utilization, ~51 C,
> ~21.55 W idle draw, 550 W cap, persistence enabled) and passed
> platform-remote functional/stress validation for rental readiness: system
> requirements, ResNet18 GPU, ECC, NCCL (1 GPU), and combined stress-ng+gpu-burn
> 60s. Test instance destroyed successfully. No Docker containers remained.

Issued by: `claude-code-swarm-research-intake` at `2026-05-25T11:30:00Z`.

## Claim boundaries

This receipt **establishes**:
- Asset identified to runtime
- No unintended workloads at timestamp
- Configured to documented operating baseline
- Passed named functional and stress tests at timestamp

This receipt **does not establish**:
- Market value
- Appraisal under USPAP or equivalent
- Manufacturer warranty status
- Insurance underwriting acceptance
- Lender acceptance
- Legal title or ownership
- Accreditation by third-party body
- Fitness for any specific purpose beyond the named tests

**Validity window:** snapshot at `observed_at` timestamp only. Successor
records supersede.

## Artifact hashes

(Hashes shown as `0000...` in this example are placeholders; the CLI will
populate real sha256 values when a real evidence directory is supplied.)

| artifact | sha256 |
| --- | --- |
| `receipts/evidence/2026-05-25T10-57-00Z_nvidia_smi_gpu_query.txt` | `0000...0000` |
| `receipts/evidence/2026-05-25T10-57-00Z_nvidia_smi_compute_apps.txt` | `0000...0000` |
| `receipts/evidence/2026-05-25T10-58-XX-XZ_service_shutdown_log.txt` | `0000...0000` |
| `receipts/evidence/vast_remote_validation_summary.txt` | `0000...0000` |

## Ledger publication

This example has not been published. Real receipts would carry a
`ledger_publication` block once anchored to DefendableLedger.

---

`Books and records. No proof, no honey. To the shed.`
