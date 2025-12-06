import os
import pytest
from src.nova.slots.slot02_deltathresh.core import DeltaThreshProcessor


class TestBiasVoidState:
    """VOID state handling for empty graphs."""

    def setup_method(self):
        os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)
        os.environ.pop('NOVA_ENABLE_VOID_MODE', None)

    def teardown_method(self):
        os.environ.pop('NOVA_ENABLE_BIAS_DETECTION', None)
        os.environ.pop('NOVA_ENABLE_VOID_MODE', None)

    def test_empty_graph_triggers_void_mode(self):
        os.environ["NOVA_ENABLE_BIAS_DETECTION"] = "1"
        processor = DeltaThreshProcessor()

        result = processor.process_content("")
        report = result.bias_report

        assert report["metadata"].get("graph_state") == "void"
        assert report["collapse_score"] == -0.5
        assert report["usm_metrics"]["equilibrium_ratio"] is None
        assert all(0.0 <= v <= 1.0 for v in report["bias_vector"].values())

    def test_non_empty_text_not_void(self):
        os.environ["NOVA_ENABLE_BIAS_DETECTION"] = "1"
        processor = DeltaThreshProcessor()

        result = processor.process_content("Nova thinks about safety.")
        report = result.bias_report

        assert report["metadata"].get("graph_state") != "void"

    def test_void_mode_can_be_disabled(self):
        os.environ["NOVA_ENABLE_BIAS_DETECTION"] = "1"
        os.environ["NOVA_ENABLE_VOID_MODE"] = "0"
        processor = DeltaThreshProcessor()

        result = processor.process_content("")
        report = result.bias_report

        assert report["metadata"].get("graph_state") != "void"
