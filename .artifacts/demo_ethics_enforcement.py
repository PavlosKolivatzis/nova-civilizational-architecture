"""
Live Ethics Enforcement Demo

Shows how Nova's ethics system responds to different stability conditions.
"""
import sys
import time
sys.path.insert(0, 'C:/code/nova-civilizational-architecture')
sys.path.insert(0, 'C:/code/nova-civilizational-architecture/src')

from nova.governor import state as governor_state
from nova.slots.slot07_production_controls.wisdom_backpressure import (
    compute_max_concurrent_jobs,
    get_backpressure_config
)

def demo_ethics_enforcement():
    """Demonstrate ethics enforcement at different stability levels."""

    baseline, frozen_jobs, reduced_jobs, threshold = get_backpressure_config()

    print("=" * 70)
    print("NOVA ETHICS ENFORCEMENT - LIVE DEMONSTRATION")
    print("=" * 70)
    print()
    print(f"Configuration:")
    print(f"  Baseline capacity:   {baseline} jobs")
    print(f"  Reduced capacity:    {reduced_jobs} jobs")
    print(f"  Frozen capacity:     {frozen_jobs} jobs")
    print(f"  Stability threshold: {threshold}")
    print()
    print("=" * 70)

    # Scenario 1: STABLE SYSTEM
    print("\n[SCENARIO 1: STABLE SYSTEM]")
    print("-" * 70)
    stability = 0.15
    governor_state.set_frozen(False)
    max_jobs = compute_max_concurrent_jobs(stability_margin=stability)
    print(f"Stability margin (S): {stability:.3f} - STABLE")
    print(f"Governor frozen:      False")
    print(f"-> Max concurrent jobs: {max_jobs} ({max_jobs/baseline*100:.0f}% capacity)")
    print("-> Status: OK FULL OPERATION")
    print()

    # Scenario 2: UNSTABLE SYSTEM
    print("\n[SCENARIO 2: UNSTABLE SYSTEM]")
    print("-" * 70)
    stability = 0.025
    governor_state.set_frozen(False)
    max_jobs = compute_max_concurrent_jobs(stability_margin=stability)
    print(f"Stability margin (S): {stability:.3f} - UNSTABLE (< {threshold})")
    print(f"Governor frozen:      False")
    print(f"→ Max concurrent jobs: {max_jobs} ({max_jobs/baseline*100:.0f}% capacity)")
    print("→ Status: ⚠️  REDUCED THROUGHPUT (ethical constraint)")
    print()

    # Scenario 3: CRITICAL - FROZEN
    print("\n[SCENARIO 3: CRITICAL - LEARNING FROZEN]")
    print("-" * 70)
    stability = 0.01
    governor_state.set_frozen(True)  # ETHICS ENFORCEMENT: FREEZE
    max_jobs = compute_max_concurrent_jobs(stability_margin=stability)
    frozen = governor_state.is_frozen()
    print(f"Stability margin (S): {stability:.3f} - CRITICAL")
    print(f"Governor frozen:      {frozen} 🔴")
    print(f"→ Max concurrent jobs: {max_jobs} ({max_jobs/baseline*100:.0f}% capacity)")
    print("→ Status: 🚨 SURVIVAL MODE (ethics enforcement active)")
    print("→ Learning HALTED (η → 0)")
    print()

    # Scenario 4: RECOVERY
    print("\n[SCENARIO 4: RECOVERY TO STABLE]")
    print("-" * 70)
    stability = 0.08
    governor_state.set_frozen(False)  # Unfreeze after recovery
    max_jobs = compute_max_concurrent_jobs(stability_margin=stability)
    print(f"Stability margin (S): {stability:.3f} - RECOVERING")
    print(f"Governor frozen:      False")
    print(f"→ Max concurrent jobs: {max_jobs} ({max_jobs/baseline*100:.0f}% capacity)")
    print("→ Status: ✅ NORMAL OPERATION RESUMED")
    print()

    print("=" * 70)
    print("ETHICS ENFORCEMENT SUMMARY")
    print("=" * 70)
    print()
    print("┌─────────────┬──────────┬─────────┬──────────┬─────────────────┐")
    print("│ Condition   │ S value  │ Frozen? │ Capacity │ Ethical Action  │")
    print("├─────────────┼──────────┼─────────┼──────────┼─────────────────┤")
    print(f"│ STABLE      │  ≥0.03   │   No    │  {baseline:2d}/16    │ Normal ops      │")
    print(f"│ UNSTABLE    │  <0.03   │   No    │   {reduced_jobs:2d}/16    │ Throttle 63%    │")
    print(f"│ CRITICAL    │  <0.03   │  Yes 🔴 │   {frozen_jobs:2d}/16    │ Freeze learning │")
    print("└─────────────┴──────────┴─────────┴──────────┴─────────────────┘")
    print()
    print("Key Insights:")
    print("  • Ethics enforced automatically (no human intervention)")
    print("  • Capacity reduced BEFORE system failure")
    print("  • Learning frozen when bifurcation risk detected")
    print("  • System recovers autonomously when stable")
    print()
    print("=" * 70)

if __name__ == "__main__":
    demo_ethics_enforcement()
