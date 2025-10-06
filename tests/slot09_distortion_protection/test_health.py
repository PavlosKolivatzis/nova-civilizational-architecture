import importlib
from types import SimpleNamespace

import pytest

import slots.slot09_distortion_protection.health as health_mod
import slots.slot09_distortion_protection.ids_policy as ids_policy_mod


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    monkeypatch.delenv("NOVA_LIGHTCLOCK_DEEP", raising=False)
    monkeypatch.delenv("NOVA_USE_SHARED_HASH", raising=False)
    return None


def test_health_returns_minimal_when_hybrid_missing(monkeypatch):
    hybrid_module = importlib.import_module("slots.slot09_distortion_protection.hybrid_api")
    original_class = getattr(hybrid_module, "HybridDistortionDetectionAPI")
    original_get_context = getattr(ids_policy_mod, "get_phase_lock_context")
    original_apply_policy = getattr(ids_policy_mod, "apply_ids_policy")

    try:
        delattr(hybrid_module, "HybridDistortionDetectionAPI")
        # Ensure imports re-resolve inside health()
        monkeypatch.setitem(ids_policy_mod.__dict__, "get_phase_lock_context", original_get_context)
        monkeypatch.setitem(ids_policy_mod.__dict__, "apply_ids_policy", original_apply_policy)

        result = health_mod.health()
        assert result["engine_status"] == "minimal"
        metrics = result["metrics"]
        assert metrics["core_available"] is False
        assert metrics["import_error"]
    finally:
        setattr(hybrid_module, "HybridDistortionDetectionAPI", original_class)


def test_health_happy_path(monkeypatch):
    class StubHybridAPI:
        def __init__(self):
            self.initialized = True

    def stub_get_phase_lock_context():
        return {"available": True, "phase_lock": 0.75, "coherence_level": "medium"}

    def stub_apply_ids_policy(result):
        return {"policy": "STANDARD_PROCESSING", "reason": "ids:test", "severity": "normal"}

    hybrid_module = importlib.import_module("slots.slot09_distortion_protection.hybrid_api")
    monkeypatch.setattr(hybrid_module, "HybridDistortionDetectionAPI", StubHybridAPI)
    ids_flags = importlib.import_module("config.feature_flags")
    monkeypatch.setattr(ids_flags, "IDS_ENABLED", True, raising=False)
    monkeypatch.setenv("NOVA_LIGHTCLOCK_DEEP", "1")
    monkeypatch.setenv("NOVA_USE_SHARED_HASH", "1")
    monkeypatch.setattr(ids_policy_mod, "get_phase_lock_context", stub_get_phase_lock_context)
    monkeypatch.setattr(ids_policy_mod, "apply_ids_policy", stub_apply_ids_policy)

    result = health_mod.health()
    assert result["self_check"] == "ok"
    metrics = result["metrics"]
    assert metrics["hybrid_api_available"] is True
    assert metrics["ids_policy_available"] is True
    assert metrics["phase_lock_integration"] in {"available", "disabled"}
    assert metrics["shared_hash_enabled"] is True
    assert metrics["core_available"] is True
