"""Adaptive Processing Layer for Slot 5 - Constellation Navigation.

This module provides the adaptive capabilities required to advance
Slot 5 from Structural+ (3.5) to Processual (4.0) level.

Key Features:
- Dynamic threshold adjustment based on context
- Feedback learning from stability patterns
- Cross-slot coordination via semantic mirror
- Predictive stability optimization
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import deque, defaultdict
from statistics import mean, stdev

logger = logging.getLogger(__name__)


class AdaptiveProcessor:
    """Adaptive processing engine for dynamic constellation optimization."""

    __version__ = "1.0.0"

    def __init__(self, semantic_mirror=None):
        """Initialize adaptive processor with optional semantic mirror integration."""
        self.semantic_mirror = semantic_mirror

        # Adaptive threshold parameters
        self.base_similarity_threshold = 0.3
        self.base_stability_window = 10
        self.base_link_strength_threshold = 0.2

        # Learning parameters
        self.learning_rate = 0.1
        self.adaptation_sensitivity = 0.05
        self.context_window = 50

        # Performance tracking
        self._performance_history = deque(maxlen=self.context_window)
        self._context_patterns = defaultdict(list)
        self._adaptation_log = []

        # Current adaptive state
        self._current_thresholds = {
            'similarity': self.base_similarity_threshold,
            'stability_window': self.base_stability_window,
            'link_strength': self.base_link_strength_threshold
        }

        logger.info(f"AdaptiveProcessor v{self.__version__} initialized")

    def adapt_thresholds(self, context: Dict[str, Any],
                        performance_metrics: Dict[str, float]) -> Dict[str, float]:
        """Dynamically adapt thresholds based on context and performance.

        Args:
            context: Current operational context
            performance_metrics: Recent performance measurements

        Returns:
            Updated threshold values
        """
        # Analyze context characteristics
        context_signature = self._analyze_context(context)

        # Record performance for learning
        self._record_performance(context_signature, performance_metrics)

        # Calculate threshold adjustments
        adjustments = self._calculate_threshold_adjustments(
            context_signature, performance_metrics
        )

        # Apply adaptations with bounds checking
        self._apply_adaptations(adjustments)

        # Log adaptation decision
        self._log_adaptation(context_signature, adjustments, performance_metrics)

        # Publish adaptation event if semantic mirror available
        self._publish_adaptation_event(context_signature, adjustments)

        return self._current_thresholds.copy()

    def _analyze_context(self, context: Dict[str, Any]) -> str:
        """Analyze context to determine adaptation strategy."""
        factors = []

        # Data volume factor
        item_count = context.get('item_count', 0)
        if item_count < 5:
            factors.append('sparse')
        elif item_count > 20:
            factors.append('dense')
        else:
            factors.append('moderate')

        # Content complexity factor
        avg_complexity = context.get('avg_complexity', 0.5)
        if avg_complexity > 0.7:
            factors.append('complex')
        elif avg_complexity < 0.3:
            factors.append('simple')
        else:
            factors.append('balanced')

        # Stability requirements
        stability_requirement = context.get('stability_requirement', 'standard')
        factors.append(f'stability_{stability_requirement}')

        # Performance pressure
        time_constraint = context.get('time_constraint', 'normal')
        factors.append(f'time_{time_constraint}')

        return '_'.join(sorted(factors))

    def _record_performance(self, context_signature: str,
                           performance_metrics: Dict[str, float]):
        """Record performance metrics for learning."""
        performance_entry = {
            'timestamp': time.time(),
            'context': context_signature,
            'metrics': performance_metrics.copy(),
            'thresholds': self._current_thresholds.copy()
        }

        self._performance_history.append(performance_entry)
        self._context_patterns[context_signature].append(performance_entry)

    def _calculate_threshold_adjustments(self, context_signature: str,
                                       performance_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate threshold adjustments based on context and performance."""
        adjustments = {
            'similarity': 0.0,
            'stability_window': 0.0,
            'link_strength': 0.0
        }

        # Historical performance for this context
        historical_performance = self._context_patterns.get(context_signature, [])

        if len(historical_performance) >= 3:
            # Learn from historical patterns
            adjustments.update(self._learn_from_history(historical_performance, performance_metrics))
        else:
            # Use heuristic adaptations for new contexts
            adjustments.update(self._heuristic_adaptations(context_signature, performance_metrics))

        return adjustments

    def _learn_from_history(self, historical_performance: List[Dict],
                           current_metrics: Dict[str, float]) -> Dict[str, float]:
        """Learn optimal thresholds from historical performance."""
        adjustments = {}

        # Analyze correlation between thresholds and performance
        for threshold_name in ['similarity', 'link_strength']:
            threshold_values = [entry['thresholds'][threshold_name] for entry in historical_performance]
            performance_values = [entry['metrics'].get('stability_score', 0.5) for entry in historical_performance]

            if len(set(threshold_values)) > 1:  # Only if we have variation
                correlation = self._calculate_correlation(threshold_values, performance_values)

                # Adjust based on correlation and current performance
                current_performance = current_metrics.get('stability_score', 0.5)
                target_performance = 0.8  # Target stability

                if current_performance < target_performance:
                    if correlation > 0:
                        # Positive correlation - increase threshold
                        adjustments[threshold_name] = self.learning_rate * (target_performance - current_performance)
                    else:
                        # Negative correlation - decrease threshold
                        adjustments[threshold_name] = -self.learning_rate * (target_performance - current_performance)
                else:
                    # Performance is good, minor adjustments
                    adjustments[threshold_name] = 0.0
            else:
                adjustments[threshold_name] = 0.0

        # Stability window adjustment
        avg_stability = mean([entry['metrics'].get('stability_score', 0.5) for entry in historical_performance])
        if avg_stability < 0.6:
            adjustments['stability_window'] = 2  # Increase window for better stability
        elif avg_stability > 0.9:
            adjustments['stability_window'] = -1  # Decrease window for efficiency
        else:
            adjustments['stability_window'] = 0

        return adjustments

    def _heuristic_adaptations(self, context_signature: str,
                              performance_metrics: Dict[str, float]) -> Dict[str, float]:
        """Apply heuristic adaptations for new contexts."""
        adjustments = {}

        # Context-based heuristics
        if 'sparse' in context_signature:
            # Lower similarity threshold for sparse data
            adjustments['similarity'] = -0.05
            adjustments['link_strength'] = -0.03
        elif 'dense' in context_signature:
            # Higher similarity threshold for dense data
            adjustments['similarity'] = 0.05
            adjustments['link_strength'] = 0.03
        else:
            adjustments['similarity'] = 0.0
            adjustments['link_strength'] = 0.0

        if 'complex' in context_signature:
            # Longer stability window for complex content
            adjustments['stability_window'] = 3
        elif 'simple' in context_signature:
            # Shorter stability window for simple content
            adjustments['stability_window'] = -2
        else:
            adjustments['stability_window'] = 0

        # Performance-based adjustments
        current_stability = performance_metrics.get('stability_score', 0.5)
        if current_stability < 0.5:
            # Poor stability - be more conservative
            adjustments['similarity'] += -0.02
            adjustments['stability_window'] += 2
        elif current_stability > 0.8:
            # Good stability - can be more aggressive
            adjustments['similarity'] += 0.02
            adjustments['stability_window'] += -1

        return adjustments

    def _calculate_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate correlation coefficient between two value lists."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0

        try:
            x_mean = mean(x_values)
            y_mean = mean(y_values)

            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))

            x_variance = sum((x - x_mean) ** 2 for x in x_values)
            y_variance = sum((y - y_mean) ** 2 for y in y_values)

            denominator = (x_variance * y_variance) ** 0.5

            if denominator == 0:
                return 0.0

            return numerator / denominator

        except Exception as e:
            logger.warning(f"Correlation calculation failed: {e}")
            return 0.0

    def _apply_adaptations(self, adjustments: Dict[str, float]):
        """Apply threshold adjustments with bounds checking."""
        # Similarity threshold bounds: [0.1, 0.8]
        new_similarity = self._current_thresholds['similarity'] + adjustments['similarity']
        self._current_thresholds['similarity'] = max(0.1, min(0.8, new_similarity))

        # Link strength threshold bounds: [0.05, 0.6]
        new_link_strength = self._current_thresholds['link_strength'] + adjustments['link_strength']
        self._current_thresholds['link_strength'] = max(0.05, min(0.6, new_link_strength))

        # Stability window bounds: [3, 50]
        new_stability_window = self._current_thresholds['stability_window'] + adjustments['stability_window']
        self._current_thresholds['stability_window'] = max(3, min(50, int(new_stability_window)))

    def _log_adaptation(self, context_signature: str, adjustments: Dict[str, float],
                       performance_metrics: Dict[str, float]):
        """Log adaptation decision for analysis."""
        log_entry = {
            'timestamp': time.time(),
            'context': context_signature,
            'adjustments': adjustments.copy(),
            'new_thresholds': self._current_thresholds.copy(),
            'performance': performance_metrics.copy()
        }

        self._adaptation_log.append(log_entry)

        logger.info(f"Adaptive thresholds updated for context {context_signature}: "
                   f"similarity={self._current_thresholds['similarity']:.3f}, "
                   f"link_strength={self._current_thresholds['link_strength']:.3f}, "
                   f"stability_window={self._current_thresholds['stability_window']}")

    def _publish_adaptation_event(self, context_signature: str, adjustments: Dict[str, float]):
        """Publish adaptation event to semantic mirror for cross-slot coordination."""
        if not self.semantic_mirror:
            return

        try:
            event_data = {
                'slot': 'slot05_constellation',
                'event_type': 'threshold_adaptation',
                'context_signature': context_signature,
                'threshold_changes': adjustments,
                'new_thresholds': self._current_thresholds.copy(),
                'timestamp': time.time(),
                'version': self.__version__
            }

            # Publish to semantic mirror for other slots to observe
            published = self.semantic_mirror.publish(
                'slot05.adaptation_event',
                event_data,
                'slot05_constellation_navigation',
                ttl=300.0  # 5 minute TTL
            )

            if published:
                logger.debug("Adaptation event published to semantic mirror")
            else:
                logger.warning("Failed to publish adaptation event")

        except Exception as e:
            logger.error(f"Error publishing adaptation event: {e}")

    def get_current_thresholds(self) -> Dict[str, float]:
        """Get current adaptive threshold values."""
        return self._current_thresholds.copy()

    def get_adaptation_metrics(self) -> Dict[str, Any]:
        """Get metrics about adaptation behavior."""
        if not self._adaptation_log:
            return {'total_adaptations': 0, 'contexts_learned': 0}

        return {
            'total_adaptations': len(self._adaptation_log),
            'contexts_learned': len(self._context_patterns),
            'recent_adaptations': len([log for log in self._adaptation_log
                                     if time.time() - log['timestamp'] < 3600]),  # Last hour
            'performance_history_size': len(self._performance_history),
            'current_thresholds': self._current_thresholds.copy(),
            'base_thresholds': {
                'similarity': self.base_similarity_threshold,
                'stability_window': self.base_stability_window,
                'link_strength': self.base_link_strength_threshold
            }
        }

    def reset_adaptations(self):
        """Reset to base thresholds and clear learning history."""
        self._current_thresholds = {
            'similarity': self.base_similarity_threshold,
            'stability_window': self.base_stability_window,
            'link_strength': self.base_link_strength_threshold
        }

        self._performance_history.clear()
        self._context_patterns.clear()
        self._adaptation_log.clear()

        logger.info("Adaptive processor reset to base configuration")