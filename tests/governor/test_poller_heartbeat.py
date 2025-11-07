from prometheus_client import generate_latest

from nova.metrics import wisdom_metrics  # noqa: F401
from nova.metrics.registry import REGISTRY


def test_wisdom_poller_metrics_registered():
    metrics = generate_latest(REGISTRY).decode("utf-8")
    assert "nova_wisdom_poller_heartbeat_unix" in metrics
    assert "nova_wisdom_poller_errors_total" in metrics
    assert "nova_wisdom_poller_last_error_unix" in metrics
