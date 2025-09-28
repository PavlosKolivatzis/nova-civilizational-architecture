"""Nova Adaptive Neural Routing (ANR) - Phase 5.0 Shadow Implementation."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional
import os
import time
import random
import uuid

from orchestrator.router.routes import ROUTE_BUILDERS, ExecutionPlan, build_plan_for_route
from orchestrator.semantic_mirror import publish, get_context
from orchestrator.router.features import (
    build_feature_vector, FEATURE_DIM,
    normalize_immediate_reward, normalize_deployment_reward
)

try:
    from orchestrator.router.bandit import BanditStore
    _BANDIT_OK = True
except Exception:
    BanditStore = None  # type: ignore
    _BANDIT_OK = False

@dataclass
class RouteDecision:
    id: str
    route: str
    probs: Dict[str, float]
    masked_out: List[str]
    reasons: List[str]
    shadow: bool
    ts: float

class AdaptiveNeuralRouter:
    """Shadow-mode neural router with Phase 4.1 anomaly coordination and safety masks."""

    ROUTES = ["R1", "R2", "R3", "R4", "R5"]

    def __init__(self):
        self.enabled = os.getenv("NOVA_ANR_ENABLED", "0") == "1"  # keep 0 for 5.0 shadow
        self.pilot = float(os.getenv("NOVA_ANR_PILOT", "0.0"))
        self.eps = float(os.getenv("NOVA_ANR_EPSILON", "0.05"))
        self.shadow_sample = float(os.getenv("NOVA_ANR_SHADOW_SAMPLE", "1.0"))
        self._pending: Dict[str, Dict[str, Any]] = {}  # decision_id -> ctx snapshot

        # ---- Phase 5.1 bandit (shadow learning by default) ----
        self.learn_in_shadow = os.getenv("NOVA_ANR_LEARN_SHADOW", "1") == "1"
        self.bandit_state_path = os.getenv("NOVA_ANR_STATE_PATH", os.path.join(".", "state", "anr_linucb.json"))
        self.bandit_alpha = float(os.getenv("NOVA_ANR_ALPHA", "0.8"))
        self.bandit_ridge = float(os.getenv("NOVA_ANR_RIDGE", "0.01"))
        self._bandit_store = BanditStore(self.bandit_state_path, self.ROUTES, FEATURE_DIM,
                                         self.bandit_alpha, self.bandit_ridge) if _BANDIT_OK else None

    # ---------- Phase 4.1 coordination ----------
    def _anomaly_engaged(self) -> bool:
        """Check if Phase 4.1 anomaly system is engaged."""
        try:
            from orchestrator.unlearn_weighting import get_anomaly_observability
            obs = get_anomaly_observability()
            return bool(obs.get("engaged", 0))
        except Exception:
            return False

    # ---------- Safety mask implementation ----------
    def _hard_blocks(self, ctx: Dict[str, Any]) -> List[str]:
        """Apply hard safety constraints (CE-001, CE-003, ACL)."""
        blocked: List[str] = []

        # Consent blocks (CE-001)
        if ctx.get("consent_denied"):
            blocked.extend(["R1", "R2", "R3", "R5"])  # only R4 guardrail allowed

        # ACL constraints
        if ctx.get("acl_forbid_fast"):
            blocked.append("R3")

        # Memory ethics blocks (CE-003)
        if ctx.get("memory_ethics_violation"):
            blocked.extend(["R1", "R3"])  # force conservative routes

        return list(set(blocked))

    def _mask(self, ctx: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Apply complete safety mask with anomaly coordination."""
        reasons: List[str] = []
        masked = self._hard_blocks(ctx)

        # Phase 4.1 coordination: anomaly engagement forces conservative routing
        if self._anomaly_engaged():
            for route in ("R1", "R3"):  # mask aggressive routes
                if route not in masked:
                    masked.append(route)
            reasons.append("anomaly_engaged")

            # Optional: zero exploration during anomaly
            if os.getenv("NOVA_ANR_STRICT_ON_ANOMALY") == "1":
                self.eps = 0.0

        return masked, reasons

    # ---------- Stateless ε-greedy policy ----------
    def _policy(self, masked: List[str], ctx: Dict[str, Any]) -> Dict[str, float]:
        """Compute route probabilities with ε-greedy exploration."""
        allowed = [r for r in self.ROUTES if r not in masked]

        # Ensure guardrail always available
        if not allowed:
            return {"R4": 1.0}

        # Bandit scores (if available)
        if self._bandit_store is not None:
            try:
                import numpy as _np
                x = _np.array(build_feature_vector(ctx), dtype=float)
                scores = {r: self._bandit_store.score(r, x) for r in allowed}
                # normalize to probabilities (range scale + small floor)
                mn, mx = min(scores.values()), max(scores.values())
                span = max(1e-6, mx - mn)
                probs = {r: (scores[r] - mn) / span + 1e-3 for r in allowed}
                total = sum(probs.values())
                return {r: v / total for r, v in probs.items()}
            except Exception:
                pass  # fall back to stateless ε-greedy

        # Stateless ε-greedy
        base = 1.0 / len(allowed)
        probs = {r: base for r in allowed}
        if random.random() < self.eps and "R3" in allowed:
            probs["R3"] += 0.05
            s = sum(probs.values())
            for k in probs:
                probs[k] /= s
        return probs

    # ---------- Route sampling ----------
    def _sample(self, probs: Dict[str, float]) -> str:
        """Sample route by probability distribution."""
        r, p = 0.0, random.random()
        for route, prob in probs.items():
            r += prob
            if p <= r:
                return route
        return max(probs, key=probs.get)  # fallback to argmax

    # ---------- Public API ----------
    def decide(self, ctx: Dict[str, Any], shadow: bool = True) -> RouteDecision:
        """Make routing decision with safety mask and anomaly coordination."""
        masked, reasons = self._mask(ctx)
        probs = self._policy(masked, ctx)

        # Route selection: argmax for shadow, sample for pilot
        if shadow or not self.enabled:
            route = max(probs, key=probs.get)
        else:
            route = self._sample(probs) if random.random() < self.pilot else max(probs, key=probs.get)

        decision = RouteDecision(
            id=str(uuid.uuid4()),
            route=route,
            probs=probs,
            masked_out=masked,
            reasons=reasons,
            shadow=shadow or not self.enabled,
            ts=time.time()
        )

        # Store decision context for delayed credit assignment
        self._pending[decision.id] = {
            "ctx": ctx,
            "route": route,
            "ts": decision.ts,
        }

        # Publish decision to semantic mirror (with sampling for shadow load control)
        key = "router.anr_shadow_decision" if decision.shadow else "router.anr_live_decision"
        if decision.shadow:
            if random.random() < self.shadow_sample:
                publish(key, decision.__dict__, "anr", ttl=120.0)
        else:
            publish(key, decision.__dict__, "anr", ttl=120.0)

        # Publish correlation ID for deployment feedback
        publish("router.current_decision_id", {"id": decision.id, "ts": decision.ts}, "anr", ttl=600.0)

        return decision

    def build_plan(self, decision: RouteDecision, ctx: Dict[str, Any]) -> ExecutionPlan:
        """Convert decision to concrete execution plan."""
        return build_plan_for_route(decision.route, ctx)

    # ---------- Credit assignment hooks (Phase 5.1 expansion points) ----------
    def credit_immediate(self, decision_id: str, latency_s: float, tri_delta: float) -> None:
        """Record immediate feedback (latency, TRI delta) for learning."""
        publish("router.anr_reward_immediate", {
            "id": decision_id,
            "latency": latency_s,
            "tri_delta": tri_delta,
            "ts": time.time()
        }, "anr", ttl=600.0)

        if self._bandit_store is not None and self.learn_in_shadow:
            try:
                import numpy as _np
                ctx = (self._pending.get(decision_id) or {}).get("ctx", {})
                x = _np.array(build_feature_vector(ctx), dtype=float)
                r = normalize_immediate_reward(latency_s, tri_delta)
                route = (self._pending.get(decision_id) or {}).get("route")
                if route in self.ROUTES:
                    self._bandit_store.update(route, x, r)
                    self._bandit_store.save()
            except Exception:
                pass

    def credit_deployment(self, feedback: Dict[str, Any]) -> None:
        """Record deployment feedback for learning."""
        # Correlate with current decision
        decision_id = feedback.get("decision_id")
        if not decision_id:
            ctx = get_context("router.current_decision_id") or {}
            decision_id = ctx.get("id")

        if not decision_id:
            return

        # Compute reward components
        reward = {
            "ok": 1.0 if feedback.get("slo_ok") else -1.0,
            "transform": 1.0 - float(feedback.get("transform_rate", 0.0)),
            "rollback": -1.0 if feedback.get("rollback") else 0.0,
            "error": -float(feedback.get("error_rate", 0.0)),
        }

        publish("router.anr_reward_deployment", {
            "id": decision_id,
            "reward": reward,
            "ts": time.time()
        }, "anr", ttl=3600.0)

        if self._bandit_store is not None and self.learn_in_shadow:
            try:
                import numpy as _np
                ctx = (self._pending.get(decision_id) or {}).get("ctx", {})
                x = _np.array(build_feature_vector(ctx), dtype=float)
                r = normalize_deployment_reward(feedback)
                route = (self._pending.get(decision_id) or {}).get("route")
                if route in self.ROUTES:
                    self._bandit_store.update(route, x, r)
                    self._bandit_store.save()
            except Exception:
                pass

    # ---------- Observability ----------
    def get_stats(self) -> Dict[str, Any]:
        """Get current router statistics."""
        return {
            "enabled": self.enabled,
            "pilot": self.pilot,
            "epsilon": self.eps,
            "shadow_sample": self.shadow_sample,
            "pending_decisions": len(self._pending),
            "anomaly_engaged": self._anomaly_engaged(),
        }