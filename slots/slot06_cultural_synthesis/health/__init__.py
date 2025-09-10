# slots/slot06_cultural_synthesis/health/__init__.py
"""Health check for Slot 6 - Cultural Synthesis."""
from __future__ import annotations
import time
from pathlib import Path
import json

# fallbacks, in case schema file cannot be read in CI
_DEFAULT_SCHEMA_ID = "urn:nova:contracts:slot6_cultural_profile_schema@1"
_DEFAULT_SCHEMA_VERSION = "1"

def _load_slot6_schema_provenance():
    try:
        # adjust path if your repo layout differs
        schema_path = Path(__file__).resolve().parents[3] / "contracts" / "slot6_cultural_profile_schema.json"
        with schema_path.open("r", encoding="utf-8") as f:
            doc = json.load(f)
        schema_id = doc.get("$id", _DEFAULT_SCHEMA_ID)
        # If you store schema version as a property or top-level field, pick accordingly:
        schema_version = (
            doc.get("schema_version")
            or doc.get("$version")
            or _DEFAULT_SCHEMA_VERSION
        )
        return schema_id, schema_version
    except Exception:
        return _DEFAULT_SCHEMA_ID, _DEFAULT_SCHEMA_VERSION

def health() -> dict:
    """
    Health check for Slot 6 - Cultural Synthesis.
    """
    result = {
        "timestamp": time.time(),
        "self_check": "ok",
        "engine_status": "operational",
        "overall_status": "operational",
        "version": "v7.4.1"
    }
    
    try:
        # Test basic cultural synthesis functionality
        from slots.slot06_cultural_synthesis.multicultural_truth_synthesis import get_legacy_usage_count
        legacy_calls = get_legacy_usage_count()
        result["legacy_calls_total"] = legacy_calls
        result["basic_synthesis"] = "functional"
    except Exception as e:
        result["self_check"] = "error"
        result["engine_status"] = "failed"
        result["overall_status"] = "critical_failure"
        result["error"] = type(e).__name__
        result["message"] = str(e)
    
    # Always attach provenance
    schema_id, schema_version = _load_slot6_schema_provenance()
    result["schema_id"] = schema_id
    result["schema_version"] = schema_version
    
    return result

__all__ = ["health"]