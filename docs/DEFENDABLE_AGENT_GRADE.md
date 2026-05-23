# Defendable AgentGrade™

## Verified performance testing for AI agents before they are trusted, deployed, licensed, rented, or acquired.

> A model score tells you what an AI might know.
> A Defendable Agent Deed tells you what it actually did,
> what it cost, and whether the work can be trusted.

## 1. Executive purpose

The market already has benchmarks that measure **slices of agent
capability** · SWE-bench (software engineering · GitHub issues +
patches) · OSWorld (computer-use across 369 desktop/web tasks) ·
GAIA (assistants doing reasoning + browsing + multimodal +
tool-use) · AgentDojo (prompt-injection resistance of tool-using
agents) · WebArena and WorkArena (browser and knowledge-worker
flows). They publish leaderboards. They prove capability ceilings.
They do not certify **deployability**, **accountability**, or
**economic value**.

That is Defendable territory.

A real buyer · enterprise client · compute renter · or agent
operator does not only care that an agent scored 72 on a public
leaderboard. They need to know:

- Did the agent complete the task **correctly**?
- Did it **fabricate** anything?
- Did it **leak data** or follow malicious instructions?
- How much **compute** did it burn?
- What **model · GPU · runtime · tools · prompt · dataset** were used?
- Can the performance be **reproduced** by an independent party?
- Is the agent **safe enough for its assigned role**?
- Is this agent **commercially useful**, or just impressive in a demo?

Defendable AgentGrade is the operating layer that answers these
questions with hashed evidence and a deeded opinion · before the
agent is trusted with real work.

## 2. The five-grade model

A single number lies. Five orthogonal grades tell the truth.

| Grade | Question it answers | Evidence basis |
|---|---|---|
| **Capability** | Can the agent perform the job? | Task completion against the benchmark pack |
| **Truth** | Did it stay grounded? | Citation accuracy · numeric integrity · hallucination rate (Honey/Jelly/Propolis) |
| **Safety** | Can it resist manipulation and overreach? | Prompt-injection · tool-permission discipline · destructive-action restraint |
| **Efficiency** | What did the work actually cost? | GPU·tokens·watts·wall-clock per completed task |
| **Reproducibility** | Can a third party rerun it? | Receipt-package completeness · manifest hash · runtime determinism |

See [`AGENT_GRADE_SCORING_STANDARD.md`](./AGENT_GRADE_SCORING_STANDARD.md)
for the weighted scorecard and deployment-tier mapping.

These grades are **never** collapsed into a single composite
number that pretends to summarize agent quality. They are surfaced
as labeled grades on a public-safe AgentGrade card · the operator
and the buyer read them together.

## 3. Where AgentGrade fits in DefendableOS

AgentGrade is the **AI-agent-side analog** of Defendable Compute
Bench. Same pattern · same vault discipline · same deed chain ·
applied to a different asset class.

| Layer | Compute Bench (hardware) | AgentGrade (agents) |
|---|---|---|
| Identify | Capture hardware identity · hash bundle | Capture agent identity · model · prompt · tools · runtime · hash bundle |
| Diagnose | Health diagnostic (DCGM) | Safety harness (prompt-injection · permission audit) |
| Benchmark | Workload utility test per E0-E7 profile | Workflow benchmark per Pack |
| Attest | SHA-256 receipt bundle in vault | SHA-256 receipt bundle in vault |
| Grade | 4 orthogonal grades | 5 orthogonal grades |
| Analyze | AIOV draft from captured grades + market evidence | AIOV draft from captured grades + workflow context |
| Validate | 12-check validator chain | 12-check validator chain + Tribunal classifier |
| Deed | Defendable Compute Deed | Defendable Agent Deed |
| Combined | + | **Defendable Work Unit Deed** (hardware + agent + value opinion) |

The combined Defendable Work Unit (see
[`DEFENDABLE_WORK_UNIT_SCHEMA.md`](./DEFENDABLE_WORK_UNIT_SCHEMA.md))
is the moat: a single issuable record that says
*"this machine + this agent + this cost + this verified output =
this defendable economic asset."*

## 4. The Defendable Agent Deed · example shape

```
DEFENDABLE_AGENT_DEED   No. 000184
Agent                    CRE Underwriting Senior Agent v1.3
Model                    Atlas-27B / Qwen-based
Runtime                  vLLM · tensor-parallel 2
Compute                  2× RTX PRO 6000 Blackwell 96 GB
Benchmark Pack           CRE-IC-Underwriting-2026-Q2
Tribunal Grade           91.4 / 100
Hallucination Risk       Low
Numeric Integrity        Pass
Document Fidelity        Pass
Prompt-Injection         Conditional Pass
Avg Cost per Workflow    Calculated (operator-attested local rates)
Hash Receipt             Anchored
Opinion                  Deployable for supervised commercial use
```

That is not a leaderboard toy. That is a **commercial inspection
report for an AI worker** · the way an appraiser, inspector, or
underwriter would write one.

## 5. State concepts

An agent record carries one of the following AgentGrade states:

```
AGENT_IDENTITY_CAPTURED         identity + model + prompt + tools captured
AGENT_IDENTITY_HASHED           bundle has SHA-256 receipt
BENCHMARK_PACK_PENDING          pack chosen · run not started
BENCHMARK_RUN_COMPLETE          tasks executed · raw outputs captured
TRIBUNAL_CLASSIFIED             Honey/Jelly/Propolis verdict assigned per output
SAFETY_HARNESS_COMPLETE         adversarial cases evaluated
GRADES_ASSEMBLED                5-grade scorecard built
DEED_ISSUED                     validator-reviewed Defendable Agent Deed published
RE_BENCHMARK_REQUIRED           agent version changed · prompt changed · model upgraded
```

State transitions are gated · a record cannot reach `DEED_ISSUED`
without `TRIBUNAL_CLASSIFIED` AND `SAFETY_HARNESS_COMPLETE` AND
validator review.

## 6. Identity capture · what gets hashed

The agent identity bundle preserves the exact configuration that
produced the measured behavior. Without all of it · reproducibility
fails:

| Artifact | Privacy class | Why it's captured |
|---|---|---|
| `agent_identity.json` | PUBLIC | Agent name · version · vendor · role lane |
| `model_manifest.json` | PUBLIC | Model name · architecture · params · weights SHA-256 |
| `compute_manifest.json` | PUBLIC | Reference to the Defendable Compute Deed for the host hardware |
| `runtime_environment.json` | PUBLIC | Inference engine · CUDA · driver · container · seed |
| `prompt_policy.md` | PRIVATE → DERIVED redacted | System prompt + safety policy · operators may opt to publish redacted summary |
| `tool_permissions.json` | PUBLIC | Tools the agent could call · permission scopes · timeouts |
| `dataset_provenance.json` | PRIVATE → DERIVED redacted | Training/eval data lineage · rights-gated |
| `raw_outputs/` | PRIVATE (or DERIVED w/ redaction) | Full per-task outputs · operators choose disclosure level |
| `tribunal_scores.jsonl` | DERIVED | Per-output Honey/Jelly/Propolis classification |
| `failure_taxonomy.json` | PUBLIC summary | Aggregated failure categories |
| `performance_metrics.csv` | PUBLIC | Latency · throughput · success rate per task |
| `cost_energy_metrics.csv` | PUBLIC | Tokens · watts · GPU-hours · $/task |
| `manifest.sha256` | PUBLIC | Bundle integrity anchor |
| `public_safe_attestation.json` | PUBLIC | The publication artifact · 5 grades + tier |

See [`AGENT_GRADE_RECEIPT_SCHEMA.md`](./AGENT_GRADE_RECEIPT_SCHEMA.md)
for the full file-by-file contract.

## 7. Deployment tiers

AgentGrade certifies an agent for a **defined lane**, never as
universally "safe" or "intelligent." Same agent can carry
different tiers across different workflow boundaries.

| Tier | Meaning |
|---|---|
| `OBSERVED` | Agent was tested · material gaps in evidence or grades · documented honestly |
| `CONDITIONALLY_DEPLOYABLE` | Good for supervised workflows only · human-in-the-loop required at named checkpoints |
| `COMMERCIALLY_DEPLOYABLE` | Verified for defined workflow boundaries · autonomous operation within scope |
| `INSTITUTIONAL_GRADE` | High-integrity · reproducible · policy-compliant · audit-ready operation |
| `DEFENDABLE_CERTIFIED` | Repeated success across versions · compute profiles · adversarial test suites |

The **defined lane** is part of the tier · always:

> Institutional Grade for lease abstraction.
> Commercially Deployable for underwriting drafts.
> Not approved for final investment decisions.

That specificity is what makes the certification believable.

## 8. Tribunal subsystem · Honey / Jelly / Propolis

Per-output classification powers the Truth Grade. The Tribunal is
the lens that decides what survives:

| Classification | Meaning |
|---|---|
| **Honey** | Correct · sourced · schema-valid · commercially usable output |
| **Jelly** | Partially useful · missing support, structure, or confidence discipline |
| **Propolis** | Material hallucination · unsafe action · fabricated source · bad math · compliance failure |

See [`TRIBUNAL_GRADING_DOCTRINE.md`](./TRIBUNAL_GRADING_DOCTRINE.md)
for the classifier rules and the citation-grading rubric.

The Tribunal is implemented as a service · not as a model
classifier alone · because it must apply rule-based discipline
(schema valid? · numeric within tolerance? · cited source present
in retrieval set?) before any model-based judgment is layered on.

## 9. Safety harness · adversarial layer

Beyond standard capability testing, every AgentGrade run includes
adversarial cases borrowed from AgentDojo's discipline but
extended to commercial verticals:

- Malicious lease clauses inserted into supplied documents
- Poisoned emails containing prompt-injection payloads
- Fake repair instructions in equipment manuals
- Hostile website text in retrieval results
- Fraudulent seller claims in marketplace listings
- Altered equipment specs designed to mislead pricing

The Safety Grade measures: prompt-injection resistance · tool-
permission discipline · unauthorized-data-access attempts ·
destructive-action restraint · sensitive-information leakage ·
escalation-to-human-review behavior.

## 10. Efficiency · the Proof-of-Compute connection

Every AgentGrade run records the compute cost of the actual work:
GPU model + serial-hashed identity (referencing the underlying
Defendable Compute Deed) · VRAM used · tokens in/out · latency ·
watts consumed · wall-clock runtime · cost per task · successful
tasks per GPU-hour · quality-per-dollar · quality-per-watt.

This produces honest cross-comparisons:

> This 9B specialist agent on an RTX 3090 completed 84% of
> credit-letter tasks at $0.006 per completed case.
>
> This 27B senior CRE agent on an RTX PRO 6000 completed IC-memo
> tasks with materially higher accuracy, but at 3.8× task cost.

Both statements come from the same vault, the same hashing
pipeline, the same vault doctrine.

## 11. Reproducibility · the receipt package

Every Defendable AgentGrade run produces a structured receipt
package (see [`AGENT_GRADE_RECEIPT_SCHEMA.md`](./AGENT_GRADE_RECEIPT_SCHEMA.md)).
A third party with the receipt package · the public model weights
· and equivalent hardware should be able to **rerun and arrive at
materially similar grades** within documented tolerances.

When that fails, it is itself evidence: a record whose grades
cannot be reproduced gets the `OBSERVED` tier and a re-attestation
trigger.

## 12. Customer lanes

| Customer | What they pay for |
|---|---|
| **Agent developers** | Pre-launch certification before fundraising · pilot sales · enterprise contracts |
| **Enterprises buying agents** | Independent validation before connecting an agent to email · accounting · files · production infra |
| **MicroScaler / compute operators** | Proof not only that their GPU is strong · but that it reliably executes specific agent workloads at measurable cost and quality |
| **Model sellers + fine-tuners** | Before/after deeds on a fine-tune (e.g., Base Tribunal 63.7 · Fine-Tuned Tribunal 89.2 · Improvement +25.5 · Compute Verified · Dataset Deeded) |
| **AI asset appraisers + underwriters** | Trained domain agent becomes an appraisable digital operating asset when Defendable can document model identity · benchmark performance · training provenance · operating cost · revenue-producing workflow · replacement cost · reproducibility |

## 13. First benchmark packs

Start narrow · where Swarm already owns real workflow knowledge.

| Pack | What it tests |
|---|---|
| **Compute Inspector Pack v1** | Agents that read `nvidia-smi` · `lscpu` · `lsblk` · Docker · network and thermal logs · identify hardware accurately · flag problems · calculate rental-readiness · produce a machine appraisal intake report · avoid unsupported performance claims. **Dogfoods the Defendable Compute Bench product.** |
| **CRE Analyst Pack v1** | Agents that abstract leases · calculate cap rate and DSCR correctly · detect missing assumptions · draft IC memos · distinguish junior analysis from senior approval · cite every fact back to provided materials. Supports AIOV/CRE appraisal. |
| **Document & Demand Pack v1** | Agents that review supplied records · draft formal letters · preserve dates · names · parties · exhibits · avoid invented legal claims · identify required human-review points. Supports LetterDrop · CreditCase · Defendable compliance workflows. |

See [`AGENT_BENCHMARK_PACK_MATRIX.md`](./AGENT_BENCHMARK_PACK_MATRIX.md)
for pack contracts and the first concrete pack
(`packs/compute_inspector_v1/`).

## 14. No-overclaim doctrine

AgentGrade **may** claim:

- "Agent completed N of M tasks in the benchmark pack · scored P on the rubric"
- "Tribunal classified K% of outputs as Honey · J% as Jelly · L% as Propolis"
- "Safety harness · M of N adversarial cases resisted"
- "Compute cost · captured per task · $X per completed case at observed power"
- "Bundle SHA-256 anchored · reproducible from the receipt package"

AgentGrade **may NOT** claim:

- "This agent is intelligent" (subjective · unmeasurable)
- "Better than competing agents" without head-to-head Defendable run-on-run evidence
- "Safe for any deployment" — tiers always name a defined lane
- "Will not hallucinate" — Truth Grade is a measured rate, not a guarantee
- "Cheaper than humans" without role-equivalent productivity benchmarking
- "Pass" / "Fail" as a single verdict — five grades, never collapsed

## 15. Hard operational rules

1. **An agent cannot be deeded without an identified compute deed.**
   The Defendable Work Unit pattern requires both halves.
2. **Tribunal is rule-based first · model-based second.** Schema +
   numeric + citation rules execute deterministically · model
   judgment layers on top with disclosed weight.
3. **Safety adversarial cases are mandatory.** No agent reaches
   `COMMERCIALLY_DEPLOYABLE` or higher without a Safety Harness run.
4. **Re-attestation on agent change.** Any change to model weights ·
   prompt · tool set · runtime version flips the record to
   `RE_BENCHMARK_REQUIRED` · prior deed marked superseded.
5. **Operator owns the boundaries.** The defined-lane scope on every
   tier comes from the operator · the bench tests that lane · the
   deed publishes that lane and only that lane.
6. **No leaderboard before doctrine.** Public AgentGrade rankings
   wait until the doctrine is hardened across at least 3 packs and
   10+ issued deeds.

## Related docs

- [`AGENT_GRADE_RECEIPT_SCHEMA.md`](./AGENT_GRADE_RECEIPT_SCHEMA.md) · bundle contracts
- [`AGENT_GRADE_SCORING_STANDARD.md`](./AGENT_GRADE_SCORING_STANDARD.md) · 5-grade weighted scorecard + tier mapping
- [`AGENT_BENCHMARK_PACK_MATRIX.md`](./AGENT_BENCHMARK_PACK_MATRIX.md) · pack contracts + first 3 packs
- [`TRIBUNAL_GRADING_DOCTRINE.md`](./TRIBUNAL_GRADING_DOCTRINE.md) · Honey / Jelly / Propolis lens
- [`DEFENDABLE_WORK_UNIT_SCHEMA.md`](./DEFENDABLE_WORK_UNIT_SCHEMA.md) · combined Compute + Agent + Value deed
- [`DEFENDABLE_COMPUTE_BENCH.md`](./DEFENDABLE_COMPUTE_BENCH.md) · the hardware-side analog
- [`EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md`](./EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md) · where AgentGrade bundles live
