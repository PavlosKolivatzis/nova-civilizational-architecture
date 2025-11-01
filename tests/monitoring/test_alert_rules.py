"""Basic validation for federation alert rule definitions."""

from pathlib import Path

import yaml


def test_federation_alert_rules_load():
    """Ensure federation alert rules parse and contain expected structure."""
    rules_path = Path("monitoring/alerts/federation.rules.yml")
    assert rules_path.exists(), "Federation alert rules file missing"

    data = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "Rules file must deserialize into a dict"
    groups = data.get("groups")
    assert isinstance(groups, list) and groups, "At least one alert group required"

    # Federation group must exist with rules
    federation_groups = [g for g in groups if g.get("name") == "federation"]
    assert federation_groups, "Federation alert group not found"

    for group in federation_groups:
        rules = group.get("rules")
        assert isinstance(rules, list) and rules, "Federation group must define rules"
        for rule in rules:
            assert "alert" in rule and rule["alert"].startswith(
                "NovaFederation"
            ), "Alert names must start with NovaFederation"
            assert "expr" in rule, f"Expression missing for alert {rule.get('alert')}"
