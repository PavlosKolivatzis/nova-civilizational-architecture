#!/usr/bin/env python3
"""
Nova Continuity Vault Verification Script

Reads vault.manifest.yaml and executes declarative verification steps.
Provides consistent exit codes for CI/CD integration.

Usage:
    python scripts/verify_vault.py [--manifest PATH] [--verbose]

Exit Codes:
    0: All verifications passed
    1: One or more verifications failed
    2: Manifest parsing error
    3: Missing dependencies
"""

import argparse
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple


class VaultVerifier:
    """Handles vault manifest verification execution."""

    def __init__(self, manifest_path: str, verbose: bool = False):
        self.manifest_path = Path(manifest_path)
        self.verbose = verbose
        self.manifest: Dict[str, Any] = {}

    def load_manifest(self) -> bool:
        """Load and parse the vault manifest."""
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                self.manifest = yaml.safe_load(f)
            if self.verbose:
                print(f"✓ Loaded manifest: {self.manifest_path}")
            return True
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"✗ Failed to load manifest: {e}")
            return False

    def execute_step(self, step: Dict[str, str]) -> Tuple[bool, str]:
        """
        Execute a single verification step.

        Returns:
            (success: bool, output: str)
        """
        name = step.get('name', 'unnamed')
        cmd = step.get('cmd', '')

        if not cmd:
            return False, f"Step '{name}' has no command"

        try:
            if self.verbose:
                print(f"→ Executing: {name}")
                print(f"  Command: {cmd}")

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent  # Repository root
            )

            success = result.returncode == 0
            output = result.stdout + result.stderr

            if self.verbose:
                status = "✓" if success else "✗"
                print(f"{status} {name}: {'PASSED' if success else 'FAILED'}")
                if output.strip():
                    print(f"  Output: {output.strip()}")

            return success, output

        except Exception as e:
            return False, f"Execution error: {e}"

    def verify_all(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Execute all verification steps from the manifest.

        Returns:
            (overall_success: bool, step_results: List[Dict])
        """
        if not self.manifest:
            return False, []

        verification = self.manifest.get('verification', {})
        steps = verification.get('steps', [])

        if not steps:
            print("✗ No verification steps defined in manifest")
            return False, []

        results = []
        overall_success = True

        for step in steps:
            success, output = self.execute_step(step)
            results.append({
                'step': step.get('name', 'unnamed'),
                'success': success,
                'output': output.strip()
            })

            if not success:
                overall_success = False

        return overall_success, results

    def print_summary(self, results: List[Dict[str, Any]]):
        """Print a summary of verification results."""
        if not results:
            print("No verification results to summarize")
            return

        passed = sum(1 for r in results if r['success'])
        total = len(results)

        print(f"\n📊 Verification Summary: {passed}/{total} steps passed")

        if passed == total:
            print("🎉 All vault verifications PASSED")
        else:
            print("❌ Some vault verifications FAILED")
            print("\nFailed steps:")
            for result in results:
                if not result['success']:
                    print(f"  ✗ {result['step']}: {result['output']}")

    def check_dependencies(self) -> bool:
        """Check if required tools are available."""
        required_tools = ['sha256sum', 'yamllint', 'gpg', 'cosign']

        missing = []
        for tool in required_tools:
            try:
                subprocess.run(
                    [tool, '--version'],
                    capture_output=True,
                    check=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(tool)

        if missing:
            print(f"✗ Missing required tools: {', '.join(missing)}")
            print("Install missing tools and try again.")
            return False

        if self.verbose:
            print("✓ All required verification tools are available")
        return True


def main():
    """Main verification entry point."""
    parser = argparse.ArgumentParser(description="Verify Nova Continuity Vault integrity")
    parser.add_argument(
        '--manifest',
        default='attest/archives/vault.manifest.yaml',
        help='Path to vault manifest file'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    print("🔒 Nova Continuity Vault Verification")
    print(f"Manifest: {args.manifest}")
    print()

    verifier = VaultVerifier(args.manifest, args.verbose)

    # Check dependencies
    if not verifier.check_dependencies():
        return 3

    # Load manifest
    if not verifier.load_manifest():
        return 2

    # Execute verifications
    success, results = verifier.verify_all()

    # Print summary
    verifier.print_summary(results)

    # Return appropriate exit code
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())