from collections import deque
import time

from orchestrator import federation_poller as poller


def test_quality_prefers_fast_success():
    params = poller._quality_params()
    now = time.time()

    fast_success = deque([1.0] * 20, maxlen=20)
    fast_durations = deque([0.1] * 20, maxlen=20)
    q_fast, _, _, _ = poller._compute_quality(fast_success, fast_durations, now, now, params)

    slow_success = deque([1.0] + [0.0] * 19, maxlen=20)
    slow_durations = deque([2.5] * 20, maxlen=20)
    q_slow, _, _, _ = poller._compute_quality(slow_success, slow_durations, 0.0, now, params)

    assert 0.0 <= q_fast <= 1.0
    assert 0.0 <= q_slow <= 1.0
    assert q_fast > q_slow


def test_fresh_peer_scores_higher():
    params = poller._quality_params()
    now = time.time()
    history_success = deque([1.0] * 5, maxlen=20)
    history_duration = deque([0.5] * 5, maxlen=20)

    quality_fresh, _, _, _ = poller._compute_quality(history_success, history_duration, now, now, params)
    quality_stale, _, _, _ = poller._compute_quality(history_success, history_duration, now - 1800, now, params)

    assert quality_fresh > quality_stale


def test_quality_zero_when_no_history():
    params = poller._quality_params()
    now = time.time()
    quality, success_rate, p95, freshness = poller._compute_quality(deque(maxlen=20), deque(maxlen=20), 0.0, now, params)

    assert quality == 0.0
    assert success_rate == 0.0
    assert p95 == 0.0
    assert freshness == 0.0
