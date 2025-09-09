import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = Path("contracts/slot6_cultural_profile_schema.json")


@pytest.mark.parametrize(
    "payload",
    [
        {
            "culture_id": "default",
            "principle_preservation_score": 0.72,
            "residual_risk": 0.31,
            "schema_version": "1",
            "source_slot": "slot06_cultural_synthesis",
            "timestamp": 1735689600.0,
        },
        # minimal required
        {
            "culture_id": "eu-west",
            "principle_preservation_score": 0.5,
            "residual_risk": 0.5
        },
    ],
)
def test_slot6_cultural_profile_schema(payload):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=payload, schema=schema)


def test_bounds_enforced():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    # out-of-bounds values should fail
    bad = {
        "culture_id": "x",
        "principle_preservation_score": 1.1,
        "residual_risk": -0.2
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)


def test_no_extra_fields():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    bad = {
        "culture_id": "x",
        "principle_preservation_score": 0.5,
        "residual_risk": 0.5,
        "unexpected": "nope"
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)