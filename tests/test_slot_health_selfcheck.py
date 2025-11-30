"""
Test for slot health self-check functionality.
"""
from unittest.mock import patch, MagicMock
from nova.orchestrator.health import collect_slot_selfchecks, clear_slot_health_cache


def test_collect_slot_selfchecks():
    """Test collection of slot self-checks."""
    # Clear cache to ensure clean test state
    clear_slot_health_cache()

    slot_registry = {
        "slot01_truth_anchor": lambda: None,
        "slot06_cultural_synthesis": lambda: None,
        "nonexistent_slot": lambda: None,
    }

    # Mock import for existing slots
    with patch("importlib.import_module") as mock_import:
        mock_health = MagicMock()
        mock_health.health.return_value = {"self_check": "ok", "status": "operational"}
        def side_effect(name):
            if "nonexistent_slot" in name:
                raise ImportError("not found")
            return mock_health
        mock_import.side_effect = side_effect

        results = collect_slot_selfchecks(slot_registry)

        assert "slot01_truth_anchor" in results
        assert "slot06_cultural_synthesis" in results
        assert "nonexistent_slot" in results

        assert results["slot01_truth_anchor"]["self_check"] == "ok"
        assert results["nonexistent_slot"]["self_check"] == "n/a"


def test_slot_health_error_handling():
    """Test error handling in slot health collection."""
    # Clear cache to ensure clean test state
    clear_slot_health_cache()

    slot_registry = {"slot01_truth_anchor": lambda: None}

    with patch("importlib.import_module") as mock_import:
        mock_import.side_effect = Exception("Import failed")

        results = collect_slot_selfchecks(slot_registry)

        assert results["slot01_truth_anchor"]["self_check"] == "error"
        assert "Import failed" in results["slot01_truth_anchor"]["reason"]
