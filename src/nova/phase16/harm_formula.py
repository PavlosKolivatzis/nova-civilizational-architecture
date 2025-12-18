"""
Harm detection formula for Phase 16 Agency Pressure Detection.

Locked formula from Step 5.2:
    harm = asymmetry (extraction_present) × agency_pressure (A_p)

See: docs/specs/phase16_agency_pressure_design.md (Step 5.2)
"""


def detect_harm_status(extraction_present: bool, A_p: float) -> str:
    """
    Harm detection formula combining Slot02 asymmetry with Phase 16 agency pressure.

    Implements multiplicative gate: Both asymmetry AND pressure required for harm.

    Thresholds (from Step 5.1):
        θ_concern = 0.33 (>1 in 3 turns pressured)
        θ_harm = 0.67 (≥2 in 3 turns pressured)

    Args:
        extraction_present: Slot02 temporal extraction flag (asymmetry detected)
        A_p: Agency pressure scalar (0.0-1.0)

    Returns:
        status: One of:
            - "benign": No asymmetry detected
            - "asymmetric_benign": Asymmetry without agency pressure (A_p=0.0)
            - "observation": Low pressure (0.0 < A_p ≤ 0.33)
            - "concern": Moderate pressure (0.33 < A_p < 0.67)
            - "harm": High sustained pressure (A_p ≥ 0.67)

    Examples:
        >>> detect_harm_status(extraction_present=False, A_p=0.5)
        'benign'
        >>> detect_harm_status(extraction_present=True, A_p=0.0)
        'asymmetric_benign'
        >>> detect_harm_status(extraction_present=True, A_p=0.25)
        'observation'
        >>> detect_harm_status(extraction_present=True, A_p=0.5)
        'concern'
        >>> detect_harm_status(extraction_present=True, A_p=1.0)
        'harm'
    """
    # Validate A_p range
    if not (0.0 <= A_p <= 1.0):
        raise ValueError(f"A_p must be in [0.0, 1.0], got {A_p}")

    if not extraction_present:
        return "benign"  # No asymmetry → benign regardless of A_p

    # extraction_present = True (asymmetry detected)
    if A_p == 0.0:
        return "asymmetric_benign"  # Asymmetry without agency pressure
    elif A_p <= 0.33:
        return "observation"  # Low pressure, watch for escalation
    elif A_p < 0.67:
        return "concern"  # Moderate pressure, escalation watch
    else:  # A_p >= 0.67
        return "harm"  # High sustained pressure


def check_escalation(A_p_current: float, A_p_previous: float) -> str:
    """
    Detect escalation/de-escalation between consecutive A_p measurements.

    Args:
        A_p_current: Current A_p value
        A_p_previous: Previous A_p value

    Returns:
        trend: One of "escalating", "de-escalating", "stable"

    Examples:
        >>> check_escalation(0.5, 0.25)
        'escalating'
        >>> check_escalation(0.25, 0.5)
        'de-escalating'
        >>> check_escalation(0.5, 0.5)
        'stable'
    """
    if A_p_current > A_p_previous:
        return "escalating"  # Pressure increasing
    elif A_p_current < A_p_previous:
        return "de-escalating"  # Pressure dilution
    else:
        return "stable"
