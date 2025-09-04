"""Tests for deployment feedback structure."""


def generate_mock_feedback():
    return {
        "deployment_feedback": {
            "deployment_id": "deployment-123",
            "outcome": "success",
            "actual_impact": {
                "measured_threat_level": 0.2,
                "prediction_accuracy": 0.95,
                "false_positive_rate": 0.0,
                "false_negative_rate": 0.0,
            },
            "lessons_learned": {
                "summary": "All good",
                "recommendations": [],
                "escalation_needed": False,
            },
        }
    }


def test_feedback_structure():
    payload = generate_mock_feedback()
    assert "deployment_feedback" in payload
    feedback = payload["deployment_feedback"]
    assert "actual_impact" in feedback
    assert "lessons_learned" in feedback
    assert isinstance(feedback["actual_impact"], dict)
    assert isinstance(feedback["lessons_learned"], dict)
