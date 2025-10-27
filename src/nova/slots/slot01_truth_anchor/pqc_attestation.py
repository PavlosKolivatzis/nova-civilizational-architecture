"""
PQC Attestation Builder for Truth Anchors.

Extends Slot01 truth anchors with post-quantum cryptographic signatures,
binding entropy measurements and fidelity metrics into tamper-evident
attestation records.

Phase 12C: Quantum-Verified Attestation
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from nova.crypto.pqc_keyring import PQCKeyring


@dataclass
class AttestationProof:
    """
    Quantum-verified attestation proof for a truth anchor.

    Binds anchor identity, entropy hash, and fidelity metrics into a
    cryptographically signed record using Dilithium2 (PQC).
    """

    anchor_id: str
    entropy_hash: str
    quantum_fidelity: Optional[float]
    timestamp: str
    sign_alg: str = "Dilithium2"
    signature: Optional[str] = None
    public_key_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class PQCAttestationBuilder:
    """
    Builder for creating quantum-verified attestation proofs.

    Combines truth anchor metadata (ID, entropy, fidelity) with PQC signatures
    to create tamper-evident attestation records.
    """

    def __init__(self, secret_key: Optional[bytes] = None, public_key_id: Optional[str] = None):
        """
        Initialize attestation builder.

        Args:
            secret_key: Dilithium2 secret key (if None, generate new keypair)
            public_key_id: Identifier for the public key (for key rotation tracking)
        """
        if secret_key is None:
            pk, sk = PQCKeyring.generate_keypair()
            self.public_key = pk
            self.secret_key = sk
            self.public_key_id = public_key_id or str(uuid.uuid4())
        else:
            self.secret_key = secret_key
            self.public_key = None  # Caller must provide separately if needed
            self.public_key_id = public_key_id or "default"

    def build_attestation(
        self,
        anchor_id: str,
        entropy_hash: str,
        quantum_fidelity: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AttestationProof:
        """
        Build a signed attestation proof for a truth anchor.

        Args:
            anchor_id: Unique identifier for the truth anchor
            entropy_hash: SHA3-256 hash of the entropy sample
            quantum_fidelity: Fidelity score from quantum entropy validation
            metadata: Additional metadata to include in proof

        Returns:
            AttestationProof with PQC signature
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create unsigned proof
        proof = AttestationProof(
            anchor_id=anchor_id,
            entropy_hash=entropy_hash,
            quantum_fidelity=quantum_fidelity,
            timestamp=timestamp,
            public_key_id=self.public_key_id,
            metadata=metadata or {},
        )

        # Create canonical message for signing
        message = self._create_canonical_message(proof)

        # Sign with PQC key
        signature_bytes = PQCKeyring.sign(self.secret_key, message)
        proof.signature = PQCKeyring.encode_signature(signature_bytes)

        return proof

    @staticmethod
    def _create_canonical_message(proof: AttestationProof) -> bytes:
        """
        Create canonical message for signing.

        Uses deterministic JSON serialization (sorted keys) to ensure
        signature verification works across different environments.
        """
        payload = {
            "anchor_id": proof.anchor_id,
            "entropy_hash": proof.entropy_hash,
            "quantum_fidelity": proof.quantum_fidelity,
            "timestamp": proof.timestamp,
        }
        return json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')

    @staticmethod
    def verify_attestation(proof: AttestationProof, public_key: bytes) -> bool:
        """
        Verify an attestation proof's signature.

        Args:
            proof: AttestationProof to verify
            public_key: Dilithium2 public key bytes

        Returns:
            True if signature is valid, False otherwise
        """
        if not proof.signature:
            return False

        try:
            message = PQCAttestationBuilder._create_canonical_message(proof)
            signature_bytes = PQCKeyring.decode_signature(proof.signature)
            return PQCKeyring.verify(public_key, message, signature_bytes)
        except Exception:
            return False

    def get_public_key_encoded(self) -> Optional[str]:
        """Get base64-encoded public key for storage/transmission."""
        if self.public_key:
            return PQCKeyring.encode_key(self.public_key)
        return None
