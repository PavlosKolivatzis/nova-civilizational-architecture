from __future__ import annotations

import math

from prometheus_client import generate_latest

from nova.orchestrator import rri
from nova.orchestrator.prometheus_metrics import _REGISTRY


def test_rri_updates_with_window():
    rri.reset()
    # Prime counts
    rri.update_from_totals(100, 40, 40, 20, now=0.0)
    assert math.isclose(rri.RRI_GAUGE._value.get(), 0.0)  # no window yet

    # Apply delta after 30 seconds
    rri.update_from_totals(110, 44, 44, 22, now=30.0)
    value = rri.RRI_GAUGE._value.get()
    assert math.isclose(value, 0.36, rel_tol=1e-6)

    # Advance beyond window; only latest delta should remain
    rri.update_from_totals(120, 48, 48, 24, now=400.0)
    value_after = rri.RRI_GAUGE._value.get()
    assert math.isclose(value_after, 0.36, rel_tol=1e-6)


def test_rri_handles_no_delta_gracefully():
    rri.reset()
    rri.update_from_totals(10, 4, 4, 2, now=0.0)
    rri.update_from_totals(10, 4, 4, 2, now=10.0)
    assert math.isclose(rri.RRI_GAUGE._value.get(), 0.0, abs_tol=1e-9)


def test_rri_metrics_exposed():
    payload = generate_latest(_REGISTRY).decode("utf-8")
    assert "nova_reflective_resonance_index" in payload
    assert "nova_reflect_traces_total" in payload
