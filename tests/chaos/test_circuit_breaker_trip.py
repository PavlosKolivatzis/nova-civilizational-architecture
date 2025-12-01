"""
Chaos test for circuit breaker trip behavior.
"""
import pytest
import asyncio
from nova.orchestrator.core.circuit_breaker import CircuitBreaker

pytestmark = [pytest.mark.chaos, pytest.mark.asyncio]


async def test_circuit_breaker_trip_behavior():
    """Test circuit breaker trips after consecutive failures."""
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=60)

    # Simulate consecutive failures
    for i in range(3):
        try:
            with cb.protect():
                raise Exception(f"Simulated failure {i+1}")
        except Exception:
            pass

    # Circuit should be open after 3 failures
    assert cb.state == 'open', f"Expected 'open' state, got '{cb.state}'"

    # Requests should be blocked while circuit is open
    with pytest.raises(Exception, match="Circuit is open"):
        with cb.protect():
            pass  # This should not execute


async def test_circuit_breaker_auto_reset():
    """Test circuit breaker auto-reset after timeout."""
    cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)  # Short timeout for test

    # Trip the circuit
    for i in range(2):
        try:
            with cb.protect():
                raise Exception("Simulated failure")
        except Exception:
            pass

    assert cb.state == 'open'

    # Wait for reset timeout
    await asyncio.sleep(0.15)

    # Circuit should be half-open now
    assert cb.state == 'half-open', f"Expected 'half-open' state, got '{cb.state}'"

    # Successful request should close the circuit
    with cb.protect():
        pass  # Successful execution

    assert cb.state == 'closed', f"Expected 'closed' state, got '{cb.state}'"
