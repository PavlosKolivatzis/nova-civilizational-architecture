import pytest

from slots.slot02_deltathresh.core import DeltaThreshProcessor
from slots.slot02_deltathresh.config import ProcessingConfig


class MockAnchor:
    def __init__(self, status):
        self.status = status

    def get_anchor_status(self):
        return self.status


class FailingAnchor:
    def get_anchor_status(self):
        raise RuntimeError("anchor link down")


def test_sync_with_anchor_adjusts_tri_lock():
    processor = DeltaThreshProcessor(ProcessingConfig())
    anchor = MockAnchor(
        {
            "anchor_state": "locked",
            "tri_lock": 0.97,
            "constellation_position": "A1",
        }
    )
    result = processor.sync_with_anchor_system(anchor)
    assert result["sync_successful"] is True
    assert result["tri_lock_status"] == 0.97
    assert processor.config.tri_strict_mode is True
    assert processor.config.tri_min_score == pytest.approx(0.92)


def test_sync_with_anchor_handles_missing_system():
    processor = DeltaThreshProcessor(ProcessingConfig())
    result = processor.sync_with_anchor_system(None)
    assert result["sync_successful"] is False
    assert result["error"] == "No anchor system provided"
    assert processor.config.tri_strict_mode is False
    assert processor.config.tri_min_score == pytest.approx(0.90)


def test_sync_with_anchor_failure_graceful():
    processor = DeltaThreshProcessor(ProcessingConfig())
    anchor = FailingAnchor()
    result = processor.sync_with_anchor_system(anchor)
    assert result["sync_successful"] is False
    assert "anchor link down" in result["error"]
    assert processor.config.tri_strict_mode is False
    assert processor.config.tri_min_score == pytest.approx(0.90)
