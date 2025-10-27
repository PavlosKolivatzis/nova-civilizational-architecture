"""
Tests for PQC keyring (Dilithium2 signing/verification).

Phase 12C: Quantum-Verified Attestation
"""

import pytest
from nova.crypto.pqc_keyring import PQCKeyring


class TestPQCKeyring:
    """Test suite for post-quantum cryptography keyring."""

    def test_generate_keypair(self):
        """Test keypair generation returns valid keys."""
        pk, sk = PQCKeyring.generate_keypair()
        assert isinstance(pk, bytes)
        assert isinstance(sk, bytes)
        assert len(pk) > 0
        assert len(sk) > 0
        # Dilithium2 public key is 1312 bytes, secret key is 2528 bytes
        assert len(pk) == 1312
        assert len(sk) == 2528

    def test_sign_and_verify_valid(self):
        """Test signing and verifying a valid message."""
        pk, sk = PQCKeyring.generate_keypair()
        message = b"Nova truth anchor attestation"

        signature = PQCKeyring.sign(sk, message)
        assert isinstance(signature, bytes)
        assert len(signature) > 0

        # Verify signature
        assert PQCKeyring.verify(pk, message, signature) is True

    def test_verify_invalid_signature(self):
        """Test verification fails for corrupted signature."""
        pk, sk = PQCKeyring.generate_keypair()
        message = b"Original message"
        signature = PQCKeyring.sign(sk, message)

        # Corrupt signature
        corrupted_sig = signature[:-1] + bytes([signature[-1] ^ 0xFF])

        assert PQCKeyring.verify(pk, message, corrupted_sig) is False

    def test_verify_wrong_message(self):
        """Test verification fails for different message."""
        pk, sk = PQCKeyring.generate_keypair()
        original_msg = b"Original message"
        different_msg = b"Different message"

        signature = PQCKeyring.sign(sk, original_msg)

        assert PQCKeyring.verify(pk, different_msg, signature) is False

    def test_verify_wrong_public_key(self):
        """Test verification fails with wrong public key."""
        pk1, sk1 = PQCKeyring.generate_keypair()
        pk2, sk2 = PQCKeyring.generate_keypair()

        message = b"Test message"
        signature = PQCKeyring.sign(sk1, message)

        # Verify with different public key
        assert PQCKeyring.verify(pk2, message, signature) is False

    def test_encode_decode_key(self):
        """Test key encoding/decoding roundtrip."""
        pk, sk = PQCKeyring.generate_keypair()

        # Encode
        pk_encoded = PQCKeyring.encode_key(pk)
        sk_encoded = PQCKeyring.encode_key(sk)

        assert isinstance(pk_encoded, str)
        assert isinstance(sk_encoded, str)

        # Decode
        pk_decoded = PQCKeyring.decode_key(pk_encoded)
        sk_decoded = PQCKeyring.decode_key(sk_encoded)

        assert pk_decoded == pk
        assert sk_decoded == sk

    def test_encode_decode_signature(self):
        """Test signature encoding/decoding roundtrip."""
        pk, sk = PQCKeyring.generate_keypair()
        message = b"Test message"
        signature = PQCKeyring.sign(sk, message)

        # Encode
        sig_encoded = PQCKeyring.encode_signature(signature)
        assert isinstance(sig_encoded, str)

        # Decode
        sig_decoded = PQCKeyring.decode_signature(sig_encoded)
        assert sig_decoded == signature

        # Verify decoded signature works
        assert PQCKeyring.verify(pk, message, sig_decoded) is True

    def test_signature_deterministic_same_key(self):
        """Test that signatures vary even for same message/key (randomized)."""
        pk, sk = PQCKeyring.generate_keypair()
        message = b"Test message"

        sig1 = PQCKeyring.sign(sk, message)
        sig2 = PQCKeyring.sign(sk, message)

        # Dilithium2 signatures are randomized, so they should differ
        # but both should verify
        assert PQCKeyring.verify(pk, message, sig1) is True
        assert PQCKeyring.verify(pk, message, sig2) is True
