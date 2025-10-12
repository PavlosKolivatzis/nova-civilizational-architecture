from collections import deque


import nova.slots.slot08_memory_lock.core.metrics as metrics


class TimeStub:
    def __init__(self, *values: float):
        self._values = list(values)
        self._index = 0
        self.current = values[-1] if values else 0.0

    def __call__(self) -> float:
        if self._index < len(self._values):
            self.current = self._values[self._index]
            self._index += 1
        return self.current


def test_record_metric_retention(monkeypatch):
    collector = metrics.Slot8MetricsCollector(retention_seconds=5)
    time_stub = TimeStub(1000.0, 1006.0)
    monkeypatch.setattr(metrics.time, "time", time_stub)

    collector.record_integrity_score(0.8)
    collector.record_integrity_score(0.9)

    points = collector.metrics["slot8.integrity_score"]
    assert len(points) == 1
    assert points[-1].value == 0.9


def test_slo_compliance(monkeypatch):
    collector = metrics.Slot8MetricsCollector()
    now = 2000.0
    monkeypatch.setattr(metrics.time, "time", lambda: now)

    collector.recovery_times = deque([
        {"timestamp": now - 10, "mttr": 4.0},
        {"timestamp": now - 8, "mttr": 6.0},
    ], maxlen=100)
    collector.quarantine_state_changes = deque([
        {"timestamp": now - 9, "active": True, "duration": 0.5},
        {"timestamp": now - 7, "active": True, "duration": 2.0},
    ], maxlen=50)
    collector.metrics["slot8.integrity_score"].append(metrics.MetricPoint(timestamp=now, value=0.75))
    collector.metrics["slot8.quarantine.active"].append(metrics.MetricPoint(timestamp=now, value=0.0))

    result = collector.get_slo_compliance(window_seconds=20)
    assert 0.0 <= result["mttr_slo_compliance"] <= 1.0
    assert 0.0 <= result["quarantine_flip_slo_compliance"] <= 1.0
    assert result["current_integrity_score"] == 0.75
    assert result["quarantine_active"] is False


def test_export_prometheus_metrics(monkeypatch):
    collector = metrics.Slot8MetricsCollector()
    time_stub = TimeStub(3000.0)
    monkeypatch.setattr(metrics.time, "time", time_stub)

    collector.record_repair_outcome("patch", True, 1.2)
    output = collector.export_prometheus_metrics().splitlines()
    assert output
    assert output[0].startswith("slot8_repair_success_rate")


def test_get_metrics_collector_singleton(monkeypatch):
    monkeypatch.setattr(metrics, "_metrics_collector", None)
    first = metrics.get_metrics_collector()
    second = metrics.get_metrics_collector()
    assert first is second


def test_emit_metric_uses_global_collector(monkeypatch):
    collector = metrics.Slot8MetricsCollector()
    monkeypatch.setattr(metrics, "_metrics_collector", collector)
    metrics.emit_metric("slot8.test.metric", 3.14, {"label": "x"})
    points = collector.metrics["slot8.test.metric"]
    assert points[-1].value == 3.14
    assert points[-1].labels == {"label": "x"}
