"""Comprehensive tests for Slot 5 Constellation Engine."""
import pytest
from unittest.mock import MagicMock, patch

from slots.slot05_constellation.constellation_engine import ConstellationEngine
from orchestrator.adapters.slot5_constellation import Slot5ConstellationAdapter


class TestConstellationEngine:
    """Test the core ConstellationEngine functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ConstellationEngine()
    
    def test_empty_input(self):
        """Test handling of empty input."""
        result = self.engine.map([])
        
        assert result["constellation"] == []
        assert result["links"] == []
        assert result["stability"]["status"] == "empty"
        assert result["stability"]["score"] == 1.0
        assert result["metadata"]["item_count"] == 0
    
    def test_single_item(self):
        """Test constellation with single item."""
        items = ["hello world"]
        result = self.engine.map(items)
        
        assert len(result["constellation"]) == 1
        assert len(result["links"]) == 0  # No links possible with one item
        assert result["constellation"][0]["content"] == "hello world"
        assert result["constellation"][0]["id"] == 0
        assert "position" in result["constellation"][0]
        assert result["metadata"]["item_count"] == 1
    
    def test_multiple_items_similar(self):
        """Test constellation with similar items that should link."""
        items = [
            "fix the error in the code",
            "solution to fix the bug", 
            "resolve the issue quickly"
        ]
        result = self.engine.map(items)
        
        assert len(result["constellation"]) == 3
        assert len(result["links"]) > 0  # Should have links between similar items
        assert result["metadata"]["item_count"] == 3
        
        # Check link properties
        for link in result["links"]:
            assert "source" in link
            assert "target" in link
            assert "strength" in link
            assert "type" in link
            assert 0 <= link["strength"] <= 1
    
    def test_multiple_items_dissimilar(self):
        """Test constellation with dissimilar items that shouldn't link."""
        items = [
            "apple fruit red sweet",
            "database query optimization", 
            "mountain climbing adventure"
        ]
        result = self.engine.map(items)
        
        assert len(result["constellation"]) == 3
        # May or may not have links depending on similarity threshold
        assert result["metadata"]["item_count"] == 3
    
    def test_item_type_classification(self):
        """Test that items are classified correctly by type."""
        items = [
            "error in the system",           # problem
            "solution to fix it",            # solution
            "process the data carefully",    # process
            "metric shows 85% accuracy",     # data
            "general concept discussion"     # concept
        ]
        result = self.engine.map(items)
        
        types = [item["type"] for item in result["constellation"]]
        assert "problem" in types
        assert "solution" in types
        assert "process" in types
        assert "data" in types
        assert "concept" in types
    
    def test_position_calculation(self):
        """Test that positions are calculated correctly."""
        items = ["item1", "item2", "item3", "item4"]
        result = self.engine.map(items)
        
        positions = [item["position"] for item in result["constellation"]]
        
        # All positions should be within bounds [0,1] x [0,1]
        for pos in positions:
            assert 0 <= pos["x"] <= 1
            assert 0 <= pos["y"] <= 1
        
        # Positions should be distributed (not all the same)
        x_coords = [pos["x"] for pos in positions]
        assert len(set(x_coords)) > 1  # At least some variation
    
    def test_similarity_calculation(self):
        """Test similarity calculation between items."""
        # Direct test of similarity calculation
        sim1 = self.engine._calculate_similarity("hello world", "hello universe")
        sim2 = self.engine._calculate_similarity("completely different", "totally unrelated")
        
        assert sim1 > sim2  # Similar items should have higher similarity
        assert 0 <= sim1 <= 1
        assert 0 <= sim2 <= 1
    
    def test_link_type_detection(self):
        """Test link type detection between items."""
        # Test problem-solution relationship
        link_type = self.engine._determine_link_type("error in code", "fix the solution")
        assert link_type == "solution"
        
        # Test default conceptual relationship
        link_type = self.engine._determine_link_type("general topic", "related concept")
        assert link_type == "conceptual"
    
    def test_stability_metrics(self):
        """Test stability metrics calculation."""
        items = ["stable item one", "stable item two", "stable item three"]
        result = self.engine.map(items)
        
        stability = result["stability"]
        assert "score" in stability
        assert "status" in stability
        assert "density" in stability
        assert "connectivity" in stability
        assert 0 <= stability["score"] <= 1
        assert stability["status"] in ["stable", "moderate", "unstable", "critical"]
    
    def test_stability_history_tracking(self):
        """Test that stability history is tracked correctly."""
        items1 = ["first batch"]
        items2 = ["second batch", "with more items"]
        
        # First mapping
        self.engine.map(items1)
        assert len(self.engine._constellation_history) == 1
        
        # Second mapping
        self.engine.map(items2)
        assert len(self.engine._constellation_history) == 2
        
        # Check history entries
        for entry in self.engine._constellation_history:
            assert "timestamp" in entry
            assert "constellation_size" in entry
            assert "link_count" in entry
            assert "stability_score" in entry

    def test_stability_metrics_include_trend_and_factors(self):
        """Ensure stability metrics include trend data and contributing factors."""
        items = ["alpha item", "beta item", "gamma item"]
        result = self.engine.map(items)

        stability = result["stability"]

        # Historical trend structure
        assert "historical_trend" in stability
        trend = stability["historical_trend"]
        assert set(["trend", "confidence", "change_rate"]).issubset(trend.keys())

        # Factor details
        assert "factors" in stability
        factors = stability["factors"]
        expected_factors = {"item_distribution", "link_strength", "structure_balance"}
        assert expected_factors.issubset(factors.keys())

    def test_historical_trend_improving(self):
        """Historical trend should detect improving stability over time."""
        engine = ConstellationEngine()

        # Patch base stability to simulate improvement across calls
        with patch.object(
            engine,
            "_calculate_base_stability",
            side_effect=[0.4, 0.4, 0.6, 0.6, 0.8, 0.8],
        ):
            engine.map(["one"])
            engine.map(["one", "two"])
            result = engine.map(["one", "two", "three"])

        trend = result["stability"]["historical_trend"]
        assert trend["trend"] == "improving"
        assert trend["change_rate"] > 0
        assert trend["confidence"] > 0
    
    def test_configuration_parameters(self):
        """Test that configuration parameters affect behavior."""
        # Test with different similarity threshold
        engine_strict = ConstellationEngine()
        engine_strict.similarity_threshold = 0.8  # Very strict
        
        engine_loose = ConstellationEngine()
        engine_loose.similarity_threshold = 0.1   # Very loose
        
        items = ["similar text", "similar content", "different topic"]
        
        result_strict = engine_strict.map(items)
        result_loose = engine_loose.map(items)
        
        # Loose threshold should generally produce more links
        assert len(result_loose["links"]) >= len(result_strict["links"])
    
    def test_complex_scenario(self):
        """Test complex scenario with diverse content."""
        items = [
            "Database connection error occurred",
            "Solution: restart the database service",
            "Monitor system performance metrics",
            "CPU usage at 85% threshold",
            "Memory optimization approach needed",
            "User authentication failed",
            "Fix authentication middleware bug",
            "System logging configuration",
            "Error tracking implementation",
            "Performance monitoring dashboard"
        ]
        
        result = self.engine.map(items)
        
        # Should have multiple constellation items
        assert len(result["constellation"]) == len(items)
        
        # Should identify relationships
        assert len(result["links"]) > 0
        
        # Should have reasonable stability
        assert 0 <= result["stability"]["score"] <= 1
        
        # Should have metadata
        metadata = result["metadata"]
        assert metadata["item_count"] == len(items)
        assert metadata["link_count"] == len(result["links"])
        assert metadata["version"] == self.engine.__version__


class TestSlot5ConstellationAdapter:
    """Test the orchestration adapter for Slot 5."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.adapter = Slot5ConstellationAdapter()
    
    def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        assert hasattr(self.adapter, 'available')
        assert hasattr(self.adapter, '_engine')
    
    def test_basic_mapping(self):
        """Test basic constellation mapping through adapter."""
        items = ["test item one", "test item two"]
        result = self.adapter.map(items)
        
        if self.adapter.available:
            assert "constellation" in result
            assert "links" in result
            assert "stability" in result
            assert "metadata" in result
        else:
            assert "error" in result
    
    def test_empty_mapping(self):
        """Test empty input through adapter."""
        result = self.adapter.map([])
        
        if self.adapter.available:
            assert result["constellation"] == []
            assert result["links"] == []
            assert result["stability"]["status"] == "empty"
    
    def test_configuration_management(self):
        """Test configuration get/set functionality."""
        if not self.adapter.available:
            pytest.skip("Adapter not available")
        
        # Get current configuration
        config = self.adapter.get_configuration()
        assert "similarity_threshold" in config
        assert "stability_window" in config
        assert "version" in config
        
        # Update configuration
        new_config = {"similarity_threshold": 0.5, "stability_window": 15}
        success = self.adapter.update_configuration(new_config)
        assert success is True
        
        # Verify update
        updated_config = self.adapter.get_configuration()
        assert updated_config["similarity_threshold"] == 0.5
        assert updated_config["stability_window"] == 15
    
    def test_stability_history(self):
        """Test stability history access."""
        if not self.adapter.available:
            pytest.skip("Adapter not available")
        
        # Perform some mappings to create history
        self.adapter.map(["first test"])
        self.adapter.map(["second test", "more items"])
        
        history = self.adapter.get_stability_history()
        assert len(history) >= 2
        
        for entry in history:
            assert "timestamp" in entry
            assert "constellation_size" in entry
    
    def test_health_check(self):
        """Test adapter health check functionality."""
        health = self.adapter.health_check()
        
        assert "available" in health
        assert "engine_loaded" in health
        assert "status" in health
        assert "version" in health
        assert "history_entries" in health
        
        if self.adapter.available:
            assert health["status"] == "healthy"
            assert health["engine_loaded"] is True
        else:
            assert health["status"] == "degraded"
    
    @patch('orchestrator.adapters.slot5_constellation.ENGINE', None)
    @patch('orchestrator.adapters.slot5_constellation.AVAILABLE', False)
    def test_unavailable_engine(self):
        """Test behavior when engine is unavailable."""
        adapter = Slot5ConstellationAdapter()
        
        result = adapter.map(["test"])
        assert "error" in result
        assert result["stability"]["status"] == "unavailable"
        
        config = adapter.get_configuration()
        assert config == {}
        
        update_success = adapter.update_configuration({"similarity_threshold": 0.5})
        assert update_success is False
        
        health = adapter.health_check()
        assert health["status"] == "degraded"
        assert health["engine_loaded"] is False
    
    def test_error_handling(self):
        """Test error handling in adapter methods."""
        if not self.adapter.available:
            pytest.skip("Adapter not available")
        
        # Test invalid configuration update
        success = self.adapter.update_configuration({
            "similarity_threshold": "invalid_value"
        })
        assert success is False


class TestIntegrationScenarios:
    """Integration tests for various real-world scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ConstellationEngine()
        self.adapter = Slot5ConstellationAdapter()
    
    def test_software_development_scenario(self):
        """Test constellation mapping for software development items."""
        items = [
            "API endpoint returning 500 errors",
            "Database connection timeout issue", 
            "Implement connection pooling solution",
            "Add retry logic for failed requests",
            "Monitor response times and error rates",
            "User authentication middleware bug",
            "JWT token validation failing",
            "Update authentication documentation"
        ]
        
        result = self.engine.map(items)
        
        # Should identify problem-solution relationships
        solution_links = [link for link in result["links"] if link["type"] == "solution"]
        assert len(solution_links) > 0
        
        # Should classify items correctly
        types = [item["type"] for item in result["constellation"]]
        assert "problem" in types
        assert "solution" in types
    
    def test_project_management_scenario(self):
        """Test constellation mapping for project management items."""
        items = [
            "Sprint planning meeting scheduled",
            "User story estimation process",
            "Define acceptance criteria clearly", 
            "Implement feature X functionality",
            "Code review and testing phase",
            "Deploy to staging environment",
            "Performance testing results",
            "Production deployment checklist"
        ]
        
        result = self.engine.map(items)
        
        # Should map all items
        assert len(result["constellation"]) == len(items)
        
        # Should have reasonable stability for structured process
        assert result["stability"]["score"] > 0.3
    
    def test_research_and_analysis_scenario(self):
        """Test constellation mapping for research items.""" 
        items = [
            "Literature review on machine learning",
            "Data collection methodology design",
            "Statistical analysis approach selection",
            "Hypothesis testing framework",
            "Experimental design considerations",
            "Results interpretation guidelines", 
            "Peer review feedback incorporation",
            "Publication preparation checklist"
        ]
        
        result = self.engine.map(items)
        
        # Research items often have conceptual relationships
        conceptual_links = [link for link in result["links"] if link["type"] == "conceptual"]
        assert len(conceptual_links) > 0
        
        # Should have good connectivity for related research items
        assert result["stability"]["connectivity"] > 0.5
    
    def test_mixed_content_robustness(self):
        """Test robustness with mixed, unrelated content."""
        items = [
            "Weather forecast shows rain tomorrow",
            "Database optimization query needed", 
            "Grocery list: milk, bread, eggs",
            "Meeting notes from client call",
            "Error: null pointer exception occurred",
            "Recipe for chocolate chip cookies",
            "Travel itinerary for next week",
            "Bug fix: authentication timeout issue"
        ]
        
        result = self.engine.map(items)
        
        # Should handle all items without crashing
        assert len(result["constellation"]) == len(items)
        
        # Mixed content might have lower connectivity
        # but should still be stable
        assert result["stability"]["score"] >= 0.0
        assert "error" not in result
    
    def test_large_input_performance(self):
        """Test performance with larger input sets."""
        # Generate larger set of items
        items = []
        for i in range(50):
            items.extend([
                f"Problem {i}: system error occurred",
                f"Solution {i}: implement fix for issue",
                f"Process {i}: review and validate approach", 
                f"Data {i}: metrics show {i}% improvement",
                f"Concept {i}: theoretical framework analysis"
            ])
        
        # Should handle 250 items without issues
        result = self.engine.map(items)
        
        assert len(result["constellation"]) == len(items)
        assert "metadata" in result
        assert result["metadata"]["item_count"] == len(items)
        
        # Should have stability metrics
        assert "stability" in result
        assert 0 <= result["stability"]["score"] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])