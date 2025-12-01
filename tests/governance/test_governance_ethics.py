from nova.orchestrator.governance.ethics import evaluate_ethics


def test_ethics_checks_fail_for_invalid_state():
    state = {
        "consent_profile": "CE999",
        "disclosure": "partial",
        "relational_honesty": False,
        "dominance_factor": 1.0,
    }
    checks = evaluate_ethics(state)
    assert any(not check.passed for check in checks)


def test_ethics_checks_pass_for_default_state():
    checks = evaluate_ethics({})
    assert all(check.passed for check in checks)
