import pytest

import slots.slot09_distortion_protection.ids_policy as ids_policy


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    monkeypatch.delenv("NOVA_LIGHTCLOCK_DEEP", raising=False)
    monkeypatch.delenv("NOVA_USE_SHARED_HASH", raising=False)
    return None


def test_get_phase_lock_context_feature_disabled(monkeypatch):
    monkeypatch.setenv("NOVA_LIGHTCLOCK_DEEP", "0")
    result = ids_policy.get_phase_lock_context()
    assert result == {"phase_lock": None, "available": False, "reason": "feature_disabled"}


def test_get_phase_lock_context_with_value(monkeypatch):
    class StubMirror:
        def get_context(self, key, actor):
            assert key == "slot07.phase_lock"
            return 0.86

    monkeypatch.setattr(ids_policy, "get_semantic_mirror", lambda: StubMirror())
    result = ids_policy.get_phase_lock_context()
    assert result["available"] is True
    assert result["phase_lock"] == pytest.approx(0.86)
    assert result["coherence_level"] == "high"


def test_get_phase_lock_context_handles_error(monkeypatch):
    def broken_mirror():
        raise RuntimeError("boom")

    monkeypatch.setattr(ids_policy, "get_semantic_mirror", broken_mirror)
    result = ids_policy.get_phase_lock_context()
    assert result["available"] is False
    assert result["reason"].startswith("error_")


def test_apply_phase_lock_policy_adjustments_high_relaxes(monkeypatch):
    base_policy = {
        "policy": "DEGRADE_AND_REVIEW",
        "reason": "ids:test",
        "severity": "medium",
    }
    ctx = {"available": True, "phase_lock": 0.9, "coherence_level": "high"}
    final = ids_policy.apply_phase_lock_policy_adjustments(base_policy, ctx)
    assert final["policy"] == "STANDARD_PROCESSING"
    assert final["severity"] == "normal"
    assert "phase_lock_0.900_high" in final["reason"]


def test_apply_phase_lock_policy_adjustments_minimal_escalates():
    base_policy = {
        "policy": "DEGRADE_AND_REVIEW",
        "reason": "ids:base",
        "severity": "medium",
    }
    ctx = {"available": True, "phase_lock": 0.2, "coherence_level": "minimal"}
    final = ids_policy.apply_phase_lock_policy_adjustments(base_policy, ctx)
    assert final["policy"] == "BLOCK_OR_SANDBOX"
    assert final["severity"] == "high"


def test_apply_ids_policy_disabled(monkeypatch):
    monkeypatch.setattr(ids_policy, "IDS_ENABLED", False)
    assert ids_policy.apply_ids_policy({}) == {
        "policy": "STANDARD_PROCESSING",
        "reason": "ids_disabled",
    }


def test_apply_ids_policy_with_phase_adjustments(monkeypatch):
    monkeypatch.setattr(ids_policy, "IDS_ENABLED", True)
    monkeypatch.setenv("NOVA_LIGHTCLOCK_DEEP", "1")
    monkeypatch.setattr(
        ids_policy,
        "get_phase_lock_context",
        lambda: {"available": True, "phase_lock": 0.9, "coherence_level": "high"},
    )
    analysis = {"stability": 0.3, "drift": 0.2, "state": "UNSTABLE"}
    result = ids_policy.apply_ids_policy(analysis)
    assert result["policy"] == "STANDARD_PROCESSING"
    assert result["severity"] == "normal"
    assert "phase_lock" in result["reason"]

def test_policy_check_with_ids(monkeypatch):
    monkeypatch.setattr(ids_policy, "IDS_ENABLED", True)
    vectors = {
        "traits": [0.1, 0.2],
        "content": [0.8, 0.9],
    }

    def fake_analyze_vector(vector, trace_id, scope):
        if scope == "traits":
            return {"stability": 0.2, "drift": 0.4, "state": "DEGRADING"}
        return {"stability": 0.9, "drift": 0.01, "state": "STABLE"}

    monkeypatch.setattr(ids_policy.ids_service, "analyze_vector", fake_analyze_vector)
    monkeypatch.setattr(ids_policy, "get_phase_lock_context", lambda: {"available": False})

    result = ids_policy.policy_check_with_ids({"embedding_vectors": vectors}, "trace-123")
    assert result["final_policy"] == "BLOCK_OR_SANDBOX"
    assert result["ids_enabled"] is True
    assert result["trace_id"] == "trace-123"
