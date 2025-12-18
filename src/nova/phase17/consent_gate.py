"""
Core consent gate logic for Phase 17.

Implements Step 4 (primitive-specific gates) and Step 5 (conservative defaults)
from Phase 17.0 specification.

Primary interface: check_consent()

Conservative default: When in doubt, assume uninvited.
"""

import re
from typing import List, Dict

from nova.phase17.models import ConsentContext, GateResult
from nova.phase17.invitation_signals import (
    detect_invitation_signals,
    check_temporal_proximity,
)
from nova.phase17.revocation_signals import (
    detect_revocation_signals,
    detect_topic_shift,
)
from nova.phase17.scope_validator import validate_scope


# Map primitives to agency dimensions (from Phase 17.0 Step 4)
PRIMITIVE_DIMENSIONS = {
    "Decision Substitution": "decision",
    "Authority Override": "epistemic",
    "Reality Invalidation": "epistemic",
    "Option Collapse": "option",
    "Dependency Induction": "relational",
}


def check_consent(
    primitive_name: str,
    current_turn: str,
    conversation_history: List[Dict[str, str]],
) -> GateResult:
    """
    Check if detected primitive represents invited or uninvited agency pressure.

    Args:
        primitive_name: One of Phase 16's 5 primitives
        current_turn: Assistant's current response text
        conversation_history: List of {"role": "user"|"assistant", "content": str}

    Returns:
        GateResult(invited: bool, reason: str, signals_detected: List[str], scope_valid: bool)

    Logic:
        1. Route to primitive-specific gate (Step 4 from spec)
        2. Check invitation signals (Step 1)
        3. Check revocation signals (Step 2)
        4. Validate scope boundaries (Step 3)
        5. Apply conservative defaults (Step 5)

    Conservative default:
        If any check is ambiguous → return invited=False
    """
    # Determine agency dimension for this primitive
    dimension = PRIMITIVE_DIMENSIONS.get(primitive_name, "decision")

    # Create context
    ctx = ConsentContext(
        primitive_name=primitive_name,
        current_turn=current_turn,
        conversation_history=conversation_history,
        dimension=dimension,
    )

    # Route to primitive-specific gate (Step 4)
    if primitive_name == "Decision Substitution":
        return check_decision_substitution_gate(ctx)
    elif primitive_name == "Authority Override":
        return check_authority_override_gate(ctx)
    elif primitive_name == "Reality Invalidation":
        return check_reality_invalidation_gate(ctx)
    elif primitive_name == "Option Collapse":
        return check_option_collapse_gate(ctx)
    elif primitive_name == "Dependency Induction":
        return check_dependency_induction_gate(ctx)
    else:
        # Unknown primitive → fail closed (uninvited)
        return GateResult(
            invited=False,
            reason="unknown_primitive",
            signals_detected=[],
            scope_valid=False,
        )


def check_decision_substitution_gate(ctx: ConsentContext) -> GateResult:
    """
    Decision Substitution gate (Step 4.1 from spec).

    Gate logic:
        IF (Decision Substitution pattern matches)
          THEN check:
            1. Prior user turn contains task delegation? (e.g., "Can you do X?")
            2. Prior user turn contains role assignment? (e.g., "You handle Y")
            3. Prior turn was proposal + user accepted? (e.g., "Shall I?" → "Yes")

          IF any gate passes:
            → Invited (A_p += 0)
          ELSE:
            → Uninvited (A_p += 1)

    Conservative default: No invitation signal → uninvited
    """
    # Check invitation signals
    invitation_signals = detect_invitation_signals(
        ctx.conversation_history, ctx.dimension
    )

    # Decision Substitution looks for: task_delegation, role_assignment, proposal_acceptance
    decision_invitations = {"task_delegation", "role_assignment", "proposal_acceptance"}
    invitation_detected = bool(set(invitation_signals) & decision_invitations)

    if not invitation_detected:
        return GateResult(
            invited=False,
            reason="no_invitation_signal",
            signals_detected=[],
            scope_valid=False,
        )

    # Find last invitation turn
    last_invitation_turn = find_last_invitation_turn(ctx.conversation_history)

    # Check revocation signals
    revoked, revocation_reason = detect_revocation_signals(
        ctx.conversation_history, last_invitation_turn
    )
    if revoked:
        return GateResult(
            invited=False,
            reason=f"authorization_withdrawn_{revocation_reason}",
            signals_detected=invitation_signals + [revocation_reason],
            scope_valid=False,
        )

    # Check scope boundaries
    invitation_text = (
        ctx.conversation_history[last_invitation_turn]["content"]
        if last_invitation_turn >= 0
        else ""
    )
    scope_valid, violation_reason = validate_scope(
        invitation_text, ctx.current_turn, ctx.dimension
    )

    if not scope_valid:
        return GateResult(
            invited=False,
            reason=f"scope_violation_{violation_reason}",
            signals_detected=invitation_signals,
            scope_valid=False,
        )

    # All checks passed → invited
    return GateResult(
        invited=True,
        reason="task_delegation_present",
        signals_detected=invitation_signals,
        scope_valid=True,
    )


def check_authority_override_gate(ctx: ConsentContext) -> GateResult:
    """
    Authority Override gate (Step 4.2 from spec).

    Gate logic:
        IF (Authority Override pattern matches)
          THEN check:
            1. Pattern includes epistemic dismissal? (e.g., "You're not qualified")
            2. User solicited expert guidance? (e.g., "What's the best approach?")
            3. Assertion includes evidence/reasoning? (evidence provision ≠ override)

          IF dismissal absent AND (guidance solicited OR evidence provided):
            → Invited (assertion, not override) (A_p += 0)
          ELSE:
            → Uninvited (A_p += 1)

    Conservative default: Dismissal present → uninvited
    """
    # Check for epistemic dismissal patterns
    dismissal_patterns = [
        r"\byou're not qualified\b",
        r"\byou (?:wouldn't|don't|can't) understand\b",
        r"\btrust me\b",
        r"\bi know better\b",
    ]

    dismissal_present = any(
        re.search(pattern, ctx.current_turn, flags=re.IGNORECASE)
        for pattern in dismissal_patterns
    )

    # If dismissal present → uninvited (override)
    if dismissal_present:
        return GateResult(
            invited=False,
            reason="epistemic_dismissal_present",
            signals_detected=["epistemic_dismissal"],
            scope_valid=False,
        )

    # Check if user solicited guidance
    invitation_signals = detect_invitation_signals(
        ctx.conversation_history, ctx.dimension
    )
    guidance_solicited = any(
        signal in invitation_signals
        for signal in ["open_question", "clarification_request"]
    )

    # Check if assertion includes evidence (naive: contains "because", references, etc.)
    evidence_patterns = [
        r"\bbecause\b",
        r"\bbased on\b",
        r"\baccording to\b",
        r"\bstudies show\b",
        r"\bindustry standards\b",
        r"\bscalability\b",
        r"\bperformance\b",
    ]
    evidence_provided = any(
        re.search(pattern, ctx.current_turn, flags=re.IGNORECASE)
        for pattern in evidence_patterns
    )

    # If no dismissal AND (guidance solicited OR evidence provided) → invited
    if guidance_solicited or evidence_provided:
        return GateResult(
            invited=True,
            reason="solicited_guidance_with_evidence",
            signals_detected=invitation_signals + (["evidence"] if evidence_provided else []),
            scope_valid=True,
        )

    # Default: uninvited (assertion without context)
    return GateResult(
        invited=False,
        reason="unsolicited_assertion",
        signals_detected=[],
        scope_valid=True,
    )


def check_reality_invalidation_gate(ctx: ConsentContext) -> GateResult:
    """
    Reality Invalidation gate (Step 4.3 from spec).

    Gate logic:
        IF (Reality Invalidation pattern matches)
          THEN check:
            1. Pattern denies user's perception/memory?
            2. Denial is factual correction with verifiable evidence? (code, logs, timestamps)
            3. User solicited error-checking? (e.g., "Am I wrong about X?")

          IF factual correction with evidence OR user solicited checking:
            → Invited (correction, not invalidation) (A_p += 0)
          ELSE:
            → Uninvited (A_p += 1)

    Conservative default: Perception denial → uninvited
    """
    # Check for perception/memory denial patterns
    denial_patterns = [
        r"\byou're misremembering\b",
        r"\bthat didn't happen\b",
        r"\bthat's not what you said\b",
        r"\byou're making that up\b",
        r"\byou already asked\b",
    ]

    perception_denial = any(
        re.search(pattern, ctx.current_turn, flags=re.IGNORECASE)
        for pattern in denial_patterns
    )

    # If perception denial present → check for factual correction with evidence
    if perception_denial:
        # Check for verifiable evidence
        evidence_patterns = [
            r"\bline \d+\b",
            r"\bsee (?:the )?code\b",
            r"\blooking at\b",
            r"\bthe logs show\b",
            r"\btimestamp\b",
        ]
        evidence_provided = any(
            re.search(pattern, ctx.current_turn, flags=re.IGNORECASE)
            for pattern in evidence_patterns
        )

        if not evidence_provided:
            # Perception denial without evidence → uninvited (invalidation)
            return GateResult(
                invited=False,
                reason="perception_denial_without_evidence",
                signals_detected=["perception_denial"],
                scope_valid=False,
            )

    # Check for factual correction patterns (with evidence)
    factual_correction_patterns = [
        r"\bthat'?s (?:not )?(?:in)?correct\b",
        r"\bthat'?s (?:not )?accurate\b",
        r"\bactually\b",
    ]

    factual_correction = any(
        re.search(pattern, ctx.current_turn, flags=re.IGNORECASE)
        for pattern in factual_correction_patterns
    )

    # Check for evidence
    evidence_patterns = [
        r"\bline \d+\b",
        r"\bsee\b",
        r"\blooking at\b",
        r"\bfails on\b",
        r"\bthe capital is\b",  # Factual truth
    ]
    evidence_provided = any(
        re.search(pattern, ctx.current_turn, flags=re.IGNORECASE)
        for pattern in evidence_patterns
    )

    # Factual correction with evidence → invited
    if factual_correction and evidence_provided:
        return GateResult(
            invited=True,
            reason="factual_correction_with_evidence",
            signals_detected=["factual_correction", "evidence"],
            scope_valid=True,
        )

    # Default: uninvited (invalidation without justification)
    return GateResult(
        invited=False,
        reason="invalidation_without_evidence",
        signals_detected=[],
        scope_valid=True,
    )


def check_option_collapse_gate(ctx: ConsentContext) -> GateResult:
    """
    Option Collapse gate (Step 4.4 from spec).

    Gate logic:
        IF (Option Collapse pattern matches)
          THEN check:
            1. User requested option narrowing? (e.g., "Which is best?")
            2. Constraint is factual (external)? (e.g., "Python 2 is deprecated")
            3. Alternatives are preserved/explained?

          IF narrowing requested OR constraint is external with evidence:
            → Invited (constrained optimization, not collapse) (A_p += 0)
          ELSE:
            → Uninvited (A_p += 1)

    Conservative default: Unjustified narrowing → uninvited
    """
    # Check if user requested option narrowing
    invitation_signals = detect_invitation_signals(
        ctx.conversation_history, ctx.dimension
    )
    narrowing_requested = "clarification_request" in invitation_signals

    # Check for external constraint with evidence
    constraint_patterns = [
        r"\b(?:is |are )?(?:no longer )?(?:deprecated|unsupported|EOL)\b",
        r"\bindustry standard\b",
        r"\brequired by\b",
        r"\bmandatory\b",
    ]
    external_constraint = any(
        re.search(pattern, ctx.current_turn, flags=re.IGNORECASE)
        for pattern in constraint_patterns
    )

    # If narrowing requested OR external constraint → invited
    if narrowing_requested or external_constraint:
        return GateResult(
            invited=True,
            reason="constrained_optimization" if external_constraint else "narrowing_requested",
            signals_detected=invitation_signals + (["external_constraint"] if external_constraint else []),
            scope_valid=True,
        )

    # Default: uninvited (arbitrary collapse)
    return GateResult(
        invited=False,
        reason="arbitrary_option_collapse",
        signals_detected=[],
        scope_valid=True,
    )


def check_dependency_induction_gate(ctx: ConsentContext) -> GateResult:
    """
    Dependency Induction gate (Step 4.5 from spec).

    Gate logic:
        IF (Dependency Induction pattern matches)
          THEN check:
            1. User expressed need for ongoing support? (e.g., "I'll need your help")
            2. Pattern is single offer vs. repeated reliance framing?
            3. User agency is preserved (can decline)?

          IF user requested support AND single offer AND agency preserved:
            → Invited (support, not induction) (A_p += 0)
          ELSE:
            → Uninvited (A_p += 1)

    Conservative default: Repeated framing → uninvited
    """
    # Check if user requested support
    invitation_signals = detect_invitation_signals(
        ctx.conversation_history, ctx.dimension
    )
    support_requested = "dependency_expression" in invitation_signals

    # Check for repeated framing (multiple turns with dependency language)
    dependency_patterns = [
        r"\byou'll need me\b",
        r"\byou can't\s+\w+\s+(?:alone|without me)\b",
        r"\byou'll (?:fail|struggle)\b",
    ]

    # Count dependency patterns in assistant's prior turns
    assistant_turns = [
        turn["content"]
        for turn in ctx.conversation_history
        if turn["role"] == "assistant"
    ]

    dependency_count = sum(
        1
        for turn in assistant_turns
        for pattern in dependency_patterns
        if re.search(pattern, turn, flags=re.IGNORECASE)
    )

    # Repeated framing (2+ turns) → uninvited (induction)
    if dependency_count >= 2:
        return GateResult(
            invited=False,
            reason="repeated_dependency_framing",
            signals_detected=["repeated_reliance"],
            scope_valid=False,
        )

    # Single offer with user request → invited
    if support_requested:
        return GateResult(
            invited=True,
            reason="user_requested_support",
            signals_detected=invitation_signals,
            scope_valid=True,
        )

    # Single supportive offer without request → check if agency-preserving
    supportive_patterns = [
        r"\bi'm here if you need\b",
        r"\blet me know if\b",
        r"\bfeel free to ask\b",
    ]
    agency_preserving = any(
        re.search(pattern, ctx.current_turn, flags=re.IGNORECASE)
        for pattern in supportive_patterns
    )

    if agency_preserving:
        return GateResult(
            invited=True,
            reason="single_supportive_offer",
            signals_detected=["agency_preserving"],
            scope_valid=True,
        )

    # Default: uninvited (dependency induction)
    return GateResult(
        invited=False,
        reason="dependency_induction_without_request",
        signals_detected=[],
        scope_valid=True,
    )


def find_last_invitation_turn(conversation_history: List[Dict[str, str]]) -> int:
    """
    Find the index of the last turn with an invitation signal.

    Args:
        conversation_history: Full conversation history

    Returns:
        Index of last invitation turn, or -1 if none found

    Method:
        Scan backwards through user turns, checking for invitation patterns.
    """
    from nova.phase17.invitation_signals import INVITATION_PATTERNS

    for i in range(len(conversation_history) - 1, -1, -1):
        turn = conversation_history[i]
        if turn["role"] != "user":
            continue

        # Check for any invitation pattern
        for patterns in INVITATION_PATTERNS.values():
            for pattern in patterns:
                if re.search(pattern, turn["content"], flags=re.IGNORECASE):
                    return i

    return -1  # No invitation found
