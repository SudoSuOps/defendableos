"""Agent adapter interface · the contract for "agents under test".

Each adapter exposes:
  · agent_id          stable identifier for the deed
  · agent_version     version string · re-bench triggered on change
  · model_summary()   structured model identity
  · runtime_summary() runtime configuration that produced outputs
  · tool_permissions() tool scopes the agent operates under
  · invoke(task)      run one task · return structured output

MVP ships the MockReferenceAgent · a structured-stub that returns
honest reference outputs for the Compute Inspector pack. Real
adapters (vLLM · OpenAI · Kimi · llama.cpp) plug in next.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class TaskInput:
    task_id: str
    prompt: str
    supplied_materials: dict[str, str]   # filename → text content
    expected_schema: dict[str, Any] | None


@dataclass
class AgentInvocationResult:
    output: Any                    # the structured output (or raw text wrapped)
    raw_text: str                  # what the agent actually emitted before parsing
    latency_ms: int
    tokens_in: int | None
    tokens_out: int | None
    tool_calls: int
    notes: list[str]


class AgentAdapter(Protocol):
    agent_id: str
    agent_version: str

    def model_summary(self) -> dict[str, Any]: ...
    def runtime_summary(self) -> dict[str, Any]: ...
    def tool_permissions(self) -> dict[str, Any]: ...
    def invoke(self, task: TaskInput) -> AgentInvocationResult: ...


# ─── Mock Reference Agent ──────────────────────────────────────────────────


class MockReferenceAgent:
    """Reference adapter for MVP.

    Returns structured outputs for known Compute Inspector task families
    by parsing the supplied_materials (nvidia-smi · lscpu · lsblk text).
    This is NOT a real LLM call · it is a deterministic stub so the
    Tribunal + bundle pipeline can produce a real first receipt.

    Honest framing in the receipt: agent_id = `mock-reference-inspector-v0`
    · runtime_summary discloses "deterministic-stub · no LLM call" ·
    every adapter quirk is captured in `notes` so the receipt is
    audit-friendly.
    """

    agent_id = "mock-reference-inspector-v0"
    agent_version = "0.1.0-mvp"

    def model_summary(self) -> dict[str, Any]:
        return {
            "model_name": "deterministic-stub-inspector",
            "base_model": "none · pure-Python parser",
            "weights_sha256": "sha256:n/a",
            "license": "MVP reference adapter · operator-attested · ships with defendable-box",
            "implementation_note": (
                "This adapter does NOT call an LLM. It parses supplied "
                "materials with regex + structured rules. Used to validate "
                "the AgentGrade pipeline end-to-end before wiring real "
                "LLM-backed agents."
            ),
        }

    def runtime_summary(self) -> dict[str, Any]:
        return {
            "inference_engine": "deterministic-stub",
            "engine_version": "compute-bench-0.1.0",
            "seed": None,
            "temperature": None,
            "stub_note": "Deterministic Python · no model inference · runtime metrics are wall-clock only",
        }

    def tool_permissions(self) -> dict[str, Any]:
        return {
            "tools": [
                {"name": "parse_supplied_materials", "scope": "supplied_materials_only"},
                {"name": "search_web", "scope": "DISABLED", "rationale": "Compute Inspector pack runs on supplied materials only"},
                {"name": "install_software", "scope": "DISABLED"},
            ]
        }

    def invoke(self, task: TaskInput) -> AgentInvocationResult:
        import time

        t0 = time.perf_counter()
        output, notes = self._handle_task(task)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        raw_text = json.dumps(output, sort_keys=True, indent=2)
        return AgentInvocationResult(
            output=output,
            raw_text=raw_text,
            latency_ms=latency_ms,
            tokens_in=None,
            tokens_out=None,
            tool_calls=0,
            notes=notes,
        )

    # ── per-family handlers ────────────────────────────────────────────────

    def _handle_task(self, task: TaskInput) -> tuple[Any, list[str]]:
        family = self._infer_family(task)
        if family == "identity":
            return self._identity(task)
        if family == "system_manifest":
            return self._system_manifest(task)
        if family == "health_diagnostic":
            return self._health_diagnostic(task)
        if family == "tier_inference":
            return self._tier_inference(task)
        if family == "rental_readiness":
            return self._rental_readiness(task)
        if family == "recommendation_draft":
            return self._recommendation_draft(task)
        if family == "reporting":
            return self._reporting(task)
        if family == "edge_case":
            return self._edge_case(task)
        return ({"status": "UNKNOWN_FAMILY", "task_id": task.task_id}, [f"no handler for family {family}"])

    def _infer_family(self, task: TaskInput) -> str:
        # task_id pattern: task_NNN_<family> · MVP uses the prompt header
        prompt_lower = task.prompt.lower()
        if "identity" in prompt_lower and "manifest" not in prompt_lower:
            return "identity"
        if "system manifest" in prompt_lower or "system_manifest" in prompt_lower:
            return "system_manifest"
        if "health" in prompt_lower or "dcgm" in prompt_lower:
            return "health_diagnostic"
        if "tier" in prompt_lower:
            return "tier_inference"
        if "rental" in prompt_lower or "vast.ai" in prompt_lower:
            return "rental_readiness"
        if "best next use" in prompt_lower or "recommendation" in prompt_lower:
            return "recommendation_draft"
        if "summary" in prompt_lower or "operator-facing" in prompt_lower:
            return "reporting"
        if "malfunction" in prompt_lower or "mismatch" in prompt_lower:
            return "edge_case"
        return "identity"

    # Helpers to read supplied materials safely
    def _material(self, task: TaskInput, name: str) -> str:
        return task.supplied_materials.get(name, "")

    # ─── identity ─────────────────────────────────────────────────────────

    def _identity(self, task: TaskInput) -> tuple[Any, list[str]]:
        nvidia = self._material(task, "nvidia_smi.txt")
        notes = []
        # Try to extract a GPU name + VRAM
        name_match = re.search(r"NVIDIA\s+([\w\s\-]+?)(?:\s+Workstation|\s+Edition|\s+\d{2,3}MiB|\n)", nvidia)
        vram_match = re.search(r"(\d+)MiB", nvidia)
        if "Failed to initialize NVML" in nvidia or "Driver/library version mismatch" in nvidia:
            return (
                {
                    "asset_class": "COMPUTE_HARDWARE",
                    "asset_tier": "E0",
                    "manufacturer": "NVIDIA",
                    "model": "DETECTED_VIA_LSPCI · DRIVER_NONFUNCTIONAL",
                    "vram_gb": None,
                    "form_factor": "CPU_NODE",
                    "identity_confidence_grade": "INCOMPLETE",
                    "reasoning": "nvidia-smi reports driver/library version mismatch · GPU is non-functional · classified E0 CPU node honestly · cited [source:nvidia_smi.txt]",
                },
                ["edge case: driver mismatch detected"],
            )
        name = name_match.group(1).strip() if name_match else "Unknown NVIDIA GPU"
        vram_mib = int(vram_match.group(1)) if vram_match else 0
        vram_gb = vram_mib // 1024
        if vram_gb >= 80:
            tier, form = "E6", "DISCRETE_CARD"
        elif vram_gb >= 30:
            tier, form = "E5", "DISCRETE_CARD"
        elif vram_gb >= 20:
            tier, form = "E4", "DISCRETE_CARD"
        else:
            tier, form = "E2", "DISCRETE_CARD"
        return (
            {
                "asset_class": "COMPUTE_HARDWARE",
                "asset_tier": tier,
                "manufacturer": "NVIDIA",
                "model": f"NVIDIA {name}",
                "vram_gb": vram_gb,
                "form_factor": form,
                "identity_confidence_grade": "C",
                "reasoning": f"Captured GPU model {name} with {vram_gb}GB VRAM from supplied nvidia-smi output. Tier {tier} inferred from VRAM. [source:nvidia_smi.txt]",
            },
            notes,
        )

    # ─── system manifest ──────────────────────────────────────────────────

    def _system_manifest(self, task: TaskInput) -> tuple[Any, list[str]]:
        lscpu = self._material(task, "lscpu.txt")
        cpu_match = re.search(r"Model name:\s+(.+)", lscpu)
        cores_match = re.search(r"^CPU\(s\):\s+(\d+)", lscpu, re.MULTILINE)
        return (
            {
                "host": {
                    "cpu_model": cpu_match.group(1).strip() if cpu_match else "Unknown CPU",
                    "cpu_count": int(cores_match.group(1)) if cores_match else None,
                    "platform": "Linux",
                },
                "captured_at": "supplied · timestamp from task materials",
                "reasoning": "Parsed lscpu output for CPU model and core count. [source:lscpu.txt]",
            },
            [],
        )

    # ─── health diagnostic ────────────────────────────────────────────────

    def _health_diagnostic(self, task: TaskInput) -> tuple[Any, list[str]]:
        dcgm = self._material(task, "dcgmi_diag.json")
        if '"status" : "Pass"' in dcgm or '"status": "Pass"' in dcgm:
            grade = "PASS"
            reason = "DCGM diag output reports Pass for all evaluated categories. [source:dcgmi_diag.json]"
        elif '"status" : "Fail"' in dcgm or '"status": "Fail"' in dcgm:
            grade = "FAIL"
            reason = "DCGM diag output reports Fail. [source:dcgmi_diag.json]"
        else:
            grade = "NOT_TESTED"
            reason = "No conclusive DCGM result in supplied materials. [source:dcgmi_diag.json]"
        return (
            {
                "health_grade": grade,
                "diagnostic_method": "supplied dcgmi diag output (parsed)",
                "reasoning": reason,
            },
            [],
        )

    # ─── tier inference ───────────────────────────────────────────────────

    def _tier_inference(self, task: TaskInput) -> tuple[Any, list[str]]:
        # Re-use identity parsing
        ident, _ = self._identity(task)
        return (
            {
                "asset_tier": ident.get("asset_tier", "E0"),
                "vram_gb": ident.get("vram_gb"),
                "model": ident.get("model"),
                "reasoning": f"Tier {ident.get('asset_tier')} matches the VRAM bucket per docs/COMPUTE_ASSET_TAXONOMY.md. [source:nvidia_smi.txt]",
            },
            [],
        )

    # ─── rental readiness ─────────────────────────────────────────────────

    def _rental_readiness(self, task: TaskInput) -> tuple[Any, list[str]]:
        return (
            {
                "vast_ai_host_ready": False,
                "missing": [
                    "Vast.ai client not installed in supplied environment",
                    "Verified host status not present",
                ],
                "reasoning": "Cannot certify Vast.ai host-readiness from supplied logs alone. [source:nvidia_smi.txt]",
            },
            [],
        )

    # ─── recommendation draft ─────────────────────────────────────────────

    def _recommendation_draft(self, task: TaskInput) -> tuple[Any, list[str]]:
        ident, _ = self._identity(task)
        tier = ident.get("asset_tier", "E0")
        if tier in ("E5", "E6"):
            rec = "RETAIN_AND_DEPLOY"
            why = "Institutional-class accelerator · high local AI capability · operator-attested deployment context"
        elif tier == "E4":
            rec = "HOLD_AND_RENT"
            why = "Workhorse-class GPU with observed rental signal · founder operating context not yet captured"
        else:
            rec = "EVIDENCE_INCOMPLETE"
            why = "Insufficient evidence for confident recommendation"
        return (
            {
                "primary_recommendation": rec,
                "primary_recommendation_basis": why,
                "evidence_to_capture_next": ["VAST_FOUNDER_RENTAL_RECEIPT", "comp evidence ≥3 records"],
                "reasoning": f"Recommendation {rec} reflects tier {tier} and available evidence. [source:nvidia_smi.txt]",
            },
            [],
        )

    # ─── reporting ────────────────────────────────────────────────────────

    def _reporting(self, task: TaskInput) -> tuple[Any, list[str]]:
        ident, _ = self._identity(task)
        return (
            {
                "summary": (
                    f"{ident.get('model', 'Unknown asset')} captured as compute_tier "
                    f"{ident.get('asset_tier', '?')} with {ident.get('vram_gb', 'unknown')}GB VRAM. "
                    f"Identity confidence {ident.get('identity_confidence_grade', '?')} per supplied nvidia-smi. "
                    f"No workload utility measured in this run. [source:nvidia_smi.txt]"
                ),
                "reasoning": "Operator-facing summary derived from identity capture. [source:nvidia_smi.txt]",
            },
            [],
        )

    # ─── edge case ────────────────────────────────────────────────────────

    def _edge_case(self, task: TaskInput) -> tuple[Any, list[str]]:
        nvidia = self._material(task, "nvidia_smi.txt")
        if "Failed to initialize NVML" in nvidia or "Driver/library version mismatch" in nvidia:
            return (
                {
                    "classification": "MALFUNCTIONING",
                    "reasoning": "nvidia-smi reports driver/library version mismatch · refusing to infer GPU specs from broken telemetry. [source:nvidia_smi.txt]",
                    "recommended_action": "Repair driver before bench · operator escalation",
                },
                ["edge case · driver mismatch · honest classification"],
            )
        return (
            {
                "classification": "NOMINAL_NO_EDGE_DETECTED",
                "reasoning": "No edge-case markers in supplied materials. [source:nvidia_smi.txt]",
            },
            [],
        )
