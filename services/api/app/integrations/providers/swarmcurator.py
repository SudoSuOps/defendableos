"""SwarmCurator-9B provider · sovereign in-house Qwen3.5 fine-tune served via vLLM.

Mirrors the Kimi provider contract (OpenAI-compatible chat completions). The
endpoint lives on smash (`http://smash:8088/v1` over Tailscale) and runs the
SwarmCurator-9B chat-template-nothink variant. All grading / evidence-aware
workflows that today call Kimi will route here when MODEL_PROVIDER=swarmcurator.

Doctrine: sovereign compute · no external dependency on the hot path · the
in-house cook is the house judge. Vision-capable workflows still route to
Kimi until SwarmCurator-Vision lands.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.model_gateway import (
    ModelProvider,
    ModelResult,
    ToolCall,
    ToolDefinition,
    VisionImage,
)
from app.models.ai import WorkflowType


_SYSTEM_PROMPT_BY_WORKFLOW: dict[WorkflowType, str] = {
    WorkflowType.AIOV_DRAFT: (
        "You are SwarmCurator · the evidence-aware AIOV assistant for DefendableOS. "
        "Produce structured Proof of Value drafts for compute hardware. "
        "Cite supplied evidence by source_id. NEVER claim a licensed appraisal, "
        "legal certification, authentication guarantee, warranty, or insurance "
        "determination. List missing evidence honestly. Always include limitations "
        "including 'AI-assisted draft only · SwarmCurator-9B'."
    ),
    WorkflowType.EVIDENCE_SUMMARY: (
        "You are SwarmCurator. Summarise the supplied evidence items factually. "
        "Cite source_id for every claim. Flag any text that cannot be supported by "
        "the supplied evidence. No hallucination."
    ),
    WorkflowType.RESEARCH_SYNTHESIS: (
        "You are SwarmCurator. Synthesise the supplied research sources. Tag every "
        "claim with the source_id and the evidence_classification (LISTING_PRICE, "
        "CONFIRMED_SALE_PRICE, MANUFACTURER_SPEC, etc). NEVER convert a listing "
        "price into a confirmed sale."
    ),
    WorkflowType.VALIDATOR_ASSIST: (
        "You are SwarmCurator · the validator. Identify weak evidence, missing "
        "comparables, and unsupported claims in the supplied AIOV draft. Be precise "
        "and minimal. Operator-grade rigor · CRE-broker discipline."
    ),
    WorkflowType.PUBLIC_DEED_SUMMARY: (
        "You are SwarmCurator. Produce a privacy-safe public verification summary. "
        "Reference only approved non-sensitive fields. No serial numbers, no "
        "purchase costs, no private documents."
    ),
    WorkflowType.EDGE_EVIDENCE_CLASSIFICATION: (
        "You are SwarmCurator. Classify the evidence item by evidence_type. Be "
        "conservative · prefer UNKNOWN over guessing."
    ),
}


class SwarmCuratorProvider(ModelProvider):
    name = "swarmcurator"
    model = settings.swarmcurator_model
    base_url = settings.swarmcurator_base_url

    def is_configured(self) -> bool:
        return bool(settings.swarmcurator_base_url)

    def generate_structured(
        self,
        workflow_type: WorkflowType,
        prompt_version: str,
        input_reference: dict,
        prompt_payload: dict,
        thinking_enabled: bool,
        tools: list[ToolDefinition] | None = None,
        images: list[VisionImage] | None = None,
    ) -> ModelResult:
        # SwarmCurator-9B is text-only today · vllm launched with image=0, video=0
        # in chat_template_nothink.jinja. Vision workflows should route to a
        # vision-capable provider (Kimi keeps that role until SwarmCurator-Vision).
        if images:
            return ModelResult(
                provider=self.name,
                model=self.model,
                status="NOT_CONFIGURED",
                error=(
                    "SwarmCurator-9B is text-only. Image workflows must route to a "
                    "vision-capable provider (set MODEL_PROVIDER=kimi or implement "
                    "per-workflow provider routing)."
                ),
            )

        system_prompt = _SYSTEM_PROMPT_BY_WORKFLOW.get(
            workflow_type,
            "You are SwarmCurator · evidence-aware assistant for DefendableOS. "
            "Cite source_id for every claim.",
        )
        user_text = (
            "Workflow: " + workflow_type.value + "\n\n"
            "Prompt version: " + prompt_version + "\n\n"
            "Input reference (sources are authoritative; do not invent facts beyond them):\n"
            + json.dumps(prompt_payload, indent=2, sort_keys=True)
            + "\n\n"
            + (
                "Call the supplied tool functions to record your findings. "
                "Use multiple calls when more than one finding applies. "
                "Do not respond in prose."
                if tools
                else "Respond in JSON when a structured output is helpful. "
                "Otherwise respond in prose, citing source_id values where applicable."
            )
        )

        body: dict[str, Any] = {
            "model": settings.swarmcurator_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        }
        if tools:
            body["tools"] = [t.to_provider_payload() for t in tools]
            body["tool_choice"] = "auto"
        # SwarmCurator vllm is launched with chat_template_nothink.jinja by default ·
        # thinking_enabled is a no-op on this provider. Kept in signature for parity.

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if settings.swarmcurator_api_key:
            headers["Authorization"] = f"Bearer {settings.swarmcurator_api_key}"

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=body,
            )
            if resp.status_code >= 400:
                raise httpx.HTTPStatusError(
                    f"SwarmCurator error {resp.status_code}: {resp.text[:500]}",
                    request=resp.request,
                    response=resp,
                )
            data = resp.json()

        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        output_json: dict | None = None
        try:
            output_json = json.loads(content)
            if not isinstance(output_json, dict):
                output_json = None
        except Exception:
            output_json = None

        tool_calls: list[ToolCall] = []
        for tc in message.get("tool_calls") or []:
            fn = tc.get("function") or {}
            raw_args = fn.get("arguments") or "{}"
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                if not isinstance(args, dict):
                    args = {"_raw": args}
            except Exception:
                args = {"_raw": raw_args}
            tool_calls.append(
                ToolCall(name=fn.get("name", ""), arguments=args, call_id=tc.get("id"))
            )

        return ModelResult(
            provider=self.name,
            model=settings.swarmcurator_model,
            status="GENERATED",
            output_text=content,
            output_json=output_json,
            tool_calls=tool_calls,
            metadata={"usage": data.get("usage")},
        )
