"""Coverage tests for Slot 9 shared hash integration."""

import pytest
import os
from unittest.mock import patch


def test_slot9_hybrid_api_imports():
    """Test that Slot 9 hybrid API imports without errors."""
    from slots.slot09_distortion_protection.hybrid_api import (
        HybridDistortionDetectionAPI,
        create_hybrid_slot9_api,
        create_production_config,
        create_development_config
    )

    # Test factory functions
    config = create_development_config()
    assert config is not None

    # Test API creation
    api = create_hybrid_slot9_api(config=config)
    assert api is not None
    assert hasattr(api, '_add_hash_chain')


def test_shared_hash_availability_detection():
    """Test that shared hash availability is properly detected."""
    from slots.slot09_distortion_protection.hybrid_api import (
        SHARED_HASH_AVAILABLE,
        NOVA_USE_SHARED_HASH
    )

    # SHARED_HASH_AVAILABLE should be a boolean
    assert isinstance(SHARED_HASH_AVAILABLE, bool)

    # NOVA_USE_SHARED_HASH should reflect environment variable
    assert isinstance(NOVA_USE_SHARED_HASH, bool)


def test_audit_hash_chain_with_shared_hash_disabled():
    """Test audit hash chain when shared hash is disabled."""
    from slots.slot09_distortion_protection.hybrid_api import (
        create_hybrid_slot9_api,
        create_development_config
    )

    with patch.dict(os.environ, {'NOVA_USE_SHARED_HASH': 'false'}):
        api = create_hybrid_slot9_api(config=create_development_config())

        # Create test audit trail
        audit_trail = {
            "trace_id": "test_trace_123",
            "timestamp": "2025-01-15T10:00:00Z",
            "policy_decision": "STANDARD_PROCESSING",
            "decision_reason": "test_processing",
            "compliance_markers": ["TEST_MARKER"],
            "processing_path": "test_path",
            "processing_time_ms": 100
        }

        # Test hash chain generation
        result = api._add_hash_chain(audit_trail)

        assert "hash_signature" in result
        assert "previous_event_hash" in result
        assert "retention_policy" in result
        assert result["hash_method"] == "fallback_sha256"
        assert result["hash_signature"].startswith("sha256:")


def test_audit_hash_chain_with_shared_hash_enabled():
    """Test audit hash chain when shared hash is enabled and available."""
    from slots.slot09_distortion_protection.hybrid_api import (
        create_hybrid_slot9_api,
        create_development_config,
        SHARED_HASH_AVAILABLE
    )

    if not SHARED_HASH_AVAILABLE:
        pytest.skip("Shared hash utility not available")

    with patch.dict(os.environ, {'NOVA_USE_SHARED_HASH': 'true'}):
        api = create_hybrid_slot9_api(config=create_development_config())

        # Create test audit trail
        audit_trail = {
            "trace_id": "test_trace_456",
            "timestamp": "2025-01-15T10:00:00Z",
            "policy_decision": "ALLOW_WITH_MONITORING",
            "decision_reason": "test_monitoring",
            "compliance_markers": ["SHARED_HASH_TEST"],
            "processing_path": "shared_path",
            "processing_time_ms": 50,
            "api_version": "3.1.0-hybrid"
        }

        # Test hash chain generation
        result = api._add_hash_chain(audit_trail)

        assert "hash_signature" in result
        assert "previous_event_hash" in result
        assert "retention_policy" in result
        assert result["hash_method"] == "shared_blake2b"
        # Shared hash should not have sha256: prefix
        assert not result["hash_signature"].startswith("sha256:")


def test_hash_chain_state_persistence():
    """Test that hash chain state persists across multiple calls."""
    from slots.slot09_distortion_protection.hybrid_api import (
        create_hybrid_slot9_api,
        create_development_config
    )

    api = create_hybrid_slot9_api(config=create_development_config())

    # First audit trail
    audit1 = {
        "trace_id": "chain_test_1",
        "timestamp": "2025-01-15T10:00:00Z",
        "policy_decision": "STANDARD_PROCESSING",
        "decision_reason": "first_call",
        "processing_time_ms": 25
    }

    result1 = api._add_hash_chain(audit1)
    first_hash = result1["hash_signature"]

    # Second audit trail
    audit2 = {
        "trace_id": "chain_test_2",
        "timestamp": "2025-01-15T10:01:00Z",
        "policy_decision": "ALLOW_FASTPATH",
        "decision_reason": "second_call",
        "processing_time_ms": 15
    }

    result2 = api._add_hash_chain(audit2)

    # Second result should reference first hash
    assert result2["previous_event_hash"] == first_hash
    assert result2["hash_signature"] != first_hash  # Should be different


def test_api_version_consistency():
    """Test that API version is consistent across components."""
    from slots.slot09_distortion_protection.hybrid_api import HybridDistortionDetectionAPI

    api = HybridDistortionDetectionAPI()

    assert hasattr(api, 'VERSION')
    assert hasattr(api, 'FORMAT_VERSION')
    assert hasattr(api, 'COMPATIBILITY_LEVEL')

    # Version should be non-empty strings
    assert isinstance(api.VERSION, str) and api.VERSION
    assert isinstance(api.FORMAT_VERSION, str) and api.FORMAT_VERSION
    assert isinstance(api.COMPATIBILITY_LEVEL, str) and api.COMPATIBILITY_LEVEL


def test_environment_flag_variations():
    """Test different environment variable values for shared hash."""
    from slots.slot09_distortion_protection.hybrid_api import create_hybrid_slot9_api

    # Test various truthy values
    truthy_values = ["1", "true", "TRUE", "yes", "YES", "on", "ON"]

    for value in truthy_values:
        with patch.dict(os.environ, {'NOVA_USE_SHARED_HASH': value}):
            # Should not raise any errors
            api = create_hybrid_slot9_api()
            assert api is not None

    # Test falsy values
    falsy_values = ["", "0", "false", "FALSE", "no", "NO", "off", "OFF"]

    for value in falsy_values:
        with patch.dict(os.environ, {'NOVA_USE_SHARED_HASH': value}):
            # Should not raise any errors
            api = create_hybrid_slot9_api()
            assert api is not None


def test_hash_signature_format():
    """Test that hash signatures follow expected format."""
    from slots.slot09_distortion_protection.hybrid_api import (
        create_hybrid_slot9_api,
        create_development_config
    )

    api = create_hybrid_slot9_api(config=create_development_config())

    audit_trail = {
        "trace_id": "format_test",
        "timestamp": "2025-01-15T10:00:00Z",
        "policy_decision": "STANDARD_PROCESSING",
        "processing_time_ms": 10
    }

    result = api._add_hash_chain(audit_trail)

    # Hash signature should be non-empty string
    assert isinstance(result["hash_signature"], str)
    assert len(result["hash_signature"]) > 0

    # Should have hash method indication
    assert "hash_method" in result
    assert result["hash_method"] in ["shared_blake2b", "fallback_sha256"]


def test_compliance_markers_in_audit_trail():
    """Test that compliance markers are properly handled in audit trails."""
    from slots.slot09_distortion_protection.hybrid_api import (
        create_hybrid_slot9_api,
        create_development_config
    )

    api = create_hybrid_slot9_api(config=create_development_config())

    # Test with compliance markers
    audit_trail = {
        "trace_id": "compliance_test",
        "timestamp": "2025-01-15T10:00:00Z",
        "policy_decision": "BLOCK_OR_SANDBOX",
        "compliance_markers": ["HIGH_THREAT_BLOCKED", "SYSTEMATIC_MANIPULATION"],
        "processing_time_ms": 75
    }

    result = api._add_hash_chain(audit_trail)

    # Original compliance markers should be preserved
    assert "compliance_markers" in result
    assert result["compliance_markers"] == ["HIGH_THREAT_BLOCKED", "SYSTEMATIC_MANIPULATION"]

    # Hash should be computed properly
    assert "hash_signature" in result
    assert len(result["hash_signature"]) > 0