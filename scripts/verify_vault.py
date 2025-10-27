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
import json
import os
import shutil
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple

if os.name == "nt":
    # Force UTF-8 output so audit logs render correctly on Windows consoles.
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass

# Make bundled audit tools available without relying on global PATH.
REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools" / "audit"
BOOTSTRAP_SCRIPT = REPO_ROOT / "scripts" / "bootstrap_audit_tools.py"
PATH_HINT_FILE = TOOLS_DIR / "paths.env"
if TOOLS_DIR.exists():
    current_path = os.environ.get("PATH", "")
    # Prepend to ensure our versions win when multiple are installed.
    os.environ["PATH"] = f"{str(TOOLS_DIR)}{os.pathsep}{current_path}" if current_path else str(TOOLS_DIR)


def ensure_audit_tools_on_path() -> None:
    """Ensure cosign/sha256sum are available, bootstrapping if necessary."""
    needs_bootstrap = (
        not shutil.which("cosign")
        or not shutil.which("sha256sum")
        or not PATH_HINT_FILE.exists()
    )

    if needs_bootstrap and BOOTSTRAP_SCRIPT.exists():
        subprocess.run([sys.executable, str(BOOTSTRAP_SCRIPT)], cwd=str(REPO_ROOT), check=True)

    if PATH_HINT_FILE.exists():
        with PATH_HINT_FILE.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.endswith("_PATH") and value:
                    os.environ[key] = value
                    candidate = Path(value)
                    path_entry = str(candidate.parent if candidate.suffix else candidate)
                    path = os.environ.get("PATH", "")
                    if path_entry not in path.split(os.pathsep):
                        os.environ["PATH"] = f"{path_entry}{os.pathsep}{path}" if path else path_entry


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
                print(f"✓ Loaded manifest: {self.manifest_path}".encode('utf-8').decode('utf-8', errors='replace'))
            return True
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"✗ Failed to load manifest: {e}".encode('utf-8').decode('utf-8', errors='replace'))
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
                print(f"→ Executing: {name}".encode('utf-8').decode('utf-8', errors='replace'))
                print(f"  Command: {cmd}".encode('utf-8').decode('utf-8', errors='replace'))

            # Use shell=True on Windows with Git Bash tools in PATH
            # Ensure commands run in text mode with proper encoding
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=Path(__file__).parent.parent  # Repository root
            )

            success = result.returncode == 0
            output = result.stdout + result.stderr

            if self.verbose:
                status = "✓" if success else "✗"
                print(f"{status} {name}: {'PASSED' if success else 'FAILED'}".encode('utf-8').decode('utf-8', errors='replace'))
                if output.strip():
                    print(f"  Output: {output.strip()}".encode('utf-8').decode('utf-8', errors='replace'))

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
            print("✗ No verification steps defined in manifest".encode('utf-8').decode('utf-8', errors='replace'))
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

        print(f"\n📊 Verification Summary: {passed}/{total} steps passed".encode('utf-8').decode('utf-8', errors='replace'))

        if passed == total:
            print("🎉 All vault verifications PASSED".encode('utf-8').decode('utf-8', errors='replace'))
        else:
            print("❌ Some vault verifications FAILED".encode('utf-8').decode('utf-8', errors='replace'))
            print("\nFailed steps:")
            for result in results:
                if not result['success']:
                    print(f"  ✗ {result['step']}: {result['output']}".encode('utf-8').decode('utf-8', errors='replace'))

    def check_dependencies(self) -> bool:
        """Check if required tools are available."""
        required_tools = ['sha256sum', 'yamllint', 'gpg', 'cosign']
        version_flags = {
            'cosign': ['version'],
        }

        missing = []
        for tool in required_tools:
            try:
                cmd = [tool] + version_flags.get(tool, ['--version'])
                subprocess.run(cmd, capture_output=True, check=True)
                if tool == 'gpg':
                    pubkey = Path("trust") / "vault_public.gpg"
                    if pubkey.exists():
                        subprocess.run(
                            ['gpg', '--import', str(pubkey)],
                            capture_output=True,
                            check=True,
                        )
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(tool)

        if missing:
            print(f"✗ Missing required tools: {', '.join(missing)}".encode('utf-8').decode('utf-8', errors='replace'))
            print("Install missing tools and try again.".encode('utf-8').decode('utf-8', errors='replace'))
            return False

        if self.verbose:
            print("✓ All required verification tools are available")
        return True


def main():
    """Main verification entry point."""
    ensure_audit_tools_on_path()
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

    # Set UTF-8 encoding for stdout to handle Unicode properly
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

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

    # Validate Phase 11 attestation if present
    phase11_path = Path("attest") / "phase11_init.json"
    if phase11_path.exists():
        try:
            with phase11_path.open("r", encoding="utf-8") as fh:
                phase11_data = json.load(fh)
        except json.JSONDecodeError as exc:
            print(f"? Phase 11 attestation invalid JSON: {exc}".encode('utf-8').decode('utf-8', errors='replace'))
            return 1

        required_keys = {
            "schema",
            "epoch_base",
            "branch",
            "base_commit",
            "generated_at_utc",
        }
        missing = sorted(required_keys - phase11_data.keys())
        if missing:
            print(f"? Phase 11 attestation missing keys: {', '.join(missing)}".encode('utf-8').decode('utf-8', errors='replace'))
            return 1

        print(f"✅ Phase 11 attestation present: {phase11_data['branch']} @ {phase11_data['base_commit']}".encode('utf-8').decode('utf-8', errors='replace'))

    # Execute verifications
    success, results = verifier.verify_all()

    # Print summary
    verifier.print_summary(results)

    # Return appropriate exit code
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
