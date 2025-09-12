"""Provenance utilities for contract schema tracking."""

from typing import Dict, Any

# Schema identifiers - these should match the actual $id in the JSON schemas
SLOT3_SCHEMA_ID = "https://github.com/PavlosKolivatzis/nova-civilizational-architecture/schemas/slot3_health_schema.json"
SLOT6_SCHEMA_ID = "https://github.com/PavlosKolivatzis/nova-civilizational-architecture/schemas/slot6_cultural_profile_schema.json"
SLOT7_SCHEMA_ID = "https://github.com/PavlosKolivatzis/nova-civilizational-architecture/schemas/slot7_production_controls_health_schema.json"

# Schema version - increment when breaking changes are made
SCHEMA_VERSION = "1"

def provenance(schema_id: str, version: str = SCHEMA_VERSION) -> Dict[str, Any]:
    """Generate standardized provenance block for health responses.
    
    Args:
        schema_id: The schema identifier (use SLOT*_SCHEMA_ID constants)
        version: Schema version (defaults to current SCHEMA_VERSION)
        
    Returns:
        Dictionary with schema_id and schema_version for contract tracking
    """
    return {
        "schema_id": schema_id,
        "schema_version": version
    }

# Convenience functions for common slots
def slot3_provenance() -> Dict[str, Any]:
    """Generate Slot 3 (Emotional Matrix) provenance block."""
    return provenance(SLOT3_SCHEMA_ID)

def slot6_provenance() -> Dict[str, Any]:
    """Generate Slot 6 (Cultural Synthesis) provenance block.""" 
    return provenance(SLOT6_SCHEMA_ID)

def slot7_provenance() -> Dict[str, Any]:
    """Generate Slot 7 (Production Controls) provenance block."""
    return provenance(SLOT7_SCHEMA_ID)