"""Enhanced Emotional Matrix Engine with Escalation Integration."""
from typing import Dict, Any, Optional, Callable
from .emotional_matrix_engine import EmotionalMatrixEngine


class EnhancedEmotionalMatrixEngine:
    """
    Enhanced wrapper around EmotionalMatrixEngine that provides
    escalation integration and monitoring capabilities.

    This maintains backward compatibility while adding new features.
    """

    def __init__(self, base_engine: Optional[EmotionalMatrixEngine] = None):
        self.base_engine = base_engine or EmotionalMatrixEngine()
        self._escalation_hook: Optional[Callable[[str, Dict[str, Any]], None]] = None
        self._analysis_count = 0
        self._threat_detections = 0

    def set_escalation_hook(self, hook_fn: Optional[Callable[[str, Dict[str, Any]], None]]) -> None:
        """Set optional escalation hook for threat detection integration."""
        self._escalation_hook = hook_fn

    def analyze(self, content: str, *, policy_hook: Optional[Callable[[Dict], None]] = None) -> Dict[str, Any]:
        """
        Enhanced analysis with escalation integration.

        Args:
            content: Text content to analyze
            policy_hook: Optional policy validation hook

        Returns:
            Analysis result with potential escalation information
        """
        self._analysis_count += 1

        # Perform base analysis
        result = self.base_engine.analyze(content, policy_hook=policy_hook)

        # Add enhanced metadata
        result['analysis_id'] = self._analysis_count
        result['enhanced'] = True

        # Check for escalation triggers
        if self._escalation_hook and self._should_escalate(result):
            self._threat_detections += 1
            try:
                self._escalation_hook(content, result)
                result['escalation_triggered'] = True
            except Exception as exc:
                result['escalation_error'] = str(exc)
        else:
            result['escalation_triggered'] = False

        return result

    def _should_escalate(self, analysis: Dict[str, Any]) -> bool:
        """
        Determine if analysis results should trigger escalation.

        This is a lightweight check - the escalation manager
        will do the heavy lifting for threat classification.
        """
        score = analysis.get('score', 0.0)
        confidence = analysis.get('confidence', 0.0)
        tone = analysis.get('emotional_tone', 'neutral')

        # Escalate high-confidence negative emotions
        if confidence > 0.6 and score < -0.3:
            return True

        # Escalate specific concerning tones regardless of score
        if tone in ['anger', 'fear', 'disgust'] and confidence > 0.5:
            return True

        return False

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance and usage metrics."""
        return {
            'total_analyses': self._analysis_count,
            'threat_detections': self._threat_detections,
            'threat_detection_rate': self._threat_detections / max(1, self._analysis_count),
            'escalation_enabled': self._escalation_hook is not None,
            'base_engine_version': getattr(self.base_engine, '__version__', 'unknown')
        }

    def analyze_batch(self, contents):
        """Batch analysis with escalation support."""
        return [self.analyze(content) for content in contents]

    def __getattr__(self, name):
        """Delegate unknown attributes to base engine for compatibility."""
        return getattr(self.base_engine, name)
