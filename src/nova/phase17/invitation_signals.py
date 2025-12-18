"""
Invitation signal detection for Phase 17 Consent Gate.

Implements Step 1 from Phase 17.0 specification (Table 1.1).
Detects observable signals that authorize assistant to reduce user agency.

Conservative default: Absence of clear signal → no invitation.
"""

import re
from typing import List, Dict


# Invitation signal patterns (from Phase 17.0 Step 1.1)
INVITATION_PATTERNS = {
    "task_delegation": [
        r"\b(can you|could you|please|would you)\s+\w+",  # "Can you [verb]" (any task verb)
        r"\bi need help\s+(with|setting up|configuring|debugging)\b",
        r"\bhelp me\s+(with|write|create|fix|debug|refactor)\b",
    ],
    "role_assignment": [
        r"\byou handle\s+the\b",
        r"\bact as\s+(my|a|an)\b",
        r"\byou(?:'re| are) in charge of\b",
    ],
    "open_question": [
        r"\bi don't know\s+(how to|what to|where to)\b",
        r"\bwhat should i\s+(do|use|choose)\b",
        r"\bhow (?:do i|should i|can i)\b",
    ],
    "proposal_acceptance": [
        r"\byes,?\s+(go ahead|proceed|do it|that(?:'s| is) fine)\b",
        r"\bgo ahead\b",
        r"\bsounds good\b",
        r"\bthat(?:'s| is) fine\b",
    ],
    "clarification_request": [
        r"\bwhich\s+(is better|should i|one)\b",
        r"\bwhat(?:'s| is) the best\s+(approach|way|method|option)\b",
        r"\brecommend\b",
    ],
    "dependency_expression": [
        r"\bi can't do this alone\b",
        r"\bi(?:'ll| will) need your help\b",
        r"\bi need\s+(ongoing|continued|your)\s+(?:help|support|guidance)\b",
    ],
}


def detect_invitation_signals(
    conversation_history: List[Dict[str, str]],
    dimension: str,
) -> List[str]:
    """
    Detect invitation signals from Step 1 (Table 1.1) in conversation history.

    Args:
        conversation_history: List of {"role": "user"|"assistant", "content": str}
        dimension: Agency dimension ("decision", "epistemic", "option", "relational")

    Returns:
        List of detected signals (e.g., ["task_delegation", "role_assignment"])

    Signals checked (from Step 1.1):
        - Explicit task delegation
        - Role assignment
        - Open question / uncertainty
        - Proposal acceptance
        - Clarification request
        - Dependency expression

    Method:
        Structural pattern matching on user turns only.
        No semantic inference.
        Conservative default: No match → no invitation.
    """
    detected = []

    # Only check user turns
    user_turns = [
        turn["content"] for turn in conversation_history if turn["role"] == "user"
    ]

    # Check each invitation pattern type
    for signal_name, patterns in INVITATION_PATTERNS.items():
        for user_turn in user_turns:
            for pattern in patterns:
                if re.search(pattern, user_turn, flags=re.IGNORECASE):
                    if signal_name not in detected:
                        detected.append(signal_name)
                    break  # Found signal, move to next signal type

    return detected


def check_temporal_proximity(
    conversation_history: List[Dict[str, str]],
    invitation_signals: List[str],
    current_turn_index: int,
    max_gap: int = 5,
) -> bool:
    """
    Check if invitation signals are temporally proximate to current turn.

    From Phase 17.0 Step 1.1:
    "Temporal proximity – Invitation applies to the immediate context (not permanent)"

    Args:
        conversation_history: Full conversation history
        invitation_signals: List of detected invitation signals
        current_turn_index: Index of current assistant turn
        max_gap: Maximum turn gap to consider proximate (default: 5)

    Returns:
        True if invitation signals are within max_gap turns of current turn

    Conservative default:
        If no invitation signals → False
        If invitation signals too far back → False
    """
    if not invitation_signals:
        return False

    # Find last user turn with invitation signal
    last_invitation_turn = -1
    user_turns_checked = 0

    for i in range(len(conversation_history) - 1, -1, -1):
        turn = conversation_history[i]
        if turn["role"] == "user":
            user_turns_checked += 1
            # Re-check this turn for invitation patterns
            for patterns in INVITATION_PATTERNS.values():
                for pattern in patterns:
                    if re.search(pattern, turn["content"], flags=re.IGNORECASE):
                        last_invitation_turn = i
                        break
                if last_invitation_turn != -1:
                    break
        if last_invitation_turn != -1:
            break

    if last_invitation_turn == -1:
        return False  # No invitation found

    # Check temporal proximity
    turn_gap = current_turn_index - last_invitation_turn
    return turn_gap <= max_gap
