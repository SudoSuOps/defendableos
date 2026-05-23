"""Judge layer · model-based per-output verdict.

Per docs/TRIBUNAL_GRADING_DOCTRINE.md:
  · Rule layer runs first (deterministic)
  · Judge layer runs second (model-based with disclosed confidence)
  · Rule layer can ONLY downgrade · never upgrade

Providers wired:
  · stub          NEUTRAL fallback (no model call)
  · kimi          Moonshot Kimi K2.6 · OpenAI-compatible API · typed tool call
                  · MUST use temperature=1 per Kimi quirk
  · openai        OpenAI gpt-4o · structured outputs via tool call
  · auto          Prefer Kimi if configured · else OpenAI · else stub

Keys read from local .env via the edge-agent _env helper · never logged,
never returned in receipts. Model name + provider ARE recorded in
verdict metadata for reproducibility.
"""
from __future__ import annotations

import json
from typing import Any, Callable

import httpx

from . import _env


JudgeFn = Callable[..., dict[str, Any]]


# ─── Conservative-vote ordering · doctrine ────────────────────────────────


_VERDICT_RANK = {"HONEY": 0, "JELLY": 1, "PROPOLIS": 2}


def _most_conservative(verdicts: list[str]) -> str:
    """Return the most-conservative verdict (highest rank).

    Doctrine: ensemble layer should bias toward downgrade · same as the
    rule layer. PROPOLIS > JELLY > HONEY. When judges disagree, the
    safer verdict wins · operators get protection from the strictest
    reviewer.
    """
    if not verdicts:
        return "HONEY"
    return max(verdicts, key=lambda v: _VERDICT_RANK.get(v, 0))


# ─── Typed tool contract for HONEY/JELLY/PROPOLIS ────────────────────────


_VERDICT_TOOL_NAME = "record_tribunal_verdict"
_VERDICT_TOOL_DESCRIPTION = (
    "Record a Tribunal verdict for the supplied agent output. The verdict "
    "MUST be one of HONEY (correct · sourced · schema-valid · commercially "
    "usable) · JELLY (partially useful · missing support · structure · or "
    "confidence discipline) · PROPOLIS (material hallucination · unsafe "
    "action · fabricated source · bad math · compliance failure). Confidence "
    "is 0.0-1.0. Reasoning is one to three sentences."
)
_VERDICT_TOOL_PARAMETERS = {
    "type": "object",
    "required": ["verdict", "confidence", "reasoning"],
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["HONEY", "JELLY", "PROPOLIS"],
            "description": "Tribunal classification of the output",
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "How confident you are in this verdict, 0.0-1.0",
        },
        "reasoning": {
            "type": "string",
            "minLength": 20,
            "maxLength": 800,
            "description": "1-3 sentences explaining the verdict · cite specific output facts",
        },
    },
    "additionalProperties": False,
}


def _verdict_tool_payload() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": _VERDICT_TOOL_NAME,
            "description": _VERDICT_TOOL_DESCRIPTION,
            "parameters": _VERDICT_TOOL_PARAMETERS,
        },
    }


_SYSTEM_PROMPT = (
    "You are the Defendable Tribunal · per docs/TRIBUNAL_GRADING_DOCTRINE.md. "
    "You classify per-output verdicts as HONEY · JELLY · or PROPOLIS using "
    "the supplied tool. You operate AFTER deterministic rule checks have "
    "already run · your job is to assess whether the output is complete, "
    "well-reasoned, appropriately scoped, and commercially usable.\n\n"
    "HONEY = correct, sourced, schema-valid, commercially usable as-is.\n"
    "JELLY = partially useful but missing support, structure, or confidence discipline.\n"
    "PROPOLIS = material hallucination, unsafe action, fabricated source, "
    "bad math, or compliance failure.\n\n"
    "Always call the record_tribunal_verdict tool. Never respond in prose. "
    "Never invent facts not in the supplied output."
)


def _build_user_payload(task_id: str, output: Any, task_context: dict | None) -> str:
    return (
        f"Task id: {task_id}\n\n"
        f"Task context (the prompt + first lines of supplied materials, if any):\n"
        f"{json.dumps(task_context or {}, indent=2)[:2000]}\n\n"
        f"Agent output to classify:\n"
        f"{json.dumps(output, indent=2)[:3000]}\n\n"
        "Classify the verdict using the record_tribunal_verdict tool."
    )


# ─── Stub provider ────────────────────────────────────────────────────────


def stub_judge(*, task_id: str, output: Any, task_context: dict | None = None) -> dict[str, Any]:
    return {
        "verdict": "HONEY",
        "confidence": 0.0,
        "reasoning": "Judge layer not consulted (stub) · rule-only verdict applies",
        "status": "STUB_NEUTRAL",
        "provider": "stub",
        "model": "none",
    }


# ─── Kimi K2.6 provider ────────────────────────────────────────────────────


def _kimi_judge(*, task_id: str, output: Any, task_context: dict | None = None) -> dict[str, Any]:
    api_key = _env.get("MOONSHOT_API_KEY")
    base_url = _env.get("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")
    model = _env.get("MOONSHOT_MODEL", "kimi-k2-thinking")
    if not api_key:
        return {**stub_judge(task_id=task_id, output=output), "status": "UNAVAILABLE_NO_KEY"}

    body = {
        "model": model,
        # Kimi quirk: temperature MUST be 1 · documented in
        # docs/DEFENDABLEOS_TOOL_USE_DOCTRINE memory + verified in production
        "temperature": 1,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_payload(task_id, output, task_context)},
        ],
        "tools": [_verdict_tool_payload()],
        # Kimi K2.6 quirk: forced tool_choice is incompatible with thinking-enabled
        # models. Auto + system-prompt instruction works · only one tool is provided
        # so the model picks ours.
        "tool_choice": "auto",
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=180.0) as client:
            r = client.post(f"{base_url}/chat/completions", headers=headers, json=body)
        if r.status_code >= 400:
            return {
                "verdict": "HONEY",
                "confidence": 0.0,
                "reasoning": f"Judge call failed · HTTP {r.status_code} · rule-only verdict applies",
                "status": f"FAILED_HTTP_{r.status_code}",
                "provider": "kimi",
                "model": model,
                "error_excerpt": r.text[:200],
            }
        data = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {
            "verdict": "HONEY",
            "confidence": 0.0,
            "reasoning": f"Judge call exception: {type(exc).__name__} · rule-only verdict applies",
            "status": "FAILED_EXCEPTION",
            "provider": "kimi",
            "model": model,
        }

    return _parse_tool_response(data, provider="kimi", model=model)


# ─── OpenAI gpt-4o provider ───────────────────────────────────────────────


def _openai_judge(*, task_id: str, output: Any, task_context: dict | None = None) -> dict[str, Any]:
    api_key = _env.get("OPENAI_API_KEY")
    base_url = _env.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = _env.get("OPENAI_MODEL", "gpt-4o")
    if not api_key:
        return {**stub_judge(task_id=task_id, output=output), "status": "UNAVAILABLE_NO_KEY"}

    body = {
        "model": model,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_payload(task_id, output, task_context)},
        ],
        "tools": [_verdict_tool_payload()],
        "tool_choice": {"type": "function", "function": {"name": _VERDICT_TOOL_NAME}},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    org = _env.get("OPENAI_ORGANIZATION")
    if org:
        headers["OpenAI-Organization"] = org
    try:
        with httpx.Client(timeout=180.0) as client:
            r = client.post(f"{base_url}/chat/completions", headers=headers, json=body)
        if r.status_code >= 400:
            return {
                "verdict": "HONEY",
                "confidence": 0.0,
                "reasoning": f"Judge call failed · HTTP {r.status_code} · rule-only verdict applies",
                "status": f"FAILED_HTTP_{r.status_code}",
                "provider": "openai",
                "model": model,
                "error_excerpt": r.text[:200],
            }
        data = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {
            "verdict": "HONEY",
            "confidence": 0.0,
            "reasoning": f"Judge call exception: {type(exc).__name__} · rule-only verdict applies",
            "status": "FAILED_EXCEPTION",
            "provider": "openai",
            "model": model,
        }
    return _parse_tool_response(data, provider="openai", model=model)


# ─── Ensemble judge · multi-model parallel verdict ───────────────────────


def _ensemble_judge(*, task_id: str, output: Any, task_context: dict | None = None) -> dict[str, Any]:
    """Call every configured provider in parallel · vote via most-conservative.

    Doctrine:
    - Run all available providers simultaneously (ThreadPoolExecutor)
    - Each returns a verdict + confidence + reasoning
    - Consensus = most-conservative (PROPOLIS > JELLY > HONEY)
    - When judges DISAGREE, surface the disagreement in metadata
    - Confidence = mean of per-judge confidences for the winning verdict
    - Defense-in-depth: a single permissive judge cannot rescue a flagged
      output · matches the rule-layer doctrine ("can only downgrade")
    """
    import concurrent.futures as _cf

    providers: list[tuple[str, JudgeFn]] = []
    if _env.get("MOONSHOT_API_KEY"):
        providers.append(("kimi", _kimi_judge))
    if _env.get("OPENAI_API_KEY"):
        providers.append(("openai", _openai_judge))

    if not providers:
        return {**stub_judge(task_id=task_id, output=output), "status": "UNAVAILABLE_NO_PROVIDERS"}
    if len(providers) == 1:
        # Only one provider configured · return single-judge result with ensemble metadata
        name, fn = providers[0]
        single = fn(task_id=task_id, output=output, task_context=task_context)
        single["ensemble_metadata"] = {
            "providers_attempted": [name],
            "providers_succeeded": [name] if single.get("status") == "RAN" else [],
            "consensus_basis": "single_provider_no_ensemble",
            "judges_agreed": True,
        }
        single["provider"] = f"ensemble({name})"
        return single

    # Parallel fan-out
    results: dict[str, dict[str, Any]] = {}
    with _cf.ThreadPoolExecutor(max_workers=len(providers)) as ex:
        future_to_name = {
            ex.submit(fn, task_id=task_id, output=output, task_context=task_context): name
            for name, fn in providers
        }
        for fut in _cf.as_completed(future_to_name):
            name = future_to_name[fut]
            try:
                results[name] = fut.result()
            except Exception as exc:  # noqa: BLE001
                results[name] = {
                    "verdict": "HONEY",
                    "confidence": 0.0,
                    "reasoning": f"Provider {name} raised {type(exc).__name__}",
                    "status": "FAILED_EXCEPTION",
                    "provider": name,
                    "model": "(unknown)",
                }

    succeeded = [n for n, r in results.items() if r.get("status") == "RAN"]
    failed = [n for n in results if n not in succeeded]

    if not succeeded:
        # All providers failed · fall back to stub HONEY (rule-only)
        return {
            "verdict": "HONEY",
            "confidence": 0.0,
            "reasoning": f"All ensemble providers failed · {failed} · rule-only verdict applies",
            "status": "FAILED_ALL_PROVIDERS",
            "provider": "ensemble",
            "model": "+".join(failed),
            "ensemble_metadata": {
                "providers_attempted": list(results.keys()),
                "providers_succeeded": [],
                "providers_failed": failed,
                "per_provider_status": {n: r.get("status") for n, r in results.items()},
            },
        }

    # Tally verdicts from successful providers
    verdicts = [results[n]["verdict"] for n in succeeded]
    consensus_verdict = _most_conservative(verdicts)
    agreed = all(v == consensus_verdict for v in verdicts)

    # Confidence · mean of providers that returned the winning verdict
    matching_confs = [
        float(results[n].get("confidence", 0.0))
        for n in succeeded
        if results[n]["verdict"] == consensus_verdict
    ]
    consensus_confidence = (
        round(sum(matching_confs) / len(matching_confs), 3) if matching_confs else 0.0
    )

    # Compose reasoning · pull the winning-verdict reasoning from each agreeing provider
    reasoning_parts = []
    for n in succeeded:
        r = results[n]
        marker = "✓" if r["verdict"] == consensus_verdict else "✗"
        reasoning_parts.append(
            f"[{marker} {n} · {r['verdict']} · {r.get('confidence', 0):.2f}] {r.get('reasoning', '')[:200]}"
        )
    composed = " | ".join(reasoning_parts)[:800]

    return {
        "verdict": consensus_verdict,
        "confidence": consensus_confidence,
        "reasoning": composed,
        "status": "RAN",
        "provider": "ensemble",
        "model": "+".join(succeeded),
        "ensemble_metadata": {
            "providers_attempted": list(results.keys()),
            "providers_succeeded": succeeded,
            "providers_failed": failed,
            "per_provider_verdict": {n: results[n]["verdict"] for n in succeeded},
            "per_provider_confidence": {n: results[n].get("confidence", 0) for n in succeeded},
            "per_provider_model": {n: results[n].get("model") for n in succeeded},
            "consensus_basis": "unanimous_agreement" if agreed else "most_conservative_vote",
            "judges_agreed": agreed,
        },
    }


# ─── Shared tool-response parser ──────────────────────────────────────────


def _parse_tool_response(data: dict, *, provider: str, model: str) -> dict[str, Any]:
    """Extract the tool call · validate enum + bounds · fail safe to stub."""
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    tool_calls = message.get("tool_calls") or []
    if not tool_calls:
        return {
            "verdict": "HONEY",
            "confidence": 0.0,
            "reasoning": "Judge returned no tool call · rule-only verdict applies",
            "status": "NO_TOOL_CALL",
            "provider": provider,
            "model": model,
        }

    fn = (tool_calls[0].get("function") or {})
    raw_args = fn.get("arguments") or "{}"
    try:
        args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
    except json.JSONDecodeError:
        return {
            "verdict": "HONEY",
            "confidence": 0.0,
            "reasoning": "Judge tool-call arguments did not parse · rule-only verdict applies",
            "status": "ARGS_PARSE_FAIL",
            "provider": provider,
            "model": model,
        }

    verdict = args.get("verdict", "").upper()
    confidence = args.get("confidence", 0.0)
    reasoning = args.get("reasoning", "")

    # Enum guard · refuse out-of-contract verdicts
    if verdict not in {"HONEY", "JELLY", "PROPOLIS"}:
        return {
            "verdict": "HONEY",
            "confidence": 0.0,
            "reasoning": f"Judge returned out-of-contract verdict '{verdict}' · downgraded to rule-only",
            "status": "OUT_OF_CONTRACT",
            "provider": provider,
            "model": model,
        }

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    return {
        "verdict": verdict,
        "confidence": round(confidence, 3),
        "reasoning": (reasoning or "")[:800],
        "status": "RAN",
        "provider": provider,
        "model": model,
    }


# ─── Factory ───────────────────────────────────────────────────────────────


def make_judge(provider: str | None = None) -> JudgeFn:
    """Resolve a provider id to a JudgeFn.

    'auto' picks the first configured provider · Kimi > OpenAI > stub.
    """
    p = (provider or "stub").lower()
    if p == "auto":
        if _env.get("MOONSHOT_API_KEY"):
            return _kimi_judge
        if _env.get("OPENAI_API_KEY"):
            return _openai_judge
        return stub_judge
    if p in ("stub", "", "none"):
        return stub_judge
    if p == "kimi":
        return _kimi_judge
    if p == "openai":
        return _openai_judge
    if p == "ensemble":
        return _ensemble_judge
    raise ValueError(f"Unknown judge provider: {provider!r}")


def judge_provider_summary(provider: str | None) -> dict[str, Any]:
    """Public-safe summary of which provider/model would be used · no key values."""
    p = (provider or "stub").lower()
    if p == "auto":
        if _env.get("MOONSHOT_API_KEY"):
            return {"provider": "kimi", "model": _env.get("MOONSHOT_MODEL"), "configured": True}
        if _env.get("OPENAI_API_KEY"):
            return {"provider": "openai", "model": _env.get("OPENAI_MODEL"), "configured": True}
        return {"provider": "stub", "model": "none", "configured": False}
    if p == "kimi":
        return {"provider": "kimi", "model": _env.get("MOONSHOT_MODEL"), "configured": bool(_env.get("MOONSHOT_API_KEY"))}
    if p == "openai":
        return {"provider": "openai", "model": _env.get("OPENAI_MODEL"), "configured": bool(_env.get("OPENAI_API_KEY"))}
    if p == "ensemble":
        return {
            "provider": "ensemble",
            "model": "+".join(
                [
                    n for n, k in [("kimi", "MOONSHOT_API_KEY"), ("openai", "OPENAI_API_KEY")]
                    if _env.get(k)
                ]
            ) or "none",
            "configured": bool(_env.get("MOONSHOT_API_KEY")) or bool(_env.get("OPENAI_API_KEY")),
            "consensus_rule": "most_conservative (PROPOLIS > JELLY > HONEY)",
        }
    return {"provider": "stub", "model": "none", "configured": False}
