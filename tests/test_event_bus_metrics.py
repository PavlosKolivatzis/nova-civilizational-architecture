import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "event_bus", Path(__file__).resolve().parents[1] / "orchestrator" / "core" / "event_bus.py"
)
event_bus_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(event_bus_module)
EventBus = event_bus_module.EventBus


def test_event_bus_metrics_track_failures():
    bus = EventBus()

    def failing_handler(data):
        raise ValueError("Test failure")

    bus.subscribe('test_event', failing_handler)

    with pytest.raises(ValueError):
        bus.publish('test_event', {})

    assert bus.metrics['total_attempts'] == 1
    assert bus.metrics['failed_attempts'] == 1
    assert bus.metrics.get('successful_attempts', 0) == 0
    assert bus.metrics['published'] == 1
    assert bus.get_success_rate() == 0.0


def test_event_bus_metrics_track_successes():
    bus = EventBus()

    called = []

    def successful_handler(data):
        called.append(data)

    bus.subscribe('test_event', successful_handler)

    bus.publish('test_event', {})

    assert bus.metrics['published'] == 1
    assert bus.metrics['total_attempts'] == 1
    assert bus.metrics.get('failed_attempts', 0) == 0
    assert bus.metrics['successful_attempts'] == 1
    assert bus.get_success_rate() == 1.0
