from __future__ import annotations

import os
import unicodedata
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional

from .safety_policy import basic_safety_policy
from .publish import publish_phase_lock_to_mirror


@dataclass(frozen=True)
class EmotionConfig:
    max_content_length: int = 10_000
    # score thresholds ([-1..1]) that map to tone labels
    positive_threshold: float = 0.10
    negative_threshold: float = -0.10
    # negation flips the next N sentiment tokens
    negation_window: int = 3
    # intensifiers: scale each matching token's magnitude
    boosters: Dict[str, float] = None
    dampeners: Dict[str, float] = None
    # default policy hooks executed after analysis
    policy_hooks: List[Callable[[Dict], None]] = None

    def __post_init__(self):
        # immutability-friendly defaults
        object.__setattr__(self, "boosters", self.boosters or {
            "very": 1.5, "really": 1.4, "extremely": 1.7, "so": 1.3, "super": 1.6
        })
        object.__setattr__(self, "dampeners", self.dampeners or {
            "slightly": 0.6, "somewhat": 0.7, "a_bit": 0.7, "kinda": 0.6, "barely": 0.5
        })
        object.__setattr__(self, "policy_hooks", self.policy_hooks or [basic_safety_policy])


class EmotionalMatrixEngine:
    """Slot 3 – Emotional Matrix (lightweight, deterministic).

    v0.3.0 changes:
      - Unicode normalization (NFKC), simple HTML/script guard
      - Faster tokenization via str.translate (no regex)
      - Negation handling with small lookahead window
      - Intensifiers (boosters/dampeners) and exclamation emphasis
      - Configurable thresholds; optional policy hook preserved
    """

    __version__ = "0.3.0"

    # translation table: strip punctuation to tokens (ASCII + a few extras)
    _PUNCT_TABLE = str.maketrans({
        **{c: " " for c in ".,!?;:()[]{}<>\"'`~|/\\@#%^&*+=\t\n\r"},
        "—": " ", "–": " ", "…": " ",
    })

    # sentiment lexicons (expanded but still lightweight)
    _POSITIVE = {
        "good", "great", "happy", "fantastic", "excellent", "love", "awesome",
        "nice", "wonderful", "brilliant", "amazing", "delightful", "joyful",
        "pleased", "superb", "outstanding", "marvelous", "cheerful", "upbeat",
    }
    _NEGATIVE = {
        "bad", "sad", "terrible", "hate", "awful", "horrible", "worse", "worst",
        "disgusting", "annoying", "dreadful", "abysmal", "miserable", "horrendous",
        "depressing", "lousy", "unhappy", "wretched", "frustrating",
    }
    _NEGATORS = {
        "not", "no", "never", "without", "hardly", "scarcely", "isnt", "doesnt",
        "dont", "wasnt", "werent", "aint", "cannot", "cant"
    }

    def __init__(self, config: Optional[EmotionConfig] = None):
        self.cfg = config or EmotionConfig()
        self._last_tri_signal: Optional[Dict[str, Any]] = None

    # ---------- helpers ----------
    @staticmethod
    def _normalize(s: str) -> str:
        # Unicode NFKC removes homoglyph tricks, normalizes quotes, etc.
        return unicodedata.normalize("NFKC", s)

    @classmethod
    def _tokenize(cls, s: str) -> List[str]:
        # Faster than regex: lowercase, translate punctuation, split
        return cls._normalize(s).lower().translate(cls._PUNCT_TABLE).split()

    def _get_tri_truth_signal(self) -> Optional[Dict[str, Any]]:
        """Return cached TRI truth signal snapshot (best-effort)."""
        if self._last_tri_signal is not None:
            return self._last_tri_signal
        return self._refresh_tri_truth_signal()

    def _refresh_tri_truth_signal(self) -> Optional[Dict[str, Any]]:
        """Fetch latest TRI truth signal from Semantic Mirror."""
        try:
            from orchestrator.semantic_mirror import get_semantic_mirror

            mirror = get_semantic_mirror()
        except Exception:
            self._last_tri_signal = None
            return None

        def _mirror_get(key: str, default=None):
            try:
                return mirror.get_context(key, default=default)
            except TypeError:
                try:
                    return mirror.get_context(key, "slot03_emotional_matrix")
                except TypeError:
                    return default

        signal = _mirror_get("slot04.tri_truth_signal", default=None)
        if isinstance(signal, dict):
            self._last_tri_signal = signal
        else:
            self._last_tri_signal = None
        return self._last_tri_signal

    def _get_phase_lock(self) -> Optional[float]:
        """
        Compute phase_lock from Semantic Mirror:
        1) If NOVA_LIGHTCLOCK_DEEP=0 → disable (None)
        2) Prefer TRI phase coherence from mirror
        3) Else map Slot7 pressure to [0.45..0.60]
        4) Fallback to env SLOT07_PHASE_LOCK, else 0.5
        """
        import os
        if os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "0":
            return None

        tri_signal = self._get_tri_truth_signal()
        if tri_signal:
            coherence = tri_signal.get("tri_coherence")
            if coherence is not None:
                return float(coherence)

        # Helper to support both mirror APIs:
        #   get_context(key, requester)  (older)
        #   get_context(key, default=...) (newer)
        def _mirror_get(m, key, default=None):
            try:
                # newer signature
                return m.get_context(key, default=default)
            except TypeError:
                try:
                    # older signature: positional requester id
                    return m.get_context(key, "slot03_emotional_matrix")
                except TypeError:
                    return default

        # Try mirror import and access
        try:
            from orchestrator.semantic_mirror import get_semantic_mirror
            try:
                mirror = get_semantic_mirror()
            except Exception:
                mirror = None
        except Exception:
            mirror = None

        # 2) TRI phase coherence wins if present
        if mirror is not None:
            phase = _mirror_get(mirror, "slot04.phase_coherence", default=None)
            if phase is not None:
                return float(phase)

            # 3) Else map Slot7 pressure → phase_lock
            pressure = _mirror_get(mirror, "slot07.pressure_level", default=None)
            if pressure is not None:
                p = max(0.0, min(1.0, float(pressure)))
                return float(0.60 - 0.15 * p)

        # 4) Fallback chain: env → hard default
        try:
            env_phase = os.getenv("SLOT07_PHASE_LOCK", None)
            if env_phase is not None:
                return float(env_phase)
        except Exception:
            pass
        return 0.5

    def _apply_phase_lock_scaling(self, score: float, phase_lock: Optional[float]) -> float:
        """Apply coherence-aware affect scaling when phase_lock < threshold."""
        thresh = float(os.getenv("NOVA_EMO_PHASE_LOCK_THRESH", "0.6"))
        if phase_lock is None or phase_lock >= thresh:
            return score

        # Low coherence: dampen strong emotions, preserve neutral
        damping_factor = 0.8  # Reduce emotional intensity by 20%
        return score * damping_factor

    # ---------- public API ----------
    def analyze(self, content: str, *, policy_hook: Optional[Callable[[Dict], None]] = None) -> Dict:
        """Return {'emotional_tone','score','confidence', 'explain':{...}}"""

        if not isinstance(content, str):
            raise TypeError("content must be a string")
        if len(content) > self.cfg.max_content_length:
            raise ValueError("content exceeds maximum allowed length")

        lower = self._normalize(content).lower()
        # cheap HTML/script guard; we keep it minimal but effective
        if "<script" in lower or "</script>" in lower or "<iframe" in lower:
            raise ValueError("potentially unsafe content detected")

        tri_signal = self._refresh_tri_truth_signal()

        tokens = self._tokenize(lower)
        if not tokens:
            metrics = {"emotional_tone": "unknown", "score": 0.0, "confidence": 0.0, "explain": {"matches": 0}}
            self._apply_policy_hooks(metrics, policy_hook)
            return metrics

        pos, neg, matched = 0.0, 0.0, 0
        i = 0
        while i < len(tokens):
            t = tokens[i]
            # map common bigrams like "a bit" into single token handled by dampeners
            if i + 1 < len(tokens) and t == "a" and tokens[i + 1] == "bit":
                t = "a_bit"
                i += 1  # consume the next
            # intensifiers scale the very next sentiment token
            intens = 1.0
            if t in self.cfg.boosters:
                intens = self.cfg.boosters[t]
            elif t in self.cfg.dampeners:
                intens = self.cfg.dampeners[t]

            # negation flips the next N sentiment tokens
            neg_window = self.cfg.negation_window if t in self._NEGATORS else 0

            # lookahead to find the next sentiment token and apply modifiers
            applied = False
            j = i + 1 if (t in self.cfg.boosters or t in self.cfg.dampeners or neg_window) else i
            window_left = neg_window
            while j < len(tokens) and (j == i or window_left > 0):
                tj = tokens[j]
                val = 0.0
                if tj in self._POSITIVE:
                    val = +1.0
                elif tj in self._NEGATIVE:
                    val = -1.0

                if val != 0.0:
                    if neg_window or window_left > 0:
                        val = -val
                        window_left -= 1
                    val *= intens
                    if val > 0:
                        pos += val
                    else:
                        neg += -val
                    matched += 1
                    applied = True
                    # Continue processing more tokens in negation window instead of breaking
                    if window_left <= 0 and not (t in self.cfg.boosters or t in self.cfg.dampeners):
                        break  # Only break when negation window is exhausted and not handling intensifiers
                j += 1

            # If current token itself is sentiment and we didn't treat it via lookahead
            if not applied:
                val = 0.0
                if t in self._POSITIVE:
                    val = +1.0 * intens
                elif t in self._NEGATIVE:
                    val = -1.0 * intens

                if val != 0.0:
                    if neg_window:
                        val = -val
                    if val > 0:
                        pos += val
                    else:
                        neg += -val
                    matched += 1

            i += 1

        total_signal = pos + neg
        score = 0.0 if total_signal == 0 else (pos - neg) / total_signal

        # exclamation emphasis (cap small boost)
        if "!" in lower:
            score *= 1.05 if score >= 0 else 1.0  # only boost positive affect slightly

        # Tone mapping
        if score >= self.cfg.positive_threshold:
            tone = "positive"
        elif score <= self.cfg.negative_threshold:
            tone = "negative"
        else:
            tone = "neutral"

        # Confidence = proportion of matched sentiment tokens (Laplace-smoothed)
        confidence = min(1.0, matched / (len(tokens) + 2))

        metrics = {
            "emotional_tone": tone,
            "score": float(max(-1.0, min(1.0, score))),
            "confidence": float(confidence),
            "explain": {
                "matched": matched,
                "pos_strength": round(pos, 4),
                "neg_strength": round(neg, 4),
            },
            "version": self.__version__,
        }

        if tri_signal:
            metrics["tri_signal"] = tri_signal
            metrics["tri_coherence"] = tri_signal.get("tri_coherence")
            metrics["tri_band"] = tri_signal.get("tri_band")
            annotations = metrics.setdefault("annotations", {})
            if tri_signal.get("tri_band"):
                annotations["tri_band"] = tri_signal["tri_band"]

        # Light-Clock coherence-aware scaling
        phase_lock = self._get_phase_lock()
        # Publish for Slot10/Slot7 gate logic (best-effort; advisory)
        publish_phase_lock_to_mirror(phase_lock)
        scaled_score = self._apply_phase_lock_scaling(metrics["score"], phase_lock)
        if scaled_score != metrics["score"]:
            metrics["score"] = scaled_score
            metrics.setdefault("annotations", {})["phase_lock"] = phase_lock
            metrics["annotations"]["lightclock_adjustment"] = "dampened_20pct"

        self._apply_policy_hooks(metrics, policy_hook)

        return metrics

    # tiny helper for batch use in pipelines
    def analyze_batch(self, contents: Iterable[str]) -> List[Dict]:
        return [self.analyze(c) for c in contents]

    # internal helper to apply configured and extra policy hooks
    def _apply_policy_hooks(self, metrics: Dict, extra_hook: Optional[Callable[[Dict], None]]) -> None:
        hooks = list(self.cfg.policy_hooks)
        if extra_hook:
            hooks.append(extra_hook)
        for hook in hooks:
            try:
                hook(metrics)
            except Exception:
                metrics["policy_error"] = "policy hook failure"
                break
