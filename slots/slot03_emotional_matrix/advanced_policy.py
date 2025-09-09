"""Advanced Safety Policy for Slot 3 - Emotional Matrix Safety System."""
from __future__ import annotations
import re
import time
import threading
from collections import defaultdict

# Patterns for harmful content detection
_HARM_PATTERNS: tuple = (
    re.compile(r"\b(self[-\s]?harm|kill myself|suicide)\b", re.I),
    re.compile(r"\b(hate\s+speech|genocide|ethnic cleansing)\b", re.I),
)

_DAMPENING_PHRASES: tuple = (
    re.compile(r"\bjust\s+kidding\b", re.I),
    re.compile(r"\bonly\s+a\s+joke\b", re.I),
)

def _ensure_ellipsis(s: str) -> str:
    """Ensure previews end with an ellipsis."""
    return s if s.endswith("...") else s + "..."


class AdvancedSafetyPolicy:
    """
    Harmful/manipulation hints + simple token-bucket rate limiting by source.
    """

    def __init__(self, rate_per_min: int = 600):
        self._allow = max(1, int(rate_per_min))
        self._lock = threading.RLock()
        self._buckets: dict = defaultdict(lambda: (time.time(), float(self._allow)))

    def rate_limit_ok(self, source: str) -> bool:
        """Check if rate limiting allows this request."""
        with self._lock:
            ts, tokens = self._buckets[source]
            now = time.time()
            refill = (now - ts) * (self._allow / 60.0)
            tokens = min(self._allow, tokens + refill)
            if tokens < 1.0:
                self._buckets[source] = (now, tokens)
                return False
            self._buckets[source] = (now, tokens - 1.0)
            return True

    def detect_harmful(self, text: str) -> list[str]:
        """Detect harmful content patterns."""
        return [p.pattern for p in _HARM_PATTERNS if p.search(text or "")]

    def detect_manipulation(self, text: str) -> list[str]:
        """Detect manipulation patterns."""
        return [p.pattern for p in _DAMPENING_PHRASES if p.search(text or "")]

    def validate(self, analysis_result: dict, content: str = "", user_id: str = None) -> dict:
        """Basic validation for compatibility."""
        return {
            "is_safe": True,
            "violations": [],
            "filtered_content": content,
            "policy_actions": [],
            "rate_limited": False
        }

    def get_policy_stats(self) -> dict:
        """Get policy statistics."""
        return {
            "total_checks": 0,
            "violations_detected": 0,
            "rate_limit_hits": 0,
            "content_filtered": 0,
            "violation_rate": 0.0,
            "safety_effectiveness": 1.0
        }

    def get_recent_violations(self, limit: int = 20) -> list:
        """Get recent violations."""
        return []