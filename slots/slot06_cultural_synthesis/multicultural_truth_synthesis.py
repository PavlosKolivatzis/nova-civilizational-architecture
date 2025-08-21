""" 
Slot 6 — Adaptive Synthesis Engine v7.4.1 (Production Consolidation)
ΔTHRESH v6.6 | Unified Cultural & Ethical Simulation
Highlights:
- Non-recursive deep iteration (BFS) with cycle/depth caps
- Canonical forbidden mapping with boundary-safe regex
- Consent-aware simulation gating
- Constellation budget integration (Slot 5)
- Thread-safe metrics (EMA preservation rate)
- Timeout & memory caps; graceful shutdown
This single file intentionally ships with the Slot 10 adapter and
serialization helper for drop-in deployment. In large repos consider
splitting into: engine.py, adapter.py, serializers.py.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Iterable, Mapping
import time
import hashlib
import threading
import re
from collections import deque
import logging
import json
logger = logging.getLogger("synthesis_engine")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
VERSION = "7.4.1"
@dataclass(frozen=True)
class EngineConfig:
    regex_text_cap: int = 2_000_000
    max_container_depth: int = 50
    analysis_timeout: float = 5.0
    max_string_length: int = 100_000
    min_safe_adaptation: float = 0.15
    max_safe_adaptation: float = 0.85
    max_budget_relaxation: float = 0.10
class CulturalContext(Enum):
    INDIVIDUALIST = "individualist"
    COLLECTIVIST = "collectivist"
    MIXED = "mixed"
    INSTITUTIONAL = "institutional"
class SimulationResult(Enum):
    APPROVED = "approved"
    APPROVED_WITH_TRANSFORMATION = "approved_with_transformation"
    BLOCKED_BY_GUARDRAIL = "blocked_by_guardrail"
    DEFERRED_NO_CONSENT = "deferred_no_consent"
class DeploymentGuardrailResult(Enum):
    APPROVED = "APPROVED"
    REQUIRES_TRANSFORMATION = "REQUIRES_TRANSFORMATION"
    BLOCKED_PRINCIPLE_VIOLATION = "BLOCKED_PRINCIPLE_VIOLATION"
    BLOCKED_CULTURAL_SENSITIVITY = "BLOCKED_CULTURAL_SENSITIVITY"
    ERROR = "ERROR"
@dataclass(frozen=True)
class EngineMetrics:
    total_analyses: int
    successful_simulations: int
    guardrail_blocks: int
    principle_preservation_rate: float
    version: str
    engine_fingerprint: str
    config: Dict[str, Any]
@dataclass
class CulturalProfile:
    individualism_index: float = 0.5
    power_distance: float = 0.5
    uncertainty_avoidance: float = 0.5
    long_term_orientation: float = 0.5
    adaptation_effectiveness: float = 0.0
    cultural_context: CulturalContext = CulturalContext.MIXED
    method_profile: Dict[str, float] = field(default_factory=dict)
    forbidden_elements_detected: List[str] = field(default_factory=list)
    guardrail_compliance: bool = True
    principle_preservation_score: float = 1.0
@dataclass
class SynthesisResult:
    simulation_status: SimulationResult
    cultural_profile: CulturalProfile
    compliance_score: float = 1.0
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
@dataclass
class GuardrailValidationResult:
    result: DeploymentGuardrailResult
    compliance_score: float
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    transformation_required: bool = False
    max_safe_adaptation: float = 0.0
class AdaptiveSynthesisEngine:
    _DEFAULT_METHODS = {
        "greek_logic": 0.8, "buddhist_impermanence": 0.7, "confucian_precision": 0.7,
        "indigenous_longterm": 0.8, "scientific_empiricism": 0.9,
    }
    _FORBIDDEN_CANON: Mapping[str, str] = {
        "divine_revelation": "divine revelation",
        "spiritual_authority": "spiritual authority",
        "faith_based_claims": "faith based claims",
        "toxic_positivity": "toxic positivity",
        "cultural_supremacy": "cultural supremacy",
        "mystical_bypassing": "mystical bypassing",
        "manipulate": "manipulate",
        "exploit": "exploit",
    }
    _REGION_BIASES = {
        "EU": {"individualism_index": 0.6, "power_distance": 0.45, "uncertainty_avoidance": 0.55},
        "US": {"individualism_index": 0.75, "power_distance": 0.4, "uncertainty_avoidance": 0.45},
        "EA": {"individualism_index": 0.45, "power_distance": 0.55, "uncertainty_avoidance": 0.6},
        "LA": {"individualism_index": 0.5, "power_distance": 0.55, "uncertainty_avoidance": 0.55},
        "AF": {"individualism_index": 0.48, "power_distance": 0.58, "uncertainty_avoidance": 0.57},
        "ME": {"individualism_index": 0.44, "power_distance": 0.62, "uncertainty_avoidance": 0.6},
    }
    _TRIGGER_TERMS = (r"imagine|what\\s+if|pretend|role-?\\s*play|simulate|perspective|"
                      r"experience|understand\\s+how|feel\\s+like|empathize")
    _TRIGGER_PATTERN = re.compile(rf"(?<!\\w)({_TRIGGER_TERMS})(?!\\w)", flags=re.IGNORECASE)
    _FORBIDDEN_PATTERN = re.compile(r"\\b(" + "|".join(map(re.escape, _FORBIDDEN_CANON.values())) + r")\\b")
    _CLEAN_PATTERN = re.compile(r"[^a-z0-9_ ]+")
    def __init__(self, deterministic_fingerprint: str = None, config: EngineConfig = None) -> None:
        self._cfg = config or EngineConfig()
        self._metrics_lock = threading.RLock()
        self._total_analyses = 0
        self._successful_simulations = 0
        self._guardrail_blocks = 0
        self._principle_preservation_rate = 1.0
        self._instance_fingerprint = deterministic_fingerprint or hashlib.sha256(
            f"SLOT6_{VERSION}::{time.time()}".encode()
        ).hexdigest()[:16]
        self._shutdown_flag = threading.Event()
    def _now(self) -> float:
        return time.perf_counter()
    def shutdown(self):
        self._shutdown_flag.set()
    def _iter_strings_bfs(self, obj: Any) -> Iterable[str]:
        queue = deque([(obj, 0)])
        visited = set()
        MAX_VISITED = 100_000
        while queue and not self._shutdown_flag.is_set():
            current, depth = queue.popleft()
            if depth > self._cfg.max_container_depth:
                break
            oid = id(current)
            if oid in visited:
                continue
            if len(visited) >= MAX_VISITED:
                break
            visited.add(oid)
            if isinstance(current, dict):
                for k, v in current.items():
                    if isinstance(k, str) and len(k) <= self._cfg.max_string_length:
                        yield k.lower()
                    queue.append((v, depth + 1))
            elif isinstance(current, (list, tuple)):
                for item in current:
                    queue.append((item, depth + 1))
            elif isinstance(current, (str, bytes)):
                if isinstance(current, bytes):
                    try:
                        current = current.decode("utf-8", "ignore")
                    except Exception:
                        continue
                if len(current) <= self._cfg.max_string_length:
                    yield current.lower()
    def _scan_forbidden_any(self, payload: Any) -> List[str]:
        start = self._now()
        total_size = 0
        buffer: List[str] = []
        for s in self._iter_strings_bfs(payload):
            if self._now() - start > self._cfg.analysis_timeout:
                break
            if total_size >= self._cfg.regex_text_cap:
                break
            if total_size + len(s) > self._cfg.regex_text_cap:
                s = s[: self._cfg.regex_text_cap - total_size]
            buffer.append(s)
            total_size += len(s)
        if not buffer:
            return []
        cleaned = self._CLEAN_PATTERN.sub(" ", " ".join(buffer))
        hits_display = {m.group(0) for m in self._FORBIDDEN_PATTERN.finditer(cleaned)}
        reverse_map = {v: k for k, v in self._FORBIDDEN_CANON.items()}
        hits_snake = {reverse_map.get(h, h.replace(" ", "_")) for h in hits_display}
        hits_snake &= set(self._FORBIDDEN_CANON.keys())
        return sorted(hits_snake)
    def _update_principle_rate(self, compliance_penalty: float):
        target = max(0.0, 1.0 - compliance_penalty)
        alpha = 0.10
        with self._metrics_lock:
            self._principle_preservation_rate = (1 - alpha) * self._principle_preservation_rate + alpha * target
    def _apply_creativity_budget(self, base_max_safe: float, context: Dict[str, Any]) -> float:
        if not context:
            return base_max_safe
        try:
            budget = (context.get("constellation_budget") or {})
            scale = budget.get("scale", None)
            if scale is None:
                tw = float(budget.get("temporal_window", 0.02))
                depth = float(budget.get("max_depth", 1))
                scale = max(0.0, min(1.0, 0.5 * (tw - 0.02) / 0.08 + 0.5 * (depth - 1) / 2))
            scale = float(scale)
            if not (0.0 <= scale <= 1.0):
                scale = max(0.0, min(1.0, scale))
            relaxed = base_max_safe + self._cfg.max_budget_relaxation * scale
            return min(self._cfg.max_safe_adaptation, max(self._cfg.min_safe_adaptation, relaxed))
        except Exception:
            return base_max_safe
    def get_config(self) -> Dict[str, Any]:
        return asdict(self._cfg)
    def analyze_and_simulate(self, institution_name: str, payload: Dict[str, Any], context: Dict[str, Any] = None) -> SynthesisResult:
        if self._shutdown_flag.is_set():
            return SynthesisResult(
                simulation_status=SimulationResult.BLOCKED_BY_GUARDRAIL,
                cultural_profile=CulturalProfile(),
                compliance_score=0.0,
                violations=["Engine is shutting down"],
            )
        t0 = self._now()
        with self._metrics_lock:
            self._total_analyses += 1
        try:
            institution_name = str(institution_name)[:256] if institution_name else "UNKNOWN"
            context = context or {}
            payload = payload or {}
            if not isinstance(payload, dict):
                payload = {"content": str(payload)}
        except Exception:
            return SynthesisResult(
                simulation_status=SimulationResult.BLOCKED_BY_GUARDRAIL,
                cultural_profile=CulturalProfile(),
                compliance_score=0.0,
                violations=["Input validation failed"],
            )
        profile = self._generate_cultural_profile(context)
        ideology_push = False
        try:
            ideology_push = bool((payload.get("messaging") or {}).get("ideology"))
        except Exception:
            pass
        compliance_penalty = 0.05 if ideology_push else 0.0
        try:
            forbidden_hits = self._scan_forbidden_any({"institution": institution_name, "payload": payload})
        except Exception:
            forbidden_hits = ["SCAN_ERROR"]
        if forbidden_hits:
            with self._metrics_lock:
                self._guardrail_blocks += 1
            self._update_principle_rate(1.0)
            return SynthesisResult(
                simulation_status=SimulationResult.BLOCKED_BY_GUARDRAIL,
                cultural_profile=profile,
                compliance_score=0.0,
                violations=[f"FORBIDDEN_ELEMENTS:{','.join(forbidden_hits)}"],
            )
        simulation_requested = False
        has_consent = False
        try:
            content = json.dumps({"institution": institution_name, "payload": payload}, ensure_ascii=False)[:10000]
            simulation_requested = bool(self._TRIGGER_PATTERN.search(content))
            has_consent = context.get("explicit_consent", False) or context.get("educational_context", False)
        except Exception:
            pass
        if simulation_requested and not has_consent:
            return SynthesisResult(
                simulation_status=SimulationResult.DEFERRED_NO_CONSENT,
                cultural_profile=profile,
                violations=["Simulation requested without sufficient consent"],
            )
        base_max = self._max_safe_adaptation(profile)
        max_safe_adapt = self._apply_creativity_budget(base_max, context)
        if profile.adaptation_effectiveness > max_safe_adapt:
            rec = f"Reduce adaptation_effectiveness from {profile.adaptation_effectiveness:.2f} to <= {max_safe_adapt:.2f}"
            profile.adaptation_effectiveness = max_safe_adapt
            with self._metrics_lock:
                self._successful_simulations += 1
            self._update_principle_rate(compliance_penalty)
            return SynthesisResult(
                simulation_status=SimulationResult.APPROVED_WITH_TRANSFORMATION,
                cultural_profile=profile,
                compliance_score=max(0.0, 0.9 - compliance_penalty),
                recommendations=[rec],
            )
        with self._metrics_lock:
            self._successful_simulations += 1
        self._update_principle_rate(compliance_penalty)
        return SynthesisResult(
            simulation_status=SimulationResult.APPROVED,
            cultural_profile=profile,
            compliance_score=max(0.0, 1.0 - compliance_penalty),
        )
    def _generate_cultural_profile(self, context: Dict[str, Any]) -> CulturalProfile:
        try:
            region = (context.get("region") or "").upper()
            base = {"individualism_index": 0.5, "power_distance": 0.5, "uncertainty_avoidance": 0.5}
            if region in self._REGION_BIASES:
                for k, v in self._REGION_BIASES[region].items():
                    if k in base:
                        base[k] = max(0.0, min(1.0, v))
            clarity = float(context.get("clarity_priority", 0.5))
            foresight = float(context.get("foresight_priority", 0.5))
            empiricism = float(context.get("empiricism_priority", 0.5))
            adaptation_effectiveness = self._score_adaptation(self._DEFAULT_METHODS, clarity, foresight, empiricism)
            long_term_orientation = 0.5 * float(context.get("foresight_priority", 0.5)) + 0.5 * float(
                context.get("long_term_orientation", base.get("long_term_orientation", 0.5))
            )
            return CulturalProfile(
                individualism_index=round(base["individualism_index"], 3),
                power_distance=round(base["power_distance"], 3),
                uncertainty_avoidance=round(base["uncertainty_avoidance"], 3),
                long_term_orientation=round(long_term_orientation, 3),
                adaptation_effectiveness=round(adaptation_effectiveness, 3),
                cultural_context=self._label_context(base),
                method_profile=self._DEFAULT_METHODS.copy(),
                forbidden_elements_detected=[],
                guardrail_compliance=True,
                principle_preservation_score=self._principle_preservation_rate,
            )
        except Exception:
            return CulturalProfile(
                method_profile=self._DEFAULT_METHODS.copy(),
                forbidden_elements_detected=[],
                guardrail_compliance=False,
                principle_preservation_score=1.0,
            )
    def get_performance_metrics(self) -> Dict[str, Any]:
        with self._metrics_lock:
            snap = EngineMetrics(
                total_analyses=self._total_analyses,
                successful_simulations=self._successful_simulations,
                guardrail_blocks=self._guardrail_blocks,
                principle_preservation_rate=round(self._principle_preservation_rate, 3),
                version=VERSION,
                engine_fingerprint=self._instance_fingerprint,
                config=asdict(self._cfg),
            )
        return {
            "synthesis_metrics": {
                "total_analyses": snap.total_analyses,
                "successful_simulations": snap.successful_simulations,
                "guardrail_blocks": snap.guardrail_blocks,
                "principle_preservation_rate": snap.principle_preservation_rate,
            },
            "engine_fingerprint": snap.engine_fingerprint,
            "version": snap.version,
            "config": snap.config,
        }
    @staticmethod
    def _label_context(base: Dict[str, float]) -> CulturalContext:
        try:
            if base["individualism_index"] >= 0.65:
                return CulturalContext.INDIVIDUALIST
            if base["power_distance"] >= 0.60 or base["uncertainty_avoidance"] >= 0.65:
                return CulturalContext.COLLECTIVIST
            if base["power_distance"] >= 0.55 and base["uncertainty_avoidance"] >= 0.55:
                return CulturalContext.INSTITUTIONAL
            return CulturalContext.MIXED
        except KeyError:
            return CulturalContext.MIXED
    @staticmethod
    def _score_adaptation(methods: Dict[str, float], clarity: float, foresight: float, empiricism: float) -> float:
        clarity = max(0.0, min(1.0, clarity))
        foresight = max(0.0, min(1.0, foresight))
        empiricism = max(0.0, min(1.0, empiricism))
        score = (0.35 * methods["scientific_empiricism"] * empiricism
                 + 0.25 * methods["greek_logic"] * clarity
                 + 0.25 * methods["indigenous_longterm"] * foresight
                 + 0.10 * methods["confucian_precision"] * clarity
                 + 0.05 * methods["buddhist_impermanence"] * (1 - abs(0.5 - foresight) * 2))
        return max(0.0, min(1.0, score))
    @staticmethod
    def _max_safe_adaptation(profile: CulturalProfile) -> float:
        try:
            penalty = 0.25 * profile.power_distance + 0.15 * profile.uncertainty_avoidance
            return max(0.15, min(0.85, 0.45 + (0.15 - penalty)))
        except AttributeError:
            return 0.85
def synthesis_result_to_dict(res: SynthesisResult) -> Dict[str, Any]:
    try:
        return {
            "simulation_status": res.simulation_status.value,
            "cultural_profile": asdict(res.cultural_profile),
            "compliance_score": res.compliance_score,
            "violations": res.violations,
            "recommendations": res.recommendations,
        }
    except Exception:
        return {"error": "Serialization failed"}
class MulticulturalTruthSynthesisAdapter:
    def __init__(self, engine: AdaptiveSynthesisEngine):
        self.engine = engine
    def analyze_cultural_context(self, institution_name: str, ctx: Optional[Dict[str, Any]] = None) -> CulturalProfile:
        try:
            res = self.engine.analyze_and_simulate(institution_name, {"content": ""}, ctx or {})
            return res.cultural_profile
        except Exception:
            return CulturalProfile()
    def validate_cultural_deployment(self, profile: CulturalProfile, institution_type: str, payload: Dict[str, Any]) -> GuardrailValidationResult:
        try:
            res = self.engine.analyze_and_simulate(institution_type, payload, {})
            status_map = {
                SimulationResult.APPROVED: DeploymentGuardrailResult.APPROVED,
                SimulationResult.APPROVED_WITH_TRANSFORMATION: DeploymentGuardrailResult.REQUIRES_TRANSFORMATION,
                SimulationResult.BLOCKED_BY_GUARDRAIL: DeploymentGuardrailResult.BLOCKED_PRINCIPLE_VIOLATION,
                SimulationResult.DEFERRED_NO_CONSENT: DeploymentGuardrailResult.BLOCKED_CULTURAL_SENSITIVITY,
            }
            return GuardrailValidationResult(
                result=status_map.get(res.simulation_status, DeploymentGuardrailResult.ERROR),
                compliance_score=res.compliance_score,
                violations=res.violations,
                recommendations=res.recommendations,
                transformation_required=(res.simulation_status == SimulationResult.APPROVED_WITH_TRANSFORMATION),
                max_safe_adaptation=AdaptiveSynthesisEngine._max_safe_adaptation(profile),
            )
        except Exception:
            return GuardrailValidationResult(
                result=DeploymentGuardrailResult.ERROR,
                compliance_score=0.0,
                violations=["Validation process failed"],
                recommendations=["Check system logs"],
                transformation_required=False,
                max_safe_adaptation=AdaptiveSynthesisEngine._max_safe_adaptation(profile),
            )
if __name__ == "__main__":
    eng = AdaptiveSynthesisEngine()
    res = eng.analyze_and_simulate("Demo", {"content": "imagine safe scenario"}, {"educational_context": True})
    print(res.simulation_status.value, res.compliance_score)
