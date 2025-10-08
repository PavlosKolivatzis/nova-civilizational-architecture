#!/usr/bin/env python3
"""
Semantic Mirror Quick Regression Assertions

Fast, stdlib-only sentinel tests to verify core Semantic Mirror behavior.
Returns exit code 0 if all checks pass, 1 if any fail.

Usage:
    python scripts/semantic_mirror_quick_asserts.py
"""

import sys
import time
import uuid


def safe_import():
    """Import semantic mirror with error handling."""
    try:
        from orchestrator.semantic_mirror import SemanticMirror, ContextScope
        return SemanticMirror, ContextScope
    except ImportError as e:
        print(f"FAIL: Import error - {e}")
        return None, None


def assert_deny_by_default():
    """Test that INTERNAL contexts are deny-by-default for unknown slots."""
    SemanticMirror, ContextScope = safe_import()
    if not SemanticMirror:
        return False
    
    try:
        mirror = SemanticMirror()
        
        # Use random key to avoid ACL conflicts
        random_key = f"slot99.test_{uuid.uuid4().hex[:8]}"
        
        # Publish INTERNAL context
        mirror.publish_context(
            random_key,
            {"test": "data"},
            "slot99_test_publisher",
            ContextScope.INTERNAL,
            ttl_seconds=60.0
        )
        
        # Try to read from unknown slot (should be denied)
        result = mirror.get_context(random_key, "slot88_unknown_reader")
        
        if result is None:
            print("OK: deny-by-default")
            return True
        else:
            print(f"FAIL: deny-by-default - got {result}, expected None")
            return False
            
    except Exception as e:
        print(f"FAIL: deny-by-default - exception {e}")
        return False


def assert_ttl_expiry():
    """Test that contexts expire based on TTL and metrics are updated."""
    SemanticMirror, ContextScope = safe_import()
    if not SemanticMirror:
        return False
    
    try:
        mirror = SemanticMirror()
        
        # Get initial expired count
        initial_metrics = mirror.get_metrics()
        initial_expired = initial_metrics.get("queries_expired", 0)
        
        # Publish with very short TTL
        test_key = f"slot07.ttl_test_{uuid.uuid4().hex[:8]}"
        mirror.publish_context(
            test_key,
            {"test": "expiry"},
            "slot07_production_controls",
            ContextScope.INTERNAL,
            ttl_seconds=0.05  # 50ms
        )
        
        # Add ACL for this test
        mirror.add_access_rules({test_key: ["slot06_cultural_synthesis"]})
        
        # Wait for expiration
        time.sleep(0.1)
        
        # Try to read (should trigger expiry cleanup)
        result = mirror.get_context(test_key, "slot06_cultural_synthesis")
        
        # Check that expired count increased
        final_metrics = mirror.get_metrics()
        final_expired = final_metrics.get("queries_expired", 0)
        
        if result is None and final_expired > initial_expired:
            print("OK: ttl expiry")
            return True
        else:
            print(f"FAIL: ttl expiry - result={result}, expired count {initial_expired}->{final_expired}")
            return False
            
    except Exception as e:
        print(f"FAIL: ttl expiry - exception {e}")
        return False


def assert_rate_limiting():
    """Test that rate limiting triggers exactly at the configured threshold."""
    SemanticMirror, ContextScope = safe_import()
    if not SemanticMirror:
        return False
    
    try:
        mirror = SemanticMirror()
        
        # Set very low rate limit
        mirror.max_queries_per_minute = 2
        
        # Publish test context
        test_key = f"slot07.rate_test_{uuid.uuid4().hex[:8]}"
        mirror.publish_context(test_key, "data", "slot07_production_controls")
        mirror.add_access_rules({test_key: ["slot06_cultural_synthesis"]})
        
        # Get initial rate limited count
        initial_metrics = mirror.get_metrics()
        initial_rate_limited = initial_metrics.get("queries_rate_limited", 0)
        
        # Make exactly 3 queries (should rate limit on 3rd)
        result1 = mirror.get_context(test_key, "slot06_cultural_synthesis")
        result2 = mirror.get_context(test_key, "slot06_cultural_synthesis")
        result3 = mirror.get_context(test_key, "slot06_cultural_synthesis")  # Should be rate limited
        
        # Check final metrics
        final_metrics = mirror.get_metrics()
        final_rate_limited = final_metrics.get("queries_rate_limited", 0)
        rate_limited_increment = final_rate_limited - initial_rate_limited
        
        # Verify: first two succeed, third fails, exactly one rate limit event
        if (result1 == "data" and result2 == "data" and result3 is None and 
            rate_limited_increment == 1):
            print("OK: rate limiting")
            return True
        else:
            print(f"FAIL: rate limiting - results=[{result1}, {result2}, {result3}], "
                  f"rl_events={rate_limited_increment}")
            return False
            
    except Exception as e:
        print(f"FAIL: rate limiting - exception {e}")
        return False


def main():
    """Run all quick assertion tests."""
    print("Running Semantic Mirror quick assertions...")
    
    tests = [
        assert_deny_by_default,
        assert_ttl_expiry,
        assert_rate_limiting
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__} - unexpected exception {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("❌ Some assertions failed")
        sys.exit(1)
    else:
        print("✅ All assertions passed")
        sys.exit(0)


if __name__ == "__main__":
    main()