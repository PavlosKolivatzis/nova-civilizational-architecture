from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional


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

    def __post_init__(self):
        # immutability-friendly defaults
        object.__setattr__(self, "boosters", self.boosters or {
            "very": 1.5, "really": 1.4, "extremely": 1.7, "so": 1.3, "super": 1.6
        })
        object.__setattr__(self, "dampeners", self.dampeners or {
            "slightly": 0.6, "somewhat": 0.7, "a_bit": 0.7, "kinda": 0.6, "barely": 0.5
        })


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

    # small, hand-curated lexicons (intentionally tiny)
    _POSITIVE = {
        "good", "great", "happy", "fantastic", "excellent", "love", "awesome",
        "nice", "wonderful", "brilliant", "amazing",
    }
    _NEGATIVE = {
        "bad", "sad", "terrible", "hate", "awful", "horrible", "worse", "worst",
        "disgusting", "annoying",
    }
    _NEGATORS = {
        "not", "no", "never", "without", "hardly", "scarcely", "isnt", "doesnt",
        "dont", "wasnt", "werent", "aint", "cannot", "cant"
    }

    def __init__(self, config: Optional[EmotionConfig] = None):
        self.cfg = config or EmotionConfig()

    # ---------- helpers ----------
    @staticmethod
    def _normalize(s: str) -> str:
        # Unicode NFKC removes homoglyph tricks, normalizes quotes, etc.
        return unicodedata.normalize("NFKC", s)

    @classmethod
    def _tokenize(cls, s: str) -> List[str]:
        # Faster than regex: lowercase, translate punctuation, split
        return cls._normalize(s).lower().translate(cls._PUNCT_TABLE).split()

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

        tokens = self._tokenize(lower)
        if not tokens:
            metrics = {"emotional_tone": "unknown", "score": 0.0, "confidence": 0.0, "explain": {"matches": 0}}
            if policy_hook:
                try: policy_hook(metrics)
                except Exception: metrics["policy_error"] = "policy hook failure"
            return metrics

        pos, neg, matched = 0.0, 0.0, 0
        i = 0
        while i < len(tokens):
            t = tokens[i]
            # map common bigrams like "a bit" into single token handled by dampeners
            if i + 1 < len(tokens) and t == "a" and tokens[i + 1] == "bit":
                t = "a_bit"; i += 1  # consume the next
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
                    if val > 0: pos += val
                    else: neg += -val
                    matched += 1
                    applied = True
                    # Continue processing more tokens in negation window instead of breaking
                    if window_left <= 0 and not (t in self.cfg.boosters or t in self.cfg.dampeners):
                        break  # Only break when negation window is exhausted and not handling intensifiers
                j += 1

            # If current token itself is sentiment and we didn't treat it via lookahead
            if not applied:
                val = 0.0
                if t in self._POSITIVE: val = +1.0 * intens
                elif t in self._NEGATIVE: val = -1.0 * intens

                if val != 0.0:
                    if neg_window: val = -val
                    if val > 0: pos += val
                    else: neg += -val
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

        if policy_hook:
            try:
                policy_hook(metrics)
            except Exception:
                metrics["policy_error"] = "policy hook failure"

        return metrics

    # tiny helper for batch use in pipelines
    def analyze_batch(self, contents: Iterable[str]) -> List[Dict]:
        return [self.analyze(c) for c in contents]

