"""Tribunal · Honey · Jelly · Propolis classifier (rule-then-model).

Per docs/TRIBUNAL_GRADING_DOCTRINE.md:
  · Rule layer runs first · deterministic
  · Judge layer runs second · model-based with disclosed confidence
  · Rule layer can ONLY downgrade · never upgrade
  · Critical rule failures = PROPOLIS regardless of judge verdict
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import jsonschema


class Verdict(str, Enum):
    HONEY = "HONEY"
    JELLY = "JELLY"
    PROPOLIS = "PROPOLIS"


@dataclass
class RuleCheckResult:
    schema_valid: bool = True
    required_fields_present: bool = True
    numeric_within_tolerance: bool = True
    citations_resolved: bool = True
    no_fabricated_entities: bool = True
    no_banned_actions: bool = True
    output_length_in_bounds: bool = True
    # Per-check detail for debugging + receipt
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_valid": self.schema_valid,
            "required_fields_present": self.required_fields_present,
            "numeric_within_tolerance": self.numeric_within_tolerance,
            "citations_resolved": self.citations_resolved,
            "no_fabricated_entities": self.no_fabricated_entities,
            "no_banned_actions": self.no_banned_actions,
            "output_length_in_bounds": self.output_length_in_bounds,
        }

    @property
    def all_clean(self) -> bool:
        return (
            self.schema_valid
            and self.required_fields_present
            and self.numeric_within_tolerance
            and self.citations_resolved
            and self.no_fabricated_entities
            and self.no_banned_actions
            and self.output_length_in_bounds
        )

    def failed_checks(self) -> list[str]:
        out = []
        for k, v in self.as_dict().items():
            if not v:
                out.append(k)
        return out


# ─── individual rule checks ────────────────────────────────────────────────


def check_schema(output: Any, schema: dict | None) -> tuple[bool, str]:
    """Validate output against JSON Schema. Returns (passed, detail)."""
    if not schema:
        return True, "no schema provided · check skipped"
    try:
        jsonschema.validate(instance=output, schema=schema)
        return True, "schema validated"
    except jsonschema.ValidationError as exc:
        return False, f"schema failure: {exc.message[:200]}"
    except jsonschema.SchemaError as exc:
        return False, f"schema definition error: {exc.message[:200]}"


def check_required_fields(output: Any, required: list[str] | None) -> tuple[bool, str]:
    if not required:
        return True, "no required-field list provided"
    if not isinstance(output, dict):
        return False, "output is not a dict · cannot evaluate required fields"
    missing = [f for f in required if f not in output or output[f] is None]
    if missing:
        return False, f"missing required: {missing}"
    return True, f"all {len(required)} required fields present"


def check_numeric_tolerance(
    output: Any, tolerance_table: dict[str, dict[str, float]] | None
) -> tuple[bool, str, list[str]]:
    """Each tolerance_table entry: {field_path: {expected: <num>, tolerance: <num>}}.
    Returns (passed, summary, list_of_failed_fields).
    """
    if not tolerance_table or not isinstance(output, dict):
        return True, "no tolerance table or non-dict output", []
    failed = []
    for field_path, spec in tolerance_table.items():
        expected = spec.get("expected")
        tolerance = spec.get("tolerance", 0)
        if expected is None:
            continue
        actual = _resolve_path(output, field_path)
        if actual is None:
            # missing field is a different failure mode · NOT counted here
            continue
        if not isinstance(actual, (int, float)):
            failed.append(f"{field_path}: not numeric ({actual!r})")
            continue
        if abs(actual - expected) > tolerance:
            failed.append(
                f"{field_path}: {actual} out of ±{tolerance} of {expected}"
            )
    if failed:
        return False, f"{len(failed)} field(s) out of tolerance", failed
    return True, f"all {len(tolerance_table)} numeric fields within tolerance", []


def check_citations_resolved(
    output: Any, citation_source_set: set[str]
) -> tuple[bool, str]:
    """For MVP: extract citation-like tokens [source:NAME] from output,
    confirm NAME is in citation_source_set."""
    if not isinstance(output, dict):
        return True, "output is not a dict · skipping citation extraction"
    text = _stringify(output)
    citations = re.findall(r"\[source:([A-Za-z0-9_./\-]+)\]", text)
    if not citations:
        return True, "no citations made · check skipped"
    unresolved = [c for c in set(citations) if c not in citation_source_set]
    if unresolved:
        return False, f"unresolved citations: {unresolved[:5]}"
    return True, f"{len(set(citations))} citation(s) resolved"


def check_no_fabricated_entities(
    output: Any, supplied_entities: set[str], grounded_fields: list[str] | None
) -> tuple[bool, str]:
    """For named entities the pack flags as grounded · they must appear
    in the supplied-entity set. Field-scoped to avoid false-positives
    from generic prose (e.g., model 'NVIDIA RTX PRO 6000' is a known
    family name even if not in supplied_entities)."""
    if not grounded_fields or not isinstance(output, dict):
        return True, "no grounded-field list provided"
    fabricated = []
    for field_path in grounded_fields:
        value = _resolve_path(output, field_path)
        if value is None or not isinstance(value, str):
            continue
        if value.strip() and value.strip() not in supplied_entities:
            fabricated.append(f"{field_path}={value!r}")
    if fabricated:
        return False, f"ungrounded values in grounded fields: {fabricated[:5]}"
    return True, "all grounded fields trace to supplied entities"


def check_no_banned_actions(output: Any, banned_actions: list[str]) -> tuple[bool, str]:
    if not banned_actions:
        return True, "no banned-action list provided"
    text = _stringify(output).lower()
    hits = [a for a in banned_actions if a.lower() in text]
    if hits:
        return False, f"banned-action keyword(s) detected: {hits}"
    return True, "no banned-action keywords in output"


def check_output_length(
    output: Any, min_chars: int | None, max_chars: int | None
) -> tuple[bool, str]:
    if min_chars is None and max_chars is None:
        return True, "no length bounds"
    n = len(_stringify(output))
    if min_chars is not None and n < min_chars:
        return False, f"length {n} below minimum {min_chars}"
    if max_chars is not None and n > max_chars:
        return False, f"length {n} above maximum {max_chars}"
    return True, f"length {n} within bounds"


# ─── final classification ──────────────────────────────────────────────────


@dataclass
class TribunalVerdict:
    task_id: str
    rule_checks: RuleCheckResult
    rule_check_details: dict[str, str]
    failed_critical_checks: list[str]
    failed_non_critical_checks: list[str]
    judge_verdict: Verdict
    judge_confidence: float
    judge_reasoning: str
    judge_status: str  # "RAN" · "STUB_NEUTRAL" · "UNAVAILABLE"
    final: Verdict
    downgraded: bool
    downgrade_reason: str | None
    reason_summary: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "rule_checks": self.rule_checks.as_dict(),
            "rule_check_details": self.rule_check_details,
            "failed_critical_checks": self.failed_critical_checks,
            "failed_non_critical_checks": self.failed_non_critical_checks,
            "judge": {
                "verdict": self.judge_verdict.value,
                "confidence": self.judge_confidence,
                "reasoning": self.judge_reasoning,
                "status": self.judge_status,
            },
            "final": self.final.value,
            "downgraded": self.downgraded,
            "downgrade_reason": self.downgrade_reason,
            "reason_summary": self.reason_summary,
        }


def classify(
    *,
    task_id: str,
    output: Any,
    pack_spec: dict[str, Any],
    citation_source_set: set[str],
    supplied_entities: set[str],
    judge_fn,
) -> TribunalVerdict:
    """Run the full Tribunal pipeline on one task output.

    pack_spec keys:
      schema · required_fields · tolerance_table · grounded_fields ·
      banned_actions · min_chars · max_chars · critical_checks
    """
    rules = RuleCheckResult()
    details: dict[str, str] = {}

    schema_ok, schema_detail = check_schema(output, pack_spec.get("schema"))
    rules.schema_valid = schema_ok
    details["schema_valid"] = schema_detail

    req_ok, req_detail = check_required_fields(output, pack_spec.get("required_fields"))
    rules.required_fields_present = req_ok
    details["required_fields_present"] = req_detail

    num_ok, num_detail, _failed_fields = check_numeric_tolerance(
        output, pack_spec.get("tolerance_table")
    )
    rules.numeric_within_tolerance = num_ok
    details["numeric_within_tolerance"] = num_detail

    cit_ok, cit_detail = check_citations_resolved(output, citation_source_set)
    rules.citations_resolved = cit_ok
    details["citations_resolved"] = cit_detail

    ent_ok, ent_detail = check_no_fabricated_entities(
        output, supplied_entities, pack_spec.get("grounded_fields")
    )
    rules.no_fabricated_entities = ent_ok
    details["no_fabricated_entities"] = ent_detail

    ban_ok, ban_detail = check_no_banned_actions(output, pack_spec.get("banned_actions", []))
    rules.no_banned_actions = ban_ok
    details["no_banned_actions"] = ban_detail

    len_ok, len_detail = check_output_length(
        output, pack_spec.get("min_chars"), pack_spec.get("max_chars")
    )
    rules.output_length_in_bounds = len_ok
    details["output_length_in_bounds"] = len_detail

    critical = set(pack_spec.get("critical_checks", []))
    failed = rules.failed_checks()
    failed_critical = [c for c in failed if c in critical or c == "schema_valid" or c == "required_fields_present"]
    failed_non_critical = [c for c in failed if c not in failed_critical]

    # Judge layer (callable provided · MVP stub returns NEUTRAL)
    judge_result = judge_fn(task_id=task_id, output=output)
    j_verdict = Verdict(judge_result["verdict"])
    j_conf = float(judge_result.get("confidence", 0.0))
    j_reasoning = judge_result.get("reasoning", "")
    j_status = judge_result.get("status", "RAN")

    # Final classification
    downgraded = False
    downgrade_reason = None
    if failed_critical:
        final = Verdict.PROPOLIS
        reason = f"Critical rule failure · {failed_critical} · auto-PROPOLIS regardless of judge"
    elif failed_non_critical:
        final = _downgrade(j_verdict)
        downgraded = True
        downgrade_reason = f"Non-critical rule failure · {failed_non_critical}"
        reason = f"Judge verdict {j_verdict.value} downgraded due to {failed_non_critical}"
    else:
        final = j_verdict
        if j_status == "STUB_NEUTRAL":
            # When judge is stubbed, rule-clean output stays at HONEY (best case under doctrine)
            final = Verdict.HONEY
            reason = "All rule checks passed · judge stub returned NEUTRAL · rule-clean → HONEY"
        else:
            reason = f"All rule checks passed · judge verdict {j_verdict.value} stands"

    return TribunalVerdict(
        task_id=task_id,
        rule_checks=rules,
        rule_check_details=details,
        failed_critical_checks=failed_critical,
        failed_non_critical_checks=failed_non_critical,
        judge_verdict=j_verdict,
        judge_confidence=j_conf,
        judge_reasoning=j_reasoning,
        judge_status=j_status,
        final=final,
        downgraded=downgraded,
        downgrade_reason=downgrade_reason,
        reason_summary=reason,
    )


# ─── aggregation ───────────────────────────────────────────────────────────


def aggregate_failure_taxonomy(verdicts: list[TribunalVerdict]) -> dict[str, Any]:
    total = len(verdicts)
    honey = sum(1 for v in verdicts if v.final == Verdict.HONEY)
    jelly = sum(1 for v in verdicts if v.final == Verdict.JELLY)
    propolis = sum(1 for v in verdicts if v.final == Verdict.PROPOLIS)

    downgrade_reasons: dict[str, int] = {}
    critical_failures: dict[str, int] = {}
    for v in verdicts:
        for c in v.failed_non_critical_checks:
            downgrade_reasons[c] = downgrade_reasons.get(c, 0) + 1
        for c in v.failed_critical_checks:
            critical_failures[c] = critical_failures.get(c, 0) + 1

    return {
        "total_tasks": total,
        "honey_count": honey,
        "jelly_count": jelly,
        "propolis_count": propolis,
        "honey_pct": round(100.0 * honey / total, 2) if total else 0.0,
        "jelly_pct": round(100.0 * jelly / total, 2) if total else 0.0,
        "propolis_pct": round(100.0 * propolis / total, 2) if total else 0.0,
        "downgrade_reasons": downgrade_reasons,
        "critical_failures": critical_failures,
    }


# ─── helpers ───────────────────────────────────────────────────────────────


def _downgrade(v: Verdict) -> Verdict:
    if v == Verdict.HONEY:
        return Verdict.JELLY
    if v == Verdict.JELLY:
        return Verdict.PROPOLIS
    return Verdict.PROPOLIS  # can't downgrade past Propolis


def _resolve_path(obj: Any, path: str) -> Any:
    """Resolve dotted path 'a.b.c' against a nested dict."""
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _stringify(obj: Any) -> str:
    if isinstance(obj, str):
        return obj
    import json as _json
    return _json.dumps(obj, sort_keys=True)
