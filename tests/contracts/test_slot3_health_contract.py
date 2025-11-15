# tests/contracts/test_slot3_health_contract.py
from pathlib import Path
import json
from jsonschema import validate  # dev dep: jsonschema>=4
from nova.slots.slot03_emotional_matrix.health import health

def test_slot3_health_matches_contract():
    schema = json.loads(Path("contracts/slot3_health_schema.json").read_text(encoding="utf-8"))
    payload = health()
    validate(instance=payload, schema=schema)
