"""Escalation Manager for Slot 3 - Emotional Matrix Safety System."""
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum


class ThreatLevel(Enum):
    """Threat classification levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EscalationEvent:
    """Represents an escalation event."""
    threat_level: ThreatLevel
    content: str
    emotional_analysis: Dict[str, Any]
    timestamp: float
    source_slot: str = "slot03_emotional"
    escalation_reason: str = ""
    suggested_actions: List[str] = None

    def __post_init__(self):
        if self.suggested_actions is None:
            self.suggested_actions = []


class EmotionalEscalationManager:
    """
    Manages escalation of emotional threats across NOVA system.
    
    Provides threat classification, escalation routing, and
    cross-slot coordination for emotional safety incidents.
    """

    def __init__(self, adapter_registry: Optional[Dict] = None):
        self.logger = logging.getLogger(__name__)
        self.adapter_registry = adapter_registry or {}
        self._escalation_handlers: Dict[ThreatLevel, List[Callable]] = {
            ThreatLevel.LOW: [],
            ThreatLevel.MEDIUM: [],
            ThreatLevel.HIGH: [],
            ThreatLevel.CRITICAL: []
        }
        self._escalation_history: List[EscalationEvent] = []

    def register_handler(self, threat_level: ThreatLevel, handler: Callable):
        """Register a handler for specific threat level."""
        self._escalation_handlers[threat_level].append(handler)

    def classify_threat(self, emotional_analysis: Dict[str, Any]) -> ThreatLevel:
        """
        Classify threat level based on emotional analysis.
        
        Args:
            emotional_analysis: Analysis from emotional matrix engine
            
        Returns:
            ThreatLevel enum indicating severity
        """
        score = emotional_analysis.get('score', 0.0)
        tone = emotional_analysis.get('emotional_tone', 'neutral')
        confidence = emotional_analysis.get('confidence', 0.0)
        
        # Critical threats: High confidence negative emotions with extreme scores
        if confidence > 0.8 and score < -0.8 and tone in ['anger', 'hatred', 'violence']:
            return ThreatLevel.CRITICAL
            
        # High threats: Strong negative emotions with high confidence
        if confidence > 0.7 and score < -0.6 and tone in ['anger', 'fear', 'disgust']:
            return ThreatLevel.HIGH
            
        # Medium threats: Moderate negative emotions
        if confidence > 0.5 and score < -0.4:
            return ThreatLevel.MEDIUM
            
        # Low threats: Mild negative emotions or uncertainty
        if score < -0.2 or confidence < 0.3:
            return ThreatLevel.LOW
            
        return ThreatLevel.LOW

    def escalate(self, content: str, emotional_analysis: Dict[str, Any]) -> EscalationEvent:
        """
        Process escalation for emotional content.
        
        Args:
            content: Original content that triggered escalation
            emotional_analysis: Analysis results from emotional matrix
            
        Returns:
            EscalationEvent with classification and suggested actions
        """
        import time
        
        threat_level = self.classify_threat(emotional_analysis)
        
        # Create escalation event
        event = EscalationEvent(
            threat_level=threat_level,
            content=content[:200] + "..." if len(content) > 200 else content,
            emotional_analysis=emotional_analysis,
            timestamp=time.time(),
            escalation_reason=self._get_escalation_reason(threat_level, emotional_analysis),
            suggested_actions=self._get_suggested_actions(threat_level)
        )
        
        # Log escalation
        self.logger.warning(
            "Emotional escalation - Level: %s, Tone: %s, Score: %.2f",
            threat_level.value,
            emotional_analysis.get('emotional_tone', 'unknown'),
            emotional_analysis.get('score', 0.0)
        )
        
        # Store in history
        self._escalation_history.append(event)
        
        # Execute registered handlers
        for handler in self._escalation_handlers[threat_level]:
            try:
                handler(event)
            except Exception as exc:
                self.logger.exception("Escalation handler failed: %s", exc)
        
        # Route to other slots if available
        self._route_to_slots(event)
        
        return event

    def _get_escalation_reason(self, threat_level: ThreatLevel, analysis: Dict[str, Any]) -> str:
        """Generate human-readable escalation reason."""
        tone = analysis.get('emotional_tone', 'unknown')
        score = analysis.get('score', 0.0)
        confidence = analysis.get('confidence', 0.0)
        
        reasons = {
            ThreatLevel.CRITICAL: f"Critical emotional threat detected: {tone} with score {score:.2f} (confidence: {confidence:.2f})",
            ThreatLevel.HIGH: f"High emotional risk: {tone} content with negative score {score:.2f}",
            ThreatLevel.MEDIUM: f"Moderate emotional concern: {tone} detected with score {score:.2f}",
            ThreatLevel.LOW: f"Low-level emotional monitoring: {tone} or low confidence ({confidence:.2f})"
        }
        
        return reasons.get(threat_level, "Unknown escalation reason")

    def _get_suggested_actions(self, threat_level: ThreatLevel) -> List[str]:
        """Get suggested actions based on threat level."""
        actions = {
            ThreatLevel.CRITICAL: [
                "Immediate content quarantine",
                "Alert system administrators",
                "Engage Slot 1 (Truth Anchor) for verification",
                "Consider user session suspension"
            ],
            ThreatLevel.HIGH: [
                "Content review required",
                "Increase monitoring for user session",
                "Consult Slot 4 (Wisdom Integration) for guidance",
                "Apply enhanced safety filters"
            ],
            ThreatLevel.MEDIUM: [
                "Enhanced content filtering",
                "Monitor subsequent interactions",
                "Log for pattern analysis"
            ],
            ThreatLevel.LOW: [
                "Standard monitoring",
                "Continue with caution"
            ]
        }
        
        return actions.get(threat_level, [])

    def _route_to_slots(self, event: EscalationEvent):
        """Route escalation event to relevant slots."""
        if not self.adapter_registry:
            return
            
        routing_map = {
            ThreatLevel.CRITICAL: ['slot01_truth', 'slot04_wisdom', 'slot07_ethical'],
            ThreatLevel.HIGH: ['slot01_truth', 'slot04_wisdom'],
            ThreatLevel.MEDIUM: ['slot04_wisdom'],
            ThreatLevel.LOW: []
        }
        
        target_slots = routing_map.get(event.threat_level, [])
        
        for slot_name in target_slots:
            if slot_name in self.adapter_registry:
                try:
                    adapter = self.adapter_registry[slot_name]
                    # Send escalation notification to slot
                    if hasattr(adapter, 'receive_escalation'):
                        adapter.receive_escalation(event)
                    self.logger.info("Escalation routed to %s", slot_name)
                except Exception as exc:
                    self.logger.exception("Failed to route escalation to %s: %s", slot_name, exc)

    def get_escalation_summary(self, limit: int = 50) -> Dict[str, Any]:
        """Get summary of recent escalations."""
        recent_events = self._escalation_history[-limit:]
        
        # Count by threat level
        level_counts = {}
        for level in ThreatLevel:
            level_counts[level.value] = sum(1 for e in recent_events if e.threat_level == level)
        
        return {
            "total_escalations": len(recent_events),
            "threat_level_distribution": level_counts,
            "most_recent": recent_events[-1].__dict__ if recent_events else None,
            "history_size": len(self._escalation_history)
        }