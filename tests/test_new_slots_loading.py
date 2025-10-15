# ruff: noqa: E402
"""Tests for newly registered slots."""
import importlib
import pytest

from src_bootstrap import ensure_src_on_path

ensure_src_on_path()

from nova.slot_loader import load_slot


SLOTS = [
    ("slot03_emotional_matrix", "EmotionalMatrixEngine"),
    ("slot05_constellation", "ConstellationEngine"),
    ("slot07_production_controls", "ProductionControlEngine"),
]


@pytest.mark.parametrize("slot_name, engine_cls", SLOTS)
def test_slot_can_be_loaded(slot_name, engine_cls):
    """Ensure each slot can be located and imported via ``load_slot``."""
    mod = load_slot(slot_name)
    assert hasattr(mod, engine_cls)


@pytest.mark.parametrize("slot_name, _", SLOTS)
def test_slot_health_check(slot_name, _):
    """Health checks should report operational status."""
    health_mod = importlib.import_module(f"nova.slots.{slot_name}.health")
    status = health_mod.health()
    assert status["self_check"] == "ok"
    assert status["engine_status"] == "operational"

