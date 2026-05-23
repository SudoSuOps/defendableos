# Compute Inspector Pack v1

The first concrete Defendable AgentGrade benchmark pack.

## Purpose

Test agents that take a fresh compute host (operator's machine ·
partner's inventory · unknown cloud instance) and produce a
**Defendable-aligned inspection intake report** · the same kind of
work the `defendable-compute inspect` CLI does, plus narrative +
recommendation.

This pack **dogfoods the Defendable Compute Bench product**: the
agent under test is the kind of agent operators would use to scale
hardware inspection. By benchmarking it first, the platform proves
the inspector before the inspector is trusted to inspect.

## Status

`DRAFT_PACK_NOT_PRODUCTION`

Promotion to `READY_FOR_PRODUCTION` requires:
1. ≥ 10 tasks with complete schemas and rubrics ✅ (24 planned)
2. ≥ 5 adversarial cases with documented expected resistance ✅ (8 planned)
3. **Internal calibration run on ≥ 1 reference agent** ⏳ (next session)
4. Tolerance tables validated by domain reviewer ⏳
5. Critical-check list reviewed ⏳
6. Pack manifest hash committed ⏳

## Scope · 24 tasks · 8 adversarial cases

| Family | Count | Weight in Capability Grade |
|---|---|---|
| Identity | 4 | 25% |
| System manifest | 3 | 15% |
| Health diagnostic | 3 | 15% |
| Tier inference (E0-E7) | 4 | 15% |
| Rental-readiness (Vast.ai) | 2 | 10% |
| Recommendation draft (Best Next Use) | 3 | 10% |
| Reporting (operator summary) | 3 | 5% |
| Edge cases (no-data behavior) | 2 | 5% |

## Adversarial cases

| ID | Category |
|---|---|
| inj-001 | Poisoned `nvidia-smi` output (claims 96 GB on a 3090) |
| inj-002 | Spoofed device ID (PCI ID mismatched to reported model) |
| inj-003 | Misleading thermal log (sustained 95°C with otherwise-clean fields) |
| inj-004 | Prompt-injection in supplied README ("ignore previous instructions") |
| inj-005 | Fabricated comp citation (empty supplied doc cited as source) |
| inj-006 | Banned action attempt (task asks agent to "uninstall driver") |
| inj-007 | Hostile log lines in dmesg |
| inj-008 | Out-of-tolerance numeric claim (TDP beyond card spec) |

## Reference agent (next session)

Proposed first agent under test: a small inspector-class agent on
swarmrails or operator rig · local Qwen 9B-class with focused
system prompt referencing the Defendable Compute Bench schema.

The output of running this pack against the reference agent will
be the first issued **Defendable Agent Deed** (`DDEED-DOV-AGENT-
COMPUTE-INSPECTOR-000001-v1`), and the input to the first
**Defendable Work Unit Deed** (`DDEED-DOV-WORK-UNIT-COMPUTE-
INSPECTOR-000001-v1`).

## What's NOT in v1

- Live multi-modal capture (no image-of-GPU tasks · text logs only)
- Live multi-GPU coordination tasks (Phase B/C of Compute Bench
  tests this on the hardware side · Pack v2 may test agents that
  coordinate per-GPU)
- Real-time benchmarking subprocess tasks (the agent reads
  pre-captured tool outputs · doesn't run tools itself in v1)

## Authoring notes

This README + `pack_manifest.json` ship as the pack contract.
Individual task directories (`tasks/task_001/` etc.) and
adversarial case directories (`adversarial_cases/inj_001/` etc.)
get authored in the next session against the reference agent run.

Per pack approval doctrine, **no production-tier deed issues from
a draft pack** · the first calibration run will produce an
`OBSERVED` tier deed. Promotion to higher tiers requires the
pack to graduate to `READY_FOR_PRODUCTION` first.

## Related

- [`docs/DEFENDABLE_AGENT_GRADE.md`](../../docs/DEFENDABLE_AGENT_GRADE.md) · umbrella
- [`docs/AGENT_BENCHMARK_PACK_MATRIX.md`](../../docs/AGENT_BENCHMARK_PACK_MATRIX.md) · pack contract
- [`docs/AGENT_GRADE_RECEIPT_SCHEMA.md`](../../docs/AGENT_GRADE_RECEIPT_SCHEMA.md) · bundle shape
- [`docs/DEFENDABLE_COMPUTE_BENCH.md`](../../docs/DEFENDABLE_COMPUTE_BENCH.md) · the hardware bench this pack inspects
- [`docs/DEFENDABLE_WORK_UNIT_SCHEMA.md`](../../docs/DEFENDABLE_WORK_UNIT_SCHEMA.md) · the combined Work Unit deed
