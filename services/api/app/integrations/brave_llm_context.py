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
    payload = {
        "query": query,
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
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        return BraveResult(
            status="FAILED",
            provider="BRAVE_LLM_CONTEXT",
            sources=[],
            error=str(exc),
        )

    sources: list[BraveSource] = []
    retrieved_at = datetime.now(tz=timezone.utc)
    raw_sources = data.get("sources") or data.get("results") or []
    for s in raw_sources:
        if not isinstance(s, dict):
            continue
        url = s.get("url") or s.get("source_url") or s.get("link")
        sources.append(
            BraveSource(
                title=s.get("title") or s.get("name"),
                url=url,
                domain=_domain(url),
                excerpt=s.get("excerpt") or s.get("snippet") or s.get("content"),
                retrieved_at=retrieved_at,
            )
        )

    return BraveResult(
        status="COMPLETED",
        provider="BRAVE_LLM_CONTEXT",
        sources=sources,
        raw=data,
    )
