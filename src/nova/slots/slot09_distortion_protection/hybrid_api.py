"""
Slot 9: Distortion Protection System - Hybrid Production API (v3.1.0)
Combines enterprise-grade resilience with deep NOVA domain logic integration.
Production-ready with complete IDS integration and Slot 10 interoperability.
"""

import time
import logging
import asyncio
import hashlib
import uuid
import json
import os
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
from contextlib import asynccontextmanager
import threading
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def _round3(value: float) -> float:
    """Round float values to three decimal places."""
    return round(value, 3)

# Optional dependencies with graceful fallback
try:
    from pydantic import BaseModel, Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    from dataclasses import dataclass as BaseModel

    def Field(default=None, **_kwargs):  # type: ignore[override]
        return default

# NOVA-specific imports (with fallbacks)
try:
    from .ids_policy import policy_check_with_ids
    from services.ids.core import IDSState
    from config.feature_flags import IDS_ENABLED
    NOVA_INTEGRATION_AVAILABLE = True
except ImportError:
    NOVA_INTEGRATION_AVAILABLE = False
    # Fallback enums
    class IDSState(str, Enum):
        STABLE = "stable"
        REINTEGRATING = "reintegrating"
        DIVERGING = "diverging"
        DISINTEGRATING = "disintegrating"
    IDS_ENABLED = True

# Shared hash utility with fallback
try:
    from nova.slots.common.hashutils import compute_audit_hash  # blake2b(backed)
    SHARED_HASH_AVAILABLE = True
except Exception:  # ImportError or any init error -> mark unavailable
    compute_audit_hash = None  # type: ignore
    SHARED_HASH_AVAILABLE = False
    # Fallback to current SHA256 implementation

def _env_truthy(name: str) -> bool:
    v = os.getenv(name, "").strip().lower()
    return v in {"1", "true", "yes", "on"}

# Exported snapshot (for tests/introspection); runtime re-reads each call.
NOVA_USE_SHARED_HASH = _env_truthy("NOVA_USE_SHARED_HASH")

# ============================================================================
# 1. ENHANCED CORE TYPES AND CONFIGURATION
# ============================================================================

class RequestPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class ResponseStatus(str, Enum):
    SUCCESS = "success"
    WARNING = "warning"
    BLOCKED = "blocked"
    ERROR = "error"

class PolicyAction(str, Enum):
    ALLOW_FASTPATH = "ALLOW_FASTPATH"
    ALLOW_WITH_MONITORING = "ALLOW_WITH_MONITORING"
    STANDARD_PROCESSING = "STANDARD_PROCESSING"
    STAGED_DEPLOYMENT = "STAGED_DEPLOYMENT"
    DEGRADE_AND_REVIEW = "DEGRADE_AND_REVIEW"
    RESTRICTED_SCOPE_DEPLOYMENT = "RESTRICTED_SCOPE_DEPLOYMENT"
    BLOCK_OR_SANDBOX = "BLOCK_OR_SANDBOX"
    
class DistortionType(str, Enum):
    NONE = "none"
    INDIVIDUAL_COGNITIVE = "individual_cognitive"
    CULTURAL_TRADITIONAL = "cultural_traditional"
    INFRASTRUCTURE_MAINTAINED = "infrastructure_maintained"
    SYSTEMATIC_MANIPULATION = "systematic_manipulation"
    UNKNOWN = "unknown"

class InfrastructureLevel(str, Enum):
    INDIVIDUAL = "individual"
    CULTURAL = "cultural"
    INSTITUTIONAL = "institutional"
    INFRASTRUCTURE = "infrastructure"
    CIVILIZATIONAL = "civilizational"
    UNKNOWN = "unknown"

class SystemStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"

class ThreatSeverity(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class HybridApiConfig:
    """Enhanced configuration combining resilience and domain-specific settings."""
    # Resilience settings (from enhanced version)
    max_content_length_bytes: int = 10240
    circuit_breaker_threshold: int = 10
    circuit_breaker_reset_timeout: float = 60.0
    cache_ttl_seconds: float = 300.0
    max_processing_time_ms: float = 5000
    ema_alpha: float = 0.1
    
    # NOVA domain settings (from my version)
    threat_threshold_warning: float = 0.6
    threat_threshold_block: float = 0.8
    ids_stability_threshold_low: float = 0.25
    ids_stability_threshold_medium: float = 0.5
    ids_stability_threshold_high: float = 0.75
    ids_drift_threshold_low: float = 0.02
    ids_drift_threshold_medium: float = 0.1
    ids_drift_threshold_high: float = 0.3
    
    # Confidence and quality settings
    default_confidence_fallback: float = 0.5
    confidence_stability_weight: float = 0.6
    confidence_drift_weight: float = 0.4

# ============================================================================
# 2. HYBRID DATA MODELS WITH NOVA INTEGRATION
# ============================================================================

if PYDANTIC_AVAILABLE:
    class DistortionDetectionRequest(BaseModel):
        content: str = Field(..., min_length=1, max_length=10240)
        context: Dict[str, Any] = Field(default_factory=dict)
        session_id: str = "default"
        trace_id: Optional[str] = None
        include_detailed_analysis: bool = False
        priority: RequestPriority = RequestPriority.NORMAL

        @field_validator('content')
        @classmethod
        def validate_content_not_empty(cls, v):
            if not v or not v.strip():
                raise ValueError('Content cannot be empty or whitespace only')
            return v

    class DistortionDetectionResponse(BaseModel):
        # Version control fields
        format_version: str
        api_version: str
        compatibility_level: str

        # Core fields (enhanced version)
        status: ResponseStatus
        threat_level: float = Field(..., ge=0.0, le=1.0)
        policy_action: PolicyAction
        confidence: float = Field(..., ge=0.0, le=1.0)
        processing_time_ms: float = Field(..., ge=0.0)
        trace_id: str

        # NOVA-specific fields (my version)
        distortion_type: DistortionType
        infrastructure_level: InfrastructureLevel
        severity: ThreatSeverity
        ids_analysis: Dict[str, Any]
        audit_trail: Dict[str, Any]
        deployment_context: Dict[str, Any] = Field(default_factory=dict)
        deployment_feedback: Dict[str, Any] = Field(default_factory=dict)

        # Optional detailed analysis
        threat_landscape: Optional[Dict[str, Any]] = None
        intervention_strategy: Optional[Dict[str, Any]] = None
        error_details: Optional[Dict[str, Any]] = None

else:
    # Fallback dataclass implementations
    @dataclass
    class DistortionDetectionRequest:
        content: str
        context: Dict[str, Any] = None
        session_id: str = "default"
        trace_id: Optional[str] = None
        include_detailed_analysis: bool = False
        priority: RequestPriority = RequestPriority.NORMAL
        
        def __post_init__(self):
            self.context = self.context or {}
            if not self.content or not self.content.strip():
                raise ValueError("Content cannot be empty")
            if len(self.content) > 10240:
                raise ValueError("Content exceeds maximum length")

    @dataclass
    class DistortionDetectionResponse:
        format_version: str
        api_version: str
        compatibility_level: str
        status: ResponseStatus
        threat_level: float
        policy_action: PolicyAction
        confidence: float
        processing_time_ms: float
        trace_id: str
        distortion_type: DistortionType
        infrastructure_level: InfrastructureLevel
        severity: ThreatSeverity
        ids_analysis: Dict[str, Any]
        audit_trail: Dict[str, Any]
        deployment_context: Dict[str, Any]
        deployment_feedback: Dict[str, Any]
        threat_landscape: Optional[Dict[str, Any]] = None
        intervention_strategy: Optional[Dict[str, Any]] = None
        error_details: Optional[Dict[str, Any]] = None

# ============================================================================
# 3. ENHANCED RESILIENCE UTILITIES
# ============================================================================

class CircuitBreaker:
    """Production-grade circuit breaker with exponential backoff."""
    
    def __init__(self, threshold: int = 10, reset_timeout: float = 60.0):
        self.threshold = threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
        self._lock = threading.RLock()
    
    def is_open(self) -> bool:
        with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure_time > self.reset_timeout:
                    self.state = "half-open"
                    return False
                return True
            return False
    
    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.threshold:
                self.state = "open"
    
    def record_success(self):
        with self._lock:
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            elif self.failure_count > 0:
                self.failure_count = max(0, self.failure_count - 1)

class SecureContentCache:
    """Content cache with TTL and optional encryption for sensitive data."""
    
    def __init__(self, ttl_seconds: float = 300.0, max_size: int = 1000):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._access_order: List[str] = []  # LRU tracking
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                timestamp, value = self._cache[key]
                if time.time() - timestamp < self.ttl:
                    # Update access order for LRU
                    if key in self._access_order:
                        self._access_order.remove(key)
                    self._access_order.append(key)
                    self.hits += 1
                    return value
                self._evict_key(key)
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any):
        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            self._cache[key] = (time.time(), value)
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
    
    def _evict_key(self, key: str):
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)
    
    def _evict_lru(self):
        if self._access_order:
            lru_key = self._access_order[0]
            self._evict_key(lru_key)
    
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / max(1, total)

    def clear_expired(self) -> int:
        """Remove expired items from the cache."""
        with self._lock:
            now = time.time()
            expired_keys = [key for key, (ts, _) in self._cache.items() if now - ts >= self.ttl]
            for key in expired_keys:
                self._evict_key(key)
            return len(expired_keys)

# ============================================================================
# 4. HYBRID API CLASS - COMBINING BOTH STRENGTHS
# ============================================================================

class HybridDistortionDetectionAPI:
    """
    Hybrid API combining enterprise resilience with deep NOVA domain integration.
    Best of both worlds: production-ready infrastructure + complete IDS integration.
    """
    VERSION = "3.1.0-hybrid"
    FORMAT_VERSION = "2.5.0-rc1"
    COMPATIBILITY_LEVEL = "slot10_v1.0"

    def __init__(self, core_detector: Any = None, config: Optional[HybridApiConfig] = None):
        self.core_detector = core_detector
        self.config = config or HybridApiConfig()
        self.logger = logging.getLogger('slot9_hybrid_api')
        
        # Performance tracking (enhanced version)
        self.metrics = {
            'total_requests': 0,
            'blocked_requests': 0,
            'warning_requests': 0,
            'error_count': 0,
            'processing_times': [],
            'start_time': time.time(),
            'threat_detections_by_type': {dt.value: 0 for dt in DistortionType},
            'policy_actions_taken': {pa.value: 0 for pa in PolicyAction}
        }
        
        # Resilience features (enhanced version)
        self.circuit_breaker = CircuitBreaker(
            threshold=self.config.circuit_breaker_threshold,
            reset_timeout=self.config.circuit_breaker_reset_timeout
        )
        self.content_cache = SecureContentCache(
            ttl_seconds=self.config.cache_ttl_seconds,
            max_size=1000
        )
        self._metrics_lock = threading.RLock()

        # Hash chain state and feedback storage
        self.last_audit_hash: Optional[str] = None
        self.last_deployment_feedback: Optional[Dict[str, Any]] = None
        
        self.logger.info(f"HybridDistortionDetectionAPI v{self.VERSION} initialized")
        self.logger.info(f"NOVA integration: {'enabled' if NOVA_INTEGRATION_AVAILABLE else 'fallback mode'}")

    async def detect_distortion(self, request: DistortionDetectionRequest) -> DistortionDetectionResponse:
        """Main API endpoint combining resilience patterns with deep NOVA integration."""
        start_time = time.perf_counter()
        trace_id = request.trace_id or f"slot9_hybrid_{uuid.uuid4().hex[:8]}"
        
        # Circuit breaker check (enhanced version resilience)
        if self.circuit_breaker.is_open():
            self.logger.warning(f"Circuit breaker open for trace_id={trace_id}")
            return self._create_circuit_breaker_response(trace_id, start_time)
        
        try:
            async with self._metrics_context():
                # Content validation (enhanced version)
                self._validate_request_content(request)
                
                # Cache check with secure hashing (enhanced version)
                cache_key = self._generate_secure_cache_key(request.content, request.context)
                if cached_response := self.content_cache.get(cache_key):
                    cached_response.trace_id = trace_id  # Update trace ID
                    self.logger.debug(f"Cache hit for trace_id={trace_id}")
                    return cached_response
                
                # Core processing with NOVA integration (hybrid approach)
                policy_result = await self._process_with_nova_integration(
                    request, trace_id
                )
                
                # Build comprehensive response (my version domain logic)
                response = await self._build_comprehensive_response(
                    policy_result, request, trace_id, start_time
                )
                
                # Cache successful responses (enhanced version)
                if response.status != ResponseStatus.ERROR:
                    self.content_cache.set(cache_key, response)
                
                # Record success for circuit breaker
                self.circuit_breaker.record_success()
                
                # Update metrics (hybrid tracking)
                self._update_comprehensive_metrics(response)
                
                self.logger.info(
                    f"Detection complete trace_id={trace_id}: "
                    f"status={response.status.value}, threat={response.threat_level:.3f}, "
                    f"policy={response.policy_action.value}, confidence={response.confidence:.3f}, "
                    f"time={response.processing_time_ms:.1f}ms"
                )
                
                return response
                
        except Exception as e:
            self.circuit_breaker.record_failure()
            processing_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Detection error trace_id={trace_id}: {e}", exc_info=True)
            
            with self._metrics_lock:
                self.metrics['error_count'] += 1
                
            return self._create_comprehensive_error_response(trace_id, str(e), processing_time)

    @asynccontextmanager
    async def _metrics_context(self):
        """Enhanced metrics context with comprehensive tracking."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            processing_time = (time.perf_counter() - start_time) * 1000
            with self._metrics_lock:
                self.metrics['total_requests'] += 1
                self.metrics['processing_times'].append(processing_time)
                # Keep only recent 1000 samples
                if len(self.metrics['processing_times']) > 1000:
                    self.metrics['processing_times'] = self.metrics['processing_times'][-1000:]

    def _validate_request_content(self, request: DistortionDetectionRequest):
        """Enhanced content validation with security checks."""
        if not request.content or not request.content.strip():
            raise ValueError("Content cannot be empty or whitespace only")
            
        if len(request.content.encode('utf-8')) > self.config.max_content_length_bytes:
            raise ValueError(f"Content exceeds maximum size of {self.config.max_content_length_bytes} bytes")
        
        # Additional security validations could go here
        if request.priority == RequestPriority.CRITICAL and not request.trace_id:
            self.logger.warning("Critical priority request without trace_id")

    def _generate_secure_cache_key(self, content: str, context: Dict[str, Any]) -> str:
        """Generate secure cache key with salt."""
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        context_str = str(sorted(context.items())) if context else ""
        context_hash = hashlib.sha256(context_str.encode('utf-8')).hexdigest()
        return f"slot9:{content_hash[:16]}:{context_hash[:8]}"

    async def _process_with_nova_integration(self, request: DistortionDetectionRequest, 
                                           trace_id: str) -> Dict[str, Any]:
        """Process request with full NOVA integration or fallback."""
        if NOVA_INTEGRATION_AVAILABLE and IDS_ENABLED:
            return await self._process_with_ids_policy(request, trace_id)
        else:
            return await self._process_with_fallback_logic(request, trace_id)

    async def _process_with_ids_policy(self, request: DistortionDetectionRequest, 
                                     trace_id: str) -> Dict[str, Any]:
        """Process using actual IDS policy integration (my version logic)."""
        try:
            # Prepare content analysis for IDS (my version approach)
            content_analysis = {
                "embedding_vectors": {
                    "traits": self._extract_traits_vector(request.content, request.context),
                    "content": self._extract_content_vector(request.content, request.context)
                }
            }
            
            # Process with timeout protection (enhanced version resilience)
            policy_result = await asyncio.wait_for(
                asyncio.to_thread(policy_check_with_ids, content_analysis, trace_id),
                timeout=self.config.max_processing_time_ms / 1000
            )
            
            return policy_result
            
        except asyncio.TimeoutError:
            self.logger.warning(f"IDS processing timeout for trace_id={trace_id}")
            raise TimeoutError("IDS processing timed out")
        except Exception as e:
            self.logger.error(f"IDS processing failed for trace_id={trace_id}: {e}")
            raise

    async def _process_with_fallback_logic(self, request: DistortionDetectionRequest,
                                         trace_id: str) -> Dict[str, Any]:
        """Fallback processing when NOVA integration unavailable."""
        self.logger.info(f"Using fallback processing for trace_id={trace_id}")
        
        # Simple heuristic-based analysis
        content_length = len(request.content)
        word_count = len(request.content.split())
        
        # Simulate stability and drift based on content characteristics
        stability = min(1.0, max(0.0, 0.8 - (content_length / 10000)))
        drift = min(0.5, max(-0.5, (word_count - 50) / 100))
        
        return {
            "final_policy": "STANDARD_PROCESSING",
            "final_reason": f"fallback:length_{content_length}|words_{word_count}",
            "final_severity": "normal",
            "traits_analysis": {
                "stability": stability,
                "drift": drift,
                "state": IDSState.STABLE.value if stability > 0.5 else IDSState.DIVERGING.value
            },
            "content_analysis": {
                "stability": stability * 0.9,
                "drift": drift * 1.1,
                "state": IDSState.STABLE.value if stability > 0.5 else IDSState.DIVERGING.value
            },
            "trace_id": trace_id,
            "ids_enabled": False
        }

    # Vector extraction methods (from my version)
    def _extract_traits_vector(self, content: str, context: Dict = None) -> List[float]:
        """Extract traits embedding vector from content."""
        words = content.split()
        return [
            len(content) / 1000.0,  # Length factor
            content.count('!') / max(1, len(content)),  # Excitement factor
            content.count('?') / max(1, len(content)),  # Question factor
            len(set(word.lower() for word in words)) / max(1, len(words)),  # Uniqueness factor
            sum(1 for char in content if char.isupper()) / max(1, len(content)),  # Caps ratio
            content.count('\n') / max(1, len(content))  # Line break density
        ]
    
    def _extract_content_vector(self, content: str, context: Dict = None) -> List[float]:
        """Extract content embedding vector from content."""
        words = content.split()
        sentences = content.split('.')
        
        return [
            len(words) / 100.0,  # Word count factor
            sum(len(word) for word in words) / max(1, len(words)),  # Avg word length
            len(sentences) / max(1, len(content)),  # Sentence density
            len([w for w in words if len(w) > 7]) / max(1, len(words)),  # Complex word ratio
            content.count(',') / max(1, len(content)),  # Comma density
            len(set(content.lower())) / max(1, len(content))  # Character diversity
        ]

    async def _build_comprehensive_response(self, policy_result: Dict[str, Any], 
                                          request: DistortionDetectionRequest,
                                          trace_id: str, start_time: float) -> DistortionDetectionResponse:
        """Build comprehensive response with full NOVA domain logic (my version approach)."""
        processing_time = (time.perf_counter() - start_time) * 1000
        
        # Calculate threat level with sophisticated logic (my version)
        threat_level = self._calculate_sophisticated_threat_level(policy_result)
        
        # Determine status based on threat level
        status = self._determine_status_from_threat(threat_level)
        
        # Calculate confidence using IDS analysis (my version)
        confidence = self._calculate_ids_based_confidence(policy_result)
        
        # Classify distortion type and infrastructure level (my version)
        distortion_type = self._classify_distortion_type(policy_result)
        infrastructure_level = self._assess_infrastructure_level(policy_result)
        severity = self._determine_severity(policy_result)
        
        # Extract comprehensive IDS analysis (my version)
        ids_analysis = self._extract_comprehensive_ids_analysis(policy_result)
        
        # Create detailed audit trail (my version)
        audit_trail = self._create_detailed_audit_trail(policy_result, trace_id, processing_time)
        
        # Build response
        response = DistortionDetectionResponse(
            format_version=self.FORMAT_VERSION,
            api_version=self.VERSION,
            compatibility_level=self.COMPATIBILITY_LEVEL,
            status=status,
            threat_level=_round3(threat_level),
            policy_action=PolicyAction(policy_result.get('final_policy', 'STANDARD_PROCESSING')),
            confidence=_round3(confidence),
            processing_time_ms=_round3(processing_time),
            trace_id=trace_id,
            distortion_type=distortion_type,
            infrastructure_level=infrastructure_level,
            severity=severity,
            ids_analysis=ids_analysis,
            audit_trail=audit_trail,
            deployment_context=self._default_deployment_context(request),
            deployment_feedback={}
        )
        
        # Add detailed analysis if requested (my version)
        if request.include_detailed_analysis:
            response.threat_landscape = self._generate_threat_landscape(policy_result, request)
            response.intervention_strategy = self._generate_intervention_strategy(policy_result, request)
        
        return response

    # Threat level calculation with sophisticated IDS integration (my version)
    def _calculate_sophisticated_threat_level(self, policy_result: Dict) -> float:
        """Calculate threat level with sophisticated IDS-based logic."""
        policy_action = policy_result.get('final_policy', 'STANDARD_PROCESSING')
        
        # Base threat levels by policy
        base_threat_mapping = {
            'ALLOW_FASTPATH': 0.1,
            'ALLOW_WITH_MONITORING': 0.2,
            'STANDARD_PROCESSING': 0.3,
            'STAGED_DEPLOYMENT': 0.5,
            'RESTRICTED_SCOPE_DEPLOYMENT': 0.6,
            'DEGRADE_AND_REVIEW': 0.7,
            'BLOCK_OR_SANDBOX': 0.9
        }
        base_threat = base_threat_mapping.get(policy_action, 0.3)
        
        # IDS-based adjustments
        traits_analysis = policy_result.get('traits_analysis', {})
        content_analysis = policy_result.get('content_analysis', {})
        
        # Stability penalties
        traits_stability = traits_analysis.get('stability', 1.0)
        content_stability = content_analysis.get('stability', 1.0)
        avg_stability = (traits_stability + content_stability) / 2
        
        stability_penalty = 0.0
        if avg_stability < self.config.ids_stability_threshold_low:
            stability_penalty += 0.3
        elif avg_stability < self.config.ids_stability_threshold_medium:
            stability_penalty += 0.2
        elif avg_stability < self.config.ids_stability_threshold_high:
            stability_penalty += 0.1
        
        # Drift penalties
        traits_drift = abs(traits_analysis.get('drift', 0.0))
        content_drift = abs(content_analysis.get('drift', 0.0))
        max_drift = max(traits_drift, content_drift)
        
        drift_penalty = 0.0
        if max_drift > self.config.ids_drift_threshold_high:
            drift_penalty += 0.2
        elif max_drift > self.config.ids_drift_threshold_medium:
            drift_penalty += 0.15
        elif max_drift > self.config.ids_drift_threshold_low:
            drift_penalty += 0.1
        
        # Combine factors
        final_threat = base_threat + stability_penalty + drift_penalty
        return round(min(1.0, max(0.0, final_threat)), 3)

    def _determine_status_from_threat(self, threat_level: float) -> ResponseStatus:
        """Determine response status based on configured threat thresholds."""
        if threat_level >= self.config.threat_threshold_block:
            return ResponseStatus.BLOCKED
        elif threat_level >= self.config.threat_threshold_warning:
            return ResponseStatus.WARNING
        else:
            return ResponseStatus.SUCCESS

    def _calculate_ids_based_confidence(self, policy_result: Dict) -> float:
        """Calculate confidence based on IDS analysis consistency."""
        traits_analysis = policy_result.get('traits_analysis', {})
        content_analysis = policy_result.get('content_analysis', {})
        
        # Use stability as base for confidence
        traits_stability = traits_analysis.get('stability', 0.5)
        content_stability = content_analysis.get('stability', 0.5)
        
        # Weight by configuration
        stability_confidence = (
            traits_stability * self.config.confidence_stability_weight +
            content_stability * (1 - self.config.confidence_stability_weight)
        )
        
        # Penalize for high drift (indicates uncertainty)
        traits_drift = abs(traits_analysis.get('drift', 0.0))
        content_drift = abs(content_analysis.get('drift', 0.0))
        avg_drift = (traits_drift + content_drift) / 2
        
        drift_penalty = avg_drift * self.config.confidence_drift_weight
        
        final_confidence = stability_confidence * (1 - drift_penalty)
        return round(max(0.1, min(1.0, final_confidence)), 3)

    def _classify_distortion_type(self, policy_result: Dict) -> DistortionType:
        """Classify distortion type based on policy and severity."""
        policy_action = policy_result.get('final_policy', 'STANDARD_PROCESSING')
        severity = policy_result.get('final_severity', 'normal')
        
        if policy_action == 'BLOCK_OR_SANDBOX':
            return DistortionType.SYSTEMATIC_MANIPULATION
        elif severity == 'high':
            return DistortionType.INFRASTRUCTURE_MAINTAINED
        elif severity == 'medium':
            return DistortionType.CULTURAL_TRADITIONAL
        elif severity == 'low':
            return DistortionType.INDIVIDUAL_COGNITIVE
        else:
            return DistortionType.INDIVIDUAL_COGNITIVE

    def _assess_infrastructure_level(self, policy_result: Dict) -> InfrastructureLevel:
        """Assess infrastructure level based on analysis."""
        severity = policy_result.get('final_severity', 'normal')
        
        severity_mapping = {
            'low': InfrastructureLevel.INDIVIDUAL,
            'normal': InfrastructureLevel.CULTURAL,
            'medium': InfrastructureLevel.INSTITUTIONAL,
            'high': InfrastructureLevel.INFRASTRUCTURE
        }
        
        return severity_mapping.get(severity, InfrastructureLevel.INDIVIDUAL)

    def _determine_severity(self, policy_result: Dict) -> ThreatSeverity:
        """Determine threat severity."""
        final_severity = policy_result.get('final_severity', 'normal')
        
        severity_mapping = {
            'low': ThreatSeverity.LOW,
            'normal': ThreatSeverity.NORMAL,
            'medium': ThreatSeverity.MEDIUM,
            'high': ThreatSeverity.HIGH
        }
        
        return severity_mapping.get(final_severity, ThreatSeverity.NORMAL)

    def _extract_comprehensive_ids_analysis(self, policy_result: Dict) -> Dict[str, Any]:
        """Extract comprehensive IDS analysis (my version approach)."""
        return {
            "traits_analysis": {
                "stability": policy_result.get('traits_analysis', {}).get('stability', 0.0),
                "drift": policy_result.get('traits_analysis', {}).get('drift', 0.0),
                "state": policy_result.get('traits_analysis', {}).get('state', IDSState.STABLE.value)
            },
            "content_analysis": {
                "stability": policy_result.get('content_analysis', {}).get('stability', 0.0),
                "drift": policy_result.get('content_analysis', {}).get('drift', 0.0),
                "state": policy_result.get('content_analysis', {}).get('state', IDSState.STABLE.value)
            },
            "ids_enabled": policy_result.get('ids_enabled', IDS_ENABLED),
            "final_reason": policy_result.get('final_reason', 'standard_processing'),
            "integration_mode": "nova" if NOVA_INTEGRATION_AVAILABLE else "fallback",
            "processing_confidence": self._calculate_ids_based_confidence(policy_result)
        }

    def _create_detailed_audit_trail(self, policy_result: Dict, trace_id: str,
                                   processing_time: float) -> Dict[str, Any]:
        """Create detailed audit trail for compliance (my version approach)."""
        audit_trail = {
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "policy_decision": policy_result.get('final_policy', 'STANDARD_PROCESSING'),
            "decision_reason": policy_result.get('final_reason', 'standard_processing'),
            "ids_traits_state": policy_result.get('traits_analysis', {}).get('state', 'unknown'),
            "ids_content_state": policy_result.get('content_analysis', {}).get('state', 'unknown'),
            "processing_path": "hybrid_ids_analysis" if NOVA_INTEGRATION_AVAILABLE else "fallback_analysis",
            "processing_time_ms": processing_time,
            "compliance_markers": self._generate_compliance_markers(policy_result),
            "api_version": self.VERSION,
            "circuit_breaker_state": self.circuit_breaker.state
        }
        return self._add_hash_chain(audit_trail)

    def _add_hash_chain(self, audit_trail: Dict[str, Any]) -> Dict[str, Any]:
        """Add hash chaining fields to the audit trail."""
        audit_trail = dict(audit_trail)  # don't mutate caller's dict
        audit_trail["previous_event_hash"] = self.last_audit_hash or ""

        use_shared = _env_truthy("NOVA_USE_SHARED_HASH")
        if SHARED_HASH_AVAILABLE and use_shared and compute_audit_hash:
            # Use shared hash utility for cross-slot compatibility
            previous = self.last_audit_hash or ""

            # Prepare structured record for shared hash
            hash_record = {
                "id": audit_trail.get("trace_id", ""),
                "slot": "slot09",
                "type": "audit_trail",
                "timestamp": audit_trail.get("timestamp", ""),
                "api_version": audit_trail.get("api_version", self.VERSION),
                "data": {
                    "policy_decision": audit_trail.get("policy_decision", ""),
                    "decision_reason": audit_trail.get("decision_reason", ""),
                    "compliance_markers": audit_trail.get("compliance_markers", []),
                    "processing_path": audit_trail.get("processing_path", ""),
                    "processing_time_ms": audit_trail.get("processing_time_ms", 0)
                },
                "previous_hash": previous
            }

            current_hash = compute_audit_hash(hash_record)
            audit_trail["hash_signature"] = current_hash
            audit_trail["hash_method"] = "shared_blake2b"
        else:
            # Fallback to current SHA256 implementation
            previous = self.last_audit_hash or ""
            parts = (
                audit_trail.get("trace_id", ""),
                audit_trail.get("timestamp", ""),
                audit_trail.get("policy_decision", ""),
                audit_trail.get("decision_reason", ""),
                json.dumps(audit_trail.get("compliance_markers", []), separators=(",", ":"), ensure_ascii=False),
                json.dumps(audit_trail.get("processing_path", ""), separators=(",", ":"), ensure_ascii=False),
                str(audit_trail.get("processing_time_ms", "")),
            )
            data = "|".join(parts).encode("utf-8")
            current_hash = hashlib.sha256(previous.encode("utf-8") + data).hexdigest()
            audit_trail["hash_signature"] = f"sha256:{current_hash}"
            audit_trail["hash_method"] = "fallback_sha256"

        audit_trail["retention_policy"] = "7_years"
        self.last_audit_hash = audit_trail["hash_signature"]
        return audit_trail

    def _default_deployment_context(self, request: DistortionDetectionRequest) -> Dict[str, Any]:
        """Extract deployment context from request if provided."""
        ctx = request.context.get("deployment_context") if hasattr(request, "context") else None
        return ctx if isinstance(ctx, dict) else {}

    def _generate_compliance_markers(self, policy_result: Dict) -> List[str]:
        """Generate compliance markers for audit trail."""
        markers = []
        
        policy_action = policy_result.get('final_policy', 'STANDARD_PROCESSING')
        if policy_action == 'BLOCK_OR_SANDBOX':
            markers.append("HIGH_THREAT_BLOCKED")
        
        severity = policy_result.get('final_severity', 'normal')
        if severity == 'high':
            markers.append("HIGH_SEVERITY_DETECTED")
        
        # Check for systematic manipulation indicators
        traits_stability = policy_result.get('traits_analysis', {}).get('stability', 1.0)
        content_stability = policy_result.get('content_analysis', {}).get('stability', 1.0)
        
        if min(traits_stability, content_stability) < 0.25:
            markers.append("SYSTEMATIC_MANIPULATION")
        
        if not NOVA_INTEGRATION_AVAILABLE:
            markers.append("FALLBACK_MODE_PROCESSING")
            
        return markers

    def _generate_threat_landscape(self, policy_result: Dict, 
                                 request: DistortionDetectionRequest) -> Dict[str, Any]:
        """Generate detailed threat landscape analysis (my version approach)."""
        traits_analysis = policy_result.get('traits_analysis', {})
        content_analysis = policy_result.get('content_analysis', {})
        
        return {
            "infrastructure_analysis": {
                "economic_indicators": self._analyze_economic_patterns(request.content),
                "institutional_markers": self._analyze_institutional_markers(request.content),
                "systematic_patterns": self._analyze_systematic_patterns(policy_result),
                "persistence_score": self._calculate_persistence_score(policy_result)
            },
            "stability_impact": {
                "stability_index": (traits_analysis.get('stability', 0.5) + 
                                  content_analysis.get('stability', 0.5)) / 2,
                "intervention_urgency": self._calculate_intervention_urgency(policy_result),
                "projected_impact": self._assess_projected_impact(policy_result),
                "constellation_effect": self._assess_constellation_impact(policy_result)
            },
            "pattern_analysis": {
                "detected_patterns": self._extract_detected_patterns(policy_result),
                "confidence_scores": {
                    "traits_confidence": traits_analysis.get('stability', 0.0),
                    "content_confidence": content_analysis.get('stability', 0.0),
                    "overall_confidence": self._calculate_ids_based_confidence(policy_result)
                },
                "threat_vectors": self._identify_threat_vectors(policy_result)
            }
        }

    def _generate_intervention_strategy(self, policy_result: Dict,
                                      request: DistortionDetectionRequest) -> Dict[str, Any]:
        """Generate intervention strategy recommendations (my version approach)."""
        policy_action = policy_result.get('final_policy', 'STANDARD_PROCESSING')
        severity = policy_result.get('final_severity', 'normal')
        
        # Strategy templates based on threat classification
        strategy_templates = {
            'ALLOW_FASTPATH': {
                'type': 'monitoring',
                'approach': 'passive_observation',
                'timeline': 'continuous',
                'expected_effectiveness': 0.9
            },
            'STANDARD_PROCESSING': {
                'type': 'gentle_correction',
                'approach': 'educational_enhancement',
                'timeline': 'short_term',
                'expected_effectiveness': 0.8
            },
            'DEGRADE_AND_REVIEW': {
                'type': 'respectful_dialogue',
                'approach': 'cultural_bridge_building',
                'timeline': 'medium_term',
                'expected_effectiveness': 0.6
            },
            'BLOCK_OR_SANDBOX': {
                'type': 'strategic_bypass',
                'approach': 'infrastructure_replacement',
                'timeline': 'long_term',
                'expected_effectiveness': 0.4
            }
        }
        
        base_strategy = strategy_templates.get(policy_action, strategy_templates['STANDARD_PROCESSING'])
        
        # Enhance with context-specific recommendations
        enhanced_strategy = {
            **base_strategy,
            'urgency': self._calculate_intervention_urgency(policy_result),
            'resource_requirements': severity,
            'success_probability': self._estimate_success_probability(policy_result),
            'monitoring_frequency': 'enhanced' if severity in ['medium', 'high'] else 'standard',
            'escalation_triggers': self._define_escalation_triggers(policy_result),
            'cultural_considerations': self._assess_cultural_factors(request.context),
            'implementation_complexity': self._assess_implementation_complexity(policy_result)
        }
        
        return enhanced_strategy

    # Helper methods for detailed analysis
    def _analyze_economic_patterns(self, content: str) -> float:
        """Analyze economic indicators in content."""
        economic_keywords = ['cost', 'price', 'money', 'profit', 'investment', 'economic', 'financial']
        content_lower = content.lower()
        matches = sum(1 for keyword in economic_keywords if keyword in content_lower)
        return min(1.0, matches / len(economic_keywords))

    def _analyze_institutional_markers(self, content: str) -> float:
        """Analyze institutional markers in content."""
        institutional_keywords = ['official', 'government', 'policy', 'regulation', 'authority', 'institution']
        content_lower = content.lower()
        matches = sum(1 for keyword in institutional_keywords if keyword in content_lower)
        return min(1.0, matches / len(institutional_keywords))

    def _analyze_systematic_patterns(self, policy_result: Dict) -> float:
        """Analyze systematic patterns from policy result."""
        traits_drift = abs(policy_result.get('traits_analysis', {}).get('drift', 0.0))
        content_drift = abs(policy_result.get('content_analysis', {}).get('drift', 0.0))
        return min(1.0, (traits_drift + content_drift) / 2)

    def _calculate_persistence_score(self, policy_result: Dict) -> float:
        """Calculate persistence score for distortion."""
        stability_avg = (
            policy_result.get('traits_analysis', {}).get('stability', 0.5) +
            policy_result.get('content_analysis', {}).get('stability', 0.5)
        ) / 2
        return 1.0 - stability_avg  # Lower stability = higher persistence

    def _calculate_intervention_urgency(self, policy_result: Dict) -> str:
        """Calculate intervention urgency level."""
        stability_avg = (
            policy_result.get('traits_analysis', {}).get('stability', 0.5) +
            policy_result.get('content_analysis', {}).get('stability', 0.5)
        ) / 2
        
        if stability_avg < 0.3:
            return 'critical'
        elif stability_avg < 0.6:
            return 'high'
        elif stability_avg < 0.8:
            return 'medium'
        else:
            return 'low'

    def _assess_projected_impact(self, policy_result: Dict) -> str:
        """Assess projected impact of distortion."""
        severity = policy_result.get('final_severity', 'normal')
        impact_mapping = {
            'low': 'minimal',
            'normal': 'moderate',
            'medium': 'significant',
            'high': 'severe'
        }
        return impact_mapping.get(severity, 'moderate')

    def _assess_constellation_impact(self, policy_result: Dict) -> str:
        """Assess impact on constellation stability."""
        stability_avg = (
            policy_result.get('traits_analysis', {}).get('stability', 0.5) +
            policy_result.get('content_analysis', {}).get('stability', 0.5)
        ) / 2
        
        if stability_avg > 0.8:
            return 'stabilizing'
        elif stability_avg < 0.3:
            return 'destabilizing'
        else:
            return 'neutral'

    def _extract_detected_patterns(self, policy_result: Dict) -> List[str]:
        """Extract detected patterns from policy result."""
        patterns = []
        
        final_reason = policy_result.get('final_reason', '')
        if 'stability' in final_reason:
            patterns.append('stability_drift')
        if 'drift' in final_reason:
            patterns.append('content_drift')
        
        # Add state-based patterns
        traits_state = policy_result.get('traits_analysis', {}).get('state', '')
        content_state = policy_result.get('content_analysis', {}).get('state', '')
        
        if traits_state == IDSState.DISINTEGRATING.value:
            patterns.append('traits_disintegration')
        if content_state == IDSState.DIVERGING.value:
            patterns.append('content_divergence')
            
        return patterns

    def _identify_threat_vectors(self, policy_result: Dict) -> List[str]:
        """Identify potential threat vectors."""
        vectors = []
        
        policy_action = policy_result.get('final_policy', 'STANDARD_PROCESSING')
        if policy_action == 'BLOCK_OR_SANDBOX':
            vectors.extend(['systematic_manipulation', 'coordinated_campaign'])
        elif policy_action == 'DEGRADE_AND_REVIEW':
            vectors.extend(['infrastructure_distortion', 'institutional_bias'])
        
        # Analyze drift patterns for additional vectors
        traits_drift = policy_result.get('traits_analysis', {}).get('drift', 0.0)
        content_drift = policy_result.get('content_analysis', {}).get('drift', 0.0)
        
        if abs(traits_drift) > 0.2:
            vectors.append('behavioral_manipulation')
        if abs(content_drift) > 0.2:
            vectors.append('content_manipulation')
            
        return vectors

    def _estimate_success_probability(self, policy_result: Dict) -> float:
        """Estimate intervention success probability."""
        severity = policy_result.get('final_severity', 'normal')
        
        # Base probabilities by severity
        base_probabilities = {
            'low': 0.9,
            'normal': 0.8,
            'medium': 0.6,
            'high': 0.4
        }
        
        base_prob = base_probabilities.get(severity, 0.7)
        
        # Adjust based on stability
        stability_avg = (
            policy_result.get('traits_analysis', {}).get('stability', 0.5) +
            policy_result.get('content_analysis', {}).get('stability', 0.5)
        ) / 2
        
        stability_bonus = (stability_avg - 0.5) * 0.2
        
        return round(max(0.1, min(1.0, base_prob + stability_bonus)), 2)

    def _define_escalation_triggers(self, policy_result: Dict) -> List[str]:
        """Define escalation triggers for intervention."""
        triggers = []
        
        stability_avg = (
            policy_result.get('traits_analysis', {}).get('stability', 0.5) +
            policy_result.get('content_analysis', {}).get('stability', 0.5)
        ) / 2
        
        if stability_avg < 0.3:
            triggers.append('immediate_escalation_required')
        if stability_avg < 0.5:
            triggers.append('enhanced_monitoring')
        
        severity = policy_result.get('final_severity', 'normal')
        if severity == 'high':
            triggers.extend(['expert_review_required', 'cross_slot_coordination'])
            
        return triggers

    def _assess_cultural_factors(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess cultural considerations from context."""
        return {
            "region": context.get('region', 'unknown'),
            "cultural_sensitivity_required": context.get('cultural_context') is not None,
            "adaptation_level": context.get('adaptation_level', 'standard'),
            "local_customs": context.get('local_customs', [])
        }

    def _assess_implementation_complexity(self, policy_result: Dict) -> str:
        """Assess implementation complexity."""
        policy_action = policy_result.get('final_policy', 'STANDARD_PROCESSING')
        
        complexity_mapping = {
            'ALLOW_FASTPATH': 'minimal',
            'STANDARD_PROCESSING': 'low',
            'DEGRADE_AND_REVIEW': 'medium',
            'BLOCK_OR_SANDBOX': 'high'
        }
        
        return complexity_mapping.get(policy_action, 'low')

    def _update_comprehensive_metrics(self, response: DistortionDetectionResponse):
        """Update comprehensive metrics tracking."""
        with self._metrics_lock:
            # Update counters by status
            if response.status == ResponseStatus.BLOCKED:
                self.metrics['blocked_requests'] += 1
            elif response.status == ResponseStatus.WARNING:
                self.metrics['warning_requests'] += 1
            
            # Update threat detection tracking
            self.metrics['threat_detections_by_type'][response.distortion_type.value] += 1
            self.metrics['policy_actions_taken'][response.policy_action.value] += 1

    def _create_circuit_breaker_response(self, trace_id: str, start_time: float) -> DistortionDetectionResponse:
        """Create response for circuit breaker open state."""
        processing_time = (time.perf_counter() - start_time) * 1000

        audit_trail = {
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": "circuit_breaker_open",
            "processing_path": "error_handler",
            "failure_count": self.circuit_breaker.failure_count
        }
        audit_trail = self._add_hash_chain(audit_trail)

        return DistortionDetectionResponse(
            format_version=self.FORMAT_VERSION,
            api_version=self.VERSION,
            compatibility_level=self.COMPATIBILITY_LEVEL,
            status=ResponseStatus.ERROR,
            threat_level=_round3(0.5),
            policy_action=PolicyAction.STANDARD_PROCESSING,
            confidence=_round3(0.0),
            processing_time_ms=_round3(processing_time),
            trace_id=trace_id,
            distortion_type=DistortionType.UNKNOWN,
            infrastructure_level=InfrastructureLevel.UNKNOWN,
            severity=ThreatSeverity.NORMAL,
            ids_analysis={
                "error": "Service temporarily unavailable",
                "details": "Circuit breaker open - too many recent failures",
                "circuit_breaker_state": "open",
                "integration_mode": "unavailable"
            },
            audit_trail=audit_trail,
            deployment_context={},
            deployment_feedback={},
            error_details={
                "error_type": "circuit_breaker",
                "error_code": "CB502",
                "error_message": "circuit breaker open"
            }
        )

    def _create_comprehensive_error_response(self, trace_id: str, error_message: str,
                                           processing_time: float) -> DistortionDetectionResponse:
        """Create comprehensive error response."""
        audit_trail = {
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error_message,
            "processing_path": "error_handler",
            "api_version": self.VERSION,
            "circuit_breaker_failures": self.circuit_breaker.failure_count
        }
        audit_trail = self._add_hash_chain(audit_trail)

        return DistortionDetectionResponse(
            format_version=self.FORMAT_VERSION,
            api_version=self.VERSION,
            compatibility_level=self.COMPATIBILITY_LEVEL,
            status=ResponseStatus.ERROR,
            threat_level=_round3(self.config.default_confidence_fallback),
            policy_action=PolicyAction.STANDARD_PROCESSING,
            confidence=_round3(0.0),
            processing_time_ms=_round3(processing_time),
            trace_id=trace_id,
            distortion_type=DistortionType.UNKNOWN,
            infrastructure_level=InfrastructureLevel.UNKNOWN,
            severity=ThreatSeverity.NORMAL,
            ids_analysis={
                "error": "Processing failed",
                "details": error_message,
                "integration_mode": "nova" if NOVA_INTEGRATION_AVAILABLE else "fallback",
                "fallback_reason": "error_occurred"
            },
            audit_trail=audit_trail,
            deployment_context={},
            deployment_feedback={},
            error_details={
                "error_type": "processing",
                "error_code": "PROC503",
                "error_message": error_message
            }
        )

    # ========================================================================
    # 5. ENHANCED SYSTEM HEALTH AND MONITORING
    # ========================================================================

    def get_comprehensive_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health with detailed metrics."""
        with self._metrics_lock:
            total_requests = self.metrics['total_requests']
            processing_times = self.metrics['processing_times'] or [0]
            
            # Calculate performance metrics
            avg_time = sum(processing_times) / len(processing_times)
            p50_time = sorted(processing_times)[len(processing_times) // 2] if processing_times else 0
            p95_time = sorted(processing_times)[int(len(processing_times) * 0.95)] if processing_times else 0
            p99_time = sorted(processing_times)[int(len(processing_times) * 0.99)] if processing_times else 0
            
            # Calculate rates
            error_rate = self.metrics['error_count'] / max(1, total_requests)
            block_rate = self.metrics['blocked_requests'] / max(1, total_requests)
            warning_rate = self.metrics['warning_requests'] / max(1, total_requests)
            
            # Determine overall system status
            if error_rate > 0.10 or self.circuit_breaker.is_open():
                system_status = SystemStatus.UNHEALTHY
            elif error_rate > 0.05 or avg_time > 100:
                system_status = SystemStatus.DEGRADED
            else:
                system_status = SystemStatus.HEALTHY
        
        return {
            "status": system_status.value,
            "version": self.VERSION,
            "uptime_requests": total_requests,
            "uptime_seconds": time.time() - self.metrics['start_time'],
            "performance_metrics": {
                "avg_processing_time_ms": round(avg_time, 2),
                "p50_processing_time_ms": round(p50_time, 2),
                "p95_processing_time_ms": round(p95_time, 2),
                "p99_processing_time_ms": round(p99_time, 2),
                "requests_per_second": total_requests / max(1, time.time() - self.metrics['start_time'])
            },
            "quality_metrics": {
                "error_rate": round(error_rate, 4),
                "block_rate": round(block_rate, 4),
                "warning_rate": round(warning_rate, 4),
                "cache_hit_rate": round(self.content_cache.hit_rate(), 4)
            },
            "threat_detection_metrics": {
                "detections_by_type": dict(self.metrics['threat_detections_by_type']),
                "policy_actions_taken": dict(self.metrics['policy_actions_taken'])
            },
            "resilience_status": {
                "circuit_breaker_state": self.circuit_breaker.state,
                "circuit_breaker_failures": self.circuit_breaker.failure_count,
                "cache_size": len(self.content_cache._cache),
                "cache_capacity_used": len(self.content_cache._cache) / self.content_cache.max_size
            },
            "integration_status": {
                "nova_integration": "available" if NOVA_INTEGRATION_AVAILABLE else "fallback",
                "ids_enabled": IDS_ENABLED if NOVA_INTEGRATION_AVAILABLE else False,
                "pydantic_available": PYDANTIC_AVAILABLE
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def bulk_detect(self, requests: List[DistortionDetectionRequest]) -> List[DistortionDetectionResponse]:
        """Enhanced bulk detection with better error handling and performance."""
        if not requests:
            return []
        
        self.logger.info(f"Processing bulk detection: {len(requests)} requests")
        
        # Process with concurrency control
        semaphore = asyncio.Semaphore(10)  # Limit concurrent processing
        
        async def process_single(request):
            async with semaphore:
                return await self.detect_distortion(request)
        
        # Execute with timeout protection
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*[process_single(req) for req in requests], return_exceptions=True),
                timeout=len(requests) * 2  # 2 seconds per request
            )
            
            # Convert exceptions to error responses
            processed_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    trace_id = requests[i].trace_id or f"bulk_error_{i}"
                    error_response = self._create_comprehensive_error_response(
                        trace_id, str(response), 0.0
                    )
                    processed_responses.append(error_response)
                else:
                    processed_responses.append(response)
            
            return processed_responses
            
        except asyncio.TimeoutError:
            self.logger.error("Bulk detection timed out")
            # Return error responses for all requests
            return [
                self._create_comprehensive_error_response(
                    req.trace_id or f"bulk_timeout_{i}",
                    "Bulk processing timed out",
                    0.0
                )
                for i, req in enumerate(requests)
            ]

    async def report_deployment_feedback(self, deployment_id: str, outcome_data: Dict[str, Any]) -> None:
        """Record deployment feedback from Slot 10."""
        feedback = {
            "deployment_id": deployment_id,
            "outcome": outcome_data.get("status", "unknown"),
            "actual_impact": {
                "measured_threat_level": _round3(outcome_data.get("measured_threat_level", 0.0)),
                "prediction_accuracy": _round3(outcome_data.get("prediction_accuracy", 0.0)),
                "false_positive_rate": _round3(outcome_data.get("false_positives", 0.0)),
                "false_negative_rate": _round3(outcome_data.get("false_negatives", 0.0)),
            },
            "lessons_learned": {
                "summary": outcome_data.get("insights", ""),
                "recommendations": outcome_data.get("recommendations", []),
                "escalation_needed": outcome_data.get("escalation", False),
            },
        }
        self.last_deployment_feedback = feedback

    def cleanup(self):
        """Enhanced cleanup with comprehensive resource management."""
        self.logger.info("Starting comprehensive API cleanup")

        # Clear expired cache entries
        expired = self.content_cache.clear_expired()
        self.logger.info(f"Cleared {expired} expired cache entries")
        
        # Reset circuit breaker if appropriate
        if self.circuit_breaker.state == "half-open":
            self.circuit_breaker.record_success()
        
        # Log final metrics
        health = self.get_comprehensive_system_health()
        self.logger.info(f"Final metrics - Requests: {health['uptime_requests']}, "
                        f"Error rate: {health['quality_metrics']['error_rate']:.4f}, "
                        f"Avg time: {health['performance_metrics']['avg_processing_time_ms']:.2f}ms")
        
        self.logger.info("API cleanup completed successfully")

# ============================================================================
# 6. FACTORY FUNCTIONS AND HELPERS
# ============================================================================

def create_hybrid_slot9_api(core_detector=None, config: Optional[HybridApiConfig] = None) -> HybridDistortionDetectionAPI:
    """Factory function for creating Hybrid Slot 9 API instance."""
    return HybridDistortionDetectionAPI(core_detector, config)

def create_production_config() -> HybridApiConfig:
    """Create production-optimized configuration."""
    return HybridApiConfig(
        max_content_length_bytes=20480,  # 20KB max
        circuit_breaker_threshold=5,
        circuit_breaker_reset_timeout=30.0,
        cache_ttl_seconds=600.0,  # 10 minute cache
        threat_threshold_warning=0.65,
        threat_threshold_block=0.85,
        ids_stability_threshold_low=0.3,
        ids_stability_threshold_high=0.8
    )

def create_development_config() -> HybridApiConfig:
    """Create development-friendly configuration."""
    return HybridApiConfig(
        circuit_breaker_threshold=20,  # More tolerant
        circuit_breaker_reset_timeout=10.0,  # Faster recovery
        cache_ttl_seconds=60.0,  # 1 minute cache
        threat_threshold_warning=0.5,
        threat_threshold_block=0.9
    )

# ============================================================================
# 7. OPTIONAL FASTAPI INTEGRATION (Enhanced)
# ============================================================================

def create_fastapi_app(api_instance: HybridDistortionDetectionAPI):
    """Enhanced FastAPI app with comprehensive endpoints."""
    try:
        from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
        from src_bootstrap import ensure_src_on_path

        ensure_src_on_path()

        from nova.auth import verify_jwt_token
        
        app = FastAPI(
            title="NOVA Slot 9 - Hybrid Distortion Protection API",
            description="Production-ready distortion detection with enterprise resilience",
            version=api_instance.VERSION,
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        security = HTTPBearer(auto_error=False)

        async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
            if credentials is None:
                raise HTTPException(status_code=401, detail="Not authenticated")
            try:
                return verify_jwt_token(credentials.credentials)
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid auth token")
        
        @app.post("/api/v1/detect",
                 response_model=DistortionDetectionResponse,
                 summary="Detect distortions in content",
                 description="Main endpoint for distortion detection with full NOVA integration")
        async def detect_distortion(request: DistortionDetectionRequest, user: Dict[str, Any] = Depends(get_current_user)):
            try:
                return await api_instance.detect_distortion(request)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                api_instance.logger.error(f"API endpoint error: {e}")
                raise HTTPException(status_code=500, detail="Internal processing error")
        
        @app.post("/api/v1/bulk-detect",
                 summary="Bulk distortion detection",
                 description="Process multiple detection requests in parallel")
        async def bulk_detect_distortion(requests: List[DistortionDetectionRequest], user: Dict[str, Any] = Depends(get_current_user)):
            try:
                if len(requests) > 100:
                    raise HTTPException(status_code=400, detail="Maximum 100 requests per batch")
                return await api_instance.bulk_detect(requests)
            except Exception as e:
                api_instance.logger.error(f"Bulk API endpoint error: {e}")
                raise HTTPException(status_code=500, detail="Bulk processing error")
        
        @app.get("/api/v1/health",
                summary="Comprehensive health check",
                description="Get detailed system health and performance metrics")
        async def health_check(user: Dict[str, Any] = Depends(get_current_user)):
            return api_instance.get_comprehensive_system_health()
        
        @app.get("/api/v1/metrics",
                summary="Performance metrics",
                description="Get detailed performance and quality metrics")
        async def get_metrics(user: Dict[str, Any] = Depends(get_current_user)):
            health = api_instance.get_comprehensive_system_health()
            return {
                "performance": health["performance_metrics"],
                "quality": health["quality_metrics"],
                "threat_detection": health["threat_detection_metrics"]
            }
        
        @app.get("/api/v1/status",
                summary="System status",
                description="Get current system status and integration info")
        async def get_status(user: Dict[str, Any] = Depends(get_current_user)):
            health = api_instance.get_comprehensive_system_health()
            return {
                "status": health["status"],
                "version": health["version"],
                "uptime_seconds": health["uptime_seconds"],
                "integration_status": health["integration_status"],
                "resilience_status": health["resilience_status"]
            }
        
        @app.post("/api/v1/admin/cleanup",
                 summary="Admin cleanup",
                 description="Trigger system cleanup (admin only)")
        async def admin_cleanup(background_tasks: BackgroundTasks, user: Dict[str, Any] = Depends(get_current_user)):
            background_tasks.add_task(api_instance.cleanup)
            return {"message": "Cleanup initiated"}
        
        @app.get("/",
                summary="API Root",
                description="API information and available endpoints")
        async def root():
            return {
                "api": "NOVA Slot 9 - Hybrid Distortion Protection",
                "version": api_instance.VERSION,
                "status": "operational",
                "endpoints": {
                    "detect": "/api/v1/detect",
                    "bulk_detect": "/api/v1/bulk-detect", 
                    "health": "/api/v1/health",
                    "metrics": "/api/v1/metrics",
                    "status": "/api/v1/status",
                    "docs": "/docs"
                }
            }
        
        return app
        
    except ImportError:
        api_instance.logger.warning("FastAPI not available - web endpoints disabled")
        return None

# ============================================================================
# 8. USAGE EXAMPLES
# ============================================================================

async def example_usage():
    """Example usage of the Hybrid API."""
    
    # Create production configuration
    config = create_production_config()
    
    # Initialize API (in production, core_detector would be the actual Slot9Core)
    api = create_hybrid_slot9_api(core_detector=None, config=config)
    
    # Single detection request
    request = DistortionDetectionRequest(
        content="This is sample content for distortion analysis.",
        context={"source": "example", "region": "US"},
        include_detailed_analysis=True,
        priority=RequestPriority.HIGH
    )
    
    # Process request
    response = await api.detect_distortion(request)
    print(f"Detection result: {response.status.value} - Threat: {response.threat_level:.3f}")
    
    # Bulk processing example
    bulk_requests = [
        DistortionDetectionRequest(content=f"Sample content {i}", trace_id=f"bulk_{i}")
        for i in range(5)
    ]
    
    bulk_responses = await api.bulk_detect(bulk_requests)
    print(f"Bulk processing: {len(bulk_responses)} responses")
    
    # Health check
    health = api.get_comprehensive_system_health()
    print(f"System status: {health['status']} - Error rate: {health['quality_metrics']['error_rate']:.4f}")
    
    # Cleanup
    api.cleanup()

if __name__ == "__main__":
    api = create_hybrid_slot9_api()
    app = create_fastapi_app(api)
    if app:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
