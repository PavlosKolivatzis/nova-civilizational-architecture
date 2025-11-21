"""
Unit tests for Phase 7.0-RC Attestation Generation

Tests attestation schema validation, hash computation, and RC criteria logic.
"""
import pytest
import json
import hashlib
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from generate_rc_attestation import (
    compute_attestation_hash,
    evaluate_rc_criteria,
    get_git_commit,
    generate_attestation
)


class TestAttestationHash:
    """Test deterministic hash computation."""

    def test_hash_deterministic(self):
        """Hash should be deterministic for same input."""
        attestation = {
            "phase": "7.0-rc",
            "commit": "abc123",
            "memory_resonance": {"stability": 0.85},
            "signature": "The sun shines on this work."
        }

        hash1 = compute_attestation_hash(attestation)
        hash2 = compute_attestation_hash(attestation)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest

    def test_hash_excludes_signature(self):
        """Hash should exclude signature field."""
        attestation_with_sig = {
            "phase": "7.0-rc",
            "commit": "abc123",
            "signature": "The sun shines on this work."
        }

        attestation_without_sig = {
            "phase": "7.0-rc",
            "commit": "abc123"
        }

        hash_with = compute_attestation_hash(attestation_with_sig)
        hash_without = compute_attestation_hash(attestation_without_sig)

        assert hash_with == hash_without

    def test_hash_changes_with_content(self):
        """Hash should change when content changes."""
        attestation1 = {"phase": "7.0-rc", "commit": "abc123"}
        attestation2 = {"phase": "7.0-rc", "commit": "def456"}

        hash1 = compute_attestation_hash(attestation1)
        hash2 = compute_attestation_hash(attestation2)

        assert hash1 != hash2

    def test_hash_canonical_order(self):
        """Hash should be same regardless of key order."""
        attestation1 = {"b": 2, "a": 1, "c": 3}
        attestation2 = {"a": 1, "c": 3, "b": 2}

        hash1 = compute_attestation_hash(attestation1)
        hash2 = compute_attestation_hash(attestation2)

        assert hash1 == hash2

    def test_hash_compact_json(self):
        """Hash should use compact JSON (no whitespace)."""
        attestation = {"phase": "7.0-rc"}

        # Compute hash manually with compact JSON
        canonical = json.dumps(attestation, sort_keys=True, separators=(",", ":"))
        expected_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        actual_hash = compute_attestation_hash(attestation)

        assert actual_hash == expected_hash


class TestRCCriteriaEvaluation:
    """Test RC pass/fail criteria logic."""

    def test_all_criteria_pass(self):
        """All criteria met should return overall_pass=True."""
        criteria = evaluate_rc_criteria(
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.95,
            samples=168
        )

        assert criteria["memory_stability_pass"] is True
        assert criteria["ris_pass"] is True
        assert criteria["stress_recovery_pass"] is True
        assert criteria["samples_sufficient"] is True
        assert criteria["overall_pass"] is True

    def test_memory_stability_fail(self):
        """Memory stability below 0.80 should fail."""
        criteria = evaluate_rc_criteria(
            memory_stability=0.75,
            ris_score=0.90,
            stress_recovery=0.95,
            samples=168
        )

        assert criteria["memory_stability_pass"] is False
        assert criteria["overall_pass"] is False

    def test_ris_fail(self):
        """RIS below 0.75 should fail."""
        criteria = evaluate_rc_criteria(
            memory_stability=0.85,
            ris_score=0.70,
            stress_recovery=0.95,
            samples=168
        )

        assert criteria["ris_pass"] is False
        assert criteria["overall_pass"] is False

    def test_stress_recovery_fail(self):
        """Stress recovery below 0.90 should fail."""
        criteria = evaluate_rc_criteria(
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.85,
            samples=168
        )

        assert criteria["stress_recovery_pass"] is False
        assert criteria["overall_pass"] is False

    def test_insufficient_samples(self):
        """Less than 24 samples should fail."""
        criteria = evaluate_rc_criteria(
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.95,
            samples=20
        )

        assert criteria["samples_sufficient"] is False
        assert criteria["overall_pass"] is False

    def test_boundary_conditions(self):
        """Test exact boundary values."""
        # Exact thresholds should pass
        criteria_pass = evaluate_rc_criteria(
            memory_stability=0.80,
            ris_score=0.75,
            stress_recovery=0.90,
            samples=24
        )

        assert criteria_pass["overall_pass"] is True

        # Just below thresholds should fail
        criteria_fail = evaluate_rc_criteria(
            memory_stability=0.799,
            ris_score=0.749,
            stress_recovery=0.899,
            samples=23
        )

        assert criteria_fail["overall_pass"] is False


class TestGitCommitRetrieval:
    """Test git commit SHA retrieval."""

    def test_get_git_commit_format(self):
        """Git commit should be valid SHA format."""
        commit = get_git_commit()

        # Should be 40 hex characters (full SHA) or 7+ (short SHA)
        assert len(commit) >= 7
        assert all(c in "0123456789abcdef" for c in commit.lower())

    def test_get_git_commit_matches_head(self):
        """Retrieved commit should match git HEAD."""
        commit = get_git_commit()

        # Query git directly
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            expected_commit = result.stdout.strip()
            assert commit == expected_commit


class TestAttestationGeneration:
    """Test full attestation generation."""

    def test_generate_attestation_structure(self, tmp_path):
        """Generated attestation should have all required fields."""
        output = tmp_path / "test_attestation.json"

        attestation = generate_attestation(
            output_path=output,
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.95
        )

        # Check all required schema fields
        assert attestation["schema_version"] == "7.0-rc-v1"
        assert attestation["phase"] == "7.0-rc"
        assert "commit" in attestation
        assert "timestamp" in attestation
        assert "validation_period" in attestation
        assert "memory_resonance" in attestation
        assert "ris" in attestation
        assert "stress_resilience" in attestation
        assert "predictive_health" in attestation
        assert "rc_criteria" in attestation
        assert "audit_status" in attestation
        assert "attestation_hash" in attestation
        assert attestation["signature"] == "The sun shines on this work."

    def test_generate_attestation_file_created(self, tmp_path):
        """Attestation file should be created."""
        output = tmp_path / "attestation.json"

        generate_attestation(
            output_path=output,
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.95
        )

        assert output.exists()

        # Verify valid JSON
        with open(output) as f:
            loaded = json.load(f)
            assert loaded["phase"] == "7.0-rc"

    def test_generate_attestation_hash_verifiable(self, tmp_path):
        """Attestation hash should be verifiable against file."""
        output = tmp_path / "attestation.json"

        generate_attestation(
            output_path=output,
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.95
        )

        # Load attestation from file
        with open(output) as f:
            attestation = json.load(f)

        # Recompute hash from loaded attestation
        recomputed_hash = compute_attestation_hash(attestation)

        # Hash in file should match recomputed hash
        assert attestation["attestation_hash"] == recomputed_hash

    def test_generate_attestation_timestamp_format(self, tmp_path):
        """Timestamp should be valid ISO 8601 format."""
        output = tmp_path / "attestation.json"

        attestation = generate_attestation(
            output_path=output,
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.95
        )

        # Should parse as ISO 8601
        timestamp = datetime.fromisoformat(attestation["timestamp"])
        assert timestamp.tzinfo is not None  # Should have timezone

    def test_generate_attestation_validation_period(self, tmp_path):
        """Validation period should be 168 hours (7 days)."""
        output = tmp_path / "attestation.json"

        attestation = generate_attestation(
            output_path=output,
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.95
        )

        period = attestation["validation_period"]
        assert period["duration_hours"] == 168

        # Parse timestamps
        start = datetime.fromisoformat(period["start"])
        end = datetime.fromisoformat(period["end"])

        # Difference should be ~7 days
        delta = end - start
        assert 167 <= delta.total_seconds() / 3600 <= 169  # Allow small variance

    def test_generate_attestation_rc_criteria_evaluated(self, tmp_path):
        """RC criteria should be correctly evaluated."""
        output = tmp_path / "attestation.json"

        # Passing attestation
        attestation_pass = generate_attestation(
            output_path=output,
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.95
        )

        assert attestation_pass["rc_criteria"]["overall_pass"] is True

        # Failing attestation
        output_fail = tmp_path / "attestation_fail.json"
        attestation_fail = generate_attestation(
            output_path=output_fail,
            memory_stability=0.70,  # Below threshold
            ris_score=0.90,
            stress_recovery=0.95
        )

        assert attestation_fail["rc_criteria"]["overall_pass"] is False

    def test_generate_attestation_predictive_health_included(self, tmp_path):
        """Predictive health metrics should be included."""
        output = tmp_path / "attestation.json"

        attestation = generate_attestation(
            output_path=output,
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.95
        )

        health = attestation["predictive_health"]
        assert "epd_alerts" in health
        assert "msc_blocks" in health
        assert "collapse_events" in health
        assert "foresight_holds" in health

        # Should be integers
        assert isinstance(health["epd_alerts"], int)
        assert isinstance(health["msc_blocks"], int)


class TestAttestationEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_values(self, tmp_path):
        """Should handle zero values gracefully."""
        output = tmp_path / "zero_attestation.json"

        attestation = generate_attestation(
            output_path=output,
            memory_stability=0.0,
            ris_score=0.0,
            stress_recovery=0.0
        )

        assert attestation["memory_resonance"]["stability"] == 0.0
        assert attestation["ris"]["score"] == 0.0
        assert attestation["stress_resilience"]["recovery_rate"] == 0.0
        assert attestation["rc_criteria"]["overall_pass"] is False

    def test_max_values(self, tmp_path):
        """Should handle maximum values gracefully."""
        output = tmp_path / "max_attestation.json"

        attestation = generate_attestation(
            output_path=output,
            memory_stability=1.0,
            ris_score=1.0,
            stress_recovery=1.0
        )

        assert attestation["memory_resonance"]["stability"] == 1.0
        assert attestation["ris"]["score"] == 1.0
        assert attestation["stress_resilience"]["recovery_rate"] == 1.0
        assert attestation["rc_criteria"]["overall_pass"] is True

    def test_nested_directory_creation(self, tmp_path):
        """Should create nested directories for output path."""
        output = tmp_path / "nested" / "dir" / "attestation.json"

        attestation = generate_attestation(
            output_path=output,
            memory_stability=0.85,
            ris_score=0.90,
            stress_recovery=0.95
        )

        assert output.exists()
        assert output.parent.exists()
