"""S3 connection settings must resolve from BOTH naming conventions:

  · Tigris (Fly native) auto-injects: AWS_ENDPOINT_URL_S3 · AWS_ACCESS_KEY_ID ·
    AWS_SECRET_ACCESS_KEY · AWS_REGION · BUCKET_NAME (via `flyctl storage create`)
  · MinIO / local dev / explicit prod overrides use: S3_ENDPOINT_URL ·
    S3_ACCESS_KEY_ID · S3_SECRET_ACCESS_KEY · S3_REGION · S3_PRIVATE_EVIDENCE_BUCKET

If both are set the AWS_* / BUCKET_NAME values win (operator-injected
production credentials take precedence over local dev defaults).

This guarantees `flyctl storage create` is the only operator step needed
to flip CLAW_BAKERY_STORAGE_DRIVER=s3 from local-ephemeral to durable.
"""
from __future__ import annotations

import importlib

import pytest


def _fresh_settings(monkeypatch, env: dict[str, str]):
    """Reload config to pick up monkeypatched env vars (lru_cache + class
    defaults capture at import time)."""
    # Clear every alias we care about so we don't inherit from the test
    # process environment.
    for k in (
        "AWS_ENDPOINT_URL_S3", "S3_ENDPOINT_URL",
        "AWS_ACCESS_KEY_ID",   "S3_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY", "S3_SECRET_ACCESS_KEY",
        "AWS_REGION",          "S3_REGION",
        "BUCKET_NAME",         "S3_PRIVATE_EVIDENCE_BUCKET",
    ):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    from app.core import config as _config
    importlib.reload(_config)
    _config.get_settings.cache_clear()
    return _config.get_settings()


def test_tigris_only_names_resolve(monkeypatch):
    s = _fresh_settings(monkeypatch, {
        "AWS_ENDPOINT_URL_S3":   "https://fly.storage.tigris.dev",
        "AWS_ACCESS_KEY_ID":     "tid_demo",
        "AWS_SECRET_ACCESS_KEY": "tsec_demo",
        "AWS_REGION":            "auto",
        "BUCKET_NAME":           "defendableos-private-evidence",
    })
    assert s.s3_endpoint_url == "https://fly.storage.tigris.dev"
    assert s.s3_access_key_id == "tid_demo"
    assert s.s3_secret_access_key == "tsec_demo"
    assert s.s3_region == "auto"
    assert s.s3_private_evidence_bucket == "defendableos-private-evidence"


def test_s3_only_names_resolve(monkeypatch):
    s = _fresh_settings(monkeypatch, {
        "S3_ENDPOINT_URL":            "http://localhost:9000",
        "S3_ACCESS_KEY_ID":           "minioadmin",
        "S3_SECRET_ACCESS_KEY":       "minioadmin",
        "S3_REGION":                  "us-east-1",
        "S3_PRIVATE_EVIDENCE_BUCKET": "local-bucket",
    })
    assert s.s3_endpoint_url == "http://localhost:9000"
    assert s.s3_access_key_id == "minioadmin"
    assert s.s3_secret_access_key == "minioadmin"
    assert s.s3_region == "us-east-1"
    assert s.s3_private_evidence_bucket == "local-bucket"


def test_aws_wins_over_s3_when_both_set(monkeypatch):
    """Operator-injected production credentials (AWS_/BUCKET_NAME) take
    precedence over any S3_-prefixed dev defaults that may still be set."""
    s = _fresh_settings(monkeypatch, {
        # Both sets present
        "AWS_ENDPOINT_URL_S3":   "https://fly.storage.tigris.dev",
        "S3_ENDPOINT_URL":       "http://localhost:9000",
        "AWS_ACCESS_KEY_ID":     "prod_key",
        "S3_ACCESS_KEY_ID":      "dev_key",
        "AWS_SECRET_ACCESS_KEY": "prod_secret",
        "S3_SECRET_ACCESS_KEY":  "dev_secret",
        "AWS_REGION":            "auto",
        "S3_REGION":             "us-east-1",
        "BUCKET_NAME":           "prod-bucket",
        "S3_PRIVATE_EVIDENCE_BUCKET": "dev-bucket",
    })
    assert s.s3_endpoint_url == "https://fly.storage.tigris.dev"
    assert s.s3_access_key_id == "prod_key"
    assert s.s3_secret_access_key == "prod_secret"
    assert s.s3_region == "auto"
    assert s.s3_private_evidence_bucket == "prod-bucket"


def test_defaults_preserved_when_nothing_set(monkeypatch):
    """Backwards-compatibility: with neither naming present, the historical
    MinIO defaults remain so local-dev `pytest` continues to pass without
    a .env file."""
    s = _fresh_settings(monkeypatch, {})
    assert s.s3_endpoint_url == "http://localhost:9000"
    assert s.s3_access_key_id == "minioadmin"
    assert s.s3_secret_access_key == "minioadmin"
    assert s.s3_region == "us-east-1"
    assert s.s3_private_evidence_bucket == "defendable-private-evidence-prod"


@pytest.fixture(autouse=True)
def _restore_settings():
    """Ensure no test leaks a reloaded config module into siblings."""
    yield
    from app.core import config as _config
    importlib.reload(_config)
    _config.get_settings.cache_clear()
