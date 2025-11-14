"""
Chain verification and trust scoring for Autonomous Verification Ledger.

Phase 13 RUN 13-2: Implements cross-slot trust computation based on
hash continuity, PQC signatures, and fidelity metrics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .model import LedgerRecord, RecordKind
from .canon import verify_record_hash
from .metrics import (
    ledger_verify_requests_total,
    ledger_verify_duration_seconds,
    ledger_trust_score as trust_score_gauge,
    ledger_chain_length,
)

# Optional import for PQC verification integration
try:
    from nova.crypto.pqc_keyring import PQCKeyring
    from nova.slots.slot08_memory_lock.pqc_verify import PQCVerificationService  # noqa: F401 - used for type hints
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False


@dataclass
class VerificationResult:
    """
    Result of ledger chain verification for an anchor.

    Includes continuity checks, PQC validation, fidelity metrics,
    and composite trust score.
    """

    anchor_id: str
    records: int
    continuity_ok: bool = False
    continuity_errors: List[str] = field(default_factory=list)

    # PQC metrics
    pqc_signed_count: int = 0
    pqc_verified_count: int = 0
    pqc_ok: float = 0.0  # Fraction of successful PQC verifications

    # Fidelity metrics
    fidelity_mean: Optional[float] = None
    fidelity_ci_width_mean: Optional[float] = None
    fidelity_bias_abs_mean: Optional[float] = None

    # Trust score
    trust_score: float = 0.0
    trust_weights: Dict[str, float] = field(default_factory=dict)

    # Metadata
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "anchor_id": self.anchor_id,
            "records": self.records,
            "continuity_ok": self.continuity_ok,
            "continuity_errors": self.continuity_errors,
            "pqc_signed_count": self.pqc_signed_count,
            "pqc_verified_count": self.pqc_verified_count,
            "pqc_ok": self.pqc_ok,
            "fidelity_mean": self.fidelity_mean,
            "fidelity_ci_width_mean": self.fidelity_ci_width_mean,
            "fidelity_bias_abs_mean": self.fidelity_bias_abs_mean,
            "trust_score": self.trust_score,
            "trust_weights": self.trust_weights,
            "verified_at": self.verified_at.isoformat(),
        }


@dataclass
class TrustWeights:
    """Configurable weights for trust score computation."""

    fidelity_mean: float = 0.5
    pqc_rate: float = 0.2
    verify_rate: float = 0.2
    continuity: float = 0.1

    @classmethod
    def from_config(cls, config: Dict) -> TrustWeights:
        """Load weights from configuration."""
        return cls(
            fidelity_mean=config.get("fidelity_mean", 0.5),
            pqc_rate=config.get("pqc_rate", 0.2),
            verify_rate=config.get("verify_rate", 0.2),
            continuity=config.get("continuity", 0.1),
        )


class ChainVerifier:
    """
    Verifies ledger chain integrity and computes trust scores.

    Performs hash continuity checks, PQC signature validation,
    fidelity sanity checks, and composite trust scoring.
    """

    def __init__(
        self,
        trust_weights: Optional[TrustWeights] = None,
        logger: Optional[logging.Logger] = None,
        pqc_service: Optional['PQCVerificationService'] = None,
    ):
        """
        Initialize chain verifier.

        Args:
            trust_weights: Weights for trust score computation
            logger: Logger instance
            pqc_service: Optional PQC verification service for real signature validation
                        (Phase 15-9: If provided, performs actual Dilithium signature verification)
        """
        self.trust_weights = trust_weights or TrustWeights()
        self.logger = logger or logging.getLogger("ledger.verify")
        self.pqc_service = pqc_service

    def verify_chain(self, records: List[LedgerRecord]) -> VerificationResult:
        """
        Verify a chain of records and compute trust score.

        Args:
            records: Ordered list of records for an anchor (chronological)

        Returns:
            VerificationResult with continuity, PQC, fidelity, and trust metrics
        """
        with ledger_verify_duration_seconds.time():
            if not records:
                result = VerificationResult(
                    anchor_id="unknown",
                    records=0,
                    continuity_ok=True,
                    trust_score=0.0,
                )
                ledger_verify_requests_total.labels(result="empty").inc()
                return result

            anchor_id = records[0].anchor_id
            result = VerificationResult(anchor_id=anchor_id, records=len(records))

            # Check hash continuity
            continuity_errors = self._check_continuity(records)
            result.continuity_ok = len(continuity_errors) == 0
            result.continuity_errors = continuity_errors

            # Check PQC signatures
            pqc_metrics = self._check_pqc_signatures(records)
            result.pqc_signed_count = pqc_metrics["signed_count"]
            result.pqc_verified_count = pqc_metrics["verified_count"]
            result.pqc_ok = pqc_metrics["success_rate"]

            # Extract fidelity metrics
            fidelity_metrics = self._extract_fidelity_metrics(records)
            result.fidelity_mean = fidelity_metrics.get("fidelity_mean")
            result.fidelity_ci_width_mean = fidelity_metrics.get("ci_width_mean")
            result.fidelity_bias_abs_mean = fidelity_metrics.get("bias_abs_mean")

            # Compute trust score
            result.trust_score = self._compute_trust_score(result)
            result.trust_weights = {
                "fidelity_mean": self.trust_weights.fidelity_mean,
                "pqc_rate": self.trust_weights.pqc_rate,
                "verify_rate": self.trust_weights.verify_rate,
                "continuity": self.trust_weights.continuity,
            }

            # Update metrics
            verify_result = "pass" if result.continuity_ok and result.trust_score >= 0.7 else "fail"
            ledger_verify_requests_total.labels(result=verify_result).inc()
            trust_score_gauge.labels(anchor_id=anchor_id).set(result.trust_score)
            ledger_chain_length.labels(anchor_id=anchor_id).set(len(records))

            # Log verification
            self.logger.info(
                f"[LEDGER] anchor={anchor_id} trust={result.trust_score:.3f} "
                f"pqc_ok={result.pqc_ok:.2f} F̄={result.fidelity_mean or 0:.3f} "
                f"cont={'✓' if result.continuity_ok else '✗'}"
            )

            if result.trust_score < 0.7:
                self.logger.warning(f"Low trust score for anchor {anchor_id}: {result.trust_score:.3f}")

            return result

    def _check_continuity(self, records: List[LedgerRecord]) -> List[str]:
        """Check hash chain continuity."""
        errors = []

        for i, record in enumerate(records):
            # Verify record hash matches content
            is_valid = verify_record_hash(
                record_hash=record.hash,
                rid=record.rid,
                anchor_id=record.anchor_id,
                slot=record.slot,
                kind=record.kind.value if isinstance(record.kind, RecordKind) else record.kind,
                ts=record.ts,
                prev_hash=record.prev_hash,
                payload=record.payload,
                producer=record.producer,
                version=record.version,
            )

            if not is_valid:
                errors.append(f"Record {record.rid}: hash mismatch")

            # Verify prev_hash continuity
            if i > 0:
                prev_record = records[i - 1]
                if record.prev_hash != prev_record.hash:
                    errors.append(
                        f"Record {record.rid}: prev_hash mismatch "
                        f"(expected {prev_record.hash[:8]}..., got {record.prev_hash[:8] if record.prev_hash else 'None'}...)"
                    )
            else:
                # First record should have prev_hash=None
                if record.prev_hash is not None:
                    errors.append(f"Record {record.rid}: first record has non-null prev_hash")

        return errors

    def _check_pqc_signatures(self, records: List[LedgerRecord]) -> Dict:
        """
        Check PQC signature presence and validity.

        Phase 15-9: If pqc_service is provided, performs actual Dilithium signature
        verification. Otherwise, assumes all signed records are valid (legacy behavior).
        """
        signed_count = sum(1 for r in records if r.sig is not None)
        verified_count = 0

        if self.pqc_service and PQC_AVAILABLE:
            # Phase 15-9: Real signature verification via Slot08
            for record in records:
                if record.sig is None:
                    continue

                # Extract public key ID from payload (if present)
                key_id = record.payload.get("public_key_id") or record.payload.get("key_id")

                if not key_id:
                    self.logger.debug(f"Record {record.rid}: No key_id in payload, skipping verification")
                    continue

                # Get public key from registry
                key_record = self.pqc_service.get_key(key_id)
                if not key_record:
                    self.logger.warning(f"Record {record.rid}: Public key {key_id} not found in registry")
                    continue

                # Verify signature over payload content
                # The signature is over the canonical JSON representation of the payload
                try:
                    import json
                    # Canonical JSON representation (sorted keys, no spaces)
                    payload_canonical = json.dumps(record.payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
                    is_valid = PQCKeyring.verify(
                        public_key=key_record.public_key,
                        message=payload_canonical,
                        signature=record.sig
                    )

                    if is_valid:
                        verified_count += 1
                        self.logger.debug(f"Record {record.rid}: Signature verified successfully")
                    else:
                        self.logger.warning(f"Record {record.rid}: Signature verification failed")

                except Exception as e:
                    self.logger.error(f"Record {record.rid}: Verification error: {e}")

        else:
            # Legacy behavior: Assume all signed records are valid
            verified_count = signed_count

        success_rate = verified_count / signed_count if signed_count > 0 else 0.0

        return {
            "signed_count": signed_count,
            "verified_count": verified_count,
            "success_rate": success_rate,
        }

    def _extract_fidelity_metrics(self, records: List[LedgerRecord]) -> Dict:
        """Extract fidelity metrics from ANCHOR_CREATED and DELTATHRESH_APPLIED records."""
        fidelity_values = []
        ci_widths = []
        biases = []

        for record in records:
            payload = record.payload

            # Extract from ANCHOR_CREATED records
            if record.kind in (RecordKind.ANCHOR_CREATED, "ANCHOR_CREATED"):
                if "quantum_fidelity" in payload:
                    fidelity_values.append(payload["quantum_fidelity"])
                if "quantum_fidelity_ci" in payload:
                    ci = payload["quantum_fidelity_ci"]
                    if isinstance(ci, list) and len(ci) == 2:
                        ci_widths.append(ci[1] - ci[0])
                if "entropy_abs_bias" in payload:
                    biases.append(payload["entropy_abs_bias"])

            # Extract from DELTATHRESH_APPLIED records
            if record.kind in (RecordKind.DELTATHRESH_APPLIED, "DELTATHRESH_APPLIED"):
                if "fidelity" in payload:
                    fidelity_values.append(payload["fidelity"])

        # Compute means
        fidelity_mean = sum(fidelity_values) / len(fidelity_values) if fidelity_values else None
        ci_width_mean = sum(ci_widths) / len(ci_widths) if ci_widths else None
        bias_abs_mean = sum(biases) / len(biases) if biases else None

        # Sanity checks
        if ci_width_mean and ci_width_mean > 0.1:
            self.logger.warning(f"High CI width: {ci_width_mean:.3f} (threshold: 0.1)")
        if bias_abs_mean and bias_abs_mean > 0.05:
            self.logger.warning(f"High bias: {bias_abs_mean:.3f} (threshold: 0.05)")

        return {
            "fidelity_mean": fidelity_mean,
            "ci_width_mean": ci_width_mean,
            "bias_abs_mean": bias_abs_mean,
        }

    def _compute_trust_score(self, result: VerificationResult) -> float:
        """
        Compute composite trust score.

        T = w1·F̄ + w2·pqc_rate + w3·verify_rate + w4·continuity
        """
        w = self.trust_weights

        # Fidelity component (default 1.0 if not available)
        fidelity_component = result.fidelity_mean if result.fidelity_mean is not None else 1.0

        # PQC component
        pqc_component = result.pqc_ok

        # Verify rate component (same as PQC for now)
        verify_component = result.pqc_ok

        # Continuity component (binary)
        continuity_component = 1.0 if result.continuity_ok else 0.0

        # Weighted sum
        trust_score = (
            w.fidelity_mean * fidelity_component
            + w.pqc_rate * pqc_component
            + w.verify_rate * verify_component
            + w.continuity * continuity_component
        )

        # Clamp to [0, 1]
        return max(0.0, min(1.0, trust_score))
