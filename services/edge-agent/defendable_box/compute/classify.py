"""Per-artifact vault + rights classification + public-safe redaction.

Matches the doctrine in:
  · docs/EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md
  · docs/COMPUTE_BENCH_RECEIPT_SCHEMA.md

The classification + public-safe export mirrors the same
public_export_or_refuse() guarantee the platform enforces server-side:
nothing classified PRIVATE_EVIDENCE / MARKET_OBSERVATIONS /
DERIVED_DATASETS ever appears in public_safe_attestation.json.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

# Map of bundle filenames → (vault_class, rights_status, public_safe_summary?)
# public_safe_summary=True means the file's contents are entirely public-safe
# (and a copy/reference may go into the public attestation).
# public_safe_summary=False means private · NEVER copied into public output.
ARTIFACT_CLASSIFICATION: dict[str, dict[str, Any]] = {
    "asset_identity.json": {
        "vault": "PUBLIC_ASSETS",
        "rights": "PUBLIC_DISPLAY_ALLOWED",
        "public_safe_summary": True,
    },
    "private_identity_reference.json": {
        "vault": "PRIVATE_EVIDENCE",
        "rights": "RESTRICTED_DO_NOT_EXPORT",
        "public_safe_summary": False,
    },
    "system_manifest.json": {
        "vault": "DERIVED_DATASETS",
        "rights": "INTERNAL_RESEARCH_ONLY",
        "public_safe_summary": False,
    },
    "runtime_environment.json": {
        "vault": "PUBLIC_ASSETS",
        "rights": "PUBLIC_DISPLAY_ALLOWED",
        "public_safe_summary": True,
    },
    "health_diagnostic.json": {
        "vault": "DERIVED_DATASETS",
        "rights": "INTERNAL_RESEARCH_ONLY",
        "public_safe_summary": False,
    },
    "thermal_power_trace.jsonl": {
        "vault": "PRIVATE_EVIDENCE",
        "rights": "INTERNAL_RESEARCH_ONLY",
        "public_safe_summary": False,
    },
    "benchmark_plan.json": {
        "vault": "PUBLIC_ASSETS",
        "rights": "PUBLIC_DISPLAY_ALLOWED",
        "public_safe_summary": True,
    },
    "benchmark_results.json": {
        "vault": "DERIVED_DATASETS",
        "rights": "INTERNAL_RESEARCH_ONLY",
        "public_safe_summary": False,
    },
    "workload_compatibility.json": {
        "vault": "PUBLIC_ASSETS",
        "rights": "PUBLIC_DISPLAY_ALLOWED",
        "public_safe_summary": True,
    },
    "evidence_classification.json": {
        "vault": "DERIVED_DATASETS",
        "rights": "INTERNAL_RESEARCH_ONLY",
        "public_safe_summary": False,
    },
    "validator_flags.json": {
        "vault": "DERIVED_DATASETS",
        "rights": "INTERNAL_RESEARCH_ONLY",
        "public_safe_summary": False,
    },
    "best_next_use_inputs.json": {
        "vault": "DERIVED_DATASETS",
        "rights": "INTERNAL_RESEARCH_ONLY",
        "public_safe_summary": False,
    },
    "public_safe_attestation.json": {
        "vault": "PUBLIC_ASSETS",
        "rights": "PUBLIC_DISPLAY_ALLOWED",
        "public_safe_summary": True,
    },
    "manifest.sha256": {
        "vault": "PUBLIC_ASSETS",
        "rights": "PUBLIC_DISPLAY_ALLOWED",
        "public_safe_summary": True,
    },
}


def evidence_classification_doc(run_dir: Path) -> dict[str, Any]:
    """Build the evidence_classification.json contents for a run."""
    items = []
    for path in sorted(run_dir.iterdir()):
        if not path.is_file():
            continue
        rel = path.name
        cls = ARTIFACT_CLASSIFICATION.get(rel)
        if cls is None:
            cls = {
                "vault": "PRIVATE_EVIDENCE",
                "rights": "INTERNAL_RESEARCH_ONLY",
                "public_safe_summary": False,
            }
        items.append({
            "artifact": rel,
            "vault": cls["vault"],
            "rights": cls["rights"],
            "public_safe_summary_allowed": cls["public_safe_summary"],
        })
    return {"items": items}


# ─── private-field redaction ───────────────────────────────────────────────


_PRIVATE_FIELD_SUFFIXES = ("_private", "_serial", "_uuid")
_PRIVATE_FIELD_NAMES = {
    "raw_serial",
    "device_uuid",
    "pci_bus_id",
    "host_machine_hostname",
    "host_dmi_uuid",
    "vbios_version",
    "board_part_number",
    "manufacturer_private",
    "product_name_private",
    "serial_number_private",
    "uuid_private",
    "serial_private",
}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: _redact(v)
            for k, v in value.items()
            if k not in _PRIVATE_FIELD_NAMES
            and not any(k.endswith(s) for s in _PRIVATE_FIELD_SUFFIXES)
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def public_safe_redacted(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip any field flagged as private from a copy of the payload."""
    return _redact(copy.deepcopy(payload))


# ─── public-safe attestation builder ───────────────────────────────────────


def public_export_or_refuse(
    *,
    asset_identity: dict[str, Any],
    runtime_env: dict[str, Any],
    grades: dict[str, str],
    benchmark_plan: dict[str, Any],
    workload_compat: dict[str, Any],
    bundle_manifest: dict[str, Any],
    captured_by: str,
    limitations: list[str],
    re_attestation_trigger: str,
) -> dict[str, Any]:
    """Build the public_safe_attestation.json content.

    Only fields from PUBLIC_ASSETS-classed inputs appear. The function
    is named to match the platform's services/artifacts.py guard so
    the boundary doctrine is recognizable.
    """
    redacted_identity = public_safe_redacted(asset_identity)
    redacted_runtime = public_safe_redacted(runtime_env)
    redacted_plan = public_safe_redacted(benchmark_plan)
    redacted_compat = public_safe_redacted(workload_compat)

    return {
        "run_id": asset_identity.get("run_id"),
        "asset_class": redacted_identity.get("asset_class"),
        "asset_tier": redacted_identity.get("asset_tier"),
        "model": redacted_identity.get("model") or redacted_identity.get("manufacturer"),
        "vram_gb": redacted_identity.get("vram_gb"),
        "form_factor": redacted_identity.get("form_factor"),
        "captured_at": redacted_identity.get("captured_at"),
        "captured_by": captured_by,
        "grades": grades,
        "demonstrated_workloads": redacted_compat.get("demonstrated", []),
        "not_tested": redacted_compat.get("not_tested", []),
        "benchmark_plan_scope": redacted_plan.get("test_scope"),
        "manifest_hash": f"sha256:{bundle_manifest.get('bundle_sha256', '')}",
        "bundle_hash": f"sha256:{bundle_manifest.get('bundle_sha256', '')}",
        "runtime_summary": {
            "driver": redacted_runtime.get("tool_versions", {}).get("nvidia-smi"),
            "cuda": redacted_runtime.get("tool_versions", {}).get("nvcc"),
            "os": redacted_runtime.get("os_release", {}).get("pretty_name"),
            "kernel": redacted_runtime.get("platform", {}).get("release"),
        },
        "limitations": limitations,
        "re_attestation_trigger": re_attestation_trigger,
    }
