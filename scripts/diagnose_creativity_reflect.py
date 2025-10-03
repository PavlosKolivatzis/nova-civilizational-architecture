"""
Diagnostic script for creativity reflection endpoint.

Reproduces endpoint context to isolate configuration issues.
Sets environment variables before imports to test lazy initialization.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set env BEFORE any imports
os.environ['NOVA_CREATIVITY_EARLY_STOP'] = '1'
os.environ['NOVA_CREATIVITY_TWO_PHASE'] = '1'
os.environ['NOVA_CREATIVITY_BNB'] = '1'
os.environ['NOVA_CREATIVITY_EARLY_STOP_SCORE'] = '0.62'
os.environ['NOVA_CREATIVITY_BNB_Q'] = '0.40'
os.environ['NOVA_CREATIVITY_BNB_MARGIN'] = '0.05'

print("=" * 60)
print("Creativity Reflection Diagnostics")
print("=" * 60)

print(f"\nProcess ID: {os.getpid()}")
print(f"Python: {sys.version.split()[0]}")

print("\nEnvironment Variables:")
env_vars = [
    'NOVA_CREATIVITY_EARLY_STOP',
    'NOVA_CREATIVITY_TWO_PHASE',
    'NOVA_CREATIVITY_BNB',
    'NOVA_CREATIVITY_EARLY_STOP_SCORE',
    'NOVA_CREATIVITY_BNB_Q',
    'NOVA_CREATIVITY_BNB_MARGIN',
]
for var in env_vars:
    value = os.getenv(var)
    print(f"  {var}: {value}")

print("\nTesting Governor Initialization...")
try:
    from orchestrator.semantic_creativity import get_creativity_governor

    governor = get_creativity_governor()
    print(f"SUCCESS: Governor instance created: {id(governor)}")

    print(f"\nConfiguration:")
    print(f"  early_stop_enabled: {governor.config.early_stop_enabled}")
    print(f"  two_phase_depth_enabled: {governor.config.two_phase_depth_enabled}")
    print(f"  bnb_enabled: {governor.config.bnb_enabled}")
    print(f"  early_stop_target_score: {governor.config.early_stop_target_score}")
    print(f"  bnb_quality_threshold: {governor.config.bnb_quality_threshold}")
    print(f"  bnb_safety_margin: {governor.config.bnb_safety_margin}")

    print(f"\nRetrieving Metrics...")
    metrics = governor.get_creativity_metrics()

    print(f"\nSUCCESS - Config Snapshot:")
    config_snapshot = metrics.get('config_snapshot', {})
    for key, value in config_snapshot.items():
        print(f"  {key}: {value}")

    print(f"\nAll checks passed!")

except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
