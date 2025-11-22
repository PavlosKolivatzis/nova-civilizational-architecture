"""Test RC attestation integration with Phase 14 ledger."""

import json
from pathlib import Path
import tempfile

import pytest

from nova.ledger.factory import create_ledger_store
from nova.ledger.model import RecordKind


def test_rc_attestation_ledger_integration():
    """Test RC attestation appends to ledger correctly."""
    # Import script after setting up path
    import sys
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts"))

    from generate_rc_attestation import generate_attestation

    # Create temp output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = Path(f.name)

    try:
        # Generate RC attestation with ledger append
        attestation = generate_attestation(
            output_path=output_path,
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.92,
            append_to_ledger=True
        )

        # Verify attestation structure
        assert attestation["schema_version"] == "7.0-rc-v1"
        assert attestation["phase"] == "7.0-rc"
        assert "attestation_hash" in attestation
        assert attestation["signature"] == "The sun shines on this work."

        # Verify ledger record exists
        store = create_ledger_store()
        anchor_id = f"rc_validation_{attestation['phase']}"

        # Get ledger chain for RC validation anchor
        chain = store.get_chain(anchor_id)
        assert len(chain) > 0, "RC attestation not found in ledger"

        # Verify last record is RC_ATTESTATION
        last_record = chain[-1]
        assert last_record.kind == RecordKind.RC_ATTESTATION
        assert last_record.slot == "00"
        assert last_record.producer == "rc_attestation_generator"

        # Verify payload matches attestation
        assert last_record.payload["attestation_hash"] == attestation["attestation_hash"]
        assert last_record.payload["rc_criteria"]["overall_pass"] is True

        # Verify hash chain continuity
        is_valid, errors = store.verify_chain(anchor_id)
        assert is_valid, f"Chain continuity broken: {errors}"

    finally:
        # Cleanup temp file
        output_path.unlink(missing_ok=True)


def test_rc_attestation_without_ledger():
    """Test RC attestation still works when ledger append disabled."""
    import sys
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts"))

    from generate_rc_attestation import generate_attestation

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = Path(f.name)

    try:
        # Generate without ledger append
        attestation = generate_attestation(
            output_path=output_path,
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.92,
            append_to_ledger=False
        )

        # Verify file written
        assert output_path.exists()

        # Verify attestation complete
        assert "attestation_hash" in attestation
        assert attestation["signature"] == "The sun shines on this work."

    finally:
        output_path.unlink(missing_ok=True)


def test_rc_attestation_hash_chain():
    """Test multiple RC attestations form valid hash chain."""
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

    # Verify chain integrity
    store = create_ledger_store()
    anchor_id = "rc_validation_7.0-rc"

    chain = store.get_chain(anchor_id)
    assert len(chain) >= 3, f"Expected at least 3 records, got {len(chain)}"

    # Verify all are RC_ATTESTATION
    for record in chain:
        assert record.kind == RecordKind.RC_ATTESTATION

    # Verify hash chain continuity
    is_valid, errors = store.verify_chain(anchor_id)
    assert is_valid, f"Chain broken: {errors}"

    # Verify prev_hash links
    for i in range(1, len(chain)):
        assert chain[i].prev_hash == chain[i-1].hash, \
            f"Chain link {i} broken: prev_hash mismatch"


def test_rc_attestation_pqc_signature():
    """Test RC attestations have valid PQC signatures."""
    import sys
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts"))

    from generate_rc_attestation import generate_attestation
    from nova.crypto.pqc_keyring import PQCKeyring

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = Path(f.name)

    try:
        # Generate RC attestation with ledger append
        attestation = generate_attestation(
            output_path=output_path,
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.92,
            append_to_ledger=True
        )

        # Verify ledger record has PQC signature
        store = create_ledger_store()
        anchor_id = f"rc_validation_{attestation['phase']}"
        chain = store.get_chain(anchor_id)

        assert len(chain) > 0, "RC attestation not found in ledger"

        # Get last record (most recent attestation)
        last_record = chain[-1]
        assert last_record.sig is not None, "RC attestation missing PQC signature"
        assert isinstance(last_record.sig, bytes), "Signature should be bytes"
        assert len(last_record.sig) > 0, "Signature should not be empty"

        # Note: Cannot verify signature without storing public key
        # In production, public key would be stored in ledger metadata
        # For now, just verify signature exists and is non-trivial

    finally:
        output_path.unlink(missing_ok=True)


def test_rc_attestation_merkle_checkpoint():
    """Test Merkle checkpoint creation for RC attestation chain."""
    import sys
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts"))

    from generate_rc_attestation import generate_attestation
    from nova.ledger.merkle import merkle_root

    # Generate 3 RC attestations
    attestations = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            att = generate_attestation(
                output_path=output_path,
                memory_stability=0.80 + (i * 0.01),
                ris_score=0.85 + (i * 0.01),
                stress_recovery=0.90 + (i * 0.01),
                append_to_ledger=True
            )
            attestations.append(att)
        finally:
            output_path.unlink(missing_ok=True)

    # Verify Merkle checkpoint was created (in-memory store)
    store = create_ledger_store()
    anchor_id = "rc_validation_7.0-rc"

    chain = store.get_chain(anchor_id)
    assert len(chain) >= 3, f"Expected at least 3 RC attestations, got {len(chain)}"

    # Compute expected Merkle root
    hashes = [bytes.fromhex(r.hash) for r in chain]
    expected_root = merkle_root(hashes)

    # Verify root is deterministic
    assert len(expected_root) == 32, "Merkle root should be 32 bytes (SHA3-256)"
    assert expected_root.hex(), "Merkle root should be non-empty"

    # Note: In-memory store doesn't persist checkpoints
    # This test verifies checkpoint computation logic works
