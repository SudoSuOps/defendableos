"""Pack loader · reads a `packs/<pack_id>/` directory into structured objects."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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


@dataclass
class AdversarialCase:
    case_id: str
    category: str
    injection_payload: str
    expected_resistance: dict[str, Any]


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


def load_pack(pack_dir: Path) -> Pack:
    pack_dir = Path(pack_dir)
    manifest = json.loads((pack_dir / "pack_manifest.json").read_text())
    pack = Pack(
        pack_id=manifest["pack_id"],
        pack_version=manifest["pack_version"],
        pack_dir=pack_dir,
        manifest=manifest,
        banned_actions=manifest.get("banned_actions", []),
        critical_checks=manifest.get("critical_checks", []),
        capability_weights=manifest.get("feeds_capability_grade_weights", {}),
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
                supplied[mp.name] = mp.read_text()
                pack.citation_source_set.add(mp.name)
                # Index entity-like strings from the file content for grounding
                for token in _tokenize_entities(mp.read_text()):
                    pack.supplied_entities.add(token)

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


def _load_adversarial(case_dir: Path) -> AdversarialCase | None:
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


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text())


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
