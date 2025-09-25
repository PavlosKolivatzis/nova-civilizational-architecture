"""Tests for smart TRI adapter routing between operational and content engines."""

from orchestrator.adapters.slot4_tri import Slot4TRIAdapter


def test_get_latest_report_uses_operational_engine(monkeypatch):
    """Test that get_latest_report routes to operational engine."""
    class Health:
        coherence = 0.91
        phase_jitter = 0.07
        tri_score = 0.88
        tri_mean = 0.87
        drift_z = 0.1
        n_samples = 128

    class OpEngine:
        def assess(self):
            return Health()

    adapter = Slot4TRIAdapter()
    monkeypatch.setattr(adapter, "_get_operational_engine", lambda: OpEngine())

    report = adapter.get_latest_report()
    assert report["coherence"] == 0.91
    assert report["tri_score"] == 0.88
    assert report["phase_jitter"] == 0.07
    assert report["tri_mean"] == 0.87
    assert report["drift_z"] == 0.1
    assert report["n_samples"] == 128


def test_get_latest_report_fallback():
    """Test get_latest_report falls back to safe defaults when engine unavailable."""
    adapter = Slot4TRIAdapter()

    # Force operational engine to be None
    adapter._operational_engine = False

    report = adapter.get_latest_report()
    assert report["coherence"] == 0.7
    assert report["phase_jitter"] == 0.15
    assert report["tri_score"] == 0.75


def test_calculate_routes_to_content_engine(monkeypatch):
    """Test that calculate routes to content analysis engine."""
    class ContentEngine:
        def calculate(self, content, context=None):
            return {
                "score": 0.77,
                "layer_scores": {"semantic": 0.8},
                "metadata": {"engine": "content"}
            }

    adapter = Slot4TRIAdapter()
    monkeypatch.setattr(adapter, "_get_content_engine", lambda: ContentEngine())

    result = adapter.calculate("test content")
    assert result["metadata"]["engine"] == "content"
    assert result["score"] == 0.77
    assert result["layer_scores"]["semantic"] == 0.8


def test_calculate_fallback_to_operational(monkeypatch):
    """Test calculate falls back to operational engine if content engine unavailable."""
    class OpEngine:
        def calculate(self, content):
            return {
                "score": 0.5,
                "layer_scores": {"structural": 0.6},
                "metadata": {"engine": "operational"}
            }

    adapter = Slot4TRIAdapter()
    monkeypatch.setattr(adapter, "_get_content_engine", lambda: None)
    monkeypatch.setattr(adapter, "_get_operational_engine", lambda: OpEngine())

    result = adapter.calculate("test content")
    assert result["metadata"]["engine"] == "operational"
    assert result["score"] == 0.5


def test_calculate_final_fallback(monkeypatch):
    """Test calculate final fallback when no engines available."""
    adapter = Slot4TRIAdapter()
    monkeypatch.setattr(adapter, "_get_content_engine", lambda: None)
    monkeypatch.setattr(adapter, "_get_operational_engine", lambda: None)

    result = adapter.calculate("test content")
    assert result["metadata"]["fallback"] is True
    assert result["metadata"]["reason"] == "No TRI engines available"
    assert result["score"] == 0.0
    assert result["layer_scores"]["structural"] == 0.0


def test_engine_caching():
    """Test that engines are cached after first load."""
    adapter = Slot4TRIAdapter()

    # First call should attempt to load
    assert adapter._operational_engine is None
    adapter._get_operational_engine()
    # Should now be cached (either engine instance or False)
    assert adapter._operational_engine is not None

    # Same for content engine
    assert adapter._content_engine is None
    adapter._get_content_engine()
    assert adapter._content_engine is not None


def test_engine_exception_handling():
    """Test that engine load exceptions are handled gracefully."""
    class BrokenEngine:
        def assess(self):
            raise RuntimeError("Engine broken")

        def calculate(self, content):
            raise RuntimeError("Calculate broken")

    adapter = Slot4TRIAdapter()

    # Mock operational engine that throws on assess()
    adapter._operational_engine = BrokenEngine()
    report = adapter.get_latest_report()
    # Should fall back to defaults
    assert report["coherence"] == 0.7
    assert report["tri_score"] == 0.75

    # Mock content engine that throws on calculate()
    adapter._content_engine = BrokenEngine()
    result = adapter.calculate("test")
    # Should attempt operational fallback, which also throws, then final fallback
    assert result["metadata"]["fallback"] is True


def test_safe_attribute_extraction():
    """Test safe extraction of attributes from Health object."""
    class PartialHealth:
        coherence = 0.85
        # Missing other attributes

    class OpEngine:
        def assess(self):
            return PartialHealth()

    adapter = Slot4TRIAdapter()
    adapter._operational_engine = OpEngine()

    report = adapter.get_latest_report()
    assert report["coherence"] == 0.85
    assert report["phase_jitter"] == 0.15  # default
    assert report["tri_score"] == 0.75    # default
    assert report["tri_mean"] is None     # default for missing attrs