#!/usr/bin/env python3
"""Check for merge integrity issues after cross-platform merge."""

import os
import sys
from pathlib import Path
from collections import defaultdict
import difflib

def check_for_duplicates():
    """Check for duplicate files and directories."""
    print("=== CHECKING FOR DUPLICATE FILES ===")

    file_hashes = defaultdict(list)
    duplicate_files = []

    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') or file.endswith('.yaml') or file.endswith('.md'):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        file_hash = hash(content)
                        file_hashes[file_hash].append(str(file_path))
                except (IOError, OSError):
                    continue

    # Find duplicates
    for file_hash, files in file_hashes.items():
        if len(files) > 1:
            print(f"Duplicate files found:")
            for file_path in files:
                print(f"  - {file_path}")
            duplicate_files.extend(files)

    if not duplicate_files:
        print("[OK] No duplicate files found")

    return duplicate_files

def check_directory_structure():
    """Check for suspicious directory structures."""
    print("\n=== CHECKING DIRECTORY STRUCTURE ===")

    dirs = set()
    suspicious_dirs = []

    for root, dirnames, files in os.walk('.'):
        for dirname in dirnames:
            dir_path = Path(root) / dirname
            normalized = str(dir_path).replace('\\', '/')
            dirs.add(normalized)

            # Check for duplicate directory names
            dirname_only = dirname
            similar_dirs = [d for d in dirs if d != normalized and Path(d).name == dirname_only]
            if similar_dirs:
                print(f"Suspicious directory: {normalized} (similar to {similar_dirs})")
                suspicious_dirs.append(normalized)

    if not suspicious_dirs:
        print("[OK] No suspicious directory structures found")

    return suspicious_dirs

def check_line_endings():
    """Check for mixed line ending issues."""
    print("\n=== CHECKING LINE ENDINGS ===")

    mixed_files = []

    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') or file.endswith('.yaml') or file.endswith('.md'):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()

                    # Check for CRLF and LF in same file
                    has_crlf = b'\r\n' in content
                    has_lf = content.count(b'\n') - content.count(b'\r\n')

                    if has_crlf and has_lf > 0:
                        print(f"Mixed line endings in: {file_path}")
                        mixed_files.append(str(file_path))

                except (IOError, OSError):
                    continue

    if not mixed_files:
        print("[OK] No mixed line ending files found")

    return mixed_files

def check_merge_artifacts():
    """Check for remaining merge artifacts."""
    print("\n=== CHECKING FOR MERGE ARTIFACTS ===")

    artifacts = []

    for root, dirs, files in os.walk('.'):
        for file in files:
            file_path = Path(root) / file

            # Check for conflict markers
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if '<<<<<<<' in content or '>>>>>>>' in content or '=======' in content:
                    print(f"Merge conflict markers in: {file_path}")
                    artifacts.append(str(file_path))

            except (IOError, OSError, UnicodeDecodeError):
                continue

    if not artifacts:
        print("[OK] No merge artifacts found")

    return artifacts

def check_critical_files():
    """Check that critical project files exist."""
    print("\n=== CHECKING CRITICAL FILES ===")

    critical_files = [
        'README.md',
        'requirements.txt',
        'pyproject.toml',
        'src/nova/__init__.py',
        'tests/test_*.py',
    ]

    missing_files = []

    for pattern in critical_files:
        if '*' in pattern:
            # Handle glob patterns
            import glob
            matches = glob.glob(pattern, recursive=True)
            if not matches:
                print(f"No files matching pattern: {pattern}")
                missing_files.append(pattern)
        else:
            if not os.path.exists(pattern):
                print(f"Missing critical file: {pattern}")
                missing_files.append(pattern)

    if not missing_files:
        print("[OK] All critical files present")

    return missing_files

def main():
    """Main check function."""
    print("NOVA CIVILIZATIONAL ARCHITECTURE - MERGE INTEGRITY CHECK")
    print("=" * 60)

    duplicate_files = check_for_duplicates()
    suspicious_dirs = check_directory_structure()
    mixed_files = check_line_endings()
    merge_artifacts = check_merge_artifacts()
    missing_files = check_critical_files()

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"  - Duplicate files: {len(duplicate_files)}")
    print(f"  - Suspicious directories: {len(suspicious_dirs)}")
    print(f"  - Mixed line ending files: {len(mixed_files)}")
    print(f"  - Merge artifacts: {len(merge_artifacts)}")
    print(f"  - Missing critical files: {len(missing_files)}")

    if not any([duplicate_files, suspicious_dirs, mixed_files, merge_artifacts, missing_files]):
        print("\n[SUCCESS] MERGE INTEGRITY CHECK PASSED - No issues found!")
        return 0
    else:
        print("\nWARNING: MERGE INTEGRITY ISSUES DETECTED - Review above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
