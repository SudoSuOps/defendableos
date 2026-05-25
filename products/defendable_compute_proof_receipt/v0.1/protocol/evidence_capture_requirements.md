# Evidence Capture Requirements · v0.1

> Every claim in a Defendable Compute Proof Receipt MUST trace back to an
> evidence artifact that an independent party can hash and inspect.

## Universal capture rules

1. **Raw is canonical.** Capture command output exactly as emitted. Do not
   summarize before hashing. Summaries belong in the receipt JSON; raw
   artifacts belong on disk and in the hash manifest.
2. **Timestamp every artifact.** File names use ISO 8601 UTC at the second:
   `{YYYY-MM-DD}T{HH-MM-SS}Z_{tool}_{purpose}.{ext}`.
3. **Hash everything.** sha256 the artifact immediately after capture and
   before any transformation. Hashes appear in `generated_artifact_hashes`
   and in `SHA256SUMS.txt`.
4. **Append, never overwrite.** Evidence directories are append-only within
   a single receipt run. A new run produces a new `receipt_id` directory.
5. **Witness the timestamp.** Where possible, prefer commands that include
   their own timestamps (e.g., `date -u && nvidia-smi`).

## Per-Phase capture spec

### Phase 1 · Identity capture

| artifact | command | required |
| --- | --- | --- |
| `nvidia_smi_identity.csv` | `nvidia-smi --query-gpu=name,driver_version,memory.total,uuid,serial --format=csv,noheader` | yes |
| `nvidia_smi_baseline.csv` | `nvidia-smi --query-gpu=persistence_mode,power.max_limit --format=csv,noheader` | yes |
| `hostname.txt` | `hostname` | yes |
| `uname.txt` | `uname -a` | yes |

### Phase 2 · Service state precheck

| artifact | command | required |
| --- | --- | --- |
| `docker_ps.txt` | `docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'` | yes |
| `docker_info.txt` | `docker info` | yes |
| `docker_images.txt` | `docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}'` | yes |
| `pgrep_model_servers.txt` | `pgrep -fa 'vllm|ollama|llama_cpp|vllm.entrypoints'` | yes |
| `systemctl_rental_platform.txt` | `systemctl status vastai vast_metrics` (or platform equivalent) | yes |
| `nvidia_smi_gpu_query.txt` | `nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw,power.max_limit,persistence_mode --format=csv,noheader` | yes |
| `nvidia_smi_compute_apps.txt` | `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader` | yes |
| `df_h.txt` | `df -h` | yes |
| `runtime_state.txt` | combined `ls /dev/nvidia*`, `nvidia-container-cli info`, `ldconfig -p | grep nvidia` | yes |

### Phase 4 · Remediation

For every remediation action:

| artifact | content | required |
| --- | --- | --- |
| `remediation_{finding_code}_command.txt` | the exact command(s) run | yes |
| `remediation_{finding_code}_stdout.txt` | stdout from the remediation | yes |
| `remediation_{finding_code}_stderr.txt` | stderr from the remediation | yes |
| `remediation_{finding_code}_exitcode.txt` | exit code | yes |
| `remediation_{finding_code}_operator_confirmation.txt` | record of explicit operator approval (signed `y` or signed CI worker token) | yes |

### Phase 5 · Post-remediation state

Same artifacts as Phase 2, captured fresh and named with a new timestamp.

### Phase 6 · Platform-remote validation

| artifact | content | required |
| --- | --- | --- |
| `platform_remote_validation.txt` | full platform-side validator output | yes |
| `platform_remote_test_index.json` | parsed mapping of test_name → result with the platform's own IDs | yes |
| `platform_remote_finish_state.txt` | platform-side machine state at end of validation (e.g., 'machine test result: DONE') | yes |

## Evidence directory layout per receipt

```
receipts/{receipt_id}/
├── receipt.json
├── receipt.md
├── manifest.json
├── SHA256SUMS.txt
└── evidence/
    ├── {YYYY-MM-DD}T{HH-MM-SS}Z_phase1_nvidia_smi_identity.csv
    ├── {YYYY-MM-DD}T{HH-MM-SS}Z_phase2_docker_ps.txt
    ├── {YYYY-MM-DD}T{HH-MM-SS}Z_phase2_nvidia_smi_compute_apps.txt
    ├── {YYYY-MM-DD}T{HH-MM-SS}Z_phase4_remediation_GPU_MEMORY_HELD_BY_LOCAL_PROCESS_stdout.txt
    ├── {YYYY-MM-DD}T{HH-MM-SS}Z_phase5_nvidia_smi_gpu_query.txt
    └── {YYYY-MM-DD}T{HH-MM-SS}Z_phase6_platform_remote_validation.txt
```

## Anti-patterns to refuse

- Empty `evidence_locator` field in any `benchmark_observation` or
  `evidence_sources` entry → Tribunal rejects.
- Evidence artifact present but not hashed → Tribunal rejects.
- Hash in receipt does not match recomputed hash of artifact → receipt is
  **INVALID** and consumers must treat the asset as unverified.
- Summary-only artifact with no raw command output → Tribunal rejects.
- Symlinks to volatile paths (e.g., `/tmp`) → Tribunal rejects;
  evidence must live in a stable receipt-scoped directory.

## Retention policy

- HONEY receipts: evidence retained ≥ 7 years (matches CRE deed retention practice).
- JELLY receipts: evidence retained ≥ 1 year or until superseded.
- PROPOLIS receipts: evidence retained ≥ 7 years (failure cases are training data).
