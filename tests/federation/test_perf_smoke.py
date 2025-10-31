"""Simple performance smoke test for federation checkpoint handler."""

from __future__ import annotations

import statistics
import time

import pytest


@pytest.mark.health
def test_checkpoint_handler_latency(client_factory, make_envelope):
    client = client_factory()
    durations = []
    for _ in range(5):
        start = time.perf_counter()
        resp = client.post(
            "/federation/checkpoint",
            json=make_envelope().model_dump(mode="json"),
        )
        assert resp.status_code == 200
        durations.append((time.perf_counter() - start) * 1000)
    assert statistics.median(durations) <= 50.0
