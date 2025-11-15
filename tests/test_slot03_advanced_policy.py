"""Comprehensive test suite for Slot 3 advanced safety policy."""
import time

from nova.slots.slot03_emotional_matrix.advanced_policy import (
    AdvancedSafetyPolicy, RateLimiter, SafetyViolation
)


class TestRateLimiter:
    """Test suite for RateLimiter."""

    def test_rate_limiter_allows_requests_within_limit(self):
        """Test that rate limiter allows requests within the limit."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True

    def test_rate_limiter_blocks_requests_over_limit(self):
        """Test that rate limiter blocks requests over the limit."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False

    def test_rate_limiter_window_expiry(self):
        """Test that rate limiter window expires correctly."""
        limiter = RateLimiter(max_requests=1, window_seconds=1)

        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False

        # Wait for window to expire
        time.sleep(1.1)
        assert limiter.is_allowed("user1") is True

    def test_rate_limiter_different_users(self):
        """Test that rate limiter tracks different users separately."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user2") is True
        assert limiter.is_allowed("user1") is False
        assert limiter.is_allowed("user2") is False


class TestAdvancedSafetyPolicy:
    """Test suite for AdvancedSafetyPolicy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.policy = AdvancedSafetyPolicy(
            rate_limit_requests=5,
            rate_limit_window=60,
            enable_content_filtering=True
        )

    def test_basic_safety_validation(self):
        """Test basic safety validation functionality."""
        # Valid analysis
        valid_analysis = {
            'score': 0.5,
            'emotional_tone': 'joy',
            'confidence': 0.8
        }

        result = self.policy.validate(valid_analysis, "happy content")
        assert result['is_safe'] is True
        assert len(result['violations']) == 0

    def test_score_bounds_validation(self):
        """Test score bounds checking."""
        # Score too high
        invalid_analysis = {
            'score': 1.5,
            'emotional_tone': 'joy',
            'confidence': 0.8
        }

        result = self.policy.validate(invalid_analysis, "content")
        assert result['is_safe'] is False
        violation_types = [v['type'] for v in result['violations']]
        assert 'score_out_of_bounds' in violation_types

    def test_invalid_tone_validation(self):
        """Test invalid emotional tone validation."""
        invalid_analysis = {
            'score': 0.5,
            'emotional_tone': 'invalid_tone',
            'confidence': 0.8
        }

        result = self.policy.validate(invalid_analysis, "content")
        violation_types = [v['type'] for v in result['violations']]
        assert 'invalid_tone' in violation_types

    def test_harmful_content_detection(self):
        """Test harmful content pattern detection."""
        harmful_contents = [
            "I hate all humans and want to kill everyone",
            "Let's attack and destroy them all",
            "You should die and disappear forever"
        ]

        analysis = {
            'score': -0.8,
            'emotional_tone': 'anger',
            'confidence': 0.9
        }

        for content in harmful_contents:
            result = self.policy.validate(analysis, content)
            assert result['is_safe'] is False
            assert len(result['violations']) > 0

            # Check that content was filtered
            assert "[FILTERED]" in result['filtered_content']

    def test_blocked_domain_detection(self):
        """Test blocked domain detection."""
        content = "Check out this link: https://malicious-site.com/bad-stuff"
        analysis = {'score': 0.0, 'emotional_tone': 'neutral', 'confidence': 0.5}

        result = self.policy.validate(analysis, content)
        violation_types = [v['type'] for v in result['violations']]
        assert 'blocked_source' in violation_types

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        analysis = {'score': 0.0, 'emotional_tone': 'neutral', 'confidence': 0.5}
        user_id = "test_user"

        # First few requests should succeed
        for i in range(5):
            result = self.policy.validate(analysis, f"content {i}", user_id)
            assert result['rate_limited'] is False

        # Next request should be rate limited
        result = self.policy.validate(analysis, "content overflow", user_id)
        assert result['rate_limited'] is True
        assert result['is_safe'] is False

    def test_policy_statistics(self):
        """Test policy statistics collection."""
        analysis = {'score': 0.0, 'emotional_tone': 'neutral', 'confidence': 0.5}

        # Perform several validations
        self.policy.validate(analysis, "normal content")
        self.policy.validate(analysis, "I hate all humans", "user1")  # Should trigger violation
        self.policy.validate(analysis, "more content", "user2")

        stats = self.policy.get_policy_stats()

        assert stats['total_checks'] >= 3
        assert stats['violations_detected'] >= 1
        assert stats['content_filtered'] >= 1
        assert 0 <= stats['violation_rate'] <= 1

    def test_harmful_pattern_updates(self):
        """Test dynamic harmful pattern updates."""
        new_patterns = [
            {
                "name": "custom_threat",
                "patterns": [r"\bcustom_bad_word\b"],
                "severity": "high"
            }
        ]

        self.policy.update_harmful_patterns(new_patterns)

        analysis = {'score': -0.5, 'emotional_tone': 'anger', 'confidence': 0.7}
        result = self.policy.validate(analysis, "This contains custom_bad_word")

        violation_types = [v['type'] for v in result['violations']]
        assert 'harmful_content_custom_threat' in violation_types

    def test_recent_violations_tracking(self):
        """Test recent violations tracking."""
        analysis = {'score': -0.8, 'emotional_tone': 'anger', 'confidence': 0.9}

        # Generate some violations
        harmful_content = "I want to kill everyone"
        self.policy.validate(analysis, harmful_content, "user1")

        violations = self.policy.get_recent_violations(limit=5)
        assert len(violations) >= 1
        assert violations[0]['content_preview'] == harmful_content[:100] + "..."

    def test_content_filtering_disabled(self):
        """Test behavior when content filtering is disabled."""
        policy_no_filter = AdvancedSafetyPolicy(enable_content_filtering=False)

        analysis = {'score': -0.8, 'emotional_tone': 'anger', 'confidence': 0.9}
        harmful_content = "I hate all humans"

        result = policy_no_filter.validate(analysis, harmful_content)

        # Should not detect harmful content violations
        violation_types = [v['type'] for v in result['violations']]
        harmful_violations = [v for v in violation_types if v.startswith('harmful_content_')]
        assert len(harmful_violations) == 0

    def test_confidence_bounds_validation(self):
        """Test confidence bounds checking."""
        invalid_analysis = {
            'score': 0.5,
            'emotional_tone': 'joy',
            'confidence': 1.5  # Invalid confidence
        }

        result = self.policy.validate(invalid_analysis, "content")
        violation_types = [v['type'] for v in result['violations']]
        assert 'confidence_out_of_bounds' in violation_types

    def test_multiple_violations(self):
        """Test handling of multiple simultaneous violations."""
        invalid_analysis = {
            'score': 2.0,  # Invalid score
            'emotional_tone': 'invalid_tone',  # Invalid tone
            'confidence': 1.5  # Invalid confidence
        }

        harmful_content = "I hate everyone and want to kill them all"

        result = self.policy.validate(invalid_analysis, harmful_content)

        assert result['is_safe'] is False
        assert len(result['violations']) >= 3  # At least score, tone, and harmful content


class TestSafetyViolation:
    """Test suite for SafetyViolation dataclass."""

    def test_safety_violation_creation(self):
        """Test SafetyViolation creation."""
        violation = SafetyViolation(
            violation_type="test_violation",
            content="test content",
            confidence=0.95,
            timestamp=time.time()
        )

        assert violation.violation_type == "test_violation"
        assert violation.content == "test content"
        assert violation.confidence == 0.95
        assert isinstance(violation.metadata, dict)

    def test_safety_violation_with_metadata(self):
        """Test SafetyViolation with custom metadata."""
        metadata = {"user_id": "test_user", "source": "api"}
        violation = SafetyViolation(
            violation_type="custom_violation",
            content="content",
            confidence=0.8,
            timestamp=time.time(),
            metadata=metadata
        )

        assert violation.metadata == metadata
