"""
Tests for PQC attestation builder (Slot01).

Phase 12C: Quantum-Verified Attestation
"""

import pytest
import uuid
from nova.slots.slot01_truth_anchor.pqc_attestation import (
    PQCAttestationBuilder,
    AttestationProof,
)
from nova.crypto.pqc_keyring import PQCKeyring


class TestPQCAttestationBuilder:
    """Test suite for quantum-verified attestation proofs."""

    def test_builder_generates_keypair_if_none_provided(self):
        """Test builder auto-generates keypair when not provided."""
        builder = PQCAttestationBuilder()
        assert builder.secret_key is not None
        assert builder.public_key is not None
        assert isinstance(builder.public_key_id, str)

    def test_builder_uses_provided_secret_key(self):
        """Test builder uses provided secret key."""
        pk, sk = PQCKeyring.generate_keypair()
        builder = PQCAttestationBuilder(secret_key=sk, public_key_id="test-key-1")
        assert builder.secret_key == sk
        assert builder.public_key_id == "test-key-1"

    def test_build_attestation_creates_valid_proof(self):
        """Test building attestation creates signed proof."""
        builder = PQCAttestationBuilder()
        anchor_id = str(uuid.uuid4())
        entropy_hash = "a" * 64  # Mock SHA3-256 hash

        proof = builder.build_attestation(
            anchor_id=anchor_id,
            entropy_hash=entropy_hash,
            quantum_fidelity=0.987,
            metadata={"source": "test"},
        )

        assert proof.anchor_id == anchor_id
        assert proof.entropy_hash == entropy_hash
        assert proof.quantum_fidelity == 0.987
        assert proof.sign_alg == "Dilithium2"
        assert proof.signature is not None
        assert proof.public_key_id == builder.public_key_id
        assert proof.metadata["source"] == "test"

    def test_verify_attestation_valid_signature(self):
        """Test verifying a valid attestation proof."""
        builder = PQCAttestationBuilder()
        proof = builder.build_attestation(
            anchor_id=str(uuid.uuid4()),
            entropy_hash="b" * 64,
            quantum_fidelity=0.995,
        )

        # Verify with correct public key
        assert PQCAttestationBuilder.verify_attestation(proof, builder.public_key) is True

    def test_verify_attestation_corrupted_signature(self):
        """Test verification fails for corrupted signature."""
        builder = PQCAttestationBuilder()
        proof = builder.build_attestation(
            anchor_id=str(uuid.uuid4()),
            entropy_hash="c" * 64,
        )

        # Corrupt signature
        original_sig = proof.signature
        proof.signature = original_sig[:-4] + "XXXX"

        assert PQCAttestationBuilder.verify_attestation(proof, builder.public_key) is False

    def test_verify_attestation_wrong_public_key(self):
        """Test verification fails with wrong public key."""
        builder1 = PQCAttestationBuilder()
        builder2 = PQCAttestationBuilder()

        proof = builder1.build_attestation(
            anchor_id=str(uuid.uuid4()),
            entropy_hash="d" * 64,
        )

        # Verify with different builder's public key
        assert PQCAttestationBuilder.verify_attestation(proof, builder2.public_key) is False

    def test_verify_attestation_tampered_data(self):
        """Test verification fails if proof data is tampered."""
        builder = PQCAttestationBuilder()
        proof = builder.build_attestation(
            anchor_id=str(uuid.uuid4()),
            entropy_hash="e" * 64,
            quantum_fidelity=0.99,
        )

        # Keep signature but tamper with data
        proof.quantum_fidelity = 0.50

        assert PQCAttestationBuilder.verify_attestation(proof, builder.public_key) is False

    def test_verify_attestation_no_signature(self):
        """Test verification fails for proof without signature."""
        proof = AttestationProof(
            anchor_id=str(uuid.uuid4()),
            entropy_hash="f" * 64,
            quantum_fidelity=0.98,
            timestamp="2025-10-27T00:00:00+00:00",
        )

        pk, _ = PQCKeyring.generate_keypair()
        assert PQCAttestationBuilder.verify_attestation(proof, pk) is False

    def test_proof_to_dict_excludes_none_values(self):
        """Test proof serialization excludes None fields."""
        proof = AttestationProof(
            anchor_id="test-id",
            entropy_hash="g" * 64,
            quantum_fidelity=None,  # None value
            timestamp="2025-10-27T00:00:00+00:00",
            signature="sig123",
        )

        proof_dict = proof.to_dict()
        assert "quantum_fidelity" not in proof_dict
        assert "anchor_id" in proof_dict
        assert "signature" in proof_dict

    def test_get_public_key_encoded(self):
        """Test public key encoding for storage."""
        builder = PQCAttestationBuilder()
        encoded_pk = builder.get_public_key_encoded()

        assert encoded_pk is not None
        assert isinstance(encoded_pk, str)

        # Verify decode roundtrip
        decoded_pk = PQCKeyring.decode_key(encoded_pk)
        assert decoded_pk == builder.public_key

    def test_attestation_with_metadata(self):
        """Test attestation includes custom metadata."""
        builder = PQCAttestationBuilder()
        metadata = {
            "slot": "slot01",
            "version": "1.2.0",
            "entropy_source": "quantum",
        }

        proof = builder.build_attestation(
            anchor_id=str(uuid.uuid4()),
            entropy_hash="h" * 64,
            quantum_fidelity=0.991,
            metadata=metadata,
        )

        assert proof.metadata == metadata
        assert PQCAttestationBuilder.verify_attestation(proof, builder.public_key) is True
