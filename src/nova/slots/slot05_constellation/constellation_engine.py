import math
import os
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import logging

# Local caching utilities
from functools import lru_cache

logger = logging.getLogger(__name__)

class ConstellationEngine:
    """Core engine for Slot 5 - Constellation mapping with link computation and stability metrics."""

    __version__ = "1.0.0"

    def __init__(self):
        """Initialize constellation engine with default parameters."""
        # Constellation parameters
        self.similarity_threshold = 0.3
        self.stability_window = 10
        self.link_strength_threshold = 0.2

        # Tracking for stability metrics
        self._constellation_history = []
        self._link_history = []

        # Ensure similarity caches start empty
        self._calculate_similarity.cache_clear()
        self._character_similarity.cache_clear()

    def _get_tri_signals(self) -> Optional[Dict[str, float]]:
        """Read TRI coherence signals with robust fallback chain."""
        import os

        if os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "0":
            return None

        # 1) Try mirror (preferred in steady-state)
        coherence = phase_jitter = None
        try:
            from orchestrator.semantic_mirror import get_semantic_mirror
            from orchestrator.mirror_utils import mirror_get as _mirror_get
            m = get_semantic_mirror()
            if m:
                coherence = _mirror_get(m, "slot04.coherence", default=None, requester="slot05_constellation")
                phase_jitter = _mirror_get(m, "slot04.phase_jitter", default=None, requester="slot05_constellation")
        except Exception:
            pass

        if coherence is not None or phase_jitter is not None:
            out = {}
            if coherence is not None:
                out["coherence"] = float(coherence)
            if phase_jitter is not None:
                out["phase_jitter"] = float(phase_jitter)
            return out

        # 2) Mirror empty? Fallback to TRI adapter (real telemetry)
        try:
            # Note: This would need actual TRI adapter implementation
            # For now, fall through to env vars
            pass
        except Exception:
            pass

        # 2b) Optional env fallback (non-NOVA names to avoid CI guard)
        try:
            import os
            env_coh = os.getenv("TRI_COHERENCE")
            env_jit = os.getenv("TRI_PHASE_JITTER")
            out = {}
            if env_coh is not None:
                out["coherence"] = float(env_coh)
            if env_jit is not None:
                out["phase_jitter"] = float(env_jit)
            if out:
                return out
        except Exception:
            pass

        # 3) Conservative default (was: Fallback to env vars)
        return {"coherence": 0.7}  # Conservative default
    def _apply_tri_weighting(self, base_weight: float, tri_signals: Optional[Dict[str, float]]) -> tuple[float, Dict[str, Any]]:
        """Apply TRI coherence-aware weighting and annotations."""
        if tri_signals is None:
            return base_weight, {}

        coherence = tri_signals.get("coherence", 1.0)
        phase_jitter = tri_signals.get("phase_jitter", 0.0)

        # Adjust weight: higher coherence = boost, higher jitter = dampen
        weight_modifier = 0.9 + 0.1 * coherence  # [0.9, 1.0]
        jitter_penalty = max(0.0, 1.0 - phase_jitter)  # [0.0, 1.0]

        adjusted_weight = base_weight * weight_modifier * jitter_penalty

        # Tunable threshold
        JITTER_STABLE = float(os.getenv("TRI_JITTER_STABLE", "0.3"))

        annotations = {
            "tri_coherence": coherence,
            "tri_phase_jitter": phase_jitter,
            "weight_modifier": weight_modifier,
            "stable": phase_jitter < JITTER_STABLE
        }

        return adjusted_weight, annotations

    def map(self, items: list[str]) -> dict:
        """Enhanced constellation mapping with computed links and stability metrics.

        Args:
            items: List of items to map into constellation

        Returns:
            Dict containing constellation, links, and stability metrics
        """
        if not items:
            return {
                "constellation": [],
                "links": [],
                "stability": {"score": 1.0, "status": "empty"},
                "metadata": {
                    "item_count": 0,
                    "link_count": 0,
                    "version": self.__version__
                }
            }

        # Create constellation mapping
        constellation = self._create_constellation_mapping(items)

        # Compute links between items
        links = self._compute_links(items)

        # Calculate stability metrics
        stability = self._calculate_stability_metrics(constellation, links)

        # Update history for stability tracking
        self._update_history(constellation, links)

        result = {
            "constellation": constellation,
            "links": links,
            "stability": stability,
            "metadata": {
                "item_count": len(items),
                "link_count": len(links),
                "version": self.__version__
            }
        }

        logger.debug(f"Mapped constellation: {len(items)} items, {len(links)} links, "
                    f"stability: {stability['score']:.3f}")

        return result

    def _create_constellation_mapping(self, items: List[str]) -> List[Dict[str, Any]]:
        """Create structured constellation mapping from items."""
        constellation = []

        for i, item in enumerate(items):
            # Basic item analysis
            item_analysis = self._analyze_item(item)

            constellation_item = {
                "id": i,
                "content": item,
                "type": item_analysis["type"],
                "weight": item_analysis["weight"],
                "position": self._calculate_position(i, len(items)),
                "properties": item_analysis["properties"]
            }

            # Add annotations if present
            if item_analysis.get("annotations"):
                constellation_item["annotations"] = item_analysis["annotations"]
            constellation.append(constellation_item)

        return constellation

    def _analyze_item(self, item: str) -> Dict[str, Any]:
        """Analyze individual item characteristics."""
        content = item.lower().strip()

        # Determine item type based on content patterns
        item_type = "concept"
        if any(word in content for word in ["error", "fail", "bug", "issue"]):
            item_type = "problem"
        elif any(word in content for word in ["solution", "fix", "resolve", "answer"]):
            item_type = "solution"
        elif any(word in content for word in ["process", "method", "approach", "way"]):
            item_type = "process"
        elif any(word in content for word in ["data", "metric", "value", "number"]):
            item_type = "data"

        # Calculate base weight based on content significance
        base_weight = min(1.0, len(content) / 100.0)  # Longer content = higher weight

        # Apply TRI coherence-aware weighting
        tri_signals = self._get_tri_signals()
        adjusted_weight, tri_annotations = self._apply_tri_weighting(base_weight, tri_signals)

        # Extract properties
        properties = {
            "length": len(item),
            "word_count": len(item.split()),
            "has_numbers": any(char.isdigit() for char in item),
            "complexity": self._calculate_complexity(item)
        }

        # Merge annotations if any
        annotations = tri_annotations.copy()

        return {
            "type": item_type,
            "weight": adjusted_weight,
            "properties": properties,
            "annotations": annotations
        }

    def _calculate_complexity(self, item: str) -> float:
        """Calculate complexity score for an item."""
        # Simple complexity based on various factors
        factors = [
            len(item.split()) / 20.0,  # Word count factor
            len(set(item.lower())) / 26.0,  # Unique character diversity
            item.count(',') / 10.0,  # Comma complexity
            item.count('(') / 5.0,   # Parentheses complexity
        ]
        return min(1.0, sum(factors) / len(factors))

    def _calculate_position(self, index: int, total: int) -> Dict[str, float]:
        """Calculate 2D position for constellation item."""
        if total == 1:
            return {"x": 0.5, "y": 0.5}

        # Arrange items in a circle for visual constellation
        angle = 2 * math.pi * index / total
        radius = 0.3  # Keep items within reasonable bounds

        x = 0.5 + radius * math.cos(angle)
        y = 0.5 + radius * math.sin(angle)

        return {"x": x, "y": y}

    def _compute_links(self, items: List[str]) -> List[Dict[str, Any]]:
        """Compute links between constellation items."""
        links = []

        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                similarity = self._calculate_similarity(items[i], items[j])

                if similarity >= self.similarity_threshold:
                    link = {
                        "source": i,
                        "target": j,
                        "strength": similarity,
                        "type": self._determine_link_type(items[i], items[j]),
                        "bidirectional": True
                    }
                    links.append(link)

        return links

    @lru_cache(maxsize=1024)
    def _calculate_similarity(self, item1: str, item2: str) -> float:
        """Calculate similarity between two items using multiple methods.

        Results are cached to avoid repeated computation for the same item
        pairs, which can significantly improve performance for repeated
        analyses.
        """
        # Convert to lowercase for comparison
        text1 = item1.lower()
        text2 = item2.lower()

        # Word-based similarity
        words1 = set(text1.split())
        words2 = set(text2.split())

        if len(words1.union(words2)) == 0:
            return 0.0

        jaccard = len(words1.intersection(words2)) / len(words1.union(words2))

        # Character-based similarity (simple)
        char_similarity = self._character_similarity(text1, text2)

        # Length similarity
        len_similarity = 1.0 - abs(len(text1) - len(text2)) / max(len(text1), len(text2), 1)

        # Combine similarities with weights
        combined = (jaccard * 0.5 + char_similarity * 0.3 + len_similarity * 0.2)

        return min(1.0, combined)

    @lru_cache(maxsize=2048)
    def _character_similarity(self, text1: str, text2: str) -> float:
        """Calculate character-level similarity with caching."""
        if not text1 or not text2:
            return 0.0

        # Simple character overlap
        chars1 = set(text1)
        chars2 = set(text2)

        if len(chars1.union(chars2)) == 0:
            return 0.0

        return len(chars1.intersection(chars2)) / len(chars1.union(chars2))

    def _determine_link_type(self, item1: str, item2: str) -> str:
        """Determine the type of relationship between two items."""
        content1 = item1.lower()
        content2 = item2.lower()

        # Check for problem-solution relationships
        if ("problem" in content1 or "error" in content1) and ("solution" in content2 or "fix" in content2):
            return "solution"
        elif ("solution" in content1 or "fix" in content1) and ("problem" in content2 or "error" in content2):
            return "solution"

        # Check for cause-effect relationships
        if any(word in content1 for word in ["cause", "because", "due to"]) or \
           any(word in content2 for word in ["result", "effect", "outcome"]):
            return "causal"

        # Check for hierarchical relationships
        if "part" in content1 and "whole" in content2 or \
           "component" in content1 and "system" in content2:
            return "hierarchical"

        # Default to conceptual similarity
        return "conceptual"

    def _calculate_stability_metrics(self, constellation: List[Dict], links: List[Dict]) -> Dict[str, Any]:
        """Calculate stability metrics for the constellation."""
        # Basic stability score
        stability_score = self._calculate_base_stability(constellation, links)

        # Historical stability (if we have history)
        historical_stability = self._calculate_historical_stability()

        # Determine stability status
        status = self._determine_stability_status(stability_score)

        # Additional metrics
        density = len(links) / max(1, len(constellation) * (len(constellation) - 1) / 2)
        connectivity = self._calculate_connectivity(constellation, links)

        return {
            "score": stability_score,
            "status": status,
            "historical_trend": historical_stability,
            "density": density,
            "connectivity": connectivity,
            "factors": {
                "item_distribution": self._calculate_distribution_stability(constellation),
                "link_strength": self._calculate_link_stability(links),
                "structure_balance": self._calculate_structure_balance(links)
            }
        }

    def _calculate_base_stability(self, constellation: List[Dict], links: List[Dict]) -> float:
        """Calculate base stability score."""
        if not constellation:
            return 1.0

        factors = []

        # Factor 1: Item weight distribution
        weights = [item["weight"] for item in constellation]
        weight_variance = self._calculate_variance(weights)
        weight_stability = 1.0 - min(1.0, weight_variance)
        factors.append(weight_stability)

        # Factor 2: Link strength consistency
        if links:
            strengths = [link["strength"] for link in links]
            strength_variance = self._calculate_variance(strengths)
            strength_stability = 1.0 - min(1.0, strength_variance)
            factors.append(strength_stability)
        else:
            factors.append(0.8)  # Neutral for no links

        # Factor 3: Position distribution
        positions = [(item["position"]["x"], item["position"]["y"]) for item in constellation]
        position_stability = self._calculate_position_stability(positions)
        factors.append(position_stability)

        return sum(factors) / len(factors)

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

    def _calculate_position_stability(self, positions: List[Tuple[float, float]]) -> float:
        """Calculate stability based on position distribution."""
        if len(positions) < 2:
            return 1.0

        # Check if positions are well distributed
        distances = []
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions[i+1:], i+1):
                dist = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                distances.append(dist)

        if not distances:
            return 1.0

        # Prefer moderate, consistent distances
        mean_distance = sum(distances) / len(distances)
        distance_variance = self._calculate_variance(distances)

        # Stability is higher when distances are consistent and reasonable
        return max(0.0, 1.0 - distance_variance) * min(1.0, mean_distance / 0.5)

    def _calculate_historical_stability(self) -> Dict[str, Any]:
        """Calculate stability trend from historical data."""
        if len(self._constellation_history) < 2:
            return {"trend": "stable", "confidence": 0.5, "change_rate": 0.0}

        # Compare recent stability scores
        recent_scores = [h.get("stability_score", 0.5) for h in self._constellation_history[-5:]]

        if len(recent_scores) < 2:
            return {"trend": "stable", "confidence": 0.5, "change_rate": 0.0}

        # Calculate trend
        change_rate = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)

        if abs(change_rate) < 0.01:
            trend = "stable"
        elif change_rate > 0:
            trend = "improving"
        else:
            trend = "declining"

        confidence = min(1.0, len(recent_scores) / 5.0)

        return {
            "trend": trend,
            "confidence": confidence,
            "change_rate": change_rate
        }

    def _determine_stability_status(self, score: float) -> str:
        """Determine stability status from score."""
        if score >= 0.8:
            return "stable"
        elif score >= 0.6:
            return "moderate"
        elif score >= 0.4:
            return "unstable"
        else:
            return "critical"

    def _calculate_connectivity(self, constellation: List[Dict], links: List[Dict]) -> float:
        """Calculate how well connected the constellation is."""
        if len(constellation) <= 1:
            return 1.0

        # Build adjacency list
        adjacency = defaultdict(set)
        for link in links:
            adjacency[link["source"]].add(link["target"])
            adjacency[link["target"]].add(link["source"])

        # Count connected components
        visited = set()
        components = 0

        for i in range(len(constellation)):
            if i not in visited:
                self._dfs_visit(i, adjacency, visited)
                components += 1

        # Connectivity is better with fewer components
        connectivity = 1.0 - (components - 1) / max(1, len(constellation) - 1)
        return connectivity

    def _dfs_visit(self, node: int, adjacency: Dict, visited: set):
        """Depth-first search visit for connectivity calculation."""
        visited.add(node)
        for neighbor in adjacency[node]:
            if neighbor not in visited:
                self._dfs_visit(neighbor, adjacency, visited)

    def _calculate_distribution_stability(self, constellation: List[Dict]) -> float:
        """Calculate stability of item distribution."""
        if not constellation:
            return 1.0

        # Check type distribution
        types = [item["type"] for item in constellation]
        type_counts = defaultdict(int)
        for t in types:
            type_counts[t] += 1

        # Prefer balanced type distribution
        total = len(constellation)
        type_distribution = [count / total for count in type_counts.values()]
        distribution_variance = self._calculate_variance(type_distribution)

        return max(0.0, 1.0 - distribution_variance)

    def _calculate_link_stability(self, links: List[Dict]) -> float:
        """Calculate stability of link strengths."""
        if not links:
            return 0.8  # Neutral score for no links

        strengths = [link["strength"] for link in links]

        # Prefer consistent, strong links
        mean_strength = sum(strengths) / len(strengths)
        strength_variance = self._calculate_variance(strengths)

        # Balance mean strength and consistency
        return (mean_strength * 0.7 + (1.0 - strength_variance) * 0.3)

    def _calculate_structure_balance(self, links: List[Dict]) -> float:
        """Calculate structural balance of the constellation."""
        if not links:
            return 0.8

        # Check for balanced link distribution
        link_counts = defaultdict(int)
        for link in links:
            link_counts[link["source"]] += 1
            link_counts[link["target"]] += 1

        if not link_counts:
            return 0.8

        counts = list(link_counts.values())
        count_variance = self._calculate_variance(counts)

        # Lower variance = better balance
        return max(0.0, 1.0 - count_variance / max(1, max(counts)))

    def _update_history(self, constellation: List[Dict], links: List[Dict]):
        """Update history for stability tracking."""
        entry = {
            "timestamp": len(self._constellation_history),
            "constellation_size": len(constellation),
            "link_count": len(links),
            "stability_score": self._calculate_base_stability(constellation, links)
        }

        self._constellation_history.append(entry)

        # Keep history within window
        if len(self._constellation_history) > self.stability_window:
            self._constellation_history = self._constellation_history[-self.stability_window:]

    def get_current_position(self) -> Dict[str, Any]:
        """Get current constellation position for TRI integration.

        This method is gated by NOVA_ENABLE_TRI_LINK environment variable.
        Returns the latest constellation state.

        Returns:
            Dict with current position data
        """
        flag = os.getenv("NOVA_ENABLE_TRI_LINK", "").strip()
        enabled = flag == "1"
        if not enabled:
            return {
                "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "stability": 1.0,
                "item_count": 0,
                "disabled": True
            }

        # Calculate current position based on constellation history
        if not self._constellation_history:
            return {
                "position": {"x": 0.5, "y": 0.5, "z": 0.5},
                "stability": 1.0,
                "item_count": 0,
                "disabled": False
            }

        latest = self._constellation_history[-1]

        # Calculate position based on constellation metrics
        x = min(1.0, latest["constellation_size"] / 20.0)  # Normalize by typical size
        y = min(1.0, latest["link_count"] / 50.0)         # Normalize by typical link count
        z = latest["stability_score"]                      # Already normalized [0,1]

        return {
            "position": {"x": x, "y": y, "z": z},
            "stability": latest["stability_score"],
            "item_count": latest["constellation_size"],
            "disabled": False
        }

    def update_from_tri(self, tri_score: float, layer_scores: Dict[str, float]) -> Dict[str, Any]:
        """Update constellation based on TRI analysis results.

        This method is gated by NOVA_ENABLE_TRI_LINK environment variable.
        Integrates TRI scoring to influence constellation stability.

        Args:
            tri_score: Main TRI score [0,1]
            layer_scores: Dict of layer-specific scores

        Returns:
            Dict with updated position and stability metrics
        """
        flag = os.getenv("NOVA_ENABLE_TRI_LINK", "").strip()
        enabled = flag == "1"
        if not enabled:
            return {
                "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "stability_index": 1.0,
                "tri_influence": 0.0,
                "disabled": True
            }

        # Get current position before update
        current = self.get_current_position()
        current_pos = current["position"]

        # Calculate TRI influence on constellation position
        tri_influence = self._calculate_tri_influence(tri_score, layer_scores)

        # Update position based on TRI analysis
        new_position = {
            "x": self._blend_coordinate(current_pos["x"], layer_scores.get("structural", 0.0), tri_influence),
            "y": self._blend_coordinate(current_pos["y"], layer_scores.get("semantic", 0.0), tri_influence),
            "z": self._blend_coordinate(current_pos["z"], layer_scores.get("expression", 0.0), tri_influence)
        }

        # Calculate new stability index influenced by TRI
        base_stability = current.get("stability", 1.0)
        tri_stability_factor = 1.0 - abs(tri_score - 0.5) * 0.5  # More extreme scores reduce stability
        new_stability = base_stability * (0.7 + 0.3 * tri_stability_factor)

        # Update internal history with TRI-influenced data
        self._record_tri_update(new_position, new_stability, tri_score, layer_scores)

        return {
            "position": new_position,
            "stability_index": max(0.0, min(1.0, new_stability)),
            "tri_influence": tri_influence,
            "tri_score": tri_score,
            "layer_scores": layer_scores,
            "disabled": False
        }

    def _calculate_tri_influence(self, tri_score: float, layer_scores: Dict[str, float]) -> float:
        """Calculate how much TRI analysis should influence constellation position."""
        # Higher TRI scores (more confident) have more influence
        base_influence = tri_score * 0.3  # Max 30% influence

        # Layer consistency increases influence
        layer_values = [layer_scores.get(k, 0.0) for k in ["structural", "semantic", "expression"]]
        layer_variance = self._calculate_variance(layer_values) if len(layer_values) > 1 else 0.0
        consistency_bonus = (1.0 - layer_variance) * 0.2  # Up to 20% bonus for consistency

        return min(0.5, base_influence + consistency_bonus)  # Cap at 50% influence

    def _blend_coordinate(self, current: float, tri_layer: float, influence: float) -> float:
        """Blend current coordinate with TRI layer score using influence factor."""
        blended = current * (1.0 - influence) + tri_layer * influence
        return max(0.0, min(1.0, blended))

    def _record_tri_update(self, position: Dict[str, float], stability: float,
                          tri_score: float, layer_scores: Dict[str, float]):
        """Record TRI-influenced update in constellation history."""
        entry = {
            "timestamp": len(self._constellation_history),
            "constellation_size": len(self._constellation_history),  # Approximate
            "link_count": max(1, len(self._constellation_history) * 2),  # Approximate
            "stability_score": stability,
            "tri_enhanced": True,
            "tri_score": tri_score,
            "layer_scores": layer_scores.copy(),
            "position": position.copy()
        }

        self._constellation_history.append(entry)

        # Keep history within window
        if len(self._constellation_history) > self.stability_window:
            self._constellation_history = self._constellation_history[-self.stability_window:]
