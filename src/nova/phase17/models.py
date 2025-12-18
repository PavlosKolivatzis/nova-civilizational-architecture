"""
Data models for Phase 17 Consent Gate.

Defines structures for consent context and gate evaluation results.
No logic, only data containers.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class ConsentContext:
    """
    Context for consent gate evaluation.

    Attributes:
        primitive_name: One of Phase 16's 5 primitives
        current_turn: Assistant's current response text
        conversation_history: List of {"role": "user"|"assistant", "content": str}
        dimension: Agency dimension ("decision", "epistemic", "option", "relational")
    """
    primitive_name: str
    current_turn: str
    conversation_history: List[Dict[str, str]]
    dimension: str


@dataclass
class GateResult:
    """
    Result of consent gate check.

    Attributes:
        invited: True if agency pressure is invited, False if uninvited
        reason: Human-readable explanation of gate decision
        signals_detected: List of invitation/revocation signals found
        scope_valid: True if action is within scope boundaries
    """
    invited: bool
    reason: str
    signals_detected: List[str]
    scope_valid: bool

    def contributes_to_A_p(self) -> bool:
        """
        Returns True if this primitive should contribute to A_p (uninvited).

        Per Phase 17.0 Step 0 invariant:
        "Agency pressure primitives only contribute to A_p when agency reduction is uninvited."
        """
        return not self.invited
