"""
Semantic Creativity Engine - Mathematics of Bounded Creativity

Implements creativity-mathematics controls for Nova's semantic mirror:
- Law of Large Numbers: Many shallow probes vs deep spirals
- Zipf's Law: Prior over concept frequencies + false-hit control
- Combinatorial Creativity: Controlled remix with evidence gates
- 10,000-Hour Rule: Compounding calibration from past runs
- Edge of Chaos: Entropy window + novelty gradient as stop rule

Key Principle: Use creativity-math as the **governor** to enable
semantic exploration without recursive complexity traps.
"""
from __future__ import annotations
import os
import time
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)


@dataclass
class CreativityConfig:
    """Configuration for creativity-math controls."""
    # Beam search constraints (Law of Large Numbers)
    max_depth: int = 3
    max_branches: int = 6
    max_tokens_per_probe: int = 64

    # Entropy/novelty window (Edge of Chaos)
    novelty_eta: float = 0.08          # cosine distance threshold
    info_gain_eps: float = 0.02        # mutual information gain min
    entropy_min: float = 1.2           # bits
    entropy_max: float = 2.8           # bits

    # Zipf distribution controls
    rare_quantile: float = 0.10
    ultra_common_quantile: float = 0.80
    lambda_rare: float = 0.6
    lambda_ultra_common: float = 0.7

    # Scoring weights (Combinatorial Creativity)
    weight_evidence: float = 0.45
    weight_tri: float = 0.25
    weight_novelty: float = 0.20
    weight_complexity_penalty: float = 0.10

    # Practice/learning (10,000-Hour Rule)
    ewma_alpha: float = 0.01            # compounding learning rate cap
    weight_min: float = 0.05
    weight_max: float = 0.70

    # Early exit thresholds
    # We use an entropy-delta surrogate for KL to detect stalls unless P/Q available
    entropy_delta_stall_threshold: float = 0.01
    min_evidence_hits: List[int] = field(default_factory=lambda: [1, 2, 3, 4])

    # Top-K Evidence Gating optimization
    topk_enabled: bool = False              # Enable Top-K optimization
    topk_full_score: int = 3                # Number of candidates for full scoring
    topk_approx_factor: float = 0.5         # Approximation factor for light candidates

    # Memoization (bounded LRU)
    memo_enabled: bool = True               # Enable memoization caching
    memo_novelty_capacity: int = 4096       # Novelty cache capacity
    memo_entropy_capacity: int = 4096       # Entropy cache capacity
    memo_zipf_capacity: int = 2048          # Zipf cache capacity

    # Early Optimal Stop (EOS)
    early_stop_enabled: bool = True         # Enable early optimal termination
    early_stop_target_score: float = 0.62  # Score threshold for early stop
    early_stop_min_info_gain: float = 0.03 # Minimum info gain required

    # Two-Phase Depth Schedule (TPD)
    two_phase_depth_enabled: bool = True    # Enable two-phase depth scheduling
    two_phase_refine_threshold: float = 0.04 # Avg info gain needed for full branching
    two_phase_min_branches: int = 3         # Minimum branches in refine phase

    # Branch-and-Bound Pruning (BnB)
    bnb_enabled: bool = True                # Enable branch-and-bound pruning
    bnb_quality_threshold: float = 0.40     # Global floor to ignore very weak candidates
    bnb_safety_margin: float = 0.05         # Optimistic margin to avoid over-pruning


@dataclass
class SemanticHypothesis:
    """A single semantic hypothesis in beam search."""
    concept_ids: List[str]
    relations: List[str]
    evidence_hits: int
    tri_coherence: float
    novelty_score: float
    entropy: float
    info_gain: float
    depth: int
    parent_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def compute_score(self, config: CreativityConfig, prev_entropy: float = 0.0,
                     zipf_mix: float = 0.0) -> float:
        """Compute creativity-math score for this hypothesis."""
        # Zipf-aware evidence score (penalize ultra-common, boost rare)
        evidence_score = min(self.evidence_hits / 10.0, 1.0)  # normalize

        # TRI coherence (bounded)
        tri_score = max(0.0, min(1.0, self.tri_coherence))

        # Novelty with diminishing returns
        novelty_score = math.tanh(self.novelty_score / config.novelty_eta)

        # Complexity penalty (grows with depth)
        complexity_penalty = math.log(1 + self.depth) / 10.0

        # Information gain boost
        info_boost = 1.0 + self.info_gain if self.info_gain > config.info_gain_eps else 1.0

        score = (
            config.weight_evidence * evidence_score +
            config.weight_tri * tri_score +
            config.weight_novelty * novelty_score -
            config.weight_complexity_penalty * complexity_penalty
        ) * info_boost

        # Inject Zipf prior as small shaping term (centered around 0 via (2x-1))
        score += 0.05 * (2.0 * max(0.0, min(1.0, zipf_mix)) - 1.0)

        return max(0.0, score)


class CreativityGovernor:
    """
    Creativity-mathematics governor for semantic exploration.

    Prevents recursive semantic loops through bounded exploration,
    Zipf-aware ranking, entropy windows, and novelty gradients.
    """

    def __init__(self, config: Optional[CreativityConfig] = None):
        self.config = config or CreativityConfig()
        self._lock = threading.RLock()

        # Telemetry and practice learning
        self._metrics = defaultdict(int)
        self._concept_frequencies = defaultdict(int)  # Zipf distribution
        self._weight_history = deque(maxlen=1000)     # EWMA practice
        self._exit_reasons = defaultdict(int)

        # Cycle detection (anti-recursion) - Use tiny LRU set for O(1) membership
        from collections import OrderedDict
        self._concept_sig_lru = OrderedDict()
        self._concept_sig_lru_cap = 2048
        self._last_cleanup = time.time()

        # Memoization caches (bounded LRU)
        self._novelty_cache = OrderedDict()
        self._entropy_cache = OrderedDict()
        self._zipf_cache = OrderedDict()

        # Memoization telemetry
        self._memo_hits = defaultdict(int)
        self._memo_misses = defaultdict(int)

        logger.info("CreativityGovernor initialized with bounded exploration")

    def _lru_get(self, cache, key, kind):
        """LRU cache get with telemetry."""
        if key in cache:
            val = cache.pop(key)
            cache[key] = val  # Move to end (most recent)
            self._memo_hits[kind] += 1
            return True, val
        self._memo_misses[kind] += 1
        return False, None

    def _lru_put(self, cache, key, val, capacity):
        """LRU cache put with bounded size."""
        cache[key] = val
        while len(cache) > capacity:
            cache.popitem(last=False)  # Remove oldest

    def explore_semantic_space(self, initial_concepts: List[str],
                              context_key: str,
                              requester_slot: str) -> Tuple[SemanticHypothesis, Dict[str, Any]]:
        """
        Explore semantic space with creativity-math controls.

        Returns best hypothesis and exploration telemetry.
        """
        start_time = time.time()
        exploration_telemetry = {
            "depth_reached": 0,
            "hypotheses_generated": 0,
            "exit_reason": "unknown",
            "entropy_trajectory": [],
            "novelty_trajectory": [],
            "info_gain_trajectory": []
        }

        with self._lock:
            # Reset per-exploration memoization to avoid stale cross-run state
            if self.config.memo_enabled:
                self._novelty_cache.clear()
                self._entropy_cache.clear()
                self._zipf_cache.clear()

            # Initialize beam with seed hypothesis
            beam = [SemanticHypothesis(
                concept_ids=initial_concepts,
                relations=[],
                evidence_hits=len(initial_concepts),  # bootstrap
                tri_coherence=0.5,                   # neutral start
                novelty_score=1.0,                   # maximum initial novelty
                entropy=self.config.entropy_max * 0.8,  # start in good zone
                info_gain=0.0,
                depth=0
            )]

            prev_best_score = 0.0
            prev_entropy = beam[0].entropy

            # Beam search with creativity controls
            for depth in range(self.config.max_depth):
                exploration_telemetry["depth_reached"] = depth

                # Generate candidate hypotheses
                candidates = []
                for hypothesis in beam[:self.config.max_branches]:
                    new_candidates = self._expand_hypothesis(
                        hypothesis, context_key, requester_slot
                    )
                    candidates.extend(new_candidates)
                    exploration_telemetry["hypotheses_generated"] += len(new_candidates)

                if not candidates:
                    exploration_telemetry["exit_reason"] = "no_candidates"
                    break

                # Rank by creativity-math score with Top-K optimization
                scored_candidates = self._score_candidates_topk(candidates, prev_entropy, context_key)

                # Early Optimal Stop: terminate when best candidate is "good enough"
                if (scored_candidates and self.config.early_stop_enabled):
                    best_score, best_cand = scored_candidates[0]
                    if (self.config.entropy_min <= best_cand.entropy <= self.config.entropy_max
                        and best_cand.info_gain >= max(self.config.info_gain_eps, self.config.early_stop_min_info_gain)
                        and best_score >= self.config.early_stop_target_score):
                        exploration_telemetry["exit_reason"] = "early_optimal"
                        beam = [best_cand]
                        break

                # Two-Phase Depth Schedule: adaptive beam width based on info gain
                next_k = self.config.max_branches
                if self.config.two_phase_depth_enabled and depth > 1:
                    recent_ig = exploration_telemetry["info_gain_trajectory"]
                    avg_ig = sum(recent_ig[-2:]) / 2.0 if len(recent_ig) >= 2 else (recent_ig[-1] if recent_ig else 0.0)
                    recent_entropy = exploration_telemetry["entropy_trajectory"][-1] if exploration_telemetry["entropy_trajectory"] else 0.0

                    if (avg_ig < self.config.two_phase_refine_threshold
                        and self.config.entropy_min <= recent_entropy <= self.config.entropy_max):
                        next_k = max(self.config.two_phase_min_branches, self.config.max_branches // 2)

                beam = [candidate for score, candidate in scored_candidates[:next_k]]

                if not beam:
                    exploration_telemetry["exit_reason"] = "beam_collapsed"
                    break

                best_candidate = beam[0]

                # Record telemetry
                exploration_telemetry["entropy_trajectory"].append(best_candidate.entropy)
                exploration_telemetry["novelty_trajectory"].append(best_candidate.novelty_score)
                exploration_telemetry["info_gain_trajectory"].append(best_candidate.info_gain)

                # Creativity-math stop conditions
                if self._should_stop_exploration(best_candidate, prev_best_score, prev_entropy):
                    exploration_telemetry["exit_reason"] = self._last_exit_reason
                    break

                prev_best_score = scored_candidates[0][0]
                prev_entropy = best_candidate.entropy

            # Select final hypothesis
            if beam:
                final_hypothesis = beam[0]
                exploration_telemetry["exit_reason"] = exploration_telemetry.get("exit_reason", "max_depth")
            else:
                # Fallback to initial hypothesis
                final_hypothesis = SemanticHypothesis(
                    concept_ids=initial_concepts,
                    relations=[],
                    evidence_hits=1,
                    tri_coherence=0.5,
                    novelty_score=0.5,
                    entropy=self.config.entropy_min,
                    info_gain=0.0,
                    depth=0
                )
                exploration_telemetry["exit_reason"] = "fallback_used"

            # Update telemetry
            exploration_telemetry["duration_ms"] = (time.time() - start_time) * 1000
            self._update_metrics(exploration_telemetry)

            return final_hypothesis, exploration_telemetry

    def _expand_hypothesis(self, hypothesis: SemanticHypothesis,
                          context_key: str, requester_slot: str) -> List[SemanticHypothesis]:
        """Generate new hypotheses from current one."""
        candidates = []

        # Simulate semantic expansion (in real implementation, this would
        # interface with TRI engine, evidence gathering, etc.)
        for i in range(min(3, self.config.max_branches)):  # bounded expansion
            new_concept = f"concept_{hypothesis.depth}_{i}"
            new_relation = f"relation_{hypothesis.depth}_{i}"

            # Compute novelty (simplified - in practice, use embedding similarity)
            novelty = self._compute_novelty(hypothesis.concept_ids + [new_concept])

            # Simulate evidence gathering
            evidence_hits = hypothesis.evidence_hits + (1 if novelty > 0.5 else 0)

            # Check minimum evidence requirement
            min_hits_required = (
                self.config.min_evidence_hits[hypothesis.depth]
                if hypothesis.depth < len(self.config.min_evidence_hits)
                else self.config.min_evidence_hits[-1]
            )

            if evidence_hits < min_hits_required:
                continue  # prune low-evidence paths

            # Simulate TRI coherence (would integrate with actual TRI)
            tri_coherence = max(0.1, hypothesis.tri_coherence + (novelty - 0.5) * 0.2)

            # Compute entropy and info gain
            entropy = self._compute_entropy(hypothesis.concept_ids + [new_concept])
            info_gain = abs(entropy - hypothesis.entropy)

            candidate = SemanticHypothesis(
                concept_ids=hypothesis.concept_ids + [new_concept],
                relations=hypothesis.relations + [new_relation],
                evidence_hits=evidence_hits,
                tri_coherence=tri_coherence,
                novelty_score=novelty,
                entropy=entropy,
                info_gain=info_gain,
                depth=hypothesis.depth + 1,
                parent_id=f"{hypothesis.depth}_{hash(tuple(hypothesis.concept_ids))}"
            )

            candidates.append(candidate)

        return candidates

    def _should_stop_exploration(self, hypothesis: SemanticHypothesis,
                               prev_score: float, prev_entropy: float) -> bool:
        """Creativity-math stop conditions."""

        # Edge of Chaos: entropy window check
        if hypothesis.entropy < self.config.entropy_min or hypothesis.entropy > self.config.entropy_max:
            self._last_exit_reason = "entropy_out_of_band"
            return True

        # Information gain collapse
        if hypothesis.info_gain < self.config.info_gain_eps:
            self._last_exit_reason = "low_info_gain"
            return True

        # Novelty below threshold
        if hypothesis.novelty_score < self.config.novelty_eta:
            self._last_exit_reason = "novelty_below_eta"
            return True

        # Entropy-delta stall detection (surrogate for KL)
        if abs(hypothesis.entropy - prev_entropy) < self.config.entropy_delta_stall_threshold:
            self._last_exit_reason = "entropy_delta_stall"
            return True

        # Cycle detection in concept graph - O(1) LRU lookup
        concept_sig = tuple(sorted(hypothesis.concept_ids))
        if concept_sig in self._concept_sig_lru:
            self._last_exit_reason = "concept_cycle_detected"
            return True

        self._concept_sig_lru[concept_sig] = True
        if len(self._concept_sig_lru) > self._concept_sig_lru_cap:
            self._concept_sig_lru.popitem(last=False)
        return False

    def _compute_novelty(self, concept_ids: List[str]) -> float:
        """Compute novelty score (cosine distance from previous states)."""
        if not self.config.memo_enabled:
            unique_concepts = len(set(concept_ids))
            total_concepts = len(concept_ids)
            return unique_concepts / max(total_concepts, 1)

        key = tuple(sorted(concept_ids))
        hit, val = self._lru_get(self._novelty_cache, key, "novelty")
        if hit:
            return val

        # Simplified novelty - in practice, use embedding similarity
        unique_concepts = len(set(concept_ids))
        total_concepts = len(concept_ids)
        val = unique_concepts / max(total_concepts, 1)

        self._lru_put(self._novelty_cache, key, val, self.config.memo_novelty_capacity)
        return val

    def _compute_entropy(self, concept_ids: List[str]) -> float:
        """Compute entropy of concept distribution."""
        if not concept_ids:
            return 0.0

        if self.config.memo_enabled:
            key = tuple(sorted(concept_ids))
            hit, val = self._lru_get(self._entropy_cache, key, "entropy")
            if hit:
                return val

        # Count frequencies
        freq_map = defaultdict(int)
        for concept in concept_ids:
            freq_map[concept] += 1

        # Compute Shannon entropy
        total = len(concept_ids)
        entropy = 0.0
        for count in freq_map.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        if self.config.memo_enabled:
            self._lru_put(self._entropy_cache, key, entropy, self.config.memo_entropy_capacity)

        return entropy

    def _update_metrics(self, telemetry: Dict[str, Any]) -> None:
        """Update creativity metrics for monitoring."""
        self._metrics["explorations_total"] += 1
        self._metrics[f"exit_reason_{telemetry['exit_reason']}"] += 1
        self._exit_reasons[telemetry["exit_reason"]] += 1
        self._metrics["depth_total"] += telemetry["depth_reached"]
        self._metrics["hypotheses_total"] += telemetry["hypotheses_generated"]

        # Practice learning: micro-updates to weights based on outcomes
        if telemetry["exit_reason"] in ["max_depth", "entropy_out_of_band"]:
            # Good exploration - reinforce current weights
            self._update_weights_ewma(success=True)
        elif telemetry["exit_reason"] in ["kl_stall", "concept_cycle_detected"]:
            # Poor exploration - adjust weights slightly
            self._update_weights_ewma(success=False)

    def _update_weights_ewma(self, success: bool) -> None:
        """Tiny EWMA updates for 10,000-hour rule learning."""
        adjustment = self.config.ewma_alpha * (0.01 if success else -0.01)

        # Bounded weight updates
        if success:
            self.config.weight_novelty = max(
                self.config.weight_min,
                min(self.config.weight_max, self.config.weight_novelty + adjustment)
            )
        else:
            self.config.weight_complexity_penalty = max(
                self.config.weight_min,
                min(self.config.weight_max, self.config.weight_complexity_penalty + abs(adjustment))
            )

        self._weight_history.append({
            "timestamp": time.time(),
            "weight_novelty": self.config.weight_novelty,
            "weight_complexity_penalty": self.config.weight_complexity_penalty,
            "success": success
        })

    def _score_candidates_topk(self, candidates: List[SemanticHypothesis],
                              prev_entropy: float, context_key: str) -> List[Tuple[float, SemanticHypothesis]]:
        """
        Top-K Evidence Gating: cheap pre-score → expensive full scoring on top-K only.
        Expected impact: -30-50% wall time when evidence/TRI is expensive.
        """
        if not self.config.topk_enabled or len(candidates) <= self.config.topk_full_score:
            scored = []
            LB = self.config.bnb_quality_threshold
            # First, do a cheap single pass to set a preliminary LB from cheap bounds
            if self.config.bnb_enabled:
                prelim = []
                for cand in candidates:
                    prelim.append((self._cheap_upper_bound(cand), cand))
                prelim.sort(key=lambda x: x[0], reverse=True)
                # seed LB with the top cheap bound as a conservative start
                if prelim:
                    LB = max(LB, prelim[0][0])

            # Now score with pruning
            for cand in candidates:
                if self.config.bnb_enabled:
                    ub = self._cheap_upper_bound(cand)
                    if ub < LB:
                        self._metrics["bnb_pruned"] += 1
                        continue
                zmix = self._zipf_mix(cand.concept_ids)
                score = cand.compute_score(self.config, prev_entropy, zmix)
                scored.append((score, cand))
                if score > LB:
                    LB = score

            return sorted(scored, key=lambda x: x[0], reverse=True)

        def pre_score(c: SemanticHypothesis) -> float:
            """Cheap pre-score: entropy in-band + novelty above threshold."""
            ent_bonus = 1.0 if self.config.entropy_min <= c.entropy <= self.config.entropy_max else 0.0
            nov_bonus = 1.0 if c.novelty_score >= self.config.novelty_eta else 0.0
            return 0.6 * ent_bonus + 0.4 * nov_bonus

        # Partition: top-K get expensive scoring, rest get approximation
        sorted_by_prescore = sorted(candidates, key=pre_score, reverse=True)
        heavy = sorted_by_prescore[:self.config.topk_full_score]
        light = sorted_by_prescore[self.config.topk_full_score:]

        scored = []
        LB = self.config.bnb_quality_threshold  # global floor

        # Full scoring for top-K candidates
        for cand in heavy:
            zmix = self._zipf_mix(cand.concept_ids)
            score = cand.compute_score(self.config, prev_entropy, zmix)
            scored.append((score, cand))
            if score > LB:
                LB = score  # improve bound with real best-so-far

        # Approximated scoring for remaining candidates (BnB prune)
        for cand in light:
            if self.config.bnb_enabled:
                ub = self._cheap_upper_bound(cand)
                # prune if even optimistic bound cannot beat LB
                if ub < LB:
                    self._metrics["bnb_pruned"] += 1
                    continue
            approx_score = self.config.topk_approx_factor * pre_score(cand)
            scored.append((approx_score, cand))

        return sorted(scored, key=lambda x: x[0], reverse=True)

    # --- Zipf prior helpers ---
    def _zipf_mix(self, concept_ids: List[str]) -> float:
        """
        Compute a simple Zipf mix score in [0,1]:
        - reward presence of at least one rare concept (quantile <= rare_quantile)
        - penalize dominance by ultra-common concepts (quantile >= ultra_common_quantile)
        Returns a shaped blend usable as a small additive term to the score.
        """
        if not concept_ids:
            return 0.5

        if self.config.memo_enabled:
            key = tuple(sorted(concept_ids))
            hit, val = self._lru_get(self._zipf_cache, key, "zipf")
            if hit:
                return val

        qs = [self._concept_quantile(cid) for cid in concept_ids]
        has_rare = any(q <= self.config.rare_quantile for q in qs)
        ultra_share = sum(1 for q in qs if q >= self.config.ultra_common_quantile) / len(qs)
        base = 0.5
        if has_rare:
            base += 0.5 * self.config.lambda_rare   # nudge up
        base -= ultra_share * self.config.lambda_ultra_common * 0.5
        val = max(0.0, min(1.0, base))

        if self.config.memo_enabled:
            self._lru_put(self._zipf_cache, key, val, self.config.memo_zipf_capacity)

        return val

    def _concept_quantile(self, concept_id: str) -> float:
        """
        Map a concept to an empirical frequency quantile in [0,1].
        Placeholder: if no stats, return 0.5. Integrate with your corpus stats provider.
        """
        freq = self._concept_frequencies.get(concept_id, 0)
        # TODO: replace with real ECDF from corpus; for now, crude mapping
        if freq <= 0:
            return 0.5
        if freq < 3:
            return 0.2
        if freq < 10:
            return 0.5
        return 0.9

    def _cheap_upper_bound(self, c: "SemanticHypothesis") -> float:
        """
        Very cheap optimistic upper bound in [0,1] used for BnB.
        Emphasizes in-band entropy, novelty above eta, and a tiny bonus
        when info_gain is already above eps. No TRI/evidence calls here.
        """
        ent_ok = 1.0 if self.config.entropy_min <= c.entropy <= self.config.entropy_max else 0.0
        nov_ok = 1.0 if c.novelty_score >= self.config.novelty_eta else 0.0
        ig_ok  = 1.0 if c.info_gain >= self.config.info_gain_eps else 0.0

        # weights sum to 1.0; keep optimistic but conservative
        ub = 0.55*ent_ok + 0.35*nov_ok + 0.10*ig_ok
        # safety margin (optimism) to reduce false negatives
        return min(1.0, ub + self.config.bnb_safety_margin)

    def get_creativity_metrics(self) -> Dict[str, Any]:
        """Get creativity telemetry for monitoring."""
        with self._lock:
            avg_depth = (
                self._metrics["depth_total"] / max(self._metrics["explorations_total"], 1)
            )
            avg_hypotheses = (
                self._metrics["hypotheses_total"] / max(self._metrics["explorations_total"], 1)
            )

            return {
                "explorations_total": self._metrics["explorations_total"],
                "avg_depth_reached": round(avg_depth, 2),
                "avg_hypotheses_per_exploration": round(avg_hypotheses, 2),
                "current_weights": {
                    "evidence": self.config.weight_evidence,
                    "tri": self.config.weight_tri,
                    "novelty": self.config.weight_novelty,
                    "complexity_penalty": self.config.weight_complexity_penalty
                },
                "exit_reasons": dict(self._exit_reasons),
                "concept_graph_cache_size": len(self._concept_sig_lru),
                "weight_adaptation_events": len(self._weight_history),
                "config_snapshot": {
                    "max_depth": self.config.max_depth,
                    "max_branches": self.config.max_branches,
                    "entropy_window": [self.config.entropy_min, self.config.entropy_max],
                    "novelty_eta": self.config.novelty_eta,
                    "info_gain_eps": self.config.info_gain_eps,
                    "early_stop_enabled": self.config.early_stop_enabled,
                    "early_stop_target_score": self.config.early_stop_target_score,
                    "two_phase_depth_enabled": self.config.two_phase_depth_enabled,
                    "two_phase_refine_threshold": self.config.two_phase_refine_threshold,
                    "bnb_enabled": self.config.bnb_enabled,
                    "bnb_quality_threshold": self.config.bnb_quality_threshold
                }
            }


# Global creativity governor instance
_creativity_governor: Optional[CreativityGovernor] = None
_creativity_lock = threading.Lock()


def get_creativity_governor() -> CreativityGovernor:
    """Get global creativity governor instance (thread-safe)."""
    global _creativity_governor
    if _creativity_governor is None:
        with _creativity_lock:
            # Double-check pattern to avoid race condition
            if _creativity_governor is None:
                config = _load_creativity_config()
                _creativity_governor = CreativityGovernor(config)
    return _creativity_governor


def _load_creativity_config() -> CreativityConfig:
    """Load creativity configuration from environment with validation."""
    # Runtime validation (Phase 2: production-safe logging)
    early_stop_val = os.getenv("NOVA_CREATIVITY_EARLY_STOP", "0")
    two_phase_val = os.getenv("NOVA_CREATIVITY_TWO_PHASE", "0")
    bnb_val = os.getenv("NOVA_CREATIVITY_BNB", "0")

    if early_stop_val != "1":
        logger.debug(f"Early stop disabled (env={early_stop_val})")
    if two_phase_val != "1":
        logger.debug(f"Two-phase disabled (env={two_phase_val})")
    if bnb_val != "1":
        logger.debug(f"BnB disabled (env={bnb_val})")

    return CreativityConfig(
        max_depth=int(os.getenv("NOVA_CREATIVITY_MAX_DEPTH", "3")),
        max_branches=int(os.getenv("NOVA_CREATIVITY_MAX_BRANCHES", "6")),
        max_tokens_per_probe=int(os.getenv("NOVA_CREATIVITY_MAX_TOKENS", "64")),
        novelty_eta=float(os.getenv("NOVA_CREATIVITY_NOVELTY_ETA", "0.08")),
        info_gain_eps=float(os.getenv("NOVA_CREATIVITY_INFO_GAIN_EPS", "0.02")),
        entropy_min=float(os.getenv("NOVA_CREATIVITY_ENTROPY_MIN", "1.2")),
        entropy_max=float(os.getenv("NOVA_CREATIVITY_ENTROPY_MAX", "2.8")),
        ewma_alpha=float(os.getenv("NOVA_CREATIVITY_EWMA_ALPHA", "0.01")),
        entropy_delta_stall_threshold=float(os.getenv("NOVA_CREATIVITY_ENTROPY_DELTA_STALL", "0.01")),
        # Early Optimal Stop (EOS) environment variables
        early_stop_enabled=(early_stop_val == "1"),
        early_stop_target_score=float(os.getenv("NOVA_CREATIVITY_EARLY_STOP_SCORE", "0.62")),
        early_stop_min_info_gain=float(os.getenv("NOVA_CREATIVITY_EARLY_STOP_IG", "0.03")),
        # Two-Phase Depth Schedule (TPD) environment variables
        two_phase_depth_enabled=(two_phase_val == "1"),
        two_phase_refine_threshold=float(os.getenv("NOVA_CREATIVITY_TWO_PHASE_THRESH", "0.045")),
        two_phase_min_branches=int(os.getenv("NOVA_CREATIVITY_TWO_PHASE_MIN", "3")),
        # Branch-and-Bound (BnB) environment variables
        bnb_enabled=(bnb_val == "1"),
        bnb_quality_threshold=float(os.getenv("NOVA_CREATIVITY_BNB_Q","0.40")),
        bnb_safety_margin=float(os.getenv("NOVA_CREATIVITY_BNB_MARGIN","0.05")),
    )


def reset_creativity_governor() -> None:
    """Reset global creativity governor (for testing)."""
    global _creativity_governor
    _creativity_governor = None


# Integration point for semantic mirror
def explore_with_creativity_math(initial_concepts: List[str],
                               context_key: str,
                               requester_slot: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Main integration point for semantic mirror creativity exploration.

    Returns (semantic_result, telemetry) where semantic_result contains
    the final creative interpretation and telemetry contains metrics.
    """
    governor = get_creativity_governor()
    hypothesis, telemetry = governor.explore_semantic_space(
        initial_concepts, context_key, requester_slot
    )

    # Convert hypothesis to semantic mirror result format
    semantic_result = {
        "concepts": hypothesis.concept_ids,
        "relations": hypothesis.relations,
        "confidence": hypothesis.tri_coherence,
        "novelty": hypothesis.novelty_score,
        "evidence_strength": hypothesis.evidence_hits,
        "entropy_bits": hypothesis.entropy,
        "depth_explored": hypothesis.depth,
        "creativity_score": hypothesis.compute_score(governor.config)
    }

    return semantic_result, telemetry
