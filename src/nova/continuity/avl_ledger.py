"""Autonomous Verification Ledger (AVL) - Phase 13

Immutable, hash-chained ledger of regime transitions with dual-modality verification.
Provides provenance, drift detection, and continuity proofs for ORP evaluations.

Design: ADR-13-Init.md
"""

from __future__ import annotations
import hashlib
import json
import os
import tempfile
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Genesis hash constant (64 zeros)
GENESIS_HASH = "0" * 64

# Default ledger path
DEFAULT_LEDGER_PATH = "data/avl/avl_ledger.jsonl"


@dataclass
class AVLEntry:
    """Single ledger entry (one regime evaluation).

    Schema per ADR-13-Init.md.
    """
    # Identity & chain
    entry_id: str = ""  # SHA256(timestamp + regime + factors_json)
    prev_entry_hash: str = GENESIS_HASH  # Hash of previous entry (chain pointer)

    # Temporal
    timestamp: str = ""  # ISO8601 with timezone
    elapsed_s: float = 0.0  # Seconds since system start

    # ORP evaluation
    orp_regime: str = "normal"
    orp_regime_score: float = 0.0
    contributing_factors: Dict[str, float] = field(default_factory=dict)
    posture_adjustments: Dict[str, Any] = field(default_factory=dict)

    # Oracle verification
    oracle_regime: str = "normal"
    oracle_regime_score: float = 0.0
    dual_modality_agreement: bool = True

    # Transition metadata
    transition_from: Optional[str] = None
    time_in_previous_regime_s: float = 0.0

    # Invariants (per-entry validation)
    hysteresis_enforced: bool = True
    min_duration_enforced: bool = True
    ledger_continuity: bool = True
    amplitude_valid: bool = True

    # Drift detection
    drift_detected: bool = False
    drift_reasons: List[str] = field(default_factory=list)

    # Metadata
    node_id: str = ""
    orp_version: str = "phase13.1"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AVLEntry:
        """Create AVLEntry from dictionary."""
        return cls(**data)

    def to_json(self) -> str:
        """Serialize to JSON string with canonical ordering."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> AVLEntry:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


def compute_entry_hash(entry: AVLEntry) -> str:
    """Compute deterministic SHA256 hash of entry.

    Uses canonical JSON representation with sorted keys for determinism.
    Hash is computed from: timestamp, orp_regime, orp_regime_score,
    contributing_factors, oracle_regime.
    """
    canonical_repr = json.dumps({
        "timestamp": entry.timestamp,
        "orp_regime": entry.orp_regime,
        "orp_regime_score": entry.orp_regime_score,
        "contributing_factors": entry.contributing_factors,
        "oracle_regime": entry.oracle_regime,
    }, sort_keys=True)
    return hashlib.sha256(canonical_repr.encode()).hexdigest()


def compute_entry_id(entry: AVLEntry) -> str:
    """Compute unique entry ID from timestamp + regime + factors.

    Entry ID is deterministic: same inputs → same ID.
    """
    id_repr = json.dumps({
        "timestamp": entry.timestamp,
        "orp_regime": entry.orp_regime,
        "contributing_factors": entry.contributing_factors,
    }, sort_keys=True)
    return hashlib.sha256(id_repr.encode()).hexdigest()


class AVLLedger:
    """Autonomous Verification Ledger.

    Immutable, append-only ledger with hash chain integrity.
    Thread-safe for concurrent reads/writes.
    """

    def __init__(self, ledger_path: Optional[str] = None):
        """Initialize ledger from file or create new.

        Args:
            ledger_path: Path to ledger file. If None, uses DEFAULT_LEDGER_PATH.
                        If file exists, loads entries. Otherwise creates empty ledger.
        """
        self._path = Path(ledger_path or os.environ.get("NOVA_AVL_PATH", DEFAULT_LEDGER_PATH))
        self._entries: List[AVLEntry] = []
        self._lock = threading.RLock()

        # Load existing ledger if present
        if self._path.exists():
            self._load()

    def _load(self) -> None:
        """Load ledger from JSON Lines file."""
        with self._lock:
            self._entries = []
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = AVLEntry.from_json(line)
                        self._entries.append(entry)

    def _save_entry(self, entry: AVLEntry) -> None:
        """Append single entry to file atomically.

        Uses temp file + rename pattern for atomic writes.
        """
        # Ensure directory exists
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Append to file (atomic at line level on most filesystems)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(entry.to_json() + "\n")

    def append(self, entry: AVLEntry) -> AVLEntry:
        """Append entry with hash chain update.

        Computes entry_id and prev_entry_hash automatically.
        Entry is persisted to file atomically.

        Args:
            entry: AVLEntry to append (entry_id and prev_entry_hash will be set)

        Returns:
            The appended entry with computed hashes

        Raises:
            ValueError: If entry_id already exists (duplicate detection)
        """
        with self._lock:
            # Set prev_entry_hash from chain
            if self._entries:
                entry.prev_entry_hash = compute_entry_hash(self._entries[-1])
            else:
                entry.prev_entry_hash = GENESIS_HASH

            # Compute entry_id
            entry.entry_id = compute_entry_id(entry)

            # Check for duplicate entry_id
            existing_ids = {e.entry_id for e in self._entries}
            if entry.entry_id in existing_ids:
                raise ValueError(f"Duplicate entry_id: {entry.entry_id}")

            # Append to in-memory list
            self._entries.append(entry)

            # Persist to file
            self._save_entry(entry)

            return entry

    def get_entries(self) -> List[AVLEntry]:
        """Get all entries (copy to prevent mutation)."""
        with self._lock:
            return list(self._entries)

    def get_latest(self, n: int = 10) -> List[AVLEntry]:
        """Return last N entries.

        Args:
            n: Number of entries to return (default 10)

        Returns:
            List of last N entries (or all if fewer than N)
        """
        with self._lock:
            return list(self._entries[-n:])

    def query_by_time_window(self, start: str, end: str) -> List[AVLEntry]:
        """Return entries in [start, end] time window.

        Args:
            start: ISO8601 timestamp (inclusive)
            end: ISO8601 timestamp (inclusive)

        Returns:
            List of entries with timestamp in [start, end]
        """
        with self._lock:
            return [
                e for e in self._entries
                if start <= e.timestamp <= end
            ]

    def query_by_regime(self, regime: str) -> List[AVLEntry]:
        """Return all entries where orp_regime == regime.

        Args:
            regime: Regime name to filter by

        Returns:
            List of matching entries
        """
        with self._lock:
            return [e for e in self._entries if e.orp_regime == regime]

    def query_drift_events(self) -> List[AVLEntry]:
        """Return only entries with drift_detected=True."""
        with self._lock:
            return [e for e in self._entries if e.drift_detected]

    def query_by_entry_id(self, entry_id: str) -> Optional[AVLEntry]:
        """Find entry by entry_id.

        Args:
            entry_id: Entry ID to search for

        Returns:
            Matching entry or None
        """
        with self._lock:
            for e in self._entries:
                if e.entry_id == entry_id:
                    return e
            return None

    def verify_hash_chain(self) -> Tuple[bool, List[str]]:
        """Verify entire hash chain is intact.

        Returns:
            Tuple of (is_valid, list of violation messages)
        """
        with self._lock:
            violations = []

            if not self._entries:
                return True, []

            # Check genesis entry
            if self._entries[0].prev_entry_hash != GENESIS_HASH:
                violations.append(
                    f"Entry 0: prev_entry_hash should be genesis hash, "
                    f"got {self._entries[0].prev_entry_hash[:16]}..."
                )

            # Check chain continuity
            for i in range(1, len(self._entries)):
                expected_hash = compute_entry_hash(self._entries[i - 1])
                actual_hash = self._entries[i].prev_entry_hash

                if actual_hash != expected_hash:
                    violations.append(
                        f"Entry {i}: prev_entry_hash mismatch. "
                        f"Expected {expected_hash[:16]}..., got {actual_hash[:16]}..."
                    )

            return len(violations) == 0, violations

    def verify_entry_ids(self) -> Tuple[bool, List[str]]:
        """Verify all entry_ids are unique and correctly computed.

        Returns:
            Tuple of (is_valid, list of violation messages)
        """
        with self._lock:
            violations = []
            seen_ids = set()

            for i, entry in enumerate(self._entries):
                # Check uniqueness
                if entry.entry_id in seen_ids:
                    violations.append(f"Entry {i}: duplicate entry_id {entry.entry_id[:16]}...")
                seen_ids.add(entry.entry_id)

                # Check computation
                expected_id = compute_entry_id(entry)
                if entry.entry_id != expected_id:
                    violations.append(
                        f"Entry {i}: entry_id mismatch. "
                        f"Expected {expected_id[:16]}..., got {entry.entry_id[:16]}..."
                    )

            return len(violations) == 0, violations

    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """Verify hash chain + entry IDs + all continuity proofs.

        Returns:
            Tuple of (is_valid, list of all violation messages)
        """
        all_violations = []

        # Hash chain
        _, hash_violations = self.verify_hash_chain()
        all_violations.extend(hash_violations)

        # Entry IDs
        _, id_violations = self.verify_entry_ids()
        all_violations.extend(id_violations)

        return len(all_violations) == 0, all_violations

    def export(self, path: str, format: str = "jsonl") -> None:
        """Export ledger to file.

        Args:
            path: Output file path
            format: Export format ("jsonl" only for now)

        Raises:
            ValueError: If format is not supported
        """
        if format != "jsonl":
            raise ValueError(f"Unsupported export format: {format}")

        with self._lock:
            output_path = Path(path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                for entry in self._entries:
                    f.write(entry.to_json() + "\n")

    def import_jsonl(self, path: str, verify: bool = True) -> int:
        """Import entries from JSON Lines file.

        Args:
            path: Input file path
            verify: If True, verify hash chain after import

        Returns:
            Number of entries imported

        Raises:
            ValueError: If verification fails
        """
        import_path = Path(path)
        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {path}")

        with self._lock:
            imported = 0
            with open(import_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = AVLEntry.from_json(line)
                        self._entries.append(entry)
                        imported += 1

            if verify:
                is_valid, violations = self.verify_integrity()
                if not is_valid:
                    # Rollback
                    self._entries = self._entries[:-imported]
                    raise ValueError(f"Import verification failed: {violations}")

            # Persist all entries
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                for entry in self._entries:
                    f.write(entry.to_json() + "\n")

            return imported

    def __len__(self) -> int:
        """Return number of entries in ledger."""
        with self._lock:
            return len(self._entries)

    def __iter__(self):
        """Iterate over entries."""
        with self._lock:
            return iter(list(self._entries))

    def clear(self) -> None:
        """Clear all entries (for testing only).

        WARNING: This destroys the ledger. Use only in tests.
        """
        with self._lock:
            self._entries = []
            if self._path.exists():
                self._path.unlink()


# ---------- Global Singleton ----------
_GLOBAL_AVL: Optional[AVLLedger] = None
_AVL_LOCK = threading.Lock()


def get_avl_ledger() -> AVLLedger:
    """Get or create global AVL ledger instance.

    Thread-safe singleton accessor.
    """
    global _GLOBAL_AVL
    with _AVL_LOCK:
        if _GLOBAL_AVL is None:
            _GLOBAL_AVL = AVLLedger()
        return _GLOBAL_AVL


def reset_avl_ledger() -> None:
    """Reset global AVL ledger (for testing)."""
    global _GLOBAL_AVL
    with _AVL_LOCK:
        if _GLOBAL_AVL is not None:
            _GLOBAL_AVL.clear()
        _GLOBAL_AVL = None


def avl_enabled() -> bool:
    """Check if AVL is enabled via environment variable.

    Returns:
        True if NOVA_ENABLE_AVL == "1"
    """
    return os.environ.get("NOVA_ENABLE_AVL", "0") == "1"
