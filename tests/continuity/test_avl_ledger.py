"""Unit tests for Autonomous Verification Ledger (AVL) - Phase 13

Tests for avl_ledger.py: entry creation, hash chain integrity,
ledger operations, persistence, and query API.

Per Phase13_Implementation_Checklist.md: 15 tests required.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.nova.continuity.avl_ledger import (
    AVLEntry,
    AVLLedger,
    GENESIS_HASH,
    compute_entry_hash,
    compute_entry_id,
    get_avl_ledger,
    reset_avl_ledger,
    avl_enabled,
)


# ---------- Fixtures ----------


@pytest.fixture
def temp_ledger_path(tmp_path):
    """Create temporary ledger file path."""
    return str(tmp_path / "test_ledger.jsonl")


@pytest.fixture
def sample_entry():
    """Create sample AVL entry."""
    return AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        elapsed_s=0.0,
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={
            "urf_composite_risk": 0.15,
            "mse_meta_instability": 0.03,
            "predictive_collapse_risk": 0.10,
            "consistency_gap": 0.05,
            "csi_continuity_index": 0.95,
        },
        posture_adjustments={
            "threshold_multiplier": 1.0,
            "traffic_limit": 1.0,
        },
        oracle_regime="normal",
        oracle_regime_score=0.15,
        dual_modality_agreement=True,
        node_id="test-node",
        orp_version="phase13.1",
    )


@pytest.fixture
def sample_entry_heightened():
    """Create sample heightened regime entry."""
    return AVLEntry(
        timestamp="2025-01-01T12:05:00+00:00",
        elapsed_s=300.0,
        orp_regime="heightened",
        orp_regime_score=0.35,
        contributing_factors={
            "urf_composite_risk": 0.45,
            "mse_meta_instability": 0.08,
            "predictive_collapse_risk": 0.25,
            "consistency_gap": 0.12,
            "csi_continuity_index": 0.85,
        },
        posture_adjustments={
            "threshold_multiplier": 0.85,
            "traffic_limit": 0.90,
        },
        oracle_regime="heightened",
        oracle_regime_score=0.35,
        dual_modality_agreement=True,
        transition_from="normal",
        time_in_previous_regime_s=300.0,
        node_id="test-node",
        orp_version="phase13.1",
    )


@pytest.fixture
def ledger(temp_ledger_path):
    """Create empty ledger for testing."""
    return AVLLedger(temp_ledger_path)


# ---------- Test 1: Entry Creation ----------


def test_entry_creation(sample_entry):
    """Test AVLEntry dataclass creation and field access."""
    assert sample_entry.timestamp == "2025-01-01T12:00:00+00:00"
    assert sample_entry.orp_regime == "normal"
    assert sample_entry.orp_regime_score == 0.15
    assert sample_entry.dual_modality_agreement is True
    assert sample_entry.drift_detected is False
    assert sample_entry.drift_reasons == []
    assert sample_entry.prev_entry_hash == GENESIS_HASH


def test_entry_to_dict(sample_entry):
    """Test AVLEntry serialization to dict."""
    d = sample_entry.to_dict()

    assert isinstance(d, dict)
    assert d["timestamp"] == "2025-01-01T12:00:00+00:00"
    assert d["orp_regime"] == "normal"
    assert d["contributing_factors"]["urf_composite_risk"] == 0.15


def test_entry_from_dict(sample_entry):
    """Test AVLEntry deserialization from dict."""
    d = sample_entry.to_dict()
    restored = AVLEntry.from_dict(d)

    assert restored.timestamp == sample_entry.timestamp
    assert restored.orp_regime == sample_entry.orp_regime
    assert restored.contributing_factors == sample_entry.contributing_factors


def test_entry_json_roundtrip(sample_entry):
    """Test AVLEntry JSON serialization roundtrip."""
    json_str = sample_entry.to_json()
    restored = AVLEntry.from_json(json_str)

    assert restored.timestamp == sample_entry.timestamp
    assert restored.orp_regime == sample_entry.orp_regime


# ---------- Test 2: Hash Computation ----------


def test_compute_entry_hash_deterministic(sample_entry):
    """Test hash computation is deterministic (same inputs → same hash)."""
    hash1 = compute_entry_hash(sample_entry)
    hash2 = compute_entry_hash(sample_entry)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length


def test_compute_entry_hash_different_inputs():
    """Test different inputs produce different hashes."""
    entry1 = AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={"urf_composite_risk": 0.15},
        oracle_regime="normal",
    )
    entry2 = AVLEntry(
        timestamp="2025-01-01T12:00:01+00:00",  # Different timestamp
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={"urf_composite_risk": 0.15},
        oracle_regime="normal",
    )

    hash1 = compute_entry_hash(entry1)
    hash2 = compute_entry_hash(entry2)

    assert hash1 != hash2


def test_compute_entry_id_deterministic(sample_entry):
    """Test entry ID computation is deterministic."""
    id1 = compute_entry_id(sample_entry)
    id2 = compute_entry_id(sample_entry)

    assert id1 == id2
    assert len(id1) == 64


# ---------- Test 3: Hash Chain Integrity ----------


def test_hash_chain_integrity(ledger, sample_entry, sample_entry_heightened):
    """Test hash chain is correctly maintained across appends."""
    # Append first entry
    entry1 = ledger.append(sample_entry)
    assert entry1.prev_entry_hash == GENESIS_HASH

    # Append second entry
    entry2 = ledger.append(sample_entry_heightened)
    assert entry2.prev_entry_hash == compute_entry_hash(entry1)

    # Verify chain
    is_valid, violations = ledger.verify_hash_chain()
    assert is_valid, f"Hash chain invalid: {violations}"


def test_hash_chain_genesis_entry(ledger, sample_entry):
    """Test genesis entry has correct prev_entry_hash."""
    entry = ledger.append(sample_entry)

    assert entry.prev_entry_hash == GENESIS_HASH

    is_valid, violations = ledger.verify_hash_chain()
    assert is_valid


# ---------- Test 4: Ledger Append-Only ----------


def test_ledger_append_only(ledger, sample_entry):
    """Test ledger is append-only (no modifications)."""
    entry = ledger.append(sample_entry)

    # Verify entry is in ledger
    entries = ledger.get_entries()
    assert len(entries) == 1
    assert entries[0].entry_id == entry.entry_id

    # Append another
    entry2 = AVLEntry(
        timestamp="2025-01-01T12:01:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.16,
        contributing_factors={"urf_composite_risk": 0.16},
        oracle_regime="normal",
    )
    ledger.append(entry2)

    entries = ledger.get_entries()
    assert len(entries) == 2


def test_ledger_duplicate_entry_rejected(ledger, sample_entry):
    """Test duplicate entry_id is rejected."""
    ledger.append(sample_entry)

    # Try to append same entry again (same timestamp + regime + factors = same ID)
    with pytest.raises(ValueError, match="Duplicate entry_id"):
        ledger.append(sample_entry)


# ---------- Test 5: Ledger Persistence ----------


def test_ledger_persistence(temp_ledger_path, sample_entry, sample_entry_heightened):
    """Test ledger survives restart (persistence verified)."""
    # Create ledger and add entries
    ledger1 = AVLLedger(temp_ledger_path)
    ledger1.append(sample_entry)
    ledger1.append(sample_entry_heightened)

    # Create new ledger instance (simulates restart)
    ledger2 = AVLLedger(temp_ledger_path)

    # Verify entries persisted
    entries = ledger2.get_entries()
    assert len(entries) == 2
    assert entries[0].orp_regime == "normal"
    assert entries[1].orp_regime == "heightened"

    # Verify hash chain intact
    is_valid, violations = ledger2.verify_hash_chain()
    assert is_valid, f"Hash chain broken after restart: {violations}"


# ---------- Test 6: Query by Time Window ----------


def test_query_by_time_window(ledger):
    """Test time range queries work correctly."""
    # Add entries at different times
    for i in range(5):
        entry = AVLEntry(
            timestamp=f"2025-01-01T12:0{i}:00+00:00",
            elapsed_s=float(i * 60),
            orp_regime="normal",
            orp_regime_score=0.10 + i * 0.01,
            contributing_factors={"urf_composite_risk": 0.10 + i * 0.01},
            oracle_regime="normal",
        )
        ledger.append(entry)

    # Query middle range
    results = ledger.query_by_time_window(
        "2025-01-01T12:01:00+00:00",
        "2025-01-01T12:03:00+00:00"
    )

    assert len(results) == 3
    assert results[0].timestamp == "2025-01-01T12:01:00+00:00"
    assert results[2].timestamp == "2025-01-01T12:03:00+00:00"


# ---------- Test 7: Query by Regime ----------


def test_query_by_regime(ledger, sample_entry, sample_entry_heightened):
    """Test regime filtering works correctly."""
    ledger.append(sample_entry)
    ledger.append(sample_entry_heightened)

    # Add another normal entry
    entry3 = AVLEntry(
        timestamp="2025-01-01T12:10:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.12,
        contributing_factors={"urf_composite_risk": 0.12},
        oracle_regime="normal",
    )
    ledger.append(entry3)

    # Query normal regime
    normal_entries = ledger.query_by_regime("normal")
    assert len(normal_entries) == 2

    # Query heightened regime
    heightened_entries = ledger.query_by_regime("heightened")
    assert len(heightened_entries) == 1


# ---------- Test 8: Query Drift Events ----------


def test_query_drift_events(ledger):
    """Test drift filtering works correctly."""
    # Add normal entry (no drift)
    entry1 = AVLEntry(
        timestamp="2025-01-01T12:00:00+00:00",
        orp_regime="normal",
        orp_regime_score=0.15,
        contributing_factors={"urf_composite_risk": 0.15},
        oracle_regime="normal",
        drift_detected=False,
    )
    ledger.append(entry1)

    # Add drift entry
    entry2 = AVLEntry(
        timestamp="2025-01-01T12:01:00+00:00",
        orp_regime="heightened",
        orp_regime_score=0.35,
        contributing_factors={"urf_composite_risk": 0.35},
        oracle_regime="normal",  # Disagreement!
        dual_modality_agreement=False,
        drift_detected=True,
        drift_reasons=["ORP=heightened vs Oracle=normal"],
    )
    ledger.append(entry2)

    # Query drift events
    drift_entries = ledger.query_drift_events()
    assert len(drift_entries) == 1
    assert drift_entries[0].drift_detected is True
    assert "ORP=heightened" in drift_entries[0].drift_reasons[0]


# ---------- Test 9: Get Latest ----------


def test_get_latest(ledger):
    """Test last N entries retrieval."""
    # Add 10 entries
    for i in range(10):
        entry = AVLEntry(
            timestamp=f"2025-01-01T12:{i:02d}:00+00:00",
            orp_regime="normal",
            orp_regime_score=0.10 + i * 0.01,
            contributing_factors={"urf_composite_risk": 0.10 + i * 0.01},
            oracle_regime="normal",
        )
        ledger.append(entry)

    # Get last 3
    latest = ledger.get_latest(3)
    assert len(latest) == 3
    assert latest[0].timestamp == "2025-01-01T12:07:00+00:00"
    assert latest[2].timestamp == "2025-01-01T12:09:00+00:00"

    # Get more than available
    all_entries = ledger.get_latest(20)
    assert len(all_entries) == 10


# ---------- Test 10: Verify Integrity ----------


def test_verify_integrity(ledger, sample_entry, sample_entry_heightened):
    """Test hash chain + proofs verification."""
    ledger.append(sample_entry)
    ledger.append(sample_entry_heightened)

    is_valid, violations = ledger.verify_integrity()
    assert is_valid, f"Integrity check failed: {violations}"
    assert violations == []


def test_verify_integrity_detects_tampering(temp_ledger_path, sample_entry, sample_entry_heightened):
    """Test integrity check detects hash chain tampering."""
    ledger = AVLLedger(temp_ledger_path)
    entry1 = ledger.append(sample_entry)
    entry2 = ledger.append(sample_entry_heightened)

    # Manually tamper with file - modify first entry's score
    # This should break the hash chain since entry2.prev_entry_hash
    # was computed from the original entry1
    with open(temp_ledger_path, "r") as f:
        lines = f.readlines()

    # Modify first entry (changes its hash)
    entry1_dict = json.loads(lines[0])
    entry1_dict["orp_regime_score"] = 0.99  # Tamper!

    with open(temp_ledger_path, "w") as f:
        f.write(json.dumps(entry1_dict, sort_keys=True) + "\n")
        f.write(lines[1])  # Keep second entry unchanged

    # Reload and verify
    ledger2 = AVLLedger(temp_ledger_path)

    # Hash chain should be broken (entry2.prev_entry_hash != hash(tampered_entry1))
    is_valid, hash_violations = ledger2.verify_hash_chain()
    assert not is_valid, "Hash chain should be invalid after tampering"
    assert len(hash_violations) > 0, f"Expected hash violations, got none"


# ---------- Test 11: Ledger Empty State ----------


def test_ledger_empty_state(ledger):
    """Test genesis entry handling on empty ledger."""
    assert len(ledger) == 0

    entries = ledger.get_entries()
    assert entries == []

    # Verify empty ledger is valid
    is_valid, violations = ledger.verify_integrity()
    assert is_valid


# ---------- Test 12: Thread Safety (Future) ----------


def test_ledger_concurrent_append(ledger):
    """Test thread safety for concurrent appends (basic test)."""
    import threading

    results = []
    errors = []

    def append_entry(idx):
        try:
            entry = AVLEntry(
                timestamp=f"2025-01-01T12:00:{idx:02d}+00:00",
                orp_regime="normal",
                orp_regime_score=0.10 + idx * 0.001,
                contributing_factors={"urf_composite_risk": 0.10 + idx * 0.001},
                oracle_regime="normal",
            )
            ledger.append(entry)
            results.append(idx)
        except Exception as e:
            errors.append((idx, str(e)))

    # Create threads
    threads = [threading.Thread(target=append_entry, args=(i,)) for i in range(10)]

    # Start all
    for t in threads:
        t.start()

    # Wait for all
    for t in threads:
        t.join()

    # Verify all appended (no duplicates due to different timestamps)
    assert len(results) == 10, f"Expected 10 appends, got {len(results)}, errors: {errors}"
    assert len(ledger) == 10


# ---------- Test 13: Export JSONL ----------


def test_export_jsonl(ledger, sample_entry, sample_entry_heightened, tmp_path):
    """Test export to file."""
    ledger.append(sample_entry)
    ledger.append(sample_entry_heightened)

    export_path = str(tmp_path / "export.jsonl")
    ledger.export(export_path)

    # Verify file exists and has correct content
    assert Path(export_path).exists()

    with open(export_path, "r") as f:
        lines = f.readlines()

    assert len(lines) == 2


def test_export_unsupported_format(ledger, tmp_path):
    """Test export with unsupported format raises error."""
    with pytest.raises(ValueError, match="Unsupported export format"):
        ledger.export(str(tmp_path / "export.csv"), format="csv")


# ---------- Test 14: Import JSONL ----------


def test_import_jsonl(temp_ledger_path, sample_entry, sample_entry_heightened, tmp_path):
    """Test import from file."""
    # Create source ledger
    source_ledger = AVLLedger(temp_ledger_path)
    source_ledger.append(sample_entry)
    source_ledger.append(sample_entry_heightened)

    # Export to file
    export_path = str(tmp_path / "export.jsonl")
    source_ledger.export(export_path)

    # Create new ledger and import
    dest_path = str(tmp_path / "dest_ledger.jsonl")
    dest_ledger = AVLLedger(dest_path)

    imported = dest_ledger.import_jsonl(export_path)

    assert imported == 2
    assert len(dest_ledger) == 2


def test_import_jsonl_file_not_found(ledger):
    """Test import with non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        ledger.import_jsonl("/nonexistent/path.jsonl")


# ---------- Test 15: Entry ID Unique ----------


def test_entry_id_unique(ledger):
    """Test no duplicate IDs across entries."""
    # Add entries with different timestamps
    for i in range(5):
        entry = AVLEntry(
            timestamp=f"2025-01-01T12:0{i}:00+00:00",
            orp_regime="normal",
            orp_regime_score=0.15,
            contributing_factors={"urf_composite_risk": 0.15},
            oracle_regime="normal",
        )
        ledger.append(entry)

    # Verify all IDs unique
    entries = ledger.get_entries()
    ids = [e.entry_id for e in entries]

    assert len(ids) == len(set(ids)), "Duplicate entry IDs found"


# ---------- Global Singleton Tests ----------


def test_get_avl_ledger_singleton(monkeypatch, tmp_path):
    """Test global AVL ledger singleton."""
    # Reset first
    reset_avl_ledger()

    # Set custom path
    ledger_path = str(tmp_path / "singleton_ledger.jsonl")
    monkeypatch.setenv("NOVA_AVL_PATH", ledger_path)

    # Get singleton
    ledger1 = get_avl_ledger()
    ledger2 = get_avl_ledger()

    assert ledger1 is ledger2

    # Cleanup
    reset_avl_ledger()


def test_avl_enabled(monkeypatch):
    """Test AVL enabled flag."""
    # Default disabled
    monkeypatch.delenv("NOVA_ENABLE_AVL", raising=False)
    assert avl_enabled() is False

    # Enable
    monkeypatch.setenv("NOVA_ENABLE_AVL", "1")
    assert avl_enabled() is True

    # Disable explicitly
    monkeypatch.setenv("NOVA_ENABLE_AVL", "0")
    assert avl_enabled() is False


# ---------- Query by Entry ID ----------


def test_query_by_entry_id(ledger, sample_entry):
    """Test finding entry by entry_id."""
    appended = ledger.append(sample_entry)

    found = ledger.query_by_entry_id(appended.entry_id)
    assert found is not None
    assert found.timestamp == sample_entry.timestamp

    # Not found
    not_found = ledger.query_by_entry_id("nonexistent")
    assert not_found is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
