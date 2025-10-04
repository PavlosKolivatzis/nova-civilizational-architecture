"""
Test .env.example documentation completeness.

Validates that all environment variables used in code are documented in .env.example.
Prevents DEF-005 regression (undocumented env vars).
"""
import re
from pathlib import Path
import pytest


def test_env_example_documents_all_env_vars():
    """Verify every os.getenv() call has corresponding .env.example entry"""

    # Collect all env vars from code
    code_env_vars = set()
    py_files = list(Path('.').rglob('*.py'))

    for py_file in py_files:
        # Skip venv, node_modules, __pycache__, test files
        if any(x in str(py_file) for x in ['.venv', 'venv', 'node_modules', '__pycache__', 'test_env_documentation.py']):
            continue

        try:
            content = py_file.read_text(encoding='utf-8')
            # Match os.getenv("VAR_NAME") or os.getenv('VAR_NAME')
            matches = re.findall(r'os\.getenv\(["\']([^"\']+)["\']', content)
            code_env_vars.update(matches)
        except Exception:
            continue

    # Collect all documented vars from .env.example
    env_example_path = Path('.env.example')
    if not env_example_path.exists():
        pytest.fail(".env.example file not found")

    documented_vars = set()
    for line in env_example_path.read_text(encoding='utf-8').splitlines():
        # Match VAR_NAME= at start of line
        match = re.match(r'^([A-Z_][A-Z0-9_]*)=', line)
        if match:
            documented_vars.add(match.group(1))

    # Check for undocumented vars
    undocumented = code_env_vars - documented_vars

    assert not undocumented, (
        f"Environment variables used in code but not documented in .env.example: {sorted(undocumented)}\n"
        f"Found {len(code_env_vars)} vars in code, {len(documented_vars)} documented\n"
        f"Add missing variables to .env.example with descriptions and defaults"
    )


def test_no_orphaned_env_documentation():
    """Verify .env.example doesn't document unused variables"""

    # Collect all env vars from code
    code_env_vars = set()
    py_files = list(Path('.').rglob('*.py'))

    for py_file in py_files:
        if any(x in str(py_file) for x in ['.venv', 'venv', 'node_modules', '__pycache__', 'test_env_documentation.py']):
            continue

        try:
            content = py_file.read_text(encoding='utf-8')
            matches = re.findall(r'os\.getenv\(["\']([^"\']+)["\']', content)
            code_env_vars.update(matches)
        except Exception:
            continue

    # Collect documented vars
    env_example_path = Path('.env.example')
    documented_vars = set()
    for line in env_example_path.read_text(encoding='utf-8').splitlines():
        match = re.match(r'^([A-Z_][A-Z0-9_]*)=', line)
        if match:
            documented_vars.add(match.group(1))

    # Check for orphaned documentation
    orphaned = documented_vars - code_env_vars

    assert not orphaned, (
        f"Environment variables documented in .env.example but not used in code: {sorted(orphaned)}\n"
        f"Remove obsolete documentation or add usage in code"
    )


def test_env_example_has_comments():
    """Verify .env.example has inline documentation for variables"""

    env_example_path = Path('.env.example')
    content = env_example_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    # Count vars with preceding comments
    vars_with_comments = 0
    total_vars = 0

    for i, line in enumerate(lines):
        # Check if this line is a var declaration
        if re.match(r'^[A-Z_][A-Z0-9_]*=', line):
            total_vars += 1

            # Check if previous line is a comment
            if i > 0 and lines[i-1].strip().startswith('#'):
                vars_with_comments += 1

    # Require at least 80% of vars to have comments
    comment_ratio = vars_with_comments / total_vars if total_vars > 0 else 0

    assert comment_ratio >= 0.8, (
        f"Only {vars_with_comments}/{total_vars} variables ({comment_ratio:.1%}) have documentation comments\n"
        f"Add inline comments explaining each variable's purpose"
    )


def test_env_example_organized_by_sections():
    """Verify .env.example uses section headers for organization"""

    env_example_path = Path('.env.example')
    content = env_example_path.read_text(encoding='utf-8')

    # Look for section headers (lines with only # and -)
    section_headers = [
        line for line in content.splitlines()
        if re.match(r'^# -+$', line)
    ]

    # Require at least 10 sections for 142 variables
    assert len(section_headers) >= 10, (
        f"Only {len(section_headers)} section headers found in .env.example\n"
        f"Use section headers (# ---) to organize variables by category"
    )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
