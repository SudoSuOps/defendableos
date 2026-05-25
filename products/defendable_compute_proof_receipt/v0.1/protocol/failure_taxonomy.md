# Failure Taxonomy · Defendable Compute Proof Receipt v0.1

> Every finding observed during the post-rental protocol maps to one of these
> codes. Codes have stable identifiers, default severities, default Tribunal
> classes, and named remediation patterns.

## Codes

### `RESIDUAL_DOCKER_ARTIFACTS`

**Definition:** Docker containers, images, networks, volumes, or other
artifacts attributable to a prior tenant remain on the host.

**Detected by:** Phase 2 docker_ps, docker_images, docker_network_ls, docker_volume_ls.

**Default severity:** warning if detected; blocker if cleanup fails.

**Default Tribunal class:** JELLY if remediated; PROPOLIS if cleanup fails.

**Remediation pattern:**
```
docker container prune -f
docker image prune -af
docker network prune -f
docker volume prune -f
```
Capture command stdout/stderr/exit code. Re-run Phase 2 to verify.

---

### `GPU_MEMORY_HELD_BY_LOCAL_PROCESS`

**Definition:** GPU VRAM is held by a process **owned by the operator's own
identity** (e.g., a first-party model server like vLLM or llama.cpp).

**Detected by:** Phase 2 nvidia-smi compute apps + pgrep model servers.

**Default severity:** blocker (the asset cannot be presented as rental-ready idle).

**Default Tribunal class:** JELLY if process identified and cleared with
operator confirmation; PROPOLIS if process cannot be cleared.

**Remediation pattern:** SIGTERM the process; wait grace period; verify
VRAM released to expected idle.

**Discovered on smash 2026-05-25.**

---

### `GPU_MEMORY_HELD_BY_UNKNOWN_PROCESS`

**Definition:** GPU VRAM is held by a process **not attributable** to the
operator, a rental platform service, or a known dependency.

**Detected by:** Phase 2 nvidia-smi compute apps with no matching first-party
process.

**Default severity:** blocker.

**Default Tribunal class:** **PROPOLIS** (mystery process = unprovable cleanliness).

**Remediation pattern:** investigation required before remediation. Capture
full process tree (`ps auxef`) and `lsof` for the GPU device. Do NOT kill
unknown processes blindly — they may be platform processes.

---

### `POWER_BASELINE_NOT_RESTORED`

**Definition:** GPU power cap does not match the documented operating
baseline (e.g., expected 550 W rental cap, observed something else).

**Detected by:** Phase 1 nvidia-smi baseline.

**Default severity:** warning if reducible to baseline; blocker if hardware
refuses.

**Default Tribunal class:** JELLY if remediable; PROPOLIS if hardware-limited.

**Remediation pattern:** `nvidia-smi -pl {target_w}`. Confirm via re-query.

---

### `PERSISTENCE_MODE_DISABLED`

**Definition:** GPU persistence mode is off.

**Detected by:** Phase 1 nvidia-smi baseline (`persistence_mode`).

**Default severity:** informational.

**Default Tribunal class:** JELLY pre-remediation, HONEY-compatible post-remediation.

**Remediation pattern:** `nvidia-smi -pm 1`.

---

### `NVIDIA_RUNTIME_UNAVAILABLE`

**Definition:** Container runtime cannot use the NVIDIA runtime (missing
runtime in `docker info`, broken `nvidia-container-cli`).

**Detected by:** Phase 2 runtime_state.

**Default severity:** blocker.

**Default Tribunal class:** **PROPOLIS**.

**Remediation pattern:** outside the scope of v0.1 protocol — requires
operator-level system intervention. Generate finding, do NOT auto-remediate.

---

### `CDI_DEVICE_MISSING`

**Definition:** Container Device Interface (CDI) device specification for
the GPU is missing.

**Detected by:** Phase 2 runtime_state (`cdi_device_available`).

**Default severity:** blocker.

**Default Tribunal class:** **PROPOLIS**.

**Remediation pattern:** out of v0.1 scope.

---

### `STORAGE_MOUNT_UNHEALTHY`

**Definition:** A storage mount the rental platform depends on is unhealthy
(unmount, read-only when expected RW, errors in dmesg).

**Detected by:** Phase 2 storage_mount_state.

**Default severity:** blocker if rental-platform mount; warning otherwise.

**Default Tribunal class:** PROPOLIS for rental-platform mount; JELLY for
ancillary mount.

**Remediation pattern:** out of v0.1 scope.

---

### `RENTAL_PLATFORM_SERVICE_DOWN`

**Definition:** The platform daemon required for renter discovery and
metrics is inactive (e.g., `vastai`, `vast_metrics`).

**Detected by:** Phase 2 rental_platform_service_state.

**Default severity:** blocker.

**Default Tribunal class:** **PROPOLIS**.

**Remediation pattern:** v0.1 protocol does NOT restart rental platform
services. Generate finding and surface to the operator for manual handling.

---

### `REMOTE_VALIDATION_FAILURE`

**Definition:** One or more tests in the Phase 6 platform-remote validation
suite failed.

**Detected by:** Phase 6.

**Default severity:** blocker.

**Default Tribunal class:** **PROPOLIS**.

**Remediation pattern:** investigation required. Re-run only after specific
findings have been remediated.

---

### `TEMPERATURE_OUT_OF_POLICY`

**Definition:** GPU temperature exceeds the configured warning or shutdown
threshold during precheck, remediation, or stress testing.

**Detected by:** any phase that captures nvidia-smi temperature.

**Default severity:** warning at `thermal_policy_c_warning`; blocker at
`thermal_policy_c_shutdown`.

**Default Tribunal class:** JELLY at warning; PROPOLIS at shutdown.

**Remediation pattern:** stop load; allow cool-down; investigate cooling
path. Do not retry stress until baseline restored.

---

### `UNVERIFIED_ASSET_IDENTITY`

**Definition:** `nvidia-smi` does not return the expected identity fields,
or the returned identity disagrees with the operator's expected
`asset_id` mapping.

**Detected by:** Phase 1.

**Default severity:** blocker.

**Default Tribunal class:** **PROPOLIS** (refuse to issue receipt).

**Remediation pattern:** investigation required. May indicate driver
breakage, hardware swap, or counterfeit hardware. v0.1 refuses receipt
issuance until resolved.

---

### `CLAIM_EXCEEDS_EVIDENCE`

**Definition:** The proposed receipt contains a banned vocabulary term, an
empty `evidence_locator`, an empty `limitations` field, or any other
linter-detected over-claim.

**Detected by:** receipt linter (Phase 8 / CLI `receipt --lint`).

**Default severity:** blocker.

**Default Tribunal class:** **PROPOLIS** (refuse to issue).

**Remediation pattern:** operator must edit the receipt to remove the
banned term or fill the missing evidence reference, then re-lint.
