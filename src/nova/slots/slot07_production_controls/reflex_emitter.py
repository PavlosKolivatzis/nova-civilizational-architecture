"""
Slot 7 Production Controls - Reflex Signal Emitter

Emits bounded, hysteresis-protected reflex signals for system coordination.
Provides breaker_pressure, memory_pressure, and integrity_violation signals
with configurable thresholds, cooldowns, and smoothing.
"""
from __future__ import annotations
import os
import time
import yaml
import logging
import threading
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ReflexLedgerEntry:
    """Audit entry for reflex signal emission."""
    timestamp: float
    signal_type: str
    cause: str
    pressure_level: float
    raw_pressure: float
    clamped_pressure: float
    trace_id: str
    engine_snapshot: Dict[str, Any] = field(default_factory=dict)
    emission_allowed: bool = True
    cooldown_remaining: float = 0.0


@dataclass
class ReflexSignal:
    """Structured reflex signal for downstream processing."""
    signal_type: str
    source_slot: str
    pressure_level: float
    cause: str
    timestamp: float
    trace_id: str
    clamps: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReflexPolicyManager:
    """Manages reflex emission policies and configuration."""
    
    def __init__(self, policy_file: Optional[str] = None):
        self.policy_file = policy_file or self._get_default_policy_file()
        self.policy = self._load_policy()
        self.last_policy_load = time.time()
        self._lock = threading.Lock()
        
    def _get_default_policy_file(self) -> str:
        """Get default policy file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "core" / "rules.yaml")
        
    def _load_policy(self) -> Dict[str, Any]:
        """Load reflex emission policy from YAML file."""
        try:
            with open(self.policy_file, 'r') as f:
                policy = yaml.safe_load(f)
                
            # Apply environment-specific overrides
            current_env = os.getenv("NOVA_CURRENT_MODE", "development")
            if current_env in policy.get("environments", {}):
                env_overrides = policy["environments"][current_env]
                policy = self._deep_merge_policy(policy, env_overrides)
                
            return policy
            
        except Exception as e:
            logger.error(f"Failed to load reflex policy from {self.policy_file}: {e}")
            return self._get_default_policy()
    
    def _deep_merge_policy(self, base_policy: Dict, overrides: Dict) -> Dict:
        """Deep merge policy overrides."""
        merged = base_policy.copy()
        for key, value in overrides.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._deep_merge_policy(merged[key], value)
            else:
                merged[key] = value
        return merged
    
    def _get_default_policy(self) -> Dict[str, Any]:
        """Get default policy if file loading fails."""
        return {
            "reflex_policy": {
                "enabled": False,
                "shadow_mode": True,
                "max_emission_rate": 1.0,
                "smoothing_alpha": 0.2,
                "debounce_window_seconds": 5.0
            },
            "signals": {
                "breaker_pressure": {
                    "thresholds": {"rise_threshold": 0.8, "fall_threshold": 0.6},
                    "cooldown_seconds": 10.0,
                    "clamps": {"min_frequency_multiplier": 0.3, "max_frequency_multiplier": 1.0}
                }
            }
        }
    
    def get_signal_config(self, signal_type: str) -> Dict[str, Any]:
        """Get configuration for specific signal type."""
        return self.policy.get("signals", {}).get(signal_type, {})
    
    def get_global_config(self) -> Dict[str, Any]:
        """Get global reflex policy configuration."""
        return self.policy.get("reflex_policy", {})
    
    def is_emission_enabled(self) -> bool:
        """Check if reflex emission is globally enabled."""
        # Environment variable override takes precedence
        env_enabled = os.getenv("NOVA_REFLEX_ENABLED", "").lower()
        if env_enabled in ("true", "false"):
            return env_enabled == "true"
        
        return self.get_global_config().get("enabled", False)
    
    def is_shadow_mode(self) -> bool:
        """Check if running in shadow mode (compute but don't act)."""
        env_shadow = os.getenv("NOVA_REFLEX_SHADOW", "").lower()
        if env_shadow in ("true", "false"):
            return env_shadow == "true"
            
        return self.get_global_config().get("shadow_mode", True)


class ReflexEmitter:
    """
    Core reflex signal emitter with hysteresis, debouncing, and rate limiting.
    
    Emits bounded signals that can coordinate with upstream slots without
    violating system stability or overwhelming downstream processors.
    """
    
    def __init__(self, reflex_bus: Optional[Callable] = None, policy_manager: Optional[ReflexPolicyManager] = None):
        self.reflex_bus = reflex_bus  # Will be wired during setup
        self.policy_manager = policy_manager or ReflexPolicyManager()
        
        # State tracking for hysteresis and debouncing
        self.signal_states = {}  # signal_type -> current state
        self.last_emissions = {}  # signal_type -> last emission timestamp
        self.emission_counts = defaultdict(int)  # signal_type -> count in current window
        self.smoothed_pressures = {}  # signal_type -> smoothed pressure value
        
        # Audit ledger
        self.ledger = deque(maxlen=1000)  # Bounded ledger for memory management
        self._lock = threading.Lock()
        
        # Rate limiting
        self.emission_window_start = time.time()
        self.emissions_in_window = 0
        
        # Blocked signal tracking for diagnostics
        self.blocked_signals = defaultdict(int)  # reason -> count
        
        logger.info(f"ReflexEmitter initialized, shadow_mode={self.policy_manager.is_shadow_mode()}")
    
    def emit_breaker_pressure(self, circuit_state: str, raw_pressure: float, 
                            cause: str = "circuit_breaker", trace_id: Optional[str] = None) -> bool:
        """
        Emit breaker pressure signal for upstream throttling.
        
        Args:
            circuit_state: Current circuit breaker state (closed/open/half-open)
            raw_pressure: Raw pressure level (0.0-1.0)
            cause: Human-readable cause description
            trace_id: Optional trace ID for correlation
            
        Returns:
            True if signal was emitted (or would be in non-shadow mode)
        """
        return self._emit_signal(
            signal_type="breaker_pressure",
            raw_pressure=raw_pressure,
            cause=cause,
            trace_id=trace_id,
            metadata={"circuit_state": circuit_state}
        )
    
    def emit_memory_pressure(self, active_requests: int, max_requests: int, 
                           resource_violations: int, cause: str = "resource_pressure", 
                           trace_id: Optional[str] = None) -> bool:
        """Emit memory/resource pressure signal."""
        # Calculate pressure from resource utilization
        request_pressure = active_requests / max(1, max_requests)
        violation_pressure = min(1.0, resource_violations / 10.0)  # Scale violations
        raw_pressure = min(1.0, max(request_pressure, violation_pressure))
        
        return self._emit_signal(
            signal_type="memory_pressure",
            raw_pressure=raw_pressure,
            cause=cause,
            trace_id=trace_id,
            metadata={
                "active_requests": active_requests,
                "max_requests": max_requests,
                "resource_violations": resource_violations
            }
        )
    
    def emit_integrity_violation(self, violation_severity: float, violation_type: str,
                               cause: str = "integrity_violation", trace_id: Optional[str] = None) -> bool:
        """Emit integrity/security violation signal."""
        return self._emit_signal(
            signal_type="integrity_violation",
            raw_pressure=violation_severity,
            cause=cause,
            trace_id=trace_id,
            metadata={"violation_type": violation_type, "severity": violation_severity}
        )
    
    def _emit_signal(self, signal_type: str, raw_pressure: float, cause: str, 
                    trace_id: Optional[str], metadata: Dict[str, Any]) -> bool:
        """
        Core signal emission with hysteresis, debouncing, and rate limiting.
        
        Args:
            signal_type: Type of reflex signal
            raw_pressure: Raw pressure value before smoothing/clamping
            cause: Cause description for audit trail
            trace_id: Trace ID for correlation
            metadata: Additional signal metadata
            
        Returns:
            True if signal was emitted or would be emitted in non-shadow mode
        """
        current_time = time.time()
        trace_id = trace_id or f"reflex_{int(current_time * 1000)}"
        
        with self._lock:
            # Get signal configuration
            signal_config = self.policy_manager.get_signal_config(signal_type)
            if not signal_config:
                logger.warning(f"No configuration found for signal type: {signal_type}")
                return False
            
            # Apply exponential smoothing to prevent oscillation
            smoothing_alpha = self.policy_manager.get_global_config().get("smoothing_alpha", 0.2)
            if signal_type in self.smoothed_pressures:
                smoothed_pressure = (
                    smoothing_alpha * raw_pressure + 
                    (1 - smoothing_alpha) * self.smoothed_pressures[signal_type]
                )
            else:
                smoothed_pressure = raw_pressure
            
            self.smoothed_pressures[signal_type] = smoothed_pressure
            
            # Apply hysteresis to prevent rapid state changes (use raw pressure for thresholds)
            should_emit = self._check_hysteresis(signal_type, raw_pressure, signal_config)
            
            # Check cooldown period
            cooldown_remaining = self._check_cooldown(signal_type, current_time, signal_config)
            block_reason = None
            if cooldown_remaining > 0:
                should_emit = False
                block_reason = "cooldown"
            
            # Check global rate limiting
            if should_emit and not self._check_rate_limit(current_time):
                should_emit = False
                block_reason = "rate_limit"
                logger.debug(f"Rate limit exceeded for {signal_type} emission")
            
            # Track blocked signals for diagnostics
            if not should_emit and block_reason:
                self.blocked_signals[block_reason] += 1
            
            # Apply signal clamping for downstream safety
            clamped_pressure, clamps = self._apply_clamps(smoothed_pressure, signal_config)
            
            # Create ledger entry for audit trail
            ledger_entry = ReflexLedgerEntry(
                timestamp=current_time,
                signal_type=signal_type,
                cause=cause,
                pressure_level=clamped_pressure,
                raw_pressure=raw_pressure,
                clamped_pressure=clamped_pressure,
                trace_id=trace_id,
                emission_allowed=should_emit,
                cooldown_remaining=cooldown_remaining
            )
            
            self.ledger.append(ledger_entry)
            
            # Actually emit signal if conditions are met
            if should_emit:
                success = self._perform_emission(
                    signal_type, clamped_pressure, cause, trace_id, clamps, metadata, current_time
                )
                
                if success:
                    self.last_emissions[signal_type] = current_time
                    self.emission_counts[signal_type] += 1
                    
                return success
            
            return False  # Signal not emitted due to hysteresis/cooldown/rate limiting
    
    def _check_hysteresis(self, signal_type: str, pressure: float, config: Dict[str, Any]) -> bool:
        """Check hysteresis thresholds to prevent oscillation using raw pressure, not smoothed."""
        hysteresis = config.get("hysteresis", {})
        rise_threshold = hysteresis.get("rise_threshold", 0.8)
        fall_threshold = hysteresis.get("fall_threshold", 0.6)
        
        current_state = self.signal_states.get(signal_type, False)
        
        if not current_state and pressure >= rise_threshold:
            # Pressure rising above threshold - start emitting
            self.signal_states[signal_type] = True
            return True
        elif current_state and pressure <= fall_threshold:
            # Pressure falling below threshold - stop emitting
            self.signal_states[signal_type] = False
            return False
        elif current_state:
            # Continue emitting while in active state
            return True
        
        return False
    
    def _check_cooldown(self, signal_type: str, current_time: float, config: Dict[str, Any]) -> float:
        """Check if signal is in cooldown period. Returns remaining cooldown seconds."""
        cooldown_seconds = config.get("cooldown_seconds", 10.0)
        last_emission = self.last_emissions.get(signal_type, 0.0)
        
        time_since_last = current_time - last_emission
        if time_since_last < cooldown_seconds:
            return cooldown_seconds - time_since_last
        
        return 0.0
    
    def _check_rate_limit(self, current_time: float) -> bool:
        """Check global emission rate limit."""
        global_config = self.policy_manager.get_global_config()
        max_rate = global_config.get("max_emission_rate", 1.0)  # signals per second
        window_size = 60.0  # 1 minute window
        
        # Reset window if needed
        if current_time - self.emission_window_start >= window_size:
            self.emission_window_start = current_time
            self.emissions_in_window = 0
        
        # Check if we're within rate limit
        max_emissions_in_window = max_rate * window_size
        return self.emissions_in_window < max_emissions_in_window
    
    def _apply_clamps(self, pressure: float, config: Dict[str, Any]) -> tuple[float, Dict[str, float]]:
        """Apply signal clamping for downstream safety."""
        clamps_config = config.get("clamps", {})
        
        # Clamp pressure to safe bounds
        clamped_pressure = max(0.0, min(1.0, pressure))
        
        # Calculate downstream effect clamps
        clamps = {
            "min_frequency_multiplier": clamps_config.get("min_frequency_multiplier", 0.1),
            "max_frequency_multiplier": clamps_config.get("max_frequency_multiplier", 1.0),
            "min_weight_multiplier": clamps_config.get("min_weight_multiplier", 0.1),
            "max_weight_multiplier": clamps_config.get("max_weight_multiplier", 1.0)
        }
        
        return clamped_pressure, clamps
    
    def _perform_emission(self, signal_type: str, pressure: float, cause: str,
                         trace_id: str, clamps: Dict[str, float], metadata: Dict[str, Any],
                         current_time: float) -> bool:
        """Actually emit the reflex signal."""
        # Check if we should emit (not in shadow mode) and have a reflex bus
        shadow_mode = self.policy_manager.is_shadow_mode()
        emission_enabled = self.policy_manager.is_emission_enabled()
        
        # Create reflex signal
        signal = ReflexSignal(
            signal_type=signal_type,
            source_slot="slot07_production_controls",
            pressure_level=pressure,
            cause=cause,
            timestamp=current_time,
            trace_id=trace_id,
            clamps=clamps,
            metadata=metadata
        )
        
        # Log emission
        if shadow_mode:
            logger.info(f"SHADOW: Would emit {signal_type} reflex (pressure={pressure:.3f}, cause={cause})")
        else:
            logger.info(f"Emitting {signal_type} reflex (pressure={pressure:.3f}, cause={cause})")
        
        # Actually emit to reflex bus if not in shadow mode and enabled
        if not shadow_mode and emission_enabled and self.reflex_bus:
            try:
                self.reflex_bus(signal)
                self.emissions_in_window += 1
                return True
            except Exception as e:
                logger.error(f"Failed to emit {signal_type} reflex signal: {e}")
                return False
        
        # In shadow mode or without bus, consider it successful for testing
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get reflex emitter metrics for monitoring."""
        with self._lock:
            return {
                "emission_enabled": self.policy_manager.is_emission_enabled(),
                "shadow_mode": self.policy_manager.is_shadow_mode(),
                "total_ledger_entries": len(self.ledger),
                "signals_emitted_by_type": dict(self.emission_counts),
                "active_signal_states": dict(self.signal_states),
                "smoothed_pressures": dict(self.smoothed_pressures),
                "emissions_in_current_window": self.emissions_in_window,
                "window_start": self.emission_window_start,
                "last_emissions": dict(self.last_emissions),
                "blocked_signals_by_reason": dict(self.blocked_signals)
            }
    
    def get_recent_ledger(self, limit: int = 50) -> List[ReflexLedgerEntry]:
        """Get recent ledger entries for debugging."""
        with self._lock:
            return list(self.ledger)[-limit:]
    
    def reset_state(self) -> None:
        """Reset emitter state (for testing)."""
        with self._lock:
            self.signal_states.clear()
            self.last_emissions.clear()
            self.emission_counts.clear()
            self.smoothed_pressures.clear()
            self.ledger.clear()
            self.emissions_in_window = 0
            self.emission_window_start = time.time()


# Global reflex emitter instance
_reflex_emitter = None


def get_reflex_emitter(reflex_bus: Optional[Callable] = None, 
                      policy_manager: Optional[ReflexPolicyManager] = None) -> ReflexEmitter:
    """Get global reflex emitter instance."""
    global _reflex_emitter
    if _reflex_emitter is None:
        _reflex_emitter = ReflexEmitter(reflex_bus, policy_manager)
    return _reflex_emitter


def reset_reflex_emitter() -> None:
    """Reset global reflex emitter (for testing)."""
    global _reflex_emitter
    _reflex_emitter = None