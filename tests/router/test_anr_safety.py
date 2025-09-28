"""Tests for ANR safety mechanisms: fast cap, pilot gating, kill-switch."""
import pytest
from unittest.mock import patch

from orchestrator.router.anr import AdaptiveNeuralRouter


class TestANRSafety:
    """Test ANR safety hardening mechanisms."""

    def test_fast_cap_under_anomaly(self, monkeypatch):
        """Test fast route probability capped when anomaly engaged."""
        monkeypatch.setenv("NOVA_ANR_MAX_FAST_PROB", "0.15")

        # Mock anomaly as engaged
        import orchestrator.unlearn_weighting as uw
        monkeypatch.setattr(uw, "get_anomaly_observability", lambda: {"engaged": 1}, raising=False)

        router = AdaptiveNeuralRouter()

        # Context that would normally favor R3 heavily
        ctx = {"system_pressure": 0.1, "cultural_residual_risk": 0.1}

        decision = router.decide(ctx)

        # R3 should be capped at 0.15 even if bandit/policy would prefer higher
        assert decision.probs.get("R3", 0.0) <= 0.15
        assert "anomaly_engaged" in decision.reasons

    def test_pilot_gating_all_shadow(self, monkeypatch):
        """Test pilot=0.0 forces all decisions to shadow mode."""
        monkeypatch.setenv("NOVA_ANR_ENABLED", "1")
        monkeypatch.setenv("NOVA_ANR_PILOT", "0.0")

        router = AdaptiveNeuralRouter()
        ctx = {"test": "value"}

        # Multiple decisions should all be shadow
        for _ in range(10):
            decision = router.decide(ctx, shadow=False)
            assert decision.shadow  # Should be forced to shadow by pilot gating

    def test_pilot_gating_all_live(self, monkeypatch):
        """Test pilot=1.0 allows all decisions to be live."""
        monkeypatch.setenv("NOVA_ANR_ENABLED", "1")
        monkeypatch.setenv("NOVA_ANR_PILOT", "1.0")

        router = AdaptiveNeuralRouter()
        ctx = {"test": "value"}

        # At least some decisions should be live (not deterministic due to sampling)
        live_count = 0
        for _ in range(20):
            decision = router.decide(ctx, shadow=False)
            if not decision.shadow:
                live_count += 1

        assert live_count > 0  # Should have some live decisions

    def test_pilot_gating_partial(self, monkeypatch):
        """Test pilot=0.5 gives mix of shadow and live."""
        monkeypatch.setenv("NOVA_ANR_ENABLED", "1")
        monkeypatch.setenv("NOVA_ANR_PILOT", "0.5")

        router = AdaptiveNeuralRouter()
        ctx = {"test": "value"}

        decisions = [router.decide(ctx, shadow=False) for _ in range(100)]
        live_count = sum(1 for d in decisions if not d.shadow)

        # Should be roughly 50% live (allow some variance)
        assert 30 <= live_count <= 70

    def test_kill_switch_forces_r4(self, monkeypatch):
        """Test kill switch forces all decisions to R4."""
        monkeypatch.setenv("NOVA_ANR_KILL", "1")

        router = AdaptiveNeuralRouter()
        ctx = {"test": "value"}

        decision = router.decide(ctx)

        assert decision.route == "R4"
        assert decision.probs == {"R4": 1.0}

    def test_kill_switch_disabled(self, monkeypatch):
        """Test kill switch disabled allows normal routing."""
        monkeypatch.setenv("NOVA_ANR_KILL", "0")

        router = AdaptiveNeuralRouter()
        ctx = {"test": "value"}

        decision = router.decide(ctx)

        # Should not be forced to R4
        assert decision.route in router.ROUTES
        # Should have multiple route probabilities
        assert len([p for p in decision.probs.values() if p > 0]) > 1

    @patch('orchestrator.unlearn_weighting.get_anomaly_observability')
    def test_combined_safety_mechanisms(self, mock_anomaly, monkeypatch):
        """Test safety mechanisms work together."""
        monkeypatch.setenv("NOVA_ANR_ENABLED", "1")
        monkeypatch.setenv("NOVA_ANR_PILOT", "1.0")
        monkeypatch.setenv("NOVA_ANR_MAX_FAST_PROB", "0.10")

        # Anomaly engaged
        mock_anomaly.return_value = {"engaged": 1}

        router = AdaptiveNeuralRouter()
        ctx = {"system_pressure": 0.0}  # Low pressure normally favors R3

        decision = router.decide(ctx, shadow=False)

        # Should have anomaly masking + fast cap
        assert "R1" in decision.masked_out or "R3" in decision.masked_out
        assert decision.probs.get("R3", 0.0) <= 0.10
        assert "anomaly_engaged" in decision.reasons


if __name__ == "__main__":
    pytest.main([__file__, "-v"])