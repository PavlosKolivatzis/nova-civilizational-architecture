import pytest

import slots.slot10_civilizational_deployment.core.factory as factory


def test_build_canary_controller_lightclock(monkeypatch):
    monkeypatch.setenv("NOVA_LIGHTCLOCK_GATING", "1")

    captured = {}

    class StubMirror:
        pass

    class StubGatekeeper:
        def __init__(self, mirror):
            captured["gatekeeper_mirror"] = mirror

    class StubController:
        def __init__(self, **kwargs):
            captured["controller_kwargs"] = kwargs

    monkeypatch.setattr(factory, "SemanticMirrorAdapter", lambda: StubMirror())
    monkeypatch.setattr(factory, "LightClockGatekeeper", StubGatekeeper)
    monkeypatch.setattr(factory, "LightClockCanaryController", StubController)

    policy = object()
    health_feed = object()
    audit = object()
    metrics = object()

    controller = factory.build_canary_controller(
        policy=policy,
        health_feed=health_feed,
        audit=audit,
        metrics_exporter=metrics,
    )

    assert isinstance(controller, StubController)
    assert isinstance(captured["gatekeeper_mirror"], StubMirror)
    kwargs = captured["controller_kwargs"]
    assert kwargs["policy"] is policy
    assert kwargs["health_feed"] is health_feed
    assert kwargs["audit"] is audit
    assert kwargs["metrics_exporter"] is metrics


def test_build_canary_controller_standard(monkeypatch):
    monkeypatch.setenv("NOVA_LIGHTCLOCK_GATING", "0")
    captured = {}

    class StubGatekeeper:
        def __init__(self, policy, health_feed):
            captured["gatekeeper_policy"] = policy
            captured["gatekeeper_health_feed"] = health_feed

    class StubController:
        def __init__(self, **kwargs):
            captured["controller_kwargs"] = kwargs

    monkeypatch.setattr(factory, "Gatekeeper", StubGatekeeper)
    monkeypatch.setattr(factory, "CanaryController", StubController)

    policy = object()
    health_feed = object()
    audit = object()
    metrics = object()

    controller = factory.build_canary_controller(
        policy=policy,
        health_feed=health_feed,
        audit=audit,
        metrics_exporter=metrics,
    )

    assert isinstance(controller, StubController)
    assert captured["gatekeeper_policy"] is policy
    assert captured["gatekeeper_health_feed"] is health_feed
    kwargs = captured["controller_kwargs"]
    assert kwargs["gatekeeper"].__class__ is StubGatekeeper
    assert kwargs["policy"] is policy
    assert kwargs["health_feed"] is health_feed
