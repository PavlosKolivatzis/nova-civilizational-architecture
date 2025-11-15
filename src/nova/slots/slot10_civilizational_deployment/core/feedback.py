"""Slot10 deployment feedback system for adaptive cognition.

This module implements deployment feedback loops that inform upstream slots
(Slot6 cultural synthesis, Slot4 TRI) about deployment outcomes to enable
adaptive learning and memory metabolism based on real-world performance.

The feedback system closes the loop from deployment back to cultural validation
and truth assessment, creating a full circuit of civilizational intelligence.
"""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

def publish(*args, **kwargs):
    """Proxy for orchestrator.semantic_mirror.publish."""
    from orchestrator import semantic_mirror
    return semantic_mirror.publish(*args, **kwargs)

def get_context(*args, **kwargs):
    """Proxy for orchestrator.semantic_mirror.get_context."""
    from orchestrator import semantic_mirror
    return semantic_mirror.get_context(*args, **kwargs)



def publish_deployment_feedback(
    phase: str,
    slo_ok: bool,
    transform_rate: float,
    rollback: bool = False,
    error_rate: Optional[float] = None,
    decision_id: Optional[str] = None
) -> None:
    """Emit deployment feedback for adaptive cognition upstream.

    Args:
        phase: Deployment phase ("canary", "consensus", "rollout", "rollback")
        slo_ok: Whether SLOs/success criteria were met
        transform_rate: Fraction ∈ [0,1] of content requiring cultural transformation
        rollback: Whether a rollback occurred
        error_rate: Optional error rate ∈ [0,1] during deployment
    """
    try:

        # Normalize inputs
        transform_rate = max(0.0, min(1.0, float(transform_rate)))
        error_rate = max(0.0, min(1.0, float(error_rate or 0.0)))

        feedback_data = {
            "phase": str(phase),
            "slo_ok": bool(slo_ok),
            "transform_rate": transform_rate,
            "rollback": bool(rollback),
            "error_rate": error_rate,
            "timestamp": time.time(),
        }

        # Phase 5.0: Include decision_id for ANR correlation
        if decision_id is None:
            try:
                ctx = get_context("router.current_decision_id") or {}
                decision_id = ctx.get("id")
            except Exception:
                pass

        if decision_id:
            feedback_data["decision_id"] = decision_id

        # Publish feedback with 5-minute TTL for upstream adaptation
        publish(
            "slot10.deployment_feedback",
            feedback_data,
            "slot10_civilizational_deployment",
            ttl=300.0,
        )

        logger.info(
            f"Slot10 feedback: phase={phase} slo_ok={slo_ok} "
            f"transform_rate={transform_rate:.3f} rollback={rollback} "
            f"error_rate={error_rate:.3f}"
        )

        # Update metrics
        _update_feedback_metrics(feedback_data)

    except Exception as e:
        logger.warning(f"Failed to publish deployment feedback: {e}")


def get_deployment_feedback() -> Optional[dict]:
    """Read current deployment feedback from semantic mirror.

    Returns:
        Dict with deployment feedback data or None if no recent feedback
    """
    try:
        return get_context("slot10.deployment_feedback")
    except Exception as e:
        logger.debug(f"Failed to read deployment feedback: {e}")
        return None


def compute_cultural_adjustment(transform_rate: float, rollback: bool) -> dict:
    """Compute recommended cultural synthesis adjustments based on deployment outcomes.

    Args:
        transform_rate: Fraction of content requiring cultural transformation
        rollback: Whether a rollback occurred

    Returns:
        Dict with adjustment recommendations for Slot6
    """
    adjustments = {
        "residual_risk_delta": 0.0,
        "adaptation_effectiveness_delta": 0.0,
        "recommended_action": "maintain",
    }

    # High transform rate → become more conservative (increase residual risk)
    if transform_rate > 0.4:
        adjustments["residual_risk_delta"] = 0.15 * transform_rate
        adjustments["recommended_action"] = "stricter_validation"

    # Rollback → significant conservatism increase + memory stabilization
    if rollback:
        adjustments["residual_risk_delta"] += 0.25
        adjustments["adaptation_effectiveness_delta"] = -0.20
        adjustments["recommended_action"] = "stabilize_memory"

    # Low transform rate → can be more adaptive
    elif transform_rate < 0.1:
        adjustments["adaptation_effectiveness_delta"] = 0.10
        adjustments["recommended_action"] = "increase_adaptation"

    return adjustments


def apply_tri_feedback_signal(rollback: bool, error_rate: float) -> None:
    """Send feedback signal to Slot4 TRI for truth validation adjustment.

    Args:
        rollback: Whether a rollback occurred
        error_rate: Error rate during deployment
    """
    try:

        # Compute TRI adjustment signal
        tri_signal = {
            "strict_mode": rollback or error_rate > 0.1,
            "validation_boost": min(0.3, error_rate * 2.0),
            "reason": "deployment_feedback",
            "timestamp": time.time(),
        }

        # Signal TRI to increase validation rigor
        publish(
            "slot4.tri_feedback",
            tri_signal,
            "slot10_deployment_feedback",
            ttl=180.0,  # 3-minute TRI adjustment window
        )

        logger.info(f"Slot10→Slot4 TRI signal: strict_mode={tri_signal['strict_mode']} "
                   f"validation_boost={tri_signal['validation_boost']:.3f}")

    except Exception as e:
        logger.warning(f"Failed to send TRI feedback signal: {e}")


def _update_feedback_metrics(feedback_data: dict) -> None:
    """Update Prometheus metrics for deployment feedback observability."""
    try:
        # Import locally to avoid hard dependency
        from orchestrator.prometheus_metrics import (
            deployment_feedback_transform_rate_gauge,
            deployment_feedback_rollback_counter,
            deployment_feedback_total_counter
        )

        deployment_feedback_transform_rate_gauge.set(feedback_data["transform_rate"])
        deployment_feedback_total_counter.labels(
            phase=feedback_data["phase"],
            slo_ok=str(feedback_data["slo_ok"])
        ).inc()

        if feedback_data["rollback"]:
            deployment_feedback_rollback_counter.inc()

    except Exception as e:
        logger.debug(f"Deployment feedback metrics update failed: {e}")


# Integration hooks for deployment controllers
def on_canary_complete(success: bool, transform_rate: float, error_rate: float = 0.0) -> None:
    """Hook for canary deployment completion."""
    publish_deployment_feedback(
        phase="canary",
        slo_ok=success,
        transform_rate=transform_rate,
        rollback=not success,
        error_rate=error_rate
    )

    if not success or error_rate > 0.05:
        apply_tri_feedback_signal(rollback=not success, error_rate=error_rate)


def on_rollback_triggered(phase: str, reason: str, transform_rate: float = 0.0) -> None:
    """Hook for rollback events."""
    publish_deployment_feedback(
        phase=f"rollback_{phase}",
        slo_ok=False,
        transform_rate=transform_rate,
        rollback=True,
        error_rate=1.0  # Rollback implies high error condition
    )

    # Strong TRI signal on rollback
    apply_tri_feedback_signal(rollback=True, error_rate=1.0)

    logger.warning(f"Deployment rollback triggered: phase={phase} reason={reason}")


def on_deployment_success(phase: str, transform_rate: float) -> None:
    """Hook for successful deployment completion."""
    publish_deployment_feedback(
        phase=phase,
        slo_ok=True,
        transform_rate=transform_rate,
        rollback=False,
        error_rate=0.0
    )

    # Reset TRI to normal mode on success
    if transform_rate < 0.1:
        apply_tri_feedback_signal(rollback=False, error_rate=0.0)
