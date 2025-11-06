"""
Tests for PQC verification integration with ledger verify.

Phase 15-9 Critical Item #2: PQC Verification Integration
"""

import pytest
from nova.ledger.store import LedgerStore
from nova.ledger.verify import ChainVerifier
from nova.ledger.model import RecordKind
from nova.crypto.pqc_keyring import PQCKeyring
from nova.slots.slot08_memory_lock.pqc_verify import PQCVerificationService


class TestPQCVerificationIntegration:
    """Test real PQC signature verification in ledger chain verification."""

    def test_verify_without_pqc_service_legacy_behavior(self):
        """
        Test that without PQC service, verifier assumes all signed records are valid (legacy).
        """
        store = LedgerStore()

        # Create records with fake signatures (no PQC service provided)
        store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            payload={}
        )
        store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.PQC_SIGNED,
            payload={},
            sig=b"fake_signature"  # Invalid signature
        )

        records = store.get_chain("a1")
        verifier = ChainVerifier()  # No PQC service
        result = verifier.verify_chain(records)

        # Legacy behavior: assumes all signed records are valid
        assert result.pqc_signed_count == 1
        assert result.pqc_verified_count == 1  # Assumes valid
        assert result.pqc_ok == 1.0

    def test_verify_with_pqc_service_valid_signature(self):
        """
        Test that with PQC service, verifier performs real signature verification.
        """
        # Setup PQC service and register key
        pqc_service = PQCVerificationService()
        public_key, secret_key = PQCKeyring.generate_keypair()  # Note: returns (pk, sk)
        key_id = pqc_service.register_key(public_key, key_id="test-key-001")

        # Create store and records
        store = LedgerStore()

        # Create anchor
        r1 = store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            payload={}
        )

        # Create signed record with valid signature
        # Sign the payload content (canonical JSON)
        import json
        payload = {"key_id": key_id, "data": "test_data"}
        payload_canonical = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        signature = PQCKeyring.sign(secret_key, payload_canonical)

        r2 = store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.PQC_SIGNED,
            payload=payload,
            sig=signature
        )

        # Verify with PQC service
        records = store.get_chain("a1")
        verifier = ChainVerifier(pqc_service=pqc_service)
        result = verifier.verify_chain(records)

        # Real verification: should verify successfully
        assert result.pqc_signed_count == 1
        assert result.pqc_verified_count == 1  # Real verification passed
        assert result.pqc_ok == 1.0

    def test_verify_with_pqc_service_invalid_signature(self):
        """
        Test that verifier rejects invalid signatures when PQC service is provided.
        """
        # Setup PQC service and register key
        pqc_service = PQCVerificationService()
        public_key, secret_key = PQCKeyring.generate_keypair()  # Note: returns (pk, sk)
        key_id = pqc_service.register_key(public_key, key_id="test-key-002")

        # Create store and records
        store = LedgerStore()

        r1 = store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            payload={}
        )

        # Create signed record with INVALID signature
        r2 = store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.PQC_SIGNED,
            payload={"key_id": key_id},
            sig=b"invalid_fake_signature_bytes_that_dont_match"
        )

        # Verify with PQC service
        records = store.get_chain("a1")
        verifier = ChainVerifier(pqc_service=pqc_service)
        result = verifier.verify_chain(records)

        # Real verification: should reject invalid signature
        assert result.pqc_signed_count == 1
        assert result.pqc_verified_count == 0  # Verification failed
        assert result.pqc_ok == 0.0

    def test_verify_with_missing_key_id(self):
        """
        Test that records without key_id in payload are skipped.
        """
        pqc_service = PQCVerificationService()
        store = LedgerStore()

        r1 = store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.PQC_SIGNED,
            payload={},  # No key_id
            sig=b"some_signature"
        )

        records = store.get_chain("a1")
        verifier = ChainVerifier(pqc_service=pqc_service)
        result = verifier.verify_chain(records)

        # Signed but no key_id = skipped verification
        assert result.pqc_signed_count == 1
        assert result.pqc_verified_count == 0  # Skipped
        assert result.pqc_ok == 0.0

    def test_verify_with_unknown_key_id(self):
        """
        Test that records with unknown key_id are not verified.
        """
        pqc_service = PQCVerificationService()
        store = LedgerStore()

        r1 = store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.PQC_SIGNED,
            payload={"key_id": "nonexistent-key"},
            sig=b"some_signature"
        )

        records = store.get_chain("a1")
        verifier = ChainVerifier(pqc_service=pqc_service)
        result = verifier.verify_chain(records)

        # Unknown key = not verified
        assert result.pqc_signed_count == 1
        assert result.pqc_verified_count == 0
        assert result.pqc_ok == 0.0

    def test_verify_multiple_records_mixed_validity(self):
        """
        Test verification with multiple records: some valid, some invalid.
        """
        pqc_service = PQCVerificationService()
        public_key, secret_key = PQCKeyring.generate_keypair()  # Note: returns (pk, sk)
        key_id = pqc_service.register_key(public_key, key_id="test-key-003")

        store = LedgerStore()

        # Record 1: No signature
        r1 = store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            payload={}
        )

        # Record 2: Valid signature
        import json
        payload2 = {"key_id": key_id, "seq": 2}
        payload2_canonical = json.dumps(payload2, sort_keys=True, separators=(',', ':')).encode('utf-8')
        sig2 = PQCKeyring.sign(secret_key, payload2_canonical)
        r2 = store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.PQC_SIGNED,
            payload=payload2,
            sig=sig2
        )

        # Record 3: Invalid signature
        payload3 = {"key_id": key_id, "seq": 3}
        r3 = store.append(
            anchor_id="a1",
            slot="08",
            kind=RecordKind.PQC_VERIFIED,
            payload=payload3,
            sig=b"invalid_signature"
        )

        # Record 4: Valid signature
        payload4 = {"key_id": key_id, "seq": 4}
        payload4_canonical = json.dumps(payload4, sort_keys=True, separators=(',', ':')).encode('utf-8')
        sig4 = PQCKeyring.sign(secret_key, payload4_canonical)
        r4 = store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.PQC_SIGNED,
            payload=payload4,
            sig=sig4
        )

        records = store.get_chain("a1")
        verifier = ChainVerifier(pqc_service=pqc_service)
        result = verifier.verify_chain(records)

        # 3 signed records: 2 valid, 1 invalid
        assert result.pqc_signed_count == 3
        assert result.pqc_verified_count == 2  # 2 valid
        assert abs(result.pqc_ok - (2.0/3.0)) < 0.01  # ~0.67

    def test_verify_with_public_key_id_alias(self):
        """
        Test that both 'key_id' and 'public_key_id' payload fields work.
        """
        pqc_service = PQCVerificationService()
        public_key, secret_key = PQCKeyring.generate_keypair()  # Note: returns (pk, sk)
        key_id = pqc_service.register_key(public_key, key_id="test-key-004")

        store = LedgerStore()

        r1 = store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.ANCHOR_CREATED,
            payload={}
        )

        # Use 'public_key_id' instead of 'key_id'
        import json
        payload = {"public_key_id": key_id, "data": "test"}
        payload_canonical = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        signature = PQCKeyring.sign(secret_key, payload_canonical)
        r2 = store.append(
            anchor_id="a1",
            slot="01",
            kind=RecordKind.PQC_SIGNED,
            payload=payload,
            sig=signature
        )

        records = store.get_chain("a1")
        verifier = ChainVerifier(pqc_service=pqc_service)
        result = verifier.verify_chain(records)

        assert result.pqc_signed_count == 1
        assert result.pqc_verified_count == 1
        assert result.pqc_ok == 1.0

    def test_backward_compatibility_no_regression(self):
        """
        Test that existing code without PQC service continues to work unchanged.
        """
        store = LedgerStore()

        # Create chain without signatures
        store.append(anchor_id="a1", slot="01", kind=RecordKind.ANCHOR_CREATED, payload={})
        store.append(anchor_id="a1", slot="02", kind=RecordKind.DELTATHRESH_APPLIED, payload={})

        records = store.get_chain("a1")
        verifier = ChainVerifier()  # No PQC service
        result = verifier.verify_chain(records)

        # No signed records
        assert result.pqc_signed_count == 0
        assert result.pqc_verified_count == 0
        assert result.pqc_ok == 0.0
        assert result.continuity_ok is True
