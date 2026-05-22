"""Brave LLM Context API connector · public market research rail.

Server-side only. The Brave API key never reaches the browser.

When BRAVE_API_KEY is unset the connector is "not configured" and returns
an empty source list along with a clear status flag. This keeps the UI
honest — no fake live results.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings


@dataclass
class BraveSource:
    title: str | None
    url: str | None
    domain: str | None
    excerpt: str | None
    retrieved_at: datetime


@dataclass
class BraveResult:
    status: str  # COMPLETED | NOT_CONFIGURED | FAILED
    provider: str
    sources: list[BraveSource]
    error: str | None = None
    raw: dict[str, Any] | None = None


def _domain(url: str | None) -> str | None:
    if not url:
        return None
    try:
        return urlparse(url).netloc or None
    except Exception:
        return None


def is_configured() -> bool:
    return bool(settings.brave_api_key)


def search(
    query: str,
    maximum_number_of_urls: int = 10,
    maximum_number_of_tokens: int = 8192,
    context_threshold_mode: str = "balanced",
    timeout_seconds: float = 25.0,
) -> BraveResult:
    if not is_configured():
        return BraveResult(
            status="NOT_CONFIGURED",
            provider="BRAVE_LLM_CONTEXT",
            sources=[],
            error="BRAVE_API_KEY is not set",
        )

    headers = {
        "X-Subscription-Token": settings.brave_api_key,
        "Accept": "application/json",
    }
    # Brave's LLM Context API uses `q` (not `query`). Per-call params:
    #   q, maximum_number_of_urls, maximum_number_of_tokens, context_threshold_mode
    payload = {
        "q": query,
        "maximum_number_of_urls": maximum_number_of_urls,
        "maximum_number_of_tokens": maximum_number_of_tokens,
        "context_threshold_mode": context_threshold_mode,
    }

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            resp = client.post(
                settings.brave_llm_context_url,
                headers=headers,
                json=payload,
            )
            if resp.status_code >= 400:
                return BraveResult(
                    status="FAILED",
                    provider="BRAVE_LLM_CONTEXT",
                    sources=[],
                    error=f"Brave error {resp.status_code}: {resp.text[:400]}",
                )
            data = resp.json()
    except Exception as exc:
        return BraveResult(
            status="FAILED",
            provider="BRAVE_LLM_CONTEXT",
            sources=[],
            error=str(exc),
        )

    # Brave response shape:
    #   { "sources": { url: {title, hostname, age} },
    #     "grounding": { "generic": [{url, title, snippets[]}], "map": [...] } }
    # `grounding.generic` is the most useful structure · each entry already
    # has the URL, title and a list of snippet strings (often JSON-flavoured).
    retrieved_at = datetime.now(tz=timezone.utc)
    sources: list[BraveSource] = []
    grounding = data.get("grounding") or {}
    generic = grounding.get("generic") or []
    for entry in generic:
        if not isinstance(entry, dict):
            continue
        url = entry.get("url")
        title = entry.get("title")
        snippets = entry.get("snippets") or []
        # Join the first few snippets into a single excerpt · capped for storage.
        excerpt_parts: list[str] = []
        for sn in snippets[:6]:
            if isinstance(sn, str):
                excerpt_parts.append(sn)
            elif isinstance(sn, dict):
                # Some snippets arrive as dict {title, table, …} · stringify.
                excerpt_parts.append(__import__("json").dumps(sn, sort_keys=True)[:1200])
        excerpt = "\n\n".join(excerpt_parts)[:4000]
        sources.append(
            BraveSource(
                title=title,
                url=url,
                domain=_domain(url),
                excerpt=excerpt,
                retrieved_at=retrieved_at,
            )
        )

    return BraveResult(
        status="COMPLETED",
        provider="BRAVE_LLM_CONTEXT",
        sources=sources,
        raw=data,
    )
