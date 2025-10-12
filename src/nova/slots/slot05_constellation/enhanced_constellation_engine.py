"""Enhanced Constellation Engine with Adaptive Processing for Processual Level.

This enhanced engine wraps the base ConstellationEngine with adaptive capabilities,
providing the dynamic processing required for 4.0 Processual maturity level.
"""

import time
import logging
from typing import Dict, List, Any, Optional

from .constellation_engine import ConstellationEngine
from .adaptive_processor import AdaptiveProcessor

logger = logging.getLogger(__name__)


class EnhancedConstellationEngine:
    """Enhanced constellation engine with adaptive processing capabilities.

    Advances Slot 5 from Structural+ (3.5) to Processual (4.0) by adding:
    - Dynamic threshold adjustment
    - Context-aware processing
    - Cross-slot coordination
    - Performance-based adaptation
    """

    __version__ = "2.0.0"

    def __init__(self, semantic_mirror=None):
        """Initialize enhanced engine with adaptive capabilities."""
        self.base_engine = ConstellationEngine()
        self.adaptive_processor = AdaptiveProcessor(semantic_mirror)
        self.semantic_mirror = semantic_mirror

        # Performance tracking
        self._operation_count = 0
        self._total_processing_time = 0.0
        self._context_cache = {}

        logger.info(f"EnhancedConstellationEngine v{self.__version__} initialized with adaptive processing")

    def map(self, items: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enhanced mapping with adaptive processing.

        Args:
            items: List of items to map into constellation
            context: Optional context for adaptive processing

        Returns:
            Enhanced constellation mapping with adaptive metrics
        """
        start_time = time.time()

        # Prepare context for adaptation
        if context is None:
            context = self._infer_context(items)

        # Get current adaptive thresholds
        adaptive_thresholds = self.adaptive_processor.get_current_thresholds()

        # Apply adaptive thresholds to base engine
        self._apply_adaptive_thresholds(adaptive_thresholds)

        # Perform base constellation mapping
        result = self.base_engine.map(items)

        # Calculate performance metrics
        processing_time = time.time() - start_time
        performance_metrics = self._calculate_performance_metrics(result, processing_time)

        # Adaptive threshold adjustment based on performance
        updated_thresholds = self.adaptive_processor.adapt_thresholds(
            context, performance_metrics
        )

        # Enhance result with adaptive information
        result['adaptive'] = {
            'thresholds_used': adaptive_thresholds,
            'thresholds_updated': updated_thresholds,
            'context': context,
            'performance': performance_metrics,
            'processing_time': processing_time,
            'version': self.__version__
        }

        # Update tracking
        self._operation_count += 1
        self._total_processing_time += processing_time

        # Log adaptive behavior
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Adaptive constellation mapping: {len(items)} items, "
                        f"{processing_time:.3f}s, stability={performance_metrics.get('stability_score', 0):.3f}")

        # Publish constellation event for cross-slot coordination
        self._publish_constellation_event(result, context)

        return result

    def _infer_context(self, items: List[str]) -> Dict[str, Any]:
        """Infer processing context from input items."""
        context = {
            'item_count': len(items),
            'avg_length': sum(len(item) for item in items) / max(1, len(items)),
            'timestamp': time.time()
        }

        # Analyze content characteristics
        if items:
            complexities = []
            for item in items:
                # Simple complexity estimation
                complexity = min(1.0, (
                    len(item.split()) / 20.0 +
                    len(set(item.lower())) / 26.0 +
                    item.count(',') / 10.0
                ) / 3.0)
                complexities.append(complexity)

            context['avg_complexity'] = sum(complexities) / len(complexities)
            context['complexity_variance'] = self._calculate_variance(complexities)
        else:
            context['avg_complexity'] = 0.0
            context['complexity_variance'] = 0.0

        # Determine stability requirement based on content
        if any(word in ' '.join(items).lower() for word in ['critical', 'important', 'urgent']):
            context['stability_requirement'] = 'high'
        elif any(word in ' '.join(items).lower() for word in ['test', 'temp', 'draft']):
            context['stability_requirement'] = 'low'
        else:
            context['stability_requirement'] = 'standard'

        # Time constraint inference
        if len(items) > 50:
            context['time_constraint'] = 'tight'
        elif len(items) < 5:
            context['time_constraint'] = 'relaxed'
        else:
            context['time_constraint'] = 'normal'

        return context

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values."""
        if len(values) < 2:
            return 0.0
        mean_val = sum(values) / len(values)
        return sum((x - mean_val) ** 2 for x in values) / len(values)

    def _apply_adaptive_thresholds(self, thresholds: Dict[str, float]):
        """Apply adaptive thresholds to base engine."""
        self.base_engine.similarity_threshold = thresholds['similarity']
        self.base_engine.stability_window = int(thresholds['stability_window'])
        self.base_engine.link_strength_threshold = thresholds['link_strength']

    def _calculate_performance_metrics(self, result: Dict[str, Any], processing_time: float) -> Dict[str, float]:
        """Calculate performance metrics from constellation mapping result."""
        metrics = {
            'processing_time': processing_time,
            'stability_score': result.get('stability', {}).get('score', 0.0),
            'connectivity': result.get('stability', {}).get('connectivity', 0.0),
            'density': result.get('stability', {}).get('density', 0.0),
            'item_count': result.get('metadata', {}).get('item_count', 0),
            'link_count': result.get('metadata', {}).get('link_count', 0)
        }

        # Calculate efficiency metrics
        if result.get('metadata', {}).get('item_count', 0) > 0:
            metrics['processing_efficiency'] = result['metadata']['item_count'] / max(0.001, processing_time)
        else:
            metrics['processing_efficiency'] = 0.0

        # Calculate quality score
        stability = metrics['stability_score']
        connectivity = metrics['connectivity']
        density = metrics['density']
        quality_score = (stability * 0.5 + connectivity * 0.3 + density * 0.2)
        metrics['quality_score'] = quality_score

        return metrics

    def _publish_constellation_event(self, result: Dict[str, Any], context: Dict[str, Any]):
        """Publish constellation mapping event to semantic mirror."""
        if not self.semantic_mirror:
            return

        try:
            event_data = {
                'slot': 'slot05_constellation',
                'event_type': 'constellation_mapped',
                'item_count': result.get('metadata', {}).get('item_count', 0),
                'link_count': result.get('metadata', {}).get('link_count', 0),
                'stability_score': result.get('stability', {}).get('score', 0.0),
                'processing_time': result.get('adaptive', {}).get('processing_time', 0.0),
                'context_signature': self._generate_context_signature(context),
                'timestamp': time.time(),
                'version': self.__version__
            }

            published = self.semantic_mirror.publish(
                'slot05.constellation_mapped',
                event_data,
                'slot05_constellation_navigation',
                ttl=600.0  # 10 minute TTL
            )

            if published:
                logger.debug("Constellation mapping event published to semantic mirror")

        except Exception as e:
            logger.error(f"Error publishing constellation event: {e}")

    def _generate_context_signature(self, context: Dict[str, Any]) -> str:
        """Generate a signature for the context."""
        factors = []

        item_count = context.get('item_count', 0)
        if item_count < 5:
            factors.append('sparse')
        elif item_count > 20:
            factors.append('dense')
        else:
            factors.append('moderate')

        complexity = context.get('avg_complexity', 0.5)
        if complexity > 0.7:
            factors.append('complex')
        elif complexity < 0.3:
            factors.append('simple')
        else:
            factors.append('balanced')

        factors.append(f"stability_{context.get('stability_requirement', 'standard')}")
        factors.append(f"time_{context.get('time_constraint', 'normal')}")

        return '_'.join(sorted(factors))

    def get_adaptive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive adaptive metrics."""
        base_metrics = {
            'total_operations': self._operation_count,
            'total_processing_time': self._total_processing_time,
            'avg_processing_time': (self._total_processing_time / max(1, self._operation_count)),
            'engine_version': self.__version__
        }

        adaptive_metrics = self.adaptive_processor.get_adaptation_metrics()

        return {**base_metrics, **adaptive_metrics}

    def reset_adaptive_state(self):
        """Reset adaptive processing state."""
        self.adaptive_processor.reset_adaptations()
        self._operation_count = 0
        self._total_processing_time = 0.0
        self._context_cache.clear()
        logger.info("Enhanced constellation engine adaptive state reset")

    def enable_cross_slot_coordination(self, semantic_mirror):
        """Enable cross-slot coordination via semantic mirror."""
        self.semantic_mirror = semantic_mirror
        self.adaptive_processor.semantic_mirror = semantic_mirror
        logger.info("Cross-slot coordination enabled via semantic mirror")

    def __getattr__(self, name):
        """Delegate unknown attributes to base engine for compatibility."""
        return getattr(self.base_engine, name)