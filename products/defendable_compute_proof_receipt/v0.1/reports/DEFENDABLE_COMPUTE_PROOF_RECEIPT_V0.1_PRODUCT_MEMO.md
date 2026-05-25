# Defendable Compute Proof Receipt v0.1 · Product Memo

**Operator:** Claude Code · DefendableOS Product Build
**Date:** 2026-05-25
**Doctrine:** `Tribunal begins before training. No proof, no honey.`
**Host repo:** `~/Desktop/defendableos` · branch `main`
**Workspace:** `products/defendable_compute_proof_receipt/v0.1/`

---

## 1 · Executive Verdict

Defendable Compute Proof Receipt v0.1 ships as a **specification + one real
example + complete schema family + protocol + CLI contract + integration
blueprints**. It is not yet a CLI implementation. It is the smallest
publishable unit needed to turn the post-rental verification cycle already
practiced on smash (RTX 5090, 2026-05-25) into a repeatable, hash-receipted,
ledger-publishable artifact.

The product is **deliberately limited to condition records**. It does not
assert market value, certified appraisal, warranty status, insurance
acceptance, lender acceptance, legal ownership, or third-party accreditation.
Those determinations are downstream products consuming this receipt as input.

**Verdict label:** `READY_FOR_V0.2_IMPLEMENTATION`

## 2 · Product Definition

A **Defendable Compute Proof Receipt** is a JSON-Schema-validated,
hash-receipted record establishing that a compute asset:

- is identified,
- is visible to the runtime,
- is clear of unintended workloads,
- is configured to an operating baseline,
- passes functional/stress validation,
- and is ready for rental, resale, disposition, or fleet audit.

Authorized vocabulary: **Proof Receipt** · **Validated Compute Condition
Record** · **Rent-Ready Evidence Package** · **Benchmark-Backed Asset Record**.

Banned vocabulary: `appraisal`, `valuation`, `certified`, `guaranteed`,
`warranted`, `insurance-backed`, `lender-accepted`, `legally proves`,
`accredited` — see `doctrine/terminology_and_claim_boundaries.md`.

## 3 · Why This Is the First Build

1. **The lifecycle already ran.** The smash RTX 5090 post-renter cycle on
   2026-05-25 executed end-to-end with full evidence in hand. The product
   formalizes what already happened — it does not invent a workflow.
2. **Schema-anchored, hash-receipted, claim-bounded.** Matches the existing
   DefendableOS books-and-records doctrine (the 82-record hash chain on
   smash, the published deed flow via the Fly API ledger publisher,
   PR #7).
3. **Smallest publishable unit.** Condition records have minimal legal
   exposure compared to value opinions. Ship condition first; value later.
4. **Direct lane to AIOV.** Every field is AIOV-ready by structural design;
   see `integrations/aiov_future_integration.md` §"Receipt → AIOV linkage
   fields".
5. **Lives next to existing infrastructure.** `streetledger/compute/...` is
   a sibling of the existing `streetledger/runs/`, `streetledger/swarmjelly/`,
   `streetledger/ledger/` namespaces.

## 4 · Real Operational Evidence: smash RTX 5090

The schemas and protocol in this product are derived from a real sequence:

| step | observed |
| ---: | --- |
| 1 | Renter exited |
| 2 | Docker rental artifacts cleaned |
| 3 | Docker storage/runtime/CDI verified (runc + nvidia runtimes, CDI present) |
| 4 | GPU reset to persistence enabled + 550 W rental cap |
| 5 | High VRAM condition discovered: 28,114 MiB used despite zero containers |
| 6 | Investigation identified the cause as **first-party**: SwarmCurator vLLM (PID 75037) holding 28,104 MiB; SwarmJelly llama.cpp and DefendableRouter sessions also identified |
| 7 | Local model services shut down without touching Vast services |
| 8 | RTX 5090 returned to 2 MiB idle VRAM, 0% utilization, ~51 C, ~21.55 W idle, 550 W cap, persistence enabled |
| 9 | `vastai` and `vast_metrics` remained active |
| 10 | No Docker containers remained |
| 11 | Vast remote validation passed: system requirements, ResNet18 GPU, ECC, NCCL (1 GPU), combined stress-ng + gpu-burn 60s, test instance destroyed, machine test result: **DONE** |

This sequence is the canonical example. See `examples/smash_rtx5090_proof_receipt.example.json`
and `examples/smash_rtx5090_proof_receipt.example.md`.

The example receipt was constructed from **only the facts listed above**.
Per mission constraint, no GPU UUID, serial number, exact host IP, renter
identity, rental income, asset value, benchmark scores beyond the named
pass/fail status, or exact logs not supplied were invented.

## 5 · What the Receipt Proves

The HONEY example receipt establishes:

- The asset (`smash`, RTX 5090, single GPU, CUDA 13.1) was **identified to
  the runtime** at `2026-05-25T10:57:00Z`.
- At that timestamp, **no unintended workloads** were running — the first-
  party model servers were enumerated, named, and stopped per
  `remediation_actions[]`.
- The asset was returned to its **documented operating baseline** (550 W
  cap, persistence enabled, 2 MiB idle VRAM, 0% utilization, ~21.55 W idle
  draw, ~51 °C).
- The asset **passed six platform-remote tests** (Vast.ai validator) at
  the named scopes.
- All evidence is **hash-anchored** in `generated_artifact_hashes`.

## 6 · What the Receipt Does NOT Prove

Quoted verbatim from the schema-enforced `claim_boundaries.does_not_establish`:

- `market_value`
- `appraisal_under_uspap_or_equivalent`
- `manufacturer_warranty_status`
- `insurance_underwriting_acceptance`
- `lender_acceptance`
- `legal_title_or_ownership`
- `accreditation_by_third_party_body`
- `fitness_for_any_specific_purpose_beyond_the_named_tests`

The Tribunal gate refuses HONEY if any of these are claimed in a value
field. The receipt linter blocks publication if any banned vocabulary term
appears in a positive-claim field.

## 7 · Schema Summary

Five JSON Schema files (all draft 2020-12, all parse-validated):

| schema | purpose |
| --- | --- |
| `compute_asset_identity.schema.json` | host + GPU + runtime identity with privacy treatment |
| `compute_proof_receipt.schema.json` | top-level receipt artifact |
| `benchmark_observation.schema.json` | per-test observation with origin + scope + result + evidence_locator |
| `service_state_observation.schema.json` | docker + model server + rental platform + GPU + storage + runtime state snapshot |
| `receipt_manifest.schema.json` | provenance manifest published alongside the receipt |

Schemas live in `schemas/`. Each is `$id`-tagged under
`https://defendable.eth/schemas/...` and pinned to `v0.1`.

## 8 · Protocol Summary

Four protocol documents codify the smash lifecycle:

| doc | scope |
| --- | --- |
| `gpu_host_post_rental_protocol.md` | 10-phase end-to-end protocol |
| `benchmark_validation_protocol.md` | test_origin hierarchy + per-use-case required tests + limitations rule |
| `evidence_capture_requirements.md` | per-phase capture spec + directory layout + retention policy |
| `failure_taxonomy.md` | 13 finding codes with default severity, default Tribunal class, default remediation pattern |

## 9 · Failure Taxonomy

Thirteen codes (see `protocol/failure_taxonomy.md`):

- `RESIDUAL_DOCKER_ARTIFACTS`
- `GPU_MEMORY_HELD_BY_LOCAL_PROCESS` (the smash finding)
- `GPU_MEMORY_HELD_BY_UNKNOWN_PROCESS` (auto-PROPOLIS)
- `POWER_BASELINE_NOT_RESTORED`
- `PERSISTENCE_MODE_DISABLED`
- `NVIDIA_RUNTIME_UNAVAILABLE` (auto-PROPOLIS)
- `CDI_DEVICE_MISSING` (auto-PROPOLIS)
- `STORAGE_MOUNT_UNHEALTHY`
- `RENTAL_PLATFORM_SERVICE_DOWN` (auto-PROPOLIS)
- `REMOTE_VALIDATION_FAILURE` (auto-PROPOLIS)
- `TEMPERATURE_OUT_OF_POLICY`
- `UNVERIFIED_ASSET_IDENTITY` (auto-PROPOLIS, refuse receipt)
- `CLAIM_EXCEEDS_EVIDENCE` (linter rejection)

## 10 · CLI Product Specification

Three CLI documents (`cli_spec/`):
- `defendable_compute_cli_spec.md` — global flags + 7 subcommands + 9 hard contracts + exit codes
- `command_examples.md` — full smash flow + resale + disposition + fleet audit + verify-hashes
- `output_contract.md` — JSON/Markdown format guarantees + telemetry policy (none) + non-output guarantees

Subcommand family:
- `defendable-compute intake`
- `defendable-compute observe` (read-only default)
- `defendable-compute remediate-plan`
- `defendable-compute remediate` (operator confirms per finding)
- `defendable-compute validate`
- `defendable-compute receipt` (Tribunal gate + linter + hashes)
- `defendable-compute verify-hashes`

v0.1 ships the specification. v0.2 will implement it.

## 11 · Vast.ai Integration Lane

See `integrations/vast_ai_readiness_lane.md`. Key invariants:

- The CLI **never** restarts or modifies `vastai` / `vast_metrics`.
- Vast validator output is captured verbatim as the `evidence_locator` for
  the corresponding `benchmark_observation`.
- The CLI does not modify the Vast listing itself; operator manually
  re-lists once the receipt is issued.
- Pricing capture is out of v0.1 scope (belongs in v0.3 + AIOV product).

## 12 · AIOV Future Integration Lane

See `integrations/aiov_future_integration.md`. Hard split:

- **No version of the Defendable Compute Proof Receipt ever asserts value.**
- AIOV is a separate downstream product with its own schema, operator, and
  claim boundaries.
- Eight v0.1 receipt fields are AIOV-ready by design: asset_id, model,
  vram_total_mib, test_origin, observed_output, tribunal_verdict.verdict,
  observed_at, ledger_publication.record_sha256.

## 13 · Object Storage / Ledger Layout

See `integrations/object_storage_record_layout.md`. Layout:

```
streetledger/compute/assets/{asset_id}/
  identity/
  observations/{receipt_id}/
  benchmarks/{receipt_id}/
  receipts/{receipt_id}.{json,md,manifest.json}
  hashes/{receipt_id}.SHA256SUMS.txt
  valuation_future/   ← reserved for AIOV
```

Publication: extends the existing `defendableos/services/api/app/services/ledger_publisher.py`
GitHub Contents API pattern (PR #7 on defendableos). Extends the
DefendableLedger record_type taxonomy with `DCPR` (new), sibling of the
existing GENESIS / RECEIPT / VERDICT / PAIR / AUDIT classes from the
82-record smash chain.

## 14 · Kimi Intake Supporting Signals

Cross-references to `research/kimi_intake/2026-05-25/` (read-only):

| Kimi intake item | DCPR v0.1 mapping | confidence |
| --- | --- | --- |
| Build queue rank 5 · "Object-storage appraisal record structure" · effort small · gate n/a | **implemented** by `integrations/object_storage_record_layout.md` (compute namespace, value-naming withheld) | direct |
| Build queue rank 6 · "Defendable Box edge intake workflow" · gate HONEY (sigedge canary live) | **future** use_case=fleet_audit extension noted in `aiov_future_integration.md` | direct |
| Build queue rank 8 · "Proof of Compute scoring receipt" · gate HONEY (dim06 cite-anchored) | **future** sustained-load extension noted in `aiov_future_integration.md` | direct |
| dim05 asset_compute citations on counterfeit chip risk | informs `failure_taxonomy.md` `UNVERIFIED_ASSET_IDENTITY` rationale (counterfeit detection use case) | indirect — research_derived |
| dim06 ai_agent_trust / TEVV federal procurement | informs `benchmark_validation_protocol.md` test_origin hierarchy (`OEM` > `platform_remote` > `third_party` > `local`) | indirect — research_derived |
| HONEY signal IBM Cost of Data Breach `$10.22M` US avg | NOT mapped — no claim of breach cost in this product; condition record only | n/a |
| HONEY signal IC3 / fraud datasets | NOT mapped — separate product family (federal demand intelligence) | n/a |

**Critical distinction the memo enforces:** the smash RTX 5090 observation
is **directly observed operational evidence** (witnessed end-to-end on
2026-05-25). The Kimi-derived signals are **research_derived market context**
that informs product positioning but is NOT inputs to a specific receipt's
verdict. The two sources are kept structurally separate in the receipts:
operational evidence appears in `evidence_sources[]` / `benchmark_validation_results[]`,
and research context (if any) belongs only in human-facing memos, never
in machine-evaluated claim fields.

## 15 · Verification Gaps

Market claims from the Kimi intake that **still require independent
verification** before they appear in any external DefendableOS asset
(including any future AIOV product that consumes this product's receipts):

- The `$140B+` AI chip secondary market projection — `SIGNAL-0519` /
  `SIGNAL-0522` flagged PROPOLIS in the Kimi tribunal for "massive" /
  "enormous" framing; underlying dim05 citation needs primary-source verification.
- The `$103B` counterfeit national-security supply chain cluster — PR-AC-006 /
  PR-AC-007 receipts in dim05; PROPOLIS-flagged pending primary-source walk.
- The `$100B` chargeback / friendly fraud claim — `SIGNAL-0500` / `SIGNAL-0511`;
  cited [^159^] but the e-commerce-fraud framing is broader than chargeback alone.

None of these are inputs to the smash example receipt. They are listed here
only so the v0.3 / AIOV-v0.1 builds do not silently inherit unverified claims.

## 16 · Build Roadmap

| version | scope | gating |
| --- | --- | --- |
| **v0.1 (this)** | specification + schemas + one real example + protocols + CLI contract + integrations | local commit, no push |
| v0.2 | CLI implementation: `intake`, `observe`, `remediate-plan`, `remediate`, `validate`, `receipt`, `verify-hashes`; Vast.ai adapter; DefendableLedger publisher | unit tests, schema validation, lint test, fixture-based integration tests on the smash example |
| v0.3 | Vast.ai price-observation capture (still condition-only); fleet audit at scale; second platform adapter (RunPod or Coreweave) | second-platform conformance harness |
| AIOV v0.1 (separate product) | first value opinion artifact consuming DCPR receipts; its own schema and operator | gated on a corpus of HONEY DCPR receipts |

## 17 · Receipt Appendix

- Workspace SHA256SUMS: `receipts/SHA256SUMS.txt` · 22 entries
- Workspace build manifest: `receipts/build_manifest.json`
- Example receipt: `examples/smash_rtx5090_proof_receipt.example.json`
- Example markdown twin: `examples/smash_rtx5090_proof_receipt.example.md`
- Example completion receipt: `examples/smash_rtx5090_completion_receipt.md`
- Kimi intake cross-reference: `../../../research/kimi_intake/2026-05-25/`
- Local git commit (about to be created): `product: define Defendable Compute Proof Receipt v0.1 from smash evidence`

---

## Safety attestation

- ✅ No GPU workload executed
- ✅ No CUDA / vLLM / Ollama / llama.cpp / transformers invoked
- ✅ No Docker state change
- ✅ No Vast service touched
- ✅ No NVIDIA driver / runtime / power-limit / persistence change
- ✅ No network configuration change
- ✅ No apt install
- ✅ No original Kimi drop modified or deleted
- ✅ No GitHub push performed during this build
- ✅ CPU / filesystem / documentation / code-scaffolding only

`Books and records. No proof, no honey. To the shed.`
