"""
VSD-0: Minimal Sovereign Derivative
Version: 0.1
Main Entry Point

This is the first constitutional child of Nova Core.
It proves that sovereign derivatives can exist mechanically.

Usage:
    python vsd0.py --nova-root <path> [options]
"""

import sys
import signal
from datetime import datetime
import argparse

from drift_monitor import ConstitutionalDriftMonitor
from f_domain_filter import FDomainFilter
from audit_log import create_audit_log_callback
from verify import SovereigntyVerifier


class VSD0:
    """
    VSD-0 Main Controller.

    Coordinates all 5 subsystems:
    1. ontology.yaml - Constitutional declaration (loaded)
    2. drift_monitor.py - Constitutional drift detection (running)
    3. f_domain_filter.py - F-domain refusal (active)
    4. audit_log.py - Tamper-evident ledger (recording)
    5. verify.py - External verifiability (available)
    """

    def __init__(self, nova_root: str, audit_log_path: str = "vsd0_audit.jsonl"):
        """
        Initialize VSD-0.

        Args:
            nova_root: Path to Nova Core repository
            audit_log_path: Path to audit log file
        """
        self.nova_root = nova_root
        self.audit_log_path = audit_log_path

        print("=== VSD-0: Minimal Sovereign Derivative ===")
        print(f"Nova Root: {nova_root}")
        print(f"Audit Log: {audit_log_path}")
        print()

        # Create audit log callback
        self.audit_log_callback = create_audit_log_callback(audit_log_path)

        # Initialize subsystems
        self.drift_monitor = None
        self.f_domain_filter = None
        self.verifier = None

        self._initialize_subsystems()

    def _initialize_subsystems(self):
        """Initialize all VSD-0 subsystems"""
        print("[INIT] Initializing subsystems...")

        # 1. Drift Monitor
        print("  [1/3] Drift Monitor...")
        self.drift_monitor = ConstitutionalDriftMonitor(
            self.nova_root,
            audit_log_callback=self.audit_log_callback
        )

        # 2. F-Domain Filter
        print("  [2/3] F-Domain Filter...")
        self.f_domain_filter = FDomainFilter(
            "ontology.yaml",
            audit_log_callback=self.audit_log_callback
        )

        # 3. Verifier
        print("  [3/3] Verifier API...")
        self.verifier = SovereigntyVerifier(
            self.nova_root,
            ".",
            self.audit_log_path
        )

        print("[INIT] [OK] All subsystems initialized\n")

    def run_pre_deployment_check(self) -> bool:
        """
        Run pre-deployment verification.

        Required by DOC v1.0 Section 4.1.

        Returns:
            True if deployment safe, False otherwise
        """
        print("=== Pre-Deployment Verification ===\n")

        results = self.verifier.verify_pre_deployment()

        return results.get("deployment_safe", False)

    def start(self, monitoring_interval: int = 60):
        """
        Start VSD-0 operation.

        Args:
            monitoring_interval: Drift monitoring interval in seconds
        """
        print("=== Starting VSD-0 ===\n")

        # Pre-deployment check
        if not self.run_pre_deployment_check():
            print("\n[FAIL] Pre-deployment check failed. Aborting.")
            sys.exit(1)

        print("\n[OK] Pre-deployment check passed\n")

        # Log startup
        self.audit_log_callback({
            "event": "vsd0_startup",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "nova_root": self.nova_root,
            "version": "0.1"
        }, event_type="system_event")

        print("VSD-0 is now running in constitutional compliance mode.")
        print("Subsystems active:")
        print("  [OK] Drift Monitor (continuous)")
        print("  [OK] F-Domain Filter (active)")
        print("  [OK] Audit Log (recording)")
        print("  [OK] Verifier API (available)")
        print()
        print(f"Monitoring interval: {monitoring_interval}s")
        print("Press Ctrl+C to stop")
        print()

        # Start drift monitoring (blocks)
        try:
            self.drift_monitor.run_continuous_monitoring(monitoring_interval)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop VSD-0 operation"""
        print("\n\n=== Stopping VSD-0 ===")

        # Stop drift monitor
        if self.drift_monitor:
            self.drift_monitor.stop()

        # Log shutdown
        self.audit_log_callback({
            "event": "vsd0_shutdown",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }, event_type="system_event")

        print("[OK] VSD-0 stopped cleanly\n")

    def query_example(self, query: str):
        """
        Process a query through VSD-0's filters.

        This demonstrates F-domain filtering in action.

        Args:
            query: Query string
        """
        print(f"\n=== Processing Query ===")
        print(f"Query: {query}\n")

        # Classify and filter
        domain = self.f_domain_filter.classify_query(query)
        allowed, refusal = self.f_domain_filter.filter_query(query)

        print(f"Domain: {domain.value}")
        print(f"Allowed: {allowed}")

        if refusal:
            print(f"Refusal Code: {refusal.refusal_code.value}")
            print(f"Constitutional Basis: {refusal.constitutional_basis}")
            print("\n[REFUSED] Query refused (F-domain)")
        else:
            print("\n[ALLOWED] Query allowed (would proceed to Nova)")

        print()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="VSD-0: Minimal Sovereign Derivative",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run pre-deployment check only
  python vsd0.py --nova-root ../nova-civilizational-architecture --check-only

  # Start VSD-0 with continuous monitoring
  python vsd0.py --nova-root ../nova-civilizational-architecture

  # Test query filtering
  python vsd0.py --nova-root ../nova-civilizational-architecture --test-query "Is this moral?"
        """
    )

    parser.add_argument(
        "--nova-root",
        required=True,
        help="Path to Nova Core repository"
    )

    parser.add_argument(
        "--audit-log",
        default="vsd0_audit.jsonl",
        help="Path to audit log file (default: vsd0_audit.jsonl)"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Drift monitoring interval in seconds (default: 60)"
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Run pre-deployment check only (don't start monitoring)"
    )

    parser.add_argument(
        "--test-query",
        type=str,
        help="Test a query through F-domain filter (don't start monitoring)"
    )

    args = parser.parse_args()

    # Create VSD-0
    vsd0 = VSD0(args.nova_root, args.audit_log)

    # Handle modes
    if args.check_only:
        # Pre-deployment check only
        safe = vsd0.run_pre_deployment_check()
        sys.exit(0 if safe else 1)

    elif args.test_query:
        # Test query filtering
        vsd0.query_example(args.test_query)
        sys.exit(0)

    else:
        # Normal operation (continuous monitoring)
        vsd0.start(args.interval)


if __name__ == "__main__":
    main()
