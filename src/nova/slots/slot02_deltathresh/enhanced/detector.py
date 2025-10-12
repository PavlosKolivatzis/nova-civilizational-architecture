"""Enhanced pattern detection utilities."""

from __future__ import annotations

import hashlib
import re
import threading
from typing import Dict

from .config import EnhancedProcessingConfig
from ..patterns import PatternDetector


class EnhancedPatternDetector(PatternDetector):
    """Advanced pattern detection with simple caching."""

    def __init__(self, config: EnhancedProcessingConfig):
        super().__init__(config)
        self.config = config
        self.pattern_cache: Dict[str, Dict[str, float]] = {}
        self._cache_lock = threading.RLock()
        self.manipulation_patterns = self._load_manipulation_patterns()

    def _load_manipulation_patterns(self) -> Dict[str, list[tuple[str, float]]]:
        return {
            "delta": [
                (r"\b(as an expert|trust me|believe me)\b", 0.9),
                (r"\bI know\b", 0.6),
            ]
        }

    def detect_patterns_advanced(self, content: str) -> Dict[str, float]:
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        if self.config.cache_enabled:
            with self._cache_lock:
                if content_hash in self.pattern_cache:
                    return self.pattern_cache[content_hash]

        result = {
            "delta": self._analyze_delta(content),
            "contextual_consistency": self._contextual_consistency(content),
        }

        if self.config.cache_enabled:
            with self._cache_lock:
                self.pattern_cache[content_hash] = result
        return result

    def _analyze_delta(self, content: str) -> float:
        score = 0.0
        text = content.lower()
        for pattern, weight in self.manipulation_patterns["delta"]:
            matches = len(re.findall(pattern, text))
            score += matches * weight * 0.1
        return min(1.0, score)

    def _contextual_consistency(self, content: str) -> float:
        sentences = [s.strip() for s in re.split(r"[.!?]+", content) if s.strip()]
        if len(sentences) <= 1:
            return 0.5
        unique_words = set()
        total_words = 0
        for s in sentences:
            words = s.split()
            unique_words.update(words)
            total_words += len(words)
        if total_words == 0:
            return 0.5
        diversity = len(unique_words) / total_words
        return max(0.1, min(1.0, 1.0 - abs(diversity - 0.6)))
