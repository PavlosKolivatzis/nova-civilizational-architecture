"""Truth Anchor Engine v1.2.0.

Provides lightweight management of immutable "truth" anchors used across
slots. Each anchor is stored with optional backup metadata and operations
update internal metrics for observability. The engine performs best-effort
recovery when anchors are missing or corrupted and logs all operations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import hashlib
import logging
import secrets

from .quantum_entropy import EntropySample, get_entropy_sample


@dataclass
class AnchorRecord:
    """In-memory representation of an anchor."""

    value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineMetrics:
    """Simple metrics container for observability."""

    lookups: int = 0
    recoveries: int = 0
    failures: int = 0


@dataclass
class AnchorMetrics:
    """Track anchor counts for regression checks."""

    total_anchors: int = 0
    active_anchors: int = 0


class TruthAnchorEngine:
    """Core engine for truth anchor management (v1.2.0)."""

    VERSION = "1.2.0"

    def __init__(
        self,
        secret_key: Optional[bytes] = None,
        logger: Optional[logging.Logger] = None,
        storage_path: Optional[str] = None,
    ) -> None:
        self._anchors: Dict[str, AnchorRecord] = {}
        self.metrics = EngineMetrics()
        self.anchor_metrics = AnchorMetrics()
        self.logger = logger or logging.getLogger("truth_anchor_engine")

        # Initialize persistence layer
        from .persistence import get_default_persistence
        self._persistence = get_default_persistence(storage_path)

        # Load existing anchors and metrics from persistence
        persisted_data = self._persistence.load()
        if persisted_data.get("anchors"):
            self._anchors = persisted_data["anchors"]
            # Update anchor counts based on loaded data
            self.anchor_metrics.total_anchors = len(self._anchors)
            self.anchor_metrics.active_anchors = len(self._anchors)
            self.logger.debug(f"Loaded {len(self._anchors)} anchors from persistence")

        if persisted_data.get("metrics"):
            # Restore metrics if available
            saved_metrics = persisted_data["metrics"]
            self.metrics.lookups = saved_metrics.get("lookups", 0)
            self.metrics.recoveries = saved_metrics.get("recoveries", 0)
            self.metrics.failures = saved_metrics.get("failures", 0)

        # Handle secret key generation or assignment
        if secret_key is None:
            key_entropy = self._draw_entropy_sample(32)
            self._secret_key = key_entropy.data
            self._secret_key_entropy = key_entropy
        else:
            self._secret_key = secret_key
            self._secret_key_entropy = None
        self._establish_core_anchor()
        # Verify the core anchor exists in an initial snapshot
        if "nova.core" not in self._anchors or self.snapshot()["anchors"] < 1:
            self.logger.error("Core anchor 'nova.core' missing from initialization snapshot")

    def export_secret_key(self) -> bytes:
        """Return the engine's secret key for external storage."""
        return self._secret_key

    # ------------------------------------------------------------------
    # Anchor management
    # ------------------------------------------------------------------
    def register(self, anchor_id: str, value: Any, **metadata: Any) -> None:
        """Register ``value`` under ``anchor_id`` with optional metadata."""
        if anchor_id not in self._anchors:
            self.anchor_metrics.total_anchors += 1
            self.anchor_metrics.active_anchors += 1

        # Ensure backup metadata for recovery
        if "backup" not in metadata:
            metadata["backup"] = value

        entropy_sample = self._draw_entropy_sample()
        self._apply_entropy_metadata(metadata, entropy_sample)

        self._anchors[anchor_id] = AnchorRecord(value=value, metadata=metadata)
        self.logger.debug("Anchor registered: %s", anchor_id)

        # Save to persistence
        self._save_to_persistence()

        # Emit to ledger (Phase 13 RUN 13-3)
        self._emit_anchor_created(anchor_id, metadata)

    def _establish_core_anchor(self) -> None:
        """Ensure the core ``nova.core`` anchor exists without skewing metrics."""
        anchor_id = "nova.core"
        if anchor_id in self._anchors:
            # Replace existing entry without touching metrics
            self._anchors[anchor_id] = AnchorRecord(
                value=self._secret_key, metadata={"backup": self._secret_key}
            )
        else:
            self.register(anchor_id, self._secret_key, backup=self._secret_key)

    def verify(self, anchor_id: str, value: Any) -> bool:
        """Validate ``value`` against a stored anchor.

        Returns ``True`` if the anchor exists and matches ``value``. If the
        anchor is missing or mismatched a recovery attempt is made using
        stored backup data and the result is logged.
        """
        self.metrics.lookups += 1
        record = self._anchors.get(anchor_id)
        if record and record.value == value:
            return True

        self.metrics.failures += 1
        self.logger.warning("Anchor mismatch or missing: %s", anchor_id)
        recovered = self._recover(anchor_id)
        return recovered == value if recovered is not None else False

    def _recover(self, anchor_id: str) -> Optional[Any]:
        """Attempt best-effort recovery for ``anchor_id``.

        Recovery uses a ``backup`` field in the anchor metadata if present.
        """
        record = self._anchors.get(anchor_id)
        backup = record.metadata.get("backup") if record else None
        if backup is not None:
            self.metrics.recoveries += 1
            self.logger.info("Recovered anchor %s from backup", anchor_id)
            # promote backup to active value
            if record:
                record.value = backup
            else:
                self._anchors[anchor_id] = AnchorRecord(value=backup)
            
            # Save recovery to persistence
            self._save_to_persistence()
            return backup
        self.logger.error("Failed to recover anchor: %s", anchor_id)
        return None

    def _save_to_persistence(self) -> None:
        """Save current anchors and metrics to persistent storage."""
        try:
            metrics_dict = {
                "lookups": self.metrics.lookups,
                "recoveries": self.metrics.recoveries,
                "failures": self.metrics.failures,
                "total_anchors": self.anchor_metrics.total_anchors,
                "active_anchors": self.anchor_metrics.active_anchors,
            }
            success = self._persistence.save(self._anchors, metrics_dict)
            if not success:
                self.logger.warning("Failed to save anchors to persistence")
        except Exception as exc:
            self.logger.error(f"Persistence save error: {exc}")

    def _draw_entropy_sample(self, n_bytes: Optional[int] = None) -> EntropySample:
        """Obtain entropy with quantum preference and safe fallback."""
        try:
            return get_entropy_sample(n_bytes)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("Entropy sample fallback: %s", exc)
            entropy = secrets.token_bytes(n_bytes or 32)
            return EntropySample(
                data=entropy,
                source="engine_fallback",
                backend="os.urandom",
                fidelity=None,
                error=str(exc),
            )

    def _apply_entropy_metadata(self, metadata: Dict[str, Any], sample: EntropySample) -> None:
        """Attach entropy provenance to anchor metadata."""
        metadata.setdefault("entropy_source", sample.source)
        metadata.setdefault("entropy_backend", sample.backend)
        metadata.setdefault("entropy_sha3_256", sample.digest())
        metadata.setdefault("entropy_n_bits", 8 * len(sample.data))
        if sample.fidelity is not None:
            metadata.setdefault("quantum_fidelity", sample.fidelity)
        if sample.fidelity_ci is not None:
            metadata.setdefault("quantum_fidelity_ci", sample.fidelity_ci)
        if sample.abs_bias is not None:
            metadata.setdefault("entropy_abs_bias", sample.abs_bias)
        if sample.error:
            metadata.setdefault("entropy_error", sample.error)

    # ------------------------------------------------------------------
    # Ledger Emitters (Phase 13 RUN 13-3)
    # ------------------------------------------------------------------
    def _emit_anchor_created(self, anchor_id: str, metadata: Dict[str, Any]) -> None:
        """Emit ANCHOR_CREATED event to ledger."""
        try:
            from nova.ledger.client import LedgerClient
            from nova.ledger.model import RecordKind

            client = LedgerClient.get_instance()
            client.append_record(
                anchor_id=anchor_id,
                slot="01",
                kind=RecordKind.ANCHOR_CREATED,
                payload={
                    "entropy_sha3_256": metadata.get("entropy_sha3_256", ""),
                    "quantum_fidelity": metadata.get("quantum_fidelity"),
                    "quantum_fidelity_ci": metadata.get("quantum_fidelity_ci"),
                    "entropy_abs_bias": metadata.get("entropy_abs_bias"),
                    "entropy_n_bits": metadata.get("entropy_n_bits"),
                },
                producer="slot01",
                version=self.VERSION,
            )
        except Exception as e:
            self.logger.warning(f"Failed to emit ANCHOR_CREATED to ledger: {e}")

    def _emit_pqc_signed(self, anchor_id: str, signature: bytes, public_key_id: str) -> None:
        """Emit PQC_SIGNED event to ledger."""
        try:
            from nova.ledger.client import LedgerClient
            from nova.ledger.model import RecordKind

            client = LedgerClient.get_instance()
            client.append_record(
                anchor_id=anchor_id,
                slot="01",
                kind=RecordKind.PQC_SIGNED,
                payload={
                    "sign_alg": "Dilithium2",
                    "public_key_id": public_key_id,
                },
                producer="slot01",
                version=self.VERSION,
                sig=signature,
            )
        except Exception as e:
            self.logger.warning(f"Failed to emit PQC_SIGNED to ledger: {e}")

    # ------------------------------------------------------------------
    # Metrics / Introspection
    # ------------------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        """Return a snapshot of the engine state and metrics."""
        return {
            "version": self.VERSION,
            "anchors": len(self._anchors),
            "lookups": self.metrics.lookups,
            "recoveries": self.metrics.recoveries,
            "failures": self.metrics.failures,
            "total_anchors": self.anchor_metrics.total_anchors,
            "active_anchors": self.anchor_metrics.active_anchors,
        }


__all__ = ["TruthAnchorEngine", "AnchorRecord", "EngineMetrics", "AnchorMetrics"]
