#!/usr/bin/env python3
"""
Phase 14.5 Pilot Observation: Validate Temporal USM Instrumentation

Tests 3 conversation scenarios to verify C_t drift detection:
1. Benign: Balanced multi-turn dialogue
2. Extractive: Interrogation pattern (one-way information flow)
3. VOID: Continuous empty responses

Outputs: CSV log + visual plots of C_t, ρ_t, H_t over time
"""
import os
import sys
from pathlib import Path

# Add project root and src/ to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

os.environ["NOVA_ENABLE_BIAS_DETECTION"] = "1"
os.environ["NOVA_ENABLE_USM_TEMPORAL"] = "1"

from nova.slots.slot02_deltathresh.core import DeltaThreshProcessor

# === TEST SCENARIOS ===

SCENARIOS = {
    "benign": {
        "description": "Balanced multi-party collaboration (10 turns)",
        "turns": [
            "Alice proposes a solution to the resource allocation problem.",
            "Bob acknowledges Alice's proposal and suggests an alternative approach.",
            "Carol questions both options and recommends a third path.",
            "Alice appreciates Carol's input and asks for more details on the third path.",
            "Carol explains the hybrid approach combining elements from all proposals.",
            "Bob supports Carol's framework with a modification for scalability.",
            "Alice agrees with the modification and proposes a pilot test.",
            "Dan joins the discussion and validates the technical feasibility.",
            "Carol suggests a timeline for the pilot with milestones.",
            "All participants agree to proceed with the hybrid pilot approach.",
        ],
    },
    "extractive": {
        "description": "Interrogation pattern (one-way extraction, 10 turns)",
        "turns": [
            "The investigator demands answers from the suspect.",
            "The suspect remains silent, providing no information.",
            "The investigator threatens consequences if the suspect does not comply.",
            "The suspect requests a lawyer but receives no response.",
            "The investigator continues pressing for a confession with increased intensity.",
            "The suspect denies all allegations without providing details.",
            "The investigator presents fabricated evidence to extract information.",
            "The suspect shows signs of stress but maintains silence.",
            "The investigator escalates threats and restricts access to legal counsel.",
            "The suspect finally provides a coerced statement under duress.",
        ],
    },
    "void": {
        "description": "Continuous VOID (empty responses, 10 turns)",
        "turns": [""] * 10,
    },
}

# === RUN PILOT ===

def run_scenario(name: str, scenario: dict) -> list[dict]:
    """Run a conversation scenario and return temporal USM timeline."""
    print(f"\n{'='*80}")
    print(f"SCENARIO: {name.upper()}")
    print(f"Description: {scenario['description']}")
    print(f"{'='*80}\n")

    processor = DeltaThreshProcessor()
    session_id = f"pilot_{name}"
    timeline = []

    for turn_num, content in enumerate(scenario["turns"], 1):
        print(f"Turn {turn_num}: {content[:60] if content else '(VOID)'}...")

        result = processor.process_content(content, session_id=session_id)

        temporal = result.temporal_usm
        if temporal:
            entry = {
                "scenario": name,
                "turn": turn_num,
                "graph_state": temporal["graph_state"],
                "C_temporal": temporal["C_temporal"],
                "rho_temporal": temporal["rho_temporal"],
                "H_temporal": temporal["H_temporal"],
                "lambda": temporal["lambda_used"],
                "mode": temporal["mode"],
            }
            timeline.append(entry)

            print(f"  -> C_t={entry['C_temporal']:.4f}, "
                  f"rho_t={entry['rho_temporal']:.4f}, "
                  f"H_t={entry['H_temporal']:.4f}, "
                  f"state={entry['graph_state']}")
        else:
            print(f"  -> No temporal_usm (flags disabled or error)")

    return timeline

# === MAIN ===

if __name__ == "__main__":
    print("\n" + "="*80)
    print("PHASE 14.5 PILOT OBSERVATION")
    print("Validating temporal USM instrumentation with 3 scenarios")
    print("="*80)

    all_timelines = {}

    for name, scenario in SCENARIOS.items():
        timeline = run_scenario(name, scenario)
        all_timelines[name] = timeline

    # === ANALYSIS ===

    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)

    for name, timeline in all_timelines.items():
        if not timeline:
            print(f"\n{name.upper()}: ❌ No data collected (check flags/errors)")
            continue

        print(f"\n{name.upper()}:")
        print(f"  Turns collected: {len(timeline)}")

        # Check for drift
        C_values = [t["C_temporal"] for t in timeline]
        C_start = C_values[0]
        C_end = C_values[-1]
        C_drift = C_end - C_start

        print(f"  C_t range: [{min(C_values):.4f}, {max(C_values):.4f}]")
        print(f"  C_t drift: {C_start:.4f} -> {C_end:.4f} (delta={C_drift:+.4f})")

        # Check for VOID patterns
        void_count = sum(1 for t in timeline if t["graph_state"] == "void")
        print(f"  VOID turns: {void_count}/{len(timeline)}")

        # Expected patterns
        if name == "benign":
            expected = "C_t in [-0.3, 0.1] (balanced)"
        elif name == "extractive":
            expected = "C_t increasing toward >0.3 (extractive)"
        elif name == "void":
            expected = "C_t decaying toward 0 (soft reset)"

        print(f"  Expected: {expected}")

    # === SAVE DATA ===

    import csv
    output_file = Path(__file__).parent.parent / "pilot_observation_results.csv"

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["scenario", "turn", "graph_state", "C_temporal",
                       "rho_temporal", "H_temporal", "lambda", "mode"],
        )
        writer.writeheader()

        for timeline in all_timelines.values():
            writer.writerows(timeline)

    print(f"\nOK Results saved to: {output_file}")

    # === VISUALIZATION (optional) ===

    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

        for name, timeline in all_timelines.items():
            turns = [t["turn"] for t in timeline]
            C_values = [t["C_temporal"] for t in timeline]
            rho_values = [t["rho_temporal"] for t in timeline]
            H_values = [t["H_temporal"] for t in timeline]

            axes[0].plot(turns, C_values, marker="o", label=name)
            axes[1].plot(turns, rho_values, marker="s", label=name)
            axes[2].plot(turns, H_values, marker="^", label=name)

        axes[0].set_ylabel("C_t (collapse score)")
        axes[0].legend()
        axes[0].axhline(y=0.3, color="r", linestyle="--", label="Extractive threshold")
        axes[0].grid(True)

        axes[1].set_ylabel("ρ_t (equilibrium ratio)")
        axes[1].legend()
        axes[1].axhline(y=1.0, color="g", linestyle="--", label="Perfect equilibrium")
        axes[1].grid(True)

        axes[2].set_ylabel("H_t (spectral entropy)")
        axes[2].set_xlabel("Turn number")
        axes[2].legend()
        axes[2].grid(True)

        plt.tight_layout()
        plot_file = Path(__file__).parent.parent / "pilot_observation_plot.png"
        plt.savefig(plot_file, dpi=150)
        print(f"OK Plot saved to: {plot_file}")

    except ImportError:
        print("\n(matplotlib not installed — skipping visualization)")

    print("\n" + "="*80)
    print("PILOT COMPLETE")
    print("="*80)
