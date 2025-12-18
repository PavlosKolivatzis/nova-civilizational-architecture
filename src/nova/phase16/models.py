"""Data models for Phase 16 Agency Pressure Detection."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AgencyPressureResult:
    """
    Result of agency pressure detection for a conversation session.

    Attributes:
        A_p: Agency pressure scalar (0.0-1.0), computed as (pressured_turns / total_turns)
        total_turns: Total number of turns analyzed
        pressured_turns: Number of turns containing agency pressure primitives
        primitives_detected: List of primitive names detected across all turns
        harm_status: Harm classification (benign, asymmetric_benign, observation, concern, harm)
        escalation_trend: Escalation direction (escalating, de-escalating, stable, N/A)
        turn_by_turn_A_p: Optional list of A_p values at each turn (running accumulation)
    """

    A_p: float
    total_turns: int
    pressured_turns: int
    primitives_detected: List[str]
    harm_status: str
    escalation_trend: str = "N/A"
    turn_by_turn_A_p: Optional[List[float]] = field(default_factory=list)

    def __post_init__(self):
        """Validate A_p range."""
        if not (0.0 <= self.A_p <= 1.0):
            raise ValueError(f"A_p must be in [0.0, 1.0], got {self.A_p}")
