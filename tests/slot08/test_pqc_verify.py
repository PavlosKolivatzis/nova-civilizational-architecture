"""
Tests for PQC verification service (Slot08).

Phase 12C: Quantum-Verified Attestation
"""

import pytest
import uuid
from nova.slots.slot08_memory_lock.pqc_verify import PQCVerificationService
from nova.slots.slot01_truth_anchor.pqc_attestation import PQCAttestationBuilder
from nova.crypto.pqc_keyring import PQCKeyring


class TestPQCVerificationService:
    """Test suite for PQC verification service."""

    def test_register_key(self):
        """Test registering a PQC public key."""
        service = PQCVerificationService()
        pk, _ = PQCKeyring.generate_keypair()

        key_id = service.register_key(pk, algorithm="Dilithium2")
        assert isinstance(key_id, str)

        record = service.get_key(key_id)
        assert record is not None
        assert record.public_key == pk
        assert record.algorithm == "Dilithium2"
        assert record.active is True

    def test_register_key_with_custom_id(self):
        """Test registering key with custom ID."""
        service = PQCVerificationService()
        pk, _ = PQCKeyring.generate_keypair()
        custom_id = "custom-key-123"

        key_id = service.register_key(pk, key_id=custom_id)
        assert key_id == custom_id

        record = service.get_key(custom_id)
        assert record is not None

    def test_list_active_keys(self):
        """Test listing active keys."""
        service = PQCVerificationService()
        pk1, _ = PQCKeyring.generate_keypair()
        pk2, _ = PQCKeyring.generate_keypair()

        key_id1 = service.register_key(pk1)
        key_id2 = service.register_key(pk2)

        active_keys = service.list_active_keys()
        assert len(active_keys) == 2
        assert all(record.active for record in active_keys)

    def test_rotate_key(self):
        """Test key rotation."""
        service = PQCVerificationService()
        pk, _ = PQCKeyring.generate_keypair()
        key_id = service.register_key(pk)

        # Rotate key
        service.rotate_key(key_id)

        record = service.get_key(key_id)
        assert record.active is False
        assert record.rotated_at is not None
        assert service.metrics["key_rotations_total"] == 1

        # Active keys should be empty
        active_keys = service.list_active_keys()
        assert len(active_keys) == 0

    def test_verify_attestation_valid(self):
        """Test verifying a valid attestation."""
        service = PQCVerificationService()
        builder = PQCAttestationBuilder()

        # Register builder's public key
        key_id = service.register_key(builder.public_key, key_id=builder.public_key_id)

        # Create signed attestation
        proof = builder.build_attestation(
            anchor_id=str(uuid.uuid4()),
            entropy_hash="a" * 64,
            quantum_fidelity=0.99,
        )

        # Verify
        assert service.verify_attestation(proof) is True
        assert service.metrics["verifications_success"] == 1
        assert service.metrics["verifications_total"] == 1

    def test_verify_attestation_invalid_signature(self):
        """Test verification fails for invalid signature."""
        service = PQCVerificationService()
        builder = PQCAttestationBuilder()
        service.register_key(builder.public_key, key_id=builder.public_key_id)

        proof = builder.build_attestation(
            anchor_id=str(uuid.uuid4()),
            entropy_hash="b" * 64,
        )

        # Corrupt signature
        proof.signature = proof.signature[:-4] + "XXXX"

        assert service.verify_attestation(proof) is False
        assert service.metrics["verifications_failure"] == 1

    def test_verify_attestation_key_not_found(self):
        """Test verification fails when key not in registry."""
        service = PQCVerificationService()
        builder = PQCAttestationBuilder()

        proof = builder.build_attestation(
            anchor_id=str(uuid.uuid4()),
            entropy_hash="c" * 64,
        )

        # Don't register key
        assert service.verify_attestation(proof) is False
        assert service.metrics["verifications_failure"] == 1

    def test_verify_attestation_with_inactive_key(self):
        """Test verification with rotated (inactive) key."""
        service = PQCVerificationService()
        builder = PQCAttestationBuilder()

        key_id = service.register_key(builder.public_key, key_id=builder.public_key_id)

        proof = builder.build_attestation(
            anchor_id=str(uuid.uuid4()),
            entropy_hash="d" * 64,
        )

        # Rotate key before verification
        service.rotate_key(key_id)

        # Verification should still work (signature is valid) but key is inactive
        # The service should warn but still verify the cryptographic signature
        assert service.verify_attestation(proof) is True

    def test_get_metrics(self):
        """Test metrics retrieval."""
        service = PQCVerificationService()
        builder = PQCAttestationBuilder()
        service.register_key(builder.public_key, key_id=builder.public_key_id)

        proof = builder.build_attestation(
            anchor_id=str(uuid.uuid4()),
            entropy_hash="e" * 64,
        )

        service.verify_attestation(proof)

        metrics = service.get_metrics()
        assert metrics["verifications_total"] == 1
        assert metrics["verifications_success"] == 1
        assert metrics["verifications_failure"] == 0
        assert metrics["key_rotations_total"] == 0

    def test_register_key_with_metadata(self):
        """Test registering key with metadata."""
        service = PQCVerificationService()
        pk, _ = PQCKeyring.generate_keypair()

        metadata = {
            "owner": "slot01",
            "purpose": "truth_anchor_attestation",
        }

        key_id = service.register_key(pk, metadata=metadata)
        record = service.get_key(key_id)

        assert record.metadata == metadata
