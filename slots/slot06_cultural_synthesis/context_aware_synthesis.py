"""
Slot 6 Cultural Synthesis - Context-Aware Decision Making

Integrates with Semantic Mirror to make context-aware cultural synthesis
decisions based on system-wide state, particularly Slot 7 production control
pressure and resource availability.
"""
import time
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from orchestrator.semantic_mirror import get_semantic_mirror

logger = logging.getLogger(__name__)


@dataclass
class SystemContext:
    """System-wide context for cultural synthesis decisions."""
    production_pressure: float  # 0.0-1.0
    breaker_state: str  # "closed", "open", "half-open"  
    resource_utilization: float  # 0.0-1.0
    system_health: str  # "healthy", "degraded"
    context_available: bool
    timestamp: float


class ContextAwareCulturalSynthesis:
    """Enhances cultural synthesis with system-wide contextual awareness."""
    
    def __init__(self, base_engine=None):
        self.base_engine = base_engine  # Original CulturalSynthesisEngine
        self.semantic_mirror = get_semantic_mirror()
        self.context_cache_ttl = 30.0  # Cache context for 30 seconds
        self.last_context_fetch = 0.0
        self.cached_system_context: Optional[SystemContext] = None
        
        # Context-aware synthesis configuration
        self.pressure_thresholds = {
            "low": 0.3,      # Normal operation
            "medium": 0.6,   # Start reducing complexity
            "high": 0.8,     # Aggressive simplification
            "critical": 0.95 # Emergency mode
        }
        
        logger.info("Context-Aware Cultural Synthesis initialized")
    
    def synthesize_with_context(self, cultural_profile: Dict[str, Any], 
                               institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform cultural synthesis with system context awareness.
        
        Args:
            cultural_profile: Base cultural profile data
            institution_data: Institution-specific data
            
        Returns:
            Enhanced cultural synthesis results with context adaptations
        """
        # Get system context
        system_context = self._get_system_context()
        
        # Perform base synthesis
        if self.base_engine:
            base_results = self.base_engine.synthesize(cultural_profile)
        else:
            # Fallback synthesis for testing/demo
            base_results = self._fallback_synthesis(cultural_profile, institution_data)
        
        # Apply context-aware adaptations
        adapted_results = self._apply_context_adaptations(base_results, system_context)
        
        # Add context metadata
        adapted_results["_context"] = {
            "system_pressure": system_context.production_pressure if system_context.context_available else None,
            "adaptations_applied": self._get_applied_adaptations(system_context),
            "context_timestamp": system_context.timestamp,
            "context_available": system_context.context_available
        }
        
        return adapted_results
    
    def _get_system_context(self) -> SystemContext:
        """Retrieve current system context with caching."""
        current_time = time.time()
        
        # Use cached context if still fresh
        if (self.cached_system_context and 
            (current_time - self.last_context_fetch) < self.context_cache_ttl):
            return self.cached_system_context
        
        try:
            # Fetch context from Semantic Mirror
            breaker_state = self.semantic_mirror.get_context("slot07.breaker_state", "slot06_cultural_synthesis")
            pressure_level = self.semantic_mirror.get_context("slot07.pressure_level", "slot06_cultural_synthesis")
            resource_status = self.semantic_mirror.get_context("slot07.resource_status", "slot06_cultural_synthesis")
            health_summary = self.semantic_mirror.get_context("slot07.health_summary", "slot06_cultural_synthesis")
            
            if breaker_state is not None and pressure_level is not None:
                # Successfully retrieved context
                resource_util = 0.0
                system_health = "healthy"
                
                if resource_status:
                    resource_util = resource_status.get("utilization", 0.0)
                
                if health_summary:
                    system_health = health_summary.get("overall_status", "healthy")
                
                context = SystemContext(
                    production_pressure=pressure_level,
                    breaker_state=breaker_state,
                    resource_utilization=resource_util,
                    system_health=system_health,
                    context_available=True,
                    timestamp=current_time
                )
                
                logger.debug(f"Retrieved system context: pressure={pressure_level:.2f}, state={breaker_state}")
                
            else:
                # Context not available - use fallback
                context = SystemContext(
                    production_pressure=0.0,
                    breaker_state="unknown",
                    resource_utilization=0.0,
                    system_health="unknown",
                    context_available=False,
                    timestamp=current_time
                )
                
                logger.debug("System context not available, using fallback")
            
            # Cache the context
            self.cached_system_context = context
            self.last_context_fetch = current_time
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to retrieve system context: {e}")
            # Return fallback context
            return SystemContext(
                production_pressure=0.0,
                breaker_state="error",
                resource_utilization=0.0,
                system_health="error",
                context_available=False,
                timestamp=current_time
            )
    
    def _apply_context_adaptations(self, base_results: Dict[str, Any], 
                                 system_context: SystemContext) -> Dict[str, Any]:
        """Apply context-aware adaptations to synthesis results."""
        adapted_results = base_results.copy()
        
        if not system_context.context_available:
            return adapted_results
        
        # Determine pressure level category
        pressure_level = self._categorize_pressure(system_context.production_pressure)
        
        # Apply complexity reduction based on system pressure
        if pressure_level in ["medium", "high", "critical"]:
            adapted_results = self._reduce_synthesis_complexity(adapted_results, pressure_level, system_context)
        
        # Apply circuit breaker state adaptations
        if system_context.breaker_state == "open":
            adapted_results = self._apply_circuit_breaker_adaptations(adapted_results, system_context)
        elif system_context.breaker_state == "half-open":
            adapted_results = self._apply_recovery_adaptations(adapted_results, system_context)
        
        # Apply resource-aware optimizations
        if system_context.resource_utilization > 0.7:
            adapted_results = self._apply_resource_optimizations(adapted_results, system_context)
        
        return adapted_results
    
    def _categorize_pressure(self, pressure: float) -> str:
        """Categorize system pressure level."""
        if pressure >= self.pressure_thresholds["critical"]:
            return "critical"
        elif pressure >= self.pressure_thresholds["high"]:
            return "high"
        elif pressure >= self.pressure_thresholds["medium"]:
            return "medium"
        else:
            return "low"
    
    def _reduce_synthesis_complexity(self, results: Dict[str, Any], pressure_level: str, 
                                   context: SystemContext) -> Dict[str, Any]:
        """Reduce cultural synthesis complexity during system pressure."""
        complexity_reductions = {
            "medium": 0.8,   # 20% reduction
            "high": 0.6,     # 40% reduction  
            "critical": 0.4  # 60% reduction
        }
        
        reduction_factor = complexity_reductions.get(pressure_level, 1.0)
        
        # Apply complexity reduction to synthesis results
        if "complexity_factor" in results:
            results["complexity_factor"] *= reduction_factor
        else:
            results["complexity_factor"] = reduction_factor
        
        # Reduce cultural nuance analysis during high pressure
        if pressure_level in ["high", "critical"]:
            results["cultural_nuance_depth"] = "simplified"
            
            # Simplify adaptation recommendations
            if "adaptation_recommendations" in results:
                recommendations = results["adaptation_recommendations"]
                if isinstance(recommendations, list) and len(recommendations) > 3:
                    # Keep only top 3 recommendations during pressure
                    results["adaptation_recommendations"] = recommendations[:3]
        
        # Add pressure adaptation metadata
        results["_pressure_adaptations"] = {
            "complexity_reduction": 1.0 - reduction_factor,
            "pressure_level": pressure_level,
            "trigger": "system_pressure"
        }
        
        logger.debug(f"Applied complexity reduction: {reduction_factor:.2f} for pressure level {pressure_level}")
        return results
    
    def _apply_circuit_breaker_adaptations(self, results: Dict[str, Any], 
                                         context: SystemContext) -> Dict[str, Any]:
        """Apply adaptations when circuit breaker is open."""
        # Switch to conservative cultural synthesis mode
        results["synthesis_mode"] = "conservative"
        results["risk_tolerance"] = "low"
        
        # Reduce adaptation aggressiveness
        if "adaptation_rate" in results:
            results["adaptation_rate"] = min(results["adaptation_rate"], 0.3)
        
        # Prioritize stability over innovation
        if "innovation_factor" in results:
            results["innovation_factor"] *= 0.5
        
        results["_circuit_breaker_adaptations"] = {
            "mode": "conservative",
            "risk_reduction": True,
            "stability_prioritized": True
        }
        
        logger.debug("Applied circuit breaker adaptations (conservative mode)")
        return results
    
    def _apply_recovery_adaptations(self, results: Dict[str, Any], 
                                  context: SystemContext) -> Dict[str, Any]:
        """Apply adaptations when circuit breaker is in half-open recovery mode."""
        # Cautious recovery mode
        results["synthesis_mode"] = "cautious"
        
        # Gradual adaptation rate increase
        if "adaptation_rate" in results:
            results["adaptation_rate"] = min(results["adaptation_rate"], 0.6)
        
        results["_recovery_adaptations"] = {
            "mode": "cautious",
            "gradual_recovery": True
        }
        
        logger.debug("Applied recovery adaptations (cautious mode)")
        return results
    
    def _apply_resource_optimizations(self, results: Dict[str, Any], 
                                    context: SystemContext) -> Dict[str, Any]:
        """Apply optimizations when system resources are constrained."""
        # Reduce computational complexity
        results["computational_complexity"] = "optimized"
        
        # Cache cultural patterns more aggressively
        results["caching_strategy"] = "aggressive"
        
        # Simplify cultural model depth
        if "cultural_model_depth" in results:
            results["cultural_model_depth"] = min(results["cultural_model_depth"], 3)
        
        results["_resource_optimizations"] = {
            "optimization_applied": True,
            "resource_utilization": context.resource_utilization
        }
        
        logger.debug(f"Applied resource optimizations for {context.resource_utilization:.1%} utilization")
        return results
    
    def _get_applied_adaptations(self, context: SystemContext) -> list:
        """Get list of adaptations that were applied."""
        adaptations = []
        
        if not context.context_available:
            return adaptations
        
        pressure_level = self._categorize_pressure(context.production_pressure)
        if pressure_level != "low":
            adaptations.append(f"complexity_reduction_{pressure_level}")
        
        if context.breaker_state == "open":
            adaptations.append("circuit_breaker_conservative")
        elif context.breaker_state == "half-open":
            adaptations.append("recovery_cautious")
        
        if context.resource_utilization > 0.7:
            adaptations.append("resource_optimization")
        
        return adaptations
    
    def _fallback_synthesis(self, cultural_profile: Dict[str, Any], 
                          institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback synthesis when base engine is not available."""
        return {
            "principle_preservation_score": 0.8,
            "cultural_fit": 0.75,
            "adaptation_rate": 0.6,
            "complexity_factor": 1.0,
            "synthesis_mode": "standard",
            "cultural_nuance_depth": "full",
            "fallback_mode": True
        }
    
    def publish_synthesis_context(self, synthesis_results: Dict[str, Any]) -> bool:
        """Publish synthesis results as context for other slots."""
        try:
            # Publish cultural profile context
            cultural_context = {
                "adaptation_rate": synthesis_results.get("adaptation_rate", 0.5),
                "complexity_factor": synthesis_results.get("complexity_factor", 1.0),
                "cultural_fit": synthesis_results.get("cultural_fit", 0.5),
                "synthesis_mode": synthesis_results.get("synthesis_mode", "standard")
            }
            
            success = self.semantic_mirror.publish_context(
                "slot06.cultural_profile",
                cultural_context,
                "slot06_cultural_synthesis",
                ttl_seconds=120.0
            )
            
            if success:
                logger.debug("Published cultural synthesis context")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to publish synthesis context: {e}")
            return False


# Global context-aware synthesis instance
_context_aware_synthesis: Optional[ContextAwareCulturalSynthesis] = None


def get_context_aware_synthesis(base_engine=None) -> ContextAwareCulturalSynthesis:
    """Get global context-aware cultural synthesis instance."""
    global _context_aware_synthesis
    if _context_aware_synthesis is None:
        _context_aware_synthesis = ContextAwareCulturalSynthesis(base_engine)
    return _context_aware_synthesis


def reset_context_aware_synthesis() -> None:
    """Reset global context-aware synthesis (for testing)."""
    global _context_aware_synthesis
    _context_aware_synthesis = None