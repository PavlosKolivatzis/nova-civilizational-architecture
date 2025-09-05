from slots.slot02_deltathresh.core import DeltaThreshProcessor
from slots.slot02_deltathresh.config import ProcessingConfig

def test_integration_shape_and_reason_codes():
    p = DeltaThreshProcessor(ProcessingConfig())
    r = p.process_content("As proven above, this validates our claim. Everyone knows it.")
    assert isinstance(r.reason_codes, list)
    assert isinstance(r.layer_scores, dict)
    assert "theta".upper() in " ".join(r.reason_codes) or "omega".upper() in " ".join(r.reason_codes)
