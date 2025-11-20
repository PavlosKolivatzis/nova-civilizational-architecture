from __future__ import annotations

import logging
from typing import Any, Dict, Callable

from orchestrator.router.decision import AdvisorScore, ConstraintResult, PolicyResult, RouterDecision
from orchestrator.router.constraints import evaluate_constraints
from orchestrator.router.anr_static_policy import StaticPolicyEngine
from orchestrator.router.advisors.slot05 import score_slot05
from orchestrator.router.advisors.slot08 import score_slot08

try:
    from orchestrator.semantic_mirror import publish as mirror_publish
except Exception:  # pragma: no cover
    mirror_publish = None  # type: ignore[assignment]

try:
    from orchestrator.prometheus_metrics import record_router_decision
except Exception:  # pragma: no cover
    def record_router_decision(decision: RouteDecision) -> None:
        return

logger = logging.getLogger(__name__)


class EpistemicRouter:
    """Deterministic routing layer that enforces hard constraints before ANR."""

    def __init__(
        self,
        constraint_fn: Callable[[Dict[str, Any]], ConstraintResult] = evaluate_constraints,
        policy_engine: StaticPolicyEngine | None = None,
    ):
        self._constraint_fn = constraint_fn
        self._policy_engine = policy_engine or StaticPolicyEngine()
        self._last_decision: RouterDecision | None = None

    def _score_advisors(self, request: Dict[str, Any]) -> Dict[str, AdvisorScore]:
        advisors = {
            "slot05": score_slot05(request),
            "slot08": score_slot08(request),
        }
        return advisors

    def _publish_decision(self, decision: RouterDecision) -> None:
        if not mirror_publish:
            return
        try:
            mirror_publish("router.constraint_snapshot", decision.constraints.to_dict(), "router", ttl=180.0)
            mirror_publish(
                "router.anr_policy",
                decision.policy.to_dict(),
                "router",
                ttl=180.0,
            )
            for name, advisor in decision.advisors.items():
                mirror_publish(f"router.advisor.{name}", advisor.to_dict(), "router", ttl=180.0)
            mirror_publish("router.final_route", decision.to_dict(), "router", ttl=120.0)
        except Exception:
            logger.debug("Failed to publish router decision to semantic mirror", exc_info=True)

    def decide(self, request: Dict[str, Any] | None) -> RouterDecision:
        request = request or {}
        constraints = self._constraint_fn(request)
        policy: PolicyResult

        if constraints.allowed:
            policy = self._policy_engine.evaluate(request)
        else:
            policy = PolicyResult(route="safe_mode", score=0.0, details={"reason": "constraints_blocked"})

        advisors = self._score_advisors(request)
        advisor_modifier = sum(advisor.score for advisor in advisors.values()) / max(len(advisors), 1)
        final_score = policy.score * advisor_modifier

        if not constraints.allowed:
            final_route = "safe_mode"
            final_score = 0.0
        else:
            final_route = policy.route
            if policy.route != "safe_mode" and final_score < 0.4:
                final_route = "low_trust"

        decision = RouterDecision(
            route=final_route,
            constraints=constraints,
            policy=policy,
            advisors=advisors,
            final_score=max(0.0, min(1.0, final_score)),
            metadata={"mode": "deterministic"},
        )

        self._publish_decision(decision)
        record_router_decision(decision)
        self._last_decision = decision
        return decision

    @property
    def last_decision(self) -> RouterDecision | None:
        return self._last_decision
