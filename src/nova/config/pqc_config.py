"""
PQC (Post-Quantum Cryptography) configuration.

Phase 12C: Quantum-Verified Attestation
"""

import os
from dataclasses import dataclass


@dataclass
class PQCConfig:
    """Configuration for post-quantum cryptography features."""

    # Slot01: Attestation configuration
    slot01_pqc_enabled: bool = True
    slot01_pqc_algorithm: str = "dilithium2"

    # Slot08: Verification and key rotation configuration
    slot08_pqc_rotation_days: int = 90
    slot08_pqc_verify_log: bool = True

    @classmethod
    def from_env(cls) -> "PQCConfig":
        """Load PQC configuration from environment variables."""
        return cls(
            slot01_pqc_enabled=os.getenv("NOVA_SLOT01_PQC_ATTESTATION_ENABLED", "true").lower() == "true",
            slot01_pqc_algorithm=os.getenv("NOVA_SLOT01_PQC_ALGORITHM", "dilithium2"),
            slot08_pqc_rotation_days=int(os.getenv("NOVA_SLOT08_PQC_ROTATION_DAYS", "90")),
            slot08_pqc_verify_log=os.getenv("NOVA_SLOT08_PQC_VERIFY_LOG", "true").lower() == "true",
        )
