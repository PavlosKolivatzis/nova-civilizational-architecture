"""
Query API for RC attestation ledger records.

Provides read-only access to RC validation attestation history
stored in Phase 14 ledger.

Phase 14-5: RC Attestation Query API
"""

from typing import Dict, List, Optional, Tuple
from .factory import create_ledger_store
from .model import RecordKind, LedgerRecord


def get_rc_chain(phase: str = "7.0-rc") -> List[LedgerRecord]:
    """
    Get all RC attestation records for a phase.

    Args:
        phase: RC phase identifier (e.g., "7.0-rc")

    Returns:
        List of LedgerRecord in chronological order
    """
    store = create_ledger_store()
    anchor_id = f"rc_validation_{phase}"
    return store.get_chain(anchor_id)


def get_rc_attestation_by_hash(attestation_hash: str, phase: str = "7.0-rc") -> Optional[LedgerRecord]:
    """
    Find RC attestation by attestation_hash field.

    Args:
        attestation_hash: SHA-256 hash from attestation body
        phase: RC phase identifier

    Returns:
        LedgerRecord if found, None otherwise
    """
    chain = get_rc_chain(phase)
    for record in chain:
        if record.payload.get("attestation_hash") == attestation_hash:
            return record
    return None


def verify_rc_chain(phase: str = "7.0-rc") -> Tuple[bool, List[str]]:
    """
    Verify RC attestation chain integrity.

    Checks:
    - Hash chain continuity (prev_hash links)
    - Record hash validity
    - All records are RC_ATTESTATION kind

    Args:
        phase: RC phase identifier

    Returns:
        (is_valid: bool, errors: List[str])
    """
    store = create_ledger_store()
    anchor_id = f"rc_validation_{phase}"

    # Verify hash chain
    is_valid, errors = store.verify_chain(anchor_id)

    # Additional RC-specific checks
    chain = store.get_chain(anchor_id)
    for record in chain:
        if record.kind != RecordKind.RC_ATTESTATION:
            errors.append(f"Record {record.rid}: wrong kind (expected RC_ATTESTATION, got {record.kind.value})")
            is_valid = False

        if record.slot != "00":
            errors.append(f"Record {record.rid}: wrong slot (expected '00', got '{record.slot}')")
            is_valid = False

    return is_valid, errors


def get_rc_summary(phase: str = "7.0-rc") -> Dict:
    """
    Get summary statistics for RC attestation chain.

    Args:
        phase: RC phase identifier

    Returns:
        Dictionary with chain statistics
    """
    chain = get_rc_chain(phase)
    is_valid, errors = verify_rc_chain(phase)

    if not chain:
        return {
            "phase": phase,
            "count": 0,
            "chain_valid": True,
            "errors": [],
        }

    # Extract metrics from attestations
    memory_scores = []
    ris_scores = []
    stress_scores = []
    pass_count = 0

    for record in chain:
        payload = record.payload
        memory_scores.append(payload.get("memory_resonance", {}).get("stability", 0.0))
        ris_scores.append(payload.get("ris", {}).get("score", 0.0))
        stress_scores.append(payload.get("stress_resilience", {}).get("recovery_rate", 0.0))

        if payload.get("rc_criteria", {}).get("overall_pass"):
            pass_count += 1

    return {
        "phase": phase,
        "count": len(chain),
        "chain_valid": is_valid,
        "errors": errors,
        "first_attestation": chain[0].ts.isoformat() if chain else None,
        "last_attestation": chain[-1].ts.isoformat() if chain else None,
        "pass_count": pass_count,
        "pass_rate": pass_count / len(chain) if chain else 0.0,
        "avg_memory_stability": sum(memory_scores) / len(memory_scores) if memory_scores else 0.0,
        "avg_ris_score": sum(ris_scores) / len(ris_scores) if ris_scores else 0.0,
        "avg_stress_recovery": sum(stress_scores) / len(stress_scores) if stress_scores else 0.0,
    }
