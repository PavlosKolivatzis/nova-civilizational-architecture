from slots.slot04_tri.engine import TRIEngine
from slots.slot02_deltathresh.enhanced.processor import (
    EnhancedDeltaThreshProcessor,
    EnhancedProcessingConfig,
)


def test_slot2_prefers_slot4_engine():
    cfg = EnhancedProcessingConfig()
    eng = TRIEngine()
    p = EnhancedDeltaThreshProcessor(cfg, slot4_engine=eng)

    hi = p.process_content("evidence suggests this might be true", "unit")
    lo = p.process_content("this is an undeniable truth everyone knows", "unit")

    assert hi.tri_score > lo.tri_score
    assert {"delta", "sigma", "theta", "omega"} <= set(hi.layer_scores.keys())
