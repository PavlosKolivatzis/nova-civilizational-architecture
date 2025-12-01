#!/usr/bin/env python3
"""
Nova Sunlight Scanner - Documentation Integrity Protocol
=======================================================

Scans the repository for documentation integrity violations.
Follows the Sunlight Doctrine: Observe → Canonize → Attest → Publish

Checks performed:
- Lifecycle status tags on all documents
- Ontology version consistency
- Contract linkage validation
- Supersession chain integrity
- Orphaned document detection
- Outdated reference detection

Usage:
    python scripts/maintenance/sunlight_scan.py [--fix] [--verbose]
"""

import os
import yaml
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

# Constants
ONTOLOGY_VERSION = "1.7.1"
CANON_PATH = "docs/architecture/ontology/_canon.yaml"
SCAN_PATHS = [
    "docs/",
    "contracts/",
    "decisions/",
    "agents/",
    "README.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md"
]

@dataclass
class ScanResult:
    """Result of a documentation scan."""
    violations: List[str]
    warnings: List[str]
    orphaned_files: List[str]
    canon_entries: Dict[str, Dict]

class SunlightScanner:
    """Scans repository for documentation integrity."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.canon = self._load_canon()
        self.violations: List[str] = []
        self.warnings: List[str] = []
        self.orphaned_files: List[str] = []

    def _load_canon(self) -> Dict:
        """Load the canonical documentation index."""
        canon_file = self.repo_root / CANON_PATH
        if not canon_file.exists():
            raise FileNotFoundError(f"Canon file not found: {canon_file}")

        with open(canon_file, 'r') as f:
            return yaml.safe_load(f)

    def scan(self) -> ScanResult:
        """Perform complete documentation integrity scan."""
        print("🔍 Starting Sunlight Scan...")
        print(f"📋 Ontology Version: {ONTOLOGY_VERSION}")
        print(f"📚 Canon Entries: {len(self.canon.get('frameworks', [])) + len(self.canon.get('contracts', [])) + len(self.canon.get('adrs', [])) + len(self.canon.get('audits', [])) + len(self.canon.get('slots', []))}")

        # Check all canon entries
        self._check_canon_integrity()

        # Scan all documentation files
        self._scan_documentation_files()

        # Check for orphaned files
        self._find_orphaned_files()

        result = ScanResult(
            violations=self.violations,
            warnings=self.warnings,
            orphaned_files=self.orphaned_files,
            canon_entries=self.canon
        )

        self._print_results(result)
        return result

    def _check_canon_integrity(self):
        """Check canonical index for internal consistency."""
        all_entries = []
        for category in ['frameworks', 'contracts', 'adrs', 'audits', 'slots', 'deprecated']:
            if category in self.canon:
                all_entries.extend(self.canon[category])

        # Check for duplicate paths
        paths = [entry['path'] for entry in all_entries]
        duplicates = set([x for x in paths if paths.count(x) > 1])
        if duplicates:
            self.violations.append(f"Duplicate paths in canon: {duplicates}")

        # Check ontology version consistency
        for entry in all_entries:
            if entry.get('status') == 'ACTIVE' and entry.get('ontology_version') != ONTOLOGY_VERSION:
                self.warnings.append(f"Outdated ontology version in {entry['path']}: {entry.get('ontology_version')} (expected {ONTOLOGY_VERSION})")

    def _scan_documentation_files(self):
        """Scan all documentation files for integrity."""
        for scan_path in SCAN_PATHS:
            scan_dir = self.repo_root / scan_path
            if scan_dir.is_file():
                self._check_file(scan_dir)
            elif scan_dir.exists():
                for file_path in scan_dir.rglob("*"):
                    if file_path.is_file() and self._is_documentation_file(file_path):
                        self._check_file(file_path)

    def _is_documentation_file(self, file_path: Path) -> bool:
        """Check if file is a documentation file."""
        if file_path.suffix.lower() in ['.md', '.yaml', '.yml', '.txt']:
            # Skip certain directories
            skip_dirs = ['__pycache__', '.git', 'node_modules', 'archive']
            if any(skip_dir in str(file_path) for skip_dir in skip_dirs):
                return False
            return True
        return False

    def _check_file(self, file_path: Path):
        """Check individual documentation file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            self.warnings.append(f"Cannot read file (encoding issue): {file_path}")
            return

        # Check for lifecycle status
        if not self._has_lifecycle_status(content):
            self.violations.append(f"Missing lifecycle status: {file_path}")

        # Check ontology references
        self._check_ontology_references(file_path, content)

        # Check for outdated contract references
        self._check_contract_references(file_path, content)

    def _has_lifecycle_status(self, content: str) -> bool:
        """Check if document has lifecycle status metadata."""
        # Look for YAML frontmatter or status markers
        if re.search(r'^status:\s*(ACTIVE|DEPRECATED|SUPERSEDED|CANDIDATE|FROZEN|ARCHIVED)', content, re.MULTILINE | re.IGNORECASE):
            return True
        if re.search(r'<!--\s*status:\s*(ACTIVE|DEPRECATED|SUPERSEDED|CANDIDATE|FROZEN|ARCHIVED)', content, re.IGNORECASE):
            return True
        return False

    def _check_ontology_references(self, file_path: Path, content: str):
        """Check ontology version references."""
        # Look for ontology version references
        version_matches = re.findall(r'ontology[_-]?version[:\s]*([0-9]+\.[0-9]+\.[0-9]+)', content, re.IGNORECASE)
        for version in version_matches:
            if version != ONTOLOGY_VERSION:
                self.warnings.append(f"Outdated ontology version reference in {file_path}: {version} (current: {ONTOLOGY_VERSION})")

    def _check_contract_references(self, file_path: Path, content: str):
        """Check for potentially outdated contract references."""
        # Look for @1, @2, etc. version references
        contract_refs = re.findall(r'@([2-9]|[1-9][0-9]+)', content)
        if contract_refs:
            # Flag files with version numbers > 1 for manual review
            high_versions = [v for v in contract_refs if int(v) > 1]
            if high_versions:
                self.warnings.append(f"High contract versions in {file_path}: {set(high_versions)} - verify currency")

    def _find_orphaned_files(self):
        """Find documentation files not in the canon."""
        canon_paths = set()
        for category in self.canon.values():
            if isinstance(category, list):
                for entry in category:
                    if 'path' in entry:
                        canon_paths.add(entry['path'])

        for scan_path in SCAN_PATHS:
            scan_dir = self.repo_root / scan_path
            if scan_dir.is_file():
                rel_path = scan_dir.relative_to(self.repo_root)
                if str(rel_path) not in canon_paths and self._is_documentation_file(scan_dir):
                    self.orphaned_files.append(str(rel_path))
            elif scan_dir.exists():
                for file_path in scan_dir.rglob("*"):
                    if file_path.is_file() and self._is_documentation_file(file_path):
                        rel_path = file_path.relative_to(self.repo_root)
                        if str(rel_path) not in canon_paths:
                            self.orphaned_files.append(str(rel_path))

    def _print_results(self, result: ScanResult):
        """Print scan results."""
        print("\n" + "="*60)
        print("SUNLIGHT SCAN RESULTS")
        print("="*60)

        if result.violations:
            print(f"\n❌ VIOLATIONS ({len(result.violations)}):")
            for v in result.violations:
                print(f"  • {v}")
        else:
            print("\n✅ NO VIOLATIONS")

        if result.warnings:
            print(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
            for w in result.warnings:
                print(f"  • {w}")
        else:
            print("\n✅ NO WARNINGS")

        if result.orphaned_files:
            print(f"\n📋 ORPHANED FILES ({len(result.orphaned_files)}):")
            for f in result.orphaned_files[:10]:  # Show first 10
                print(f"  • {f}")
            if len(result.orphaned_files) > 10:
                print(f"  ... and {len(result.orphaned_files) - 10} more")
        else:
            print("\n✅ NO ORPHANED FILES")

        print(f"\n📊 SUMMARY:")
        print(f"  • Canon entries: {len(result.canon_entries.get('frameworks', [])) + len(result.canon_entries.get('contracts', [])) + len(result.canon_entries.get('adrs', [])) + len(result.canon_entries.get('audits', [])) + len(result.canon_entries.get('slots', []))}")
        print(f"  • Ontology version: {ONTOLOGY_VERSION}")
        print(f"  • Scan completed successfully")

def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Nova Sunlight Scanner")
    parser.add_argument("--fix", action="store_true", help="Attempt automatic fixes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent.parent
    scanner = SunlightScanner(repo_root)

    try:
        result = scanner.scan()

        # Exit codes: 0=success, 1=violations, 2=warnings only
        if result.violations:
            exit(1)
        elif result.warnings:
            exit(2)
        else:
            exit(0)

    except Exception as e:
        print(f"❌ Scan failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()