import logging
from typing import Any, Dict, Optional

try:
    from slots.slot03_emotional_matrix.emotional_matrix_engine import EmotionalMatrixEngine
    from slots.slot03_emotional_matrix.escalation import EmotionalEscalationManager, ThreatLevel
    from slots.slot03_emotional_matrix.advanced_policy import AdvancedSafetyPolicy
    ENGINE = EmotionalMatrixEngine()
    ESCALATION_MANAGER = None  # Will be initialized with registry
    SAFETY_POLICY = AdvancedSafetyPolicy()
    AVAILABLE = True
except Exception as exc:  # pragma: no cover - optional slot
    logging.getLogger(__name__).exception(
        "Failed to import Slot 3 emotional matrix engine: %s", exc
    )
    ENGINE = None
    ESCALATION_MANAGER = None
    SAFETY_POLICY = None
    AVAILABLE = False


class Slot3EmotionalAdapter:
    """
    Enhanced adapter for Slot-3 Emotional Matrix engine with escalation,
    advanced safety policies, and inter-slot communication.
    """

    def __init__(self, adapter_registry: Optional[Dict] = None) -> None:
        self.available = AVAILABLE
        self.logger = logging.getLogger(__name__)
        self.adapter_registry = adapter_registry or {}
        
        # Initialize escalation manager with registry
        if AVAILABLE and ESCALATION_MANAGER is None:
            global ESCALATION_MANAGER
            ESCALATION_MANAGER = EmotionalEscalationManager(adapter_registry)
        
        self.escalation_manager = ESCALATION_MANAGER
        self.safety_policy = SAFETY_POLICY

    def analyze(self, content: str, user_id: Optional[str] = None, 
                enable_escalation: bool = True) -> Dict[str, Any]:
        """
        Enhanced emotional analysis with safety validation and escalation.
        
        Args:
            content: Text content to analyze
            user_id: User identifier for rate limiting and tracking
            enable_escalation: Whether to trigger escalation for threats
            
        Returns:
            Analysis result with safety validation and escalation info
        """
        if not self.available or not ENGINE:
            return {}
            
        try:
            # Perform emotional analysis
            analysis = ENGINE.analyze(content)
            
            # Apply advanced safety policy validation
            if self.safety_policy:
                safety_result = self.safety_policy.validate(analysis, content, user_id)
                analysis['safety'] = safety_result
                
                # Don't proceed with escalation if rate limited or unsafe
                if safety_result['rate_limited'] or not safety_result['is_safe']:
                    if safety_result['violations']:
                        self.logger.warning("Safety violations detected: %s", 
                                          [v['type'] for v in safety_result['violations']])
                    return analysis
            
            # Check for escalation if enabled
            if enable_escalation and self.escalation_manager:
                threat_level = self.escalation_manager.classify_threat(analysis)
                analysis['threat_level'] = threat_level.value
                
                # Trigger escalation for medium and above threats
                if threat_level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                    escalation_event = self.escalation_manager.escalate(content, analysis)
                    analysis['escalation'] = {
                        'triggered': True,
                        'event_id': id(escalation_event),
                        'threat_level': threat_level.value,
                        'suggested_actions': escalation_event.suggested_actions,
                        'escalation_reason': escalation_event.escalation_reason
                    }
                else:
                    analysis['escalation'] = {'triggered': False, 'threat_level': threat_level.value}
            
            return analysis
            
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.exception("Emotional analysis failed: %s", exc)
            return {}

    def receive_escalation(self, escalation_event) -> bool:
        """
        Receive escalation events from other slots.
        
        Args:
            escalation_event: Escalation event from another slot
            
        Returns:
            True if event was processed successfully
        """
        try:
            self.logger.info(
                "Received escalation from %s: %s (level: %s)", 
                escalation_event.source_slot,
                escalation_event.escalation_reason,
                escalation_event.threat_level.value
            )
            
            # Process the escalation - could trigger additional analysis
            # or safety measures based on the incoming event
            if escalation_event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                self.logger.warning("High-priority escalation received - implementing additional safety measures")
            
            return True
            
        except Exception as exc:
            self.logger.exception("Failed to process escalation event: %s", exc)
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status including escalation metrics."""
        base_status = {
            "available": self.available,
            "engine_status": "operational" if ENGINE else "unavailable",
            "escalation_enabled": self.escalation_manager is not None,
            "safety_policy_enabled": self.safety_policy is not None
        }
        
        if not self.available:
            return base_status
        
        # Add escalation metrics
        if self.escalation_manager:
            escalation_summary = self.escalation_manager.get_escalation_summary()
            base_status['escalation_metrics'] = escalation_summary
        
        # Add safety policy metrics
        if self.safety_policy:
            policy_stats = self.safety_policy.get_policy_stats()
            base_status['safety_metrics'] = policy_stats
        
        return base_status

    def update_adapter_registry(self, registry: Dict) -> None:
        """Update the adapter registry for inter-slot communication."""
        self.adapter_registry = registry
        if self.escalation_manager:
            self.escalation_manager.adapter_registry = registry