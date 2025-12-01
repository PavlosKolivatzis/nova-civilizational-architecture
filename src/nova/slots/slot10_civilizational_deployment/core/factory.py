"""Factory for building canary controllers with Light-Clock integration."""
import os
from typing import Optional

from .canary import CanaryController
from .lightclock_canary import LightClockCanaryController
from .lightclock_gatekeeper import LightClockGatekeeper
from .gatekeeper import Gatekeeper
from .policy import Slot10Policy
from .health_feed import HealthFeedAdapter, MockHealthFeed
from .audit import AuditLog
from .metrics import CanaryMetricsExporter


class MirrorReader:
    """Minimal interface for reading mirror data."""
    def read(self, key: str, default=None):
        return default

class SemanticMirrorAdapter(MirrorReader):
    """Adapter to connect Semantic Mirror to LightClockGatekeeper."""

    def __init__(self):
        try:
            from nova.orchestrator.semantic_mirror import get_semantic_mirror
            self.semantic_mirror = get_semantic_mirror()
        except ImportError:
            self.semantic_mirror = None

    def read(self, key: str, default=None):
        """Read from Semantic Mirror with slot10 deployment context."""
        if not self.semantic_mirror:
            return default

        try:
            return self.semantic_mirror.get_context(key, "slot10_deployment")
        except Exception:
            return default


def build_canary_controller(
    policy: Optional[Slot10Policy] = None,
    health_feed: Optional[HealthFeedAdapter] = None,
    audit: Optional[AuditLog] = None,
    metrics_exporter: Optional[CanaryMetricsExporter] = None
) -> CanaryController:
    """Build appropriate canary controller based on environment flags."""

    # Default arguments
    if policy is None:
        policy = Slot10Policy()
    if health_feed is None:
        health_feed = MockHealthFeed()

    # Check if Light-Clock gating is enabled
    if os.getenv("NOVA_LIGHTCLOCK_GATING", "1") == "1":
        # Build Light-Clock enhanced controller
        mirror = SemanticMirrorAdapter()
        lightclock_gatekeeper = LightClockGatekeeper(mirror=mirror)

        return LightClockCanaryController(
            policy=policy,
            lightclock_gatekeeper=lightclock_gatekeeper,
            health_feed=health_feed,
            audit=audit,
            metrics_exporter=metrics_exporter,
        )
    else:
        # Build standard controller
        gatekeeper = Gatekeeper(policy=policy, health_feed=health_feed)

        return CanaryController(
            policy=policy,
            gatekeeper=gatekeeper,
            health_feed=health_feed,
            audit=audit,
            metrics_exporter=metrics_exporter
        )


def get_lightclock_gate_summary() -> dict:
    """Get Light-Clock gate summary for monitoring/debugging."""
    if os.getenv("NOVA_LIGHTCLOCK_GATING", "1") == "0":
        return {"enabled": False, "reason": "feature_disabled"}

    try:
        mirror = SemanticMirrorAdapter()
        gatekeeper = LightClockGatekeeper(mirror=mirror)

        # Get dummy gate evaluation to see current state
        dummy_result = gatekeeper.evaluate_deploy_gate({}, {})

        return {
            "enabled": True,
            "phase_lock": dummy_result.phase_lock_value,
            "tri_score": dummy_result.tri_score,
            "slot9_policy": dummy_result.slot9_policy,
            "coherence_level": dummy_result.coherence_level,
            "gate_passes": dummy_result.lightclock_passes,
            "gate_reason": dummy_result.lightclock_reason,
            "failed_conditions": dummy_result.failed_conditions
        }
    except Exception as e:
        return {"enabled": True, "error": str(e)}
