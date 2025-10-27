"""
PQC Verification Service for Memory Lock (Slot08).

Provides verification of quantum-resistant attestation signatures and manages
PQC public key registry for truth anchor attestation validation.

Phase 12C: Quantum-Verified Attestation
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, List
import logging

from nova.crypto.pqc_keyring import PQCKeyring
from nova.slots.slot01_truth_anchor.pqc_attestation import AttestationProof


@dataclass
class PQCKeyRecord:
    """
    Public key registry entry for PQC attestation verification.

    Tracks post-quantum public keys for signature verification,
    including key rotation metadata.
    """

    key_id: str
    algorithm: str
    public_key: bytes
    created_at: datetime
    active: bool = True
    rotated_at: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)


class PQCVerificationService:
    """
    Service for verifying PQC attestation signatures.

    Manages public key registry and provides attestation verification
    with Prometheus metrics integration.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize PQC verification service."""
        self.logger = logger or logging.getLogger("pqc_verify")
        self._key_registry: Dict[str, PQCKeyRecord] = {}

        # Metrics (will be exposed via Prometheus)
        self.metrics = {
            "verifications_total": 0,
            "verifications_success": 0,
            "verifications_failure": 0,
            "key_rotations_total": 0,
        }

    def register_key(
        self,
        public_key: bytes,
        key_id: Optional[str] = None,
        algorithm: str = "Dilithium2",
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Register a PQC public key in the registry.

        Args:
            public_key: Dilithium2 public key bytes
            key_id: Optional key identifier (generated if not provided)
            algorithm: Signature algorithm (default: Dilithium2)
            metadata: Optional metadata (owner, purpose, etc.)

        Returns:
            key_id for the registered key
        """
        if key_id is None:
            key_id = str(uuid.uuid4())

        record = PQCKeyRecord(
            key_id=key_id,
            algorithm=algorithm,
            public_key=public_key,
            created_at=datetime.now(timezone.utc),
            active=True,
            metadata=metadata or {},
        )

        self._key_registry[key_id] = record
        self.logger.info(f"Registered PQC key: {key_id} (algorithm: {algorithm})")
        return key_id

    def get_key(self, key_id: str) -> Optional[PQCKeyRecord]:
        """Retrieve a public key record by ID."""
        return self._key_registry.get(key_id)

    def list_active_keys(self) -> List[PQCKeyRecord]:
        """List all active public keys."""
        return [record for record in self._key_registry.values() if record.active]

    def rotate_key(self, old_key_id: str) -> None:
        """
        Mark a key as rotated (inactive).

        Args:
            old_key_id: Key ID to rotate out
        """
        if old_key_id in self._key_registry:
            record = self._key_registry[old_key_id]
            record.active = False
            record.rotated_at = datetime.now(timezone.utc)
            self.metrics["key_rotations_total"] += 1
            self.logger.info(f"Rotated PQC key: {old_key_id}")
        else:
            self.logger.warning(f"Attempted to rotate non-existent key: {old_key_id}")

    def verify_attestation(
        self,
        proof: AttestationProof,
        public_key_id: Optional[str] = None,
    ) -> bool:
        """
        Verify an attestation proof's PQC signature.

        Args:
            proof: AttestationProof to verify
            public_key_id: Optional key ID (uses proof.public_key_id if not provided)

        Returns:
            True if signature is valid, False otherwise
        """
        self.metrics["verifications_total"] += 1

        # Determine which key to use
        key_id = public_key_id or proof.public_key_id
        if not key_id:
            self.logger.error("No public_key_id provided for verification")
            self.metrics["verifications_failure"] += 1
            return False

        # Retrieve key from registry
        key_record = self.get_key(key_id)
        if not key_record:
            self.logger.error(f"Public key not found in registry: {key_id}")
            self.metrics["verifications_failure"] += 1
            return False

        if not key_record.active:
            self.logger.warning(f"Attempting verification with inactive key: {key_id}")

        # Verify signature
        try:
            from nova.slots.slot01_truth_anchor.pqc_attestation import PQCAttestationBuilder

            is_valid = PQCAttestationBuilder.verify_attestation(proof, key_record.public_key)

            if is_valid:
                self.metrics["verifications_success"] += 1
                self.logger.debug(f"Attestation verified successfully (key: {key_id})")
            else:
                self.metrics["verifications_failure"] += 1
                self.logger.warning(f"Attestation verification failed (key: {key_id})")

            return is_valid

        except Exception as e:
            self.logger.error(f"Verification error: {e}")
            self.metrics["verifications_failure"] += 1
            return False

    def get_metrics(self) -> Dict[str, int]:
        """Get current verification metrics."""
        return self.metrics.copy()
