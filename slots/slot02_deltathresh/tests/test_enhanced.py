from slots.slot02_deltathresh.enhanced.config import EnhancedProcessingConfig
from slots.slot02_deltathresh.enhanced.processor import EnhancedDeltaThreshProcessor
from slots.slot02_deltathresh.config import OperationalMode, ProcessingMode


def test_pass_through_mode_allows_all():
    cfg = EnhancedProcessingConfig(
        operational_mode=OperationalMode.PASS_THROUGH,
        processing_mode=ProcessingMode.QUARANTINE_ONLY,
        quarantine_enabled=False,
        pattern_neutralization_enabled=False,
    )
    processor = EnhancedDeltaThreshProcessor(cfg)
    res = processor.process_content("test content")
    assert res.action == "allow"
    assert res.reason_codes == []
    assert res.tri_score == 1.0


def test_status_reporting_uses_metrics_alias():
    """Enhanced tracker should expose the core get_metrics interface."""
    processor = EnhancedDeltaThreshProcessor()

    base_status = processor.get_status()
    enhanced_status = processor.get_enhanced_status()

    assert "performance_metrics" in base_status
    assert base_status["performance_metrics"]["total_processed"] == 0
    assert "enhanced_version" in enhanced_status
