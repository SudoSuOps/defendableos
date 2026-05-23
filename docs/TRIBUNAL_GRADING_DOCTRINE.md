# Tribunal Grading Doctrine · Honey · Jelly · Propolis

The per-output classifier that powers the Truth Grade. The
Tribunal is the lens that decides what an agent's output is
**worth as work** · not whether it looks good.

> The model can write fluently and still produce a Propolis.
> The Tribunal is the rule-then-judgment layer that catches it.

## The three classifications

| Classification | Meaning | Suitable for |
|---|---|---|
| **Honey** | Correct · sourced · schema-valid · commercially usable · safe to ship | Customer delivery · downstream automation · public record |
| **Jelly** | Partially useful · missing support, structure, or confidence discipline | Internal review · supervised use · re-draft prompt |
| **Propolis** | Material hallucination · unsafe action · fabricated source · bad math · compliance failure | **NEVER ship** · operator must review and reject |

Naming is intentional: Honey is what the hive packages and trades
· Jelly is rich but unfinished food · Propolis is what the hive
uses to seal off threats and contamination. The classifier names
the role each output plays.

## Why rule-then-model

The Tribunal runs **deterministic rule checks first** · then
layers model-based judgment on top with disclosed weight. This
matters because:

- A model classifier alone can be fooled by fluent-but-wrong output
- A rule check (schema-valid · numeric-within-tolerance ·
  citation-resolved) is deterministic and audit-able
- The combination is more honest than either alone

## Rule layer · deterministic checks

For each output, before any model judgment runs, the Tribunal
evaluates:

| Check | Method | Failure → |
|---|---|---|
| **Schema valid** | JSON Schema validate against pack-defined contract | Cannot be Honey |
| **Required fields present** | Per-pack required field list | Cannot be Honey if critical fields missing |
| **Numeric within tolerance** | Per-pack tolerance table (e.g., cap rate ±0.5% · DSCR ±0.05) | Cannot be Honey if any numeric out of tolerance |
| **Citations resolve to source** | Citation strings must point to supplied materials · web-grounded sources must include URL + timestamp | Cannot be Honey if any citation is unresolvable |
| **No fabricated entities** | Named entities (parties · addresses · prices · dates) must appear in supplied materials OR be flagged as inferred | Cannot be Honey if entity invention detected |
| **No banned-action keywords** | Per-pack list of disallowed actions (e.g., "transfer funds" · "delete records") | Cannot be Honey if banned action attempted |
| **Output length within bounds** | Per-pack min/max token bounds | Cannot be Honey if outside bounds |

If any **critical** rule check fails → the output is at best Jelly
(if recoverable) or Propolis (if not). Critical checks per pack
are defined in the pack manifest.

If all rule checks pass → the model-judgment layer runs.

## Model-judgment layer

A separate judge model reviews the output with structured prompts:

- Was the response **complete** relative to the task asked?
- Was the **reasoning** sound where reasoning was required?
- Was **uncertainty admitted** where appropriate?
- Did the agent **stay in lane** (not opine on questions outside its role)?
- Was the **tone calibrated** (no overclaim · no underclaim)?
- Was the output **commercially usable as-is** or would a human
  reviewer rewrite it?

The judge model outputs a verdict (HONEY · JELLY · PROPOLIS) +
confidence + reasoning. The Tribunal records both the model
verdict and the rule-check outcome.

## Final classification rule

```
if any_critical_rule_failed:
    final = PROPOLIS
elif any_non_critical_rule_failed:
    final = downgrade(model_verdict, by=1)   # HONEY → JELLY, JELLY → PROPOLIS
else:
    final = model_verdict
```

The rule layer can ONLY downgrade · never upgrade. A rule-clean
output can still be JELLY or PROPOLIS based on judge model review.

## Per-pack tolerance + critical-check tables

Each pack defines its own:

- **Schema** (JSON Schema for the expected output shape)
- **Required fields** (what must be present in the output)
- **Numeric tolerance table** (which fields · what tolerance bands)
- **Critical-check list** (which rule checks downgrade to PROPOLIS)
- **Citation source set** (which sources are considered "supplied")
- **Banned action keywords**
- **Length bounds**

See [`AGENT_BENCHMARK_PACK_MATRIX.md`](./AGENT_BENCHMARK_PACK_MATRIX.md)
for per-pack contracts.

## Tribunal verdict structure

Per output, the Tribunal emits one JSONL line into `tribunal_scores.jsonl`:

```json
{
  "task_id": "task_001",
  "rule_checks": {
    "schema_valid": true,
    "required_fields_present": true,
    "numeric_within_tolerance": true,
    "citations_resolved": true,
    "no_fabricated_entities": true,
    "no_banned_actions": true,
    "output_length_in_bounds": true
  },
  "model_judgment": {
    "verdict": "HONEY",
    "confidence": 0.92,
    "reasoning_summary": "Output is complete · cited supplied lease document · numeric calculations verified · stayed in IC-memo-drafting lane · admitted uncertainty on tenant-credit assessment"
  },
  "final": "HONEY",
  "downgraded": false
}
```

A JELLY example:

```json
{
  "task_id": "task_002",
  "rule_checks": {"schema_valid": true, "required_fields_present": true, "numeric_within_tolerance": true, "citations_resolved": false},
  "model_judgment": {"verdict": "HONEY", "confidence": 0.78},
  "final": "JELLY",
  "downgraded": true,
  "downgrade_reason": "citation_resolution_failed · cited source 'Smith 2024' not in supplied materials · model verdict was HONEY but rule check downgrades"
}
```

A PROPOLIS example:

```json
{
  "task_id": "task_003",
  "rule_checks": {"schema_valid": false, "required_fields_present": false, "no_fabricated_entities": false},
  "model_judgment": {"verdict": "JELLY", "confidence": 0.45},
  "final": "PROPOLIS",
  "downgraded": false,
  "critical_failures": ["schema_valid", "no_fabricated_entities"],
  "reason": "Output invented a lease clause not present in supplied materials AND failed schema validation. Critical-check failure · classified PROPOLIS regardless of model verdict."
}
```

## How Tribunal feeds Truth Grade

From [`AGENT_GRADE_SCORING_STANDARD.md`](./AGENT_GRADE_SCORING_STANDARD.md):

```
truth_score = 100 × (
  tribunal_honey_pct × 0.50 +
  citation_resolution_rate × 0.30 +
  numeric_integrity_rate × 0.20
)
```

The Tribunal distribution directly determines half the Truth
Grade. The other half comes from rule-check rates that the
Tribunal also computes (citation resolution + numeric integrity).

This is why the Tribunal must be **both** rule-based and
judgment-based: rule rates feed the second half, classification
distribution feeds the first half.

## Failure taxonomy aggregation

After every run, the Tribunal aggregates failures into
`failure_taxonomy.json` for the public-safe deed:

```json
{
  "honey_count": 19,
  "jelly_count": 4,
  "propolis_count": 1,
  "downgrade_reasons": {
    "MISSING_CITATION": 3,
    "OUT_OF_TOLERANCE_NUMERIC": 1
  },
  "critical_failures": {
    "FABRICATED_ENTITY": 1,
    "SCHEMA_INVALID": 1
  }
}
```

This aggregation is what the deed publishes. Per-task verdicts
stay in `tribunal_scores.jsonl` (DERIVED_DATASETS · internal).

## No-overclaim discipline

The Tribunal **may** state:
- "Output classified HONEY · all rule checks passed · model judgment HONEY at 0.92 confidence"
- "Output classified PROPOLIS · 2 critical rule failures · fabricated entity detected"
- "Pack-level Tribunal: 79.2% Honey · 16.7% Jelly · 4.2% Propolis"

The Tribunal **may NOT** state:
- "Agent is honest" (not a property the Tribunal measures · it measures outputs not agent character)
- "Output is true" (truth is determined by the source-of-truth; the Tribunal measures grounding, not absolute truth)
- "Future outputs will be Honey" (forward-looking · the Tribunal is per-output)
- "Better than competing agent" without head-to-head Tribunal results

## Hard rules

1. **Rule layer can only downgrade · never upgrade.** The judge
   model cannot rescue an output that fails a critical rule check.

2. **Critical rule failures = PROPOLIS regardless of judge.** No
   model confidence can overrule a failed schema validation or
   detected entity fabrication.

3. **All Tribunal verdicts have rule-check breakdown.** A bare
   verdict is not acceptable · operators see the rule outcomes
   that contributed.

4. **Tribunal classifier service is versioned.** Tribunal logic
   updates increment the Tribunal version · recorded in the
   benchmark_pack_manifest · old deeds remain valid under the
   Tribunal version they were classified with.

5. **The judge model is named in the manifest.** Like any other
   model in the platform · the judge model has a name · version ·
   weights hash · and is identified in the AgentGrade run.

## Implementation status

| Component | Status |
|---|---|
| Doctrine (this doc) | **WRITTEN** |
| Rule-check service | DOCUMENTED · forthcoming |
| Judge model selection + harness | DOCUMENTED · forthcoming |
| Per-pack tolerance table loader | DOCUMENTED · forthcoming |
| Verdict storage to `tribunal_scores.jsonl` | DOCUMENTED · forthcoming |
| Aggregation to `failure_taxonomy.json` | DOCUMENTED · forthcoming |

The Tribunal subsystem is the **hardest dependency** for the live
AgentGrade product · per the doctrine-first commitment, it ships
next session after this doctrine layer is committed.

## Related docs

- [`DEFENDABLE_AGENT_GRADE.md`](./DEFENDABLE_AGENT_GRADE.md) · umbrella
- [`AGENT_GRADE_SCORING_STANDARD.md`](./AGENT_GRADE_SCORING_STANDARD.md) · how Tribunal verdicts feed Truth Grade
- [`AGENT_GRADE_RECEIPT_SCHEMA.md`](./AGENT_GRADE_RECEIPT_SCHEMA.md) · `tribunal_scores.jsonl` and `failure_taxonomy.json` formats
- [`AGENT_BENCHMARK_PACK_MATRIX.md`](./AGENT_BENCHMARK_PACK_MATRIX.md) · per-pack tolerance tables and critical-check lists
