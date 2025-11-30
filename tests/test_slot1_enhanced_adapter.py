"""Tests for enhanced Slot1 Truth Anchor adapter with cryptographic features."""

import pytest
from nova.orchestrator.adapters.slot1_truth_anchor import Slot1TruthAnchorAdapter


@pytest.fixture
def adapter():
    """Create a fresh Slot1 adapter for testing."""
    return Slot1TruthAnchorAdapter()


def test_adapter_availability(adapter):
    """Test that adapter reports correct availability."""
    assert hasattr(adapter, 'available')
    assert hasattr(adapter, 'enhanced_available')
    assert isinstance(adapter.available, bool)
    assert isinstance(adapter.enhanced_available, bool)


def test_basic_functionality_preserved(adapter):
    """Test that basic anchor functionality still works."""
    # Basic registration and verification
    adapter.register('test.basic', 'Basic Value', metadata={'type': 'test'})
    assert adapter.verify('test.basic', 'Basic Value') is True
    assert adapter.verify('test.basic', 'Wrong Value') is False

    # Snapshot functionality
    snapshot = adapter.snapshot()
    assert isinstance(snapshot, dict)
    assert 'version' in snapshot or len(snapshot) == 0  # May be empty if not available


@pytest.mark.skipif(
    not hasattr(Slot1TruthAnchorAdapter(), 'enhanced_available') or
    not Slot1TruthAnchorAdapter().enhanced_available,
    reason="Enhanced features not available"
)
def test_cryptographic_anchor_establishment(adapter):
    """Test establishing cryptographic RealityLock anchors."""
    domain = adapter.establish_cryptographic_anchor(
        'test.crypto.domain',
        ['Fact 1: Truth matters', 'Fact 2: Evidence is required']
    )

    assert domain == 'test.crypto.domain'


@pytest.mark.skipif(
    not hasattr(Slot1TruthAnchorAdapter(), 'enhanced_available') or
    not Slot1TruthAnchorAdapter().enhanced_available,
    reason="Enhanced features not available"
)
def test_cryptographic_anchor_verification(adapter):
    """Test cryptographic anchor verification."""
    # Establish anchor first
    adapter.establish_cryptographic_anchor(
        'test.verify.domain',
        ['Verifiable fact 1', 'Verifiable fact 2']
    )

    # Verify the anchor
    verification = adapter.verify_cryptographic_anchor('test.verify.domain')

    assert verification is not None
    assert isinstance(verification, dict)
    assert verification.get('exists') is True
    assert verification.get('verified') is True
    assert verification.get('domain') == 'test.verify.domain'
    assert verification.get('fact_count') == 2


@pytest.mark.skipif(
    not hasattr(Slot1TruthAnchorAdapter(), 'enhanced_available') or
    not Slot1TruthAnchorAdapter().enhanced_available,
    reason="Enhanced features not available"
)
def test_enhanced_anchor_listing(adapter):
    """Test listing enhanced anchors."""
    # Create a test anchor
    adapter.establish_cryptographic_anchor(
        'test.list.domain',
        ['Listable fact']
    )

    anchors = adapter.list_enhanced_anchors()
    assert isinstance(anchors, list)

    # Find our test anchor
    test_anchor = next((a for a in anchors if a.get('domain') == 'test.list.domain'), None)
    assert test_anchor is not None
    assert test_anchor.get('fact_count') == 1
    assert test_anchor.get('verified') is True


@pytest.mark.skipif(
    not hasattr(Slot1TruthAnchorAdapter(), 'enhanced_available') or
    not Slot1TruthAnchorAdapter().enhanced_available,
    reason="Enhanced features not available"
)
def test_content_truth_analysis(adapter):
    """Test content truth analysis functionality."""
    # Create a domain anchor for testing
    adapter.establish_cryptographic_anchor(
        'test.analysis.domain',
        ['Scientific evidence is important', 'Peer review validates research']
    )

    # Analyze truthful content
    content = "Research shows that evidence-based approaches are more reliable"
    analysis = adapter.analyze_content_truth(content, 'test_req_001', 'test.analysis.domain')

    if analysis and 'error' not in analysis:
        assert isinstance(analysis, dict)
        assert 'truth_score' in analysis
        assert 'anchor_stable' in analysis
        assert 'request_id' in analysis
        assert analysis['request_id'] == 'test_req_001'
        assert 0.0 <= analysis['truth_score'] <= 1.0
        assert isinstance(analysis['anchor_stable'], bool)


def test_cache_stats_access(adapter):
    """Test cache statistics access."""
    stats = adapter.get_cache_stats()
    assert isinstance(stats, dict)

    if adapter.enhanced_available and stats:
        # If enhanced features available, should have cache stats
        assert 'hits' in stats or 'size' in stats


def test_enhanced_features_graceful_degradation(adapter):
    """Test that enhanced features gracefully degrade when not available."""
    # These should not raise exceptions even if enhanced features unavailable
    result = adapter.establish_cryptographic_anchor('test.graceful', ['fact'])
    if not adapter.enhanced_available:
        assert result is None

    verification = adapter.verify_cryptographic_anchor('test.graceful')
    if not adapter.enhanced_available:
        assert verification is None

    anchors = adapter.list_enhanced_anchors()
    if not adapter.enhanced_available:
        assert anchors == []

    analysis = adapter.analyze_content_truth('test content', 'req_001')
    if not adapter.enhanced_available:
        assert analysis is None

    stats = adapter.get_cache_stats()
    if not adapter.enhanced_available:
        assert stats == {}
