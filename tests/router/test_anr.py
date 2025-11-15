"""Minimal tests for Phase 5.0 ANR shadow implementation."""
import pytest
from unittest.mock import patch

from orchestrator.router.anr import AdaptiveNeuralRouter, RouteDecision
from orchestrator.router.routes import build_plan_for_route


class TestAdaptiveNeuralRouter:
    """Test ANR shadow mode functionality."""

    def test_init_shadow_mode(self):
        """Test router initializes in shadow mode by default."""
        router = AdaptiveNeuralRouter()
        assert not router.enabled  # disabled by default
        assert router.pilot == 0.0
        assert router.eps == 0.05
        assert router.shadow_sample == 1.0

    def test_decide_shadow_argmax(self):
        """Test shadow mode uses argmax policy."""
        router = AdaptiveNeuralRouter()
        ctx = {"test": "value"}

        decision = router.decide(ctx, shadow=True)

        assert isinstance(decision, RouteDecision)
        assert decision.shadow
        assert decision.route in router.ROUTES
        assert len(decision.id) > 0
        assert decision.ts > 0

    def test_safety_mask_consent_block(self):
        """Test safety mask blocks routes on consent denial."""
        router = AdaptiveNeuralRouter()
        ctx = {"consent_denied": True}

        decision = router.decide(ctx)

        # Only R4 should be allowed
        assert decision.route == "R4"
        assert "R1" in decision.masked_out
        assert "R2" in decision.masked_out
        assert "R3" in decision.masked_out
        assert "R5" in decision.masked_out

    def test_anomaly_coordination(self, monkeypatch):
        """Test Phase 4.1 anomaly coordination masks aggressive routes."""
        import orchestrator.unlearn_weighting as uw
        monkeypatch.setattr(uw, "get_anomaly_observability", lambda: {"engaged": 1}, raising=False)

        router = AdaptiveNeuralRouter()
        decision = router.decide({})

        assert "R1" in decision.masked_out and "R3" in decision.masked_out
        assert "anomaly_engaged" in decision.reasons

    def test_build_plan_integration(self):
        """Test decision builds concrete execution plan."""
        router = AdaptiveNeuralRouter()
        ctx = {"test": "value"}

        decision = router.decide(ctx)
        plan = router.build_plan(decision, ctx)

        assert plan.route.startswith(decision.route)  # e.g., R1 -> R1_STANDARD
        assert hasattr(plan, 'steps')
        assert hasattr(plan, 'conservative')

    @patch('orchestrator.router.anr.publish')
    def test_credit_immediate(self, mock_publish):
        """Test immediate credit assignment publishes reward."""
        router = AdaptiveNeuralRouter()

        router.credit_immediate("test-id", 0.5, 0.1)

        mock_publish.assert_called_once()
        args = mock_publish.call_args
        assert args[0][0] == "router.anr_reward_immediate"
        assert args[0][1]["id"] == "test-id"
        assert args[0][1]["latency"] == 0.5
        assert args[0][1]["tri_delta"] == 0.1

    @patch('orchestrator.router.anr.publish')
    def test_credit_deployment(self, mock_publish):
        """Test deployment feedback credit assignment."""
        router = AdaptiveNeuralRouter()
        feedback = {
            "decision_id": "test-id",
            "slo_ok": True,
            "transform_rate": 0.2,
            "rollback": False,
            "error_rate": 0.0
        }

        router.credit_deployment(feedback)

        mock_publish.assert_called_once()
        args = mock_publish.call_args
        assert args[0][0] == "router.anr_reward_deployment"
        assert args[0][1]["id"] == "test-id"
        assert args[0][1]["reward"]["ok"] == 1.0
        assert args[0][1]["reward"]["transform"] == 0.8  # 1 - 0.2


class TestRouteBuilders:
    """Test route builder integration."""

    def test_all_routes_buildable(self):
        """Test all routes can build execution plans."""
        ctx = {"test": "value"}

        for route in ["R1", "R2", "R3", "R4", "R5"]:
            plan = build_plan_for_route(route, ctx)
            assert plan.route.startswith(route)

            if route == "R4":
                assert len(plan.steps) == 0  # block route
                assert plan.conservative
            else:
                assert len(plan.steps) > 0

    def test_unknown_route_defaults_strict(self):
        """Test unknown routes default to R2 strict."""
        ctx = {"test": "value"}

        plan = build_plan_for_route("UNKNOWN", ctx)
        assert plan.route == "R2_STRICT"
        assert plan.conservative


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
