"""Attest secrets baseline to create tamper-evident audit trail.

Phase 17: Secret Scanning Enhancement
Creates hash-linked attestation of secrets baseline following Nova's
ledger pattern for immutable provenance.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any


def compute_baseline_hash(baseline_path: Path) -> str:
    """Compute BLAKE2b hash of baseline file.

    Args:
        baseline_path: Path to .secrets.baseline

    Returns:
        Hex digest of baseline content
    """
    content = baseline_path.read_bytes()
    return hashlib.blake2b(content).hexdigest()


def extract_baseline_stats(baseline_path: Path) -> Dict[str, Any]:
    """Extract statistics from baseline file.

    Args:
        baseline_path: Path to .secrets.baseline

    Returns:
        Dict with file_count, finding_count, plugin counts
    """
    try:
        data = json.loads(baseline_path.read_text())
    except json.JSONDecodeError:
        return {
            'file_count': 0,
            'finding_count': 0,
            'plugins': {},
            'version': 'unknown'
        }

    results = data.get('results', {})
    file_count = len(results)
    finding_count = sum(len(secrets) for secrets in results.values())

    # Count findings by plugin type
    plugins: Dict[str, int] = {}
    for secrets in results.values():
        for secret in secrets:
            plugin_type = secret.get('type', 'unknown')
            plugins[plugin_type] = plugins.get(plugin_type, 0) + 1

    return {
        'file_count': file_count,
        'finding_count': finding_count,
        'plugins': plugins,
        'version': data.get('version', 'unknown')
    }


def create_attestation(
    baseline_path: Path,
    output_path: Path | None = None
) -> Dict[str, Any]:
    """Create attestation record for secrets baseline.

    Args:
        baseline_path: Path to .secrets.baseline
        output_path: Optional output path for attestation JSON

    Returns:
        Attestation dict
    """
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline not found: {baseline_path}")

    # Compute hash
    baseline_hash = compute_baseline_hash(baseline_path)

    # Extract stats
    stats = extract_baseline_stats(baseline_path)

    # Create attestation
    attestation = {
        'kind': 'SECRETS_BASELINE_ATTESTATION',
        'version': '1.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'baseline_path': str(baseline_path),
        'baseline_hash': baseline_hash,
        'hash_algorithm': 'BLAKE2b-512',
        'statistics': stats,
        'attested_by': 'attest_secrets_baseline.py',
        'nova_phase': '17'
    }

    # Write to file if requested
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(attestation, indent=2))

    return attestation


def verify_attestation(
    baseline_path: Path,
    attestation_path: Path
) -> bool:
    """Verify that baseline matches its attestation.

    Args:
        baseline_path: Path to .secrets.baseline
        attestation_path: Path to attestation JSON

    Returns:
        True if hashes match, False otherwise

    Raises:
        FileNotFoundError: If files don't exist
        ValueError: If attestation is invalid
    """
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline not found: {baseline_path}")

    if not attestation_path.exists():
        raise FileNotFoundError(f"Attestation not found: {attestation_path}")

    # Load attestation
    try:
        attestation = json.loads(attestation_path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid attestation JSON: {e}")

    # Compute current hash
    current_hash = compute_baseline_hash(baseline_path)

    # Compare
    attested_hash = attestation.get('baseline_hash')
    if not attested_hash:
        raise ValueError("Attestation missing 'baseline_hash' field")

    return current_hash == attested_hash


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Attest secrets baseline for tamper-evident audit trail"
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Create attestation
    create_parser = subparsers.add_parser(
        'create',
        help='Create new attestation'
    )
    create_parser.add_argument(
        '--baseline',
        default='.secrets.baseline',
        help='Path to secrets baseline (default: .secrets.baseline)'
    )
    create_parser.add_argument(
        '--output',
        default='.artifacts/secrets-baseline-attestation.json',
        help='Output path for attestation (default: .artifacts/secrets-baseline-attestation.json)'
    )

    # Verify attestation
    verify_parser = subparsers.add_parser(
        'verify',
        help='Verify baseline against attestation'
    )
    verify_parser.add_argument(
        '--baseline',
        default='.secrets.baseline',
        help='Path to secrets baseline (default: .secrets.baseline)'
    )
    verify_parser.add_argument(
        '--attestation',
        default='.artifacts/secrets-baseline-attestation.json',
        help='Path to attestation (default: .artifacts/secrets-baseline-attestation.json)'
    )

    args = parser.parse_args()

    if args.command == 'create':
        try:
            attestation = create_attestation(
                Path(args.baseline),
                Path(args.output)
            )

            print(f"[OK] Baseline attested: {attestation['baseline_hash'][:16]}...")
            print(f"[INFO] Attestation: {args.output}")
            print(f"[STATS] Statistics:")
            print(f"   - Files scanned: {attestation['statistics']['file_count']}")
            print(f"   - Findings: {attestation['statistics']['finding_count']}")
            print(f"   - Plugins: {len(attestation['statistics']['plugins'])}")

        except FileNotFoundError as e:
            print(f"[ERROR] Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == 'verify':
        try:
            is_valid = verify_attestation(
                Path(args.baseline),
                Path(args.attestation)
            )

            if is_valid:
                print("[OK] Baseline matches attestation - integrity verified")
                sys.exit(0)
            else:
                print("[ERROR] Baseline does NOT match attestation - possible tampering!", file=sys.stderr)
                print("   Run 'create' to generate new attestation after reviewing changes.", file=sys.stderr)
                sys.exit(1)

        except (FileNotFoundError, ValueError) as e:
            print(f"[ERROR] Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
