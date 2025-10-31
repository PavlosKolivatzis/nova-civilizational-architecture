"""Additional metrics validation for gradient score."""

from __future__ import annotations

import pytest


@pytest.mark.health
def test_score_gauge_updates(client_factory, make_envelope):
    client = client_factory()
    client.post("/federation/checkpoint", json=make_envelope().model_dump(mode="json"))
    metrics = client.get("/metrics").text.splitlines()
    line = next(line for line in metrics if line.startswith('federation_score_gauge{peer="node-athens"}'))
    value = float(line.split(" ")[-1])
    assert 0.0 <= value <= 1.0
