# Compute Attestation · Four-Grade Standard

A single number lies. Four orthogonal grades tell the truth.

A benchmark-attested record carries **four separate grades**. They
are NEVER collapsed into one composite. The operator and the
validator read them together · because a high utility grade with a
low evidence grade means something very different from a high
utility grade with a high evidence grade.

## A · Identity Confidence Grade

Measures whether the asset was accurately captured.

| Status | Meaning |
|---|---|
| `A · PRIVATE_IDENTIFIER_CAPTURED_AND_HASHED` | Raw serial / device UUID / PCI bus ID captured to PRIVATE vault · hashed into bundle manifest · public-safe reference exists |
| `B · SYSTEM_IDENTITY_CAPTURED_NO_PRIVATE_SERIAL` | System manifest (model · VRAM · driver) captured · raw serial not yet obtained (e.g., remote inspection scenario) |
| `C · MODEL_SELF_REPORTED_ONLY` | Identity sourced from `nvidia-smi --query` only · no PCI confirmation · no UUID · no serial |
| `INCOMPLETE` | Capture failed or was skipped · record cannot advance |

**Hard rule:** An Identity Confidence Grade of `INCOMPLETE` blocks
attestation. The bench refuses to issue a `BENCHMARK_ATTESTED`
record without at least Grade C identity.

## B · Health Grade

Measures operational diagnostic condition at capture time.

| Status | Meaning |
|---|---|
| `PASS` | All applicable health checks passed · no errors · no throttling · thermals + power within nominal |
| `PASS_WITH_OBSERVATIONS` | Pass · but the run captured at least one non-blocking observation (e.g., elevated idle temp · driver version older than current LTS) |
| `CONDITIONAL` | Pass under specific conditions only (e.g., works at 250W cap · fails at full TDP) · conditions documented |
| `FAIL` | A health check failed · ECC errors · sustained throttling · crashed under sustained load · driver instability |
| `NOT_TESTED` | Operator opted to skip · or environment doesn't support the test |
| `UNSUPPORTED_TEST_SCOPE` | The asset class doesn't have a health-test definition yet · the bench labels the gap honestly |

Every Health Grade output **must disclose**:

- Diagnostic method used (which tool · which command)
- Runtime of the diagnostic
- Thermal envelope observed (idle · sustained · peak)
- Power state observed (idle · sustained · peak)
- Errors or warnings the tool reported
- Limits of the test (what wasn't covered)

A `FAIL` Health Grade does NOT block attestation · it documents
the failure. The record is still issuable as
`BENCHMARK_ATTESTED · HEALTH_FAIL` if the operator wants to publish
the receipt as part of an honest condition disclosure.

## C · Utility Grade

Measures workload fitness within the asset's tier. The grade names
the **workload class actually measured** · not an abstract score.

| Status | Meaning |
|---|---|
| `E1_EDGE_VISION_UTILITY_MEASURED` | Small vision / CV workload completed on edge accelerator · throughput + latency captured |
| `E2_ENTRY_LOCAL_INFERENCE_MEASURED` | Small-model inference test completed on 6-8 GB GPU class |
| `E4_WORKHORSE_AI_RENTAL_UTILITY_MEASURED` | 24 GB-class workload (13B-30B inference) completed · sustained power captured |
| `E5_PREMIUM_LOCAL_AI_UTILITY_MEASURED` | Workstation Blackwell-class workload · large-model inference or LoRA fine-tune completed |
| `E6_INSTITUTIONAL_ACCELERATOR_UTILITY_MEASURED` | 96 GB-class workload (70B inference · training-capable) completed |
| `E7_PRODUCING_NODE_READINESS_MEASURED` | Multi-GPU coordination · interconnect throughput · whole-node deployment validated |
| `UTILITY_NOT_YET_MEASURED` | Identity + Health captured · workload test not yet run |

Each Utility Grade output carries:

- Workload name + version + parameters
- Input size class (model size · context length · batch · resolution)
- Throughput observed (tokens/sec · images/sec · samples/sec)
- Peak memory used
- Sustained power during the test
- Test runtime
- Source classification of the measurement (FIRST_PARTY_WORKLOAD_TEST)

Mixing tiers is forbidden. The bench does NOT issue an `E4_*` Utility
Grade for a Jetson · it documents an `E1_*` grade and stops.

## D · Evidence Grade

Measures how strongly the surrounding claims are supported.

| Status | Meaning |
|---|---|
| `A · FIRST_PARTY_AND_VALIDATOR_REVIEWED` | First-party benchmark receipts + first-party operating receipts + validator has reviewed the bundle · highest grade |
| `B · FIRST_PARTY_OPERATIONAL_EVIDENCE_ONLY` | First-party identity + first-party benchmark + first-party operating evidence · validator review pending |
| `C · PUBLIC_OBSERVATION_ONLY` | No first-party benchmark · public observations only (e.g., Vast.ai snapshot · public spec sheet) |
| `BLOCKED · MATERIAL_EVIDENCE_MISSING` | The claim being made requires evidence that's absent (e.g., asserting paid rental yield without rental receipts) |

The Evidence Grade is the validator's anchor. An issued deed at
Evidence Grade `B` says "this is what we measured · validator review
not yet complete." An issued deed at Evidence Grade `C` says "this
is public-only evidence · no captured benchmark."

## Reading the grades together

The four grades multiply context, they don't average:

| Identity | Health | Utility | Evidence | Reading |
|---|---|---|---|---|
| A | PASS | E6_INSTITUTIONAL_* | A | Premium deed · validator-cleared · fully attested |
| A | PASS | E4_WORKHORSE_* | B | Workhorse record · operator evidence · validator pending |
| B | PASS_WITH_OBS | E4_WORKHORSE_* | B | Remote bench · operating soundly · operator-only evidence |
| C | NOT_TESTED | UTILITY_NOT_YET_MEASURED | C | Public-spec-only record · no captured evidence · weak |
| A | FAIL | UTILITY_NOT_YET_MEASURED | B | Honest condition disclosure · failed health · sold as-is |
| INCOMPLETE | * | * | * | Cannot issue · re-run identity capture |

## The hard rule

> A benchmark grade is not an Opinion of Value.
> An Opinion of Value is not an issued deed.
> An issued deed is not a guarantee of future performance,
> future rental income or future sale price.

Compute Bench produces grades. AIOV produces opinions. The
validator produces approvals. The deed publishes the survivors.
Each layer is allowed to question the layer beneath it. None of
them issue certifications.

## Public-safe display

Public-safe attestation surfaces the four grades as labeled badges,
never as a numeric score:

```
IDENTITY    A · PRIVATE_IDENTIFIER_CAPTURED_AND_HASHED
HEALTH      PASS
UTILITY     E6_INSTITUTIONAL_ACCELERATOR_UTILITY_MEASURED
EVIDENCE    B · FIRST_PARTY_OPERATIONAL_EVIDENCE_ONLY
```

A future buyer-side re-attestation publishes a second set of grades
linked to the seller's record · drift is documented per grade.

## Related docs

- [`DEFENDABLE_COMPUTE_BENCH.md`](./DEFENDABLE_COMPUTE_BENCH.md) · the umbrella product
- [`COMPUTE_BENCH_RECEIPT_SCHEMA.md`](./COMPUTE_BENCH_RECEIPT_SCHEMA.md) · where the grades appear in the bundle
- [`COMPUTE_BENCH_PROFILE_MATRIX.md`](./COMPUTE_BENCH_PROFILE_MATRIX.md) · which tier produces which Utility Grade
- [`BEST_NEXT_USE_DECISION_SCHEMA.md`](./BEST_NEXT_USE_DECISION_SCHEMA.md) · how the grades feed the decision
- [`COMPUTE_UTILITY_SCORE_STANDARD.md`](./COMPUTE_UTILITY_SCORE_STANDARD.md) · the related (post-bench) 3-family scoring framework
