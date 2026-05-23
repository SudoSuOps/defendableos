# Defendable Work Unit Schema

The moat. A single issuable record that bundles a **Defendable
Compute Deed** + a **Defendable Agent Deed** + a **Value Opinion**
into one defendable economic asset.

> A GPU on a shelf is hardware.
> A model on a drive is weights.
> A Defendable Work Unit is a graded · benchmarked · costed ·
> deedable AI producing asset.

## 1. Why a Work Unit deed exists

Buyers · enterprises · operators · underwriters · insurers · and
acquirers don't buy GPUs or agents in isolation. They buy
**capacity to produce a verified outcome at a known cost**.

That outcome requires:

- **Hardware** that actually works (Compute Bench attested)
- **An agent** that actually completes the work (AgentGrade attested)
- **A cost basis** the operator can defend (energy + amortized
  compute + per-task observed cost)
- **A workflow boundary** the deed certifies for (defined lane)

Three separate records already exist:

- `DDEED-DOV-COMPUTE-...` · the Compute Bench deed (hardware)
- `DDEED-DOV-AGENT-...` · the AgentGrade deed (agent)
- `DDEED-DOV-COMPUTE-...-v3` · the Opinion of Value (asking price)

The Work Unit deed is the **fourth record that binds them
together** into one issuable asset record.

## 2. Naming

```
DDEED-DOV-WORK-UNIT-<asset_class>-<NNNNNN>-v<n>
```

Examples:

```
DDEED-DOV-WORK-UNIT-COMPUTE-AGENT-000001-v1
DDEED-DOV-WORK-UNIT-CRE-ANALYST-000001-v1
DDEED-DOV-WORK-UNIT-LEGALSNIPER-DRAFT-000001-v1
```

ENS pattern:

```
ddeed-dov-work-unit-compute-agent-000001-v1.swarmbee.defendable.eth
```

## 3. The three required components

Every Work Unit deed references **all three** of:

| Component | Source | Required field |
|---|---|---|
| **Physical Compute Deed** | Compute Bench | `compute_deed_reference` |
| **Agent Performance Deed** | AgentGrade | `agent_deed_reference` |
| **Economic Opinion of Value** | AIOV / OPERATOR_ASK_PRICE | `value_deed_reference` |

If any one is missing the Work Unit is `INCOMPLETE` and cannot
be issued.

## 4. Bundle layout

```
work_units/
└── <work_unit_id>/
    ├── work_unit_identity.json
    ├── physical_compute_deed_ref.json
    ├── agent_performance_deed_ref.json
    ├── economic_opinion_ref.json
    ├── defined_lane.json
    ├── unit_economics.json
    ├── workload_capacity.json
    ├── validator_review.json
    ├── manifest.sha256
    └── public_safe_attestation.json
```

`<work_unit_id>` format: `wu-<yyyymmddTHHMMSSZ>-<short_random>`.

## 5. File-by-file contract

### `work_unit_identity.json` · PUBLIC

```json
{
  "work_unit_id": "wu-20260524T120000Z-7c2a",
  "work_unit_class": "COMPUTE_AGENT_PRODUCING_UNIT",
  "name": "SwarmRails E6 · Atlas-27B CRE Analyst Producing Unit",
  "vendor": "swarm-and-bee",
  "issued_at": null,
  "captured_at": "2026-05-24T12:00:00Z"
}
```

### `physical_compute_deed_ref.json` · PUBLIC

```json
{
  "deed_reference": "DDEED-DOV-COMPUTE-000001-BENCH-v2",
  "deed_record_hash": "sha256:7769d094a2e1d8b860e50486fcaf28b7f79f63d9efaaa6cace6708b912070e11",
  "asset_tier": "E6",
  "model": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
  "grades": {
    "identity": "C · MODEL_SELF_REPORTED_ONLY",
    "health": "PASS (DCGM Level 1 · 1/1 categories)",
    "utility": "UTILITY_NOT_YET_MEASURED",
    "evidence": "B · FIRST_PARTY_OPERATIONAL_EVIDENCE_ONLY"
  }
}
```

### `agent_performance_deed_ref.json` · PUBLIC

```json
{
  "deed_reference": "DDEED-DOV-AGENT-CRE-ANALYST-000001-v1",
  "deed_record_hash": "sha256:...",
  "agent_id": "agent-cre-underwriting-senior-v1.3",
  "benchmark_pack": "cre-analyst-v1",
  "grades": {
    "capability": 92,
    "truth": 95,
    "safety": 86,
    "numeric_structural": 98,
    "efficiency": 82,
    "reproducibility": 100,
    "agentgrade_composite": 91.4
  },
  "deployment_tier": "COMMERCIALLY_DEPLOYABLE",
  "deployment_lane": "CRE_IC_MEMO_DRAFTING · supervised commercial use"
}
```

### `economic_opinion_ref.json` · PUBLIC

```json
{
  "deed_reference": "DDEED-DOV-COMPUTE-000001-v3",
  "value_class": "OPERATOR_ASK_PRICE",
  "value_usd": 9850,
  "value_currency": "USD",
  "doctrine_note": "Operator-stated asking price · operator claim · not validator-issued conclusion or confirmed-sale comparable"
}
```

### `defined_lane.json` · PUBLIC

```json
{
  "lane_id": "CRE_IC_MEMO_DRAFTING",
  "lane_description": "Drafting investment committee memos · cap rate calc · DSCR check · missing-assumption flagging · explicit human-review checkpoint for final IC approval",
  "approved_workflow_boundaries": [
    "draft IC memos for review",
    "abstract lease terms",
    "calculate cap rate and DSCR with citation"
  ],
  "explicitly_NOT_approved_for": [
    "final IC approval without human review",
    "wire transfer authorization",
    "binding offer issuance"
  ]
}
```

### `unit_economics.json` · PUBLIC

Cost basis the operator publishes for the Work Unit's productive
output:

```json
{
  "kwh_rate_assumption_usd": 0.13,
  "avg_total_cost_per_task_usd": 0.058,
  "avg_gpu_seconds_per_task": 4.8,
  "avg_power_w": 295,
  "throughput_tasks_per_gpu_hour": 12.3,
  "amortization_notes": "Compute amortized over 36-month operator-stated useful life. Energy from operator-stated local rate. Independent verification recommended for institutional buyers.",
  "captured_at": "2026-05-24T12:00:00Z"
}
```

### `workload_capacity.json` · PUBLIC

What the Work Unit can produce per period · capacity not yield:

```json
{
  "demonstrated_workloads": [
    {
      "name": "CRE IC memo draft",
      "tasks_per_gpu_hour": 12.3,
      "tasks_per_day_at_24h": 295.2,
      "tasks_per_day_at_8h_operator_use": 98.4,
      "evidence_basis": "BENCH-v2 + AGENT-v1 measured"
    }
  ],
  "limitations": [
    "Capacity is theoretical at observed throughput · operator pause windows reduce realized capacity",
    "Capacity does NOT equal customer demand · no buyer guaranteed",
    "Capacity does NOT equal revenue · no $/task price represented · per-task cost is captured separately"
  ]
}
```

### `validator_review.json` · DERIVED

```json
{
  "protocol": "VALIDATE_THE_VALIDATOR",
  "status": "VALIDATOR_REVIEW_REQUIRED",
  "compute_deed_validator_status": "READY_FOR_REVIEW",
  "agent_deed_validator_status": "READY_FOR_REVIEW",
  "work_unit_specific_checks": [
    {"id": "WU-1", "name": "compute_deed_resolves", "status": "PENDING"},
    {"id": "WU-2", "name": "agent_deed_resolves", "status": "PENDING"},
    {"id": "WU-3", "name": "agent_compute_deed_matches_host", "status": "PENDING"},
    {"id": "WU-4", "name": "defined_lane_present_and_specific", "status": "PENDING"},
    {"id": "WU-5", "name": "unit_economics_source_disclosed", "status": "PENDING"},
    {"id": "WU-6", "name": "capacity_not_represented_as_yield", "status": "PENDING"}
  ]
}
```

### `manifest.sha256` · PUBLIC

Sorted-key JSON of per-file hashes · bundle hash anchors the
Work Unit · same exclusion rules as Compute Bench / AgentGrade.

### `public_safe_attestation.json` · PUBLIC

```json
{
  "work_unit_id": "wu-20260524T120000Z-7c2a",
  "work_unit_class": "COMPUTE_AGENT_PRODUCING_UNIT",
  "name": "SwarmRails E6 · Atlas-27B CRE Analyst Producing Unit",
  "captured_at": "2026-05-24T12:00:00Z",
  "captured_by": "swarm-and-bee",
  "compute_deed": "DDEED-DOV-COMPUTE-000001-BENCH-v2",
  "agent_deed": "DDEED-DOV-AGENT-CRE-ANALYST-000001-v1",
  "value_deed": "DDEED-DOV-COMPUTE-000001-v3",
  "compute_summary": {
    "tier": "E6",
    "model": "RTX PRO 6000 Blackwell · 96 GB",
    "health_grade": "PASS",
    "evidence_grade": "B"
  },
  "agent_summary": {
    "agent_id": "agent-cre-underwriting-senior-v1.3",
    "agentgrade_composite": 91.4,
    "deployment_tier": "COMMERCIALLY_DEPLOYABLE",
    "deployment_lane": "CRE_IC_MEMO_DRAFTING · supervised commercial use"
  },
  "economic_summary": {
    "operator_ask_usd": 9850,
    "avg_total_cost_per_task_usd": 0.058,
    "throughput_tasks_per_gpu_hour": 12.3
  },
  "defined_lane": "CRE_IC_MEMO_DRAFTING · supervised commercial use · final IC approval requires human review",
  "manifest_hash": "sha256:...",
  "bundle_hash": "sha256:...",
  "limitations": [
    "Capacity is theoretical · not a buyer guarantee of throughput",
    "Cost amortization uses operator-attested kWh + useful-life · independent verification recommended",
    "Per-task price NOT represented · cost basis ≠ pricing"
  ],
  "re_attestation_trigger": "COMPUTE_DEED_SUPERSEDED · AGENT_DEED_SUPERSEDED · OWNERSHIP_TRANSFER · DEFINED_LANE_CHANGE"
}
```

## 6. Work Unit specific validator checks

In addition to the standard 12-check validator chain, a Work Unit
deed runs:

| ID | Check | Failure → |
|---|---|---|
| WU-1 | `compute_deed_resolves` | Cannot issue · referenced Compute Deed must exist + be ISSUED |
| WU-2 | `agent_deed_resolves` | Cannot issue · referenced Agent Deed must exist + be ISSUED |
| WU-3 | `agent_compute_deed_matches_host` | Agent's `compute_manifest.compute_deed_reference` must match the Work Unit's `compute_deed_reference` |
| WU-4 | `defined_lane_present_and_specific` | Lane must include both `approved_workflow_boundaries` AND `explicitly_NOT_approved_for` lists |
| WU-5 | `unit_economics_source_disclosed` | kWh rate · amortization period · operator-attested fields must be named |
| WU-6 | `capacity_not_represented_as_yield` | `workload_capacity.json` must contain the limitations list explicitly stating capacity ≠ demand ≠ revenue |

## 7. Re-attestation triggers

A Work Unit deed flips to `RE_ATTESTATION_REQUIRED` on any of:

- Compute Deed superseded (Compute Bench re-run)
- Agent Deed superseded (AgentGrade re-run · agent version change)
- Defined lane change (boundary expanded or narrowed)
- Ownership transfer (buyer-side re-attestation required)
- kWh rate change > ±20% (amortization basis changes the unit economics)
- Major workflow change (the kind of work the unit is producing changes)

## 8. No-overclaim doctrine

A Work Unit deed **may** state:
- "Compute deed X + Agent deed Y compose this Work Unit"
- "Composite throughput observed at N tasks/GPU-hour · at observed power"
- "Cost per task at operator-stated kWh = $Z · independently verifiable from receipts"
- "Approved for defined lane L · explicitly not approved for actions M, N"

A Work Unit deed **may NOT** state:
- "Guaranteed revenue per month" · capacity ≠ demand
- "Independent of operator" · the Work Unit is operator-attested
- "Resale price $X for the bundle" · resale of a Work Unit requires comp evidence the platform doesn't yet have
- "Equivalent to N human workers" · productivity comparisons need role-equivalence benchmarking not in scope

## 9. Customer lanes for the Work Unit deed

| Customer | Why they want a Work Unit deed |
|---|---|
| Enterprise procurement | Lets them buy "AI capacity for X workflow at $Y/task on this hardware" instead of buying GPUs + integrating agents separately |
| MicroScaler operators | Sells producing capacity, not just GPU-hours · differentiated against commodity rental |
| AI asset acquirers | Acquires a verified producing asset with grades + lane + cost basis · not just weights and a card |
| Insurers / underwriters | Has a defined-lane scope they can underwrite against · not vague "AI agent" risk |
| Lenders | Has a depreciable producing asset with documented cost basis + capacity |

## 10. Implementation status

| Component | Status |
|---|---|
| Doctrine (this doc) | **WRITTEN** |
| Schema for Work Unit deed JSON | DOCUMENTED |
| Work-Unit-specific validator checks (WU-1..WU-6) | DOCUMENTED · service-side implementation forthcoming |
| First issuable Work Unit deed | PROPOSED · awaits first AgentGrade deed |

The first issuable Work Unit deed will be:

```
DDEED-DOV-WORK-UNIT-COMPUTE-INSPECTOR-000001-v1
```

Bundling:
- `DDEED-DOV-COMPUTE-000001-BENCH-v2` (the swarmrails Phase B deed)
- `DDEED-DOV-AGENT-COMPUTE-INSPECTOR-000001-v1` (the forthcoming first AgentGrade deed against the Compute Inspector Pack v1)
- `DDEED-DOV-COMPUTE-000001-v3` (the $9,850 OPERATOR_ASK flagship)

That bundle becomes the first **producing-unit deed** in the
platform · the model for every Work Unit that follows.

## Related docs

- [`DEFENDABLE_AGENT_GRADE.md`](./DEFENDABLE_AGENT_GRADE.md) · the agent side
- [`AGENT_GRADE_RECEIPT_SCHEMA.md`](./AGENT_GRADE_RECEIPT_SCHEMA.md) · agent bundle
- [`DEFENDABLE_COMPUTE_BENCH.md`](./DEFENDABLE_COMPUTE_BENCH.md) · the compute side
- [`COMPUTE_BENCH_RECEIPT_SCHEMA.md`](./COMPUTE_BENCH_RECEIPT_SCHEMA.md) · compute bundle
- [`EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md`](./EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md) · where bundles live
- [`BEST_NEXT_USE_DECISION_SCHEMA.md`](./BEST_NEXT_USE_DECISION_SCHEMA.md) · adjacent · the decision record per asset
