# Nova Test Suite

## Overview

**2,089 total tests** with 100% pass rate - comprehensive coverage across all 10 cognitive slots and system components.

## Test Categories

### Core Test Suites
- **`tests/api/`** - API endpoint tests and integrations
- **`tests/attestation/`** - Cryptographic verification and attestation systems
- **`tests/chaos/`** - Resilience testing and failure simulation
- **`tests/concurrency/`** - Thread safety and concurrent operations
- **`tests/continuity/`** - Temporal continuity and regime transitions
- **`tests/federation/`** - Multi-peer coordination and federation
- **`tests/health/`** - System health checks and monitoring

### Specialized Testing
- **`tests/orchestrator/`** - Event-driven coordination layer
- **`tests/performance/`** - Performance benchmarks and optimization
- **`tests/property/`** - Property-based testing with Hypothesis
- **`tests/slo/`** - Service Level Objective validation
- **`tests/meta/`** - Documentation and configuration validation

### Slot-Specific Tests
- **`tests/slot01/`** - Truth Anchor (cryptographic reality verification)
- **`tests/slot02/`** - ΔTHRESH (pattern detection, META_LENS)
- **`tests/slot03/`** - Emotional Matrix (cognitive processing hub)
- **`tests/slot04/`** - TRI Engine (flow-mesh reasoning)
- **`tests/slot05/`** - Constellation (spatial navigation)
- **`tests/slot06/`** - Cultural Synthesis (ethical guardrails)
- **`tests/slot07/`** - Production Controls (circuit breaker system)
- **`tests/slot08/`** - Memory Ethics & IDS (ACL and self-healing)
- **`tests/slot09/`** - Distortion Protection (hybrid defense)
- **`tests/slot10/`** - Civilizational Deployment (MetaLegitimacySeal)

## Quick Commands

```bash
# Full test suite (recommended)
pytest tests/ -q

# Health checks only (fast, for CI)
pytest -m health -q

# Slot-specific testing
pytest tests/slot01_truth_anchor/ -q
pytest tests/slot07_production_controls/ -q

# Performance testing
pytest tests/performance/ -q

# Chaos engineering
pytest tests/chaos/ -q

# Stop on first failure
pytest tests/ --maxfail=1 -x

# Verbose output with coverage
pytest tests/ -v --cov=nova --cov-report=html
```

## Test Infrastructure

### Quality Assurance
- **Property-based testing** with Hypothesis for edge cases
- **Integration testing** for cross-slot interactions
- **Performance benchmarking** with statistical analysis
- **Chaos engineering** for resilience validation
- **Concurrency testing** for thread safety

### Test Markers
```bash
# Health matrix (CI smoke tests)
pytest -m health

# Slow tests (performance, integration)
pytest -m slow

# Integration tests
pytest -m integration

# Property-based tests
pytest -m property

# Slot-specific markers
pytest -m slot01,slot02,slot03,...
```

## Coverage Metrics

- **Line Coverage**: >95% across core modules
- **Branch Coverage**: >90% for decision logic
- **Mutation Testing**: >85% mutation score
- **Performance Regression**: Automated detection

## Test Data & Fixtures

### Shared Fixtures
- **`conftest.py`** - Global test configuration and fixtures
- **Mock data** for external dependencies
- **Test ontologies** for validation scenarios
- **Performance baselines** for regression detection

### Environment Setup
```bash
# Test environment variables
export NOVA_TEST_MODE=1
export NOVA_ENABLE_PROMETHEUS=0  # Disable for faster tests
export JWT_SECRET="test-secret-minimum-32-characters-long"
```

## CI/CD Integration

### Health Matrix
- **11 test suites** run across Python 3.10/3.11/3.12
- **<15 seconds** execution time per matrix job
- **Zero false positives** through marker filtering

### Quality Gates
- **Test pass rate**: 100% required
- **Coverage thresholds**: Must maintain or improve
- **Performance regression**: Automatic failure detection
- **Security scanning**: Integrated with test pipeline

## Contributing Tests

### Test Structure Guidelines
```python
# Use descriptive test names
def test_slot_emotion_processing_under_load():
    """Test emotional processing maintains accuracy under high load."""

# Use fixtures for setup/teardown
@pytest.fixture
def emotional_matrix():
    return create_test_emotional_matrix()

# Mark appropriately
@pytest.mark.health
@pytest.mark.slot03
def test_emotional_matrix_health_check():
    pass

@pytest.mark.performance
@pytest.mark.slow
def test_emotional_processing_performance():
    pass
```

### Test Categories
- **Unit tests**: Individual function/component testing
- **Integration tests**: Cross-component interactions
- **End-to-end tests**: Full system workflows
- **Performance tests**: Speed, memory, scalability
- **Chaos tests**: Failure injection and recovery

## Debugging Failed Tests

### Common Issues
```bash
# Check test isolation
pytest tests/slot03/ -v --pdb

# Run with logging
pytest tests/ -v -s --log-cli-level=INFO

# Check for race conditions
pytest tests/concurrency/ -v --tb=long

# Performance debugging
pytest tests/performance/ -v --durations=10
```

### Test Dependencies
- **pytest** - Core testing framework
- **pytest-cov** - Coverage reporting
- **pytest-xdist** - Parallel execution
- **hypothesis** - Property-based testing
- **faker** - Test data generation

## Test Maintenance

### Regular Tasks
- **Update baselines** after performance improvements
- **Review coverage gaps** monthly
- **Update test data** for new features
- **Clean up obsolete tests** after refactoring

### Quality Metrics
- **Test-to-code ratio**: >1.5 (current: 2.1)
- **Test execution time**: <5 minutes for full suite
- **Flakiness rate**: <0.1% (current: 0.05%)

---

*This test suite ensures Nova Civilizational Architecture maintains production-grade quality across all 10 cognitive slots and system components.*