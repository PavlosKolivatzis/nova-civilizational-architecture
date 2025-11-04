"""Tests for ledger alert rules (Phase 15-7)."""

import yaml


def test_ledger_alert_rules_valid_yaml():
    """Verify ledger.rules.yml is valid YAML."""
    with open("monitoring/alerts/ledger.rules.yml", "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)

    assert "groups" in rules
    assert len(rules["groups"]) > 0


def test_ledger_alert_rules_structure():
    """Verify ledger alert rules have required structure."""
    with open("monitoring/alerts/ledger.rules.yml", "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)

    group = rules["groups"][0]
    assert group["name"] == "nova_ledger_alerts"
    assert "interval" in group
    assert "rules" in group

    alert_names = {rule["alert"] for rule in group["rules"]}
    assert "NovaLedgerFederationDivergence" in alert_names
    assert "NovaLedgerHeadStalled" in alert_names


def test_ledger_recording_rules_valid_yaml():
    """Verify ledger.recording.yml is valid YAML."""
    with open("monitoring/recording/ledger.recording.yml", "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)

    assert "groups" in rules
    assert len(rules["groups"]) > 0


def test_ledger_recording_rules_structure():
    """Verify ledger recording rules have required structure."""
    with open("monitoring/recording/ledger.recording.yml", "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)

    group = rules["groups"][0]
    assert group["name"] == "nova_ledger_recording"
    assert "interval" in group
    assert "rules" in group

    record_names = {rule["record"] for rule in group["rules"]}
    assert "nova_ledger_federation_gap_abs:5m_avg" in record_names
    assert "nova_ledger_head_age_seconds:5m_avg" in record_names


def test_ledger_alert_rules_have_annotations():
    """Verify all ledger alerts have summary and description."""
    with open("monitoring/alerts/ledger.rules.yml", "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)

    for rule in rules["groups"][0]["rules"]:
        assert "annotations" in rule
        assert "summary" in rule["annotations"]
        assert "description" in rule["annotations"]
        assert len(rule["annotations"]["summary"]) > 0
        assert len(rule["annotations"]["description"]) > 0


def test_ledger_alert_rules_have_labels():
    """Verify all ledger alerts have severity and component labels."""
    with open("monitoring/alerts/ledger.rules.yml", "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)

    for rule in rules["groups"][0]["rules"]:
        assert "labels" in rule
        assert "severity" in rule["labels"]
        assert "component" in rule["labels"]
        assert rule["labels"]["component"] == "ledger"
