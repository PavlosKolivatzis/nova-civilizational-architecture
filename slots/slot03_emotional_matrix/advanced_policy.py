"""Advanced Safety Policy for Slot 3 - Emotional Matrix Safety System."""
import logging
import time
import re
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque


@dataclass
class SafetyViolation:
    """Represents a safety policy violation."""
    violation_type: str
    content: str
    confidence: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class RateLimiter:
    """Simple rate limiter for content analysis."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed within rate limits."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        request_times = self.requests[identifier]
        while request_times and request_times[0] < window_start:
            request_times.popleft()
        
        # Check if within limits
        if len(request_times) >= self.max_requests:
            return False
        
        # Add current request
        request_times.append(now)
        return True


class AdvancedSafetyPolicy:
    """
    Advanced safety policy with harmful content detection,
    rate limiting, and comprehensive validation.
    
    Extends basic safety validation with sophisticated
    content analysis and policy enforcement.
    """
    
    def __init__(self, 
                 rate_limit_requests: int = 100,
                 rate_limit_window: int = 60,
                 enable_content_filtering: bool = True):
        self.logger = logging.getLogger(__name__)
        self.rate_limiter = RateLimiter(rate_limit_requests, rate_limit_window)
        self.enable_content_filtering = enable_content_filtering
        
        # Harmful content patterns
        self._harmful_patterns = self._load_harmful_patterns()
        self._blocked_domains = self._load_blocked_domains()
        self._violation_history: List[SafetyViolation] = []
        
        # Policy statistics
        self.stats = {
            "total_checks": 0,
            "violations_detected": 0,
            "rate_limit_hits": 0,
            "content_filtered": 0
        }

    def _load_harmful_patterns(self) -> List[Dict[str, Any]]:
        """Load patterns for harmful content detection."""
        return [
            {
                "name": "hate_speech",
                "patterns": [
                    r'\b(?:hate|despise|loathe)\s+(?:all|every)\s+\w+',
                    r'\b(?:kill|destroy|eliminate)\s+(?:all|every)\s+\w+',
                ],
                "severity": "high"
            },
            {
                "name": "violence_incitement",
                "patterns": [
                    r'\b(?:attack|assault|harm|hurt|kill)\s+(?:him|her|them|everyone)',
                    r'\blet\'s\s+(?:attack|fight|destroy)',
                ],
                "severity": "critical"
            },
            {
                "name": "harassment",
                "patterns": [
                    r'\b(?:stupid|idiot|moron|worthless)\s+(?:person|people|human)',
                    r'\byou\s+(?:should|must|need to)\s+(?:die|disappear|leave)',
                ],
                "severity": "medium"
            },
            {
                "name": "self_harm",
                "patterns": [
                    r'\bi\s+(?:want to|will|should)\s+(?:kill myself|end it all|die)',
                    r'\b(?:suicide|self-harm|cutting)\s+(?:is|seems)\s+(?:good|right|appealing)',
                ],
                "severity": "critical"
            },
            {
                "name": "misinformation",
                "patterns": [
                    r'\b(?:proven|scientific|fact):\s+(?:vaccines|medicine)\s+(?:cause|create)\s+(?:autism|cancer)',
                    r'\b(?:earth|planet)\s+is\s+(?:flat|hollow|fake)',
                ],
                "severity": "medium"
            }
        ]

    def _load_blocked_domains(self) -> Set[str]:
        """Load list of blocked domains/sources."""
        return {
            "malicious-site.com",
            "fake-news-source.net",
            "spam-domain.org"
        }

    def validate(self, analysis_result: Dict[str, Any], 
                 content: str = "", 
                 user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Advanced validation with comprehensive safety checks.
        
        Args:
            analysis_result: Emotional analysis result
            content: Original content being analyzed
            user_id: User identifier for rate limiting
            
        Returns:
            Validation result with safety status and violations
        """
        self.stats["total_checks"] += 1
        
        validation_result = {
            "is_safe": True,
            "violations": [],
            "filtered_content": content,
            "policy_actions": [],
            "rate_limited": False
        }
        
        # Rate limiting check
        if user_id and not self.rate_limiter.is_allowed(user_id):
            validation_result["is_safe"] = False
            validation_result["rate_limited"] = True
            validation_result["policy_actions"].append("rate_limit_exceeded")
            self.stats["rate_limit_hits"] += 1
            self.logger.warning("Rate limit exceeded for user: %s", user_id)
            return validation_result
        
        # Basic safety checks from parent class equivalent
        basic_result = self._basic_safety_check(analysis_result)
        if not basic_result["is_safe"]:
            validation_result.update(basic_result)
        
        # Advanced content filtering
        if self.enable_content_filtering and content:
            content_result = self._check_harmful_content(content)
            if content_result["violations"]:
                validation_result["is_safe"] = False
                validation_result["violations"].extend(content_result["violations"])
                validation_result["filtered_content"] = content_result["filtered_content"]
                validation_result["policy_actions"].extend(content_result["actions"])
                self.stats["content_filtered"] += 1
        
        # Domain/source validation
        source_result = self._check_content_source(content)
        if source_result["violations"]:
            validation_result["violations"].extend(source_result["violations"])
            validation_result["policy_actions"].extend(source_result["actions"])
        
        # Track violations
        if validation_result["violations"]:
            self.stats["violations_detected"] += 1
            for violation in validation_result["violations"]:
                self._violation_history.append(SafetyViolation(
                    violation_type=violation["type"],
                    content=content[:100] + "..." if len(content) > 100 else content,
                    confidence=violation["confidence"],
                    timestamp=time.time(),
                    metadata={"user_id": user_id}
                ))
        
        return validation_result

    def _basic_safety_check(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Basic safety validation equivalent to original safety_policy.py."""
        result = {
            "is_safe": True,
            "violations": [],
            "policy_actions": []
        }
        
        # Score bounds checking
        score = analysis_result.get('score', 0.0)
        if not (-1.0 <= score <= 1.0):
            result["is_safe"] = False
            result["violations"].append({
                "type": "score_out_of_bounds",
                "confidence": 1.0,
                "details": f"Score {score} outside valid range [-1.0, 1.0]"
            })
            result["policy_actions"].append("clamp_score")
            # Clamp the score
            analysis_result['score'] = max(-1.0, min(1.0, score))
        
        # Tone validation
        valid_tones = {'joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust', 'neutral'}
        tone = analysis_result.get('emotional_tone', 'neutral')
        if tone not in valid_tones:
            result["violations"].append({
                "type": "invalid_tone",
                "confidence": 0.8,
                "details": f"Tone '{tone}' not in valid set: {valid_tones}"
            })
            result["policy_actions"].append("default_tone")
            analysis_result['emotional_tone'] = 'neutral'
        
        # Confidence bounds
        confidence = analysis_result.get('confidence', 0.0)
        if not (0.0 <= confidence <= 1.0):
            result["violations"].append({
                "type": "confidence_out_of_bounds", 
                "confidence": 1.0,
                "details": f"Confidence {confidence} outside valid range [0.0, 1.0]"
            })
            result["policy_actions"].append("clamp_confidence")
            analysis_result['confidence'] = max(0.0, min(1.0, confidence))
        
        return result

    def _check_harmful_content(self, content: str) -> Dict[str, Any]:
        """Check content against harmful patterns."""
        result = {
            "violations": [],
            "filtered_content": content,
            "actions": []
        }
        
        content_lower = content.lower()
        filtered_content = content
        
        for pattern_group in self._harmful_patterns:
            for pattern in pattern_group["patterns"]:
                matches = re.finditer(pattern, content_lower, re.IGNORECASE)
                for match in matches:
                    violation = {
                        "type": f"harmful_content_{pattern_group['name']}",
                        "confidence": 0.9,
                        "details": f"Detected {pattern_group['name']} pattern",
                        "severity": pattern_group["severity"],
                        "matched_text": match.group(0)
                    }
                    result["violations"].append(violation)
                    
                    # Filter the content
                    filtered_content = filtered_content[:match.start()] + "[FILTERED]" + filtered_content[match.end():]
                    result["actions"].append(f"filter_{pattern_group['name']}")
        
        result["filtered_content"] = filtered_content
        return result

    def _check_content_source(self, content: str) -> Dict[str, Any]:
        """Check if content contains references to blocked sources."""
        result = {
            "violations": [],
            "actions": []
        }
        
        # Simple URL detection and domain checking
        url_pattern = r'https?://(?:www\.)?([^/\s]+)'
        urls = re.findall(url_pattern, content.lower())
        
        for domain in urls:
            if domain in self._blocked_domains:
                result["violations"].append({
                    "type": "blocked_source",
                    "confidence": 1.0,
                    "details": f"Content references blocked domain: {domain}",
                    "domain": domain
                })
                result["actions"].append("block_domain_reference")
        
        return result

    def get_policy_stats(self) -> Dict[str, Any]:
        """Get comprehensive policy enforcement statistics."""
        recent_violations = [v for v in self._violation_history if time.time() - v.timestamp < 3600]  # Last hour
        
        violation_types = defaultdict(int)
        for violation in recent_violations:
            violation_types[violation.violation_type] += 1
        
        return {
            "total_checks": self.stats["total_checks"],
            "violations_detected": self.stats["violations_detected"],
            "rate_limit_hits": self.stats["rate_limit_hits"], 
            "content_filtered": self.stats["content_filtered"],
            "recent_violations": len(recent_violations),
            "violation_types": dict(violation_types),
            "violation_rate": self.stats["violations_detected"] / max(1, self.stats["total_checks"]),
            "safety_effectiveness": 1.0 - (self.stats["violations_detected"] / max(1, self.stats["total_checks"]))
        }

    def update_harmful_patterns(self, new_patterns: List[Dict[str, Any]]):
        """Update harmful content patterns (for dynamic policy updates)."""
        self._harmful_patterns.extend(new_patterns)
        self.logger.info("Added %d new harmful content patterns", len(new_patterns))

    def get_recent_violations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent safety violations for analysis."""
        recent = sorted(self._violation_history, key=lambda x: x.timestamp, reverse=True)[:limit]
        return [
            {
                "type": v.violation_type,
                "timestamp": v.timestamp,
                "confidence": v.confidence,
                "content_preview": v.content,
                "metadata": v.metadata
            }
            for v in recent
        ]