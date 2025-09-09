#!/usr/bin/env python3
"""
Local schema validation smoke test.
Usage: python scripts/validate-schemas.py
"""
import json
import pathlib
import sys
from jsonschema import Draft7Validator


def validate_schemas():
    """Validate all contract schemas are well-formed JSON Schema Draft-07"""
    schemas = [
        'contracts/slot3_health_schema.json',
        'contracts/slot6_cultural_profile_schema.json'
    ]
    
    validated = 0
    for schema_path in schemas:
        path = pathlib.Path(schema_path)
        if not path.exists():
            print(f"Schema missing: {schema_path}")
            continue
            
        try:
            schema = json.loads(path.read_text(encoding='utf-8'))
            Draft7Validator.check_schema(schema)
            print(f"OK schema: {schema_path}")
            validated += 1
        except Exception as e:
            print(f"Invalid schema {schema_path}: {e}")
            return False
    
    print(f"Validated {validated} schemas")
    return validated == len(schemas)


if __name__ == "__main__":
    success = validate_schemas()
    sys.exit(0 if success else 1)