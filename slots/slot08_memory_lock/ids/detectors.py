"""Intrusion Detection System detectors for memory protection."""

import time
import re
from collections import deque, defaultdict
from typing import List, Dict, Any, Optional, Set, Callable
from pathlib import Path

# Handle imports for both pytest and direct execution
try:
    from ..core.types import IDSEvent, ThreatLevel
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.types import IDSEvent, ThreatLevel


class SurgeDetector:
    """Detects anomalous write surges that may indicate attacks."""

    def __init__(self, window_s: int = 60, threshold: int = 500):
        """Initialize surge detector with time window and threshold."""
        self.window_s = window_s
        self.threshold = threshold
        self.events = deque(maxlen=1000)  # Keep last 1000 events
        self.adaptive_threshold = threshold
        self.baseline_rate = 0.0

    def record_write(self, count: int = 1, timestamp: Optional[float] = None) -> bool:
        """Record write operations and return True if surge detected."""
        if timestamp is None:
            timestamp = time.time()

        self.events.append((timestamp, count))

        # Clean old events outside window
        cutoff_time = timestamp - self.window_s
        while self.events and self.events[0][0] < cutoff_time:
            self.events.popleft()

        # Calculate current rate
        current_rate = sum(count for _, count in self.events)

        # Update adaptive threshold
        self._update_adaptive_threshold(current_rate)

        # Check for surge
        is_surge = current_rate > self.adaptive_threshold

        if is_surge:
            self._log_surge_event(current_rate, timestamp)

        return is_surge

    def _update_adaptive_threshold(self, current_rate: int):
        """Update adaptive threshold based on recent behavior."""
        if len(self.events) > 10:
            # Calculate baseline from recent history
            recent_rates = []
            current_time = time.time()

            # Sample rates from recent windows
            for i in range(5):
                window_start = current_time - (i + 1) * self.window_s
                window_end = current_time - i * self.window_s
                window_rate = sum(count for ts, count in self.events
                                if window_start <= ts < window_end)
                recent_rates.append(window_rate)

            if recent_rates:
                self.baseline_rate = sum(recent_rates) / len(recent_rates)
                # Set adaptive threshold to 3x baseline, but with bounds
                self.adaptive_threshold = max(
                    self.threshold // 2,  # Minimum threshold
                    min(self.threshold * 3, int(self.baseline_rate * 3))  # Adaptive with max
                )

    def _log_surge_event(self, rate: int, timestamp: float):
        """Log surge detection event."""
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Write surge detected: {rate} writes in {self.window_s}s "
                      f"(threshold: {self.adaptive_threshold}, baseline: {self.baseline_rate:.1f})")

    def get_metrics(self) -> Dict[str, Any]:
        """Get surge detector metrics."""
        current_time = time.time()
        recent_rate = sum(count for ts, count in self.events
                         if ts > current_time - self.window_s)

        return {
            "current_rate": recent_rate,
            "adaptive_threshold": self.adaptive_threshold,
            "baseline_rate": self.baseline_rate,
            "window_size_s": self.window_s,
            "events_tracked": len(self.events),
            "is_surging": recent_rate > self.adaptive_threshold
        }


class ForbiddenPathDetector:
    """Detects access to forbidden paths and sensitive locations."""

    def __init__(self, denied_patterns: List[str]):
        """Initialize with list of denied path patterns."""
        self.denied_patterns = denied_patterns
        self.compiled_patterns = [re.compile(pattern) for pattern in denied_patterns]
        self.access_attempts = defaultdict(int)
        self.recent_violations = deque(maxlen=100)

    def check_path(self, path: str, operation: str = "access") -> bool:
        """Check if path access should be denied. Returns True if forbidden."""
        normalized_path = str(Path(path).resolve())

        # Check against all patterns
        for pattern in self.compiled_patterns:
            if pattern.search(normalized_path):
                self._record_violation(normalized_path, operation, pattern.pattern)
                return True

        # Check for suspicious patterns
        if self._is_suspicious_path(normalized_path):
            self._record_violation(normalized_path, operation, "suspicious_pattern")
            return True

        return False

    def _is_suspicious_path(self, path: str) -> bool:
        """Check for suspicious path patterns that may indicate attacks."""
        suspicious_indicators = [
            "../",  # Directory traversal
            "..\\",  # Windows directory traversal
            "%2e%2e",  # URL encoded directory traversal
            "/proc/",  # Linux proc filesystem
            "/dev/",  # Device files
            "shadow",  # Password files
            "passwd",  # Password files
            ".ssh/",  # SSH keys
            ".aws/",  # AWS credentials
            ".git/",  # Git repositories
        ]

        path_lower = path.lower()
        return any(indicator in path_lower for indicator in suspicious_indicators)

    def _record_violation(self, path: str, operation: str, pattern: str):
        """Record a path violation for analysis."""
        violation = {
            "path": path,
            "operation": operation,
            "pattern": pattern,
            "timestamp": time.time()
        }
        self.recent_violations.append(violation)
        self.access_attempts[path] += 1

        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Forbidden path access: {operation} on {path} (matched: {pattern})")

    def get_violations(self, since_timestamp: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get recent violations, optionally filtered by timestamp."""
        if since_timestamp is None:
            return list(self.recent_violations)

        return [v for v in self.recent_violations if v["timestamp"] >= since_timestamp]

    def get_metrics(self) -> Dict[str, Any]:
        """Get forbidden path detector metrics."""
        recent_time = time.time() - 3600  # Last hour
        recent_violations = self.get_violations(recent_time)

        return {
            "total_violations": len(self.recent_violations),
            "recent_violations": len(recent_violations),
            "denied_patterns": len(self.denied_patterns),
            "most_accessed_forbidden": dict(list(self.access_attempts.items())[:10]),
            "violation_rate_per_hour": len(recent_violations)
        }


class TamperDetector:
    """Detects memory tampering and unauthorized modifications."""

    def __init__(self):
        """Initialize tamper detector."""
        self.checksum_mismatches = 0
        self.signature_failures = 0
        self.metadata_anomalies = 0
        self.recent_tamper_events = deque(maxlen=50)

    def check_integrity_violation(self, expected_hash: str, actual_hash: str,
                                 context: Dict[str, Any]) -> bool:
        """Check for integrity violations in content hashes."""
        if expected_hash != actual_hash:
            self.checksum_mismatches += 1
            self._record_tamper_event("checksum_mismatch", {
                "expected": expected_hash,
                "actual": actual_hash,
                **context
            })
            return True
        return False

    def check_signature_violation(self, verification_result: bool,
                                signature: bytes, context: Dict[str, Any]) -> bool:
        """Check for cryptographic signature violations."""
        if not verification_result:
            self.signature_failures += 1
            self._record_tamper_event("signature_failure", {
                "signature": signature.hex() if signature else "missing",
                **context
            })
            return True
        return False

    def check_metadata_anomaly(self, expected_metadata: Dict[str, Any],
                             actual_metadata: Dict[str, Any]) -> bool:
        """Check for metadata anomalies that may indicate tampering."""
        anomalies = []

        # Check file sizes
        if expected_metadata.get("size") != actual_metadata.get("size"):
            anomalies.append("size_mismatch")

        # Check timestamps (allow some tolerance)
        expected_mtime = expected_metadata.get("mtime", 0)
        actual_mtime = actual_metadata.get("mtime", 0)
        if abs(expected_mtime - actual_mtime) > 1:  # 1 second tolerance
            anomalies.append("timestamp_anomaly")

        # Check permissions
        if expected_metadata.get("permissions") != actual_metadata.get("permissions"):
            anomalies.append("permission_change")

        if anomalies:
            self.metadata_anomalies += 1
            self._record_tamper_event("metadata_anomaly", {
                "anomalies": anomalies,
                "expected": expected_metadata,
                "actual": actual_metadata
            })
            return True

        return False

    def _record_tamper_event(self, event_type: str, details: Dict[str, Any]):
        """Record a tamper detection event."""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "details": details
        }
        self.recent_tamper_events.append(event)

        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Tamper detected - {event_type}: {details}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get tamper detector metrics."""
        recent_time = time.time() - 3600  # Last hour
        recent_events = [e for e in self.recent_tamper_events if e["timestamp"] >= recent_time]

        return {
            "total_checksum_mismatches": self.checksum_mismatches,
            "total_signature_failures": self.signature_failures,
            "total_metadata_anomalies": self.metadata_anomalies,
            "recent_tamper_events": len(recent_events),
            "total_tamper_events": len(self.recent_tamper_events),
            "tamper_rate_per_hour": len(recent_events)
        }


class ReplayDetector:
    """Detects replay attacks and duplicate operations."""

    def __init__(self, window_s: int = 300):  # 5 minute window
        """Initialize replay detector with time window."""
        self.window_s = window_s
        self.operation_hashes = deque(maxlen=10000)
        self.replay_attempts = 0

    def check_operation(self, operation_data: Dict[str, Any]) -> bool:
        """Check if operation is a replay. Returns True if replay detected."""
        import hashlib
        import json

        # Create hash of operation data
        operation_json = json.dumps(operation_data, sort_keys=True)
        operation_hash = hashlib.sha256(operation_json.encode()).hexdigest()

        current_time = time.time()

        # Check if we've seen this operation recently
        for timestamp, op_hash in self.operation_hashes:
            if current_time - timestamp > self.window_s:
                continue  # Outside window

            if op_hash == operation_hash:
                self.replay_attempts += 1
                self._record_replay_event(operation_data, operation_hash)
                return True

        # Record this operation
        self.operation_hashes.append((current_time, operation_hash))

        # Clean old operations
        cutoff_time = current_time - self.window_s
        while self.operation_hashes and self.operation_hashes[0][0] < cutoff_time:
            self.operation_hashes.popleft()

        return False

    def _record_replay_event(self, operation_data: Dict[str, Any], operation_hash: str):
        """Record a replay attack event."""
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Replay attack detected: {operation_hash[:16]}... "
                      f"Operation: {operation_data.get('type', 'unknown')}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get replay detector metrics."""
        current_time = time.time()
        active_operations = sum(1 for ts, _ in self.operation_hashes
                              if current_time - ts <= self.window_s)

        return {
            "total_replay_attempts": self.replay_attempts,
            "active_operations": active_operations,
            "window_size_s": self.window_s,
            "operations_tracked": len(self.operation_hashes)
        }


class IDSDetectorSuite:
    """Comprehensive intrusion detection system combining all detectors."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize IDS detector suite with configuration."""
        self.surge_detector = SurgeDetector(
            window_s=config.get("surge_window_s", 60),
            threshold=config.get("surge_threshold", 500)
        )

        self.path_detector = ForbiddenPathDetector(
            denied_patterns=config.get("forbidden_paths", [])
        )

        self.tamper_detector = TamperDetector()
        self.replay_detector = ReplayDetector(
            window_s=config.get("replay_window_s", 300)
        )

        self.threat_events = deque(maxlen=1000)

    def check_write_surge(self, count: int = 1) -> Optional[IDSEvent]:
        """Check for write surge and return event if detected."""
        if self.surge_detector.record_write(count):
            return IDSEvent(
                event_type="write_surge",
                threat_level=ThreatLevel.HIGH,
                source_path="memory_system",
                description=f"Write surge detected: {count} operations",
                ts_ms=int(time.time() * 1000),
                metadata=self.surge_detector.get_metrics()
            )
        return None

    def check_forbidden_access(self, path: str, operation: str = "access") -> Optional[IDSEvent]:
        """Check for forbidden path access and return event if detected."""
        if self.path_detector.check_path(path, operation):
            return IDSEvent(
                event_type="forbidden_access",
                threat_level=ThreatLevel.CRITICAL,
                source_path=path,
                description=f"Forbidden {operation} attempted on {path}",
                ts_ms=int(time.time() * 1000),
                metadata={"operation": operation}
            )
        return None

    def check_integrity_tamper(self, expected_hash: str, actual_hash: str,
                             context: Dict[str, Any]) -> Optional[IDSEvent]:
        """Check for integrity tampering and return event if detected."""
        if self.tamper_detector.check_integrity_violation(expected_hash, actual_hash, context):
            return IDSEvent(
                event_type="integrity_tamper",
                threat_level=ThreatLevel.CRITICAL,
                source_path=context.get("source_path", "unknown"),
                description="Content integrity violation detected",
                ts_ms=int(time.time() * 1000),
                metadata={"expected_hash": expected_hash, "actual_hash": actual_hash, **context}
            )
        return None

    def check_replay_attack(self, operation_data: Dict[str, Any]) -> Optional[IDSEvent]:
        """Check for replay attack and return event if detected."""
        if self.replay_detector.check_operation(operation_data):
            return IDSEvent(
                event_type="replay_attack",
                threat_level=ThreatLevel.HIGH,
                source_path=operation_data.get("source_path", "unknown"),
                description="Replay attack detected",
                ts_ms=int(time.time() * 1000),
                metadata=operation_data
            )
        return None

    def record_event(self, event: IDSEvent):
        """Record an IDS event for analysis."""
        self.threat_events.append(event)

    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics from all detectors."""
        return {
            "surge_detector": self.surge_detector.get_metrics(),
            "path_detector": self.path_detector.get_metrics(),
            "tamper_detector": self.tamper_detector.get_metrics(),
            "replay_detector": self.replay_detector.get_metrics(),
            "total_threat_events": len(self.threat_events),
            "recent_threats": len([e for e in self.threat_events
                                 if time.time() * 1000 - e.ts_ms < 3600000])  # Last hour
        }