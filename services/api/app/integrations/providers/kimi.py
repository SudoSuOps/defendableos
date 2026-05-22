"""Kimi K2.6 provider · Moonshot's OpenAI-compatible API.

Requests are sent server-side only. MOONSHOT_API_KEY never reaches the browser.
Thinking is disabled by default (per gateway policy) so structured outputs
arrive at UI speed; deeper workflows may opt-in server-side.
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


class KimiProvider(ModelProvider):
    name = "kimi"
    model = settings.moonshot_model
    base_url = settings.moonshot_base_url

    def is_configured(self) -> bool:
        return bool(settings.moonshot_api_key)

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
            "model": settings.moonshot_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        if thinking_enabled:
            body["enable_thinking"] = True

        headers = {
            "Authorization": f"Bearer {settings.moonshot_api_key}",
            "Content-Type": "application/json",
        }

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
            output_json = json.loads(content)
            if not isinstance(output_json, dict):
                output_json = None
        except Exception:
            output_json = None

        return ModelResult(
            provider=self.name,
            model=settings.moonshot_model,
            status="GENERATED",
            output_text=content,
            output_json=output_json,
            metadata={"usage": data.get("usage")},
        )
