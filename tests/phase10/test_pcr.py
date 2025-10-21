"""Tests for Provenance & Consensus Registry (PCR)."""

import pytest
from src.nova.phase10.pcr import LedgerEntry, ProvenanceConsensusRegistry


def test_ledger_entry_creation():
    """Verify ledger entry creation with auto-Merkle root."""
    entry = LedgerEntry(
        entry_id="pcr-000001",
        decision_id="d1",
        decision_hash="abc123",
        parent_hash="genesis",
    )

    assert entry.entry_id == "pcr-000001"
    assert len(entry.merkle_root) == 64  # SHA-256


def test_ledger_entry_verification():
    """Verify entry integrity check."""
    entry = LedgerEntry(
        entry_id="pcr-000001",
        decision_id="d1",
        decision_hash="abc123",
        parent_hash="genesis",
    )

    # Valid entry
    assert entry.verify() is True

    # Tampered entry
    entry.decision_hash = "tampered"
    assert entry.verify() is False


def test_pcr_append():
    """Verify ledger append operation."""
    pcr = ProvenanceConsensusRegistry()

    entry1 = pcr.append("d1", "hash1")
    assert entry1.entry_id == "pcr-000000"
    assert entry1.parent_hash == "phase9-nci-baseline"

    entry2 = pcr.append("d2", "hash2")
    assert entry2.entry_id == "pcr-000001"
    assert entry2.parent_hash == entry1.merkle_root  # Chained


def test_pcr_append_duplicate_rejection():
    """Verify duplicate decision IDs are rejected."""
    pcr = ProvenanceConsensusRegistry()
    pcr.append("d1", "hash1")

    with pytest.raises(ValueError, match="already in ledger"):
        pcr.append("d1", "hash2")


def test_pcr_get_entry():
    """Verify entry retrieval by decision ID."""
    pcr = ProvenanceConsensusRegistry()
    pcr.append("d1", "hash1")
    pcr.append("d2", "hash2")

    entry = pcr.get_entry("d1")
    assert entry is not None
    assert entry.decision_id == "d1"

    assert pcr.get_entry("d99") is None


def test_pcr_chain_verification():
    """Verify Merkle chain integrity check."""
    pcr = ProvenanceConsensusRegistry()
    pcr.append("d1", "hash1")
    pcr.append("d2", "hash2")
    pcr.append("d3", "hash3")

    result = pcr.verify_chain()

    assert result["verified"] is True
    assert result["pis"] == 1.0
    assert len(result["breaks"]) == 0


def test_pcr_chain_break_detection():
    """Verify broken chain detection."""
    pcr = ProvenanceConsensusRegistry()
    pcr.append("d1", "hash1")
    pcr.append("d2", "hash2")
    pcr.append("d3", "hash3")

    # Tamper with middle entry
    pcr.ledger[1].decision_hash = "tampered"

    result = pcr.verify_chain()

    assert result["verified"] is False
    assert result["pis"] < 1.0
    assert len(result["breaks"]) > 0


def test_pcr_regeneration():
    """Verify autonomous chain repair."""
    pcr = ProvenanceConsensusRegistry()
    pcr.append("d1", "hash1")
    pcr.append("d2", "hash2")
    pcr.append("d3", "hash3")

    # Tamper with entry
    pcr.ledger[1].decision_hash = "tampered"

    # Verify break detected
    result_before = pcr.verify_chain()
    assert result_before["verified"] is False

    # Regenerate from index 1
    regen_result = pcr.regenerate(1)
    assert regen_result["status"] == "regenerated"
    assert regen_result["repaired_entries"] == 2  # Entries 1 and 2

    # Verify chain restored
    result_after = pcr.verify_chain()
    assert result_after["verified"] is True
    assert result_after["pis"] == 1.0


def test_pcr_pis_calculation():
    """Verify PIS (Provenance Integrity Score) calculation."""
    pcr = ProvenanceConsensusRegistry()

    # Add 10 entries
    for i in range(10):
        pcr.append(f"d{i}", f"hash{i}")

    # Tamper with 2 entries
    pcr.ledger[3].decision_hash = "tampered1"
    pcr.ledger[7].decision_hash = "tampered2"

    result = pcr.verify_chain()

    # Expected PIS = (10 - 2) / 10 = 0.8
    assert 0.79 <= result["pis"] <= 0.81


def test_pcr_export_audit_trail():
    """Verify JSON-LD audit trail export."""
    pcr = ProvenanceConsensusRegistry()
    pcr.append("d1", "hash1")
    pcr.append("d2", "hash2")

    audit_trail = pcr.export_audit_trail(format="json-ld")

    assert "@context" in audit_trail
    assert "ProvenanceLedger" in audit_trail
    assert "d1" in audit_trail
    assert "d2" in audit_trail


def test_pcr_export_unsupported_format():
    """Verify unsupported format rejection."""
    pcr = ProvenanceConsensusRegistry()

    with pytest.raises(ValueError, match="Unsupported format"):
        pcr.export_audit_trail(format="xml")


def test_pcr_metrics():
    """Verify metrics export."""
    pcr = ProvenanceConsensusRegistry()

    pcr.append("d1", "hash1")
    pcr.append("d2", "hash2")
    # Note: get_metrics() calls verify_chain() internally, incrementing count

    metrics = pcr.get_metrics()

    assert metrics["total_entries"] == 2
    assert metrics["pis"] == 1.0
    assert metrics["chain_verified"] is True
    assert metrics["verification_count"] >= 1  # At least one verification
    assert metrics["breaks_detected"] == 0


def test_pcr_empty_ledger_verification():
    """Verify empty ledger verification."""
    pcr = ProvenanceConsensusRegistry()

    result = pcr.verify_chain()

    assert result["verified"] is True
    assert result["pis"] == 1.0
    assert result["entries_checked"] == 0
