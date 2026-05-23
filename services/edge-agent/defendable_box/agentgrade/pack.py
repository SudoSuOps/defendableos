"""Pack loader · reads a `packs/<pack_id>/` directory into structured objects.

Two pack conventions are supported (auto-detected per task/case dir):

  · compute_inspector_v1 style · rules.json + rubric.json + injection_payload.md
  · refund_agent_v1 style      · task.yaml + scoring.json + supplied_materials/ ;
                                  case.yaml + attack_prompt.md + supplied_materials/poisoned_input.txt

The detection is by-file (not by-pack), so a pack that mixes both styles loads
correctly. Malformed YAML/JSON raises PackLoadError · we do NOT silently skip.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class PackLoadError(ValueError):
    """Raised when a required pack file is missing or unparseable."""


@dataclass
class PackTask:
    task_id: str
    family: str
    prompt: str
    supplied_materials: dict[str, str]
    expected_schema: dict[str, Any] | None
    tolerance_table: dict[str, dict[str, float]] | None
    rubric: dict[str, Any] | None
    required_fields: list[str] | None
    grounded_fields: list[str] | None
    min_chars: int | None
    max_chars: int | None
    points_max: int
    # New (refund_agent_v1 fields · optional · None for compute-inspector tasks)
    expected_behavior_md: str | None = None
    scoring: dict[str, Any] | None = None
    allowed_action_taken_values: list[str] | None = None
    operator_approval_required_for_any_followon: bool = False
    family_weight: float | None = None
    schema_ref: str | None = None


@dataclass
class AdversarialCase:
    case_id: str
    category: str
    injection_payload: str
    expected_resistance: dict[str, Any]
    # New (refund_agent_v1 fields · optional)
    attack_prompt_md: str | None = None
    expected_safe_behavior_md: str | None = None
    failure_conditions_md: str | None = None
    scoring: dict[str, Any] | None = None
    banned_action_requested: str | None = None
    hard_fail_condition_triggered_if_compromised: str | None = None


@dataclass
class Pack:
    pack_id: str
    pack_version: str
    pack_dir: Path
    manifest: dict[str, Any]
    tasks: list[PackTask] = field(default_factory=list)
    adversarial_cases: list[AdversarialCase] = field(default_factory=list)
    citation_source_set: set[str] = field(default_factory=set)
    supplied_entities: set[str] = field(default_factory=set)
    banned_actions: list[str] = field(default_factory=list)
    critical_checks: list[str] = field(default_factory=list)
    capability_weights: dict[str, float] = field(default_factory=dict)
    # New (refund_agent_v1 fields)
    risk_tier: str | None = None
    risk_class: str | None = None
    deployment_status: str | None = None
    deed_eligibility: str | None = None
    required_review_path: list[str] = field(default_factory=list)
    hard_fail_conditions: list[str] = field(default_factory=list)
    hard_fail_consequence: dict[str, Any] = field(default_factory=dict)
    banned_action_keywords: list[str] = field(default_factory=list)
    permitted_lane: list[str] = field(default_factory=list)
    prohibited_lane: list[str] = field(default_factory=list)


def load_pack(pack_dir: Path) -> Pack:
    pack_dir = Path(pack_dir)
    manifest_path = pack_dir / "pack_manifest.json"
    if not manifest_path.exists():
        raise PackLoadError(f"pack_manifest.json missing in {pack_dir}")
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as exc:
        raise PackLoadError(f"pack_manifest.json malformed: {exc}") from exc

    # Load optional policy YAML files (refund_agent_v1 convention)
    policy_dir = pack_dir / "policy"
    prohibited_yaml = _read_yaml(policy_dir / "prohibited_actions.yaml") or {}
    scoring_rubric_yaml = _read_yaml(policy_dir / "scoring_rubric.yaml") or {}
    permitted_yaml = _read_yaml(policy_dir / "permitted_lane.yaml") or {}

    # Merge banned actions + keywords from manifest + policy
    banned_actions = list(dict.fromkeys(
        list(manifest.get("banned_actions", []))
        + list(prohibited_yaml.get("not_approved_for", []))
    ))
    banned_action_keywords = list(prohibited_yaml.get("banned_action_keywords", []))
    permitted_lane = list(
        permitted_yaml.get("commercially_deployable_for", [])
        or permitted_yaml.get("permitted_lane", [])
    )
    prohibited_lane = list(prohibited_yaml.get("not_approved_for", []))
    hard_fail_conditions = list(scoring_rubric_yaml.get("hard_fail_conditions", []))
    hard_fail_consequence = dict(scoring_rubric_yaml.get("hard_fail_consequence", {}))

    pack = Pack(
        pack_id=manifest["pack_id"],
        pack_version=manifest["pack_version"],
        pack_dir=pack_dir,
        manifest=manifest,
        banned_actions=banned_actions,
        critical_checks=manifest.get("critical_checks", []),
        capability_weights=manifest.get("feeds_capability_grade_weights", {}),
        risk_tier=manifest.get("risk_tier"),
        risk_class=manifest.get("risk_class"),
        deployment_status=manifest.get("deployment_status"),
        deed_eligibility=manifest.get("deed_eligibility"),
        required_review_path=list(manifest.get("required_review_path", [])),
        hard_fail_conditions=hard_fail_conditions,
        hard_fail_consequence=hard_fail_consequence,
        banned_action_keywords=banned_action_keywords,
        permitted_lane=permitted_lane,
        prohibited_lane=prohibited_lane,
    )

    # Load tasks
    tasks_dir = pack_dir / "tasks"
    if tasks_dir.is_dir():
        for task_dir in sorted(tasks_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            task = _load_task(task_dir, pack)
            if task is not None:
                pack.tasks.append(task)

    # Load adversarial cases
    adv_dir = pack_dir / "adversarial_cases"
    if adv_dir.is_dir():
        for case_dir in sorted(adv_dir.iterdir()):
            if not case_dir.is_dir():
                continue
            case = _load_adversarial(case_dir)
            if case is not None:
                pack.adversarial_cases.append(case)

    return pack


def _load_task(task_dir: Path, pack: Pack) -> PackTask | None:
    prompt_path = task_dir / "prompt.md"
    if not prompt_path.exists():
        return None
    prompt = prompt_path.read_text()

    materials_dir = task_dir / "supplied_materials"
    supplied: dict[str, str] = {}
    if materials_dir.is_dir():
        for mp in sorted(materials_dir.iterdir()):
            if mp.is_file():
                content = mp.read_text()
                supplied[mp.name] = content
                pack.citation_source_set.add(mp.name)
                # Index entity-like strings from the file content for grounding
                for token in _tokenize_entities(content):
                    pack.supplied_entities.add(token)

    # Refund-agent-style detection · task.yaml present means new convention
    task_yaml_path = task_dir / "task.yaml"
    if task_yaml_path.exists():
        return _load_task_refund_style(task_dir, prompt, supplied)

    # Fall back to compute-inspector convention
    schema = _read_json(task_dir / "expected_schema.json")
    tolerance = _read_json(task_dir / "tolerance_table.json")
    rubric = _read_json(task_dir / "rubric.json") or {}
    rules = _read_json(task_dir / "rules.json") or {}

    family = rubric.get("family", "identity")
    required = rules.get("required_fields") or rubric.get("required_fields")
    grounded = rules.get("grounded_fields") or rubric.get("grounded_fields")
    min_chars = rules.get("min_chars") or rubric.get("min_chars")
    max_chars = rules.get("max_chars") or rubric.get("max_chars")
    points_max = int(rubric.get("points_max", 100))

    return PackTask(
        task_id=task_dir.name,
        family=family,
        prompt=prompt,
        supplied_materials=supplied,
        expected_schema=schema,
        tolerance_table=tolerance,
        rubric=rubric,
        required_fields=required,
        grounded_fields=grounded,
        min_chars=min_chars,
        max_chars=max_chars,
        points_max=points_max,
    )


def _load_task_refund_style(
    task_dir: Path,
    prompt: str,
    supplied: dict[str, str],
) -> PackTask:
    task_yaml = _read_yaml_strict(task_dir / "task.yaml")
    scoring = _read_json_strict(task_dir / "scoring.json")
    expected_behavior_md = (task_dir / "expected_behavior.md").read_text() \
        if (task_dir / "expected_behavior.md").exists() else None
    return PackTask(
        task_id=task_yaml.get("task_id") or task_dir.name,
        family=task_yaml.get("family", "unspecified"),
        prompt=prompt,
        supplied_materials=supplied,
        expected_schema=None,
        tolerance_table=task_yaml.get("tolerance_table"),
        rubric=None,
        required_fields=list(task_yaml.get("required_fields", [])),
        grounded_fields=None,
        min_chars=None,
        max_chars=None,
        points_max=int(task_yaml.get("points_max", 100)),
        expected_behavior_md=expected_behavior_md,
        scoring=scoring,
        allowed_action_taken_values=list(task_yaml.get("allowed_action_taken_values", [])),
        operator_approval_required_for_any_followon=bool(
            task_yaml.get("operator_approval_required_for_any_followon", False)
        ),
        family_weight=float(task_yaml["family_weight"]) if "family_weight" in task_yaml else None,
        schema_ref=task_yaml.get("schema_ref"),
    )


def _load_adversarial(case_dir: Path) -> AdversarialCase | None:
    # Refund-agent-style detection · case.yaml + attack_prompt.md
    case_yaml_path = case_dir / "case.yaml"
    if case_yaml_path.exists():
        return _load_adversarial_refund_style(case_dir)

    # Fall back to compute-inspector convention
    payload_path = case_dir / "injection_payload.md"
    if not payload_path.exists():
        return None
    expected = _read_json(case_dir / "expected_resistance.json") or {}
    return AdversarialCase(
        case_id=case_dir.name,
        category=expected.get("category", "UNCATEGORIZED"),
        injection_payload=payload_path.read_text(),
        expected_resistance=expected,
    )


def _load_adversarial_refund_style(case_dir: Path) -> AdversarialCase:
    case_yaml = _read_yaml_strict(case_dir / "case.yaml")
    attack_prompt_md = (case_dir / "attack_prompt.md").read_text() \
        if (case_dir / "attack_prompt.md").exists() else None
    expected_safe_behavior_md = (case_dir / "expected_safe_behavior.md").read_text() \
        if (case_dir / "expected_safe_behavior.md").exists() else None
    failure_conditions_md = (case_dir / "failure_conditions.md").read_text() \
        if (case_dir / "failure_conditions.md").exists() else None
    scoring = _read_json(case_dir / "scoring.json")

    poisoned_path = case_dir / "supplied_materials" / "poisoned_input.txt"
    injection_payload = poisoned_path.read_text() if poisoned_path.exists() else (attack_prompt_md or "")

    return AdversarialCase(
        case_id=case_yaml.get("case_id") or case_dir.name,
        category=case_yaml.get("category", "UNCATEGORIZED"),
        injection_payload=injection_payload,
        expected_resistance={
            "category": case_yaml.get("category"),
            "expected_verdict_if_resisted": case_yaml.get("expected_verdict_if_resisted", "HONEY"),
            "expected_verdict_if_compromised": case_yaml.get("expected_verdict_if_compromised", "PROPOLIS"),
            "required_fields": case_yaml.get("required_fields", []),
            "scoring": scoring,
        },
        attack_prompt_md=attack_prompt_md,
        expected_safe_behavior_md=expected_safe_behavior_md,
        failure_conditions_md=failure_conditions_md,
        scoring=scoring,
        banned_action_requested=case_yaml.get("banned_action_requested"),
        hard_fail_condition_triggered_if_compromised=case_yaml.get(
            "hard_fail_condition_triggered_if_compromised"
        ),
    )


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise PackLoadError(f"{path} is malformed JSON: {exc}") from exc


def _read_json_strict(path: Path) -> Any:
    if not path.exists():
        raise PackLoadError(f"required file missing: {path}")
    return _read_json(path)


def _read_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    import yaml
    try:
        return yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise PackLoadError(f"{path} is malformed YAML: {exc}") from exc


def _read_yaml_strict(path: Path) -> Any:
    if not path.exists():
        raise PackLoadError(f"required YAML file missing: {path}")
    out = _read_yaml(path)
    if out is None:
        raise PackLoadError(f"{path} parsed to None")
    return out


def _tokenize_entities(text: str) -> list[str]:
    """Best-effort entity extraction for grounding checks.

    Returns identifiers that look like model names · PCI bus IDs ·
    numeric specs · etc. that might be referenced in agent outputs.
    Conservative · false-negatives are fine (agent isn't penalized
    for grounding to a real entity).
    """
    import re
    out: set[str] = set()
    # NVIDIA GPU naming patterns
    for m in re.finditer(r"NVIDIA[\w\s\-]+(?:Edition|Workstation)?", text):
        out.add(m.group(0).strip())
    # PCI bus IDs
    for m in re.finditer(r"\d{8}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}\.\d", text):
        out.add(m.group(0))
    # Memory sizes like 97887MiB · 24GB
    for m in re.finditer(r"\d+\s?(?:MiB|GiB|MB|GB)", text):
        out.add(m.group(0).strip())
    return list(out)
