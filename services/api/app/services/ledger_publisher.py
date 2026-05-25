"""Publish issued deeds to the public defendable-ledger repo via the GitHub Contents API.

Doctrine: every published deed lands at https://defendableledger.com — single
canonical surface for books-and-records. The smash-side spine publishes there
today via local git; this service does the same from the Fly app without
cloning the repo locally. Two parallel rails can write into the same repo
because record_id prefixes don't collide (smash mints DRR-/TRIB-/SJP-/DLR-,
Fly mints whatever deed.deed_reference resolves to).

Fail-OPEN: if the publisher is unconfigured (missing PAT/repo) or any API
call fails, this service returns None and logs a warning. The deed remains
in Postgres as the source of truth · the public surface eventually catches
up via a retry or a periodic reconciliation worker. Production rail is
never blocked.

Hot path · invoked as a FastAPI BackgroundTask so /publish returns immediately.
"""
from __future__ import annotations

import base64
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_GH_API_BASE = "https://api.github.com"
_INDEX_PATH = "public/records/index.json"
_RECORDS_DIR = "public/records/deeds"  # deed records live under /deeds; receipts/verdicts/pairs from smash are siblings


@dataclass
class PublishResult:
    ok: bool
    public_url: Optional[str] = None
    commit_sha: Optional[str] = None
    error: Optional[str] = None


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class LedgerPublisher:
    """Publishes deed JSONs into the defendable-ledger repo via GH Contents API."""

    def __init__(
        self,
        token: Optional[str] = None,
        repo: Optional[str] = None,
        branch: Optional[str] = None,
        public_url_base: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.token = token or settings.github_publish_token
        self.repo = repo or settings.github_publish_repo
        self.branch = branch or settings.github_publish_branch
        self.public_url_base = public_url_base or settings.defendable_ledger_public_url
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.token) and bool(self.repo)

    def publish_deed(
        self,
        *,
        slug: str,
        deed_reference: str,
        deed_json: dict,
        public_payload: dict,
        record_hash: Optional[str] = None,
        deed_version: int = 1,
    ) -> PublishResult:
        """Publish a single deed.

        Writes:
          - /public/records/deeds/{slug}.json  → the public deed payload
          - /public/records/index.json         → appended with this deed's metadata

        Returns PublishResult with the canonical public URL on success.
        """
        if not self.is_configured():
            logger.warning("ledger publisher not configured · skipping deed=%s", slug)
            return PublishResult(ok=False, error="LEDGER_PUBLISHER_NOT_CONFIGURED")

        record_path = f"{_RECORDS_DIR}/{slug}.json"
        record_body = _canonical_json_bytes(public_payload)

        # 1. Upsert the deed JSON.
        try:
            commit_sha = self._upsert_file(
                path=record_path,
                body=record_body,
                message=f"Publish deed {deed_reference} · slug {slug} · v{deed_version}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("ledger publisher · deed upsert failed slug=%s", slug)
            return PublishResult(ok=False, error=f"DEED_UPSERT_FAILED: {exc}"[:300])

        # 2. Append to index.json (retry on SHA conflict from concurrent writers).
        index_entry = {
            "natural_id": slug,
            "deed_reference": deed_reference,
            "record_type": "DEED",
            "record_sha256": record_hash or "",
            "deed_version": deed_version,
            "path": f"records/deeds/{slug}.json",
            "created_at": _utc_iso(),
            "issued_by": "defendableos-api",
        }
        try:
            self._append_index_entry(index_entry, retries=3)
        except Exception as exc:  # noqa: BLE001
            logger.exception("ledger publisher · index append failed slug=%s", slug)
            return PublishResult(
                ok=False,
                public_url=self._public_url_for(slug),
                commit_sha=commit_sha,
                error=f"INDEX_APPEND_FAILED: {exc}"[:300],
            )

        return PublishResult(
            ok=True,
            public_url=self._public_url_for(slug),
            commit_sha=commit_sha,
        )

    # ------------------------------------------------------------------ internals

    def _public_url_for(self, slug: str) -> str:
        base = self.public_url_base.rstrip("/")
        return f"{base}/records/deeds/{slug}.json"

    def _gh_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _upsert_file(self, *, path: str, body: bytes, message: str) -> str:
        """PUT /repos/{owner}/{repo}/contents/{path} · returns commit SHA."""
        existing_sha = self._get_blob_sha(path)
        payload: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(body).decode("ascii"),
            "branch": self.branch,
        }
        if existing_sha:
            payload["sha"] = existing_sha
        with httpx.Client(timeout=self.timeout) as client:
            r = client.put(
                f"{_GH_API_BASE}/repos/{self.repo}/contents/{path}",
                headers=self._gh_headers(),
                json=payload,
            )
            if r.status_code not in (200, 201):
                raise RuntimeError(f"GH PUT {path} failed {r.status_code}: {r.text[:300]}")
            data = r.json()
            return ((data.get("commit") or {}).get("sha") or "")[:40]

    def _get_blob_sha(self, path: str) -> Optional[str]:
        """GET /repos/{owner}/{repo}/contents/{path} · returns SHA or None if missing."""
        with httpx.Client(timeout=self.timeout) as client:
            r = client.get(
                f"{_GH_API_BASE}/repos/{self.repo}/contents/{path}",
                headers=self._gh_headers(),
                params={"ref": self.branch},
            )
            if r.status_code == 404:
                return None
            if r.status_code != 200:
                raise RuntimeError(f"GH GET {path} failed {r.status_code}: {r.text[:300]}")
            return (r.json() or {}).get("sha")

    def _get_index(self) -> tuple[list[dict], Optional[str]]:
        """Return (entries, sha) for index.json · ([], None) if it does not exist yet."""
        with httpx.Client(timeout=self.timeout) as client:
            r = client.get(
                f"{_GH_API_BASE}/repos/{self.repo}/contents/{_INDEX_PATH}",
                headers=self._gh_headers(),
                params={"ref": self.branch},
            )
            if r.status_code == 404:
                return ([], None)
            if r.status_code != 200:
                raise RuntimeError(f"GH GET index failed {r.status_code}: {r.text[:300]}")
            data = r.json() or {}
            content = data.get("content") or ""
            sha = data.get("sha")
            try:
                decoded = base64.b64decode(content).decode("utf-8") if content else "[]"
                entries = json.loads(decoded)
                if not isinstance(entries, list):
                    entries = []
            except Exception:
                entries = []
            return (entries, sha)

    def _append_index_entry(self, new_entry: dict, retries: int = 3) -> None:
        """Append + sort + PUT. Retries on SHA conflict (concurrent writers)."""
        last_exc: Optional[Exception] = None
        for attempt in range(retries):
            try:
                entries, sha = self._get_index()
                # idempotent: replace any prior entry with the same natural_id
                seen = {e.get("natural_id") for e in entries}
                if new_entry["natural_id"] in seen:
                    entries = [
                        new_entry if e.get("natural_id") == new_entry["natural_id"] else e
                        for e in entries
                    ]
                else:
                    entries.append(new_entry)
                entries.sort(key=lambda e: (e.get("created_at") or "", e.get("natural_id") or ""))
                body = _canonical_json_bytes(entries)
                payload: dict[str, Any] = {
                    "message": f"Update index · +{new_entry['natural_id']}",
                    "content": base64.b64encode(body).decode("ascii"),
                    "branch": self.branch,
                }
                if sha:
                    payload["sha"] = sha
                with httpx.Client(timeout=self.timeout) as client:
                    r = client.put(
                        f"{_GH_API_BASE}/repos/{self.repo}/contents/{_INDEX_PATH}",
                        headers=self._gh_headers(),
                        json=payload,
                    )
                    if r.status_code in (200, 201):
                        return
                    if r.status_code == 409 and attempt < retries - 1:
                        # SHA stale · re-read and retry
                        time.sleep(0.3 * (attempt + 1))
                        continue
                    raise RuntimeError(f"GH PUT index failed {r.status_code}: {r.text[:300]}")
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt >= retries - 1:
                    break
                time.sleep(0.3 * (attempt + 1))
        if last_exc:
            raise last_exc


def _canonical_json_bytes(obj: Any) -> bytes:
    """Sorted-keys, 2-space indent · so git diffs are readable and stable."""
    return (
        json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    )


_publisher_singleton: Optional[LedgerPublisher] = None


def get_ledger_publisher() -> LedgerPublisher:
    global _publisher_singleton
    if _publisher_singleton is None:
        _publisher_singleton = LedgerPublisher()
    return _publisher_singleton
