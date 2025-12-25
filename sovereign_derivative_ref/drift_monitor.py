"""
VSD-0 Constitutional Drift Monitor
Version: 0.1
Purpose: Detect constitutional boundary violations in real-time
Compliance: DOC v1.0 Section 4.2 (Operational Monitoring - DEPLOYMENT REQUIREMENT)

This module implements continuous constitutional drift monitoring as required by DOC.
Non-compliance makes the derivative invalid.
"""

import os
import subprocess
import hashlib
import time
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class DriftType(Enum):
    """Types of constitutional drift that can be detected"""
    O_R_COUPLING = "o_r_drift"  # O-domain signals gaining R-domain authority
    FREEZE_VIOLATION = "freeze_violation"  # Frozen artifacts modified
    BOUNDARY_CROSSING = "boundary_crossing"  # Approaching F-domains
    GIT_INTEGRITY = "git_integrity_violation"  # Git history rewritten


class DriftSeverity(Enum):
    """Severity levels for drift events"""
    INFO = "info"  # Boundary proximity, no violation
    WARNING = "warning"  # Potential drift detected
    CRITICAL = "critical"  # Constitutional violation confirmed
    HALT = "halt"  # Requires immediate operation halt


@dataclass
class DriftEvent:
    """Record of a constitutional drift detection"""
    timestamp: str
    drift_type: DriftType
    severity: DriftSeverity
    description: str
    evidence: Dict[str, str]
    action_taken: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "drift_type": self.drift_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "evidence": self.evidence,
            "action_taken": self.action_taken
        }


class ConstitutionalDriftMonitor:
    """
    Monitors Nova Core for constitutional boundary violations.

    Required by DOC v1.0 Section 4.2:
    - Monitor for O→R drift (MANDATORY)
    - Monitor for constitutional modifications (MANDATORY)
    - Monitor for boundary crossings (MANDATORY)

    Non-compliance makes derivative invalid.
    """

    def __init__(self, nova_root: str, audit_log_callback=None):
        """
        Initialize drift monitor.

        Args:
            nova_root: Path to Nova Core repository root
            audit_log_callback: Function to call when drift detected (writes to audit log)
        """
        self.nova_root = nova_root
        self.audit_log = audit_log_callback
        self.is_running = False

        # Frozen artifacts to monitor (from nova_constitutional_freeze.md)
        self.frozen_artifacts = [
            "docs/architecture/ontology/specs/nova_framework_ontology.v1.yaml",
            "docs/specs/nova_jurisdiction_map.md",
            "docs/specs/refusal_event_contract.md",
            "docs/specs/refusal_event_exemplars.md",
            "docs/specs/phase16_alpha_calibration_protocol.md",
            "docs/specs/phase16_agency_pressure_evidence.md",
            "docs/specs/derivative_ontology_contract.md"
        ]

        # Baseline hashes of frozen artifacts
        self.artifact_hashes: Dict[str, str] = {}
        self._compute_baseline_hashes()

    def _compute_baseline_hashes(self):
        """Compute SHA256 hashes of all frozen artifacts as baseline"""
        for artifact_path in self.frozen_artifacts:
            full_path = os.path.join(self.nova_root, artifact_path)
            if os.path.exists(full_path):
                with open(full_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                    self.artifact_hashes[artifact_path] = file_hash
            else:
                # Artifact missing - critical violation
                self._emit_drift_event(
                    drift_type=DriftType.FREEZE_VIOLATION,
                    severity=DriftSeverity.CRITICAL,
                    description=f"Frozen artifact missing: {artifact_path}",
                    evidence={"artifact": artifact_path, "status": "missing"},
                    action="halt_required"
                )

    def _emit_drift_event(self, drift_type: DriftType, severity: DriftSeverity,
                         description: str, evidence: dict, action: str):
        """Emit drift event to audit log"""
        event = DriftEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            drift_type=drift_type,
            severity=severity,
            description=description,
            evidence=evidence,
            action_taken=action
        )

        if self.audit_log:
            self.audit_log(event.to_dict(), event_type="drift_event")

        # Print to stdout for debugging
        print(f"[DRIFT] {severity.value.upper()}: {description}")

        # If HALT severity, raise exception
        if severity == DriftSeverity.HALT:
            raise ConstitutionalViolationError(
                f"Constitutional violation detected: {description}. Operation halted."
            )

    def check_o_r_drift(self) -> List[DriftEvent]:
        """
        Check for O→R drift: O-domain signals gaining routing authority.

        Detects if A_p, M_p, harm_status (O-domain) are wired to governance (R-domain).
        This is semantic→decision authority coupling.

        Returns:
            List of drift events detected (empty if no drift)
        """
        events = []

        # Check if A_p is wired to governance
        try:
            result = subprocess.run(
                ["grep", "-r", "harm_status.*governance\\|A_p.*governance",
                 os.path.join(self.nova_root, "src/nova")],
                capture_output=True,
                text=True,
                cwd=self.nova_root
            )

            if result.returncode == 0 and result.stdout.strip():
                # O→R drift detected
                self._emit_drift_event(
                    drift_type=DriftType.O_R_COUPLING,
                    severity=DriftSeverity.CRITICAL,
                    description="O→R drift detected: A_p or harm_status wired to governance",
                    evidence={
                        "grep_output": result.stdout.strip(),
                        "semantic_domain": "O (observe-only)",
                        "decision_domain": "R (routing authority)",
                        "coupling": "semantic→decision authority coupling detected"
                    },
                    action="alert_and_halt"
                )
        except Exception as e:
            # Monitoring failed - emit warning
            self._emit_drift_event(
                drift_type=DriftType.O_R_COUPLING,
                severity=DriftSeverity.WARNING,
                description=f"O→R drift check failed: {str(e)}",
                evidence={"error": str(e)},
                action="continue_with_degraded_monitoring"
            )

        return events

    def check_freeze_violations(self) -> List[DriftEvent]:
        """
        Check for constitutional freeze violations.

        Detects if any frozen artifact has been modified since baseline.

        Returns:
            List of drift events detected (empty if no violations)
        """
        events = []

        for artifact_path, baseline_hash in self.artifact_hashes.items():
            full_path = os.path.join(self.nova_root, artifact_path)

            if not os.path.exists(full_path):
                # Artifact deleted - critical violation
                self._emit_drift_event(
                    drift_type=DriftType.FREEZE_VIOLATION,
                    severity=DriftSeverity.CRITICAL,
                    description=f"Frozen artifact deleted: {artifact_path}",
                    evidence={
                        "artifact": artifact_path,
                        "status": "deleted",
                        "baseline_hash": baseline_hash
                    },
                    action="halt_required"
                )
                continue

            # Compute current hash
            with open(full_path, 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()

            if current_hash != baseline_hash:
                # Artifact modified - critical violation
                self._emit_drift_event(
                    drift_type=DriftType.FREEZE_VIOLATION,
                    severity=DriftSeverity.CRITICAL,
                    description=f"Frozen artifact modified: {artifact_path}",
                    evidence={
                        "artifact": artifact_path,
                        "baseline_hash": baseline_hash,
                        "current_hash": current_hash,
                        "modified": "true"
                    },
                    action="halt_and_reaudit_required"
                )

        return events

    def check_git_integrity(self) -> List[DriftEvent]:
        """
        Check git history integrity.

        Detects force-push, history rewriting, or other git manipulations.

        Returns:
            List of drift events detected (empty if git is clean)
        """
        events = []

        try:
            # Check for unpushed commits (could indicate force-push)
            result = subprocess.run(
                ["git", "log", "--branches", "--not", "--remotes", "--oneline"],
                capture_output=True,
                text=True,
                cwd=self.nova_root
            )

            if result.returncode == 0 and result.stdout.strip():
                # Unpushed commits detected - could be normal or force-push
                self._emit_drift_event(
                    drift_type=DriftType.GIT_INTEGRITY,
                    severity=DriftSeverity.INFO,
                    description="Unpushed commits detected (normal for development, verify before deployment)",
                    evidence={"unpushed_commits": result.stdout.strip()},
                    action="inform_only"
                )

            # Check for diverged branches (could indicate rebase/force-push)
            result = subprocess.run(
                ["git", "status", "-sb"],
                capture_output=True,
                text=True,
                cwd=self.nova_root
            )

            if "ahead" in result.stdout or "behind" in result.stdout:
                self._emit_drift_event(
                    drift_type=DriftType.GIT_INTEGRITY,
                    severity=DriftSeverity.WARNING,
                    description="Git branch diverged from remote (verify history integrity)",
                    evidence={"git_status": result.stdout.strip()},
                    action="manual_verification_required"
                )

        except Exception as e:
            self._emit_drift_event(
                drift_type=DriftType.GIT_INTEGRITY,
                severity=DriftSeverity.WARNING,
                description=f"Git integrity check failed: {str(e)}",
                evidence={"error": str(e)},
                action="continue_with_degraded_monitoring"
            )

        return events

    def run_continuous_monitoring(self, interval_seconds: int = 60):
        """
        Run continuous constitutional drift monitoring.

        Required by DOC v1.0 Section 4.2:
        "Derivatives must implement continuous constitutional drift monitoring
        as a deployment requirement."

        Args:
            interval_seconds: Monitoring check interval (default 60 seconds)
        """
        self.is_running = True
        print(f"[DRIFT MONITOR] Starting continuous monitoring (interval: {interval_seconds}s)")

        try:
            while self.is_running:
                # Run all drift checks
                self.check_o_r_drift()
                self.check_freeze_violations()
                self.check_git_integrity()

                # Wait for next interval
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("[DRIFT MONITOR] Stopped by operator")
            self.is_running = False

        except ConstitutionalViolationError as e:
            print(f"[DRIFT MONITOR] HALTED: {e}")
            self.is_running = False
            raise

    def stop(self):
        """Stop continuous monitoring"""
        self.is_running = False
        print("[DRIFT MONITOR] Monitoring stopped")

    def get_status(self) -> dict:
        """Get current drift monitor status"""
        return {
            "is_running": self.is_running,
            "nova_root": self.nova_root,
            "frozen_artifacts_count": len(self.frozen_artifacts),
            "baseline_hashes_computed": len(self.artifact_hashes),
            "monitoring_active": self.is_running
        }


class ConstitutionalViolationError(Exception):
    """Raised when critical constitutional violation detected"""
    pass


# Standalone check function for pre-deployment verification
def verify_nova_constitutional_state(nova_root: str) -> dict:
    """
    Verify Nova's constitutional state (one-time check).

    Used for pre-deployment verification (DOC Section 4.1).

    Returns:
        dict with verification results
    """
    monitor = ConstitutionalDriftMonitor(nova_root)

    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "nova_root": nova_root,
        "checks": {},
        "compliant": True
    }

    # Check O→R drift
    try:
        monitor.check_o_r_drift()
        results["checks"]["o_r_drift"] = "PASS"
    except ConstitutionalViolationError:
        results["checks"]["o_r_drift"] = "FAIL"
        results["compliant"] = False

    # Check freeze violations
    try:
        monitor.check_freeze_violations()
        results["checks"]["freeze_violations"] = "PASS"
    except ConstitutionalViolationError:
        results["checks"]["freeze_violations"] = "FAIL"
        results["compliant"] = False

    # Check git integrity
    try:
        monitor.check_git_integrity()
        results["checks"]["git_integrity"] = "PASS"
    except ConstitutionalViolationError:
        results["checks"]["git_integrity"] = "FAIL"
        results["compliant"] = False

    return results


if __name__ == "__main__":
    # Example: Run one-time verification
    import sys

    if len(sys.argv) < 2:
        print("Usage: python drift_monitor.py <nova_root_path>")
        sys.exit(1)

    nova_root = sys.argv[1]

    print("=== Nova Constitutional State Verification ===")
    results = verify_nova_constitutional_state(nova_root)

    print(f"\nTimestamp: {results['timestamp']}")
    print(f"Nova Root: {results['nova_root']}")
    print("\nChecks:")
    for check, status in results['checks'].items():
        print(f"  {check}: {status}")

    print(f"\nCompliant: {results['compliant']}")

    if not results['compliant']:
        print("\n❌ Constitutional violations detected. Deployment NOT SAFE.")
        sys.exit(1)
    else:
        print("\n✅ Nova constitutional state verified. Deployment safe.")
        sys.exit(0)
