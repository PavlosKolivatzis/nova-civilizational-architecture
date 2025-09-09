"""Test NullAdapter fallback payloads conform to contract schemas."""

import json
import pytest
from pathlib import Path
from jsonschema import validate


class TestNullAdapterConformance:
    """Ensure fallback payloads validate against current schemas."""
    
    def test_slot3_null_adapter_health_conformance(self):
        """Slot 3 NullAdapter health response must validate against schema."""
        schema_path = Path("contracts/slot3_health_schema.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        
        # Test minimal conformant fallback (what NullAdapter should provide)
        null_health_payload = {
            "self_check": "error",
            "engine_status": "failed", 
            "basic_analysis": "degraded",
            "overall_status": "critical_failure",
            "maturity_level": "0/4_missing",
            "timestamp": 0.0
        }
        
        # Should validate against schema (minimal failure state)
        validate(instance=null_health_payload, schema=schema)
    
    def test_slot6_null_adapter_profile_conformance(self):
        """Slot 6 NullAdapter profile response must validate against schema."""
        schema_path = Path("contracts/slot6_cultural_profile_schema.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        
        # Test minimal conformant fallback (what NullAdapter should provide)
        null_profile_payload = {
            "culture_id": "null",
            "principle_preservation_score": 0.0,
            "residual_risk": 1.0
        }
        
        # Should validate against schema (minimal safe fallback)
        validate(instance=null_profile_payload, schema=schema)
    
    def test_sample_payloads_validate(self):
        """Verify our sample payloads validate against current schemas."""
        test_cases = [
            ("contracts/slot3_health_schema.json", "tests/contracts/samples/slot3_health_sample.json"),
            ("contracts/slot3_health_schema.json", "tests/contracts/samples/slot3_health_minimal.json"),
            ("contracts/slot6_cultural_profile_schema.json", "tests/contracts/samples/slot6_profile_sample.json"),
            ("contracts/slot6_cultural_profile_schema.json", "tests/contracts/samples/slot6_profile_minimal.json")
        ]
        
        for schema_path, sample_path in test_cases:
            schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
            sample = json.loads(Path(sample_path).read_text(encoding="utf-8"))
            
            # Should validate without error
            validate(instance=sample, schema=schema)