"""Judge layer · model-based per-output verdict.

MVP ships the callable interface + a NEUTRAL stub. The stub
returns `STUB_NEUTRAL` so the Tribunal's classify() knows the
judge wasn't actually consulted · rule-clean outputs reduce to
HONEY by default · rule-failed outputs still get downgraded.

Real judge wiring (Kimi K2.6 · OpenAI gpt-4o) lands next session.
"""
from __future__ import annotations

from typing import Any, Callable


JudgeFn = Callable[..., dict[str, Any]]


def stub_judge(*, task_id: str, output: Any) -> dict[str, Any]:
    """Stub judge · returns NEUTRAL with explicit STUB_NEUTRAL status.

    The Tribunal's classify() detects STUB_NEUTRAL and resolves
    rule-clean outputs to HONEY rather than blocking on judge
    confidence. This keeps MVP runs producing real verdicts
    without falsifying judgment.
    """
    return {
        "verdict": "HONEY",  # treated as "no judge opinion · defer to rules"
        "confidence": 0.0,
        "reasoning": "Judge layer not consulted (MVP stub) · rule-only verdict applies",
        "status": "STUB_NEUTRAL",
    }


def make_judge(provider: str | None = None) -> JudgeFn:
    """Factory for the judge function.

    MVP: only "stub" is implemented. Future providers (kimi, openai,
    local) plug in here.
    """
    if provider in (None, "stub", ""):
        return stub_judge
    raise NotImplementedError(
        f"Judge provider '{provider}' not implemented in MVP · only 'stub' is available"
    )
