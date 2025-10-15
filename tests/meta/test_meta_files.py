"""Meta file validation tests for consistent slot documentation."""
import glob
import os
from typing import Dict, List

import yaml

REQUIRED_KEYS = {
    "name", "slug", "version", "description", "status", "feature_flags",
    "compat", "contracts", "dependencies"
}

VALID_STATUSES = {"alpha", "beta", "stable", "moderate", "deprecated"}

KNOWN_FEATURE_FLAGS = {
    "NOVA_ENABLE_TRI_LINK",
    "NOVA_ENABLE_LIFESPAN",
    "NOVA_USE_SHARED_HASH",
    "NOVA_ENABLE_PROMETHEUS",
}


def _discover_slot_meta_files() -> List[str]:
    """Return unique slot metadata paths preferring namespaced layout."""
    paths: List[str] = []
    seen: set[str] = set()
    for base in ("src/nova/slots", "slots"):
        pattern = os.path.join(base, "slot*/meta.yaml")
        for path in glob.glob(pattern):
            if path not in seen:
                paths.append(path)
                seen.add(path)
    return paths


def _load_meta(path: str) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_meta_shape():
    """Test that all meta.yaml files have required keys and structure."""
    meta_files = _discover_slot_meta_files() + ["meta.yaml"]

    assert meta_files, "No meta.yaml files found"

    for path in meta_files:
        meta = _load_meta(path)

        # Check required keys
        missing = REQUIRED_KEYS - set(meta.keys())
        assert not missing, f"{path} missing keys: {sorted(missing)}"

        # Validate structure
        assert isinstance(meta["feature_flags"], list), f"{path} feature_flags must be list"
        assert "min_version" in meta["compat"], f"{path} missing compat.min_version"
        assert isinstance(meta["contracts"], list), f"{path} contracts must be list"
        assert meta["contracts"], f"{path} needs at least one contract"
        assert meta["status"] in VALID_STATUSES, f"{path} invalid status: {meta['status']}"


def test_feature_flag_consistency():
    """Test that feature flags are from known set and properly documented."""
    meta_files = _discover_slot_meta_files() + ["meta.yaml"]

    for path in meta_files:
        meta = _load_meta(path)

        for flag in meta["feature_flags"]:
            assert flag in KNOWN_FEATURE_FLAGS, f"{path} unknown feature flag: {flag}"


def test_phase2_flag_mapping():
    """Test that Phase 2 slots have correct feature flag assignments."""
    expected_flags_by_slot = {
        "slot01_truth_anchor": [],
        "slot04_tri": ["NOVA_ENABLE_TRI_LINK"],
        "slot05_constellation": ["NOVA_ENABLE_TRI_LINK"],
        "slot09_distortion_protection": ["NOVA_USE_SHARED_HASH"],
        "slot10_civilizational_deployment": ["NOVA_USE_SHARED_HASH"],
    }

    def resolve_slot_meta(slot: str) -> str:
        for base in ("src/nova/slots", "slots"):
            candidate = os.path.join(base, slot, "meta.yaml")
            if os.path.exists(candidate):
                return candidate
        raise AssertionError(f"No metadata found for {slot}")

    root_expected = ["NOVA_ENABLE_LIFESPAN", "NOVA_ENABLE_PROMETHEUS"]
    assert os.path.exists("meta.yaml"), "Root meta.yaml missing"
    root_meta = _load_meta("meta.yaml")
    assert root_meta["feature_flags"] == root_expected, (
        f"meta.yaml expected flags {root_expected}, got {root_meta['feature_flags']}"
    )

    for slot, expected in expected_flags_by_slot.items():
        path = resolve_slot_meta(slot)
        meta = _load_meta(path)
        actual = meta["feature_flags"]
        assert actual == expected, f"{path} expected flags {expected}, got {actual}"
