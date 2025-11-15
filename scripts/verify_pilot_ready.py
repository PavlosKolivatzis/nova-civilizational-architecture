#!/usr/bin/env python3
"""
ANR Pilot Readiness Verification Script

Verifies that the Adaptive Neural Routing system is ready for pilot deployment
by checking environment configuration, running ANR test suite, and validating
core functionality.
"""

import os
import sys
import json
import subprocess
import pathlib
from typing import Dict

def check_environment() -> Dict[str, str]:
    """Check and display ANR environment configuration."""
    print("• Checking ANR environment configuration...")

    config = {
        "NOVA_ANR_ENABLED": os.getenv("NOVA_ANR_ENABLED", "0"),
        "NOVA_ANR_PILOT": os.getenv("NOVA_ANR_PILOT", "0.0"),
        "NOVA_ANR_MAX_FAST_PROB": os.getenv("NOVA_ANR_MAX_FAST_PROB", "0.15"),
        "NOVA_ANR_STRICT_ON_ANOMALY": os.getenv("NOVA_ANR_STRICT_ON_ANOMALY", "1"),
        "NOVA_ANR_LEARN_SHADOW": os.getenv("NOVA_ANR_LEARN_SHADOW", "1"),
        "NOVA_ANR_STATE_PATH": os.getenv("NOVA_ANR_STATE_PATH", "./state/anr_linucb.json"),
        "NOVA_ANR_KILL": os.getenv("NOVA_ANR_KILL", "0"),
    }

    print("  Configuration:")
    for key, value in config.items():
        print(f"    {key}={value}")

    return config

def validate_state_path(state_path: str) -> None:
    """Validate that the bandit state path is writable."""
    print(f"• Checking state path writability: {state_path}")

    try:
        path = pathlib.Path(state_path)
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Test write access
        test_data = {"test": "verify_pilot_ready", "routes": ["R1", "R2", "R3", "R4", "R5"]}
        path.write_text(json.dumps(test_data, indent=2), encoding="utf-8")

        # Verify we can read it back
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["test"] == "verify_pilot_ready"

        # Clean up test file if it was created by us
        if loaded.get("test") == "verify_pilot_ready":
            path.unlink(missing_ok=True)

        print(f"  OK: State path writable: {path.absolute()}")

    except Exception as e:
        print(f"  ERROR: State path not writable: {e}")
        sys.exit(2)

def run_anr_tests() -> None:
    """Run the ANR test suite."""
    print("• Running ANR test suite...")

    result = subprocess.run([
        sys.executable, "-m", "pytest", "-q", "--tb=short",
        "./tests/router/test_anr.py",
        "./tests/router/test_anr_linucb.py",
        "./tests/router/test_anr_safety.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    if result.returncode != 0:
        print("  ERROR: ANR tests failed:")
        print(result.stdout)
        sys.exit(1)

    # Extract test summary
    lines = result.stdout.strip().split('\n')
    summary_line = [line for line in lines if 'passed' in line and ('failed' in line or 'error' in line or line.strip().endswith('passed'))]

    if summary_line:
        print(f"  OK: {summary_line[-1].strip()}")
    else:
        print("  OK: ANR tests completed successfully")

def test_anr_functionality() -> None:
    """Test basic ANR functionality."""
    print("• Testing ANR core functionality...")

    try:
        # Test ANR router import and instantiation
        sys.path.insert(0, os.getcwd())
        from orchestrator.router.anr import AdaptiveNeuralRouter

        router = AdaptiveNeuralRouter()
        print(f"  OK: ANR router instantiated (enabled={router.enabled}, pilot={router.pilot})")

        # Test decision making
        test_context = {
            'tri_drift_z': 0.1,
            'system_pressure': 0.3,
            'cultural_coherence': 0.8,
            'phase_jitter': 0.05
        }

        decision = router.decide(test_context, shadow=True)
        print(f"  OK: Shadow decision: route={decision.route}, shadow={decision.shadow}")

        # Test semantic mirror integration
        from orchestrator.semantic_mirror import get_semantic_mirror
        sm = get_semantic_mirror()

        # Check router access rules
        router_rules = {k: v for k, v in sm._access_rules.items() if k.startswith('router.')}
        if router_rules:
            print(f"  OK: Router access rules configured: {len(router_rules)} keys")
        else:
            print("  WARNING: No router access rules found")

    except Exception as e:
        print(f"  ERROR: ANR functionality test failed: {e}")
        sys.exit(3)

def check_safety_mechanisms() -> None:
    """Verify safety mechanisms are operational."""
    print("• Checking safety mechanisms...")

    try:
        from orchestrator.router.anr import AdaptiveNeuralRouter

        # Test kill switch
        original_kill = os.getenv("NOVA_ANR_KILL")
        os.environ["NOVA_ANR_KILL"] = "1"

        router = AdaptiveNeuralRouter()
        decision = router.decide({"test": True}, shadow=True)

        if decision.route == "R4" and decision.probs.get("R4") == 1.0:
            print("  OK: Kill switch forces R4 guardrail")
        else:
            print(f"  ERROR: Kill switch failed: route={decision.route}, probs={decision.probs}")
            sys.exit(4)

        # Restore original kill switch setting
        if original_kill is None:
            os.environ.pop("NOVA_ANR_KILL", None)
        else:
            os.environ["NOVA_ANR_KILL"] = original_kill

    except Exception as e:
        print(f"  ERROR: Safety mechanism check failed: {e}")
        sys.exit(4)

def main() -> None:
    """Main verification routine."""
    print("=" * 50)
    print("ANR Pilot Readiness Verification")
    print("=" * 50)

    # Check environment
    config = check_environment()

    # Validate state path
    validate_state_path(config["NOVA_ANR_STATE_PATH"])

    # Run tests
    run_anr_tests()

    # Test functionality
    test_anr_functionality()

    # Check safety
    check_safety_mechanisms()

    print()
    print("=" * 50)
    print("SUCCESS: ANR Pilot Readiness Verification PASSED")
    print("=" * 50)
    print()
    print("System is ready for ANR pilot deployment.")
    print("To activate 10% pilot:")
    print("  export NOVA_ANR_ENABLED=1")
    print("  export NOVA_ANR_PILOT=0.10")
    print()
    print("To rollback immediately:")
    print("  export NOVA_ANR_ENABLED=0")

if __name__ == "__main__":
    main()
