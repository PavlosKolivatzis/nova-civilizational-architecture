"""Prometheus helpers for the adaptive wisdom governor."""

from __future__ import annotations

from prometheus_client import Gauge

from nova.governor.adaptive_wisdom import Telemetry

from .registry import REGISTRY

__all__ = [
    "publish_telemetry",
    "gamma_eta_gauge",
    "gamma_margin_gauge",
    "gamma_generativity_gauge",
    "reset_for_tests",
]

_gamma_eta = Gauge(
    "nova_gamma_eta_current",
    "Adaptive wisdom learning rate eta",
    registry=REGISTRY,
)
_gamma_margin = Gauge(
    "nova_gamma_margin",
    "Stability margin = -Re(lambda_max)",
    registry=REGISTRY,
)
_gamma_generativity = Gauge(
    "nova_gamma_generativity_star",
    "Generativity score G* = C*rho*S - alpha*H",
    registry=REGISTRY,
)


def publish_telemetry(telemetry: Telemetry) -> None:
    """Publish governor telemetry to Prometheus gauges."""

    _gamma_eta.set(telemetry.eta)
    _gamma_margin.set(telemetry.margin)
    _gamma_generativity.set(telemetry.G)


def gamma_eta_gauge() -> Gauge:
    return _gamma_eta


def gamma_margin_gauge() -> Gauge:
    return _gamma_margin


def gamma_generativity_gauge() -> Gauge:
    return _gamma_generativity


def reset_for_tests() -> None:
    """Reset gauges to zero for isolated unit tests."""
    _gamma_eta.set(0.0)
    _gamma_margin.set(0.0)
    _gamma_generativity.set(0.0)
