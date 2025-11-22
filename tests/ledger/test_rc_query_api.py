"""Test RC attestation query API."""

import tempfile
from pathlib import Path

from nova.ledger.rc_query import (
    get_rc_chain,
    get_rc_attestation_by_hash,
    verify_rc_chain,
    get_rc_summary,
)


def test_get_rc_chain():
    """Test retrieving RC attestation chain."""
    import sys
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts"))

    from generate_rc_attestation import generate_attestation

    # Generate 3 RC attestations
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            generate_attestation(
                output_path=output_path,
                memory_stability=0.80 + (i * 0.01),
                ris_score=0.85 + (i * 0.01),
                stress_recovery=0.90 + (i * 0.01),
                append_to_ledger=True
            )
        finally:
            output_path.unlink(missing_ok=True)

    # Query chain
    chain = get_rc_chain("7.0-rc")

    assert len(chain) >= 3, f"Expected at least 3 attestations, got {len(chain)}"

    # Verify all records are RC_ATTESTATION
    from nova.ledger.model import RecordKind
    for record in chain:
        assert record.kind == RecordKind.RC_ATTESTATION
        assert record.slot == "00"
        assert "attestation_hash" in record.payload


def test_get_rc_attestation_by_hash():
    """Test finding RC attestation by hash."""
    import sys
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts"))

    from generate_rc_attestation import generate_attestation

    # Generate attestation
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = Path(f.name)

    try:
        attestation = generate_attestation(
            output_path=output_path,
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.92,
            append_to_ledger=True
        )
    finally:
        output_path.unlink(missing_ok=True)

    # Query by hash
    attestation_hash = attestation["attestation_hash"]
    record = get_rc_attestation_by_hash(attestation_hash, "7.0-rc")

    assert record is not None, "Attestation not found by hash"
    assert record.payload["attestation_hash"] == attestation_hash
    assert record.payload["memory_resonance"]["stability"] == 0.85


def test_verify_rc_chain():
    """Test RC chain integrity verification."""
    import sys
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts"))

    from generate_rc_attestation import generate_attestation

    # Generate 2 RC attestations
    for i in range(2):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            generate_attestation(
                output_path=output_path,
                memory_stability=0.85,
                ris_score=0.90,
                stress_recovery=0.92,
                append_to_ledger=True
            )
        finally:
            output_path.unlink(missing_ok=True)

    # Verify chain
    is_valid, errors = verify_rc_chain("7.0-rc")

    assert is_valid, f"Chain validation failed: {errors}"
    assert len(errors) == 0, f"Unexpected errors: {errors}"


def test_get_rc_summary():
    """Test RC attestation summary statistics."""
    import sys
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts"))

    from generate_rc_attestation import generate_attestation

    # Generate 3 attestations (2 pass, 1 fail)
    test_cases = [
        (0.85, 0.90, 0.92),  # PASS
        (0.86, 0.91, 0.93),  # PASS
        (0.70, 0.60, 0.80),  # FAIL (below thresholds)
    ]

    for memory, ris, stress in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            generate_attestation(
                output_path=output_path,
                memory_stability=memory,
                ris_score=ris,
                stress_recovery=stress,
                append_to_ledger=True
            )
        finally:
            output_path.unlink(missing_ok=True)

    # Get summary
    summary = get_rc_summary("7.0-rc")

    assert summary["count"] >= 3, f"Expected at least 3 attestations, got {summary['count']}"
    assert summary["chain_valid"] is True
    assert summary["pass_count"] >= 2  # At least 2 should pass
    assert 0.0 < summary["pass_rate"] <= 1.0
    assert summary["avg_memory_stability"] > 0.0
    assert summary["avg_ris_score"] > 0.0
    assert summary["avg_stress_recovery"] > 0.0
    assert "first_attestation" in summary
    assert "last_attestation" in summary


def test_query_empty_chain():
    """Test querying non-existent phase."""
    chain = get_rc_chain("non-existent-phase")
    assert len(chain) == 0

    summary = get_rc_summary("non-existent-phase")
    assert summary["count"] == 0
    assert summary["chain_valid"] is True

    is_valid, errors = verify_rc_chain("non-existent-phase")
    assert is_valid is True
    assert len(errors) == 0
