"""Test META_LENS_REPORT@1 contract schema validation."""

import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError


@pytest.fixture
def meta_lens_schema():
    """Load META_LENS_REPORT@1 schema."""
    schema_path = Path(__file__).parent.parent.parent / "contracts" / "meta_lens_report@1.json"
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture
def valid_meta_lens_report():
    """Valid META_LENS_REPORT@1 instance."""
    return {
        "schema_version": "1.0.0",
        "timestamp": "2025-09-22T10:15:00Z",
        "lightclock_tick": 1284,
        "source_slot": "S2",
        "input_reference": "sha256:5f4dcc3b5aa765d61d8327deb882cf99e6b1f3c7a0b123456789abcdef",
        "meta_lens_analysis": {
            "cognitive_level": "synthesis",
            "lenses_applied": ["Bloom_Critical", "DeltaC_Systemic", "Cultural_Historical", "Manipulation_Audit"],
            "state_vector": [0.85, 0.73, 0.12, 0.91, 0.25, 0.15],
            "manipulative_patterns": {
                "detected": [
                    {"id": "INF-14", "name": "Source Laundering", "severity": 0.70, "confidence": 0.86}
                ],
                "confidence": 0.82,
                "cross_validation_source": "INF-o-INITY"
            },
            "cultural_overlay": {
                "historical_context": "Post-1990 institutional consolidation; lobbying normalization 2005–2020.",
                "cultural_bias_markers": ["Consensus_Building", "Privacy_Priority"],
                "synthesis_confidence": 0.91
            }
        },
        "iteration": {
            "epoch": 2,
            "max_iters": 3,
            "alpha": 0.5,
            "epsilon": 0.02,
            "converged": True,
            "residual": 0.018,
            "frozen_inputs": {
                "padel_ref": "req_abc123",
                "infinity_ref": "req_def456"
            },
            "watchdog": {
                "distortion_overall": 0.25,
                "emotional_volatility": 0.15,
                "abort_triggered": False
            }
        },
        "risk_assessment": {
            "level": "medium",
            "vectors": ["structural_capture", "lobbying_opacity"],
            "mitigation_suggestions": ["surface_origins", "require_cross_family_anchors"]
        },
        "notes": ["Iteration reached fixed point under α=0.5; residual < ε."],
        "integrity": {
            "hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "signed_by": "slot01_truth_anchor",
            "timestamp": "2025-09-22T10:15:01Z"
        }
    }


def test_valid_meta_lens_report(meta_lens_schema, valid_meta_lens_report):
    """Test that valid report passes schema validation."""
    validate(instance=valid_meta_lens_report, schema=meta_lens_schema)


def test_required_fields_missing(meta_lens_schema, valid_meta_lens_report):
    """Test that missing required fields fail validation."""
    # Remove required field
    incomplete_report = valid_meta_lens_report.copy()
    del incomplete_report["meta_lens_analysis"]

    with pytest.raises(ValidationError):
        validate(instance=incomplete_report, schema=meta_lens_schema)


def test_state_vector_constraints(meta_lens_schema, valid_meta_lens_report):
    """Test state vector length and value constraints."""
    report = valid_meta_lens_report.copy()

    # Test wrong length
    report["meta_lens_analysis"]["state_vector"] = [0.5, 0.3]  # Too short
    with pytest.raises(ValidationError):
        validate(instance=report, schema=meta_lens_schema)

    # Test values out of range
    report["meta_lens_analysis"]["state_vector"] = [1.5, 0.73, 0.12, 0.91, 0.25, 0.15]  # > 1.0
    with pytest.raises(ValidationError):
        validate(instance=report, schema=meta_lens_schema)


def test_iteration_convergence_fields(meta_lens_schema, valid_meta_lens_report):
    """Test iteration and convergence field validation."""
    report = valid_meta_lens_report.copy()

    # Test alpha out of range
    report["iteration"]["alpha"] = 1.5  # > 1.0
    with pytest.raises(ValidationError):
        validate(instance=report, schema=meta_lens_schema)

    # Test epsilon out of range
    report["iteration"]["alpha"] = 0.5  # Reset
    report["iteration"]["epsilon"] = 0.15  # > 0.1
    with pytest.raises(ValidationError):
        validate(instance=report, schema=meta_lens_schema)


def test_integrity_hash_pattern(meta_lens_schema, valid_meta_lens_report):
    """Test integrity hash format validation."""
    report = valid_meta_lens_report.copy()

    # Test invalid hash format
    report["integrity"]["hash"] = "invalid_hash_format"
    with pytest.raises(ValidationError):
        validate(instance=report, schema=meta_lens_schema)

    # Test valid hash format
    report["integrity"]["hash"] = "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    validate(instance=report, schema=meta_lens_schema)  # Should pass


def test_cognitive_level_enum(meta_lens_schema, valid_meta_lens_report):
    """Test cognitive level enum validation."""
    report = valid_meta_lens_report.copy()

    # Test invalid cognitive level
    report["meta_lens_analysis"]["cognitive_level"] = "invalid_level"
    with pytest.raises(ValidationError):
        validate(instance=report, schema=meta_lens_schema)

    # Test all valid levels
    valid_levels = ["analysis", "synthesis", "evaluation", "creation"]
    for level in valid_levels:
        report["meta_lens_analysis"]["cognitive_level"] = level
        validate(instance=report, schema=meta_lens_schema)  # Should pass


def test_lens_uniqueness(meta_lens_schema, valid_meta_lens_report):
    """Test that lenses_applied requires unique items."""
    report = valid_meta_lens_report.copy()

    # Test duplicate lenses
    report["meta_lens_analysis"]["lenses_applied"] = ["Bloom_Critical", "Bloom_Critical"]
    with pytest.raises(ValidationError):
        validate(instance=report, schema=meta_lens_schema)


def test_watchdog_abort_scenario(meta_lens_schema, valid_meta_lens_report):
    """Test watchdog abort triggered scenario."""
    report = valid_meta_lens_report.copy()

    # Simulate abort scenario
    report["iteration"]["watchdog"]["distortion_overall"] = 0.85  # > 0.75 threshold
    report["iteration"]["watchdog"]["abort_triggered"] = True
    report["iteration"]["converged"] = False

    validate(instance=report, schema=meta_lens_schema)  # Should still be valid schema


def test_minimal_required_report(meta_lens_schema):
    """Test minimal report with only required fields."""
    minimal_report = {
        "schema_version": "1.0.0",
        "timestamp": "2025-09-22T10:15:00Z",
        "source_slot": "S2",
        "input_reference": "sha256:abc123",
        "meta_lens_analysis": {
            "cognitive_level": "analysis",
            "lenses_applied": ["Bloom_Critical"],
            "state_vector": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        },
        "iteration": {
            "epoch": 0,
            "max_iters": 3,
            "alpha": 0.5,
            "epsilon": 0.02,
            "converged": False,
            "residual": 0.05,
            "frozen_inputs": {
                "padel_ref": "req_123",
                "infinity_ref": "req_456"
            }
        },
        "risk_assessment": {
            "level": "low",
            "vectors": []
        },
        "integrity": {
            "hash": "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "signed_by": "slot01_truth_anchor",
            "timestamp": "2025-09-22T10:15:01Z"
        }
    }

    validate(instance=minimal_report, schema=meta_lens_schema)
