"""Common enumerations used across the NOVA architecture.

This module centralises small ``Enum`` classes that are required by various
modules and tests.  Historically these lived in ad-hoc locations which meant
that imports were fragile and difficult to reuse.  The CI failure referenced in
issue #135 highlighted this when new architecture-validation tests attempted to
import risk and orientation enums that were not available.

The enums defined here are intentionally lightweight – they merely capture the
string values used throughout the test-suite and the application.  By keeping
them in a dedicated module we avoid circular imports and provide a single source
of truth for these symbolic constants.
"""

from enum import Enum

class DeploymentGuardrailResult(Enum):
    APPROVED = "APPROVED"
    REQUIRES_TRANSFORMATION = "REQUIRES_TRANSFORMATION"
    BLOCKED_PRINCIPLE_VIOLATION = "BLOCKED_PRINCIPLE_VIOLATION"
    BLOCKED_CULTURAL_SENSITIVITY = "BLOCKED_CULTURAL_SENSITIVITY"
    ERROR = "ERROR"


# --- Slot 10 architecture validation enums ---------------------------------

class RiskLevel(str, Enum):
    """Generic risk levels used for conflict and escalation modelling."""

    HIGH = "high"
    MED = "med"
    LOW = "low"


class LangOrientation(str, Enum):
    """Word-order orientations for linguistic alignment checks."""

    SVO = "svo"  # Subject–Verb–Object (e.g. English, German)
    SOV = "sov"
    VSO = "vso"
    VOS = "vos"
    OVS = "ovs"
    OSV = "osv"


class PsychologyType(str, Enum):
    """High‑level psychological archetypes used in the matrix payload."""

    COLLECTIVISM = "collectivism"
    INDIVIDUALISM = "individualism"


class DiversityStatus(str, Enum):
    """Support state for diversity dimensions."""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"


class DiversityDimension(str, Enum):
    """Dimensions under which diversity may be evaluated."""

    LINGUISTIC = "linguistic"
    CULTURAL = "cultural"
    ETHNIC = "ethnic"


__all__ = [
    "DeploymentGuardrailResult",
    "RiskLevel",
    "LangOrientation",
    "PsychologyType",
    "DiversityStatus",
    "DiversityDimension",
]

