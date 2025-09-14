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
    "slot07.cutover_tick",
    "slot07.health_summary",
    "slot07.public_metrics",
    "slot07.context_published",
    "slot07.internal_state",
    "slot06.synthesis_results",
    "slot06.cultural_profile",
    "slot06.adaptation_rate",
    "slot06.synthesis_complexity",
    "slot03.confidence_level",
    "slot03.emotional_state",
    "slot10.deployer"
}

# Valid key pattern (no stray 'test.' matches)
VALID_KEY_RE = re.compile(r"\bslot\d{2}\.[a-z0-9_]+(?:\.[a-z0-9_]+)*", re.I)

# Allowlisted test-only keys/prefixes
ALLOWED_TEST_KEYS = {"slot07.test_data", "slot07.rate_test", "slot07.test"}
ALLOWED_TEST_PREFIXES = ("slot07.test_",)

def _extract_keys_from_code():
    """Extract context keys from production code."""
    roots = [
        Path("orchestrator"),
        Path("slots"),
        Path("tests"),  # we do scan tests, but will filter allowlisted keys
    ]
    keys = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in VALID_KEY_RE.finditer(text):
                keys.add(m.group(0))
    # drop test-only keys/prefixes
    filtered = {
        k for k in keys
        if k not in ALLOWED_TEST_KEYS and not any(k.startswith(prefix) for prefix in ALLOWED_TEST_PREFIXES)
    }
    return filtered

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