# Compute Bench Profile Matrix

Per-tier benchmark profiles. One universal benchmark would lie
about hardware doing unlike work. Each profile names: required
evidence · optional evidence · safe test duration · disruption
considerations · unsupported claim boundaries · public-safe
outputs.

## E0 · CPU / Orchestration Node

**Examples:** ZimaBoard · OPNsense box · NAS-class hardware ·
mini-PC · Apple Silicon · Raspberry Pi-class SBC.

### Test categories

- CPU identity (model · cores · threads · frequency state)
- RAM capacity + speed (health observations where accessible)
- Storage throughput + SMART health (`fio` if installed · safe seq reads only by default)
- Networking link status + throughput (where safely measurable · `iperf3` only with operator opt-in)
- Container runtime readiness (docker · podman · k3s)
- Evidence-hashing throughput (Defendable doctrine fit · MB/s SHA-256)
- API/service readiness (curl the local API · check ports listening)
- Embeddings/retrieval task ONLY where installed and testable

### Required evidence
- `asset_identity.json` · CPU + RAM + storage + network captured
- `runtime_environment.json` · OS · kernel · container runtime
- `health_diagnostic.json` · uptime · load average · thermal if available

### Safe test duration
`quick` 30s · `standard` 5min · `extended` 30min

### Unsupported claim boundary
**Do NOT claim GPU inference utility.** E0 nodes carry orchestration
and evidence value · not accelerator value.

### Public-safe outputs
Identity Grade + Health Grade + `UTILITY: ORCHESTRATION_OR_EVIDENCE_NODE`

---

## E1 · Edge AI Device

**Examples:** Jetson Orin Nano 4/8 GB · Jetson Orin NX 8/16 GB ·
Coral TPU · low-power NPU SoMs.

### Test categories

- Module/device identity (`tegrastats` · `jtop` · vendor SDK)
- RAM / shared memory profile
- Power mode (5W · 7W · 15W · MAXN where applicable)
- Storage + network state
- Runtime availability (L4T · JetPack · vendor SDK version)
- Local vision OR small-LLM task where SAFE and PRESENT
- Task latency + throughput
- Thermal + power observation per power mode
- Offline / local deployment readiness

### Required evidence
- `asset_identity.json` · module + SoC + RAM
- `runtime_environment.json` · L4T/JetPack/SDK version
- `health_diagnostic.json` · power mode · thermal envelope
- At least one workload test if SDK present

### Safe test duration
`quick` 60s · `standard` 5min · `extended` 30min

### Unsupported claim boundary
Do NOT compare an edge accelerator to a workstation GPU's workload.
The Utility Grade is `E1_EDGE_VISION_UTILITY_MEASURED` ·
**not** any E4+ grade.

---

## E2 · Entry Local GPU

**Examples:** RTX 3050 · 3060 · 4060 · A2000 · workstation cards
4-8 GB · SFF/USFF boxes with discrete GPU.

### Test categories

- GPU identity · VRAM verification
- Driver / runtime version
- Health + stability check (short)
- Memory constraint profile (largest model that fits)
- Small-model or 512-768px image-gen workload
- Thermal + power observation
- Honest workload ceiling documentation

### Safe test duration
`quick` 60s · `standard` 5min · `extended` 15min

### Unsupported claim boundary
Do NOT issue claims about workloads requiring more VRAM than the
card has. Document the ceiling explicitly.

---

## E3 · Efficient Inference GPU

**Examples:** RTX 3060 12 GB · 4070 · A4000 · low-profile
workstation cards.

### Test categories

- Low-profile / form-factor confirmation (where captured)
- Power-capped sustained inference
- Performance-per-watt
- Thermal stability
- Always-on workload suitability (steady-state behavior over time)
- Deployment fit (rack-mount · desk · vehicle · pop-up retail)

### Safe test duration
`quick` 90s · `standard` 10min · `extended` 1h

### Unsupported claim boundary
"Always-on" claims require sustained-test evidence at the operator's
intended power cap · not nominal TDP.

---

## E4 · Workhorse Local / Rental GPU

**Priority proof case:** RTX 3090 / 3090 Ti 24 GB · **Workhorse
Utilization Record**. Founder owns this class · evidence depth is
highest from day 1.

**Examples:** RTX 3090 · 3090 Ti · 4090 · 5090 · RTX A5000.

### Test categories

- Identity + 24/32 GB VRAM verification
- System / runtime capture
- Sustained health + stability
- Local AI workload utility (13B–30B inference at Q4-Q6)
- Thermal + power evidence at full and capped TDP
- **Vast.ai rental-readiness evidence** (driver + runtime + container
  + network checks per Vast.ai host requirements · NOT actual rental)
- Actual founder rental receipts ONLY where supplied (never auto-fetched)
- Hold/rent/sell/redeploy analysis inputs

### Required evidence
- All E2/E3 fields
- 13B-class inference test (default · scales to 30B if RAM allows)
- Sustained-power trace for at least 90s under workload
- Vast.ai host-readiness checklist output

### Safe test duration
`quick` 2min · `standard` 15min · `extended` 1h

### Unsupported claim boundary
- Vast.ai listing snapshot is OBSERVATION ONLY · not rental yield
- Founder rental receipt is FIRST_PARTY_RENTAL_RECEIPT · individual
  to that asset · not generalizable to "RTX 3090s earn $X/hr"

---

## E5 · Modern Builder / Professional GPU

**Priority proof cases:**
- RTX 5090 · *Smash Fleet*
- RTX PRO 6000 Blackwell · *SwarmRails* (E6-eligible · placed at E5
  for some configurations · see note)

**Examples:** RTX 4500 Blackwell · 5090 · A6000 · A6000 Ada.

### Test categories

- Identity + configuration (per-card · within multi-GPU rig)
- Heavy local AI utility (30B-class inference · LoRA fine-tune)
- Sustained thermal + power behavior
- Rental readiness (where applicable)
- Performance context (FP16 · FP8 · INT8 throughput)
- Condition evidence (chassis · cooling · cable management)
- Market observation inputs (eBay Browse · Vast.ai · sold comps where available)

### Safe test duration
`quick` 3min · `standard` 20min · `extended` 2h

---

## E6 · Institutional Accelerator

**Priority proof case:** RTX PRO 6000 Blackwell · **SwarmRails**
(founder-owned · DDEED-DOV-COMPUTE-000001 live)

**Examples:** RTX PRO 6000 Blackwell (96 GB) · 2-4 GPU WRX90
ThreadRipper PRO or Xeon Sapphire Rapids rigs · institutional AI
infrastructure.

### Test categories

- Enhanced health diagnostics (`dcgmi diag -r 2` when available)
- Error / ECC monitoring (where supported)
- Sustained load testing (longer windows · larger workloads)
- Memory + interconnect observations (PCIe Gen + width)
- Workload throughput (70B inference Q4 · training-capable proof)
- Deployment / diligence reporting
- Heightened private/public control (operator may opt to keep more
  in PRIVATE vault by default)

### Required evidence
- All E5 fields
- ECC status snapshot
- PCIe link state
- 70B inference test (or operator-chosen equivalent)
- Sustained-power trace at full TDP for at least 5min

### Safe test duration
`quick` 5min · `standard` 30min · `extended` 4h

### **SwarmRails-specific safety profile**

The founder-approved swarmrails rig has 2× RTX PRO 6000 Blackwell.
GPU 0 (PCI 00000000:34:00.0) is the **only target** for bench.
GPU 1 (PCI 00000000:CA:00.0) hosts the production Qwen3.5 serving
loop and **must never be touched** by the bench.

The CLI enforces:

- `--gpu` defaults to `0` on swarmrails-class targets
- A pre-flight check uses `nvidia-smi --query-compute-apps=pid,used_memory --format=csv` to detect occupied GPUs
- Any GPU with an active process raises `BenchSafetyError` unless `--force-occupied-gpu` is passed *and* the operator types the GPU's PCI Bus ID as confirmation
- The CLI prints the occupied-GPU process list before refusing

Driver/runtime baseline: `590.48.01` · CUDA `13.1` · ECC: `Off`
(consumer/workstation profile · not datacenter ECC).

---

## E7 · Complete Producing Node / Fleet

**Priority proof case:** Complete GPU server / node (E7 record ·
multi-GPU + storage + network + chassis treated as one asset)

### Test categories

- Component inventory (every GPU · every disk · every NIC · PSU)
- GPU + CPU + RAM + storage + network captured as one bundle
- Docker / runtime / container readiness
- Disk throughput (per-device sequential + random)
- Network throughput (per-NIC link state + speed)
- Thermals + power (chassis-level · not just per-card)
- Multi-GPU behavior where relevant (NVLink · PCIe topology)
- Workload deployment readiness (does the orchestrator come up?)
- **Complete-node versus part-out versus rental-deployment analysis**

### Safe test duration
`quick` 10min · `standard` 1h · `extended` 6h+

### Public-safe output is the **node-level deed**
Per-component grades roll up to a node-level Identity · Health ·
Utility · Evidence summary. Buyer-side re-attestation is more
involved · documented in deed.

---

## Per-profile schema fields

Every profile output respects the contract in
[`COMPUTE_BENCH_RECEIPT_SCHEMA.md`](./COMPUTE_BENCH_RECEIPT_SCHEMA.md):

- `required_evidence` (list) · what the bundle MUST contain
- `optional_evidence` (list) · what's nice-to-have
- `safe_test_duration_seconds` (map) · per scope
- `disruption_considerations` (string) · operator-readable
- `unsupported_claim_boundaries` (list) · what NOT to publish
- `public_safe_output_template` (string) · the redacted shape

## Founder proof-case priority

| Order | Asset | Tier | Status |
|---|---|---|---|
| **1** | **RTX PRO 6000 Blackwell · SwarmRails GPU 0** | E6 | **FOUNDER-APPROVED · awaits MVP CLI deployment** |
| 2 | RTX 3090 / 3090 Ti 24GB · Workhorse | E4 | Founder-owned · proof case pending |
| 3 | RTX 5090 · Smash Fleet | E5 | Founder-owned (8 units per memory) · proof case pending |
| 4 | Jetson Orin Nano-class · sigedge | E1 | Founder-attested · benchmark + uptime captured |
| 5 | Zima-class CPU Node · evidence/orchestration | E0 | Founder-attested · production role |
| 6 | Complete GPU Server / Node | E7 | PROPOSED_PROOF_CASE · awaits first institutional intake |

## Related docs

- [`DEFENDABLE_COMPUTE_BENCH.md`](./DEFENDABLE_COMPUTE_BENCH.md) · umbrella product
- [`COMPUTE_BENCH_RECEIPT_SCHEMA.md`](./COMPUTE_BENCH_RECEIPT_SCHEMA.md) · receipt structure
- [`COMPUTE_ATTESTATION_GRADING_STANDARD.md`](./COMPUTE_ATTESTATION_GRADING_STANDARD.md) · 4-grade output
- [`DEFENDABLE_COMPUTE_BENCH_CLI_SPEC.md`](./DEFENDABLE_COMPUTE_BENCH_CLI_SPEC.md) · CLI surface
- [`COMPUTE_BENCH_TOOLING_AUDIT.md`](./COMPUTE_BENCH_TOOLING_AUDIT.md) · per-tool evaluation
- [`COMPUTE_ASSET_TAXONOMY.md`](./COMPUTE_ASSET_TAXONOMY.md) · the E0-E7 ladder
