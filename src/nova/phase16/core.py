"""
Core agency pressure detection logic for Phase 16.

AgencyPressureDetector: Main class for turn-by-turn A_p computation and harm assessment.
"""

from typing import List, Optional
from nova.phase16.models import AgencyPressureResult
from nova.phase16.primitives import detect_primitives
from nova.phase16.harm_formula import detect_harm_status, check_escalation


class AgencyPressureDetector:
    """
    Detects agency pressure across conversation turns.

    Computes A_p (agency pressure scalar) as:
        A_p = (number of turns with pressure primitives) / (total turns)

    Provides turn-by-turn A_p evolution for escalation detection.
    """

    def __init__(self):
        """Initialize detector (stateless, no configuration needed)."""
        pass

    def analyze(
        self,
        turns: List[str],
        extraction_present: bool = True,
    ) -> AgencyPressureResult:
        """
        Analyze conversation turns for agency pressure and compute harm status.

        Args:
            turns: List of conversation turns (assistant responses)
            extraction_present: Slot02 temporal extraction flag (default True for testing)

        Returns:
            AgencyPressureResult with A_p, harm_status, primitives, and trend

        Examples:
            >>> detector = AgencyPressureDetector()
            >>> turns = ["I'll decide for you.", "Trust me, I'm the expert."]
            >>> result = detector.analyze(turns, extraction_present=True)
            >>> result.A_p
            1.0
            >>> result.harm_status
            'harm'
            >>> result.primitives_detected
            ['Decision Substitution', 'Authority Override']
        """
        if not turns:
            return AgencyPressureResult(
                A_p=0.0,
                total_turns=0,
                pressured_turns=0,
                primitives_detected=[],
                harm_status="benign",
                escalation_trend="N/A",
                turn_by_turn_A_p=[],
            )

        total_turns = len(turns)
        primitives_per_turn = [detect_primitives(turn) for turn in turns]

        # Count turns with at least one primitive
        pressured_turns = sum(1 for prims in primitives_per_turn if prims)

        # Compute final A_p
        A_p = pressured_turns / total_turns if total_turns > 0 else 0.0

        # Collect all unique primitives detected
        all_primitives = set()
        for prims in primitives_per_turn:
            all_primitives.update(prims)
        primitives_detected = sorted(list(all_primitives))

        # Compute turn-by-turn A_p (running accumulation)
        turn_by_turn_A_p = self._compute_running_A_p(primitives_per_turn)

        # Detect escalation trend (compare last two A_p values if available)
        escalation_trend = self._detect_escalation_trend(turn_by_turn_A_p)

        # Get harm status from formula
        harm_status = detect_harm_status(extraction_present, A_p)

        return AgencyPressureResult(
            A_p=A_p,
            total_turns=total_turns,
            pressured_turns=pressured_turns,
            primitives_detected=primitives_detected,
            harm_status=harm_status,
            escalation_trend=escalation_trend,
            turn_by_turn_A_p=turn_by_turn_A_p,
        )

    def _compute_running_A_p(self, primitives_per_turn: List[set]) -> List[float]:
        """
        Compute running A_p at each turn.

        Args:
            primitives_per_turn: List of primitive sets, one per turn

        Returns:
            List of A_p values after each turn (cumulative)

        Examples:
            >>> detector = AgencyPressureDetector()
            >>> prims = [{'A'}, set(), {'B'}, set()]
            >>> detector._compute_running_A_p(prims)
            [1.0, 0.5, 0.67, 0.5]
        """
        running_A_p = []
        pressured_count = 0

        for i, prims in enumerate(primitives_per_turn):
            if prims:  # Turn has at least one primitive
                pressured_count += 1
            turn_num = i + 1
            A_p_at_turn = pressured_count / turn_num
            running_A_p.append(round(A_p_at_turn, 2))  # Round for readability

        return running_A_p

    def _detect_escalation_trend(self, turn_by_turn_A_p: List[float]) -> str:
        """
        Detect escalation trend from turn-by-turn A_p evolution.

        Args:
            turn_by_turn_A_p: List of A_p values at each turn

        Returns:
            trend: "escalating", "de-escalating", "stable", or "N/A"

        Examples:
            >>> detector = AgencyPressureDetector()
            >>> detector._detect_escalation_trend([0.0, 0.5, 1.0])
            'escalating'
            >>> detector._detect_escalation_trend([1.0, 0.5, 0.33])
            'de-escalating'
            >>> detector._detect_escalation_trend([0.5, 0.5, 0.5])
            'stable'
            >>> detector._detect_escalation_trend([0.5])
            'N/A'
        """
        if len(turn_by_turn_A_p) < 2:
            return "N/A"  # Not enough data

        # Compare last two A_p values
        A_p_current = turn_by_turn_A_p[-1]
        A_p_previous = turn_by_turn_A_p[-2]

        return check_escalation(A_p_current, A_p_previous)
