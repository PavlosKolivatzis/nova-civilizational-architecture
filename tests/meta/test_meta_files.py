"""Meta file validation tests for consistent slot documentation."""
import yaml
import glob
import os

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


def test_meta_shape():
    """Test that all meta.yaml files have required keys and structure."""
    meta_files = list(glob.glob("slots/*/meta.yaml")) + ["meta.yaml"]

    assert meta_files, "No meta.yaml files found"

    for path in meta_files:
        with open(path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f)

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
    meta_files = list(glob.glob("slots/*/meta.yaml")) + ["meta.yaml"]

    for path in meta_files:
        with open(path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f)

        for flag in meta["feature_flags"]:
            assert flag in KNOWN_FEATURE_FLAGS, f"{path} unknown feature flag: {flag}"


def test_phase2_flag_mapping():
    """Test that Phase 2 slots have correct feature flag assignments."""
    expected_flags = {
        "slots/slot01_truth_anchor/meta.yaml": [],
        "slots/slot04_tri/meta.yaml": ["NOVA_ENABLE_TRI_LINK"],
        "slots/slot05_constellation/meta.yaml": ["NOVA_ENABLE_TRI_LINK"],
        "slots/slot09_distortion_protection/meta.yaml": ["NOVA_USE_SHARED_HASH"],
        "meta.yaml": ["NOVA_ENABLE_LIFESPAN", "NOVA_ENABLE_PROMETHEUS"],
        "slots/slot10_civilizational_deployment/meta.yaml": ["NOVA_USE_SHARED_HASH"]
    }

    for path, expected in expected_flags.items():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f)

            actual = meta["feature_flags"]
            assert actual == expected, f"{path} expected flags {expected}, got {actual}"