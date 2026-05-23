# Best Next Use Decision · Schema

A benchmark-attested compute record must ultimately support a
**decision**, not just a score. The Best Next Use Decision (BNUD) is
the structured record that combines bench grades + deployment
context + market evidence + owner objective into one of a small set
of recommendation states.

It is **not** a price prediction. It is "given what we observed,
here is the most defendable next action."

## Recommendation states

| State | Triggers when |
|---|---|
| `RETAIN_AND_DEPLOY` | Asset is load-bearing in current role · removing it would damage operator capability |
| `HOLD_AND_RENT` | Asset has observable rental signal + operator has rental capacity · projected gross yield positive based on captured inputs |
| `REDEPLOY_EDGE` | Asset fits a lower-tier role (E1-E3) at lower power · current TDP wasted |
| `PACKAGE_AS_NODE` | Asset's value compounds when bundled with CPU + RAM + storage + network as one complete-node deed |
| `UPGRADE_AND_REASSIGN` | Operator upgrading · outbound asset moves to second rig (`KEEP_AS_SECONDARY_RIG` equivalent in TRADE_UP_LANE) |
| `SELL_NOW` | Comp evidence supports sale price > 12-month projected rental yield · no operational role |
| `TRADE_UP` | Operator wants to upgrade · outbound asset has resale comp evidence supporting a trade |
| `SELL_COMPLETE_SYSTEM` | Bundled-system comp evidence > per-card comp evidence × component count |
| `PART_OUT` | Sum of components > whole-asset comp evidence · GPU + RAM + storage + CPU more liquid separately |
| `REFURBISH` | Health Grade indicates fixable issue (thermal pad replacement · re-paste · cable management) before rental or sale |
| `RECYCLE_OR_RETIRE` | Hardware below useful deployment threshold · honest end-of-life · platform supports this as valid outcome |
| `REVIEW_REQUIRED` | One or more grades carry observations the validator must address before recommendation can issue |
| `EVIDENCE_INCOMPLETE` | Material evidence missing · operator gets a "what to capture next" list |

## Required inputs

A BNUD cannot issue without all of:

| Input | Source | Notes |
|---|---|---|
| `asset_identity_confidence` | bench Identity Grade | Must be at least Grade C |
| `health_grade` | bench Health Grade | Including `NOT_TESTED` (documents the gap) |
| `measured_utility_grade` | bench Utility Grade | Including `UTILITY_NOT_YET_MEASURED` |
| `power_thermal_observations` | bench `health_diagnostic.json` + `thermal_power_trace.jsonl` | |
| `deployment_context` | operator attestation in `best_next_use_inputs.json` | E.g., "WRX90 host · institutional rack" |
| `current_workload` | operator attestation | E.g., "Qwen3.5-27B drafting" |
| `market_observations` | OBSERVATION vault | Vast.ai snapshots · eBay listings · partner observations |
| `verified_sold_comps` | DERIVED vault · Comp Foundry | Where available |
| `actual_rental_receipts` | PRIVATE vault | Where available |
| `cost_maintenance_information` | operator attestation | Where supplied |
| `owner_objective` | operator attestation | RENTAL_REVENUE · LOCAL_CAPABILITY · CASH_CONVERSION · SIMPLICITY |
| `evidence_limitations` | bench `validator_flags.json` + operator attestation | Honest list |

## Output schema

```json
{
  "bnud_id": "bnud-<run_id>",
  "asset_record_id": "DDEED-DOV-COMPUTE-000001",
  "asset_tier": "E6",
  "captured_at": "2026-05-23T03:00:00Z",
  "bench_run_ref": "cb-20260523T024500Z-9f2c",
  "bench_grades": {
    "identity": "A · PRIVATE_IDENTIFIER_CAPTURED_AND_HASHED",
    "health": "PASS",
    "utility": "E6_INSTITUTIONAL_ACCELERATOR_UTILITY_MEASURED",
    "evidence": "B · FIRST_PARTY_OPERATIONAL_EVIDENCE_ONLY"
  },
  "owner_objective": "RENTAL_REVENUE",
  "deployment_context": "INSTITUTIONAL_FLEET · WRX90/Xeon · 2-GPU rig · GPU 1 serving Qwen",
  "market_inputs": {
    "vast_ai_listing_snapshots": 0,
    "ebay_browse_observations": 0,
    "first_party_rental_receipts": 0,
    "verified_sold_comps": 0,
    "operator_ask_price_usd": 9850
  },
  "primary_recommendation": "EVIDENCE_INCOMPLETE",
  "primary_recommendation_basis": "Bench grades support institutional utility · rental signal evidence not yet captured · sale comp evidence not yet captured · operator-stated ask present but unanchored",
  "secondary_paths": [
    {"state": "HOLD_AND_RENT", "blocked_on": "Capture Vast.ai listing snapshot + first-party rental receipt"},
    {"state": "SELL_NOW", "blocked_on": "Capture ≥3 sold-comp receipts for RTX PRO 6000 Blackwell 96GB"},
    {"state": "PACKAGE_AS_NODE", "blocked_on": "Run E7 complete-node bench on swarmrails (requires GPU 1 maintenance window)"}
  ],
  "evidence_to_capture_next": [
    "VAST_PUBLIC_LISTING_RATE snapshot (manual analyst · 1 hour)",
    "FIRST_PARTY_RENTAL_RECEIPT if operator runs trial Vast.ai listing",
    "Sold-comp receipts via eBay Browse + ITAD partner feeds"
  ],
  "validator_status": "VALIDATOR_REVIEW_REQUIRED",
  "issuance_status": "RESERVED_NOT_ISSUED"
}
```

## Hard rules

1. **Benchmark utility does not alone determine sell price.** A
   Utility Grade `E6_*` tells you what the card *can do*. It does not
   tell you what a buyer will pay.

2. **Public asking prices do not alone determine value.** Vast.ai
   rates and eBay asks are OBSERVATION-class evidence · they carry a
   Grade C ceiling.

3. **Offered Vast.ai rates do not alone determine yield.** Offered
   ≠ rented · rented ≠ paid · the platform requires first-party
   rental receipts to model yield honestly.

4. **A decision recommendation must disclose missing inputs.** The
   `evidence_to_capture_next` field is mandatory · the operator
   sees exactly what's blocking the upgrade to a stronger
   recommendation.

5. **No paid-value opinion may be public-safe issued from
   incomplete benchmark/evidence status unless clearly scoped and
   founder/validator approved.** Even with `BNUD: EVIDENCE_INCOMPLETE`,
   the operator may issue an OPERATOR_ASK price record · but the deed
   labels it as operator-stated, not validator-approved.

## How the BNUD interacts with existing lanes

| BNUD State | Routes to |
|---|---|
| `HOLD_AND_RENT` | Workhorse Utility Record (E4-E5) · or institutional rental track (E6) |
| `SELL_NOW` · `TRADE_UP` | Compute Proof of Value record · sell-side package |
| `SELL_COMPLETE_SYSTEM` | Complete Node Package (E5-E7) |
| `UPGRADE_AND_REASSIGN` | Trade-Up Record (per [`COMPUTE_TRADE_UP_AND_REDEPLOYMENT_LANE.md`](./COMPUTE_TRADE_UP_AND_REDEPLOYMENT_LANE.md)) |
| `REDEPLOY_EDGE` | Edge Utility Record (E1-E2) on the redeployed asset |
| `PACKAGE_AS_NODE` | E7 Complete-Node Package |
| `PART_OUT` | Per-component sell records |
| `REFURBISH` | Refurbish task + re-bench afterward |
| `RECYCLE_OR_RETIRE` | ITAD partner handoff (per [`ITAD_OUTREACH_EXECUTION_PACK.md`](./ITAD_OUTREACH_EXECUTION_PACK.md)) |

## Public surfacing

A BNUD's public-safe form shows the primary recommendation, the
blocked-on list for secondary paths, and the evidence-to-capture-next
list. It never shows the operator's full deployment context, private
cost data, or operator commentary. The recommendation is a labeled
**doctrine output**, never a guarantee.

## Related docs

- [`DEFENDABLE_COMPUTE_BENCH.md`](./DEFENDABLE_COMPUTE_BENCH.md) · the layer that produces the bench inputs
- [`COMPUTE_ATTESTATION_GRADING_STANDARD.md`](./COMPUTE_ATTESTATION_GRADING_STANDARD.md) · how grades feed the decision
- [`SECOND_LIFE_COMPUTE_STRATEGY.md`](./SECOND_LIFE_COMPUTE_STRATEGY.md) · sister doctrine for prior-gen hardware
- [`COMPUTE_TRADE_UP_AND_REDEPLOYMENT_LANE.md`](./COMPUTE_TRADE_UP_AND_REDEPLOYMENT_LANE.md) · sister doctrine for upgrading operators
- [`COMPUTE_UTILITY_SCORE_STANDARD.md`](./COMPUTE_UTILITY_SCORE_STANDARD.md) · the post-bench 3-family scoring framework
