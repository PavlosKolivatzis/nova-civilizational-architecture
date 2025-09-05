from slots.slot02_deltathresh.enhanced.processor import EnhancedDeltaThreshProcessor


def test_enhanced_tri_score_regression():
    """Enhanced TRI should rank coherent text higher than manipulative text."""
    processor = EnhancedDeltaThreshProcessor()

    high_quality = (
        "Research suggests this approach may be effective based on preliminary data."
    )
    low_quality = "This is absolutely undeniable and everyone knows it's true."

    high_score = processor._calculate_tri_score(high_quality)
    low_score = processor._calculate_tri_score(low_quality)

    assert 0.0 <= high_score <= 1.0
    assert 0.0 <= low_score <= 1.0
    assert high_score > low_score
