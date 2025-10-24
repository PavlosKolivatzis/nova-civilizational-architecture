from __future__ import annotations

from types import SimpleNamespace

from orchestrator import arc


def test_arc_records_disagreement(monkeypatch):
    arc.reset()
    monkeypatch.setenv("NOVA_ARC_ENABLED", "1")
    monkeypatch.setenv("NOVA_ARC_SAMPLE", "1.0")

    decision = SimpleNamespace(route="R1")
    why = {"tri_delta_expected": -0.5}

    before = arc.DISAGREEMENTS._value.get()
    arc.maybe_reflect(decision, "R2", why, lambda: 0.0)
    after = arc.DISAGREEMENTS._value.get()

    assert after == before + 1
    assert arc.CONSISTENCY._value.get() < 0.8


def test_arc_disabled_noop(monkeypatch):
    arc.reset()
    monkeypatch.setenv("NOVA_ARC_ENABLED", "0")
    monkeypatch.setenv("NOVA_ARC_SAMPLE", "1.0")

    decision = SimpleNamespace(route="R1")
    why = {"tri_delta_expected": 0.2}

    before = arc.DISAGREEMENTS._value.get()
    arc.maybe_reflect(decision, "R1", why, lambda: 0.0)
    assert arc.DISAGREEMENTS._value.get() == before
    # Consistency should remain at baseline
    assert arc.CONSISTENCY._value.get() == 0.8
