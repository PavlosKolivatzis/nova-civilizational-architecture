"""Metrics behaviour tests for federation scaffold."""

from __future__ import annotations

import pytest

from nova.metrics import federation as federation_metrics


@pytest.mark.health
def test_metrics_increment_on_success(client_factory, make_envelope):
    client = client_factory()
    client.post("/federation/checkpoint", json=make_envelope().model_dump(mode="json"))
    family = federation_metrics.verifications_counter().collect()[0]
    sample = next(s for s in family.samples if s.labels.get("result") == "ok" and s.labels.get("peer") == "node-athens")
    assert sample.value == 1.0


@pytest.mark.health
def test_last_sync_updated(client_factory, make_envelope):
    client = client_factory()
    client.post("/federation/checkpoint", json=make_envelope().model_dump(mode="json"))
    family = federation_metrics.verifications_counter().collect()[0]
    assert any(s.labels.get("result") == "ok" for s in family.samples)
    gauge_family = federation_metrics._last_sync.collect()[0]  # type: ignore[attr-defined]
    sample = next(s for s in gauge_family.samples if s.labels.get("peer") == "node-athens")
    assert sample.value == 0.0
