import json
import pathlib


def test_slot3_schema_exists_and_is_json():
    """Guard test: ensures schema file exists and is valid JSON"""
    p = pathlib.Path("contracts/slot3_health_schema.json")
    assert p.is_file(), "Slot 3 health schema file missing"
    json.load(p.open("r", encoding="utf-8"))
