# Compute Asset Taxonomy

The canonical asset ladder for Defendable Compute. Every record
in the platform attaches one `compute_tier` from E0 to E7 so the
right doctrine, the right score family, and the right recommendation
matrix apply.

## Doctrinal premise

> Useful AI compute exists at eight tiers · not three. The market
> talks about three (consumer / workstation / enterprise). The
> platform documents eight because customer reality has eight.

## The E0 → E7 ladder

### E0 · CPU-only utility node
- Examples: ZimaBoard, OPNsense box, NAS-class hardware,
  Raspberry Pi-class SBC, Apple Silicon Mac mini, x86 mini-PC
- Typical role: orchestration · evidence capture · storage gateway ·
  agent host · vector DB · API frontend · ETL
- Power envelope: 5W-30W
- Score family: Edge / Local Utility (`CUS_EDGE_v1`)
- Primary doc: `CPU_AND_SMALL_GPU_UTILITY_LANE.md`

### E1 · Edge AI accelerator
- Examples: Jetson Orin Nano (4/8 GB) · Jetson Orin NX (8/16 GB) ·
  Coral TPU · low-power NPU SoMs
- Typical role: local inference · sensor processing · CV/VLM
  workloads · always-on edge intelligence
- Power envelope: 7W-25W
- Score family: Edge / Local Utility (`CUS_EDGE_v1`)
- Primary doc: `EDGE_AI_COMPUTE_LANE.md`

### E2 · Premium edge / mobile workstation
- Examples: Jetson AGX-class · NUC-style boxes with eGPU ·
  workstation laptops with discrete GPU · small-form-factor desktops
  with 6-8 GB GPU
- Typical role: mobile rigs · creator boxes · field deployment ·
  small-business AI workflows
- Power envelope: 30W-150W
- Score family: Edge / Local Utility (`CUS_EDGE_v1`) graduating
  into Workhorse where rental signal exists

### E3 · Small-GPU workstation
- Examples: RTX 3050/3060/4060 · A2000 · workstation cards 4-12 GB
- Typical role: entry local inference · LoRA experiments · embeddings ·
  image gen at 512-768px · video transcoding
- Power envelope: 100W-200W
- Score family: Workhorse Utility (`CUS_WORKHORSE_v1`)
- Primary doc: `CPU_AND_SMALL_GPU_UTILITY_LANE.md`

### E4 · Workhorse GPU rig (consumer flagship · current or prior-gen)
- Examples: RTX 3090 · RTX 4090 · RTX 5090 · RTX A5000
- Typical role: serious local AI · rental on Vast.ai · stable
  diffusion · 13B-30B inference · LoRA fine-tunes
- Power envelope: 250W-450W per GPU
- Score family: Workhorse Utility (`CUS_WORKHORSE_v1`)
- Primary docs: `VAST_AI_UTILIZATION_SIGNAL_RAIL.md` ·
  `SECOND_LIFE_COMPUTE_STRATEGY.md`

### E5 · Workstation Blackwell / premium workstation tier
- Examples: RTX 4500 Blackwell · A6000 · A6000 Ada · enterprise
  workstation cards in workstation chassis
- Typical role: professional workloads · long-life deployment ·
  serve dual 9B + image gen · vast.ai sweet spot
- Power envelope: 230W-300W per GPU
- Score family: Workhorse Utility (`CUS_WORKHORSE_v1`)

### E6 · Institutional workstation rack node
- Examples: RTX PRO 6000 Blackwell (96 GB) · 2-4 GPU WRX90 ThreadRipper
  PRO rigs · institutional AI infrastructure
- Typical role: 70B+ training · multi-GPU inference · institutional
  deployment · premium deeds
- Power envelope: 600W-2,000W per node
- Score family: Institutional Utility (`CUS_INSTITUTIONAL_v1`)
- Anchor record: `DDEED-DOV-COMPUTE-000001-v3`

### E7 · Rack / multi-node cluster
- Examples: H100/H200 SXM rack nodes · multi-node clusters with
  high-speed interconnect · datacenter-grade deployments
- Typical role: large-scale training · production inference clusters ·
  enterprise tenancy
- Power envelope: 10kW+ per rack
- Score family: Institutional Utility (`CUS_INSTITUTIONAL_v1`)
- Note: PROPOSED_PROOF_CASE status until first institutional customer
  onboarded with rack-scale infrastructure

## Asset attributes captured per tier

Every record carries the following identity fields regardless of tier:

```
compute_tier            E0..E7
asset_class             COMPUTE_HARDWARE
manufacturer            string
model                   string
form_factor             SOM_WITH_CARRIER | DISCRETE_CARD | MOBILE | DESKTOP
                        | WORKSTATION_TOWER | RACK_NODE | RACK_CHASSIS
vram_gb_per_unit        nullable for CPU-only nodes
ram_gb                  required
storage_class           required (NVMe class · capacity)
network_class           required (GbE/10GbE/100GbE/IB)
tdp_w_nominal           required from spec
tdp_w_observed          captured when measured
ai_acceleration_tops    when applicable
ownership_status        FOUNDER_OWNED | OPERATOR_OWNED | PARTNER_INVENTORY
                        | PROPOSED_PROOF_CASE
deployment_state        ACTIVE_PRODUCTION | LISTED | IDLE | DECOMMISSIONED
                        | NOT_YET_OWNED
```

## Cross-tier interactions · the lanes

Assets move between tiers via documented lanes:

| From | To | Lane | Typical trigger |
|---|---|---|---|
| E4 | E2 | REDEPLOY_EDGE | flagship card retired from rental → fits a creator/desk role at lower power |
| E4 | E1 | PART_OUT | sum of GPU + RAM + storage > whole-asset comp |
| E5 | E4 | REDEPLOY_WORKSTATION | workstation card moved into a consumer rig for vast.ai listing |
| E6 | E4 | REDEPLOY_WORKSTATION | enterprise rig stepped down to workstation tier on retirement |
| E0 | E0 | RETAIN_FOR_ORCHESTRATION | CPU node load-bearing in current role · no movement |
| E3 | E0 | DOWNGRADE_TO_DISPLAY | small GPU deprecated → still useful for display + light compute |

These lanes are the `COMPUTE_TRADE_UP_AND_REDEPLOYMENT_LANE.md`
substrate · documented in detail there.

## What the taxonomy is NOT

- Not a price ladder. E7 is not "more valuable than" E0 by default.
  A load-bearing E0 in production beats an idle E7 in a closet.
- Not a quality ladder. Every tier has serious, useful AI deployments.
- Not a permanent classification. An asset's tier reflects its
  current configuration · a card moved into a different host can
  shift tier.

## What the taxonomy IS

- The canonical reference every Defendable Compute record cites.
- The cross-reference for which score family applies.
- The basis for which doctrine docs and which signal classes are valid.
- The shared vocabulary for ITAD partner conversations · founder
  records · public claims.

## Currently-known assets · placed on the ladder

| Asset | Tier | Status |
|---|---|---|
| ZimaBoard 2 832 (founder-owned) | E0 | EVIDENCE_PARTIAL · agent role attested |
| Jetson Orin Nano Super 8GB (sigedge) | E1 | EVIDENCE_RICH · benchmark + uptime captured |
| RTX 3090 Founders (DDEED-DOV-COMPUTE-000003) | E4 | DEED LIVE · OPERATOR_ASK $950 |
| RTX 5090 (DDEED-DOV-COMPUTE-000002) | E4 | DEED LIVE · OPERATOR_ASK $3,900 |
| RTX 4500 Blackwell | E5 | PROPOSED_PROOF_CASE (4-card swarmrig-01) |
| RTX PRO 6000 Blackwell (DDEED-DOV-COMPUTE-000001) | E6 | DEED LIVE · OPERATOR_ASK $9,850 |
| Multi-node H100/H200 cluster | E7 | PROPOSED_PROOF_CASE · awaiting first institutional intake |

## Related docs

- `EDGE_AI_COMPUTE_LANE.md` · E1-E2 primary
- `CPU_AND_SMALL_GPU_UTILITY_LANE.md` · E0 + E3 primary
- `VAST_AI_UTILIZATION_SIGNAL_RAIL.md` · E4-E5 rental signal
- `SECOND_LIFE_COMPUTE_STRATEGY.md` · E3-E5 second-life lens
- `COMPUTE_UTILITY_SCORE_STANDARD.md` · score families per tier
- `COMPUTE_UTILIZATION_INDEX_SPEC.md` · aggregation across tiers
- `COMPUTE_TRADE_UP_AND_REDEPLOYMENT_LANE.md` · lane mechanics
- `DEFENDABLE_COMPUTE_BENCH.md` · the benchmark-attested live-test layer that grades every tier
- `COMPUTE_BENCH_PROFILE_MATRIX.md` · per-tier benchmark profiles
