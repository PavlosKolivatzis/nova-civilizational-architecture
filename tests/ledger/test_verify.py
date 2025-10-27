"""
Tests for chain verification and trust scoring.

Phase 13 RUN 13-2: Autonomous Verification Ledger
"""

import pytest
from nova.ledger.store import LedgerStore
from nova.ledger.verify import ChainVerifier, TrustWeights
from nova.ledger.model import RecordKind


class TestChainVerifier:
    """Test chain verification logic."""

    def test_verify_empty_chain(self):
        """Test verifying an empty chain."""
        verifier = ChainVerifier()
        result = verifier.verify_chain([])

        assert result.records == 0
        assert result.continuity_ok is True
        assert result.trust_score == 0.0

    def test_verify_single_record(self):
        """Test verifying a chain with one record."""
        store = LedgerStore()
        record = store.append(
            anchor_id="anchor-1",
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            payload={"quantum_fidelity": 0.99},
        )

        verifier = ChainVerifier()
        result = verifier.verify_chain([record])

        assert result.records == 1
        assert result.continuity_ok is True
        assert result.trust_score > 0.0

    def test_verify_valid_chain(self):
        """Test verifying a valid multi-record chain."""
        store = LedgerStore()

        store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={"quantum_fidelity": 0.98})
        store.append(anchor_id="a1", slot="01", kind=RecordKind.PQC_SIGNED, payload={})
        store.append(anchor_id="a1", slot="08", kind=RecordKind.PQC_VERIFIED, payload={})

        records = store.get_chain("a1")
        verifier = ChainVerifier()
        result = verifier.verify_chain(records)

        assert result.records == 3
        assert result.continuity_ok is True
        assert len(result.continuity_errors) == 0
        assert result.trust_score > 0.5  # Has good fidelity + continuity

    def test_verify_detects_hash_tampering(self):
        """Test that verification detects tampered records."""
        store = LedgerStore()

        r1 = store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={"data": "original"})
        r2 = store.append(anchor_id="a1", slot="01", kind=RecordKind.PQC_SIGNED, payload={})

        # Tamper with record
        r1.payload["data"] = "tampered"

        records = store.get_chain("a1")
        verifier = ChainVerifier()
        result = verifier.verify_chain(records)

        assert result.continuity_ok is False
        assert len(result.continuity_errors) > 0
        assert "hash mismatch" in result.continuity_errors[0].lower()

    def test_verify_detects_broken_chain(self):
        """Test that verification detects broken prev_hash chain."""
        store = LedgerStore()

        r1 = store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})
        r2 = store.append(anchor_id="a1", slot="01", kind=RecordKind.PQC_SIGNED, payload={})

        # Break the chain
        r2.prev_hash = "invalid_hash"

        records = store.get_chain("a1")
        verifier = ChainVerifier()
        result = verifier.verify_chain(records)

        assert result.continuity_ok is False
        assert any("prev_hash mismatch" in err.lower() for err in result.continuity_errors)


class TestTrustScoring:
    """Test trust score computation."""

    def test_trust_score_perfect_chain(self):
        """Test trust score for a perfect chain."""
        store = LedgerStore()

        store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            payload={"quantum_fidelity": 1.0, "quantum_fidelity_ci": [0.99, 1.0], "entropy_abs_bias": 0.0},
        )
        store.append(anchor_id="a1", slot="01", kind=RecordKind.PQC_SIGNED, payload={}, sig=b"fake_sig")
        store.append(anchor_id="a1", slot="08", kind=RecordKind.PQC_VERIFIED, payload={})

        records = store.get_chain("a1")
        verifier = ChainVerifier()
        result = verifier.verify_chain(records)

        # Perfect chain should have high trust score
        assert result.trust_score >= 0.9
        assert result.fidelity_mean == 1.0
        assert result.pqc_ok > 0.0  # Has signatures

    def test_trust_score_no_fidelity(self):
        """Test trust score when fidelity data is missing."""
        store = LedgerStore()

        store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})
        store.append(anchor_id="a1", slot="01", kind=RecordKind.PQC_SIGNED, payload={})

        records = store.get_chain("a1")
        verifier = ChainVerifier()
        result = verifier.verify_chain(records)

        # Should use default fidelity of 1.0
        assert result.fidelity_mean is None
        assert result.trust_score > 0.0  # Still computes score

    def test_trust_score_broken_continuity(self):
        """Test that broken continuity lowers trust score."""
        store = LedgerStore()

        r1 = store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={"quantum_fidelity": 1.0})
        r2 = store.append(anchor_id="a1", slot="01", kind=RecordKind.PQC_SIGNED, payload={})

        # Break continuity
        r2.prev_hash = "invalid"

        records = store.get_chain("a1")
        verifier = ChainVerifier()
        result = verifier.verify_chain(records)

        assert result.continuity_ok is False
        # Trust score should be lowered due to continuity weight
        assert result.trust_score < 1.0

    def test_trust_score_custom_weights(self):
        """Test trust score with custom weights."""
        store = LedgerStore()

        store.append(
            anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={"quantum_fidelity": 0.8}
        )

        records = store.get_chain("a1")

        # Fidelity-heavy weighting
        weights = TrustWeights(fidelity_mean=0.9, pqc_rate=0.05, verify_rate=0.025, continuity=0.025)
        verifier = ChainVerifier(trust_weights=weights)
        result = verifier.verify_chain(records)

        # Trust score should be heavily influenced by fidelity (0.8)
        assert 0.7 <= result.trust_score <= 0.9

    def test_trust_score_clamped(self):
        """Test that trust score is clamped to [0, 1]."""
        store = LedgerStore()

        store.append(
            anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={"quantum_fidelity": 2.0}  # Invalid
        )

        records = store.get_chain("a1")
        verifier = ChainVerifier()
        result = verifier.verify_chain(records)

        # Should be clamped to 1.0
        assert 0.0 <= result.trust_score <= 1.0

    def test_fidelity_extraction(self):
        """Test extraction of fidelity metrics from records."""
        store = LedgerStore()

        store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            payload={
                "quantum_fidelity": 0.98,
                "quantum_fidelity_ci": [0.97, 0.99],
                "entropy_abs_bias": 0.01,
            },
        )
        store.append(
            anchor_id="a1", slot="02", kind=RecordKind.DELTATHRESH_APPLIED, payload={"fidelity": 0.99, "weight": 1.05}
        )

        records = store.get_chain("a1")
        verifier = ChainVerifier()
        result = verifier.verify_chain(records)

        # Should average fidelity from both records
        assert result.fidelity_mean is not None
        assert 0.98 <= result.fidelity_mean <= 0.99
        assert result.fidelity_ci_width_mean is not None
        assert abs(result.fidelity_ci_width_mean - 0.02) < 1e-6  # 0.99 - 0.97, float tolerance
        assert result.fidelity_bias_abs_mean == 0.01
