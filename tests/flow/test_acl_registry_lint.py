"""ACL registry linter - validates context keys against documentation."""
import re
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
    # Slot04 TRI coherence signals (ADR-012)
    "slot04.coherence",
    "slot04.phase_coherence",
    "slot04.phase_jitter",
    "slot06.cultural_profile",
    "slot06.adaptation_rate",
    "slot06.synthesis_complexity",
    "slot03.confidence_level",
    "slot03.emotional_state",
    "slot03.phase_lock",
    "slot10.deployer",
    "slot05.adaptation_event",
    "slot05.constellation_mapped",
    # Slot 8 Memory Lock & IDS health metrics for deployment gates
    "slot08.integrity_score",
    "slot08.quarantine_active",
    "slot08.recent_recoveries",
    "slot08.checksum_mismatch",
    "slot08.tamper_evidence",
    # Slot 4 TRI Engine health metrics for deployment gates
    "slot04.safe_mode_active",
    "slot04.drift_z",
    "slot04.tri_drift_z",
    "slot04.tri_score",
    # Phase lock and policy metrics for Light-Clock deployment gates
    "slot07.phase_lock",
    "slot09.final_policy",
    # Phase 4.1 inter-slot coordination keys
    "slot07.backpressure",
    "slot10.deployment_feedback",
    # Phase 5.0 Adaptive Neural Routing keys
    "router.anr_shadow_decision",
    "router.anr_live_decision",
    "router.current_decision_id",
    "router.anr_reward_immediate",
    "router.anr_reward_deployment",
    "router.anr_explain"
}

# Valid key pattern (no stray 'test.' matches)
VALID_KEY_RE = re.compile(r"\b(?:slot\d{2}|router)\.[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*\b")

# Mirror API call patterns to extract actual context keys
PUBLISH_RE = re.compile(r'publish\(\s*["\']((?: slot\d{2}|router)\.[a-z0-9_.]+)["\']', re.I)
GET_RE     = re.compile(r'get_context\(\s*["\']((?: slot\d{2}|router)\.[a-z0-9_.]+)["\']', re.I)
QUERY_RE   = re.compile(r'query\(\s*["\']((?: slot\d{2}|router)\.[a-z0-9_.]+)["\']', re.I)

# Allowlisted test-only keys/prefixes
ALLOWED_TEST_KEYS = {"slot07.test_data", "slot07.rate_test", "slot07.test", "slot04.get", "slot08.get"}
ALLOWED_TEST_PREFIXES = ("slot07.test_",)

def _extract_keys_from_code():
    """Only capture context keys actually passed to mirror APIs."""
    roots = [Path("orchestrator"), Path("slots"), Path("tests")]  # existing roots
    found_keys = set()
    for root in roots:
        if not root.exists():
            continue
        for pyfile in root.rglob("*.py"):
            try:
                content = pyfile.read_text(encoding="utf-8")
                for rx in (PUBLISH_RE, GET_RE, QUERY_RE):
                    for m in rx.finditer(content):
                        k = m.group(1)
                        if k == k.lower() and VALID_KEY_RE.match(k):
                            found_keys.add(k)
            except Exception:
                continue

    # Remove allowlisted test keys
    filtered_keys = set()
    for key in found_keys:
        if key in ALLOWED_TEST_KEYS:
            continue
        if any(key.startswith(prefix) for prefix in ALLOWED_TEST_PREFIXES):
            continue
        filtered_keys.add(key)

    return filtered_keys


def test_acl_registry_coverage():
    """Ensure all context keys are documented and no unknown keys exist."""
    code_keys = _extract_keys_from_code()

    # Hard failure: unknown keys in code
    unknown_keys = code_keys - DOCUMENTED_KEYS
    assert not unknown_keys, f"Undocumented context keys found: {sorted(unknown_keys)}"

    # Soft warning: documented keys not found in code
    unused_keys = DOCUMENTED_KEYS - code_keys
    if unused_keys:
        print(f"Warning: Documented keys not found in code: {sorted(unused_keys)}")


def test_acl_key_format():
    """Test that all documented keys follow proper naming convention."""
    for key in DOCUMENTED_KEYS:
        assert VALID_KEY_RE.match(key), f"Invalid key format: {key}"
        assert key.startswith(("slot", "router")), f"Key should start with 'slot' or 'router': {key}"


if __name__ == "__main__":
    test_acl_registry_coverage()
    test_acl_key_format()
    print("✅ ACL registry validation passed")
