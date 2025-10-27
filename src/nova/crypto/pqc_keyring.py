"""
Post-Quantum Cryptography (PQC) keyring for Nova attestation signing.

Uses Dilithium2 (ML-DSA, FIPS 204) for quantum-resistant digital signatures.
Supports key generation, message signing, and signature verification.

Phase 12C: Quantum-Verified Attestation
"""

from typing import Tuple
import base64
from dilithium_py.dilithium import Dilithium2


class PQCKeyring:
    """
    Post-quantum cryptography keyring using Dilithium2.

    Provides quantum-resistant signing and verification for attestation records.
    All keys are Dilithium2 (security level 2, ~128-bit quantum security).
    """

    @staticmethod
    def generate_keypair() -> Tuple[bytes, bytes]:
        """
        Generate a new Dilithium2 keypair.

        Returns:
            (public_key, secret_key) as bytes
        """
        pk, sk = Dilithium2.keygen()
        return pk, sk

    @staticmethod
    def sign(secret_key: bytes, message: bytes) -> bytes:
        """
        Sign a message using Dilithium2.

        Args:
            secret_key: Dilithium2 secret key (from generate_keypair)
            message: Raw message bytes to sign

        Returns:
            Signature bytes
        """
        return Dilithium2.sign(secret_key, message)

    @staticmethod
    def verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
        """
        Verify a Dilithium2 signature.

        Args:
            public_key: Dilithium2 public key
            message: Original message bytes
            signature: Signature to verify

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            return Dilithium2.verify(public_key, message, signature)
        except Exception:
            return False

    @staticmethod
    def encode_key(key: bytes) -> str:
        """Encode key bytes to base64 for storage/transmission."""
        return base64.b64encode(key).decode('ascii')

    @staticmethod
    def decode_key(key_str: str) -> bytes:
        """Decode base64 key string to bytes."""
        return base64.b64decode(key_str.encode('ascii'))

    @staticmethod
    def encode_signature(sig: bytes) -> str:
        """Encode signature bytes to base64."""
        return base64.b64encode(sig).decode('ascii')

    @staticmethod
    def decode_signature(sig_str: str) -> bytes:
        """Decode base64 signature string to bytes."""
        return base64.b64decode(sig_str.encode('ascii'))
