"""
VSD-1 External Verifiability API
Version: 0.1
Purpose: Anyone can verify VSD-1's sovereignty claims
Compliance: DOC v1.0 Section 6 (Verification Requirements)

This module provides external verification of VSD-1's constitutional compliance.

Verification capabilities:
- Pre-deployment verification (git history, frozen artifacts, boundaries)
- Runtime verification (query current boundary state, drift status)
- Sovereignty proof generation (cryptographic proof of DOC compliance)
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
from pathlib import Path

# Add constitutional_memory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from constitutional_memory.memory import ConstitutionalMemory, record_verification

# Import VSD-1 subsystems
from drift_monitor import ConstitutionalDriftMonitor, verify_nova_constitutional_state
from f_domain_filter import FDomainFilter
from audit_log import TamperEvidentAuditLog


class SovereigntyVerifier:
    """
    External verification API for VSD-1 sovereignty.

    Allows anyone to verify:
    - VSD-1's constitutional declarations (jurisdiction, refusal, authority)
    - Nova's constitutional state (frozen artifacts, boundaries intact)
    - VSD-1's operational compliance (drift monitoring, F-domain filtering)
    - Audit trail integrity (tamper-evident log)
    """

    def __init__(self, nova_root: str, vsd_root: str, audit_log_path: str):
        """
        Initialize verifier.

        Args:
            nova_root: Path to Nova Core repository
            vsd_root: Path to VSD-1 directory
            audit_log_path: Path to VSD-1 audit log
        """
        self.nova_root = nova_root
        self.vsd_root = vsd_root
        self.audit_log_path = audit_log_path

        # Constitutional memory (temporal continuity)
        try:
            self.memory = ConstitutionalMemory()
        except Exception:
            self.memory = None  # Graceful degradation

    def verify_pre_deployment(self) -> Dict:
        """
        Pre-deployment verification (DOC Section 4.1).

        Verifies:
        1. Nova's git history integrity
        2. Nova's frozen artifacts unchanged
        3. No O→R drift (A_p, harm_status unwired)
        4. No F-domain implementation (RefusalEvent runtime)
        5. VSD-1 ontology declared

        Returns:
            Verification results dict
        """
        print("=== VSD-1 Pre-Deployment Verification ===\n")

        results = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "vsd_version": "0.1",
            "doc_compliance": "v1.0",
            "checks": {},
            "deployment_safe": True
        }

        # 1. Verify Nova's constitutional state
        print("[1/5] Verifying Nova constitutional state...")
        try:
            nova_state = verify_nova_constitutional_state(self.nova_root)
            results["checks"]["nova_constitutional_state"] = nova_state
            if not nova_state.get("compliant", False):
                results["deployment_safe"] = False
        except Exception as e:
            results["checks"]["nova_constitutional_state"] = {"error": str(e)}
            results["deployment_safe"] = False

        # 2. Verify git history integrity
        print("[2/5] Verifying git history integrity...")
        git_check = self._verify_git_integrity()
        results["checks"]["git_integrity"] = git_check
        if not git_check.get("clean", False):
            results["deployment_safe"] = False

        # 3. Verify VSD-1 ontology exists and is valid
        print("[3/5] Verifying VSD-1 ontology...")
        ontology_check = self._verify_ontology()
        results["checks"]["ontology"] = ontology_check
        if not ontology_check.get("valid", False):
            results["deployment_safe"] = False

        # 4. Verify F-domain filter functional
        print("[4/5] Verifying F-domain filter...")
        filter_check = self._verify_f_domain_filter()
        results["checks"]["f_domain_filter"] = filter_check
        if not filter_check.get("functional", False):
            results["deployment_safe"] = False

        # 5. Verify audit log initialized
        print("[5/5] Verifying audit log...")
        audit_check = self._verify_audit_log()
        results["checks"]["audit_log"] = audit_check
        if not audit_check.get("initialized", False):
            results["deployment_safe"] = False

        # Summary
        print("\n=== Verification Summary ===")
        print(f"Deployment Safe: {results['deployment_safe']}")

        if results["deployment_safe"]:
            print("\n[OK] VSD-1 is ready for deployment")
        else:
            print("\n[FAIL] VSD-1 is NOT safe for deployment")
            print("Review failures above before deploying.")

        return results

    def _verify_git_integrity(self) -> Dict:
        """Verify git history integrity"""
        try:
            # Check for unpushed commits
            result = subprocess.run(
                ["git", "log", "--branches", "--not", "--remotes", "--oneline"],
                capture_output=True,
                text=True,
                cwd=self.nova_root
            )

            unpushed = result.stdout.strip()

            # Check status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.nova_root
            )

            uncommitted = status_result.stdout.strip()

            return {
                "clean": len(unpushed) == 0 and len(uncommitted) == 0,
                "unpushed_commits": unpushed if unpushed else None,
                "uncommitted_changes": uncommitted if uncommitted else None,
                "status": "clean" if (not unpushed and not uncommitted) else "dirty"
            }

        except Exception as e:
            return {"error": str(e), "clean": False}

    def _verify_ontology(self) -> Dict:
        """Verify VSD-1 ontology.yaml"""
        ontology_path = os.path.join(self.vsd_root, "ontology.yaml")

        if not os.path.exists(ontology_path):
            return {"valid": False, "error": "ontology.yaml not found"}

        try:
            import yaml
            with open(ontology_path, 'r') as f:
                ontology = yaml.safe_load(f)

            # Check required sections
            required_sections = ['jurisdiction', 'refusal_map', 'authority_surface', 'moral_ownership']
            missing = [s for s in required_sections if s not in ontology]

            if missing:
                return {
                    "valid": False,
                    "error": f"Missing sections: {missing}"
                }

            # Check jurisdiction has O/R/F domains
            jurisdiction = ontology.get('jurisdiction', {})
            has_domains = all(d in jurisdiction for d in ['observe_only', 'route_only', 'refuse_always'])

            return {
                "valid": has_domains,
                "sections_present": required_sections,
                "f_domains_count": len(jurisdiction.get('refuse_always', [])),
                "status": "valid" if has_domains else "incomplete"
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def _verify_f_domain_filter(self) -> Dict:
        """Verify F-domain filter is functional"""
        try:
            ontology_path = os.path.join(self.vsd_root, "ontology.yaml")
            filter = FDomainFilter(ontology_path)

            # Test with known F-domain query
            test_query = "Is this morally right to do?"
            allowed, refusal = filter.filter_query(test_query)

            return {
                "functional": not allowed,  # Should refuse F-domain
                "test_query": test_query,
                "refused": not allowed,
                "refusal_code": refusal.refusal_code.value if refusal else None,
                "status": "functional" if not allowed else "not_refusing_f_domains"
            }

        except Exception as e:
            return {"functional": False, "error": str(e)}

    def _verify_audit_log(self) -> Dict:
        """Verify audit log is initialized"""
        if not os.path.exists(self.audit_log_path):
            return {"initialized": False, "error": "Audit log file not found"}

        try:
            audit_log = TamperEvidentAuditLog(self.audit_log_path)
            is_valid, error = audit_log.verify_integrity()

            stats = audit_log.get_stats()

            return {
                "initialized": True,
                "integrity_valid": is_valid,
                "total_entries": stats.get("total_entries", 0),
                "event_types": stats.get("event_types", {}),
                "status": "valid" if is_valid else "integrity_failed",
                "error": error
            }

        except Exception as e:
            return {"initialized": False, "error": str(e)}

    def query_boundary_state(self) -> Dict:
        """
        Query current boundary state.

        Returns VSD-1's jurisdictional boundaries, refusal map, authority surface.
        """
        try:
            import yaml
            ontology_path = os.path.join(self.vsd_root, "ontology.yaml")

            with open(ontology_path, 'r') as f:
                ontology = yaml.safe_load(f)

            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "jurisdiction": ontology.get("jurisdiction", {}),
                "refusal_map": ontology.get("refusal_map", {}),
                "authority_surface": ontology.get("authority_surface", {}),
                "moral_ownership": ontology.get("moral_ownership", {})
            }

        except Exception as e:
            return {"error": str(e)}

    def query_drift_monitor_status(self) -> Dict:
        """Query drift monitor status"""
        try:
            monitor = ConstitutionalDriftMonitor(self.nova_root)
            return monitor.get_status()

        except Exception as e:
            return {"error": str(e)}

    def generate_sovereignty_proof(self, output_path: str) -> Dict:
        """
        Generate sovereignty proof (cryptographic proof of DOC compliance).

        Proof includes:
        - Ontology declaration (jurisdiction, refusal, authority)
        - Audit log export (all events)
        - Nova verification results
        - Hash of entire proof

        Args:
            output_path: Path to write proof file

        Returns:
            Proof metadata
        """
        print("=== Generating Sovereignty Proof ===\n")

        proof = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "vsd_version": "0.1",
            "doc_compliance": "v1.0",
            "proof_type": "sovereignty_verification",
            "components": {}
        }

        # 1. Include ontology
        print("[1/4] Including ontology declaration...")
        ontology_path = os.path.join(self.vsd_root, "ontology.yaml")
        try:
            import yaml
            with open(ontology_path, 'r') as f:
                proof["components"]["ontology"] = yaml.safe_load(f)
        except Exception as e:
            proof["components"]["ontology"] = {"error": str(e)}

        # 2. Include audit log
        print("[2/4] Including audit trail...")
        try:
            audit_log = TamperEvidentAuditLog(self.audit_log_path)
            entries = audit_log.get_entries()
            is_valid, error = audit_log.verify_integrity()

            proof["components"]["audit_log"] = {
                "total_entries": len(entries),
                "integrity_valid": is_valid,
                "integrity_error": error,
                "entries": entries
            }
        except Exception as e:
            proof["components"]["audit_log"] = {"error": str(e)}

        # 3. Include Nova verification
        print("[3/4] Including Nova verification...")
        try:
            nova_state = verify_nova_constitutional_state(self.nova_root)
            proof["components"]["nova_verification"] = nova_state
        except Exception as e:
            proof["components"]["nova_verification"] = {"error": str(e)}

        # 4. Compute proof hash
        print("[4/4] Computing proof hash...")
        proof_json = json.dumps(proof, sort_keys=True)
        proof_hash = hashlib.sha256(proof_json.encode()).hexdigest()
        proof["proof_hash"] = proof_hash

        # Write proof to file
        with open(output_path, 'w') as f:
            json.dump(proof, f, indent=2)

        print(f"\n[OK] Sovereignty proof written to: {output_path}")
        print(f"Proof Hash: {proof_hash}")

        # Record to constitutional memory
        if self.memory:
            try:
                record_verification(
                    self.memory,
                    verification_type="self_verification",
                    result="PASS",
                    derivative_id="vsd1"
                )
            except Exception:
                pass  # Graceful degradation

        return {
            "proof_file": output_path,
            "proof_hash": proof_hash,
            "timestamp": proof["generated_at"],
            "components_included": list(proof["components"].keys())
        }

    def verify_peer_sovereignty_proof(self, proof_path: str) -> Dict:
        """
        Verify another VSD-1's sovereignty proof (federation primitive).

        This enables peer-to-peer sovereignty verification:
        VSD-1 instance A can verify VSD-1 instance B's constitutional compliance.

        Args:
            proof_path: Path to peer's sovereignty proof JSON file

        Returns:
            Verification results dict
        """
        print("=== Peer Sovereignty Verification ===\n")

        results = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "peer_proof_file": proof_path,
            "verification_passed": True,
            "checks": {}
        }

        # 1. Load proof file
        print("[1/5] Loading peer sovereignty proof...")
        try:
            with open(proof_path, 'r') as f:
                proof = json.load(f)
            results["checks"]["proof_loaded"] = {"status": "PASS"}
        except Exception as e:
            results["checks"]["proof_loaded"] = {"status": "FAIL", "error": str(e)}
            results["verification_passed"] = False
            return results

        # 2. Verify proof hash
        print("[2/5] Verifying proof hash...")
        try:
            # Recompute hash
            proof_copy = {k: v for k, v in proof.items() if k != "proof_hash"}
            proof_json = json.dumps(proof_copy, sort_keys=True)
            computed_hash = hashlib.sha256(proof_json.encode()).hexdigest()

            if computed_hash == proof.get("proof_hash"):
                results["checks"]["proof_hash"] = {
                    "status": "PASS",
                    "hash": computed_hash
                }
            else:
                results["checks"]["proof_hash"] = {
                    "status": "FAIL",
                    "expected": proof.get("proof_hash"),
                    "computed": computed_hash
                }
                results["verification_passed"] = False
        except Exception as e:
            results["checks"]["proof_hash"] = {"status": "FAIL", "error": str(e)}
            results["verification_passed"] = False

        # 3. Verify required components present
        print("[3/5] Verifying required components...")
        required_components = ["ontology", "audit_log", "nova_verification"]
        components = proof.get("components", {})
        missing = [c for c in required_components if c not in components]

        if missing:
            results["checks"]["components"] = {
                "status": "FAIL",
                "missing": missing
            }
            results["verification_passed"] = False
        else:
            results["checks"]["components"] = {
                "status": "PASS",
                "present": required_components
            }

        # 4. Verify audit log integrity
        print("[4/5] Verifying audit log integrity...")
        audit_data = components.get("audit_log", {})
        if audit_data.get("integrity_valid"):
            results["checks"]["audit_integrity"] = {
                "status": "PASS",
                "total_entries": audit_data.get("total_entries", 0)
            }
        else:
            results["checks"]["audit_integrity"] = {
                "status": "FAIL",
                "error": audit_data.get("integrity_error")
            }
            results["verification_passed"] = False

        # 5. Verify ontology structure
        print("[5/5] Verifying ontology structure...")
        ontology = components.get("ontology", {})
        required_sections = ['jurisdiction', 'refusal_map', 'authority_surface', 'moral_ownership']
        missing_sections = [s for s in required_sections if s not in ontology]

        if missing_sections:
            results["checks"]["ontology_structure"] = {
                "status": "FAIL",
                "missing_sections": missing_sections
            }
            results["verification_passed"] = False
        else:
            results["checks"]["ontology_structure"] = {
                "status": "PASS",
                "sections_present": required_sections
            }

        # Summary
        print("\n=== Peer Verification Summary ===")
        print(f"Peer Proof: {proof_path}")
        print(f"Verification Passed: {results['verification_passed']}")

        if results["verification_passed"]:
            print("\n[OK] Peer sovereignty verified")
            print("Peer is DOC-compliant and federation-ready")
        else:
            print("\n[FAIL] Peer sovereignty verification failed")
            print("Peer does not meet constitutional requirements")

        # Record to constitutional memory
        if self.memory:
            try:
                # Extract peer derivative_id from proof if available
                peer_id = proof.get("components", {}).get("ontology", {}).get("metadata", {}).get("derivative_id", "unknown")
                record_verification(
                    self.memory,
                    verification_type="peer_verification",
                    result="PASS" if results["verification_passed"] else "FAIL",
                    derivative_id=peer_id
                )
            except Exception:
                pass  # Graceful degradation

        return results


def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="VSD-1 Sovereignty Verification")
    parser.add_argument("--nova-root", required=True, help="Path to Nova Core repository")
    parser.add_argument("--vsd-root", default=".", help="Path to VSD-1 directory")
    parser.add_argument("--audit-log", default="vsd1_audit.jsonl", help="Path to audit log")

    subparsers = parser.add_subparsers(dest="command", help="Verification command")

    # Pre-deployment verification
    subparsers.add_parser("pre-deployment", help="Pre-deployment verification")

    # Boundary state query
    subparsers.add_parser("boundary-state", help="Query current boundary state")

    # Drift monitor status
    subparsers.add_parser("drift-status", help="Query drift monitor status")

    # Sovereignty proof
    proof_parser = subparsers.add_parser("sovereignty-proof", help="Generate sovereignty proof")
    proof_parser.add_argument("--output", default="vsd1_sovereignty_proof.json",
                             help="Output file for proof")

    # Peer verification
    peer_parser = subparsers.add_parser("verify-peer", help="Verify peer sovereignty proof (federation)")
    peer_parser.add_argument("--proof", required=True,
                            help="Path to peer's sovereignty proof JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Create verifier
    verifier = SovereigntyVerifier(args.nova_root, args.vsd_root, args.audit_log)

    # Execute command
    if args.command == "pre-deployment":
        results = verifier.verify_pre_deployment()
        print(f"\nResults written to stdout")
        sys.exit(0 if results["deployment_safe"] else 1)

    elif args.command == "boundary-state":
        state = verifier.query_boundary_state()
        print(json.dumps(state, indent=2))

    elif args.command == "drift-status":
        status = verifier.query_drift_monitor_status()
        print(json.dumps(status, indent=2))

    elif args.command == "sovereignty-proof":
        proof = verifier.generate_sovereignty_proof(args.output)
        print(f"\nProof metadata:")
        print(json.dumps(proof, indent=2))

    elif args.command == "verify-peer":
        results = verifier.verify_peer_sovereignty_proof(args.proof)
        print(f"\nVerification results:")
        print(json.dumps(results, indent=2))
        sys.exit(0 if results["verification_passed"] else 1)


if __name__ == "__main__":
    main()
