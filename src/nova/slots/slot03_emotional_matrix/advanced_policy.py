"""Advanced Safety Policy for Slot 3 - Emotional Matrix Safety System."""
from __future__ import annotations

import re
import time
import threading
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional

# Patterns for harmful content detection
_HARM_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(self[-\s]?harm|kill myself|suicide)\b", re.I),
    re.compile(r"\b(hate\s+speech|genocide|ethnic cleansing)\b", re.I),
    re.compile(r"\b(hate all|kill everyone|want to kill|destroy them all)\b", re.I),
    re.compile(r"\b(should die|disappear forever|attack and destroy)\b", re.I),
)

_DAMPENING_PHRASES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bjust\s+kidding\b", re.I),
    re.compile(r"\bonly\s+a\s+joke\b", re.I),
)


def _ensure_ellipsis(s: str) -> str:
    """Ensure previews end with an ellipsis."""
    return s if s.endswith("...") else s + "..."


class SafetyViolation:
    """Represents a safety policy violation."""

    def __init__(
        self,
        violation_type: str,
        content: str,
        confidence: float,
        timestamp: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.violation_type = violation_type
        self.content = content
        self.confidence = confidence
        self.timestamp = timestamp
        self.metadata: Dict[str, Any] = metadata or {}


class RateLimiter:
    """Simple rate limiter for content analysis."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: DefaultDict[str, List[float]] = defaultdict(list)

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed within rate limits."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        request_times = self.requests[identifier]
        self.requests[identifier] = [t for t in request_times if t > window_start]

        # Check if within limits
        if len(self.requests[identifier]) >= self.max_requests:
            return False

        # Add current request
        self.requests[identifier].append(now)
        return True


class AdvancedSafetyPolicy:
    """
    Harmful/manipulation hints + simple token-bucket rate limiting by source.
    """

    def __init__(
        self,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60,
        rate_per_min: Optional[int] = None,
        enable_content_filtering: bool = True,
    ) -> None:
        # Support both old and new parameter names for compatibility
        if rate_per_min is not None:
            self._allow = max(1, int(rate_per_min))
        else:
            # Convert from requests per window to requests per minute
            self._allow = max(1, int(rate_limit_requests * 60 / rate_limit_window))
        self._lock = threading.RLock()
        self._buckets: DefaultDict[str, tuple[float, float]] = defaultdict(
            lambda: (time.time(), float(self._allow))
        )
        self.enable_content_filtering: bool = enable_content_filtering
        self.stats: Dict[str, int] = {
            "total_checks": 0,
            "violations_detected": 0,
            "rate_limit_hits": 0,
            "content_filtered": 0
        }
        self._recent_violations: List[SafetyViolation] = []  # Track recent violations
        self._pattern_names: Dict[str, str] = {}  # Track custom pattern names

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

    def detect_harmful(self, text: str) -> List[str]:
        """Detect harmful content patterns."""
        return [p.pattern for p in _HARM_PATTERNS if p.search(text or "")]

    def detect_manipulation(self, text: str) -> List[str]:
        """Detect manipulation patterns."""
        return [p.pattern for p in _DAMPENING_PHRASES if p.search(text or "")]

    def validate(
        self,
        analysis_result: Dict[str, Any],
        content: str = "",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Advanced validation with comprehensive safety checks."""
        self.stats["total_checks"] += 1

        validation_result: Dict[str, Any] = {
            "is_safe": True,
            "violations": [],
            "filtered_content": content,
            "policy_actions": [],
            "rate_limited": False
        }

        # Check rate limiting first
        if user_id is not None and not self.rate_limit_ok(user_id):
            validation_result["rate_limited"] = True
            validation_result["is_safe"] = False
            self.stats["rate_limit_hits"] += 1
            return validation_result

        # Basic safety checks (score bounds, tone validation, etc.)
        basic_result = self._basic_safety_check(analysis_result)
        if not basic_result["is_safe"]:
            validation_result["is_safe"] = False
            validation_result["violations"].extend(basic_result["violations"])
            validation_result["policy_actions"].extend(basic_result["policy_actions"])

        # Content filtering if enabled
        if self.enable_content_filtering and content:
            content_violations = self._check_content_safety(content)
            if content_violations:
                validation_result["is_safe"] = False
                validation_result["violations"].extend(content_violations)
                validation_result["filtered_content"] = "[FILTERED]"  # Replace harmful content
                self.stats["content_filtered"] += 1

        # Update violation statistics and tracking
        if validation_result["violations"]:
            self.stats["violations_detected"] += 1
            # Track recent violations
            for violation in validation_result["violations"]:
                violation_record = SafetyViolation(
                    violation_type=violation["type"],
                    content=content[:100],  # Store first 100 chars
                    confidence=violation["confidence"],
                    timestamp=time.time(),
                    metadata={"user_id": user_id}
                )
                self._recent_violations.append(violation_record)
                # Keep only last 100 violations
                if len(self._recent_violations) > 100:
                    self._recent_violations.pop(0)

        return validation_result

    def _basic_safety_check(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Basic safety validation."""
        from nova.slots.slot03_emotional_matrix.safety_policy import validate_metrics

        result: Dict[str, Any] = {
            "is_safe": True,
            "violations": [],
            "policy_actions": []
        }

        errors = validate_metrics(analysis_result)
        if errors:
            result["is_safe"] = False
            for error in errors:
                result["violations"].append({
                    "type": error,
                    "confidence": 1.0,
                    "details": f"Validation error: {error}"
                })

        return result

    def _check_content_safety(self, content: str) -> List[Dict[str, Any]]:
        """Check content for safety violations."""
        violations: List[Dict[str, Any]] = []

        # Check harmful patterns (including dynamically added ones)
        harmful_patterns = self.detect_harmful(content)
        for pattern in harmful_patterns:
            # Check if this is a custom pattern by looking for pattern info
            pattern_name = self._pattern_names.get(pattern)
            if pattern_name:
                violation_type = f"harmful_content_{pattern_name}"
            else:
                violation_type = "harmful_content"

            violations.append({
                "type": violation_type,
                "confidence": 0.9,
                "details": f"Harmful pattern detected: {pattern}"
            })

        # Check for blocked domains/sources
        import re
        domain_pattern = re.compile(r'https?://([^/\s]+)', re.I)
        domains = domain_pattern.findall(content)
        blocked_domains = ['malicious-site.com', 'badsite.org', 'dangerous.net']  # Example blocked domains

        for domain in domains:
            if domain in blocked_domains:
                violations.append({
                    "type": "blocked_source",
                    "confidence": 1.0,
                    "details": f"Blocked domain detected: {domain}"
                })

        return violations

    def get_policy_stats(self) -> Dict[str, float | int]:
        """Get policy statistics."""
        total_checks = self.stats["total_checks"]
        violations = self.stats["violations_detected"]
        violation_rate = violations / max(1, total_checks)
        return {
            "total_checks": self.stats["total_checks"],
            "violations_detected": self.stats["violations_detected"],
            "rate_limit_hits": self.stats["rate_limit_hits"],
            "content_filtered": self.stats["content_filtered"],
            "violation_rate": violation_rate,
            "safety_effectiveness": 1.0 - violation_rate,
        }

    def get_recent_violations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent violations."""
        violations = self._recent_violations[-limit:]
        # Convert SafetyViolation objects to dict format expected by tests
        return [
            {
                'type': v.violation_type,
                'content_preview': _ensure_ellipsis(v.content[:100]),
                'confidence': v.confidence,
                'timestamp': v.timestamp,
                'metadata': v.metadata
            }
            for v in violations
        ]

    def update_harmful_patterns(self, new_patterns: List[Dict[str, Any]]) -> None:
        """Update harmful content patterns."""
        global _HARM_PATTERNS

        # Add new patterns to existing ones
        new_compiled_patterns: List[re.Pattern[str]] = []
        for pattern_info in new_patterns:
            if isinstance(pattern_info, dict) and 'patterns' in pattern_info:
                pattern_name = pattern_info.get('name', 'unnamed')
                for pattern_str in pattern_info['patterns']:
                    try:
                        compiled_pattern = re.compile(pattern_str, re.I)
                        new_compiled_patterns.append(compiled_pattern)
                        # Track the pattern name for violation types
                        self._pattern_names[pattern_str] = pattern_name
                    except re.error:
                        continue  # Skip invalid patterns

        # Update global patterns (in a real system, this might be handled differently)
        _HARM_PATTERNS = _HARM_PATTERNS + tuple(new_compiled_patterns)
