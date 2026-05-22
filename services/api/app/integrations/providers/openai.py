"""OpenAI provider · OpenAI Chat Completions API.

Server-side only. OPENAI_API_KEY never reaches the browser.
Select via `MODEL_PROVIDER=openai` in the .env file.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.model_gateway import ModelProvider, ModelResult
from app.models.ai import WorkflowType


_SYSTEM_PROMPT_BY_WORKFLOW: dict[WorkflowType, str] = {
    WorkflowType.AIOV_DRAFT: (
        "You are an evidence-aware AIOV assistant for DefendableOS. "
        "You produce structured Proof of Value drafts for compute hardware. "
        "Cite supplied evidence by source_id. NEVER claim a licensed appraisal, "
        "legal certification, authentication guarantee, warranty, or insurance "
        "determination. List missing evidence honestly. Always include "
        "limitations including 'AI-assisted draft only'."
    ),
    WorkflowType.EVIDENCE_SUMMARY: (
        "Summarise the supplied evidence items factually. Cite source_id for "
        "every claim. Flag any text that cannot be supported by the supplied "
        "evidence."
    ),
    WorkflowType.RESEARCH_SYNTHESIS: (
        "Synthesise the supplied research sources. Tag every claim with the "
        "source_id and the evidence_classification (LISTING_PRICE, "
        "CONFIRMED_SALE_PRICE, MANUFACTURER_SPEC, etc). NEVER convert a listing "
        "price into a confirmed sale."
    ),
    WorkflowType.VALIDATOR_ASSIST: (
        "You are the validator. Identify weak evidence, missing comparables, "
        "and unsupported claims in the supplied AIOV draft. Be precise and "
        "minimal."
    ),
    WorkflowType.PUBLIC_DEED_SUMMARY: (
        "Produce a privacy-safe public verification summary. Reference only "
        "approved non-sensitive fields. No serial numbers, no purchase costs, "
        "no private documents."
    ),
    WorkflowType.EDGE_EVIDENCE_CLASSIFICATION: (
        "Classify the evidence item by evidence_type. Be conservative · prefer "
        "UNKNOWN over guessing."
    ),
}


class OpenAIProvider(ModelProvider):
    name = "openai"
    model = settings.openai_model
    base_url = settings.openai_base_url

    def is_configured(self) -> bool:
        return bool(settings.openai_api_key)

    def generate_structured(
        self,
        workflow_type: WorkflowType,
        prompt_version: str,
        input_reference: dict,
        prompt_payload: dict,
        thinking_enabled: bool,
    ) -> ModelResult:
        system_prompt = _SYSTEM_PROMPT_BY_WORKFLOW.get(
            workflow_type,
            "You are an evidence-aware assistant for DefendableOS. Cite source_id for every claim.",
        )
        user_prompt = (
            "Workflow: " + workflow_type.value + "\n\n"
            "Prompt version: " + prompt_version + "\n\n"
            "Input reference (sources are authoritative; do not invent facts beyond them):\n"
            + json.dumps(prompt_payload, indent=2, sort_keys=True)
            + "\n\n"
            "Respond in JSON when a structured output is helpful. Otherwise respond "
            "in prose, citing source_id values where applicable."
        )

        body: dict[str, Any] = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        # OpenAI's reasoning models (o1, o3 family) use the same API surface but
        # ignore `temperature` and expose a `reasoning_effort` field. We pass it
        # only when explicitly opted into "thinking" to stay backwards-compatible
        # with regular gpt-4o-class models.
        if thinking_enabled:
            body["reasoning_effort"] = "medium"

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        if settings.openai_organization:
            headers["OpenAI-Organization"] = settings.openai_organization

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()

        choice = (data.get("choices") or [{}])[0]
        content = (choice.get("message") or {}).get("content") or ""
        output_json: dict | None = None
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                output_json = parsed
        except Exception:
            output_json = None

        return ModelResult(
            provider=self.name,
            model=settings.openai_model,
            status="GENERATED",
            output_text=content,
            output_json=output_json,
            metadata={"usage": data.get("usage")},
        )
