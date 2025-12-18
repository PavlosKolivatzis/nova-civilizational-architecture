"""
Phase 17: Consent Gate for Agency Pressure Detection.

Implements structural consent/invitation gate for Phase 16 primitives.
Per Finding F-16-C: Agency pressure primitives only contribute to A_p when uninvited.

Primary interface: check_consent()

Feature flag: NOVA_ENABLE_CONSENT_GATE (default: 0/off)
"""

from nova.phase17.consent_gate import check_consent
from nova.phase17.models import ConsentContext, GateResult

__all__ = ["check_consent", "ConsentContext", "GateResult"]
