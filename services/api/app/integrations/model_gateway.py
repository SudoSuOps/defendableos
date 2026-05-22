"""Provider-agnostic model gateway.

Workflows go through this gateway, not directly to any provider SDK. The first
configured provider is Kimi K2.6 (Moonshot · OpenAI-compatible). Local Swarm
endpoints, Atlas, SwarmCurator, and vertical-specific 9B models can be added
as providers without rewriting AIOV / validator / evidence-summary workflows.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings
from app.models.ai import WorkflowType


@dataclass
class ModelResult:
    provider: str
    model: str
    status: str  # GENERATED | NOT_CONFIGURED | FAILED
    output_text: str | None = None
    output_json: dict | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelProvider:
    name: str = "unknown"
    model: str = "unknown"

    def is_configured(self) -> bool:
        return False

    def generate_structured(
        self,
        workflow_type: WorkflowType,
        prompt_version: str,
        input_reference: dict,
        prompt_payload: dict,
        thinking_enabled: bool,
    ) -> ModelResult:  # pragma: no cover · abstract
        raise NotImplementedError


class ModelGateway:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def generate_structured(
        self,
        workflow_type: WorkflowType,
        prompt_version: str,
        input_reference: dict,
        prompt_payload: dict,
        thinking_enabled: bool = False,
    ) -> ModelResult:
        if not self.provider.is_configured():
            return ModelResult(
                provider=self.provider.name,
                model=self.provider.model,
                status="NOT_CONFIGURED",
                error=f"{self.provider.name} provider is not configured",
            )
        try:
            return self.provider.generate_structured(
                workflow_type=workflow_type,
                prompt_version=prompt_version,
                input_reference=input_reference,
                prompt_payload=prompt_payload,
                thinking_enabled=thinking_enabled,
            )
        except Exception as exc:
            return ModelResult(
                provider=self.provider.name,
                model=self.provider.model,
                status="FAILED",
                error=str(exc),
            )


_gateway: ModelGateway | None = None


def get_model_gateway() -> ModelGateway:
    global _gateway
    if _gateway is None:
        provider_name = (settings.model_provider or "kimi").lower()
        if provider_name == "kimi":
            from app.integrations.providers.kimi import KimiProvider

            provider: ModelProvider = KimiProvider()
        elif provider_name == "openai":
            from app.integrations.providers.openai import OpenAIProvider

            provider = OpenAIProvider()
        else:
            provider = ModelProvider()  # type: ignore[abstract]
        _gateway = ModelGateway(provider)
    return _gateway
