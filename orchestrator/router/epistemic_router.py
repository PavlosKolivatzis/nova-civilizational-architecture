from __future__ import annotations

import logging
from typing import Any, Dict, Callable

from orchestrator.router.decision import AdvisorScore, ConstraintResult, PolicyResult, RouterDecision
from orchestrator.router.constraints import evaluate_constraints
from orchestrator.router.anr_static_policy import StaticPolicyEngine
from orchestrator.router.advisors.slot05 import score_slot05
from orchestrator.router.advisors.slot08 import score_slot08
from orchestrator.router.temporal_constraints import TemporalConstraintEngine, TemporalConstraintResult
from orchestrator.temporal.adapters import publish_router_modifiers
from orchestrator.predictive.adapters import read_predictive_snapshot
from orchestrator.thresholds import get_threshold

try:  # pragma: no cover - metrics optional
    from orchestrator.prometheus_metrics import record_predictive_penalty
except Exception:  # pragma: no cover
    def record_predictive_penalty(value: float) -> None:  # type: ignore[misc]
        return

try:
    from src.nova.continuity.risk_reconciliation import get_unified_risk_field
except Exception:  # pragma: no cover
    def get_unified_risk_field() -> dict:  # type: ignore[misc]
        return {"alignment_score": 1.0, "composite_risk": 0.0, "risk_gap": 0.0}

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
        temporal_engine: TemporalConstraintEngine | None = None,
    ):
        self._constraint_fn = constraint_fn
        self._policy_engine = policy_engine or StaticPolicyEngine()
        self._temporal_engine = temporal_engine or TemporalConstraintEngine()
        self._last_decision: RouterDecision | None = None

    def _score_advisors(self, request: Dict[str, Any]) -> Dict[str, AdvisorScore]:
        advisors = {
            "slot05": score_slot05(request),
            "slot08": score_slot08(request),
        }
        return advisors

    @staticmethod
    def _build_temporal_payload(
        request: Dict[str, Any],
        constraints: ConstraintResult,
    ) -> Dict[str, Any]:
        payload = dict(request)
        snapshot = constraints.snapshot or {}
        for key in ("tri_signal", "slot07", "slot10"):
            if key not in payload and key in snapshot:
                payload[key] = snapshot[key]
        payload.setdefault("governance", request.get("governance", {}))
        return payload

    def _read_predictive_snapshot(self) -> Dict[str, Any] | None:
        try:
            snapshot = read_predictive_snapshot("router")
        except Exception:
            return None
        return snapshot

    def _apply_predictive_modifiers(
        self,
        constraints: ConstraintResult,
        initial_score: float,
    ) -> Dict[str, Any]:
        snapshot = self._read_predictive_snapshot()
        collapse_threshold = get_threshold("predictive_collapse_threshold")
        accel_threshold = get_threshold("predictive_acceleration_threshold")

        meta = {
            "predictive_allowed": True,
            "predictive_penalty": 0.0,
            "collapse_risk": 0.0,
            "reason": None,
            "predictive_score": initial_score,
        }
        if not snapshot:
            return meta

        collapse_risk = float(snapshot.get("collapse_risk", snapshot.get("predictive_collapse_risk", 0.0)))
        drift_accel = abs(float(snapshot.get("drift_acceleration", 0.0)))
        penalty = min(1.0, drift_accel / max(accel_threshold, 1e-6))
        meta.update(
            {
                "predictive_penalty": penalty,
                "collapse_risk": collapse_risk,
            }
        )

        if collapse_risk >= collapse_threshold:
            meta["predictive_allowed"] = False
            meta["reason"] = "foresight_hold"
            meta["predictive_score"] = 0.0
            if "foresight_hold" not in constraints.reasons:
                constraints.reasons.append("foresight_hold")
        else:
            meta["predictive_score"] = max(0.0, initial_score - penalty)
            if penalty > 0:
                meta["reason"] = "penalty"
        return meta

    def _apply_urf_modifiers(
        self,
        constraints: ConstraintResult,
        initial_score: float,
    ) -> Dict[str, Any]:
        """Apply Unified Risk Field (URF) routing modifiers.

        Penalizes routes when:
        - composite_risk >= 0.7 (high unified risk) → force safe_mode
        - alignment_score < 0.5 (divergent risk signals) → apply penalty
        - risk_gap > 0.4 (large epistemic/temporal mismatch) → apply penalty
        """
        urf = get_unified_risk_field()
        composite_threshold = get_threshold("urf_composite_risk_threshold")
        alignment_threshold = get_threshold("urf_alignment_threshold")
        gap_threshold = get_threshold("urf_risk_gap_threshold")

        composite_risk = urf.get("composite_risk", 0.0)
        alignment_score = urf.get("alignment_score", 1.0)
        risk_gap = urf.get("risk_gap", 0.0)

        meta = {
            "urf_allowed": True,
            "urf_penalty": 0.0,
            "composite_risk": composite_risk,
            "alignment_score": alignment_score,
            "risk_gap": risk_gap,
            "reason": None,
            "urf_score": initial_score,
        }

        # Hard block: composite risk too high
        if composite_risk >= composite_threshold:
            meta["urf_allowed"] = False
            meta["reason"] = "urf_composite_risk_high"
            meta["urf_score"] = 0.0
            if "urf_composite_risk_high" not in constraints.reasons:
                constraints.reasons.append("urf_composite_risk_high")
            return meta

        # Soft penalties for alignment/gap issues
        penalty = 0.0
        if alignment_score < alignment_threshold:
            penalty += (alignment_threshold - alignment_score) * 0.5
            meta["reason"] = "urf_alignment_low"

        if risk_gap > gap_threshold:
            penalty += (risk_gap - gap_threshold) * 0.3
            if not meta["reason"]:
                meta["reason"] = "urf_risk_gap_high"

        meta["urf_penalty"] = min(1.0, penalty)
        meta["urf_score"] = max(0.0, initial_score - meta["urf_penalty"])
        return meta

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
        temporal_meta = (decision.metadata or {}).get("temporal") if decision.metadata else None
        if temporal_meta:
            publish_router_modifiers(
                {
                    "allowed": temporal_meta.get("allowed"),
                    "reason": temporal_meta.get("reason"),
                    "penalty": temporal_meta.get(
                        "penalty",
                        (decision.metadata or {}).get("temporal_penalty"),
                    ),
                    "snapshot": temporal_meta.get("snapshot", {}),
                }
            )
        predictive_meta = (decision.metadata or {}).get("predictive") if decision.metadata else None
        if predictive_meta and mirror_publish:
            try:
                mirror_publish(
                    "predictive.router_modifiers",
                    predictive_meta,
                    "router",
                    ttl=120.0,
                )
            except Exception:
                logger.debug("Failed to publish predictive modifiers", exc_info=True)

    def decide(self, request: Dict[str, Any] | None) -> RouterDecision:
        request = request or {}
        constraints = self._constraint_fn(request)
        temporal_result: TemporalConstraintResult = self._temporal_engine.evaluate(
            self._build_temporal_payload(request, constraints)
        )

        if temporal_result.snapshot:
            constraints.snapshot["temporal"] = temporal_result.snapshot
        if not temporal_result.allowed:
            constraints.allowed = False
            if temporal_result.reason and temporal_result.reason not in constraints.reasons:
                constraints.reasons.append(temporal_result.reason)
        elif temporal_result.reason not in ("ok", None) and temporal_result.reason not in constraints.reasons:
            constraints.reasons.append(temporal_result.reason)

        policy: PolicyResult

        if constraints.allowed:
            policy = self._policy_engine.evaluate(request)
        else:
            policy = PolicyResult(route="safe_mode", score=0.0, details={"reason": "constraints_blocked"})

        advisors = self._score_advisors(request)
        advisor_modifier = sum(advisor.score for advisor in advisors.values()) / max(len(advisors), 1)
        final_score = policy.score * advisor_modifier
        temporal_penalty = max(0.0, temporal_result.penalty)
        if temporal_penalty:
            final_score = max(0.0, final_score - temporal_penalty)

        predictive_meta = self._apply_predictive_modifiers(constraints, final_score)
        final_score = predictive_meta["predictive_score"]
        predictive_allowed = predictive_meta["predictive_allowed"]
        record_predictive_penalty(predictive_meta["predictive_penalty"])

        # Phase 9: Apply URF modifiers after predictive
        urf_meta = self._apply_urf_modifiers(constraints, final_score)
        final_score = urf_meta["urf_score"]
        urf_allowed = urf_meta["urf_allowed"]

        if not constraints.allowed:
            final_route = "safe_mode"
            final_score = 0.0
        elif not predictive_allowed:
            final_route = "safe_mode"
            final_score = 0.0
            if "foresight_hold" not in constraints.reasons:
                constraints.reasons.append("foresight_hold")
        elif not urf_allowed:
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
            metadata={
                "mode": "deterministic",
                "temporal_allowed": temporal_result.allowed,
                "temporal_penalty": temporal_penalty,
                "temporal": temporal_result.to_dict(),
                "predictive": {
                    "predictive_allowed": predictive_meta["predictive_allowed"],
                    "predictive_penalty": predictive_meta["predictive_penalty"],
                    "collapse_risk": predictive_meta["collapse_risk"],
                    "reason": predictive_meta["reason"],
                },
                "urf": {
                    "urf_allowed": urf_meta["urf_allowed"],
                    "urf_penalty": urf_meta["urf_penalty"],
                    "composite_risk": urf_meta["composite_risk"],
                    "alignment_score": urf_meta["alignment_score"],
                    "risk_gap": urf_meta["risk_gap"],
                    "reason": urf_meta["reason"],
                },
            },
        )

        self._publish_decision(decision)
        record_router_decision(decision)
        self._last_decision = decision
        return decision

    @property
    def last_decision(self) -> RouterDecision | None:
        return self._last_decision
