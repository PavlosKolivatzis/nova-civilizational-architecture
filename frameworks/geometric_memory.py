from __future__ import annotations

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class GeometricMemory:
    """Opt-in cache/embedding facade.

    The underlying geometric memory core is omitted for brevity; this
    facade exposes a small in-memory cache suitable for tests. When
    ``enabled`` is ``False`` all operations degrade to no-ops.
    """

    enabled: bool = False
    _store: Dict[str, Tuple[float, Any]] = field(default_factory=dict)

    def get(self, key: str) -> Any:
        if not self.enabled:
            return None
        try:
            expiry, value = self._store[key]
            if expiry < time.time():
                self._store.pop(key, None)
                return None
            return value
        except KeyError:
            return None

    def put(self, key: str, value: Any, ttl_s: int = 60) -> None:
        if not self.enabled:
            return
        self._store[key] = (time.time() + ttl_s, value)

    def similar(self, query: str, k: int = 1) -> List[str]:
        if not self.enabled or not self._store:
            return []
        # simple cosine distance on key hashing for demonstration
        def _vec(s: str) -> Tuple[float, float]:
            digest = hashlib.sha256(s.encode()).hexdigest()
            h1 = int(digest[:16], 16)
            h2 = int(digest[16:32], 16)
            return math.cos(h1), math.sin(h2)

        qv = _vec(query)
        scores = []
        for key in self._store.keys():
            kv = _vec(key)
            dot = qv[0] * kv[0] + qv[1] * kv[1]
            scores.append((dot, key))
        scores.sort(reverse=True)
        return [k for _, k in scores[:k]]
