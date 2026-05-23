# Defendable Compute Bench

## Benchmark-Attested Proof of Utility before Opinion of Value.

> The asset is captured.
> The evidence is hashed.
> The hardware is tested.
> The utility is graded.
> The market evidence is classified.
> The opinion is formed.
> The validator challenges it.
> The Deed publishes only what survives proof.

## 1. Executive purpose

Defendable Compute Bench is the **operating layer** that turns a real
piece of hardware into structured, hashed, evidence-classified
benchmark receipts. It must run **before** any Compute Proof of Value
record may move toward validator approval or public-safe deed
issuance.

This is not synthetic score theater. It is the physical-compute
expression of *Validate the Validator*: the platform refuses to
opine on resale, utility, or yield until the asset has been
captured, diagnosed, tested at appropriate scope, and the receipts
hashed into the Evidence Vault.

The bench is potentially the **front-door product** for Defendable
Compute: a software-led acquisition surface where any operator can
run a benchmark, get a hashed attestation receipt, and choose to
upgrade to a Proof of Value or MarketReady package.

## 2. Why benchmark attestation must occur before Opinion of Value

A market observation, a public specification, a founder statement,
and a rental signal **each carry different evidentiary weight** —
and none of them prove what the hardware in front of the operator
actually does today. Without a captured benchmark:

- AIOV is opining on a *spec sheet*, not on the *machine*
- A buyer cannot verify operational health at point of sale
- A rental yield claim is unanchored from this card's actual
  thermal/performance envelope
- Hold/rent/sell/redeploy analysis is forced to assume nominal
  performance
- A validator has nothing measurable to challenge

After a captured benchmark:

- AIOV sees identity confirmation, runtime state, thermals, power,
  measured utility within the asset's tier, and the receipt hash
- A buyer can re-attest at delivery against the seller's hashed
  receipt
- Rental yield analysis cites observed sustained behavior, not
  marketing TDP
- Hold/rent/sell/redeploy recommendations cite captured evidence
- The validator chain has something concrete to test claims against

## 3. Where Compute Bench fits in DefendableOS

| Layer | Role |
|---|---|
| **ProductRadar** | Identifies assets and market/utilization signals worth inspecting |
| **Defendable Compute Bench** | Captures hardware and produces benchmark-attested utility evidence |
| **Evidence Vault** | Preserves receipts, manifests, private evidence and public-safe exports |
| **Pair Factory** | Learns from failed claims, benchmark anomalies and validator corrections |
| **AIOV** | Forms draft Opinion of Value and Best Next Use Decision |
| **Validator Workflow** | Challenges the evidence, claim scope and public disclosure |
| **DefendableOS** | Controls lifecycle, identity, access and issuance |
| **Defendable Deed** | Ships the approved public-safe trust record |

## 4. E0–E7 benchmark philosophy

A Jetson and an H100 do not do the same work. **One universal score
would lie about both of them.** Compute Bench runs the workload tests
appropriate to the asset's tier. See
[`COMPUTE_BENCH_PROFILE_MATRIX.md`](./COMPUTE_BENCH_PROFILE_MATRIX.md)
for the per-tier profile.

The bench has no concept of a single asset-level number. It produces
**four orthogonal grades** (Identity · Health · Utility · Evidence)
that the operator and the validator read together. See
[`COMPUTE_ATTESTATION_GRADING_STANDARD.md`](./COMPUTE_ATTESTATION_GRADING_STANDARD.md).

## 5. Identity and private-identifier handling

Per Evidence Vault doctrine (see
[`EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md`](./EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md)):

- **Raw serial numbers** are PRIVATE_EVIDENCE by default
- **Device UUIDs · PCI identity · board identifiers · host
  relationships** are captured but routed to PRIVATE_EVIDENCE
- **Public-safe records** show *redacted identity confirmation*
  ("RTX 3090 Founders · 24 GB · serial captured · hash on file") and
  *manifest hash references* — never the raw serial
- A hash proves artifact integrity relative to the captured
  receipt. **It does not alone prevent future hardware
  substitution.** Higher-assurance transfer workflows may later
  require buyer-side re-attestation, photographs, chain-of-custody
  records and transfer receipts

### State concepts

The asset record carries one of the following bench-attestation
states:

```
IDENTITY_CAPTURED          identity evidence in PRIVATE vault
IDENTITY_HASHED            identity bundle has a SHA-256 receipt
BENCHMARK_PENDING          test plan exists · run not started
BENCHMARK_COMPLETE         test run finished · awaiting attestation
BENCHMARK_ATTESTED         hashed receipt bundle written to vault
RE_ATTESTATION_REQUIRED    transfer/lifecycle change demands re-run
BUYER_RE_ATTESTED          new owner has captured + hashed
```

## 6. Hashing and receipt bundle rules

Every bench run produces a **receipt bundle** at `compute-bench/runs/<run_id>/`
containing structured JSON files plus a `manifest.sha256` covering
the whole bundle.

See [`COMPUTE_BENCH_RECEIPT_SCHEMA.md`](./COMPUTE_BENCH_RECEIPT_SCHEMA.md)
for the canonical structure.

Hashes are computed with the same `services/hashing.py` pipeline the
rest of the platform uses · sorted-key compact JSON · SHA-256 · so
the integrity chain is uniform from edge capture through deed
publication.

## 7. Health diagnostic standard

The health portion of every run captures:

- Thermals (idle + sustained)
- Power (nominal + observed)
- Driver/runtime state
- ECC error status (where supported)
- Throttling events
- Memory/PCIe health where supported
- Operational stability over the chosen test duration

Health output is **classified into one of**: PASS · PASS_WITH_OBSERVATIONS
· CONDITIONAL · FAIL · NOT_TESTED · UNSUPPORTED_TEST_SCOPE. Each
result discloses **diagnostic method · runtime · thermal envelope ·
power state · errors/warnings · test limits.**

## 8. Utility benchmark standard

Workload tests are tier-aware. The utility grade names the workload
class actually measured, not an abstract score:

- `E1_EDGE_VISION_UTILITY_MEASURED`
- `E2_ENTRY_LOCAL_INFERENCE_MEASURED`
- `E4_WORKHORSE_AI_RENTAL_UTILITY_MEASURED`
- `E5_PREMIUM_LOCAL_AI_UTILITY_MEASURED`
- `E6_INSTITUTIONAL_ACCELERATOR_UTILITY_MEASURED`
- `E7_PRODUCING_NODE_READINESS_MEASURED`
- `UTILITY_NOT_YET_MEASURED`

Utility evidence captures: workload name + version + parameters,
input size class, throughput/latency observed, peak memory, sustained
power, runtime, and the source-classified output.

## 9. Market-evidence boundary

Benchmark utility proves **tested capability at inspection time**.
It does NOT prove resale value, future rental income, guaranteed
buyer interest, or guaranteed future performance. The platform's
public claims must respect this:

| The bench proves | The bench does NOT prove |
|---|---|
| What this machine did during the test | What buyers will pay for it |
| What workload class fits this hardware today | What this card will earn rented over a year |
| That identity was captured and hashed | That the hardware will never be substituted |
| That health was within X envelope at capture | That the hardware will perform the same in another rig |

## 10. Best Next Use Decision relationship

A benchmark-attested record must ultimately support a **decision**,
not just a score. The Best Next Use Decision record combines the
four grades with deployment context, owner objective, market
observations, comps where available, and rental receipts where
available to produce one of the documented recommendation states.

See [`BEST_NEXT_USE_DECISION_SCHEMA.md`](./BEST_NEXT_USE_DECISION_SCHEMA.md).

Recommendation states include HOLD_AND_RENT · RETAIN_AND_DEPLOY ·
SELL_NOW · TRADE_UP · PACKAGE_AS_NODE · REDEPLOY_EDGE ·
UPGRADE_AND_REASSIGN · PART_OUT · REFURBISH · RECYCLE_OR_RETIRE ·
SELL_COMPLETE_SYSTEM · REVIEW_REQUIRED · EVIDENCE_INCOMPLETE.

## 11. Public-safe attestation output

Every run produces `public_safe_attestation.json` derived from the
private bundle via the same `public_export_or_refuse()` guard the
rest of the platform uses. The public-safe output contains:

- Asset class · model · form factor (no raw serial)
- Compute tier (E0–E7)
- Identity Confidence Grade · Health Grade · Utility Grade ·
  Evidence Grade
- Workload class measured + summary metrics
- Captured-at timestamp · captured-by org reference
- Manifest hash and run_id
- Limitations + re-attestation triggers
- Cross-reference to the full deed once issued

The private bundle is **never** sent through the public lane.

## 12. Future buyer-side re-attestation and transfer lifecycle

When a benchmark-attested asset transfers ownership, the record
state advances to `RE_ATTESTATION_REQUIRED`. The new owner runs the
bench against the delivered hardware, and the platform:

1. Compares the new identity capture against the seller's hashed
   identity receipt
2. Re-grades health and utility on the buyer's side
3. Issues a `BUYER_RE_ATTESTED` follow-on record linked to the
   seller's deed
4. Documents any drift (different host · clock policy · thermal
   environment · driver version)

This is **documented**, not implemented in MVP. The seam is
defined so the chain extends naturally when transfer flow ships.

## 13. No-overclaim doctrine

Compute Bench may claim:
- "Benchmark-attested at the timestamps captured in the receipt"
- "Hardware identity captured and hashed to the bundle manifest"
- "Tested workload of class X produced observed throughput Y"
- "Public-safe attestation reflects validator-approved fields only"

Compute Bench **may not** claim:
- "Permanently authenticated hardware" (a hash is not a chain-of-custody)
- "Guaranteed future performance" (capture-time only)
- "Guaranteed rental income" (rental yield requires receipts)
- "Guaranteed resale value" (resale needs comp evidence)
- "Certified appraisal" (no certification authority issues anything)
- "Tamper-proof physical device identity from a hash alone"

## Hard operational rules

1. **No benchmark may run on a rented or active production asset
   without explicit founder approval and a safe maintenance window.**
   The CLI checks before running and reports the conflict if
   detected.
2. **Read-only by default.** No CLI command may change GPU clocks,
   power limits, or runtime configuration unless a future explicit
   operator mode is designed.
3. **Heavy load tests warn before running.** `quick` is the default
   scope · `standard` and `extended` require explicit operator opt-in.
4. **Local-first storage.** Every artifact is written to disk before
   any upload is considered. Upload is opt-in and per-artifact.
5. **No automatic deed issuance.** Bench receipts feed the deed
   pipeline · they do not bypass the validator.

## Related docs

- [`COMPUTE_BENCH_RECEIPT_SCHEMA.md`](./COMPUTE_BENCH_RECEIPT_SCHEMA.md) · the canonical run receipt structure
- [`COMPUTE_ATTESTATION_GRADING_STANDARD.md`](./COMPUTE_ATTESTATION_GRADING_STANDARD.md) · the 4-grade model
- [`COMPUTE_BENCH_PROFILE_MATRIX.md`](./COMPUTE_BENCH_PROFILE_MATRIX.md) · E0–E7 benchmark profiles
- [`DEFENDABLE_COMPUTE_BENCH_CLI_SPEC.md`](./DEFENDABLE_COMPUTE_BENCH_CLI_SPEC.md) · CLI command surface
- [`COMPUTE_BENCH_TOOLING_AUDIT.md`](./COMPUTE_BENCH_TOOLING_AUDIT.md) · per-tool evaluation
- [`BEST_NEXT_USE_DECISION_SCHEMA.md`](./BEST_NEXT_USE_DECISION_SCHEMA.md) · decision record
- [`EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md`](./EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md) · the storage layer this feeds
- [`COMPUTE_ASSET_TAXONOMY.md`](./COMPUTE_ASSET_TAXONOMY.md) · E0–E7 ladder
- [`COMPUTE_BEACHHEAD_30_DAY_PLAN.md`](./COMPUTE_BEACHHEAD_30_DAY_PLAN.md) · where bench fits in the product ladder
