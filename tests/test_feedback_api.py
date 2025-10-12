"""Tests for deployment feedback structure and API integration."""

import pytest

from nova.slots.slot09_distortion_protection.hybrid_api import (
    HybridDistortionDetectionAPI,
    HybridApiConfig,
)


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


@pytest.mark.asyncio
async def test_report_deployment_feedback():
    api = HybridDistortionDetectionAPI(core_detector=None, config=HybridApiConfig())
    await api.report_deployment_feedback(
        "deploy-1",
        {
            "status": "success",
            "measured_threat_level": 0.1,
            "prediction_accuracy": 0.9,
            "false_positives": 0.0,
            "false_negatives": 0.0,
            "insights": "ok",
        },
    )
    assert api.last_deployment_feedback["deployment_id"] == "deploy-1"
    assert (
        api.last_deployment_feedback["actual_impact"]["measured_threat_level"]
        == 0.1
    )
