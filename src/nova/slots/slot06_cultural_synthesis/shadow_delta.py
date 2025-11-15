"""
Shadow Delta Counter for Cultural Synthesis Context Awareness

Tracks when cultural synthesis decisions change due to Semantic Mirror context
availability. Used for measuring the impact of contextual intelligence without
affecting production behavior.

Usage Example:
    from nova.slots.slot06_cultural_synthesis.shadow_delta import record_changed, get_and_reset

    # In cultural synthesis logic:
    baseline_result = synthesize_without_context(input_data)
    context_aware_result = synthesize_with_context(input_data, mirror_context)

    # Record if context changed the decision
    record_changed(baseline_result, context_aware_result)

    # Periodically collect metrics:
    delta_count = get_and_reset()
    print(f"Context influenced {delta_count} synthesis decisions")
"""

# Global counter for shadow delta tracking
_shadow_delta_counter = 0


def record_changed(before: dict, after: dict) -> None:
    """
    Record when a synthesis result changed due to context awareness.

    Args:
        before: Synthesis result without context
        after: Synthesis result with context influence

    Note:
        Compares dictionaries by value equality. Any difference in the
        result structure, values, or keys counts as a context-influenced change.
    """
    global _shadow_delta_counter
    if before != after:
        _shadow_delta_counter += 1


def get_and_reset() -> int:
    """
    Get current shadow delta count and reset counter to zero.

    Returns:
        Number of synthesis decisions influenced by context since last reset
    """
    global _shadow_delta_counter
    count = _shadow_delta_counter
    _shadow_delta_counter = 0
    return count


def get_current_count() -> int:
    """
    Get current shadow delta count without resetting.

    Returns:
        Number of synthesis decisions influenced by context since last reset
    """
    global _shadow_delta_counter
    return _shadow_delta_counter


def reset_counter() -> None:
    """Reset the shadow delta counter to zero without returning the count."""
    global _shadow_delta_counter
    _shadow_delta_counter = 0
