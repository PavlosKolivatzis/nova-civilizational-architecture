"""ACL registry linter - validates context keys against documentation."""
import re
import pytest
from pathlib import Path

# Known keys from docs/semantic_mirror_acl.md
DOCUMENTED_KEYS = {
    "slot07.breaker_state",
    "slot07.pressure_level",
    "slot07.resource_status",
    "slot07.heartbeat",
    "slot07.cutover_tick"
}

def _extract_keys_from_code():
    """Extract context keys from production code."""
    keys_found = set()

    # Scan orchestrator and slots for publish/get_context calls
    code_paths = [
        "orchestrator/",
        "slots/",
        "scripts/",
        "tests/"
    ]

    pattern = r'(?:publish_context|get_context|query_context_keys)\s*\(\s*["\']([^"\']+)["\']'

    for path_str in code_paths:
        path = Path(path_str)
        if path.exists():
            for py_file in path.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    matches = re.findall(pattern, content)
                    keys_found.update(matches)
                except (UnicodeDecodeError, PermissionError):
                    continue

    return keys_found

def test_acl_registry_coverage():
    """Ensure all context keys are documented and no unknown keys exist."""
    code_keys = _extract_keys_from_code()

    # Hard failure: unknown keys in code
    unknown_keys = code_keys - DOCUMENTED_KEYS
    assert not unknown_keys, f"Undocumented context keys found: {sorted(unknown_keys)}"

def test_acl_registry_staleness():
    """Warn about documented keys not found in code (potential cleanup needed)."""
    code_keys = _extract_keys_from_code()

    # Soft warning: documented but unused keys
    unused_docs = DOCUMENTED_KEYS - code_keys
    if unused_docs:
        pytest.xfail(f"Documented keys not found in code: {sorted(unused_docs)}")