"""Quarantine system for isolating compromised memory during security incidents."""

import logging
import threading
import time
from contextlib import contextmanager
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .types import ThreatLevel, QuarantineReason
from .policy import QuarantinePolicy

logger = logging.getLogger(__name__)


class QuarantineState(Enum):
    """States of the quarantine system."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    RECOVERY = "recovery"
    FAILED = "failed"




class QuarantineSystem:
    """Advanced quarantine system with read-only continuity and automated recovery."""

    def __init__(self, policy: Optional[QuarantinePolicy] = None):
        """Initialize quarantine system with policy configuration."""
        self.policy = policy or QuarantinePolicy()

        # Quarantine state
        self.state: QuarantineState = QuarantineState.INACTIVE
        self.activation_time: Optional[float] = None
        self.activation_reason: Optional[QuarantineReason] = None
        self.activation_context: Dict[str, Any] = {}

        # Access control
        self._read_only_mode: bool = False
        self._write_blocked: bool = False
        self._access_lock = threading.RLock()

        # Event tracking
        self.quarantine_events: List[Dict[str, Any]] = []
        self.access_attempts_during_quarantine: List[Dict[str, Any]] = []
        self.recovery_attempts: int = 0
        self.auto_recoveries_attempted: int = 0

        # Callbacks for integration
        self.escalation_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.recovery_callbacks: List[Callable[[float, Optional[QuarantineReason], Dict[str, Any]], None]] = []

    def activate_quarantine(self, reason: QuarantineReason,
                          threat_level: ThreatLevel,
                          context: Dict[str, Any]) -> bool:
        """Activate quarantine system with specified reason and context."""
        with self._access_lock:
            if self.state == QuarantineState.ACTIVE:
                logger.warning(f"Quarantine already active, ignoring new activation request: {reason}")
                return False

            # Record activation
            self.state = QuarantineState.ACTIVE
            self.activation_time = time.time()
            self.activation_reason = reason
            self.activation_context = context.copy()

            # Configure access restrictions based on policy
            if self.policy.allow_read_only_access:
                self._read_only_mode = True
                logger.info("Quarantine activated with read-only access permitted")
            else:
                self._read_only_mode = False
                logger.warning("Quarantine activated with all access blocked")

            if self.policy.block_all_writes:
                self._write_blocked = True

            # Log quarantine activation
            self._log_quarantine_event("activation", {
                "reason": reason.value,
                "threat_level": threat_level.value,
                "context": context,
                "read_only_permitted": self._read_only_mode,
                "writes_blocked": self._write_blocked
            })

            # Alert administrators if configured
            if self.policy.alert_administrators:
                self._alert_administrators(reason, threat_level, context)

            # Schedule automatic recovery if enabled
            if (self.policy.auto_recovery_after_s > 0 and
                self.auto_recoveries_attempted < self.policy.max_auto_recoveries):
                self._schedule_auto_recovery()

            logger.critical(f"QUARANTINE ACTIVATED: {reason.value} - {context}")
            return True

    def deactivate_quarantine(self, manual_override: bool = False,
                            context: Optional[Dict[str, Any]] = None) -> bool:
        """Deactivate quarantine system and restore normal operations."""
        with self._access_lock:
            if self.state != QuarantineState.ACTIVE:
                logger.info("Quarantine not active, ignoring deactivation request")
                return False

            # Check if manual approval is required
            if (
                self.policy.require_manual_approval
                and not manual_override
                and self.activation_reason in [QuarantineReason.TAMPER_EVIDENCE, QuarantineReason.CORRUPTION_DETECTED]
            ):
                logger.warning("Manual approval required for quarantine deactivation")
                return False

            # Record deactivation
            activation_time = self.activation_time or time.time()
            duration = time.time() - activation_time
            self.state = QuarantineState.INACTIVE

            # Restore normal access
            self._read_only_mode = False
            self._write_blocked = False

            # Log deactivation
            self._log_quarantine_event("deactivation", {
                "duration_seconds": duration,
                "manual_override": manual_override,
                "context": context or {},
                "access_attempts_during_quarantine": len(self.access_attempts_during_quarantine)
            })

            # Execute recovery callbacks
            for callback in self.recovery_callbacks:
                try:
                    callback(duration, self.activation_reason, self.activation_context)
                except Exception as e:
                    logger.error(f"Recovery callback failed: {e}")

            # Reset state
            self.activation_time = None
            self.activation_reason = None
            self.activation_context = {}
            self.access_attempts_during_quarantine.clear()

            logger.info(f"Quarantine deactivated after {duration:.1f} seconds")
            return True

    @contextmanager
    def read_access(self, source: str, operation: str = "read"):
        """Context manager for read access during quarantine."""
        access_granted = False

        try:
            with self._access_lock:
                if self.state != QuarantineState.ACTIVE:
                    # Normal operation - access granted
                    access_granted = True
                elif self._read_only_mode:
                    # Quarantine active but read-only access permitted
                    access_granted = True
                    self._record_quarantine_access(source, operation, "read", True)
                else:
                    # All access blocked
                    access_granted = False
                    self._record_quarantine_access(source, operation, "read", False)

            if access_granted:
                yield
            else:
                raise PermissionError(f"Read access denied during quarantine: {operation} by {source}")

        except Exception as e:
            if access_granted:
                self._record_quarantine_access(source, operation, "read", False, str(e))
            raise

    @contextmanager
    def write_access(self, source: str, operation: str = "write"):
        """Context manager for write access during quarantine."""
        with self._access_lock:
            if self.state == QuarantineState.ACTIVE or self._write_blocked:
                self._record_quarantine_access(source, operation, "write", False)
                raise PermissionError(f"Write access denied during quarantine: {operation} by {source}")

            # Normal operation - access granted
            yield

    def check_access_permitted(self, operation_type: str) -> bool:
        """Check if a specific operation type is permitted in current state."""
        with self._access_lock:
            if self.state != QuarantineState.ACTIVE:
                return True

            if operation_type.lower() in ["read", "query", "get", "list"]:
                return self._read_only_mode
            else:
                return False  # All write operations blocked during quarantine

    def force_recovery_attempt(self, context: Dict[str, Any]) -> bool:
        """Force a recovery attempt from quarantine state."""
        with self._access_lock:
            if self.state != QuarantineState.ACTIVE:
                logger.info("No quarantine active, recovery not needed")
                return True

            self.state = QuarantineState.RECOVERY
            self.recovery_attempts += 1

            try:
                # Execute recovery procedures
                recovery_success = self._execute_recovery_procedures(context)

                if recovery_success:
                    return self.deactivate_quarantine(manual_override=True, context=context)
                else:
                    self.state = QuarantineState.FAILED
                    self._handle_recovery_failure(context)
                    return False

            except Exception as e:
                logger.error(f"Recovery attempt failed with exception: {e}")
                self.state = QuarantineState.FAILED
                self._handle_recovery_failure({"error": str(e), **context})
                return False

    def _schedule_auto_recovery(self):
        """Schedule automatic recovery attempt."""
        def auto_recovery():
            time.sleep(self.policy.auto_recovery_after_s)

            if self.state == QuarantineState.ACTIVE:
                logger.info("Attempting automatic quarantine recovery")
                self.auto_recoveries_attempted += 1

                if self.activation_time is None:
                    logger.warning("Activation time missing during auto recovery attempt")
                    return

                recovery_context: Dict[str, Any] = {
                    "type": "automatic",
                    "attempt_number": self.auto_recoveries_attempted,
                    "time_in_quarantine": time.time() - self.activation_time
                }

                success = self.force_recovery_attempt(recovery_context)
                if not success:
                    logger.warning(f"Automatic recovery attempt {self.auto_recoveries_attempted} failed")

                    # Escalate if we've reached max attempts
                    if self.auto_recoveries_attempted >= self.policy.max_auto_recoveries:
                        self._escalate_quarantine_failure()

        # Start recovery thread
        recovery_thread = threading.Thread(target=auto_recovery, daemon=True)
        recovery_thread.start()

    def _execute_recovery_procedures(self, context: Dict[str, Any]) -> bool:
        """Execute recovery procedures to exit quarantine safely."""
        logger.info("Executing quarantine recovery procedures")

        # Step 1: Verify system integrity
        integrity_check = context.get("integrity_verified", False)
        if not integrity_check:
            logger.warning("Recovery failed: integrity not verified")
            return False

        # Step 2: Check if threat has been mitigated
        threat_mitigated = context.get("threat_mitigated", False)
        if not threat_mitigated:
            logger.warning("Recovery failed: threat not mitigated")
            return False

        # Step 3: Verify no ongoing suspicious activity
        ongoing_threats = context.get("ongoing_threats", True)
        if ongoing_threats:
            logger.warning("Recovery failed: ongoing threats detected")
            return False

        # Step 4: Validate system health
        system_health = context.get("system_health_score", 0.0)
        if system_health < 0.8:
            logger.warning(f"Recovery failed: system health too low ({system_health})")
            return False

        logger.info("All recovery checks passed")
        return True

    def _handle_recovery_failure(self, context: Dict[str, Any]):
        """Handle failed recovery attempts."""
        logger.error("Quarantine recovery failed")

        # Log failure details
        time_in_quarantine = time.time() - self.activation_time if self.activation_time else 0.0
        self._log_quarantine_event("recovery_failed", {
            "attempt_number": self.recovery_attempts,
            "context": context,
            "time_in_quarantine": time_in_quarantine
        })

        # Check if we should escalate
        if self.recovery_attempts >= self.policy.escalate_after_failures:
            self._escalate_quarantine_failure()

    def _escalate_quarantine_failure(self):
        """Escalate quarantine failure to configured targets."""
        logger.critical("Escalating quarantine failure to administrators")

        time_in_quarantine = time.time() - self.activation_time if self.activation_time else 0.0
        escalation_data: Dict[str, Any] = {
            "reason": self.activation_reason.value if self.activation_reason else "unknown",
            "time_in_quarantine": time_in_quarantine,
            "recovery_attempts": self.recovery_attempts,
            "auto_recovery_attempts": self.auto_recoveries_attempted,
            "context": self.activation_context
        }

        # Execute escalation callbacks
        for callback in self.escalation_callbacks:
            try:
                callback(escalation_data)
            except Exception as e:
                logger.error(f"Escalation callback failed: {e}")

        # Send to configured escalation targets
        for target in self.policy.escalation_targets:
            self._send_escalation_alert(target, escalation_data)

    def _send_escalation_alert(self, target: str, data: Dict[str, Any]):
        """Send escalation alert to specific target."""
        # This would integrate with Nova's cross-slot messaging
        logger.critical(f"ESCALATION ALERT to {target}: Quarantine system requires intervention")
        logger.critical(f"Escalation data: {data}")

        # In real implementation, this would use semantic mirror to alert other slots
        # For now, just log the escalation

    def _alert_administrators(self, reason: QuarantineReason, threat_level: ThreatLevel,
                            context: Dict[str, Any]):
        """Alert system administrators of quarantine activation."""
        alert_message = (f"QUARANTINE ACTIVATED: {reason.value} "
                        f"(Threat Level: {threat_level.value}) - {context}")

        logger.critical(alert_message)

        # In production, this would send alerts via email, Slack, PagerDuty, etc.

    def _record_quarantine_access(
        self,
        source: str,
        operation: str,
        access_type: str,
        granted: bool,
        error: Optional[str] = None,
    ) -> None:
        """Record access attempts during quarantine for analysis."""
        access_record = {
            "timestamp": time.time(),
            "source": source,
            "operation": operation,
            "access_type": access_type,
            "granted": granted,
            "error": error
        }

        self.access_attempts_during_quarantine.append(access_record)

        if granted:
            logger.debug(f"Quarantine access granted: {access_type} {operation} by {source}")
        else:
            logger.warning(f"Quarantine access denied: {access_type} {operation} by {source}")

    def _log_quarantine_event(self, event_type: str, details: Dict[str, Any]):
        """Log quarantine system events for audit and analysis."""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "state": self.state.value,
            "details": details
        }

        self.quarantine_events.append(event)

        # Keep event history manageable
        if len(self.quarantine_events) > 1000:
            self.quarantine_events = self.quarantine_events[-500:]

        logger.info(f"Quarantine event: {event_type} - {details}")

    def register_escalation_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register callback for quarantine escalation events."""
        self.escalation_callbacks.append(callback)

    def register_recovery_callback(
        self,
        callback: Callable[[float, Optional[QuarantineReason], Dict[str, Any]], None],
    ) -> None:
        """Register callback for quarantine recovery events."""
        self.recovery_callbacks.append(callback)

    def get_status(self) -> Dict[str, Any]:
        """Get current quarantine system status."""
        status = {
            "state": self.state.value,
            "read_only_mode": self._read_only_mode,
            "write_blocked": self._write_blocked,
            "total_quarantine_events": len(self.quarantine_events),
            "recovery_attempts": self.recovery_attempts,
            "auto_recovery_attempts": self.auto_recoveries_attempted
        }

        if self.state == QuarantineState.ACTIVE and self.activation_time:
            status_extra: Dict[str, Any] = {
                "activation_reason": self.activation_reason.value if self.activation_reason else None,
                "time_in_quarantine_s": time.time() - self.activation_time,
                "access_attempts_during_quarantine": len(self.access_attempts_during_quarantine)
            }
            status.update(status_extra)

        return status

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive quarantine system metrics."""
        # Calculate quarantine frequency and duration statistics
        activations = [e for e in self.quarantine_events if e["event_type"] == "activation"]
        deactivations = [e for e in self.quarantine_events if e["event_type"] == "deactivation"]

        total_activations = len(activations)
        successful_recoveries = len(deactivations)

        quarantine_reasons: Dict[str, int] = {}
        policy_effectiveness: Dict[str, float] = {}
        metrics: Dict[str, Any] = {
            "total_activations": total_activations,
            "successful_recoveries": successful_recoveries,
            "current_state": self.state.value,
            "recovery_success_rate": successful_recoveries / max(1, total_activations),
            "average_quarantine_duration": 0.0,
            "quarantine_reasons": quarantine_reasons,
            "policy_effectiveness": policy_effectiveness,
        }

        # Calculate average quarantine duration
        if deactivations:
            durations = [d["details"].get("duration_seconds", 0) for d in deactivations]
            metrics["average_quarantine_duration"] = sum(durations) / len(durations)

        # Analyze quarantine reasons
        for activation in activations:
            reason = activation["details"].get("reason", "unknown")
            quarantine_reasons[reason] = quarantine_reasons.get(reason, 0) + 1

        # Policy effectiveness analysis
        if self.policy.auto_recovery_after_s > 0:
            auto_successes = len([d for d in deactivations
                                if not d["details"].get("manual_override", True)])
            policy_effectiveness["auto_recovery_rate"] = auto_successes / max(1, total_activations)

        return metrics
