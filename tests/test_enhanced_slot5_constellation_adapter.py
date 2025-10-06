import importlib
import sys
import types

import pytest


@pytest.fixture
def adapter_factory(monkeypatch):
    """Provide a factory that yields adapters backed by controllable stubs."""
    module_name = "orchestrator.adapters.enhanced_slot5_constellation"
    module = importlib.import_module(module_name)

    class DummyAdaptiveProcessor:
        def __init__(self):
            self.learning_rate = 0.15
            self.adaptation_sensitivity = 2.5
            self._thresholds = {
                "learning_rate": self.learning_rate,
                "adaptation_sensitivity": self.adaptation_sensitivity,
            }

        def get_current_thresholds(self):
            return dict(self._thresholds)

    class DummyEngine:
        __version__ = "9.9.9"

        def __init__(self):
            self.adaptive_processor = DummyAdaptiveProcessor()
            self.similarity_threshold = 0.31
            self.link_strength_threshold = 0.22
            self.stability_window = 12
            self._constellation_history = [{"score": 0.8}]
            self.semantic_mirror = None
            self.map_calls = []
            self.reset_calls = 0
            self.fail_metrics = False
            self.fail_reset = False
            self.fail_coordination = False
            self.map_error = False

        def map(self, items, context=None):
            if self.map_error:
                raise RuntimeError("mapping failed")
            self.map_calls.append((tuple(items), context))
            return {
                "constellation": list(items),
                "links": [(items[0], items[-1])] if items else [],
                "stability": {"score": 0.93},
                "adaptive": {"processing_time": 0.42},
            }

        def get_adaptive_metrics(self):
            if self.fail_metrics:
                raise RuntimeError("metrics offline")
            return {"processing_time": 0.84, "quality": 0.97}

        def reset_adaptive_state(self):
            if self.fail_reset:
                raise RuntimeError("reset failed")
            self.reset_calls += 1

        def enable_cross_slot_coordination(self, mirror):
            if self.fail_coordination:
                raise RuntimeError("coordination failed")
            self.semantic_mirror = mirror

    class BaseEngine:
        def __init__(self):
            self.similarity_threshold = 0.2
            self.link_strength_threshold = 0.15
            self.stability_window = 8
            self._constellation_history = [{"score": 0.5}]
            self.map_calls = []

        def map(self, items):
            self.map_calls.append(tuple(items))
            return {"constellation": list(items), "links": []}

    def factory(*, engine=None, available=True, engine_type="enhanced"):
        if engine is None and available:
            eng = DummyEngine()
        else:
            eng = engine
        monkeypatch.setattr(module, "ENGINE", eng, raising=False)
        monkeypatch.setattr(module, "AVAILABLE", available, raising=False)
        monkeypatch.setattr(module, "ENGINE_TYPE", engine_type, raising=False)
        monkeypatch.setattr(module, "semantic_mirror", object(), raising=False)
        adapter = module.EnhancedSlot5ConstellationAdapter()
        return module, adapter, eng

    factory.DummyEngine = DummyEngine
    factory.BaseEngine = BaseEngine
    factory.module = module
    return factory


def test_map_enhanced_path(adapter_factory):
    module, adapter, engine = adapter_factory()

    result = adapter.map(["alpha", "beta"], context={"phase": "processual"})

    assert result["constellation"] == ["alpha", "beta"]
    assert result["adaptive"]["processing_time"] == pytest.approx(0.42)
    assert engine.map_calls[-1] == (("alpha", "beta"), {"phase": "processual"})


def test_map_unavailable_engine_returns_placeholder(adapter_factory):
    module, adapter, _ = adapter_factory(available=False, engine=None)

    data = adapter.map(["alpha"])

    assert data["adaptive"]["enabled"] is False
    assert data["stability"]["status"] == "unavailable"


def test_map_base_engine_fallback(adapter_factory):
    base_engine = adapter_factory.BaseEngine()
    module, adapter, engine = adapter_factory(engine=base_engine, engine_type="base")

    payload = adapter.map(["x", "y", "z"], context={"ignored": True})

    assert payload["adaptive"]["enabled"] is False
    assert engine.map_calls[-1] == ("x", "y", "z")


def test_map_handles_engine_exception(adapter_factory):
    module, adapter, engine = adapter_factory()
    engine.map_error = True

    output = adapter.map(["bad"])

    assert output["stability"]["status"] == "error"
    assert output["error"] == "mapping failed"


def test_get_adaptive_metrics_success(adapter_factory):
    module, adapter, _ = adapter_factory()

    metrics = adapter.get_adaptive_metrics()

    assert metrics["engine_type"] == "enhanced"
    assert metrics["processing_time"] == pytest.approx(0.84)


def test_get_adaptive_metrics_handles_error(adapter_factory):
    module, adapter, engine = adapter_factory()
    engine.fail_metrics = True

    metrics = adapter.get_adaptive_metrics()

    assert metrics["error"] == "metrics offline"
    assert metrics["engine_type"] == "enhanced"


def test_get_adaptive_metrics_base_engine(adapter_factory):
    base_engine = adapter_factory.BaseEngine()
    module, adapter, _ = adapter_factory(engine=base_engine, engine_type="base")

    metrics = adapter.get_adaptive_metrics()

    assert metrics["adaptive_enabled"] is False
    assert metrics["engine_type"] == "base"


def test_get_configuration_with_adaptive_processor(adapter_factory):
    module, adapter, engine = adapter_factory()

    config = adapter.get_configuration()

    assert config["engine_type"] == "enhanced"
    assert config["adaptive_enabled"] is True
    assert config["adaptive_thresholds"]["learning_rate"] == pytest.approx(0.15)


def test_get_configuration_base_engine(adapter_factory):
    base_engine = adapter_factory.BaseEngine()
    module, adapter, _ = adapter_factory(engine=base_engine, engine_type="base")

    config = adapter.get_configuration()

    assert config["adaptive_enabled"] is False
    assert config["similarity_threshold"] == pytest.approx(0.2)


def test_get_configuration_handles_threshold_error(adapter_factory):
    module, adapter, engine = adapter_factory()
    engine.adaptive_processor.get_current_thresholds = lambda: (_ for _ in ()).throw(RuntimeError("broken"))

    cfg = adapter.get_configuration()

    assert cfg["adaptive_error"] == "broken"


def test_update_configuration_applies_values(adapter_factory):
    module, adapter, engine = adapter_factory()

    success = adapter.update_configuration({
        "similarity_threshold": 0.7,
        "link_strength_threshold": 0.4,
        "stability_window": 21,
        "adaptive_config": {"learning_rate": 0.5, "adaptation_sensitivity": 1.5},
    })

    assert success is True
    assert engine.similarity_threshold == pytest.approx(0.7)
    assert engine.adaptive_processor.learning_rate == pytest.approx(0.5)
    assert engine.adaptive_processor.adaptation_sensitivity == pytest.approx(1.5)


def test_update_configuration_rejects_invalid_values(adapter_factory):
    module, adapter, _ = adapter_factory()

    ok = adapter.update_configuration({"similarity_threshold": "bad"})

    assert ok is False


def test_reset_adaptive_state_success(adapter_factory):
    module, adapter, engine = adapter_factory()

    assert adapter.reset_adaptive_state() is True
    assert engine.reset_calls == 1


def test_reset_adaptive_state_handles_failure(adapter_factory):
    module, adapter, engine = adapter_factory()
    engine.fail_reset = True

    assert adapter.reset_adaptive_state() is False


def test_reset_adaptive_state_not_supported(adapter_factory):
    base_engine = adapter_factory.BaseEngine()
    delattr(base_engine, "_constellation_history")
    module, adapter, engine = adapter_factory(engine=base_engine, engine_type="base")

    assert adapter.reset_adaptive_state() is False


def test_enable_cross_slot_coordination_success(adapter_factory, monkeypatch):
    module, adapter, engine = adapter_factory()
    mirror = object()
    monkeypatch.setattr("orchestrator.semantic_mirror.get_semantic_mirror", lambda: mirror)

    assert adapter.enable_cross_slot_coordination() is True
    assert engine.semantic_mirror is mirror


def test_enable_cross_slot_coordination_handles_failure(adapter_factory, monkeypatch):
    module, adapter, engine = adapter_factory()
    engine.fail_coordination = True
    monkeypatch.setattr("orchestrator.semantic_mirror.get_semantic_mirror", lambda: object())

    assert adapter.enable_cross_slot_coordination() is False


def test_enable_cross_slot_coordination_not_supported(adapter_factory):
    base_engine = adapter_factory.BaseEngine()
    module, adapter, _ = adapter_factory(engine=base_engine, engine_type="base")

    assert adapter.enable_cross_slot_coordination() is False


def test_get_stability_history_prefers_wrapped_engine(adapter_factory):
    module, adapter, engine = adapter_factory()
    engine.base_engine = types.SimpleNamespace(_constellation_history=[{"score": 0.99}])

    history = adapter.get_stability_history()

    assert history == [{"score": 0.99}]


def test_get_stability_history_when_unavailable(adapter_factory):
    module, adapter, _ = adapter_factory(available=False, engine=None)

    assert adapter.get_stability_history() == []


def test_health_check_reports_processual_status(adapter_factory):
    module, adapter, engine = adapter_factory()
    engine.base_engine = types.SimpleNamespace(_constellation_history=[{"score": 0.77}])
    engine.semantic_mirror = object()

    health = adapter.health_check()

    assert health["status"] == "processual"
    assert health["history_entries"] == 1
    assert health["adaptive_enabled"] is True


def test_health_check_handles_adaptive_error(adapter_factory):
    module, adapter, engine = adapter_factory()
    engine.fail_metrics = True

    report = adapter.health_check()

    assert report["adaptive_enabled"] is False
    assert report["adaptive_error"] == "metrics offline"


def test_health_check_unavailable_engine(adapter_factory):
    module, adapter, _ = adapter_factory(available=False, engine=None)

    status = adapter.health_check()

    assert status["status"] == "unavailable"
    assert status["engine_loaded"] is False
