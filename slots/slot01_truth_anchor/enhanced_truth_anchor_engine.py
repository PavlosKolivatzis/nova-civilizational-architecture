"""Enhanced truth anchoring system with cryptographic integrity."""

import asyncio
import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional, Set, Any
from collections import OrderedDict
import threading


# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================


@dataclass(frozen=True)
class RealityLock:
    """Immutable, cryptographically signed truth anchor point."""

    domain: str
    facts: Tuple[str, ...]
    integrity_hash: str
    signature: str
    timestamp: float
    version: int = 1

    @classmethod
    def create(
        cls, domain: str, facts: Tuple[str, ...], secret_key: bytes
    ) -> "RealityLock":
        """Creates and signs a new RealityLock."""
        timestamp = time.time()

        # Create deterministic hash
        hash_data = json.dumps(
            {
                "domain": domain,
                "facts": sorted(facts),  # Sort for deterministic hashing
                "timestamp": timestamp,
                "version": 1,
            },
            sort_keys=True,
        ).encode()

        integrity_hash = hashlib.sha256(hash_data).hexdigest()

        # Create signature
        signature_data = f"{domain}:{integrity_hash}:{timestamp}".encode()
        signature = hashlib.blake2b(
            signature_data, key=secret_key, digest_size=16
        ).hexdigest()

        return cls(domain, facts, integrity_hash, signature, timestamp)

    def verify(self, secret_key: bytes) -> bool:
        """Verifies the integrity and signature of the lock."""
        try:
            # Recalculate hash
            hash_data = json.dumps(
                {
                    "domain": self.domain,
                    "facts": sorted(self.facts),
                    "timestamp": self.timestamp,
                    "version": self.version,
                },
                sort_keys=True,
            ).encode()

            expected_hash = hashlib.sha256(hash_data).hexdigest()
            if not secrets.compare_digest(self.integrity_hash, expected_hash):
                return False

            # Recalculate signature
            signature_data = f"{self.domain}:{self.integrity_hash}:{self.timestamp}".encode()
            expected_signature = hashlib.blake2b(
                signature_data, key=secret_key, digest_size=16
            ).hexdigest()

            return secrets.compare_digest(self.signature, expected_signature)

        except (TypeError, ValueError):
            return False


@dataclass
class CacheEntry:
    """Cache entry with timestamp for TTL management."""

    result: dict
    timestamp: float
    access_count: int = 0


class LRUCache:
    """Thread-safe LRU cache with TTL support."""

    def __init__(self, max_size: int = 1024, ttl_seconds: float = 60.0):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[dict]:
        """Get item from cache with LRU update."""
        with self._lock:
            entry = self._cache.get(key)
            current_time = time.time()

            if not entry or (current_time - entry.timestamp > self.ttl_seconds):
                if entry:
                    self._cache.pop(key, None)
                self._misses += 1
                return None

            # Update LRU order and access count
            self._cache.move_to_end(key)
            entry.access_count += 1
            self._hits += 1
            return entry.result

    def set(self, key: str, value: dict) -> None:
        """Set item in cache with LRU eviction if needed."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)

            self._cache[key] = CacheEntry(
                result=value, timestamp=time.time(), access_count=1
            )

            # Evict if over capacity
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def clear_expired(self) -> int:
        """Clear expired entries and return count removed."""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if current_time - entry.timestamp > self.ttl_seconds
            ]

            for key in expired_keys:
                self._cache.pop(key, None)

            return len(expired_keys)

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._lock:
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio": self._hits / max(1, self._hits + self._misses),
            }


# ============================================================================
# TRUTH ANCHOR ENGINE
# ============================================================================


class TruthAnchorEngine:
    """High-performance truth anchoring system with cryptographic integrity."""

    def __init__(
        self,
        cache_max: int = 2048,
        cache_ttl: float = 120.0,
        stable_threshold: float = 0.7,
        secret_key: Optional[bytes] = None,
    ):
        self.stable_threshold = stable_threshold
        self._secret_key = secret_key or secrets.token_bytes(32)
        self._cache = LRUCache(cache_max, cache_ttl)
        self._anchors: Dict[str, RealityLock] = {}
        self._anchor_lock = threading.RLock()
        self._truth_indicators: Set[str] = {
            "evidence",
            "verified",
            "documented",
            "confirmed",
            "proof",
            "fact",
            "data shows",
            "research indicates",
        }
        self._distortion_indicators: Set[str] = {
            "allegedly",
            "sources say",
            "reportedly",
            "rumored",
            "unconfirmed",
            "speculation",
            "hearsay",
            "anonymous sources",
        }

        # Initialize with core truth anchor
        self._initialize_core_anchor()

    def _initialize_core_anchor(self) -> None:
        """Initialize the core truth anchor."""
        core_facts = (
            "Truth must be verifiable and evidence-based",
            "Epistemic integrity cannot be compromised",
            "Systems must maintain accountability and transparency",
            "Cultural adaptation should not distort factual reality",
        )
        self.establish_anchor("nova.core", list(core_facts))

    def _score_truth(
        self, content: str, anchor_domain: Optional[str] = None
    ) -> float:
        """Score truthfulness of content with optional anchor verification."""
        if not content:
            return 0.5

        content_lower = content.lower()

        # Count truth indicators
        truth_count = sum(
            1 for indicator in self._truth_indicators if indicator in content_lower
        )

        # Count distortion indicators
        distortion_count = sum(
            1 for indicator in self._distortion_indicators if indicator in content_lower
        )

        # Base score with indicators
        base_score = 0.8
        score = base_score + (truth_count * 0.08) - (distortion_count * 0.12)

        # Apply anchor verification if specified
        if anchor_domain:
            anchor_penalty = self._check_anchor_violation(content_lower, anchor_domain)
            score -= anchor_penalty

        return max(0.0, min(1.0, round(score, 3)))

    def _check_anchor_violation(self, content: str, anchor_domain: str) -> float:
        """Check for violations against a specific anchor."""
        with self._anchor_lock:
            anchor = self._anchors.get(anchor_domain)
            if not anchor:
                return 0.3  # Penalty for missing anchor

            violation_penalty = 0.0
            for fact in anchor.facts:
                fact_lower = fact.lower()
                # Check for direct contradictions
                if ("not " in content or "no " in content) and any(
                    word in content for word in fact_lower.split()[:3]
                ):
                    violation_penalty += 0.4  # Significant penalty per violation

            return min(0.8, violation_penalty)  # Cap total penalty

    async def analyze_content(
        self, content: str, request_id: str, anchor_domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze content for truthfulness with caching."""
        # Check cache first
        if cached_result := self._cache.get(request_id):
            return cached_result

        try:
            # Simulate processing time
            await asyncio.sleep(0.02)

            # Calculate truth score
            truth_score = self._score_truth(content, anchor_domain)
            is_stable = truth_score >= self.stable_threshold

            result = {
                "truth_score": truth_score,
                "anchor_stable": is_stable,
                "critical": not is_stable,
                "request_id": request_id,
                "timestamp": time.time(),
                "anchor_used": anchor_domain if anchor_domain else "none",
            }

            # Cache the result
            self._cache.set(request_id, result)
            return result

        except Exception as e:  # pragma: no cover - defensive
            return {
                "error": f"analysis_failed: {str(e)}",
                "request_id": request_id,
                "timestamp": time.time(),
            }

    def establish_anchor(self, domain: str, facts: List[str]) -> str:
        """Establish a new cryptographic truth anchor."""
        if not domain or not facts:
            raise ValueError("Domain and facts are required")

        facts_tuple = tuple(sorted(set(facts)))  # Deduplicate and sort for consistency

        with self._anchor_lock:
            if domain in self._anchors:
                raise ValueError(f"Anchor domain '{domain}' already exists")

            anchor = RealityLock.create(domain, facts_tuple, self._secret_key)
            self._anchors[domain] = anchor

            return domain

    def verify_anchor(self, domain: str) -> Dict[str, Any]:
        """Verify the integrity of a truth anchor."""
        with self._anchor_lock:
            anchor = self._anchors.get(domain)
            if not anchor:
                return {"exists": False, "verified": False, "domain": domain}

            is_verified = anchor.verify(self._secret_key)
            return {
                "exists": True,
                "verified": is_verified,
                "domain": domain,
                "fact_count": len(anchor.facts),
                "timestamp": anchor.timestamp,
            }

    def list_anchors(self) -> List[Dict[str, Any]]:
        """List all established anchors."""
        with self._anchor_lock:
            return [
                {
                    "domain": domain,
                    "fact_count": len(anchor.facts),
                    "timestamp": anchor.timestamp,
                    "verified": anchor.verify(self._secret_key),
                }
                for domain, anchor in self._anchors.items()
            ]

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache.get_stats()

    def cleanup(self) -> int:
        """Clean up expired cache entries."""
        return self._cache.clear_expired()


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

# Global instance for easy access
truth_anchor = TruthAnchorEngine()


# Example usage
async def example_usage() -> None:  # pragma: no cover - example
    # Establish a new anchor
    truth_anchor.establish_anchor(
        "climate.science",
        [
            "Climate change is supported by overwhelming scientific evidence",
            "Human activities are the primary driver of recent climate change",
            "Global temperatures have been rising consistently",
        ],
    )

    # Analyze content
    result = await truth_anchor.analyze_content(
        "Research shows climate change is real and human-caused",
        "req_123",
        "climate.science",
    )

    print(f"Truth score: {result['truth_score']}")
    print(f"Stable: {result['anchor_stable']}")


if __name__ == "__main__":  # pragma: no cover - example
    asyncio.run(example_usage())
