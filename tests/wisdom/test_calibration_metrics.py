"""Test calibration infrastructure for Phase 15-8.3."""

from __future__ import annotations

import pathlib

import yaml


def test_wisdom_recording_rules_load():
    """Test that wisdom recording rules YAML loads correctly."""
    path = pathlib.Path("monitoring/recording/wisdom.recording.yml")
    assert path.exists(), "wisdom.recording.yml not found"

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "groups" in data, "Missing 'groups' key in YAML"

    groups = {g["name"] for g in data.get("groups", [])}
    assert "wisdom-recording" in groups, "Missing 'wisdom-recording' group"


def test_wisdom_recording_rules_completeness():
    """Test that key recording rules are present."""
    path = pathlib.Path("monitoring/recording/wisdom.recording.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    # Extract all record names
    rules = [r["record"] for g in data["groups"] for r in g.get("rules", [])]

    # Core metrics that must be recorded
    expected = {
        "nova_wisdom_eta_current_avg_5m",
        "nova_wisdom_stability_margin_mean_5m",
        "nova_wisdom_stability_margin_min_1m",
        "nova_wisdom_hopf_distance_min_5m",
        "nova_wisdom_eta_clamped_ratio_5m",
    }

    assert expected.issubset(set(rules)), f"Missing rules: {expected - set(rules)}"


def test_wisdom_recording_interval():
    """Test that recording interval is set appropriately."""
    path = pathlib.Path("monitoring/recording/wisdom.recording.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    wisdom_group = next(g for g in data["groups"] if g["name"] == "wisdom-recording")
    interval = wisdom_group.get("interval")

    # Should be 15s or 30s for calibration (frequent enough to catch transients)
    assert interval in ["15s", "30s"], f"Unexpected interval: {interval}"


def test_wisdom_recording_rules_have_valid_expr():
    """Test that all recording rules have non-empty expr."""
    path = pathlib.Path("monitoring/recording/wisdom.recording.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    for group in data["groups"]:
        for rule in group.get("rules", []):
            assert "record" in rule, f"Rule missing 'record' field: {rule}"
            assert "expr" in rule, f"Rule {rule['record']} missing 'expr' field"
            assert len(rule["expr"]) > 0, f"Rule {rule['record']} has empty expr"
