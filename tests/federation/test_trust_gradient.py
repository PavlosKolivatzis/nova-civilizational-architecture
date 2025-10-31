"""Gradient trust score tests."""

from __future__ import annotations

import pytest

from nova.federation.trust_model import compute_gradient_score


@pytest.mark.health
def test_gradient_score_bounds():
    score = compute_gradient_score(verified=True, latency_ms=10.0, age_s=1.0, continuity=1.0)
    assert 0.0 <= score <= 1.0


@pytest.mark.health
def test_verified_increases_score():
    base = compute_gradient_score(verified=False, latency_ms=50.0, age_s=10.0, continuity=0.5)
    higher = compute_gradient_score(verified=True, latency_ms=50.0, age_s=10.0, continuity=0.5)
    assert higher > base


@pytest.mark.health
def test_latency_and_age_decrease_score():
    fast = compute_gradient_score(verified=True, latency_ms=10.0, age_s=5.0, continuity=1.0)
    slow = compute_gradient_score(verified=True, latency_ms=1500.0, age_s=1800.0, continuity=1.0)
    assert slow < fast


@pytest.mark.health
def test_continuity_boosts_score():
    low = compute_gradient_score(verified=True, latency_ms=10.0, age_s=5.0, continuity=0.2)
    high = compute_gradient_score(verified=True, latency_ms=10.0, age_s=5.0, continuity=1.0)
    assert high > low
