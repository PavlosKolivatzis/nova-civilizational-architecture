import pytest

import nova.slots.slot10_civilizational_deployment.core.feedback as feedback


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    monkeypatch.delenv("NOVA_USE_SHARED_HASH", raising=False)
    return None


def test_publish_deployment_feedback_success(monkeypatch):
    published = {}

    def fake_publish(key, payload, actor, ttl):
        published["args"] = (key, payload, actor, ttl)

    monkeypatch.setattr("nova.orchestrator.semantic_mirror.publish", fake_publish, raising=False)
    monkeypatch.setattr("nova.orchestrator.semantic_mirror.get_context", lambda key=None, actor=None: {"id": "decision-123"}, raising=False)
    monkeypatch.setattr(feedback, "_update_feedback_metrics", lambda payload: published.setdefault("metrics", payload))

    feedback.publish_deployment_feedback(
        phase="canary",
        slo_ok=True,
        transform_rate=0.2,
        rollback=False,
        error_rate=0.05,
        decision_id="decision-456",
    )

    assert published["args"][0] == "slot10.deployment_feedback"
    payload = published["args"][1]
    assert payload["phase"] == "canary"
    assert payload["slo_ok"] is True
    assert payload["transform_rate"] == pytest.approx(0.2)
    assert payload["decision_id"] == "decision-456"


def test_get_deployment_feedback_success(monkeypatch):
    expected = {"status": "ok"}
    monkeypatch.setattr("nova.orchestrator.semantic_mirror.get_context", lambda key, actor=None: expected, raising=False)
    assert feedback.get_deployment_feedback() is expected


def test_get_deployment_feedback_handles_error(monkeypatch):
    monkeypatch.setattr("nova.orchestrator.semantic_mirror.get_context", lambda key, actor=None: (_ for _ in ()).throw(RuntimeError("fail")), raising=False)
    assert feedback.get_deployment_feedback() is None


def test_compute_cultural_adjustment_scenarios():
    adjustments = feedback.compute_cultural_adjustment(transform_rate=0.5, rollback=False)
    assert adjustments["recommended_action"] == "stricter_validation"

    adjustments = feedback.compute_cultural_adjustment(transform_rate=0.05, rollback=False)
    assert adjustments["recommended_action"] == "increase_adaptation"

    adjustments = feedback.compute_cultural_adjustment(transform_rate=0.3, rollback=True)
    assert adjustments["recommended_action"] == "stabilize_memory"


def test_apply_tri_feedback_signal(monkeypatch):
    captured = {}

    def fake_publish(key, payload, actor, ttl):
        captured["args"] = (key, payload, actor, ttl)

    monkeypatch.setattr("nova.orchestrator.semantic_mirror.publish", fake_publish, raising=False)

    feedback.apply_tri_feedback_signal(rollback=True, error_rate=0.2)

    assert captured["args"][0] == "slot4.tri_feedback"
    payload = captured["args"][1]
    assert payload["strict_mode"] is True
    assert payload["validation_boost"] > 0


def test_on_canary_complete_triggers_feedback(monkeypatch):
    calls = {}
    monkeypatch.setattr(feedback, "publish_deployment_feedback", lambda **kw: calls.setdefault("publish", kw))
    monkeypatch.setattr(feedback, "apply_tri_feedback_signal", lambda rollback, error_rate: calls.setdefault("signal", (rollback, error_rate)))

    feedback.on_canary_complete(success=False, transform_rate=0.3, error_rate=0.2)

    assert calls["publish"]["rollback"] is True
    assert calls["signal"] == (True, 0.2)


def test_on_deployment_success(monkeypatch):
    calls = {}
    monkeypatch.setattr(feedback, "publish_deployment_feedback", lambda **kw: calls.setdefault("publish", kw))
    monkeypatch.setattr(feedback, "apply_tri_feedback_signal", lambda rollback, error_rate: calls.setdefault("signal", (rollback, error_rate)))

    feedback.on_deployment_success("consensus", transform_rate=0.05)

    assert calls["publish"]["phase"] == "consensus"
    # Low transform rate triggers reset signal
    assert calls["signal"] == (False, 0.0)


def test_publish_handles_exception(monkeypatch):
    monkeypatch.setattr("nova.orchestrator.semantic_mirror.publish", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")), raising=False)
    # Should not raise
    feedback.publish_deployment_feedback(phase="canary", slo_ok=True, transform_rate=0.1)
