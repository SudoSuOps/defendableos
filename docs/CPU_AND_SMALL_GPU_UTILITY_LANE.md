# CPU & Small-GPU Utility Lane

Defendable Compute must support assets that perform useful
AI-system work even when they are not premium GPUs. A CPU-only
node running the orchestration layer of an agent stack is
load-bearing. An 8GB GPU running embeddings + small models for a
local-business workflow is load-bearing. The platform values both.

## Doctrinal premise

> Not every useful compute asset is a GPU. Not every GPU is a
> training rig. Score the asset by the work it does, not by the
> dollar tier it sits in.

A CPU-only node should NOT be scored as if it were a GPU rental
asset. A Jetson edge node should NOT be scored as if it were an
RTX PRO 6000. An 8GB GPU should NOT be represented as suitable
for workloads requiring 24GB or 96GB memory. Each asset class
needs workload-specific utility representations and honest
limitations.

## CPU-only node classes

| Class | Example | Primary AI-system role |
|---|---|---|
| Orchestration node | EPYC, Xeon, Ryzen 9, Threadripper | runs the agent loop, the task queue, the scheduler |
| API / service node | mid-range Xeon, Ryzen 7 | serves the FastAPI / Node backend that fronts the AI stack |
| Embeddings / retrieval node | high-core-count CPU + fast NVMe | runs vector DB · BM25 · re-ranker · without GPU acceleration |
| ETL / data-normalization node | any modern multi-core | parses, validates, hashes, deduplicates source data before it ever touches a model |
| Vector database host | NVMe-heavy CPU box | hosts pgvector / Qdrant / Weaviate / Milvus · cold + warm tiers |
| Storage / catalog node | NAS-class hardware (TrueNAS, Synology, custom) | holds the Evidence Vault · serves manifest reads |
| Evidence hashing / receipt node | any modern CPU | computes SHA-256 over arriving artifacts · writes ArtifactRegistry rows |
| Lightweight local inference | Apple Silicon · Intel N-series with AVX | runs 1B-3B param models for very specific tasks |
| Network gateway / monitoring | OPNsense / pfSense / ZimaBoard | network observability for the platform itself |

A CPU-only node CAN be the most important node in a stack and the
cheapest. Defendable Compute records that honestly.

## Small GPU classes

| Class | VRAM | Example | Typical workload |
|---|---|---|---|
| 4GB GPU utility | 4 GB | GTX 1650 · older RX cards · entry-level discrete | display + light compute · embeddings · CV at low res |
| 6GB / 8GB GPU inference | 6-8 GB | RTX 3050 · 3060 · 4060 · A2000 | small-model inference · LoRA experiments · image gen at 512px-768px |
| 12GB GPU builder | 12 GB | RTX 3060 12GB · 4070 · A4000 | mid-size models · stable diffusion full-resolution · 7B-13B Q4 inference |
| Low-profile GPU edge | varies | T1000 · A2000 LP · workstation single-slot | server-rackmount edge inference · transcoding |

## Required utility signals for CPU + small-GPU nodes

The platform captures evidence around:

| Signal | Why it matters |
|---|---|
| Power draw (nominal + observed) | TCO calculation · always-on viability |
| Always-on suitability | thermal · noise · stability · enclosure fit |
| RAM / storage capacity | gates which workloads run · gates concurrency |
| Networking (link speed · LAN/WAN topology) | gates the workload that can be served externally |
| Largest model successfully run | the honest answer to "what does it actually do?" |
| Tokens-per-second or task throughput | only when captured · never estimated |
| Container / runtime readiness | Docker · k3s · systemd · supported? |
| Deployment stability | uptime over a tracked window · drift events |
| Private / offline utility | does this earn its keep on a local-only deployment? |
| Operating cost | $/month at observed power × local kWh rate |
| Intended workload | operator-attested target use |

## What we explicitly DO NOT score on these tiers

- **No `marketplace_sold_signal` weighting** for CPU-only nodes that
  rarely transact as discrete used assets · most CPU-only utility
  evidence is operator-attested redeployment value
- **No `rental yield analysis`** for nodes that aren't rentable through
  observable rails like Vast.ai
- **No "compute power" comparison to GPUs** for CPU nodes · they are
  not competing for the same job
- **No "VRAM equivalent"** abstraction · CPU RAM is not GPU VRAM ·
  the platform reports both honestly per-asset

## Recommendation outcomes for CPU + small-GPU records

| Recommendation | When it fires |
|---|---|
| `RETAIN_FOR_ORCHESTRATION` | CPU node load-bearing in an operator's stack · don't sell · don't redeploy elsewhere |
| `REDEPLOY_TO_LOCAL_AI` | small GPU underutilized in current role · stronger fit for local inference deployment |
| `SELL` | operator no longer has a workload · marketplace observation shows liquid resale |
| `PART_OUT` | system value > whole-asset value · CPU + RAM + storage worth more separately |
| `RECYCLE` | hardware below useful deployment threshold · honest end-of-life |
| `EVIDENCE_INCOMPLETE` | not enough captured to recommend · request more from operator |

## Worked example · ZimaBoard agent node

```json
{
  "record_type": "DEFENDABLE_CPU_NODE_UTILITY_RECORD",
  "compute_tier": "E0",
  "device": {
    "manufacturer": "Icewhale Tech",
    "model": "ZimaBoard 2 832",
    "cpu": "Intel N150",
    "ram_gb": 16,
    "storage_class": "M.2 NVMe + microSD",
    "tdp_w": 6,
    "network": "Dual 2.5GbE",
    "form_factor": "Single Board Computer"
  },
  "deployment_state": "ACTIVE_PRODUCTION",
  "workload_evidence": [
    {
      "workload": "Defendable evidence-capture agent",
      "events_per_sec": 320,
      "sha256_throughput_mb_s": 110,
      "uptime_days": 47,
      "captured_at": "2026-05-22T18:00:00Z",
      "evidence_status": "FIRST_PARTY_OPERATOR_RECEIPT"
    }
  ],
  "always_on_suitable": true,
  "operating_cost_usd_per_month": 0.62,
  "recommendation": "RETAIN_FOR_ORCHESTRATION",
  "recommendation_basis": "Sub-1W typical idle · always-on evidence capture role · zero marketplace resale signal · highest-utility role is in-place"
}
```

## Claim discipline

- A CPU-only node CAN be useful and a 4GB GPU CAN be useful · the
  platform NEVER says "useless" or "obsolete"
- A small GPU CAN be unsuitable for a 70B model · the platform DOES
  say so when the operator asks the wrong question
- A used CPU has limited liquid resale value · the platform says so
  honestly when an operator asks "what's it worth"
- A CPU node's resale value and its operating utility are separate
  numbers · the platform reports both

## Related docs

- `EDGE_AI_COMPUTE_LANE.md` · sister lane for edge devices
- `COMPUTE_ASSET_TAXONOMY.md` · the E0 → E7 ladder
- `COMPUTE_UTILITY_SCORE_STANDARD.md` · scoring framework that
  honors the tier differences encoded above
- `SECOND_LIFE_COMPUTE_STRATEGY.md` · why older isn't worthless
