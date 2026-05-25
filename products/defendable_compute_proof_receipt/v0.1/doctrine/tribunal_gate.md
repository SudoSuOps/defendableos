# Tribunal Gate · Defendable Compute Proof Receipt v0.1

> `Tribunal begins before training. No proof, no honey.`

Every Proof Receipt is Tribunal-graded before it is published. This document
defines the gate that determines the `tribunal_verdict` field value.

## Verdict taxonomy

| verdict | criteria |
| --- | --- |
| 🍯 **HONEY** | All schema-mandatory observations PASS; no unresolved findings; named platform-remote or third-party functional/stress validation passed within the validity window. |
| 🟡 **JELLY** | All schema-mandatory observations recorded; one or more JELLY-class findings exist; named functional validation may still have passed but cannot be promoted to HONEY because some condition needs corroboration (e.g., local-only benchmark without remote replication). |
| 🟤 **PROPOLIS** | At least one PROPOLIS-class finding exists, OR the named functional validation FAILED, OR identity could not be verified to runtime. **The asset is not ready for the named use case.** |

## Finding-class mapping

Findings from `protocol/failure_taxonomy.md` map to verdict classes:

| finding code | default class | rationale |
| --- | --- | --- |
| `RESIDUAL_DOCKER_ARTIFACTS` | JELLY if cleaned; PROPOLIS if cleanup failed | Residual artifacts are recoverable by cleanup; failed cleanup blocks rental readiness. |
| `GPU_MEMORY_HELD_BY_LOCAL_PROCESS` | JELLY if process identified and cleared; PROPOLIS if process unidentified | Identification + clearance is recoverable; mystery process blocks. |
| `GPU_MEMORY_HELD_BY_UNKNOWN_PROCESS` | **PROPOLIS** | Unidentified workload means the asset is not provably clean. |
| `POWER_BASELINE_NOT_RESTORED` | JELLY if remediable; PROPOLIS if hardware-limited | Most power-cap restores succeed; if hardware refuses, asset baseline is broken. |
| `PERSISTENCE_MODE_DISABLED` | JELLY | Easily restored; non-blocking if observed pre-validation and fixed. |
| `NVIDIA_RUNTIME_UNAVAILABLE` | **PROPOLIS** | Without nvidia runtime, container-side validation cannot run. |
| `CDI_DEVICE_MISSING` | **PROPOLIS** | Container Device Interface missing breaks platform-remote validation. |
| `STORAGE_MOUNT_UNHEALTHY` | JELLY if non-critical mount; PROPOLIS if rental platform mount | Rental platform depends on healthy storage; non-rental mounts may be JELLY. |
| `RENTAL_PLATFORM_SERVICE_DOWN` | **PROPOLIS** | Without `vastai` / `vast_metrics` (or equivalent), the asset cannot be listed. |
| `REMOTE_VALIDATION_FAILURE` | **PROPOLIS** | Platform-remote validation is the strongest signal; failure blocks the verdict. |
| `TEMPERATURE_OUT_OF_POLICY` | JELLY if within thermal warning; PROPOLIS if shutdown threshold | Policy thresholds are operator-set. |
| `UNVERIFIED_ASSET_IDENTITY` | **PROPOLIS** | Unidentified asset cannot be receipted; refuse to issue. |
| `CLAIM_EXCEEDS_EVIDENCE` | **PROPOLIS** | Linter rejection on banned terminology; refuse to publish. |

## Promotion rules

A receipt may be **promoted from JELLY to HONEY** only when ALL of:
- All JELLY findings are explicitly resolved with a remediation_action entry.
- A successor observation confirms post-remediation state matches the
  operating baseline.
- A platform-remote or third-party validation passes within the validity
  window of the successor observation.

A receipt may be **demoted from HONEY to JELLY or PROPOLIS** any time after
issuance if new evidence emerges that contradicts the original observations.
The original receipt is preserved as a historical record and a successor
record is issued with a `supersedes` field.

## Hard rejections

The Tribunal gate must refuse to issue a HONEY receipt — even if all schema
checks pass — when:

1. The receipt contains any banned vocabulary term from `terminology_and_claim_boundaries.md`.
2. The `claim_boundaries.scope` field has been edited away from `"operational_condition_at_timestamp_only"`.
3. The `evidence_locator` field on any benchmark observation is empty.
4. The artifact hash list is empty or contains placeholder values.
5. The operator field is empty or set to a generic identifier.

These are tested in the CLI as `defendable-compute receipt --lint`.

## Audit trail

Every Tribunal verdict change (promotion, demotion, supersession) generates
an `AUDIT` record in the DefendableLedger chain, linking the new receipt to
the prior receipt by `parent_receipt_id` and `parent_record_sha256`. This
matches the existing 82-record DefendableLedger hash chain on smash.
