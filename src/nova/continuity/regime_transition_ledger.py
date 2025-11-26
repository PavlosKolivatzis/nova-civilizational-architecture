"""Regime Transition Ledger - Phase 11.3

Immutable append-only ledger tracking ORP regime transitions.
Records transition history for duration calculation, oscillation detection, and audit trail.
Pure observation layer - does not modify regime classification behavior.

Contract: regime_transition_ledger@1.yaml
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


# Regime ordering for transition type classification
REGIME_ORDER = ["normal", "heightened", "controlled_degradation", "emergency_stabilization", "recovery"]


@dataclass
class TransitionRecord:
    """Single regime transition record (immutable after creation)."""
    timestamp: str  # ISO 8601 UTC
    from_regime: str
    to_regime: str
    regime_score: float
    contributing_factors: Dict[str, float]
    duration_in_previous_s: float
    transition_type: str  # "upgrade", "downgrade", "initial"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return asdict(self)


@dataclass
class LedgerQueryResult:
    """Result of ledger query operations."""
    transitions: List[TransitionRecord]
    total_count: int
    current_regime: str
    time_in_current_regime_s: float


@dataclass
class OscillationDetection:
    """Metrics for detecting regime oscillation."""
    window_s: float
    transition_count: int
    oscillation_detected: bool
    oscillation_threshold: int


class RegimeTransitionLedger:
    """Append-only ledger for regime transitions.

    Thread-safe for single-writer, multiple-reader scenarios.
    """

    def __init__(self, ledger_path: str = "data/regime_transition_ledger.jsonl"):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory cache of recent transitions (for fast queries)
        self._cache: List[TransitionRecord] = []
        self._cache_limit = 1000

        # Current regime state
        self._current_regime = "normal"
        self._last_transition_time: Optional[float] = None

        # Load existing ledger
        self._load_ledger()

    def _load_ledger(self) -> None:
        """Load existing ledger file into cache."""
        if not self.ledger_path.exists():
            return

        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    record = TransitionRecord(**data)
                    self._cache.append(record)

                    # Update current regime state
                    self._current_regime = record.to_regime
                    self._last_transition_time = self._parse_timestamp(record.timestamp)

            # Keep only recent records in cache
            if len(self._cache) > self._cache_limit:
                self._cache = self._cache[-self._cache_limit:]

        except Exception as e:
            # Non-fatal: log and continue with empty cache
            print(f"Warning: Failed to load regime ledger: {e}")

    def _parse_timestamp(self, iso_timestamp: str) -> float:
        """Parse ISO 8601 timestamp to Unix epoch seconds."""
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        return dt.timestamp()

    def _compute_transition_type(self, from_regime: str, to_regime: str) -> str:
        """Compute transition type based on regime ordering."""
        if from_regime == "initial":
            return "initial"

        try:
            from_idx = REGIME_ORDER.index(from_regime)
            to_idx = REGIME_ORDER.index(to_regime)

            if to_idx > from_idx:
                return "upgrade"  # More restrictive
            elif to_idx < from_idx:
                return "downgrade"  # Less restrictive
            else:
                return "initial"  # Same regime (shouldn't happen)
        except ValueError:
            return "initial"  # Unknown regime

    def record_transition(
        self,
        from_regime: str,
        to_regime: str,
        regime_score: float,
        contributing_factors: Dict[str, float],
        duration_in_previous_s: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Append transition record to ledger (immutable).

        Returns:
            {"success": bool, "record_id": str}
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        transition_type = self._compute_transition_type(from_regime, to_regime)

        record = TransitionRecord(
            timestamp=timestamp,
            from_regime=from_regime,
            to_regime=to_regime,
            regime_score=regime_score,
            contributing_factors=contributing_factors or {},
            duration_in_previous_s=duration_in_previous_s,
            transition_type=transition_type,
            metadata=metadata or {}
        )

        # Append to file (atomic write with fsync)
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict()) + "\n")
                f.flush()
                os.fsync(f.fileno())

            # Update cache and current state
            self._cache.append(record)
            if len(self._cache) > self._cache_limit:
                self._cache = self._cache[-self._cache_limit:]

            self._current_regime = to_regime
            self._last_transition_time = self._parse_timestamp(timestamp)

            return {"success": True, "record_id": timestamp}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_current_regime_duration(self) -> Dict[str, Any]:
        """Calculate time in current regime.

        Returns:
            {"regime": str, "duration_s": float, "since_timestamp": str}
        """
        if self._last_transition_time is None:
            # No transitions recorded - return initial state
            return {
                "regime": self._current_regime,
                "duration_s": 0.0,
                "since_timestamp": datetime.now(timezone.utc).isoformat()
            }

        duration_s = time.time() - self._last_transition_time

        # Find the timestamp from cache
        since_timestamp = None
        for record in reversed(self._cache):
            if record.to_regime == self._current_regime:
                since_timestamp = record.timestamp
                break

        if since_timestamp is None:
            since_timestamp = datetime.now(timezone.utc).isoformat()

        return {
            "regime": self._current_regime,
            "duration_s": duration_s,
            "since_timestamp": since_timestamp
        }

    def query_transitions(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        from_regime: Optional[str] = None,
        to_regime: Optional[str] = None,
        limit: int = 100
    ) -> LedgerQueryResult:
        """Query transition history with filters.

        Returns transitions in descending timestamp order (newest first).
        """
        # Filter cache
        filtered = self._cache[:]

        if start_time:
            start_ts = self._parse_timestamp(start_time)
            filtered = [r for r in filtered if self._parse_timestamp(r.timestamp) >= start_ts]

        if end_time:
            end_ts = self._parse_timestamp(end_time)
            filtered = [r for r in filtered if self._parse_timestamp(r.timestamp) <= end_ts]

        if from_regime:
            filtered = [r for r in filtered if r.from_regime == from_regime]

        if to_regime:
            filtered = [r for r in filtered if r.to_regime == to_regime]

        # Sort descending (newest first)
        filtered.sort(key=lambda r: r.timestamp, reverse=True)

        # Apply limit
        total_count = len(filtered)
        filtered = filtered[:limit]

        # Get current regime info
        duration_info = self.get_current_regime_duration()

        return LedgerQueryResult(
            transitions=filtered,
            total_count=total_count,
            current_regime=duration_info["regime"],
            time_in_current_regime_s=duration_info["duration_s"]
        )

    def detect_oscillation(
        self,
        window_s: float = 3600,
        threshold: int = 5
    ) -> OscillationDetection:
        """Check for regime oscillation in recent history.

        Only counts actual regime changes (not same→same).
        """
        now = time.time()
        cutoff_time = now - window_s

        # Count transitions in window
        transition_count = 0
        for record in self._cache:
            record_time = self._parse_timestamp(record.timestamp)
            if record_time < cutoff_time:
                continue

            # Only count actual changes
            if record.from_regime != record.to_regime:
                transition_count += 1

        oscillation_detected = transition_count >= threshold

        return OscillationDetection(
            window_s=window_s,
            transition_count=transition_count,
            oscillation_detected=oscillation_detected,
            oscillation_threshold=threshold
        )


# Global singleton instance
_ledger_instance: Optional[RegimeTransitionLedger] = None


def _ledger_enabled() -> bool:
    """Check if regime ledger is enabled via NOVA_ENABLE_REGIME_LEDGER flag."""
    return os.getenv("NOVA_ENABLE_REGIME_LEDGER", "0") == "1"


def get_regime_ledger() -> RegimeTransitionLedger:
    """Get global ledger instance (singleton)."""
    global _ledger_instance
    if _ledger_instance is None:
        _ledger_instance = RegimeTransitionLedger()
    return _ledger_instance


def record_regime_transition(
    from_regime: str,
    to_regime: str,
    regime_score: float,
    contributing_factors: Dict[str, float],
    duration_in_previous_s: float,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Record regime transition (flag-gated).

    Returns {"success": bool, "record_id": str} if enabled, else {"success": False}.
    """
    if not _ledger_enabled():
        return {"success": False, "reason": "ledger_disabled"}

    ledger = get_regime_ledger()
    return ledger.record_transition(
        from_regime=from_regime,
        to_regime=to_regime,
        regime_score=regime_score,
        contributing_factors=contributing_factors,
        duration_in_previous_s=duration_in_previous_s,
        metadata=metadata
    )


def get_current_regime_duration() -> Dict[str, Any]:
    """Get current regime duration (flag-gated).

    Returns {"regime": str, "duration_s": float, "since_timestamp": str}.
    If disabled, returns {"regime": "normal", "duration_s": 0.0, ...}.
    """
    if not _ledger_enabled():
        return {
            "regime": "normal",
            "duration_s": 0.0,
            "since_timestamp": datetime.now(timezone.utc).isoformat()
        }

    ledger = get_regime_ledger()
    return ledger.get_current_regime_duration()
