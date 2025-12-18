"""
Revocation signal detection for Phase 17 Consent Gate.

Implements Step 2 from Phase 17.0 specification (Tables 2.1, 2.2).
Detects signals that user withdraws previously granted authorization.

Conservative default: Any revocation signal → authorization withdrawn.
"""

import re
from typing import List, Dict, Tuple, Optional


# Explicit revocation patterns (from Phase 17.0 Step 2.1)
REVOCATION_PATTERNS = {
    "explicit_rejection": [
        r"\bno,?\s+don't\s+(do that|)\b",
        r"\bstop\b",
        r"\bwait\b",
        r"\bhold on\b",
        r"\bcancel\b",
    ],
    "agency_reclaimed": [
        r"\bactually,?\s+i'?ll\s+handle\s+it\b",
        r"\blet me\s+(decide|do it|handle)\b",
        r"\bi'?ll\s+(do it|take care of it)\s+myself\b",
    ],
    "scope_narrowing": [
        r"\bjust\s+(show|explain|list)\b.+don't\s+(choose|decide|execute)\b",
        r"\bexplain.+don't\s+(do|execute|implement)\b",
    ],
    "interruption": [
        r"\bhold on\b",
        r"\bwait\b",
        r"\bi changed my mind\b",
    ],
    "alternative_assertion": [
        r"\bno,?\s+do\s+\w+\s+instead\b",
        r"\bi prefer\s+\w+\b",
    ],
}


# Completion signals (from Phase 17.0 Step 2.2)
COMPLETION_PATTERNS = [
    r"\bthat'?s\s+done\b",
    r"\bthanks?,?\s+(?:that'?s\s+)?(?:all|enough|good)\b",
    r"\bwe'?re\s+done\s+with\b",
    r"\bfinished\s+with\b",
]


def detect_revocation_signals(
    conversation_history: List[Dict[str, str]],
    last_invitation_turn: int,
) -> Tuple[bool, Optional[str]]:
    """
    Detect revocation signals from Step 2 (Tables 2.1, 2.2) after last invitation.

    Args:
        conversation_history: List of {"role": "user"|"assistant", "content": str}
        last_invitation_turn: Turn index of last detected invitation

    Returns:
        (revoked: bool, reason: Optional[str])

    Signals checked (from Step 2.1):
        - Explicit rejection
        - Correction / override (agency reclaimed)
        - Scope narrowing
        - Interruption
        - Alternative assertion

    Implicit decay (from Step 2.2):
        - Session boundary (always revoked cross-session)
        - Topic shift
        - Time decay (multi-turn gap)
        - Completion signal

    Method:
        Check all user turns after last_invitation_turn.
        Any revocation signal → return (True, reason).

    Conservative default:
        If revocation detected → authorization withdrawn.
    """
    # Check explicit revocation patterns
    for i in range(last_invitation_turn + 1, len(conversation_history)):
        turn = conversation_history[i]
        if turn["role"] != "user":
            continue

        content = turn["content"]

        # Check each revocation pattern type
        for signal_name, patterns in REVOCATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, flags=re.IGNORECASE):
                    return (True, signal_name)

        # Check completion signals
        for pattern in COMPLETION_PATTERNS:
            if re.search(pattern, content, flags=re.IGNORECASE):
                return (True, "completion_signal")

    # Check implicit decay (temporal gap)
    # From Phase 17.0 Step 2.2: "Multi-turn gap without reaffirmation"
    user_turns_after_invitation = sum(
        1
        for turn in conversation_history[last_invitation_turn + 1 :]
        if turn["role"] == "user"
    )
    if user_turns_after_invitation > 10:  # Conservative threshold
        return (True, "temporal_decay")

    # No revocation detected
    return (False, None)


def detect_topic_shift(
    conversation_history: List[Dict[str, str]],
    last_invitation_turn: int,
    current_turn_index: int,
) -> bool:
    """
    Detect topic shift between invitation and current turn.

    From Phase 17.0 Step 2.2:
    "Topic shift – Consent is topic-scoped"

    Args:
        conversation_history: Full conversation history
        last_invitation_turn: Turn index of last invitation
        current_turn_index: Index of current assistant turn

    Returns:
        True if topic shift detected (consent revoked)

    Method:
        Naive keyword-based topic tracking.
        If intervening user turns discuss unrelated topics → shift detected.

    Conservative default:
        Ambiguous → assume topic shift (fail closed).
    """
    if last_invitation_turn < 0:
        return True  # No invitation → always shifted

    # Extract keywords from invitation turn
    invitation_turn = conversation_history[last_invitation_turn]
    if invitation_turn["role"] != "user":
        return True  # Sanity check failure

    # Simple keyword extraction (nouns, verbs related to task)
    # This is intentionally naive per spec constraints
    invitation_keywords = set(
        re.findall(r"\b\w{4,}\b", invitation_turn["content"].lower())
    )

    # Check intervening user turns for keyword overlap
    for i in range(last_invitation_turn + 1, min(current_turn_index, len(conversation_history))):
        turn = conversation_history[i]
        if turn["role"] != "user":
            continue

        turn_keywords = set(re.findall(r"\b\w{4,}\b", turn["content"].lower()))

        # If user turn has <20% keyword overlap with invitation → topic shift
        if invitation_keywords:
            overlap = len(invitation_keywords & turn_keywords) / len(
                invitation_keywords
            )
            if overlap < 0.2:  # Conservative threshold
                return True  # Topic shift detected

    return False  # No topic shift
