"""Ensure policy actions map to expected base threat levels."""

import pytest

from slots.slot09_distortion_protection.hybrid_api import (
    HybridDistortionDetectionAPI,
    HybridApiConfig,
    PolicyAction,
)

@pytest.mark.parametrize(
    "policy_action,expected",
    [
        (PolicyAction.ALLOW_FASTPATH, 0.1),
        (PolicyAction.ALLOW_WITH_MONITORING, 0.2),
        (PolicyAction.STANDARD_PROCESSING, 0.3),
        (PolicyAction.STAGED_DEPLOYMENT, 0.5),
        (PolicyAction.RESTRICTED_SCOPE_DEPLOYMENT, 0.6),
        (PolicyAction.DEGRADE_AND_REVIEW, 0.7),
        (PolicyAction.BLOCK_OR_SANDBOX, 0.9),
    ],
)
def test_policy_threat_mapping_consistency(policy_action, expected):
    api = HybridDistortionDetectionAPI(core_detector=None, config=HybridApiConfig())
    policy_result = {
        "final_policy": policy_action.value,
        "traits_analysis": {"stability": 1.0, "drift": 0.0},
        "content_analysis": {"stability": 1.0, "drift": 0.0},
    }
    threat = api._calculate_sophisticated_threat_level(policy_result)
    assert threat == expected
