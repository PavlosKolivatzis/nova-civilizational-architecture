"""Federation metrics health checks."""

from nova.federation.metrics import m


def test_metrics_increment_on_pull():
    metrics = m()

    ok_counter = metrics["pull_result"].labels(status="success")
    err_counter = metrics["pull_result"].labels(status="error")
    start_ok = ok_counter._value.get()
    start_err = err_counter._value.get()

    ok_counter.inc()
    assert ok_counter._value.get() == start_ok + 1

    err_counter.inc()
    assert err_counter._value.get() == start_err + 1
