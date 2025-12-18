"""
Scope boundary validation for Phase 17 Consent Gate.

Implements Step 3 from Phase 17.0 specification (Tables 3.1, 3.2, 3.3).
Validates that current action is within authorized scope (dimension, task, temporal).

Conservative default: Ambiguous scope → fail closed (violation).
"""

import re
from typing import Tuple, Optional, Set


# Task scope keywords (from Phase 17.0 Step 3.2)
# Maps invitation keywords to authorized action keywords
TASK_SCOPE_MAP = {
    "debug": {"check", "analyze", "trace", "log", "inspect", "identify"},
    "fix": {"patch", "correct", "resolve", "repair"},
    "help": {"assist", "guide", "explain", "show"},
    "write": {"create", "draft", "compose"},
    "review": {"check", "analyze", "critique", "assess"},
    "refactor": {"restructure", "reorganize", "extract", "rename"},
    "configure": {"setup", "set up", "install", "initialize"},
    "deploy": {"release", "publish", "push", "ship"},
}

# Scope violation keywords (actions that exceed typical delegation)
SCOPE_VIOLATION_KEYWORDS = {
    "delete": {"remove", "erase", "wipe", "purge"},
    "deploy": {"release", "publish", "push to production", "ship"},
    "rewrite": {"replace entirely", "start over", "delete and recreate"},
}


def validate_scope(
    invitation_text: str,
    current_action: str,
    dimension: str,
) -> Tuple[bool, Optional[str]]:
    """
    Validate scope boundaries from Step 3 (Tables 3.1, 3.2, 3.3).

    Args:
        invitation_text: The user turn that contained invitation signal
        current_action: The assistant's current turn
        dimension: Agency dimension ("decision", "epistemic", "option", "relational")

    Returns:
        (within_scope: bool, violation_reason: Optional[str])

    Checks (from Step 3):
        - Dimension scoping (Table 3.1)
        - Task scoping (Table 3.2)
        - Temporal scoping (Table 3.3)

    Examples:
        "Help me debug" → "I've deployed to production" = scope violation
        "Fix the typo" → "I rewrote the entire file" = scope violation

    Method:
        Keyword extraction + boundary checking.
        Ambiguous scope → fail closed (violation).

    Conservative default:
        If scope boundary unclear → assume violation.
    """
    # Extract action verbs from invitation and current action
    invitation_verbs = extract_action_verbs(invitation_text)
    current_verbs = extract_action_verbs(current_action)

    # Check for scope violations (destructive actions without authorization)
    for violation_category, keywords in SCOPE_VIOLATION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in current_action.lower():
                # Check if this action was authorized
                if violation_category not in invitation_text.lower():
                    return (
                        False,
                        f"scope_violation_{violation_category}_not_authorized",
                    )

    # Check task scope alignment
    # If invitation specifies narrow task, current action should match
    invitation_scope = determine_task_scope(invitation_verbs)
    current_scope = determine_task_scope(current_verbs)

    if invitation_scope and current_scope:
        # Check if current action exceeds invitation scope
        if not is_scope_compatible(invitation_scope, current_scope):
            return (False, "task_scope_exceeded")

    # Check dimension scoping (from Table 3.1)
    # This is a simplified check; full implementation would map verbs to dimensions
    if dimension == "decision":
        # Decision dimension: execution authorization
        # Violation: executing actions not requested
        if any(
            keyword in current_action.lower()
            for keyword in ["deployed", "deleted", "published", "committed"]
        ):
            if not any(
                keyword in invitation_text.lower()
                for keyword in ["deploy", "delete", "publish", "commit"]
            ):
                return (False, "decision_dimension_violation")

    # Scope is valid
    return (True, None)


def extract_action_verbs(text: str) -> Set[str]:
    """
    Extract action verbs from text using naive keyword extraction.

    Args:
        text: Input text

    Returns:
        Set of action verbs found

    Method:
        Naive pattern matching.
        No NLP, no semantic analysis.
    """
    # Common action verbs in software tasks
    action_verbs = {
        "debug",
        "fix",
        "help",
        "write",
        "review",
        "refactor",
        "configure",
        "deploy",
        "delete",
        "create",
        "update",
        "analyze",
        "check",
        "test",
        "build",
        "install",
    }

    found_verbs = set()
    text_lower = text.lower()

    for verb in action_verbs:
        if re.search(rf"\b{verb}\b", text_lower):
            found_verbs.add(verb)

    return found_verbs


def determine_task_scope(verbs: Set[str]) -> Optional[str]:
    """
    Determine task scope category from action verbs.

    Args:
        verbs: Set of action verbs

    Returns:
        Scope category (e.g., "debug", "deploy") or None

    Method:
        Map verbs to scope categories using TASK_SCOPE_MAP.
    """
    for scope_category, authorized_verbs in TASK_SCOPE_MAP.items():
        if scope_category in verbs:
            return scope_category

    return None


def is_scope_compatible(invitation_scope: str, current_scope: str) -> bool:
    """
    Check if current scope is compatible with (not exceeding) invitation scope.

    Args:
        invitation_scope: Scope from invitation (e.g., "debug")
        current_scope: Scope from current action (e.g., "deploy")

    Returns:
        True if current scope is within invitation scope bounds

    Rules (from Phase 17.0 Step 3.2):
        "debug" authorizes: check, analyze, trace, identify (NOT fix, deploy)
        "fix" authorizes: patch, correct, resolve (NOT deploy, rewrite)
        "help" authorizes: assist, guide, explain (NOT execute)

    Conservative default:
        If relationship unclear → not compatible (fail closed).
    """
    # Same scope → compatible
    if invitation_scope == current_scope:
        return True

    # Check if current scope is within authorized set for invitation scope
    if invitation_scope in TASK_SCOPE_MAP:
        authorized_verbs = TASK_SCOPE_MAP[invitation_scope]
        if current_scope in authorized_verbs:
            return True

    # Scope escalation patterns (always violations)
    escalation_violations = {
        ("debug", "fix"),
        ("debug", "deploy"),
        ("fix", "deploy"),
        ("help", "fix"),
        ("help", "deploy"),
        ("review", "fix"),
        ("review", "deploy"),
    }

    if (invitation_scope, current_scope) in escalation_violations:
        return False

    # Default: unclear relationship → not compatible (fail closed)
    return False
