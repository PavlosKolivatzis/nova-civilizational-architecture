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
