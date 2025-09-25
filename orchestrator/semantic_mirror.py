"""
Orchestrator Semantic Mirror - Flow Fabric Phase 3

Provides read-only context sharing between slots with bounded access control.
Enables contextual intelligence while preserving slot autonomy.

Key Principles:
- Read-only: Consumers can query but never mutate
- Allow-listed: Explicit permissions for who can read what
- Bounded: TTL expiration, memory limits, rate limiting
- Thread-safe: Concurrent access from multiple slots
"""
from __future__ import annotations
import time
import threading
import os
from collections import defaultdict, deque
from typing import Dict, Any, Optional, Set, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ContextScope(str, Enum):
    """Defines the scope of context data visibility."""
    PRIVATE = "private"      # Only originating slot can read
    INTERNAL = "internal"    # Only other slots can read (not external)
    PUBLIC = "public"        # Available to all consumers


@dataclass
class ContextEntry:
    """A single context entry in the semantic mirror."""
    key: str
    value: Any
    scope: ContextScope
    published_by: str
    timestamp: float
    ttl_seconds: float = 300.0  # 5 minutes default TTL
    access_count: int = 0
    last_accessed: float = 0.0
    
    def is_expired(self, current_time: float) -> bool:
        """Check if this context entry has expired."""
        return (current_time - self.timestamp) > self.ttl_seconds
    
    def is_accessible_by(self, requesting_slot: str, access_rules: Dict[str, Set[str]]) -> bool:
        """Check if requesting slot can access this context entry."""
        # Self-access always allowed (publisher can read back)
        if requesting_slot == self.published_by:
            return True
        
        # Private means strictly publisher-only
        if self.scope == ContextScope.PRIVATE:
            return False
        
        # Public means everyone can read
        if self.scope == ContextScope.PUBLIC:
            return True
        
        # INTERNAL → require explicit allow-list (deny-by-default)
        allowed_consumers = access_rules.get(self.key)
        if not allowed_consumers:  # No ACL entry = deny access
            return False
        return requesting_slot in allowed_consumers


class SemanticMirror:
    """
    Thread-safe read-only context broker for inter-slot awareness.
    
    Provides bounded context sharing with access control, TTL expiration,
    and observability for contextual decision making across slots.
    """
    
    def __init__(self, max_entries: int = 1000, cleanup_interval_seconds: float = 60.0):
        self._contexts: Dict[str, ContextEntry] = {}
        self._access_rules: Dict[str, Set[str]] = {}
        self._access_history = deque(maxlen=10000)  # Bounded access log
        self._metrics = defaultdict(int)
        self._lock = threading.RLock()
        
        # Configuration
        self.max_entries = max_entries
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.last_cleanup = time.time()
        
        # Rate limiting per slot
        self._rate_limits: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.max_queries_per_minute = 1000
        
        logger.info(f"SemanticMirror initialized (max_entries={max_entries})")
    
    def configure_access_rules(self, rules: Dict[str, List[str]]) -> None:
        """Configure which slots can access which context keys.
        
        Args:
            rules: Dict mapping context keys to list of allowed consumer slots
        """
        with self._lock:
            self._access_rules = {key: set(consumers) for key, consumers in rules.items()}
            logger.info(f"Configured access rules for {len(rules)} context keys")
    
    def add_access_rules(self, rules: Dict[str, List[str]]) -> None:
        """Add/merge access rules without replacing existing ones.
        
        Args:
            rules: Dict mapping context keys to list of additional allowed consumer slots
        """
        with self._lock:
            for key, readers in rules.items():
                current = self._access_rules.get(key, set())
                self._access_rules[key] = current | set(readers)
            logger.info(f"Added access rules for {len(rules)} context keys")
    
    def publish_context(self, key: str, value: Any, publisher_slot: str, 
                       scope: ContextScope = ContextScope.INTERNAL,
                       ttl_seconds: float = 300.0) -> bool:
        """Publish context data to the semantic mirror.
        
        Args:
            key: Unique context identifier (e.g., "slot07.breaker_state")
            value: Context data (must be JSON serializable)
            publisher_slot: Slot identifier publishing this context
            scope: Visibility scope for this context
            ttl_seconds: Time-to-live for this context entry
            
        Returns:
            True if published successfully, False otherwise
        """
        current_time = time.time()
        
        with self._lock:
            # Cleanup if needed
            if current_time - self.last_cleanup > self.cleanup_interval_seconds:
                self._cleanup_expired_entries(current_time)
            
            # Check memory bounds
            if len(self._contexts) >= self.max_entries:
                logger.warning(f"SemanticMirror at capacity ({self.max_entries}), rejecting publication")
                self._metrics["publications_rejected_capacity"] += 1
                return False
            
            # Validate key format
            if not self._is_valid_context_key(key):
                logger.warning(f"Invalid context key format: {key}")
                self._metrics["publications_rejected_invalid_key"] += 1
                return False
            
            # Create context entry
            entry = ContextEntry(
                key=key,
                value=value,
                scope=scope,
                published_by=publisher_slot,
                timestamp=current_time,
                ttl_seconds=ttl_seconds
            )
            
            self._contexts[key] = entry
            self._metrics["publications_total"] += 1
            self._metrics[f"publications_by_{publisher_slot}"] += 1
            
            logger.debug(f"Published context: {key} by {publisher_slot} (scope={scope.value})")
            return True
    
    def get_context(self, key: str, requesting_slot: str) -> Optional[Any]:
        """Retrieve context data from the semantic mirror.
        
        Args:
            key: Context identifier to retrieve
            requesting_slot: Slot identifier making the request
            
        Returns:
            Context value if accessible, None otherwise
        """
        current_time = time.time()
        
        with self._lock:
            # Rate limiting check
            if not self._check_rate_limit(requesting_slot, current_time):
                self._metrics["queries_rate_limited"] += 1
                return None
            
            # Find context entry
            entry = self._contexts.get(key)
            if not entry:
                self._metrics["queries_not_found"] += 1
                return None
            
            # Check expiration
            if entry.is_expired(current_time):
                logger.debug(f"Context expired: {key}")
                del self._contexts[key]
                self._metrics["queries_expired"] += 1
                return None
            
            # Check access permissions
            if not entry.is_accessible_by(requesting_slot, self._access_rules):
                logger.warning(f"Access denied: {requesting_slot} -> {key}")
                self._metrics["queries_access_denied"] += 1
                return None
            
            # Update access tracking
            entry.access_count += 1
            entry.last_accessed = current_time
            
            # Log access for audit
            self._access_history.append({
                "timestamp": current_time,
                "key": key,
                "requesting_slot": requesting_slot,
                "publisher_slot": entry.published_by,
                "value_type": type(entry.value).__name__
            })
            
            self._metrics["queries_successful"] += 1
            self._metrics[f"queries_by_{requesting_slot}"] += 1
            
            return entry.value
    
    def query_context_keys(self, prefix: str, requesting_slot: str) -> List[str]:
        """List available context keys with given prefix.
        
        Args:
            prefix: Key prefix to filter by (e.g., "slot07.")
            requesting_slot: Slot making the request
            
        Returns:
            List of accessible context keys matching prefix
        """
        current_time = time.time()
        accessible_keys = []
        
        with self._lock:
            for key, entry in self._contexts.items():
                if key.startswith(prefix) and not entry.is_expired(current_time):
                    if entry.is_accessible_by(requesting_slot, self._access_rules):
                        accessible_keys.append(key)
        
        return accessible_keys
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get semantic mirror metrics for monitoring."""
        current_time = time.time()
        
        with self._lock:
            active_contexts = sum(1 for entry in self._contexts.values() 
                                if not entry.is_expired(current_time))
            
            return {
                "active_contexts": active_contexts,
                "total_contexts": len(self._contexts),
                "access_rules_configured": len(self._access_rules),
                "access_history_size": len(self._access_history),
                "last_cleanup": self.last_cleanup,
                **dict(self._metrics)
            }
    
    def get_context_summary(self, requesting_slot: str) -> Dict[str, Any]:
        """Get summary of accessible contexts for debugging."""
        current_time = time.time()
        summary = {}
        
        with self._lock:
            for key, entry in self._contexts.items():
                if not entry.is_expired(current_time):
                    if entry.is_accessible_by(requesting_slot, self._access_rules):
                        summary[key] = {
                            "published_by": entry.published_by,
                            "scope": entry.scope.value,
                            "age_seconds": current_time - entry.timestamp,
                            "access_count": entry.access_count,
                            "value_type": type(entry.value).__name__
                        }
        
        return summary
    
    def _is_valid_context_key(self, key: str) -> bool:
        """Validate context key format (slot_name.context_type)."""
        parts = key.split('.')
        return len(parts) >= 2 and all(part.isidentifier() or part.replace('_', '').isalnum() 
                                      for part in parts)
    
    def _check_rate_limit(self, requesting_slot: str, current_time: float) -> bool:
        """Check if requesting slot is within rate limits."""
        slot_queries = self._rate_limits[requesting_slot]
        
        # Remove queries older than 1 minute
        cutoff_time = current_time - 60.0
        while slot_queries and slot_queries[0] < cutoff_time:
            slot_queries.popleft()
        
        # Check if under limit
        if len(slot_queries) >= self.max_queries_per_minute:
            return False
        
        # Record this query
        slot_queries.append(current_time)
        return True
    
    def _cleanup_expired_entries(self, current_time: float) -> None:
        """Remove expired context entries and emit unlearn pulses (observable-only)."""
        expired_entries = [
            (key, entry) for key, entry in self._contexts.items()
            if self._entry_is_expired(entry, current_time)
        ]

        delivered_total = 0
        for key, entry in expired_entries:
            delivered_total += self._emit_unlearn_pulse(key, entry)
            del self._contexts[key]

        # Safe counter updates
        self._metrics.setdefault("entries_expired", 0)
        self._metrics["entries_expired"] += len(expired_entries)

        self._metrics.setdefault("unlearn_pulses_sent", 0)
        self._metrics["unlearn_pulses_sent"] += delivered_total

        self.last_cleanup = current_time

        if expired_entries:
            logger.debug(f"Cleaned up {len(expired_entries)} expired context entries")
            logger.info(f"Emitted {delivered_total} unlearn pulses")

    # ---------- expiry helper (robust to malformed entries) ----------
    def _entry_is_expired(self, entry: ContextEntry, current_time: float) -> bool:
        """Return True if entry is expired, handling missing attrs and bad types."""
        try:
            if hasattr(entry, "is_expired") and callable(entry.is_expired):
                return bool(entry.is_expired(current_time))
            ts = float(getattr(entry, "timestamp", 0.0))
            ttl = float(getattr(entry, "ttl_seconds", 0.0))
            return (current_time - ts) > ttl
        except Exception:
            # Defensive: treat malformed entries as expired so they don't linger forever
            return True

    # ---------- Observable Pulse helpers ----------
    def _should_emit_unlearn_pulse(self, entry: ContextEntry) -> bool:
        """Should we emit an unlearn pulse for this expiring context?"""
        return (
            getattr(entry, "access_count", 0) > 1          # actually used
            and getattr(entry, "scope", None) in [ContextScope.INTERNAL, ContextScope.PUBLIC]
            and float(getattr(entry, "ttl_seconds", 0.0)) >= 60.0  # not transient
        )

    def _emit_unlearn_pulse(self, key: str, entry: ContextEntry) -> int:
        """Log a reciprocal unlearn pulse (prototype; no weight decay).
        Returns number of destinations actually notified (after immunity filter)."""
        if not self._should_emit_unlearn_pulse(entry):
            return 0

        source_slots = self._extract_source_slots(key, entry)  # already immunity-filtered
        delivered = len(source_slots)
        if delivered == 0:
            return 0

        # Gate noisy logs with env flag (default ON for prototype)
        if os.getenv("NOVA_UNLEARN_PULSE_LOG", "1") == "1":
            try:
                age = time.time() - float(getattr(entry, "timestamp", time.time()))
            except Exception:
                age = 0.0
            logger.info(
                f"UNLEARN_PULSE key={key} → {source_slots} "
                f"(ttl={getattr(entry,'ttl_seconds',None)}s, "
                f"accessed={getattr(entry,'access_count',0)}x, age={age:.1f}s)"
            )

        # Phase 2: emit UNLEARN_PULSE@1 contract to source slots
        # Phase 3: implement exponential weight decay in receivers

        # Per-destination pulse counters
        for s in source_slots:
            k = f"unlearn_pulse_to_{s}"
            self._metrics.setdefault(k, 0)
            self._metrics[k] += 1
        self._metrics.setdefault("unlearn_pulse_total_contexts", 0)
        self._metrics["unlearn_pulse_total_contexts"] += 1
        return delivered

    def _extract_source_slots(self, key: str, entry: ContextEntry) -> List[str]:
        """Infer slots to notify; core truth/production are immune."""
        slots: List[str] = []
        if key.startswith("slot") and "." in key:
            slots.append(key.split(".")[0])  # e.g., "slot03"
        pub = getattr(entry, "published_by", None)
        if pub and pub not in slots:
            slots.append(pub)
        return [s for s in slots if self._slot_should_receive_unlearn_pulse(s)]

    def _slot_should_receive_unlearn_pulse(self, slot: str) -> bool:
        """Protect foundational engines from unlearning pulses."""
        immune = {"slot01", "slot07", "slot1_truth_anchor", "slot7_production_controls"}
        return slot not in immune


# Global semantic mirror instance
_semantic_mirror: Optional[SemanticMirror] = None


def get_semantic_mirror() -> SemanticMirror:
    """Get global semantic mirror instance."""
    global _semantic_mirror
    if _semantic_mirror is None:
        _semantic_mirror = SemanticMirror()
        _configure_default_access_rules(_semantic_mirror)
    return _semantic_mirror


def _configure_default_access_rules(mirror: SemanticMirror) -> None:
    """Configure default access rules for slot context sharing."""
    default_rules = {
        # Slot 4 TRI contexts accessible by consuming slots
        "slot04.coherence": ["slot02_deltathresh", "slot03_emotional_matrix", "slot05_constellation", "slot07_production_controls", "slot08_memory_lock", "slot10_civilizational_deployment"],
        "slot04.phase_coherence": ["slot02_deltathresh", "slot03_emotional_matrix", "slot05_constellation", "slot07_production_controls", "slot08_memory_lock", "slot10_civilizational_deployment"],
        "slot04.phase_jitter": ["slot02_deltathresh", "slot05_constellation", "slot07_production_controls", "slot10_civilizational_deployment"],

        # Slot 3 LightClock phase lock accessible by deployment gates
        "slot03.phase_lock": ["slot02_deltathresh", "slot07_production_controls", "slot10_civilizational_deployment"],

        # Slot 7 contexts accessible by other slots
        "slot07.breaker_state": ["slot06_cultural_synthesis", "slot03_emotional_matrix"],
        "slot07.pressure_level": ["slot06_cultural_synthesis", "slot03_emotional_matrix"],
        "slot07.resource_status": ["slot06_cultural_synthesis"],
        "slot07.public_metrics": ["slot06_cultural_synthesis"],  # For test compatibility
        
        # Slot 6 contexts accessible by other slots  
        "slot06.cultural_profile": ["slot03_emotional_matrix", "slot07_production_controls"],
        "slot06.adaptation_rate": ["slot03_emotional_matrix", "slot07_production_controls"],
        "slot06.synthesis_complexity": ["slot07_production_controls"],
        "slot06.synthesis_results": ["slot07_production_controls"],  # For test compatibility
        
        # Slot 3 contexts (more restricted)
        "slot03.emotional_state": ["slot06_cultural_synthesis"],
        "slot03.confidence_level": ["slot06_cultural_synthesis", "slot07_production_controls"]
    }
    
    mirror.configure_access_rules(default_rules)


def reset_semantic_mirror() -> None:
    """Reset global semantic mirror (for testing)."""
    global _semantic_mirror
    _semantic_mirror = None


# Convenience functions for common patterns
def publish(key: str, value: Any, publisher: str, ttl: float = 300.0) -> bool:
    """Publish context to semantic mirror."""
    return get_semantic_mirror().publish_context(key, value, publisher, ttl_seconds=ttl)


def query(key: str, requester: str) -> Optional[Any]:
    """Query context from semantic mirror."""
    return get_semantic_mirror().get_context(key, requester)


def list_available(prefix: str, requester: str) -> List[str]:
    """List available context keys with prefix."""
    return get_semantic_mirror().query_context_keys(prefix, requester)