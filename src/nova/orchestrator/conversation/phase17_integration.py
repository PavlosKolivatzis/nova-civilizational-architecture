"""
Phase 17 consent gate integration for conversation processing.

Implements the integration contract from Phase 17.0 spec:
1. Detect primitives (Phase 16, context-blind)
2. Check consent (Phase 17, context-aware)
3. Count pressured turns only when uninvited

Feature-flagged: NOVA_ENABLE_CONSENT_GATE
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def build_provenance_metadata(
    session_id: str,
    turn_index: int,
    primitives_detected: List[str],
    primitives_uninvited: List[str],
    gate_reasons: List[str],
    context_length: int,
) -> Dict[str, Any]:
    """
    Build provenance metadata for a gated signal (C3: metadata-only, no behavior change).

    Args:
        session_id: Conversation session identifier
        turn_index: Index of this turn in conversation history
        primitives_detected: All primitives found by Phase 16 (context-blind)
        primitives_uninvited: Primitives that failed consent gate (Phase 17)
        gate_reasons: Human-readable reasons for gate decisions
        context_length: Number of turns in conversation history

    Returns:
        Provenance metadata dict (lossless projection of existing state)
    """
    return {
        "session_id": session_id,
        "turn_index": turn_index,
        "phase16_primitives_detected": primitives_detected,
        "phase17_primitives_uninvited": primitives_uninvited,
        "consent_gate_enabled": is_consent_gate_enabled(),
        "gate_reasons": gate_reasons,
        "context_length": context_length,
    }


def is_consent_gate_enabled() -> bool:
    """
    Check if Phase 17 consent gate is enabled.

    Returns:
        True if NOVA_ENABLE_CONSENT_GATE=1
    """
    return os.getenv("NOVA_ENABLE_CONSENT_GATE", "0") == "1"


def analyze_turn_with_consent_gate(
    turn_content: str,
    conversation_history: List[Dict[str, str]],
    session_id: Optional[str] = None,
    turn_index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Analyze a single assistant turn for agency pressure with consent gate.

    Implements Phase 17 integration contract:
    1. Detect primitives using Phase 16 (context-blind)
    2. Check consent for each primitive using Phase 17 (context-aware)
    3. Return analysis with uninvited primitives only

    Args:
        turn_content: Assistant's turn text
        conversation_history: Full conversation up to and including current turn
            List[{"role": "user"|"assistant", "content": str}]
        session_id: Optional session identifier (for provenance metadata)
        turn_index: Optional turn index (for provenance metadata)

    Returns:
        Dict containing:
            - primitives_detected: List[str] (all primitives found, structure-only)
            - primitives_uninvited: List[str] (primitives that are uninvited)
            - consent_results: List[GateResult] (consent gate results per primitive)
            - is_pressured: bool (True if any uninvited primitive)
            - provenance: Dict (if session_id and turn_index provided, C3 metadata)

    Example:
        >>> history = [
        ...     {"role": "user", "content": "Can you help me debug?"},
        ...     {"role": "assistant", "content": "I'll check the logs for you."},
        ... ]
        >>> result = analyze_turn_with_consent_gate(history[-1]["content"], history)
        >>> result["is_pressured"]
        False  # "I'll check" is invited (user requested help)
    """
    # Step 1: Detect primitives (Phase 16, context-blind)
    try:
        from nova.phase16.primitives import detect_primitives

        primitives_detected = list(detect_primitives(turn_content))
    except Exception as exc:
        logger.warning(f"Failed to import Phase 16 primitives: {exc}")
        return {
            "primitives_detected": [],
            "primitives_uninvited": [],
            "consent_results": [],
            "is_pressured": False,
            "error": f"phase16_import_failed: {exc}",
        }

    if not primitives_detected:
        # No primitives detected → not pressured
        result = {
            "primitives_detected": [],
            "primitives_uninvited": [],
            "consent_results": [],
            "is_pressured": False,
        }

        # C3: Attach provenance metadata if session info provided
        if session_id is not None and turn_index is not None:
            result["provenance"] = build_provenance_metadata(
                session_id=session_id,
                turn_index=turn_index,
                primitives_detected=[],
                primitives_uninvited=[],
                gate_reasons=["no_primitives_detected"],
                context_length=len(conversation_history),
            )

        return result

    # Step 2: Check consent gate (Phase 17, context-aware) if enabled
    if is_consent_gate_enabled():
        try:
            from nova.phase17 import check_consent

            consent_results = []
            primitives_uninvited = []

            for primitive in primitives_detected:
                gate_result = check_consent(primitive, turn_content, conversation_history)
                consent_results.append(gate_result)

                if gate_result.contributes_to_A_p():  # uninvited
                    primitives_uninvited.append(primitive)

            is_pressured = len(primitives_uninvited) > 0

            result = {
                "primitives_detected": primitives_detected,
                "primitives_uninvited": primitives_uninvited,
                "consent_results": consent_results,
                "is_pressured": is_pressured,
            }

            # C3: Attach provenance metadata if session info provided
            if session_id is not None and turn_index is not None:
                gate_reasons = [str(gr) for gr in consent_results]
                result["provenance"] = build_provenance_metadata(
                    session_id=session_id,
                    turn_index=turn_index,
                    primitives_detected=primitives_detected,
                    primitives_uninvited=primitives_uninvited,
                    gate_reasons=gate_reasons,
                    context_length=len(conversation_history),
                )

            return result

        except Exception as exc:
            logger.error(f"Failed to check consent gate: {exc}")
            # Fallback to naive detection on error
            return {
                "primitives_detected": primitives_detected,
                "primitives_uninvited": primitives_detected,  # assume all uninvited on error
                "consent_results": [],
                "is_pressured": True,
                "error": f"consent_gate_failed: {exc}",
            }
    else:
        # Naive detection (structure-only, falsified by RT-862)
        # All detected primitives are treated as pressured
        logger.debug("Consent gate disabled, using naive detection")
        result = {
            "primitives_detected": primitives_detected,
            "primitives_uninvited": primitives_detected,  # naive: all primitives = pressured
            "consent_results": [],
            "is_pressured": len(primitives_detected) > 0,
            "mode": "naive",
        }

        # C3: Attach provenance metadata if session info provided
        if session_id is not None and turn_index is not None:
            result["provenance"] = build_provenance_metadata(
                session_id=session_id,
                turn_index=turn_index,
                primitives_detected=primitives_detected,
                primitives_uninvited=primitives_detected,  # naive mode
                gate_reasons=["naive_mode: all primitives treated as uninvited"],
                context_length=len(conversation_history),
            )

        return result


def compute_session_agency_pressure(
    conversation_history: List[Dict[str, str]],
    extraction_present: bool = True,
) -> Dict[str, Any]:
    """
    Compute agency pressure (A_p) for entire conversation session.

    Implements Phase 17 integration pattern:
    - Analyze each assistant turn with consent gate
    - Count turns with uninvited primitives
    - Compute A_p = (uninvited turns) / (total assistant turns)

    Args:
        conversation_history: Full conversation history
        extraction_present: Slot02 temporal extraction flag (default: True)

    Returns:
        Dict containing:
            - A_p: float (0.0-1.0, agency pressure score)
            - total_turns: int (total assistant turns)
            - pressured_turns: int (turns with uninvited primitives)
            - harm_status: str (benign, asymmetric_benign, observation, concern, harm)
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
            "A_p": 0.0,
            "total_turns": 0,
            "pressured_turns": 0,
            "harm_status": "benign",
            "turn_analyses": [],
            "consent_gate_enabled": is_consent_gate_enabled(),
        }

    turn_analyses = []
    pressured_turns = 0

    for turn_index, turn in assistant_turns:
        # Get conversation history up to and including this turn
        history_slice = conversation_history[: turn_index + 1]

        # Analyze turn with consent gate
        analysis = analyze_turn_with_consent_gate(turn["content"], history_slice)
        analysis["turn_index"] = turn_index
        turn_analyses.append(analysis)

        if analysis["is_pressured"]:
            pressured_turns += 1

    total_turns = len(assistant_turns)
    A_p = pressured_turns / total_turns if total_turns > 0 else 0.0

    # Get harm status from Phase 16 formula
    try:
        from nova.phase16.harm_formula import detect_harm_status

        harm_status = detect_harm_status(extraction_present, A_p)
    except Exception as exc:
        logger.warning(f"Failed to compute harm status: {exc}")
        harm_status = "unknown"

    return {
        "A_p": A_p,
        "total_turns": total_turns,
        "pressured_turns": pressured_turns,
        "harm_status": harm_status,
        "turn_analyses": turn_analyses,
        "consent_gate_enabled": is_consent_gate_enabled(),
    }
