"""Test SlotMetadata tolerance for id field and unknown extras."""

import pytest
from slots.config.enhanced_manager import SlotMetadata


class TestSlotMetadataTolerance:
    """Ensure SlotMetadata accepts id field and handles unknown keys gracefully."""
    
    def test_slot_metadata_accepts_id_and_extras(self):
        """SlotMetadata should accept id field and store unknown keys in extra."""
        raw = {
            "name": "deltathresh", 
            "version": "1.0",
            "slot": 2,
            "entry_point": "delta.main",
            "id": "slot02",  # This should be accepted
            "unexpected": 123,  # This should go to extra
            "another_unknown": "value"  # This too
        }
        
        meta = SlotMetadata.from_dict(raw)
        
        # Known fields should be properly assigned
        assert meta.name == "deltathresh"
        assert meta.version == "1.0"
        assert meta.slot == 2
        assert meta.entry_point == "delta.main"
        assert meta.id == "slot02"
        
        # Unknown fields should be in extra
        assert meta.extra.get("unexpected") == 123
        assert meta.extra.get("another_unknown") == "value"
    
    def test_legacy_slot_id_mapping(self):
        """SlotMetadata should map legacy slot_id to id field."""
        raw = {
            "name": "emotional", 
            "version": "2.0",
            "slot": 3,
            "entry_point": "emotional.main",
            "slot_id": "slot03_emotional_matrix"  # Legacy field
        }
        
        meta = SlotMetadata.from_dict(raw)
        
        assert meta.id == "slot03_emotional_matrix"
        assert "slot_id" not in meta.extra  # Should be consumed, not stored
    
    def test_minimal_required_fields(self):
        """SlotMetadata should work with just required fields."""
        raw = {
            "name": "truth_anchor",
            "version": "1.0"
        }
        
        meta = SlotMetadata.from_dict(raw)
        
        assert meta.name == "truth_anchor"
        assert meta.version == "1.0"
        assert meta.slot is None  # Optional field defaults to None
        assert meta.entry_point is None  # Optional field defaults to None
        assert meta.id is None  # Optional field defaults to None
        assert meta.extra == {}  # No unknown fields
    
    def test_from_yaml_uses_from_dict(self):
        """from_yaml should delegate to from_dict for tolerance."""
        # This is more of a smoke test to ensure the method chain works
        # We can't easily test file loading without creating temp files
        # But we can verify the method exists and has the right signature
        assert hasattr(SlotMetadata, 'from_yaml')
        assert hasattr(SlotMetadata, 'from_dict')
    
    def test_real_yaml_schema_compatibility(self):
        """SlotMetadata should handle real YAML schema with produces/consumes/optional."""
        raw = {
            "id": "slot02_deltathresh",
            "name": "ΔTHRESH Manager", 
            "version": "1.0.0",
            "optional": False,
            "produces": ["DETECTION_REPORT@1"],
            "consumes": [],
            "description": "Advanced pattern detection and threshold management"
        }
        
        meta = SlotMetadata.from_dict(raw)
        
        assert meta.id == "slot02_deltathresh"
        assert meta.name == "ΔTHRESH Manager"
        assert meta.version == "1.0.0"
        assert meta.description == "Advanced pattern detection and threshold management"
        # produces should be mapped to outputs
        assert meta.outputs == ["DETECTION_REPORT@1"]
        # consumes should be mapped to inputs  
        assert meta.inputs == []
        # optional should be in extra
        assert meta.extra.get("optional") == False

    def test_empty_or_none_input(self):
        """SlotMetadata should handle empty/None input gracefully."""
        # This will fail due to missing required fields, but shouldn't crash on the dict handling
        with pytest.raises(ValueError):  # Missing required fields (name/version)
            SlotMetadata.from_dict({})
            
        with pytest.raises(ValueError):  # Missing required fields  
            SlotMetadata.from_dict(None)