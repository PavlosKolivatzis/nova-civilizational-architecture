import pytest

from orchestrator.core.event_bus import EventBus


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
    assert bus.get_success_rate() == 0.0
