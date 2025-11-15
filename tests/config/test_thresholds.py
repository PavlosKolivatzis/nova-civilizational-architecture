"""Tests for nova.config.thresholds validation layer."""

from __future__ import annotations

from typing import Iterable

import pytest

from nova.config import thresholds

WISE_ENV_VARS = (
    "NOVA_WISDOM_CRITICAL_MARGIN",
    "NOVA_WISDOM_STABILIZING_MARGIN",
    "NOVA_WISDOM_EXPLORING_MARGIN",
    "NOVA_WISDOM_OPTIMAL_MARGIN",
    "NOVA_WISDOM_EXPLORING_G",
    "NOVA_WISDOM_OPTIMAL_G",
)


def _clear_env(monkeypatch: pytest.MonkeyPatch, keys: Iterable[str]) -> None:
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def _reset_cache() -> None:
    thresholds.load_wisdom_thresholds.cache_clear()


def test_load_wisdom_thresholds_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default env (or unset) should yield the documented safe defaults."""
    _clear_env(monkeypatch, WISE_ENV_VARS)
    _reset_cache()

    config = thresholds.load_wisdom_thresholds()

    assert config.critical_margin == pytest.approx(0.01)
    assert config.stabilizing_margin == pytest.approx(0.02)
    assert config.optimal_margin == pytest.approx(0.05)
    assert config.exploring_margin == pytest.approx(0.10)
    assert config.exploring_g == pytest.approx(0.60)
    assert config.optimal_g == pytest.approx(0.70)
    _reset_cache()


def test_stabilizing_must_exceed_critical(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validator rejects configurations where stabilizing <= critical."""
    monkeypatch.setenv("NOVA_WISDOM_CRITICAL_MARGIN", "0.02")
    monkeypatch.setenv("NOVA_WISDOM_STABILIZING_MARGIN", "0.02")  # equal on purpose
    _reset_cache()

    with pytest.raises(ValueError):
        thresholds.load_wisdom_thresholds()
    _reset_cache()


def test_margin_ordering_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    """Root validator ensures strict ordering critical < stabilizing < optimal < exploring."""
    monkeypatch.setenv("NOVA_WISDOM_CRITICAL_MARGIN", "0.01")
    monkeypatch.setenv("NOVA_WISDOM_STABILIZING_MARGIN", "0.03")
    monkeypatch.setenv("NOVA_WISDOM_OPTIMAL_MARGIN", "0.08")
    monkeypatch.setenv("NOVA_WISDOM_EXPLORING_MARGIN", "0.07")  # exploring below optimal
    _reset_cache()

    with pytest.raises(ValueError):
        thresholds.load_wisdom_thresholds()
    _reset_cache()


def test_optimal_g_above_exploring_g(monkeypatch: pytest.MonkeyPatch) -> None:
    """optimal_g must remain >= exploring_g for consistent gating."""
    monkeypatch.setenv("NOVA_WISDOM_EXPLORING_G", "0.75")
    monkeypatch.setenv("NOVA_WISDOM_OPTIMAL_G", "0.70")
    _reset_cache()

    with pytest.raises(ValueError):
        thresholds.load_wisdom_thresholds()
    _reset_cache()
