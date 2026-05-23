# Compute Utilization Index · Specification

This is **not** a public index launch yet. It is the schema and
intelligence concept that Defendable Compute aggregates over time
as records accumulate.

## Purpose

Defendable Compute should eventually show **which categories of
hardware remain economically or operationally useful** · not merely
which cards are newest. The Compute Utilization Index is the
internal data model and report framework that, once populated, can
answer questions like:

- Which prior-generation cards still produce rental revenue?
- Which edge devices are deployed in production today?
- Which CPU node configurations are doing real orchestration work?
- Where is the cheapest entry into "useful AI compute" right now?

## Index categories

### 1. Rental Utilization Signal
- Source: lawful public rental observations (`VAST_PUBLIC_LISTING_RATE`,
  `VAST_PUBLIC_SUPPLY_OBSERVATION`) + first-party rental receipts
  (`VAST_FOUNDER_RENTAL_RECEIPT`, `VAST_FOUNDER_OCCUPANCY_HISTORY`)
- Output: per-asset-class median rental rate snapshot · operator
  capture rate · supply density observation
- Honest framing: "rental signal observed" · NOT "asset is rented"

### 2. Edge Deployment Utility
- Source: captured workload tests (Edge Utility Records)
- Output: per-device-class typical workload class · power envelope ·
  deployment-readiness rate
- Honest framing: "deployed in N captured cases" · NOT "fits all edge use"

### 3. Local AI Utility
- Source: model-compatibility evidence · memory-constraint testing ·
  runtime receipts
- Output: per-VRAM-bucket largest-model-successfully-run · tokens/sec
  envelope · runtime maturity
- Honest framing: "ran model X at quantization Y in N cases" · NOT
  "supports all models"

### 4. Upgrade-Cycle Liquidity
- Source: marketplace observations · verified paid comps where obtainable
- Output: per-asset-class days-on-market · sold-price-range observation
- Honest framing: "comparable activity observed" · NOT "guaranteed sale price"

### 5. Complete Node Readiness
- Source: GPU + CPU + RAM + storage + network configuration evidence ·
  operational test receipts
- Output: per-node-template completeness score · deployment-ready rate
- Honest framing: "configured and tested" · NOT "production guaranteed"

### 6. Second-Life Productivity
- Source: evidence that prior-generation equipment still performs
  useful, monetizable, or deployment-relevant work
- Output: per-prior-gen-card observed utility class breakdown ·
  hold/rent/sell/redeploy recommendations issued
- Honest framing: "still productively deployed in N captured cases"
  · NOT "still as good as new"

## Output examples · honest framing

Each index output is a labeled card · NEVER a ranking that implies
guaranteed value:

```
RTX 3090 24GB · Workhorse Rental / Local AI Utility
  Observed today: 8 captured Vast.ai listings (median $0.21/hr,
  snapshotted 2026-05-22T18Z).
  First-party operating receipts: 0 captured (founder upload pending).
  Largest local model run in captured tests: Llama-3-13B Q5 at 8K ctx.
  Recommendation tier: RETAIN_AND_RENT for operators · SELL only with
  paid-comp evidence.
```

```
Jetson Orin Nano-class · Affordable Edge AI Deployment Utility
  Observed today: 2 captured Edge Utility Records (operator-attested).
  Typical power envelope: 15W observed.
  Workload class breakdown: 1 small-LLM inference · 1 evidence capture.
  Recommendation tier: DEPLOY_LOCAL · resale value low · redeployment
  value high.
```

```
8GB GPU Node · Entry Local Inference / Creator Utility
  Observed today: 0 captured Defendable records yet.
  Public market context: liquid resale market · prices visible on
  eBay/Marketplace (snapshots pending).
  Largest local model run in captured tests: pending.
  Recommendation tier: EVIDENCE_INCOMPLETE.
```

```
CPU-Only Node · Orchestration / Retrieval / Evidence Utility
  Observed today: 1 captured node (ZimaBoard agent · operator-attested).
  Typical role: agent + evidence capture + storage gateway.
  Average operating cost: $0.62/mo at observed power.
  Recommendation tier: RETAIN_FOR_ORCHESTRATION when load-bearing.
```

```
RTX PRO 6000 Blackwell · Institutional AI Infrastructure Utility
  Observed today: 1 founder-owned deed live (DDEED-DOV-COMPUTE-000001-v3).
  Operating context: Tier 1 Cook · WRX90 Threadripper PRO.
  Largest captured workload: training-capable infrastructure.
  Recommendation tier: PREMIUM_DEED_LANE.
```

```
GPU Server + Storage + Network · Producing Node Utility
  Observed today: 0 captured records yet.
  Forthcoming source: ITAD partner pilots · complete-node intake schema
  ready · awaiting first ingested fleet.
  Recommendation tier: PROPOSED_PROOF_CASE.
```

## Hard constraints

- **The index must NOT publish unsupported rankings.** Numbers in
  the index are always counts of observations and receipts · not
  market authority claims.
- **The index must NOT imply guaranteed profitability.** Recommendations
  are based on captured evidence; future yield is not promised.
- **The index begins as an internal data model and report framework**
  until enough verified observations and paid receipts exist to
  publish a public-facing surface honestly.
- **The index must label `EVIDENCE_INCOMPLETE` openly.** If only
  one observation exists, the card says so · not "limited data
  suggests..."
- **The index never blends signal classes into a single score.**
  Rental utility, edge deployment utility, and local AI utility are
  surfaced as separate cards · the operator decides relative
  importance.

## Storage + schema (forthcoming · documented today)

Internal table for the index (future schema · documented here as
the contract):

```
compute_utility_observations
  · id
  · canonical_good_id  (FK to canonical_goods)
  · index_category     (RENTAL / EDGE / LOCAL_AI / UPGRADE_CYCLE
                       / NODE_READINESS / SECOND_LIFE)
  · signal_class       (the SignalClass enum value · honest)
  · observed_value     (numeric or JSONB depending on shape)
  · evidence_basis_artifact_id (FK to artifact_registry)
  · captured_at
  · rights_status
  · created_at
```

Aggregation views (forthcoming):

```
compute_utility_per_asset_class_view
  · canonical_good_id
  · category_breakdown JSONB
  · last_updated
```

## Path from "internal report" to "public index"

The index becomes public-facing only when:

1. ≥ 50 observations exist per asset class for ≥ 5 asset classes
2. ≥ 5 first-party rental receipts captured (operator-uploaded)
3. ≥ 3 Defendable Deeds with operating history have been issued
4. Doctrine review confirms the public framing matches what the
   evidence supports
5. The founder explicitly authorizes publication via a labeled
   commit · same gate as ENS publication

Until then · this remains internal report framework.

## Related docs

- `VAST_AI_UTILIZATION_SIGNAL_RAIL.md` · primary data source for the
  Rental Utilization signal
- `EDGE_AI_COMPUTE_LANE.md` · primary source for the Edge Deployment
  Utility signal
- `CPU_AND_SMALL_GPU_UTILITY_LANE.md` · primary source for the CPU/small
  GPU contributions
- `SECOND_LIFE_COMPUTE_STRATEGY.md` · primary source for the Second-Life
  Productivity index
- `COMPUTE_UTILITY_SCORE_STANDARD.md` · scoring framework feeding the index
- `COMPUTE_ASSET_TAXONOMY.md` · the canonical asset ladder
