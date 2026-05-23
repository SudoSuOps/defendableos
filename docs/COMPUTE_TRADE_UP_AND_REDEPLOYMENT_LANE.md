# Compute Trade-Up & Redeployment Lane

When an operator upgrades · the old asset doesn't disappear. It
moves. The Trade-Up & Redeployment Lane is the doctrine + workflow
that documents the move and assigns honest value to both sides
of the transition.

## Doctrinal premise

> The operator upgrading from a 3090 to a 5090 is not "throwing
> away" the 3090. They are deciding between HOLD, RENT, SELL,
> REDEPLOY, PART_OUT, or RECYCLE. The platform's job is to make
> that decision defensible.

This is the sister lane to `SECOND_LIFE_COMPUTE_STRATEGY.md`.
Second-Life describes the asset class. Trade-Up describes the
operator's transition workflow.

## The transition matrix

Every trade-up event produces ONE inbound asset (the new card)
and a recommendation for the outbound asset (the old card).

| Outbound recommendation | Triggers when |
|---|---|
| `KEEP_AS_SECONDARY_RIG` | operator has workloads at both tiers · old card moves to second rig |
| `LIST_ON_VAST_AI` | operator has rental capacity · card fits the workhorse rental lane |
| `SELL_WITH_DEED` | comp evidence supports sale price > 12-month projected rental yield |
| `SELL_BUNDLED_WITH_RIG` | host system + card sells better than card alone |
| `REDEPLOY_TO_EDGE_ROLE` | card has lower-power local deployment fit · creator desk · sensor rig |
| `PART_OUT` | GPU + RAM + storage worth more separately than whole-rig |
| `RECYCLE` | hardware below useful deployment threshold · honest end-of-life |
| `EVIDENCE_INCOMPLETE` | need more captured data to recommend |

## The Trade-Up Record

A Trade-Up Record is a Defendable Compute artifact that:

1. **Identifies both assets** · inbound + outbound with tier + spec
2. **Captures the operator's workload context** · what the new
   asset enables · what the old asset stops doing
3. **Surfaces the recommendation** for the outbound asset based on
   captured evidence (Vast.ai signal · comp evidence · workload fit)
4. **Optionally links to a Compute Proof of Value record** for the
   outbound asset when SELL_WITH_DEED is the recommendation
5. **Stays anchored to operator-attested inputs** · no auto-pricing

Structured output:

```json
{
  "record_type": "DEFENDABLE_TRADE_UP_RECORD",
  "transition_id": "DTU-DOV-COMPUTE-3090-TO-5090-001",
  "outbound_asset": {
    "compute_tier": "E4",
    "manufacturer": "NVIDIA",
    "model": "GeForce RTX 3090 Founders Edition",
    "current_role": "Operator workstation · 13B-30B inference + FLUX",
    "documented_workload_history": "18 months in workstation role",
    "evidence_captured": [
      "VAST_PUBLIC_LISTING_RATE × 8 snapshots",
      "operator-attested role history",
      "operator-attested mint condition"
    ]
  },
  "inbound_asset": {
    "compute_tier": "E4",
    "manufacturer": "NVIDIA",
    "model": "GeForce RTX 5090",
    "intended_role": "Replace 3090 in operator rig · GDDR7 · 32 GB"
  },
  "decision_inputs": {
    "operator_has_second_rig": true,
    "operator_has_rental_capacity": true,
    "captured_comp_evidence_for_outbound": "EVIDENCE_INCOMPLETE",
    "captured_rental_receipts_for_outbound": "EVIDENCE_INCOMPLETE",
    "redeployment_fit": "fits E2 creator desk · fits E1-E2 local AI inference"
  },
  "recommended_action": "LIST_ON_VAST_AI",
  "recommendation_basis": "Operator has rental capacity · card class shows productive rental signal · proceeding to SELL requires comp receipts not yet captured",
  "next_evidence_to_capture": [
    "VAST_FOUNDER_MACHINE_LISTING for outbound 3090",
    "VAST_FOUNDER_RENTAL_RECEIPT after 30-60 days listing",
    "comp evidence from 3 closed eBay/Marketplace transactions"
  ],
  "linked_records": {
    "outbound_compute_proof_of_value": "DDEED-DOV-COMPUTE-000003-v3 (existing)",
    "outbound_workhorse_utility_record": "DDEED-DOV-COMPUTE-3090-WORKHORSE-001-v1 (proposed)"
  }
}
```

## The redeployment fitness rule

Before the platform recommends `REDEPLOY_TO_EDGE_ROLE`, it MUST
verify:

| Check | How |
|---|---|
| Lower-power role available | operator-attested workload exists at lower tier |
| Power envelope fits | TDP × hours × kWh rate produces honest TCO |
| Driver / runtime fit | card works in the proposed lower-tier host |
| Cooling / chassis fit | physical placement validated · operator-attested |
| No higher-value alternative | rental + sale options scored lower than redeployment |

If any check fails · the recommendation degrades to `EVIDENCE_INCOMPLETE`
with a list of what's missing.

## Pricing entry · Trade-Up lane

| Product | Audience | Price |
|---|---|---|
| Free Trade-Up Triage | any operator upgrading | $0 · 1-page recommendation |
| Paid Trade-Up Record | operators wanting documented outbound recommendation | $149-$249 |
| Bundle: Trade-Up + Workhorse Utility Record | operators wanting both | $349-$499 |
| Bundle: Trade-Up + Compute Proof of Value | operators selling the outbound | $599-$799 |
| ITAD Partner Bulk Trade-Up | refresh-cycle inventory | $50-$100 per asset |

## The ITAD-partner version

When an ITAD partner ingests a refresh-cycle batch:

1. **Identify** which inbound assets are replacing which outbound assets
2. **Cluster** by outbound asset class (e.g., 12 returning 3090s · 4
   returning A6000s · 8 returning T4s)
3. **Score** the outbound cluster using current Vast.ai + comp evidence
4. **Output** a recommendation matrix by cluster · HOLD/RENT/SELL/
   REDEPLOY/PART_OUT/RECYCLE columns
5. **Surface** flagship-record candidates · assets with rich evidence
   become candidates for paid Workhorse Utility Records the partner
   can resell alongside the asset

## The operator-attested upgrade dialog

The intake form for a Trade-Up Record asks:

```
1. What asset are you replacing?
   [class · model · capacity · age · current role]

2. What asset are you replacing it with?
   [class · model · capacity · planned role]

3. What is your current workload?
   [free text · operator-attested]

4. Do you have a second rig the outbound could move to?
   [yes / no / maybe]

5. Have you rented on Vast.ai before?
   [yes / no / interested but never tried]

6. What's your storage / network setup?
   [free text · for redeployment fit]

7. What's your local kWh rate?
   [number · for TCO math]

8. What outcome are you optimizing for?
   [revenue / simplicity / cash conversion / keep capability]
```

The recommendation is generated from these inputs plus captured
external signal · operator sees exactly which inputs drove which
recommendation.

## Anti-overclaim discipline

The Trade-Up Record may say:
- "Captured signal supports LIST_ON_VAST_AI as best-evidenced path"
- "Operator-attested second-rig availability supports KEEP_AS_SECONDARY_RIG"
- "Captured comp evidence supports SELL at price range $X-$Y"

The Trade-Up Record may NOT say:
- "Guaranteed sale at $X"
- "Rental income of $X/month"
- "Your old card is obsolete"
- "You should upgrade"

The platform never advises on whether to upgrade · only on how
to handle the outbound asset once the operator has decided.

## Related docs

- `SECOND_LIFE_COMPUTE_STRATEGY.md` · the asset-class lens
- `VAST_AI_UTILIZATION_SIGNAL_RAIL.md` · rental-signal source
- `COMPUTE_ASSET_TAXONOMY.md` · the E0-E7 tier ladder
- `COMPUTE_UTILITY_SCORE_STANDARD.md` · scoring framework
- `ITAD_OUTREACH_EXECUTION_PACK.md` · partner-side workflow
- `COMPUTE_BEACHHEAD_30_DAY_PLAN.md` · where Trade-Up sits in the product ladder
