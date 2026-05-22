"""ENS service · slug validation + adapter safety."""
import pytest

from app.services.ens import (
    BLOCKED_LABELS,
    MockENSAdapter,
    OnchainWrappedSubnameAdapter,
    normalise_label,
)


def test_normalise_label_basic():
    assert normalise_label("Swarm & Bee Demo") == "swarm-bee-demo"


def test_normalise_label_rejects_blocked():
    for blocked in list(BLOCKED_LABELS)[:3]:
        with pytest.raises(ValueError):
            normalise_label(blocked)


def test_normalise_label_rejects_empty():
    with pytest.raises(ValueError):
        normalise_label("---")


def test_mock_adapter_never_issues():
    adapter = MockENSAdapter()
    with pytest.raises(RuntimeError):
        adapter.issue(db=None, identity=None)  # type: ignore[arg-type]


def test_onchain_adapter_requires_explicit_opt_in(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "ens_live_writes_enabled", False, raising=False)
    adapter = OnchainWrappedSubnameAdapter()
    with pytest.raises(RuntimeError):
        adapter.issue(db=None, identity=None)  # type: ignore[arg-type]
