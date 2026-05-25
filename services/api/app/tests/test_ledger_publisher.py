"""LedgerPublisher unit tests · GitHub Contents API mocked via httpx MockTransport."""
from __future__ import annotations

import base64
import json
from typing import Any

import httpx
import pytest

from app.services.ledger_publisher import LedgerPublisher


def _b64(obj: Any) -> str:
    return base64.b64encode(
        json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    ).decode("ascii")


def _make_publisher_with_transport(transport: httpx.MockTransport) -> LedgerPublisher:
    pub = LedgerPublisher(
        token="ghp_test_token",
        repo="SudoSuOps/defendable-ledger",
        branch="main",
        public_url_base="https://defendableledger.com",
    )
    # Force every Client() opened inside the publisher to use our mock transport.
    orig_client_init = httpx.Client.__init__

    def patched_init(self, *args, **kwargs):
        kwargs.pop("transport", None)
        orig_client_init(self, *args, transport=transport, **kwargs)

    httpx.Client.__init__ = patched_init  # type: ignore[assignment]
    pub._test_cleanup = lambda: setattr(httpx.Client, "__init__", orig_client_init)  # type: ignore[attr-defined]
    return pub


def test_not_configured_returns_unconfigured():
    pub = LedgerPublisher(token="", repo="", branch="main", public_url_base="https://defendableledger.com")
    assert not pub.is_configured()
    result = pub.publish_deed(
        slug="x", deed_reference="X", deed_json={}, public_payload={}, deed_version=1
    )
    assert not result.ok
    assert result.error == "LEDGER_PUBLISHER_NOT_CONFIGURED"


def test_publish_deed_happy_path_creates_both_files():
    state = {"index_sha": "abc123", "deed_sha": None, "puts": []}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET":
            if path.endswith("/contents/public/records/index.json"):
                return httpx.Response(
                    200,
                    json={
                        "sha": state["index_sha"],
                        "content": _b64([{"natural_id": "OLD-DEED", "created_at": "2020-01-01T00:00:00Z"}]),
                    },
                )
            return httpx.Response(404)
        if request.method == "PUT":
            state["puts"].append(path)
            commit_sha = "c0ffee" + str(len(state["puts"]))
            return httpx.Response(201, json={"commit": {"sha": commit_sha}})
        return httpx.Response(500)

    pub = _make_publisher_with_transport(httpx.MockTransport(handler))
    try:
        result = pub.publish_deed(
            slug="deed-001",
            deed_reference="DEED-001",
            deed_json={"foo": "bar"},
            public_payload={"foo": "bar"},
            record_hash="d3adbe3f" * 8,
            deed_version=1,
        )
    finally:
        pub._test_cleanup()  # type: ignore[attr-defined]

    assert result.ok
    assert result.public_url == "https://defendableledger.com/records/deeds/deed-001.json"
    # 2 PUTs · the deed and the index (existing index is updated)
    assert any("contents/public/records/deeds/deed-001.json" in p for p in state["puts"])
    assert any("contents/public/records/index.json" in p for p in state["puts"])


def test_publish_deed_creates_first_index_when_missing():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            # No existing deed · no existing index
            return httpx.Response(404)
        if request.method == "PUT":
            return httpx.Response(201, json={"commit": {"sha": "abcdef0"}})
        return httpx.Response(500)

    pub = _make_publisher_with_transport(httpx.MockTransport(handler))
    try:
        result = pub.publish_deed(
            slug="first-deed",
            deed_reference="FIRST",
            deed_json={},
            public_payload={"first": True},
            deed_version=1,
        )
    finally:
        pub._test_cleanup()  # type: ignore[attr-defined]

    assert result.ok
    assert result.public_url.endswith("/records/deeds/first-deed.json")


def test_publish_deed_returns_error_when_deed_put_fails():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(404)
        if request.method == "PUT":
            return httpx.Response(503, text="rate limited")
        return httpx.Response(500)

    pub = _make_publisher_with_transport(httpx.MockTransport(handler))
    try:
        result = pub.publish_deed(
            slug="boom", deed_reference="BOOM", deed_json={}, public_payload={}, deed_version=1
        )
    finally:
        pub._test_cleanup()  # type: ignore[attr-defined]

    assert not result.ok
    assert "DEED_UPSERT_FAILED" in (result.error or "")


def test_publish_idempotent_replaces_same_natural_id():
    """Re-publishing the same slug should replace the existing index entry, not duplicate."""
    state = {"index_data": [{"natural_id": "deed-X", "created_at": "2020-01-01T00:00:00Z"}], "puts": []}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET":
            if path.endswith("/contents/public/records/index.json"):
                return httpx.Response(
                    200,
                    json={"sha": "idx-sha", "content": _b64(state["index_data"])},
                )
            return httpx.Response(404)
        if request.method == "PUT":
            if path.endswith("/contents/public/records/index.json"):
                body = json.loads(request.content)
                state["puts"].append(json.loads(base64.b64decode(body["content"]).decode()))
            return httpx.Response(201, json={"commit": {"sha": "ok"}})
        return httpx.Response(500)

    pub = _make_publisher_with_transport(httpx.MockTransport(handler))
    try:
        result = pub.publish_deed(
            slug="deed-X",
            deed_reference="DEED-X",
            deed_json={},
            public_payload={"v": 2},
            deed_version=2,
        )
    finally:
        pub._test_cleanup()  # type: ignore[attr-defined]

    assert result.ok
    # The index after publish should still have exactly ONE entry for deed-X · not two
    index_after = state["puts"][-1]
    deed_x_entries = [e for e in index_after if e["natural_id"] == "deed-X"]
    assert len(deed_x_entries) == 1
    assert deed_x_entries[0]["deed_version"] == 2


def test_get_blob_sha_returns_none_on_404():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    pub = _make_publisher_with_transport(httpx.MockTransport(handler))
    try:
        sha = pub._get_blob_sha("nonexistent/path.json")
    finally:
        pub._test_cleanup()  # type: ignore[attr-defined]
    assert sha is None
