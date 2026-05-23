"""Bundle manifest + public-safe export.

Same SHA-256 hashing pattern as Compute Bench (see
docs/COMPUTE_BENCH_RECEIPT_SCHEMA.md and the matching
defendable_box/compute/manifest.py).

Manifest excludes itself + public_safe_attestation.json (same
chicken-and-egg rule).
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


_MANIFEST_EXCLUDES = {"manifest.sha256", "public_safe_attestation.json"}

_PRIVATE_FIELD_NAMES = {
    "prompt_policy_private",
    "raw_serial",
    "device_uuid",
    "pci_bus_id",
    "host_machine_hostname",
    "training_dataset_lineage",
}


def _sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _sha256_json(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_manifest(run_dir: Path) -> dict[str, Any]:
    per_file: dict[str, str] = {}
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(run_dir).as_posix()
        if rel in _MANIFEST_EXCLUDES:
            continue
        per_file[rel] = _sha256_file(path)
    bundle_hash = _sha256_json(per_file)
    return {
        "bundle_sha256": bundle_hash,
        "hash_algorithm": "SHA-256",
        "per_file_sha256": per_file,
        "manifest_excludes": sorted(_MANIFEST_EXCLUDES),
    }


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: _redact(v)
            for k, v in value.items()
            if k not in _PRIVATE_FIELD_NAMES and not k.endswith("_private")
        }
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def public_safe_redact(payload: dict[str, Any]) -> dict[str, Any]:
    return _redact(copy.deepcopy(payload))


def public_export_or_refuse(
    *,
    run_id: str,
    agent_identity: dict[str, Any],
    model_summary: dict[str, Any],
    runtime_summary: dict[str, Any],
    compute_deed_reference: str,
    grades_card: dict[str, Any],
    tribunal_summary: dict[str, Any],
    adversarial_summary: dict[str, Any],
    pack,
    captured_by: str,
    captured_at: str,
    role_lane: str,
    intended_workflow_boundary: str,
    bundle_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Build public_safe_attestation.json from public-safe-classed inputs."""
    redacted_identity = public_safe_redact(agent_identity)
    redacted_model = public_safe_redact(model_summary)
    redacted_runtime = public_safe_redact(runtime_summary)
    bundle_hash = bundle_manifest.get("bundle_sha256", "")
    return {
        "run_id": run_id,
        "agent_id": redacted_identity.get("agent_id"),
        "agent_version": redacted_identity.get("agent_version"),
        "vendor": redacted_identity.get("vendor"),
        "role_lane": role_lane,
        "intended_workflow_boundary": intended_workflow_boundary,
        "captured_at": captured_at,
        "captured_by": captured_by,
        "benchmark_pack": pack.pack_id,
        "benchmark_pack_version": pack.pack_version,
        "compute_deed_reference": compute_deed_reference,
        "model_summary": {
            "name": redacted_model.get("model_name"),
            "base": redacted_model.get("base_model"),
            "weights_sha256": redacted_model.get("weights_sha256"),
            "implementation_note": redacted_model.get("implementation_note"),
        },
        "grades": {
            "capability": grades_card["capability"]["score"],
            "truth": grades_card["truth"]["score"],
            "safety": grades_card["safety"]["score"],
            "numeric_structural": grades_card["numeric_structural"]["score"],
            "efficiency": grades_card["efficiency"]["score"],
            "reproducibility": grades_card["reproducibility"]["score"],
            "agentgrade_composite": grades_card.get("agentgrade_composite"),
        },
        "deployment_tier": grades_card.get("deployment_tier"),
        "deployment_tier_rationale": grades_card.get("deployment_tier_rationale"),
        "deployment_lane": grades_card.get("deployment_lane"),
        "pack_status_cap_applied": grades_card.get("pack_status_cap_applied", False),
        "tribunal_summary": {
            "honey_pct": tribunal_summary.get("honey_pct"),
            "jelly_pct": tribunal_summary.get("jelly_pct"),
            "propolis_pct": tribunal_summary.get("propolis_pct"),
            "downgrade_reasons": tribunal_summary.get("downgrade_reasons", {}),
            "critical_failures": tribunal_summary.get("critical_failures", {}),
        },
        "safety_summary": {
            "adversarial_total": adversarial_summary.get("adversarial_cases_total"),
            "adversarial_resisted": adversarial_summary.get("resisted"),
            "adversarial_compromised": adversarial_summary.get("compromised"),
            "adversarial_conditional": adversarial_summary.get("conditional"),
        },
        "cost_summary": {
            "avg_total_cost_per_task_usd": None,
            "amortization_notes": "MVP reference adapter has no LLM cost · efficiency grade INCOMPLETE",
        },
        "runtime_summary": {
            "engine": redacted_runtime.get("inference_engine"),
            "engine_version": redacted_runtime.get("engine_version"),
            "stub_note": redacted_runtime.get("stub_note"),
        },
        "manifest_hash": f"sha256:{bundle_hash}",
        "bundle_hash": f"sha256:{bundle_hash}",
        "limitations": [
            "MVP run · pack v1.0-alpha · tier capped at OBSERVED until pack graduates to READY_FOR_PRODUCTION",
            "Judge layer = stub · rule-only Tribunal verdicts · model-judgment layer wired next session",
            "Mock reference adapter · no real LLM call · proves the pipeline · real adapters wired next",
            "Efficiency grade INCOMPLETE · cost capture pending Phase 2",
        ],
        "re_attestation_trigger": "AGENT_VERSION_CHANGE · MODEL_WEIGHTS_CHANGE · PROMPT_POLICY_CHANGE · PACK_VERSION_CHANGE · TOOL_SET_CHANGE",
    }
