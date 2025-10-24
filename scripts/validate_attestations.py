#!/usr/bin/env python3
"""Lightweight validator for Nova attestation artifacts.

The vault manifest references a mixture of JSON attestations, markdown
capsules, and log directories.  This script verifies that the referenced
artifacts exist, that required JSON resources parse correctly, and that
any wildcard patterns resolve to at least one file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

import yaml


def load_manifest(manifest_path: Path) -> dict:
    with manifest_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve_paths(base: Path, patterns: Iterable[str]) -> List[Tuple[str, List[Path]]]:
    """Return list of (pattern, matches) for each pattern."""
    resolved = []
    for pattern in patterns:
        target = base / pattern
        if any(ch in pattern for ch in "*?[]"):
            matches = sorted(base.glob(pattern))
        else:
            matches = [target] if target.exists() else []
        resolved.append((pattern, matches))
    return resolved


def validate_json_files(files: Iterable[Path]) -> List[str]:
    errors: List[str] = []
    for file_path in files:
        if file_path.suffix.lower() != ".json":
            continue

        try:
            with file_path.open("r", encoding="utf-8") as handle:
                json.load(handle)
        except Exception as exc:  # pragma: no cover - best-effort validation
            errors.append(f"{file_path}: invalid JSON ({exc})")
    return errors


def validate_attestations(manifest: dict, repo_root: Path) -> List[str]:
    errors: List[str] = []
    lineage = manifest.get("lineage", [])
    base = repo_root

    for entry in lineage:
        phase = entry.get("phase", "unknown")
        for pattern, matches in resolve_paths(base, entry.get("attestations", [])):
            if not matches:
                errors.append(f"phase {phase}: missing attestation '{pattern}'")
                continue
            errors.extend(validate_json_files(matches))

    return errors


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate attestation artifacts referenced by the vault manifest.")
    parser.add_argument(
        "--manifest",
        default="attest/archives/vault.manifest.yaml",
        help="Path to the vault manifest (default: %(default)s)",
    )
    parser.add_argument(
        "--schema-dir",
        default=None,
        help="Schema directory (unused placeholder, retained for manifest compatibility).",
    )
    parser.add_argument(
        "--logs",
        default=None,
        help="Logs directory (unused placeholder, retained for manifest compatibility).",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest).resolve()
    repo_root = manifest_path.parents[2]  # repository root

    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    manifest = load_manifest(manifest_path)
    errors = validate_attestations(manifest, repo_root)

    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        return 1

    print("All attestation artifacts validated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
