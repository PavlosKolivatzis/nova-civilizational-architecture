"""Prometheus metrics for bifurcation-aware adaptive wisdom system.

Exports:
  nova_wisdom_eta_current                       - Current learning rate η
  nova_wisdom_gamma                              - Current wisdom level γ
  nova_wisdom_generativity                       - Generativity score G*
  nova_wisdom_generativity_components            - G* components (progress, novelty, consistency)
  nova_wisdom_eta_bias_from_generativity         - Δη bias from G*
  nova_wisdom_stability_margin                   - Stability margin S = -max Re(λ)
  nova_wisdom_hopf_distance                      - Hopf distance H = min |Re(λ)| for oscillatory modes
  nova_wisdom_spectral_radius                    - Spectral radius ρ = max |λ|
"""

from __future__ import annotations

from prometheus_client import Gauge

from .registry import REGISTRY

__all__ = [
    "publish_wisdom_telemetry",
    "publish_generativity_components",
    "wisdom_eta_gauge",
    "wisdom_gamma_gauge",
    "wisdom_generativity_gauge",
    "wisdom_generativity_components_gauge",
    "wisdom_eta_bias_gauge",
    "wisdom_stability_margin_gauge",
    "wisdom_hopf_distance_gauge",
    "wisdom_spectral_radius_gauge",
    "reset_for_tests",
]

# Core wisdom metrics
_wisdom_eta = Gauge(
    "nova_wisdom_eta_current",
    "Adaptive wisdom learning rate eta",
    registry=REGISTRY,
)

_wisdom_gamma = Gauge(
    "nova_wisdom_gamma",
    "Current wisdom level gamma",
    registry=REGISTRY,
)

_wisdom_generativity = Gauge(
    "nova_wisdom_generativity",
    "Generativity score G*",
    registry=REGISTRY,
)

_wisdom_generativity_components = Gauge(
    "nova_wisdom_generativity_components",
    "Generativity components (progress, novelty, consistency)",
    labelnames=["component"],
    registry=REGISTRY,
)

_wisdom_eta_bias = Gauge(
    "nova_wisdom_eta_bias_from_generativity",
    "Learning rate bias from generativity (Δη = κ·(G* - G₀))",
    registry=REGISTRY,
)

# Bifurcation analysis metrics
_wisdom_stability_margin = Gauge(
    "nova_wisdom_stability_margin",
    "Stability margin S = -max Re(lambda)",
    registry=REGISTRY,
)

_wisdom_hopf_distance = Gauge(
    "nova_wisdom_hopf_distance",
    "Hopf distance H = min |Re(lambda)| for oscillatory modes",
    registry=REGISTRY,
)

_wisdom_spectral_radius = Gauge(
    "nova_wisdom_spectral_radius",
    "Spectral radius rho = max |lambda|",
    registry=REGISTRY,
)


def publish_wisdom_telemetry(
    eta: float,
    gamma: float,
    generativity: float,
    stability_margin: float,
    hopf_distance: float,
    spectral_radius: float,
) -> None:
    """Publish all wisdom telemetry to Prometheus gauges.

    Args:
        eta: Current learning rate
        gamma: Current wisdom level
        generativity: Generativity score G*
        stability_margin: S = -max Re(λ)
        hopf_distance: H = min |Re(λ)| for oscillatory
        spectral_radius: ρ = max |λ|
    """
    _wisdom_eta.set(eta)
    _wisdom_gamma.set(gamma)
    _wisdom_generativity.set(generativity)
    _wisdom_stability_margin.set(stability_margin)
    _wisdom_hopf_distance.set(hopf_distance)
    _wisdom_spectral_radius.set(spectral_radius)


def wisdom_eta_gauge() -> Gauge:
    return _wisdom_eta


def wisdom_gamma_gauge() -> Gauge:
    return _wisdom_gamma


def wisdom_generativity_gauge() -> Gauge:
    return _wisdom_generativity


def wisdom_stability_margin_gauge() -> Gauge:
    return _wisdom_stability_margin


def wisdom_hopf_distance_gauge() -> Gauge:
    return _wisdom_hopf_distance


def wisdom_spectral_radius_gauge() -> Gauge:
    return _wisdom_spectral_radius


def wisdom_generativity_components_gauge() -> Gauge:
    return _wisdom_generativity_components


def wisdom_eta_bias_gauge() -> Gauge:
    return _wisdom_eta_bias


def publish_generativity_components(
    progress: float, novelty: float, consistency: float, eta_bias: float
) -> None:
    """Publish generativity components and bias to Prometheus.

    Args:
        progress: Progress component P ∈ [0,1]
        novelty: Novelty component N ∈ [0,1]
        consistency: Consistency component Cc ∈ [0,1]
        eta_bias: Bias term Δη from generativity
    """
    _wisdom_generativity_components.labels(component="progress").set(progress)
    _wisdom_generativity_components.labels(component="novelty").set(novelty)
    _wisdom_generativity_components.labels(component="consistency").set(consistency)
    _wisdom_eta_bias.set(eta_bias)


def reset_for_tests() -> None:
    """Reset all wisdom gauges to zero for isolated unit tests."""
    _wisdom_eta.set(0.0)
    _wisdom_gamma.set(0.0)
    _wisdom_generativity.set(0.0)
    _wisdom_generativity_components.labels(component="progress").set(0.0)
    _wisdom_generativity_components.labels(component="novelty").set(0.0)
    _wisdom_generativity_components.labels(component="consistency").set(0.0)
    _wisdom_eta_bias.set(0.0)
    _wisdom_stability_margin.set(0.0)
    _wisdom_hopf_distance.set(0.0)
    _wisdom_spectral_radius.set(0.0)
