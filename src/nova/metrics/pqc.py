"""
Prometheus metrics for Post-Quantum Cryptography (PQC) operations.

Phase 12C: Quantum-Verified Attestation
"""

from prometheus_client import Counter, Gauge

# Slot01: Attestation creation metrics
slot01_attestation_pqc_success_total = Counter(
    "slot01_attestation_pqc_success_total",
    "Total number of successful PQC attestation creations in Slot01",
)

slot01_attestation_pqc_failure_total = Counter(
    "slot01_attestation_pqc_failure_total",
    "Total number of failed PQC attestation creations in Slot01",
)

# Slot08: Verification metrics
slot08_pqc_verifications_total = Counter(
    "slot08_pqc_verifications_total",
    "Total number of PQC attestation verifications attempted in Slot08",
)

slot08_pqc_verifications_success_total = Counter(
    "slot08_pqc_verifications_success_total",
    "Total number of successful PQC attestation verifications in Slot08",
)

slot08_pqc_verifications_failure_total = Counter(
    "slot08_pqc_verifications_failure_total",
    "Total number of failed PQC attestation verifications in Slot08",
)

slot08_pqc_key_rotations_total = Counter(
    "slot08_pqc_key_rotations_total",
    "Total number of PQC key rotations in Slot08",
)

slot08_pqc_active_keys = Gauge(
    "slot08_pqc_active_keys",
    "Number of active PQC public keys in Slot08 registry",
)
