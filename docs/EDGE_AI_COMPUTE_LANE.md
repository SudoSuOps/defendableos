# Edge AI Compute Lane

Edge devices are a first-class lane inside Defendable Compute · not
an afterthought. Useful AI begins well below enterprise GPU pricing
when the workload is documented honestly.

## Strategic position

The Edge lane proves that AI compute starts at the device level ·
not the rack level. A Jetson Orin Nano-class device deployed for
private inference produces measurable value for a founder, a small
business, a hospital office, a creator, or a security operator ·
even if its resale price is small.

Edge devices in scope:

- **Jetson Orin Nano-class** systems (4GB · 8GB)
- **Jetson Orin NX-class** systems (8GB · 16GB)
- **Jetson AGX-class** systems where appropriate
- Compact NVIDIA edge devices and developer kits
- **ZimaBoard-class** compact systems used for agents, storage,
  retrieval, orchestration, or CPU inference
- Low-profile GPU edge boxes (single-slot · USFF · NUC-style with
  external accelerator)
- Local / offline inference nodes
- Air-gapped evidence-capture systems
- Computer-vision and sensor-processing nodes

## Workloads to evaluate

The Edge Utility Record asks one question per device: **what does
this hardware demonstrably do?**

| Workload class | What we measure |
|---|---|
| Small language-model inference | tokens/sec on a tested model under a tested quantization |
| Vision-language models | per-image latency · supported resolution · context window |
| Object detection / visual inspection | FPS at target resolution · supported model |
| Document capture / preprocessing | pages-per-minute · OCR accuracy if measured |
| Local retrieval / embeddings | embeddings-per-second · vector DB compatibility |
| Robotics / automation | control-loop frequency · sensor I/O latency |
| Retail / local-business automation | uptime · workload-specific throughput |
| Security-camera / monitoring | streams-per-device · detection events |
| Local agent execution | concurrent agents · memory headroom |
| Data capture / evidence hashing | events/sec · SHA-256 throughput |

Medical / industrial edge inference is in scope ONLY with
appropriate regulatory caution and explicit operator-attested
disclosures · the platform never claims clinical or industrial
certification.

## Edge Value Dimensions

The Edge Utility Record evaluates each of these · `EVIDENCE_COMPLETE`
or `EVIDENCE_INCOMPLETE` per dimension:

| Dimension | Source |
|---|---|
| Hardware identity | manufacturer + model + serial (private) + SKU |
| RAM / VRAM / shared memory | spec sheet + system probe receipt |
| AI acceleration capability | TOPS at INT8 / INT4 from official spec · validated on-device benchmark when available |
| Power draw | nominal TDP · measured wattage when captured |
| Storage expandability | onboard + slot/SSD/microSD capacity · I/O class |
| Network connectivity | wired GbE / 10GbE / Wi-Fi standards · WAN/LAN topology fit |
| Camera / sensor / I/O compatibility | CSI lanes · USB · GPIO · M.2 · 40-pin · whatever applies |
| Local model compatibility | tested models with quantization + memory footprint |
| Operating system / runtime state | L4T version · JetPack · container/runtime ready |
| Privacy / offline deployment benefit | air-gap suitability · local-only inference path documented |
| Benchmark receipt | first-party JSON benchmark output with timestamp + SHA-256 |
| Deployment-readiness status | rack-ready · desk-ready · sensor-mount-ready · enclosure-needed |
| Recommended workload class | inferred from evidence above |
| Retain / redeploy / sell decision | operator decision after Defendable analysis |

## Trust rule · what makes an edge asset valuable

An edge device's value is NOT its resale price. Its value may come
from any of:

- Low power · sub-30W deployments enable always-on inference where
  a workstation cannot
- Local privacy · the data never leaves the device · doctrine-aligned
  with the Defendable evidence-vault model
- Small footprint · fits inside enclosures, mobile rigs, vehicles,
  pop-up retail
- Offline execution · zero cloud cost · zero round-trip latency
- Sensor integration · CSI camera, GPIO, USB-C industrial · classes
  of work a discrete GPU literally cannot perform
- Persistent deployment · 24/7 operation at low TCO
- Avoidance of cloud cost · $0/hr local inference vs paid API
- **Evidence capture close to the asset or operation being measured**
  · this is the Defendable doctrine alignment · edge devices ARE the
  evidence-capture layer in the platform's own architecture

## Claim discipline

Workload capability must be proven by **actual captured benchmark or
deployment evidence** before appearing as an issued claim on a
Defendable Edge Utility Record.

Allowed claim language:
- "Device of class X with manufacturer-published Y TOPS specification"
- "Tested locally · ran Llama-3.1-8B Q4_K_M at Z tokens/sec at T watts"
- "Deployed in a [described context] with operator-attested uptime"

Forbidden claim language:
- "Capable of running [larger model] in production" without a
  workload test receipt
- "Always-on revenue from edge inference" without uptime + revenue
  receipts
- "Edge-grade certified" · the platform issues no certification
- "Best-in-class" or "superior to [X]" without comparative receipts

## Defendable Edge Utility Record · structured output

```json
{
  "record_type": "DEFENDABLE_EDGE_UTILITY_RECORD",
  "asset_class": "COMPUTE_HARDWARE",
  "compute_tier": "E1",
  "device": {
    "manufacturer": "NVIDIA",
    "model": "Jetson Orin Nano Super 8GB",
    "ram_gb": 8,
    "ai_acceleration_tops": 67,
    "tdp_w": 15,
    "form_factor": "SOM_WITH_CARRIER"
  },
  "deployment_state": "ACTIVE_PRODUCTION",
  "workload_evidence": [
    {
      "workload": "Qwen-2.5 7B INT4",
      "tokens_per_sec": 16.7,
      "power_observed_w": 15.4,
      "captured_at": "2026-05-22T18:00:00Z",
      "evidence_status": "FIRST_PARTY_BENCHMARK_RECEIPT"
    }
  ],
  "value_dimensions_complete": [
    "hardware_identity", "ram_capacity", "ai_acceleration_capability",
    "power_draw", "operating_system_state", "workload_compatibility",
    "benchmark_receipt"
  ],
  "value_dimensions_incomplete": [
    "storage_expandability_audit", "network_topology_fit_audit"
  ],
  "recommendation": "RETAIN_AND_REDEPLOY",
  "recommendation_basis": "15W always-on operation produces measurable inference utility · resale value low but redeployment value high"
}
```

This is a forthcoming structured output · the schema is locked in
this doctrine doc · the implementation lands when the first Edge
Utility Record customer is onboarded.

## Related docs

- `COMPUTE_ASSET_TAXONOMY.md` · the E0 → E7 ladder this lane sits in
- `CPU_AND_SMALL_GPU_UTILITY_LANE.md` · sister lane for non-edge low-power compute
- `COMPUTE_UTILITY_SCORE_STANDARD.md` · workload-aware scoring framework
- `COMPUTE_BEACHHEAD_30_DAY_PLAN.md` · where the Edge Utility Record fits in the product ladder
