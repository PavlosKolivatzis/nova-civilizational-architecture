"""Phase 5.1 LinUCB bandit + JSON persistence.

- Uses NumPy if available; otherwise raises ImportError (ANR will degrade to ε-greedy).
- Thread-safe updates; simple JSON state file.
"""
from __future__ import annotations
from typing import Dict
import json, os, threading

try:
    import numpy as np  # type: ignore
except Exception as e:  # pragma: no cover
    np = None  # Allow router to degrade gracefully

class LinUCB:
    def __init__(self, dim: int, alpha: float = 0.8, ridge: float = 1e-2):
        if np is None:
            raise ImportError("NumPy required for LinUCB")
        self.dim = dim
        self.alpha = float(alpha)
        self.A = np.eye(dim) * float(ridge)   # d×d
        self.b = np.zeros((dim,))             # d
        self._Ainv = np.linalg.inv(self.A)
        self._lock = threading.Lock()

    def score(self, x) -> float:
        with self._lock:
            theta = self._Ainv @ self.b
            mean = float(theta @ x)
            bonus = self.alpha * float((x @ self._Ainv @ x) ** 0.5)
            return mean + bonus

    def update(self, x, r: float) -> None:
        with self._lock:
            self.A += np.outer(x, x)
            self.b += float(r) * x
            self._Ainv = np.linalg.inv(self.A)

class BanditStore:
    """JSON persistence for per-route LinUCB models."""
    def __init__(self, path: str, routes, dim: int, alpha: float, ridge: float):
        self.path = path
        self.routes = list(routes)
        self.dim = int(dim)
        self.alpha = float(alpha)
        self.ridge = float(ridge)
        self.models: Dict[str, LinUCB] = {}
        self._lock = threading.Lock()
        self._init_models()
        self.load()

    def _init_models(self):
        if np is None:
            return
        for r in self.routes:
            self.models[r] = LinUCB(self.dim, self.alpha, self.ridge)

    def load(self):
        if np is None or not os.path.exists(self.path):
            return
        with self._lock, open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for r, s in data.items():
            if r in self.models:
                m = self.models[r]
                m.A = np.array(s["A"], dtype=float)
                m.b = np.array(s["b"], dtype=float)
                m._Ainv = np.linalg.inv(m.A)

    def save(self):
        if np is None:
            return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with self._lock, open(self.path, "w", encoding="utf-8") as f:
            json.dump({r: {"A": m.A.tolist(), "b": m.b.tolist()} for r, m in self.models.items()}, f)

    def score(self, route: str, x) -> float:
        return self.models[route].score(x)

    def update(self, route: str, x, r: float):
        self.models[route].update(x, r)