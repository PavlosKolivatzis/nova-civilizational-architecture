"""Autonomy Governor (AG) — Phase 10.0.

Self-regulating decision boundaries enforcing TRI ≥ 0.8 and ethical constraints.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from collections import deque


@dataclass
class BoundaryEvent:
    """AG decision boundary event (throttle/escalate/hold)."""

    timestamp: str
    eai: float
    action: str  # 'throttle', 'escalate', 'hold'
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class AutonomyGovernor:
    """AG decision throttle and escalation engine."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize AG with configuration."""
        self.config = config or {}

        # Thresholds
        self.tri_min = self.config.get("tri_min", 0.80)
        self.eai_target = self.config.get("eai_target", 0.85)
        self.eai_throttle_threshold = self.config.get("eai_throttle_threshold", 0.75)
        self.csi_min = self.config.get("csi_min", 0.75)

        # State tracking
        self.total_decisions = 0
        self.safe_decisions = 0
        self.throttle_events: List[BoundaryEvent] = []
        self.escalation_events: List[BoundaryEvent] = []

        # Rolling window for EAI computation (14-day default)
        self.decision_window = deque(maxlen=self.config.get("decision_window_size", 200))

        # Current metrics cache
        self._current_tri = 0.81  # Default from Phase 4.0
        self._current_csi = 0.78  # Default from Phase 8.0
        self._consensus_quality = 1.0  # Default FCQ

    def update_metrics(
        self,
        tri: Optional[float] = None,
        csi: Optional[float] = None,
        fcq: Optional[float] = None,
    ):
        """Update cached metrics from external sources."""
        if tri is not None:
            self._current_tri = tri
        if csi is not None:
            self._current_csi = csi
        if fcq is not None:
            self._consensus_quality = fcq

    def compute_eai(self) -> float:
        """Compute Ethical Autonomy Index.

        Formula: EAI = (safe_decisions / total_decisions) × consensus_quality
        """
        if self.total_decisions == 0:
            return 1.0  # No decisions yet = perfect (cautious default)

        base_ratio = self.safe_decisions / self.total_decisions
        eai = base_ratio * self._consensus_quality

        return round(eai, 4)

    def check_decision_boundary(
        self,
        _decision_type: str = "autonomous",
        **kwargs
    ) -> Dict[str, Any]:
        """Check if decision should proceed, throttle, or escalate.

        Returns:
            - action: 'proceed', 'throttle', 'escalate'
            - reason: Explanation
            - eai: Current EAI
        """
        eai = self.compute_eai()

        # Check TRI violation (highest priority)
        if self._current_tri < self.tri_min:
            event = BoundaryEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                eai=eai,
                action="escalate",
                reason=f"tri_violation: {self._current_tri:.3f} < {self.tri_min}",
                metadata={"tri": self._current_tri, "threshold": self.tri_min},
            )
            self.escalation_events.append(event)

            return {
                "action": "escalate",
                "reason": event.reason,
                "eai": eai,
                "requires_human_review": True,
            }

        # Check CSI stability
        if self._current_csi < self.csi_min:
            event = BoundaryEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                eai=eai,
                action="escalate",
                reason=f"csi_instability: {self._current_csi:.3f} < {self.csi_min}",
                metadata={"csi": self._current_csi, "threshold": self.csi_min},
            )
            self.escalation_events.append(event)

            return {
                "action": "escalate",
                "reason": event.reason,
                "eai": eai,
                "requires_human_review": True,
            }

        # Check EAI throttle threshold
        if eai < self.eai_throttle_threshold:
            event = BoundaryEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                eai=eai,
                action="throttle",
                reason=f"eai_low: {eai:.3f} < {self.eai_throttle_threshold}",
                metadata={"eai": eai, "threshold": self.eai_throttle_threshold},
            )
            self.throttle_events.append(event)

            return {
                "action": "throttle",
                "reason": event.reason,
                "eai": eai,
                "requires_human_review": False,
            }

        # Decision can proceed
        return {
            "action": "proceed",
            "reason": "within_bounds",
            "eai": eai,
            "requires_human_review": False,
        }

    def record_decision(self, safe: bool, **metadata):
        """Record autonomous decision outcome."""
        self.total_decisions += 1
        if safe:
            self.safe_decisions += 1

        self.decision_window.append({
            "safe": safe,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
        })

    def get_throttle_rate(self, window_hours: int = 6) -> float:
        """Compute throttle event rate over time window."""
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        recent_throttles = [
            e for e in self.throttle_events
            if datetime.fromisoformat(e.timestamp) > cutoff
        ]

        return len(recent_throttles) / window_hours if window_hours > 0 else 0.0

    def get_escalation_rate(self, window_hours: int = 6) -> float:
        """Compute escalation event rate over time window."""
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        recent_escalations = [
            e for e in self.escalation_events
            if datetime.fromisoformat(e.timestamp) > cutoff
        ]

        return len(recent_escalations) / window_hours if window_hours > 0 else 0.0

    def get_metrics(self) -> Dict[str, Any]:
        """Export AG operational metrics."""
        eai = self.compute_eai()

        return {
            "eai": eai,
            "tri": self._current_tri,
            "csi": self._current_csi,
            "fcq": self._consensus_quality,
            "total_decisions": self.total_decisions,
            "safe_decisions": self.safe_decisions,
            "throttle_events_total": len(self.throttle_events),
            "escalation_events_total": len(self.escalation_events),
            "throttle_rate_6h": self.get_throttle_rate(6),
            "escalation_rate_6h": self.get_escalation_rate(6),
            "within_bounds": eai >= self.eai_target and self._current_tri >= self.tri_min,
        }

    def export_boundary_log(self) -> Dict[str, Any]:
        """Export audit trail of boundary events."""
        return {
            "throttle_events": [
                {
                    "timestamp": e.timestamp,
                    "eai": e.eai,
                    "action": e.action,
                    "reason": e.reason,
                    "metadata": e.metadata,
                }
                for e in self.throttle_events
            ],
            "escalation_events": [
                {
                    "timestamp": e.timestamp,
                    "eai": e.eai,
                    "action": e.action,
                    "reason": e.reason,
                    "metadata": e.metadata,
                }
                for e in self.escalation_events
            ],
        }
