"""
Phase 16: Agency Pressure Detection

Discriminates benign from harmful asymmetry by detecting agency pressure primitives.

Key components:
- harm_formula: detect_harm_status(extraction_present, A_p) -> status
- primitives: 5 structural agency pressure patterns
- core: AgencyPressureDetector (turn-by-turn A_p computation)
- models: AgencyPressureResult data model

See: docs/specs/phase16_agency_pressure_design.md
"""

from nova.phase16.harm_formula import detect_harm_status
from nova.phase16.models import AgencyPressureResult
from nova.phase16.primitives import detect_primitives, PRIMITIVES

__all__ = [
    "detect_harm_status",
    "AgencyPressureResult",
    "detect_primitives",
    "PRIMITIVES",
]
