# Second-Life Compute Strategy

> **A newer generation does not automatically make previous-generation
> compute economically obsolete. Older equipment is not valuable solely
> because it remains functional · utility and evidence must support the
> opinion.**

## Doctrinal premise

The market narrative for AI compute is "buy the latest." That narrative
under-represents an entire category of productive hardware. Second-Life
Compute is the lane that documents what prior-generation cards and
systems still do · at honest valuations · with workload-tested evidence.

This is not nostalgia. It is the lane where the platform has the most
intelligence advantage:

- The current market is loud about H100/H200/B-series · quiet about
  what 3090s actually earn today
- Most operators upgrading from 3090/4090 → 5090 don't have a
  defensible exit path
- ITAD firms move A100/T4/V100 inventory constantly · the buyer side
  needs trust signals more than the seller side

## What "Second-Life" includes

| Asset class | Why second-life |
|---|---|
| **RTX 3090 / 3090 Ti (24 GB)** | flagship of this lane · 24 GB still runs serious local models · rental demand observable · see Workhorse thesis |
| **RTX 4090** | previous consumer flagship · heavy rental rotation · large secondary supply |
| **A100 (40 GB / 80 GB)** | second-life enterprise training · still active in rental for fine-tunes and inference at scale |
| **V100 (16 GB / 32 GB)** | older enterprise · still useful for many inference workloads with INT8/FP16 |
| **T4 (16 GB)** | low-power inference workhorse · stable rental presence · datacenter density wins |
| **RTX A5000 / A6000** | workstation lineage · longer service life than consumer · steady inference + render |
| **GTX 1080 Ti / Titan-class** | edge-of-useful · runs small models · part-out value often higher than whole-asset |
| **Older complete workstations** | when the GPU + CPU + RAM + storage configuration is greater than the sum of parts |

## Why this lane matters commercially

1. **Volume:** orders of magnitude more 3090/4090 transactions per
   month than H100 transactions · the customer pool is wider
2. **Trust gap:** a used GPU on eBay has no provenance · buyers
   discount heavily · a Defendable Deed closes that discount
3. **Operator confusion:** owners genuinely don't know whether to
   hold/rent/sell · the platform's hold/rent/sell/redeploy/part-out
   analysis IS the product
4. **Aligned with founder's actual operating context:** the founder
   has owned 3090-class hardware · has observed rental signal first
   hand · this is the lane with the highest evidence depth available
   from day 1
5. **Adjacent to ITAD partner lane:** ITAD firms move enormous
   volumes of second-life hardware · the lane creates a natural
   conversation entry point for ITAD outreach

## The hold / rent / sell / redeploy / part-out / recycle matrix

Every Second-Life record outputs ONE of these recommendations
based on captured evidence:

| Recommendation | Triggers when |
|---|---|
| `HOLD_AND_RENT` | observable rental signal + first-party rental receipts (when captured) show positive yield |
| `SELL` | liquid resale comp evidence exists at price above 12-month projected rental yield · no operational role |
| `REDEPLOY_LOCAL` | owner has a workload that fits this card's VRAM/perf envelope · no need to expose to rental market |
| `REDEPLOY_EDGE` | card or system fits a lower-tier role (E1-E3) at lower power · current TDP wasted |
| `PART_OUT` | sum of components > whole-asset comp evidence · GPU + RAM + storage + CPU more liquid separately |
| `RECYCLE` | hardware below useful deployment threshold · honest end-of-life · platform supports this as a valid outcome |
| `EVIDENCE_INCOMPLETE` | recommendation cannot be issued without more captured data · operator gets a "what to collect next" list |

## The RTX 3090 flagship record · scope

`DDEED-DOV-COMPUTE-3090-WORKHORSE-001-v1` (forthcoming · proposed)

```json
{
  "record_type": "DEFENDABLE_WORKHORSE_UTILIZATION_RECORD",
  "compute_tier": "E4",
  "asset_class": "COMPUTE_HARDWARE",
  "subject": {
    "manufacturer": "NVIDIA",
    "model": "GeForce RTX 3090 Founders Edition",
    "vram_gb": 24,
    "memory_type": "GDDR6X",
    "tdp_w": 350,
    "ownership_status": "FOUNDER_OWNED",
    "host_rig": "Operator workstation · PCIe 4.0 x16 · 850W PSU"
  },
  "second_life_basis": {
    "production_role_documented": true,
    "current_workload": "local 13B-30B inference · FLUX.1 image gen",
    "still_market_relevant": true,
    "market_relevance_evidence": "VAST_PUBLIC_LISTING_RATE snapshots present · operator-observed rental demand"
  },
  "vast_ai_evidence_summary": {
    "public_listing_observations": "TBD · awaits first capture run",
    "founder_machine_listings": "TBD · founder-attested upload",
    "founder_rental_receipts": "TBD · founder-attested upload",
    "founder_occupancy_history": "TBD · founder-attested upload",
    "derived_yield_analysis": "EVIDENCE_INCOMPLETE until receipts captured"
  },
  "recommendation": "EVIDENCE_INCOMPLETE · upgrade to HOLD_AND_RENT or SELL once Vast.ai receipts captured",
  "operator_attested_disclaimers": [
    "Operator-owned single unit · mint condition · Founders Edition reference cooler",
    "Operator attestation only · no third-party inspection on file"
  ]
}
```

The current DDEED-DOV-COMPUTE-000003-v3 (RTX 3090 Founders · $950
operator-ask) is a **Compute Proof of Value** record · not a
Workhorse Utilization Record. They are different deliverables.
The PoV record sells the asset · the WUR analyzes whether to sell
at all. Both can be true for the same asset · in sequence.

## Pricing entry · Second-Life lane

| Product | Audience | Price |
|---|---|---|
| Free Second-Life Triage | any operator | $0 · 1-page identity + recommendation request |
| Paid Workhorse Utilization Record | owners with rental ambitions or hold/sell uncertainty | $199-$299 |
| Sell-side Upgrade package | active sellers needing premium presentation | $499 |
| Bulk Second-Life Fleet Triage | ITAD partners · refresh-cycle operators | $50-$100 per asset at lot prices |

## Anti-overclaim discipline

What the platform may say:
- "Captured Vast.ai listing snapshot shows N units at median $X/hr"
- "Founder operating receipts show Y hours rented in window Z · $W gross"
- "Card class is observed in productive deployment in N captured records"

What the platform may NOT say:
- "Older card outperforms newer card" without head-to-head receipts
- "Guaranteed rental income" · no income is guaranteed
- "This is the best card for [workload]" without comparative receipts
- "Always rents out" without occupancy history

## How Second-Life feeds the ITAD lane

When an ITAD partner signs a pilot agreement, their inventory feed
is automatically classified by tier. Second-Life-eligible inventory
(A100 · V100 · T4 · 3090 · 4090 · workstation cards) gets routed
to the Workhorse Utilization analyzer · the partner gets a
per-asset recommendation back instead of a flat resale estimate.

That's the partner-side product. The partner sees their inventory
sorted into HOLD/RENT/SELL/REDEPLOY/PART_OUT/RECYCLE columns with
evidence basis attached.

## Related docs

- `VAST_AI_UTILIZATION_SIGNAL_RAIL.md` · the primary data source for
  workhorse rental signal
- `COMPUTE_UTILIZATION_INDEX_SPEC.md` · Second-Life Productivity is
  index category #6
- `COMPUTE_ASSET_TAXONOMY.md` · E3-E6 tiers are where Second-Life lives
- `ITAD_OUTREACH_EXECUTION_PACK.md` · how the lane links to ITAD outreach
- `COMPUTE_TRADE_UP_AND_REDEPLOYMENT_LANE.md` · sister lane for active upgraders
