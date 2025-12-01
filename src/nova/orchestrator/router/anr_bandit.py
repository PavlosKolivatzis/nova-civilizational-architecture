"""
ANR LinUCB Bandit with Bulletproof State Persistence

Production-grade contextual bandit for Adaptive Neural Routing with:
- Cross-platform file locking (Windows msvcrt / Unix fcntl)
- Atomic writes with crash safety
- Multi-process coordination
- Prometheus metrics integration
"""

import json
import os
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from nova.orchestrator.anr_mutex import file_lock, save_json_atomic

logger = logging.getLogger(__name__)


class LinUCBBandit:
    """LinUCB contextual bandit with bulletproof persistence."""

    def __init__(
        self,
        arms: List[str],
        context_dim: int,
        alpha: float = 1.0,
        state_path: Optional[str] = None,
        save_interval: int = 10,
    ):
        self.arms = arms
        self.context_dim = context_dim
        self.alpha = alpha
        self.state_path = state_path
        self.save_interval = save_interval
        self.save_counter = 0

        # LinUCB matrices: A_a = I + X_a^T X_a, b_a = X_a^T r_a
        self.A = {arm: np.eye(context_dim) for arm in arms}
        self.b = {arm: np.zeros(context_dim) for arm in arms}
        self.total_pulls = {arm: 0 for arm in arms}
        self.total_reward = {arm: 0.0 for arm in arms}

        # State tracking
        self.last_context = None
        self.last_selected_arm = None
        self.last_update_time = time.time()

        # Load existing state if available
        if state_path:
            self._load_state()

    def _get_theta(self, arm: str) -> np.ndarray:
        """Compute theta_a = A_a^{-1} b_a."""
        try:
            return np.linalg.solve(self.A[arm], self.b[arm])
        except np.linalg.LinAlgError:
            # Fallback for singular matrix
            return np.linalg.pinv(self.A[arm]) @ self.b[arm]

    def _get_confidence_bound(self, arm: str, context: np.ndarray) -> float:
        """Compute confidence bound for LinUCB upper confidence."""
        try:
            A_inv = np.linalg.inv(self.A[arm])
            cb = self.alpha * np.sqrt(context.T @ A_inv @ context)
            return float(cb)
        except np.linalg.LinAlgError:
            # Fallback for numerical issues
            return self.alpha

    def select_arm(self, context: np.ndarray) -> Tuple[str, Dict[str, float]]:
        """Select arm using LinUCB algorithm."""
        context = np.array(context).reshape(-1, 1)

        if context.shape[0] != self.context_dim:
            raise ValueError(f"Context dimension mismatch: expected {self.context_dim}, got {context.shape[0]}")

        # Compute upper confidence bounds for all arms
        scores = {}
        confidence_bounds = {}

        for arm in self.arms:
            theta = self._get_theta(arm)
            expected_reward = float(theta.T @ context)
            confidence_bound = self._get_confidence_bound(arm, context)

            scores[arm] = expected_reward + confidence_bound
            confidence_bounds[arm] = confidence_bound

        # Select arm with highest upper confidence bound
        selected_arm = max(scores, key=scores.get)

        # Store for potential reward update
        self.last_context = context.copy()
        self.last_selected_arm = selected_arm

        # Return metadata for observability
        metadata = {
            "selected_score": scores[selected_arm],
            "confidence_bound": confidence_bounds[selected_arm],
            "arm_scores": scores,
            "total_pulls": dict(self.total_pulls),
        }

        return selected_arm, metadata

    def update_reward(self, reward: float) -> bool:
        """Update bandit with reward for last selected arm."""
        if self.last_selected_arm is None or self.last_context is None:
            logger.warning("No previous selection to update")
            return False

        arm = self.last_selected_arm
        context = self.last_context

        # LinUCB update: A_a += x_t x_t^T, b_a += r_t x_t
        self.A[arm] += context @ context.T
        self.b[arm] += reward * context.flatten()

        # Statistics tracking
        self.total_pulls[arm] += 1
        self.total_reward[arm] += reward
        self.last_update_time = time.time()

        # Reset last selection
        self.last_context = None
        self.last_selected_arm = None

        # Periodic state persistence
        self.save_counter += 1
        if self.state_path and self.save_counter >= self.save_interval:
            self._save_state()
            self.save_counter = 0

        return True

    def get_arm_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all arms."""
        stats = {}
        for arm in self.arms:
            theta = self._get_theta(arm)
            stats[arm] = {
                "total_pulls": self.total_pulls[arm],
                "total_reward": self.total_reward[arm],
                "avg_reward": (
                    self.total_reward[arm] / self.total_pulls[arm]
                    if self.total_pulls[arm] > 0 else 0.0
                ),
                "theta_norm": float(np.linalg.norm(theta)),
                "matrix_condition": float(np.linalg.cond(self.A[arm])),
            }
        return stats

    def _state_dict(self) -> Dict[str, Any]:
        """Serialize bandit state to JSON-compatible dict."""
        return {
            "version": "1.0",
            "arms": self.arms,
            "context_dim": self.context_dim,
            "alpha": self.alpha,
            "A": {arm: self.A[arm].tolist() for arm in self.arms},
            "b": {arm: self.b[arm].tolist() for arm in self.arms},
            "total_pulls": dict(self.total_pulls),
            "total_reward": dict(self.total_reward),
            "last_update_time": self.last_update_time,
            "save_counter": self.save_counter,
        }

    def _save_state(self) -> bool:
        """Save bandit state atomically with file locking."""
        if not self.state_path:
            return False

        try:
            lock_path = f"{self.state_path}.lock"
            with file_lock(lock_path, timeout=10.0):
                save_json_atomic(self.state_path, self._state_dict())

            logger.debug(f"Saved ANR bandit state to {self.state_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save ANR bandit state: {e}")
            return False

    def _load_state(self) -> bool:
        """Load bandit state from file."""
        if not os.path.exists(self.state_path):
            logger.info(f"No existing state file: {self.state_path}")
            return False

        try:
            with open(self.state_path, 'rb') as f:
                data = f.read()
            state = json.loads(data.decode('utf-8'))

            # Validate version compatibility
            if state.get("version") != "1.0":
                logger.warning(f"State version mismatch: {state.get('version')}")
                return False

            # Validate arms match
            if set(state["arms"]) != set(self.arms):
                logger.warning("Arms mismatch in state file")
                return False

            # Restore matrices and statistics
            self.context_dim = state["context_dim"]
            self.alpha = state["alpha"]

            for arm in self.arms:
                self.A[arm] = np.array(state["A"][arm])
                self.b[arm] = np.array(state["b"][arm])
                self.total_pulls[arm] = state["total_pulls"][arm]
                self.total_reward[arm] = state["total_reward"][arm]

            self.last_update_time = state.get("last_update_time", time.time())
            self.save_counter = state.get("save_counter", 0)

            logger.info(f"Loaded ANR bandit state from {self.state_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load ANR bandit state: {e}")
            return False

    def force_save(self) -> bool:
        """Force immediate state save regardless of save_interval."""
        return self._save_state()

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information for monitoring."""
        total_pulls = sum(self.total_pulls.values())
        return {
            "total_decisions": total_pulls,
            "arm_distribution": {
                arm: (pulls / total_pulls if total_pulls > 0 else 0.0)
                for arm, pulls in self.total_pulls.items()
            },
            "avg_rewards": {
                arm: (reward / pulls if pulls > 0 else 0.0)
                for arm, (reward, pulls) in zip(
                    self.arms,
                    [(self.total_reward[arm], self.total_pulls[arm]) for arm in self.arms]
                )
            },
            "last_update_age_s": time.time() - self.last_update_time,
            "state_path": self.state_path,
            "save_counter": self.save_counter,
        }
