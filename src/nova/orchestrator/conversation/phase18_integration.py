"""
Phase 18 Slot02 manipulation pattern consent gate integration.

Implements context-aware routing for Slot02 manipulation patterns:
1. Detect patterns (Slot02, context-blind)
2. Check consent (Phase 18, context-aware)
3. Count manipulation pressure only when uninvited

Feature-flagged: NOVA_ENABLE_SLOT02_CONSENT_GATE

Architectural parallel to Phase 17 agency pressure consent gate.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def is_slot02_consent_gate_enabled() -> bool:
    """
    Check if Phase 18 Slot02 consent gate is enabled.

    Returns:
        True if NOVA_ENABLE_SLOT02_CONSENT_GATE=1
    """
    return os.getenv("NOVA_ENABLE_SLOT02_CONSENT_GATE", "0") == "1"


# Consent Signal Patterns (Structural Only)

EDUCATIONAL_REQUEST = [
    re.compile(
        r"\b(explain|describe|what\s+(?:is|are))\s+.*?\s*(?:manipulation|persuasion|rhetoric|tactic)",
        re.I,
    ),
    re.compile(r"\b(teach|show|demonstrate)\s+(?:me\s+)?(?:how|examples?\s+of)", re.I),
    re.compile(r"\bcan\s+you\s+(?:explain|describe|list|tell\s+me\s+about)\b", re.I),
]

META_DISCUSSION = [
    re.compile(r"\b(quote|cited?|said|claimed|argues?\s+that)\b", re.I),
    re.compile(r"\b(example|instance|case\s+(?:study|where))\b", re.I),
    re.compile(r"\b(not|don't|avoid|never)\s+(?:use|say|claim)\b", re.I),
]

REVOCATION_SIGNALS = [
    re.compile(r"\b(stop|enough|too\s+much|back\s+off)\b", re.I),
    re.compile(r"\b(don't|do\s+not)\s+(?:explain|tell|use)\b", re.I),
    re.compile(
        r"\b(just\s+)?(?:answer|tell)\s+(?:me\s+)?(?:directly|simply|plainly)\b", re.I
    ),
]

# Quoted text detection (simple structural signal)
QUOTED_TEXT = [
    re.compile(r'"[^"]{10,}"', re.I),  # Double quotes with substantial content
    re.compile(r"'[^']{10,}'", re.I),  # Single quotes with substantial content
    re.compile(r"`[^`]{10,}`", re.I),  # Backticks (code/technical quotes)
]


@dataclass
class ManipulationGateResult:
    """Result from manipulation pattern consent gate check."""

    pattern_layer: str  # "delta", "sigma", "theta", "omega"
    invited: bool  # True if pattern usage is invited/benign
    reason: str  # Human-readable gate decision
    invitation_turn: Optional[int] = None  # Turn index where invitation detected
    pattern_in_quotes: bool = False  # True if pattern found in quoted text


def check_educational_invitation(
    conversation_history: List[Dict[str, str]], lookback_turns: int = 5
) -> Optional[int]:
    """
    Check if user requested educational/explanatory content.

    Args:
        conversation_history: Full conversation history
        lookback_turns: How many recent turns to check

    Returns:
        Turn index where invitation was detected, or None
    """
    # Look at recent user turns only
    user_turns = [
        (i, turn)
        for i, turn in enumerate(conversation_history)
        if turn["role"] == "user"
    ]

    # Check last N user turns
    recent_user_turns = user_turns[-lookback_turns:] if user_turns else []

    for turn_index, turn in reversed(recent_user_turns):
        content = turn["content"]
        for pattern in EDUCATIONAL_REQUEST:
            if pattern.search(content):
                return turn_index

    return None


def check_meta_discussion_signal(turn_content: str) -> bool:
    """
    Check if turn contains meta-discussion signals (quoted, examples, negation).

    Args:
        turn_content: Turn text to check

    Returns:
        True if meta-discussion signals detected
    """
    for pattern in META_DISCUSSION:
        if pattern.search(turn_content):
            return True
    return False


def check_revocation_signal(
    conversation_history: List[Dict[str, str]], lookback_turns: int = 3
) -> Optional[int]:
    """
    Check if user withdrew consent for detailed explanations.

    Args:
        conversation_history: Full conversation history
        lookback_turns: How many recent turns to check

    Returns:
        Turn index where revocation was detected, or None
    """
    user_turns = [
        (i, turn)
        for i, turn in enumerate(conversation_history)
        if turn["role"] == "user"
    ]

    recent_user_turns = user_turns[-lookback_turns:] if user_turns else []

    for turn_index, turn in reversed(recent_user_turns):
        content = turn["content"]
        for pattern in REVOCATION_SIGNALS:
            if pattern.search(content):
                return turn_index

    return None


def check_quoted_text(turn_content: str, pattern_text: str) -> bool:
    """
    Check if manipulation pattern appears within quoted text.

    Args:
        turn_content: Full turn text
        pattern_text: Specific pattern text to check (e.g., "undeniable truth")

    Returns:
        True if pattern appears within quotes
    """
    # Simple heuristic: check if pattern appears within quoted segments
    for quote_pattern in QUOTED_TEXT:
        for match in quote_pattern.finditer(turn_content):
            quoted_segment = match.group(0)
            if pattern_text.lower() in quoted_segment.lower():
                return True

    return False


def check_manipulation_consent(
    pattern_layer: str,
    turn_content: str,
    conversation_history: List[Dict[str, str]],
) -> ManipulationGateResult:
    """
    Check if detected manipulation pattern is invited/benign.

    Implements Phase 18 consent gate logic:
    1. Check if pattern in quoted text → invited
    2. Check for educational invitation → invited
    3. Check for revocation → uninvited
    4. Default → uninvited

    Args:
        pattern_layer: Manipulation layer ("delta", "sigma", "theta", "omega")
        turn_content: Assistant's turn text
        conversation_history: Full conversation history

    Returns:
        ManipulationGateResult with invitation status and reason
    """
    # Step 1: Check if pattern in quoted text
    # (Simple check: look for quotes in turn content)
    pattern_in_quotes = any(
        quote_pattern.search(turn_content) for quote_pattern in QUOTED_TEXT
    )
    if pattern_in_quotes:
        return ManipulationGateResult(
            pattern_layer=pattern_layer,
            invited=True,
            reason="quoted_text",
            pattern_in_quotes=True,
        )

    # Step 2: Check for revocation (takes precedence over invitation)
    revocation_turn = check_revocation_signal(conversation_history)
    if revocation_turn is not None:
        return ManipulationGateResult(
            pattern_layer=pattern_layer,
            invited=False,
            reason="consent_revoked",
            invitation_turn=None,
        )

    # Step 3: Check for educational invitation
    invitation_turn = check_educational_invitation(conversation_history)
    if invitation_turn is not None:
        # Check if turn also has meta-discussion signals
        has_meta = check_meta_discussion_signal(turn_content)
        reason = (
            "educational_request+meta_discussion" if has_meta else "educational_request"
        )

        return ManipulationGateResult(
            pattern_layer=pattern_layer,
            invited=True,
            reason=reason,
            invitation_turn=invitation_turn,
        )

    # Step 4: Default - no invitation found
    return ManipulationGateResult(
        pattern_layer=pattern_layer,
        invited=False,
        reason="no_invitation_found",
    )


def analyze_turn_with_slot02_gate(
    turn_content: str,
    conversation_history: List[Dict[str, str]],
    session_id: Optional[str] = None,
    turn_index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Analyze assistant turn for manipulation patterns with consent gate.

    Implements Phase 18 integration:
    1. Detect patterns using Slot02 (context-blind)
    2. Check consent for detected patterns using Phase 18 (context-aware)
    3. Return analysis with uninvited patterns only

    Args:
        turn_content: Assistant's turn text
        conversation_history: Full conversation history
        session_id: Optional session identifier (for provenance)
        turn_index: Optional turn index (for provenance)

    Returns:
        Dict containing:
            - patterns_detected: Dict[str, float] (all layers, Slot02 scores)
            - patterns_uninvited: Dict[str, float] (uninvited layers only)
            - gate_results: List[ManipulationGateResult]
            - is_manipulative: bool (True if any uninvited pattern)
            - provenance: Dict (if session_id and turn_index provided)
    """
    # Step 1: Detect patterns using Slot02 (context-blind)
    try:
        from nova.slots.slot02_deltathresh.patterns import PatternDetector

        detector = PatternDetector()
        patterns_detected = detector.detect_patterns(turn_content)
    except Exception as exc:
        logger.warning(f"Failed to import Slot02 patterns: {exc}")
        return {
            "patterns_detected": {},
            "patterns_uninvited": {},
            "gate_results": [],
            "is_manipulative": False,
            "error": f"slot02_import_failed: {exc}",
        }

    # Filter to patterns with score > 0
    detected_layers = {
        layer: score for layer, score in patterns_detected.items() if score > 0
    }

    if not detected_layers:
        # No patterns detected → not manipulative
        result = {
            "patterns_detected": patterns_detected,
            "patterns_uninvited": {},
            "gate_results": [],
            "is_manipulative": False,
        }

        # Attach provenance if session info provided
        if session_id is not None and turn_index is not None:
            result["provenance"] = build_slot02_provenance_metadata(
                session_id=session_id,
                turn_index=turn_index,
                patterns_detected=patterns_detected,
                patterns_uninvited={},
                gate_reasons=["no_patterns_detected"],
                context_length=len(conversation_history),
            )

        return result

    # Step 2: Check consent gate (Phase 18, context-aware) if enabled
    if is_slot02_consent_gate_enabled():
        gate_results = []
        patterns_uninvited = {}

        for layer in detected_layers:
            gate_result = check_manipulation_consent(
                pattern_layer=layer,
                turn_content=turn_content,
                conversation_history=conversation_history,
            )
            gate_results.append(gate_result)

            if not gate_result.invited:  # uninvited
                patterns_uninvited[layer] = patterns_detected[layer]

        is_manipulative = len(patterns_uninvited) > 0

        result = {
            "patterns_detected": patterns_detected,
            "patterns_uninvited": patterns_uninvited,
            "gate_results": gate_results,
            "is_manipulative": is_manipulative,
        }

        # Attach provenance if session info provided
        if session_id is not None and turn_index is not None:
            gate_reasons = [gr.reason for gr in gate_results]
            result["provenance"] = build_slot02_provenance_metadata(
                session_id=session_id,
                turn_index=turn_index,
                patterns_detected=patterns_detected,
                patterns_uninvited=patterns_uninvited,
                gate_reasons=gate_reasons,
                context_length=len(conversation_history),
            )

        return result

    else:
        # Naive mode: all detected patterns = manipulative
        logger.debug("Slot02 consent gate disabled, using naive detection")
        result = {
            "patterns_detected": patterns_detected,
            "patterns_uninvited": detected_layers,  # naive: all detected = uninvited
            "gate_results": [],
            "is_manipulative": len(detected_layers) > 0,
            "mode": "naive",
        }

        # Attach provenance if session info provided
        if session_id is not None and turn_index is not None:
            result["provenance"] = build_slot02_provenance_metadata(
                session_id=session_id,
                turn_index=turn_index,
                patterns_detected=patterns_detected,
                patterns_uninvited=detected_layers,
                gate_reasons=["naive_mode: all detected patterns treated as uninvited"],
                context_length=len(conversation_history),
            )

        return result


def build_slot02_provenance_metadata(
    session_id: str,
    turn_index: int,
    patterns_detected: Dict[str, float],
    patterns_uninvited: Dict[str, float],
    gate_reasons: List[str],
    context_length: int,
) -> Dict[str, Any]:
    """
    Build provenance metadata for Slot02 manipulation signals (C3 pattern).

    Args:
        session_id: Conversation session identifier
        turn_index: Index of this turn
        patterns_detected: All patterns found by Slot02 (context-blind)
        patterns_uninvited: Patterns that failed consent gate (Phase 18)
        gate_reasons: Human-readable reasons for gate decisions
        context_length: Number of turns in conversation history

    Returns:
        Provenance metadata dict (lossless projection)
    """
    return {
        "session_id": session_id,
        "turn_index": turn_index,
        "slot02_patterns_detected": patterns_detected,
        "slot02_patterns_uninvited": patterns_uninvited,
        "consent_gate_enabled": is_slot02_consent_gate_enabled(),
        "gate_reasons": gate_reasons,
        "context_length": context_length,
    }


def compute_session_manipulation_pressure(
    conversation_history: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Compute manipulation pressure (M_p) for entire conversation session.

    Implements Phase 18 integration:
    - Analyze each assistant turn with Slot02 consent gate
    - Count turns with uninvited manipulation patterns
    - Compute M_p = (uninvited turns) / (total assistant turns)

    Args:
        conversation_history: Full conversation history

    Returns:
        Dict containing:
            - M_p: float (0.0-1.0, manipulation pressure score)
            - total_turns: int (total assistant turns)
            - manipulative_turns: int (turns with uninvited patterns)
            - turn_analyses: List[Dict] (per-turn analysis results)
            - consent_gate_enabled: bool
    """
    assistant_turns = [
        (i, turn)
        for i, turn in enumerate(conversation_history)
        if turn["role"] == "assistant"
    ]

    if not assistant_turns:
        return {
            "M_p": 0.0,
            "total_turns": 0,
            "manipulative_turns": 0,
            "turn_analyses": [],
            "consent_gate_enabled": is_slot02_consent_gate_enabled(),
        }

    turn_analyses = []
    manipulative_turns = 0

    for turn_index, turn in assistant_turns:
        # Get conversation history up to and including this turn
        history_slice = conversation_history[: turn_index + 1]

        # Analyze turn with Slot02 consent gate
        analysis = analyze_turn_with_slot02_gate(turn["content"], history_slice)
        analysis["turn_index"] = turn_index
        turn_analyses.append(analysis)

        if analysis["is_manipulative"]:
            manipulative_turns += 1

    total_turns = len(assistant_turns)
    M_p = manipulative_turns / total_turns if total_turns > 0 else 0.0

    return {
        "M_p": M_p,
        "total_turns": total_turns,
        "manipulative_turns": manipulative_turns,
        "turn_analyses": turn_analyses,
        "consent_gate_enabled": is_slot02_consent_gate_enabled(),
    }
