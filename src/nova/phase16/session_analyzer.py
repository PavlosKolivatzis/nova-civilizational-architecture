"""
Session analyzer for Phase 16 Agency Pressure Detection.

Provides session-level analysis of conversation turns for agency pressure,
exporting Prometheus metrics and providing governance recommendations.

Intended use:
- Evidentiary RT analysis (post-session)
- Integration blueprint for real-time orchestrator (future)
"""

import logging
from typing import List, Optional, Dict, Any

from nova.phase16.core import AgencyPressureDetector
from nova.phase16.models import AgencyPressureResult

logger = logging.getLogger(__name__)


class SessionAnalyzer:
    """
    Analyzes conversation sessions for agency pressure and harm potential.

    Designed for post-session analysis (RT evidence) with future hooks
    for real-time integration.
    """

    def __init__(self):
        """Initialize session analyzer with Phase 16 detector."""
        self.detector = AgencyPressureDetector()

    def analyze_session(
        self,
        session_id: str,
        turns: List[str],
        extraction_present: bool = True,
        export_metrics: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze a conversation session for agency pressure.

        Args:
            session_id: Session identifier
            turns: List of conversation turns (assistant responses)
            extraction_present: Slot02 temporal extraction flag (asymmetry detected)
            export_metrics: Whether to export Prometheus metrics (requires NOVA_ENABLE_AGENCY_PRESSURE=1)

        Returns:
            Dict containing:
                - agency_pressure_result: AgencyPressureResult object
                - governance_recommendation: Recommended Slot07 regime
                - session_summary: Human-readable summary

        Example:
            >>> analyzer = SessionAnalyzer()
            >>> turns = ["I'll decide for you.", "Trust me, I'm the expert."]
            >>> result = analyzer.analyze_session("test-session", turns, extraction_present=True)
            >>> result["agency_pressure_result"].A_p
            1.0
            >>> result["governance_recommendation"]
            'restrictive'
        """
        # Run Phase 16 detector
        ap_result = self.detector.analyze(turns, extraction_present)

        # Export Prometheus metrics if requested
        if export_metrics:
            try:
                from nova.orchestrator.prometheus_metrics import (
                    record_phase16_agency_pressure_metrics,
                )

                record_phase16_agency_pressure_metrics(session_id, ap_result)
            except Exception as exc:
                logger.warning(
                    "Failed to export Phase 16 metrics (flag disabled or import failed): %s",
                    exc,
                )

        # Generate governance recommendation (Step 5.3 mapping)
        governance_recommendation = self._recommend_governance_regime(ap_result)

        # Generate human-readable summary
        session_summary = self._generate_summary(session_id, ap_result)

        return {
            "agency_pressure_result": ap_result,
            "governance_recommendation": governance_recommendation,
            "session_summary": session_summary,
        }

    def _recommend_governance_regime(self, ap_result: AgencyPressureResult) -> str:
        """
        Recommend Slot07 governance regime based on harm_status.

        Mapping from Step 5.3:
            - benign, asymmetric_benign, observation → permissive (default)
            - concern → balanced or restrictive (operator discretion)
            - harm → restrictive or safety_mode (mandatory tightening)

        Args:
            ap_result: AgencyPressureResult from detector

        Returns:
            regime: "permissive", "balanced", "restrictive", or "safety_mode"
        """
        harm_status = ap_result.harm_status

        regime_map = {
            "benign": "permissive",
            "asymmetric_benign": "permissive",
            "observation": "permissive",
            "concern": "balanced",  # Could be restrictive based on operator policy
            "harm": "restrictive",  # Could be safety_mode for A_p=1.0
        }

        regime = regime_map.get(harm_status, "permissive")

        # Escalate to safety_mode for critical harm (A_p=1.0 sustained pressure)
        if harm_status == "harm" and ap_result.A_p == 1.0:
            regime = "safety_mode"

        return regime

    def _generate_summary(
        self, session_id: str, ap_result: AgencyPressureResult
    ) -> str:
        """
        Generate human-readable summary of session analysis.

        Args:
            session_id: Session identifier
            ap_result: AgencyPressureResult from detector

        Returns:
            summary: Formatted summary string
        """
        lines = [
            f"Session: {session_id}",
            f"Total Turns: {ap_result.total_turns}",
            f"Pressured Turns: {ap_result.pressured_turns}",
            f"A_p (Agency Pressure): {ap_result.A_p:.2f}",
            f"Harm Status: {ap_result.harm_status}",
            f"Escalation Trend: {ap_result.escalation_trend}",
        ]

        if ap_result.primitives_detected:
            primitives_str = ", ".join(ap_result.primitives_detected)
            lines.append(f"Primitives Detected: {primitives_str}")
        else:
            lines.append("Primitives Detected: None")

        if ap_result.turn_by_turn_A_p:
            A_p_evolution = " → ".join(f"{x:.2f}" for x in ap_result.turn_by_turn_A_p)
            lines.append(f"A_p Evolution: {A_p_evolution}")

        return "\n".join(lines)
