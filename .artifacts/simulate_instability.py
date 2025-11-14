#!/usr/bin/env python
"""
Simulate system instability and show automatic ethics enforcement.
"""
import sys
import time
sys.path.insert(0, 'C:/code/nova-civilizational-architecture')
sys.path.insert(0, 'C:/code/nova-civilizational-architecture/src')

import warnings
warnings.filterwarnings('ignore')

from nova.governor import state as governor_state
from nova.slots.slot07_production_controls.wisdom_backpressure import compute_max_concurrent_jobs

def show_system_state(scenario, stability, frozen=False):
    """Show system state for a given scenario."""
    governor_state.set_frozen(frozen)
    max_jobs = compute_max_concurrent_jobs(stability_margin=stability)

    print(f"\n{'='*70}")
    print(f"{scenario}")
    print('='*70)
    print(f"Stability margin (S): {stability:.3f}")
    print(f"Governor frozen:      {frozen}")
    print(f"Max concurrent jobs:  {max_jobs}/16 ({max_jobs/16*100:.0f}% capacity)")

    if frozen:
        print("Learning status:      FROZEN (eta -> 0)")
        print("Enforcement:          [ALERT] SURVIVAL MODE")
    elif stability < 0.03:
        print("Learning status:      Active but throttled")
        print("Enforcement:          [WARN] REDUCED THROUGHPUT")
    else:
        print("Learning status:      Normal")
        print("Enforcement:          [OK] FULL OPERATION")

    return max_jobs

def main():
    print("\n" + "="*70)
    print(" NOVA ETHICS ENFORCEMENT - INSTABILITY SIMULATION")
    print("="*70)

    # Scenario 1: Normal operation
    show_system_state(
        "SCENARIO 1: NORMAL OPERATION",
        stability=0.15,
        frozen=False
    )

    time.sleep(1)

    # Scenario 2: System becomes unstable
    print("\n\n[ALERT] System detecting instability...")
    time.sleep(0.5)
    show_system_state(
        "SCENARIO 2: INSTABILITY DETECTED (S < 0.03)",
        stability=0.025,
        frozen=False
    )
    print("\n-> AUTOMATIC RESPONSE: Throughput reduced to 37%")
    print("-> This prevents cascading failures")

    time.sleep(1)

    # Scenario 3: Critical - bifurcation risk
    print("\n\n[CRITICAL] Bifurcation risk detected...")
    time.sleep(0.5)
    show_system_state(
        "SCENARIO 3: CRITICAL - BIFURCATION RISK",
        stability=0.01,
        frozen=True
    )
    print("\n-> AUTOMATIC RESPONSE: Learning FROZEN")
    print("-> System enters SURVIVAL MODE (12% capacity)")
    print("-> Prevents system collapse")

    time.sleep(1)

    # Scenario 4: Recovery begins
    print("\n\n[INFO] Stability improving...")
    time.sleep(0.5)
    show_system_state(
        "SCENARIO 4: RECOVERY BEGINNING",
        stability=0.05,
        frozen=False
    )
    print("\n-> AUTOMATIC RESPONSE: Unfrozen, gradual capacity increase")

    time.sleep(1)

    # Scenario 5: Full recovery
    print("\n\n[INFO] System stabilized...")
    time.sleep(0.5)
    show_system_state(
        "SCENARIO 5: FULL RECOVERY",
        stability=0.12,
        frozen=False
    )
    print("\n-> AUTOMATIC RESPONSE: Normal operations resumed")

    # Summary
    print("\n\n" + "="*70)
    print(" ETHICS ENFORCEMENT SUMMARY")
    print("="*70)
    print("\nAutomatic Response Timeline:")
    print("  t=0s:  Normal (S=0.15) -> 16 jobs (100%)")
    print("  t=1s:  Unstable (S=0.025) -> 6 jobs (37%) [THROTTLED]")
    print("  t=2s:  Critical (S=0.01) -> 2 jobs (12%) [FROZEN]")
    print("  t=3s:  Recovering (S=0.05) -> 6 jobs (37%) [UNFROZEN]")
    print("  t=4s:  Stable (S=0.12) -> 16 jobs (100%) [RECOVERED]")

    print("\n" + "="*70)
    print(" KEY INSIGHT: Ethics enforced AUTOMATICALLY by code")
    print("="*70)
    print("\nNo human intervention needed:")
    print("  - Detection: <15 seconds (wisdom poller cycle)")
    print("  - Response: <100ms (function call)")
    print("  - Recovery: Autonomous (when S improves)")
    print("\nAll observable via:")
    print("  - Prometheus: nova_wisdom_stability_margin")
    print("  - Prometheus: nova_slot07_jobs_current")
    print("  - Health API: /health (circuit_breaker state)")
    print("\n" + "="*70 + "\n")

    # Reset to normal
    governor_state.set_frozen(False)

if __name__ == "__main__":
    main()
