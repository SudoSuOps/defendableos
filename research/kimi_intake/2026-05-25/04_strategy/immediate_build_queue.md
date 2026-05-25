# Immediate Build Queue · 2026-05-25T11:37:32Z

> Ranked, executable build list from Kimi drop intake.
> Each item names the supporting signal + Tribunal gate.

| rank | build | business reason | source signal | effort | type | deliverable | tribunal gate |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | **Compute appraisal deed intake schema** | AIOV foundation; every Defendable Box needs a deed | dim05 signals + product_opportunity_map | medium | code+schema | `compute_deed.schema.json` v0.1 | HONEY: dim05 cite-anchored |
| 2 | **GPU benchmark-to-value receipt** | Converts raw benchmark output into signed valuation evidence | dim05 + Defendable Compute Bench (existing) | medium | code | `gpu_benchmark_receipt.py` CLI | HONEY: dim05 |
| 3 | **ITAD / secondary-market signal registry** | Capture refurbished GPU listings + counterfeit-risk markers | dim05 PR-AC-006 + supply chain receipts | medium | research+ingest | `itad_secondary_signals.jsonl` daily snapshot | JELLY: corroborate counterfeit cluster |
| 4 | **Vast.ai demand capture module** | First-party GPU pricing reality vs hyperscaler list prices | dim05 + Vast.ai entity in registry | small | code+integration | `vastai_demand_snapshot.py` cron module | HONEY |
| 5 | **Object-storage appraisal record structure** | Tigris bucket layout for appraisal evidence | existing object storage rail + dim05 | small | infra+schema | `streetledger/appraisals/{deed_id}.json` layout doc | n/a (infra) |
| 6 | **Defendable Box edge intake workflow** | Jetson sigedge already exists; needs the v1 enroll → bench → grade pipeline | sigedge defense doctrine + dim05 | medium | code | `/api/v1/edge/enroll` + `/api/v1/edge/benchmark` endpoints | HONEY: sigedge canary live |
| 7 | **Verified comps booklet generator** | Render an appraisal deed + comparable comps into a buyer-ready PDF | existing buyer-room work in `defendable/` | medium | code+template | `defendable_comps_booklet_v0.1.py` | n/a (rendering) |
| 8 | **Proof of Compute scoring receipt** | Signed receipt attesting sustained compute capability | dim06 ai_agent_trust + dim05 | medium | code+schema | `proof_of_compute_receipt.json` per-rig | HONEY: dim06 cite-anchored |
| 9 | **Federal demand intelligence registry expansion** | Layer in dim01 (consumer financial) + dim02 (fraud) into the federal corpus v0.3 | dim01-02 + pod07_08 | medium | dataset assembly | federal v0.3 with consumer-finance lane | HONEY/JELLY mix |
| 10 | **defendable_demand_signals_v0.1 HF dataset** | Publish the 262 HONEY signals as a citable AI-trust dataset | signal_registry HONEY rows | small | dataset packaging | HuggingFace dataset card + JSONL | HONEY: per-row cited |

## Sequencing guidance

- **Week 1:** Ranks 1, 4, 5 — establishes the appraisal deed schema + first GPU pricing snapshot + object-storage layout
- **Week 2:** Ranks 2, 6, 8 — builds the bench → value → POC receipt chain on sigedge as first edge customer
- **Week 3:** Ranks 3, 7, 10 — ITAD signal registry + comps booklet + first dataset publication
- **Week 4:** Rank 9 + dimension files promoted to swarm-research v0.3

## Tribunal gates explained

- **HONEY** = at least one cite-anchored supporting signal in the drop · safe to build
- **JELLY** = supporting signal exists but needs corroboration · build but mark as preview
- **PROPOLIS** = no supporting signal or inflated framing · DO NOT build until verified
