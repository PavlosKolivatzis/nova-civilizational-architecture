#!/usr/bin/env python3
"""
Semantic Convergence Analysis for Phase 11 Step C

Analyzes cross-AI audit results to identify:
1. Convergence points (where all AIs agree)
2. Divergence points (where interpretations differ)
3. Implementation quality metrics
4. Ontology tightening recommendations

Usage:
    python scripts/analyze_semantic_convergence.py
    python scripts/analyze_semantic_convergence.py --verbose
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter


class ConvergenceAnalyzer:
    """Analyzes semantic convergence across multiple AI audits."""

    def __init__(self, audit_dir: Path):
        self.audit_dir = audit_dir
        self.ai_systems: List[str] = []
        self.convergence_points: List[str] = []
        self.divergence_points: List[Dict] = []
        self.recommendations: List[str] = []

    def discover_audits(self) -> None:
        """Discover all AI audit directories."""
        for subdir in self.audit_dir.iterdir():
            if subdir.is_dir() and "phase11" in subdir.name:
                ai_name = subdir.name.replace("_phase11", "").replace("_", " ").title()
                self.ai_systems.append(ai_name)

        print(f"Discovered {len(self.ai_systems)} AI audit results:")
        for ai in sorted(self.ai_systems):
            print(f"  - {ai}")

    def analyze_regime_state_machine(self) -> None:
        """Analyze regime state machine reconstructions."""
        print("\n=== Regime State Machine Convergence ===")

        transitions_per_ai: Dict[str, Set[Tuple[str, str]]] = {}

        # Extract transitions from each AI's output
        for subdir in self.audit_dir.iterdir():
            if not subdir.is_dir() or "phase11" not in subdir.name:
                continue

            ai_name = subdir.name.replace("_phase11", "").replace("_", " ").title()

            # Try to find transition data in various formats
            transitions = set()

            # Check for JSON schema
            json_file = subdir / "regime_state_machine_schema.json"
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        schema = json.load(f)
                        edges = schema.get("transition_graph", {}).get("allowed_edges", [])
                        transitions.update(tuple(edge) for edge in edges)
                except Exception:
                    pass

            # Check for markdown files
            md_file = subdir / "regime_state_machine.md"
            if md_file.exists() and not transitions:
                # Parse markdown for transition mentions
                # This is a simplified parser - could be enhanced
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for common patterns like "NORMAL -> HEIGHTENED"
                    import re
                    pattern = r'(\w+)\s*-+>\s*(\w+)'
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    transitions.update((m[0].lower(), m[1].lower()) for m in matches)

            if transitions:
                transitions_per_ai[ai_name] = transitions

        # Find common transitions (convergence)
        if transitions_per_ai:
            all_transitions = set.union(*transitions_per_ai.values())
            common_transitions = set.intersection(*transitions_per_ai.values())

            print(f"\n  Total unique transitions found: {len(all_transitions)}")
            print(f"  Universally agreed transitions: {len(common_transitions)}")

            if common_transitions:
                print(f"\n  Converged transitions ({len(common_transitions)}):")
                for from_regime, to_regime in sorted(common_transitions):
                    print(f"    {from_regime} -> {to_regime}")
                self.convergence_points.append(f"State machine: {len(common_transitions)} transitions unanimous")

            # Find divergent transitions
            divergent = all_transitions - common_transitions
            if divergent:
                print(f"\n  Divergent interpretations ({len(divergent)}):")
                for from_regime, to_regime in sorted(divergent):
                    supporters = [ai for ai, trans in transitions_per_ai.items()
                                 if (from_regime, to_regime) in trans]
                    print(f"    {from_regime} -> {to_regime}: {', '.join(supporters)}")
                    self.divergence_points.append({
                        "area": "state_machine",
                        "transition": f"{from_regime}->{to_regime}",
                        "supporters": supporters
                    })

    def analyze_hysteresis_rules(self) -> None:
        """Analyze hysteresis rule interpretations."""
        print("\n=== Hysteresis Rules Convergence ===")

        min_durations_per_ai: Dict[str, Dict[str, float]] = {}

        for subdir in self.audit_dir.iterdir():
            if not subdir.is_dir() or "phase11" not in subdir.name:
                continue

            ai_name = subdir.name.replace("_phase11", "").replace("_", " ").title()

            # Check JSON schema
            json_file = subdir / "regime_state_machine_schema.json"
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        schema = json.load(f)
                        min_dur = schema.get("hysteresis_config", {}).get("min_duration_s", {})
                        if min_dur:
                            min_durations_per_ai[ai_name] = min_dur
                except Exception:
                    pass

            # Check markdown files
            md_file = subdir / "hysteresis_rules.md"
            if md_file.exists() and ai_name not in min_durations_per_ai:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Parse for duration values
                    import re
                    # Look for patterns like "normal: 60s" or "recovery: 1800"
                    durations = {}
                    for line in content.split('\n'):
                        match = re.search(r'(normal|heightened|controlled_degradation|emergency_stabilization|recovery).*?(\d+)', line, re.IGNORECASE)
                        if match:
                            regime = match.group(1).lower()
                            duration = float(match.group(2))
                            durations[regime] = duration
                    if durations:
                        min_durations_per_ai[ai_name] = durations

        if min_durations_per_ai:
            # Check convergence on minimum durations
            regimes = ["normal", "heightened", "controlled_degradation", "emergency_stabilization", "recovery"]
            canonical_durations = {
                "normal": 60.0,
                "heightened": 300.0,
                "controlled_degradation": 600.0,
                "emergency_stabilization": 900.0,
                "recovery": 1800.0
            }

            converged = 0
            diverged = 0

            for regime in regimes:
                values = [ai_durs.get(regime) for ai_durs in min_durations_per_ai.values()
                         if regime in ai_durs]
                if values:
                    if all(v == canonical_durations[regime] for v in values):
                        converged += 1
                    else:
                        diverged += 1
                        unique_vals = set(values)
                        print(f"  {regime}: {unique_vals} (expected {canonical_durations[regime]}s)")
                        self.divergence_points.append({
                            "area": "hysteresis",
                            "regime": regime,
                            "values": list(unique_vals),
                            "expected": canonical_durations[regime]
                        })

            print(f"\n  Minimum durations:")
            print(f"    Converged: {converged}/{len(regimes)}")
            print(f"    Diverged: {diverged}/{len(regimes)}")

            if converged == len(regimes):
                self.convergence_points.append("Hysteresis: All minimum durations unanimous")

    def analyze_safety_violations(self) -> None:
        """Analyze safety envelope violation detection."""
        print("\n=== Safety Envelope Analysis ===")

        violations_per_ai: Dict[str, List[str]] = {}

        for subdir in self.audit_dir.iterdir():
            if not subdir.is_dir() or "phase11" not in subdir.name:
                continue

            ai_name = subdir.name.replace("_phase11", "").replace("_", " ").title()

            # Check for safety violations file
            violations_file = subdir / "safety_violations.md"
            if violations_file.exists():
                with open(violations_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract violation types mentioned
                    violations = []
                    for inv in ["no_uncontrolled_acceleration", "no_noise_amplification",
                               "no_destructive_oscillation", "continuity_preservation"]:
                        if inv in content:
                            violations.append(inv)
                    violations_per_ai[ai_name] = violations

        if violations_per_ai:
            all_violations = set.union(*[set(v) for v in violations_per_ai.values()])
            print(f"\n  Safety rules validated:")
            for violation in sorted(all_violations):
                validators = [ai for ai, viols in violations_per_ai.items() if violation in viols]
                print(f"    {violation}: {len(validators)}/{len(violations_per_ai)} AIs")

            # Check if all AIs validated all 4 core invariants
            core_invariants = {"no_uncontrolled_acceleration", "no_noise_amplification",
                              "no_destructive_oscillation", "continuity_preservation"}
            complete_audits = [ai for ai, viols in violations_per_ai.items()
                              if core_invariants.issubset(set(viols))]
            print(f"\n  Complete safety audits: {len(complete_audits)}/{len(violations_per_ai)}")

            if len(complete_audits) >= len(violations_per_ai) * 0.75:
                self.convergence_points.append(f"Safety: {len(complete_audits)} AIs validated all core invariants")

    def generate_recommendations(self) -> None:
        """Generate ontology tightening recommendations based on divergence."""
        print("\n=== Ontology Tightening Recommendations ===")

        if not self.divergence_points:
            print("\n  No significant divergence detected - ontology is well-specified!")
            return

        # Group divergence by area
        by_area = {}
        for div in self.divergence_points:
            area = div["area"]
            by_area.setdefault(area, []).append(div)

        for area, divs in by_area.items():
            print(f"\n  {area.upper()}:")
            for div in divs:
                if area == "state_machine":
                    print(f"    - Clarify if transition {div['transition']} is allowed")
                    print(f"      (Supported by: {', '.join(div['supporters'])})")
                    self.recommendations.append(
                        f"Add explicit forbidden_direct rule for {div['transition']} if not allowed"
                    )
                elif area == "hysteresis":
                    print(f"    - Reconcile {div['regime']} min_duration values: {div['values']}")
                    print(f"      (Expected: {div['expected']}s)")
                    self.recommendations.append(
                        f"Document {div['regime']} minimum duration more explicitly in contracts"
                    )

        if self.recommendations:
            print(f"\n  Total recommendations: {len(self.recommendations)}")
        else:
            print("\n  No specific recommendations - minor divergences only")

    def generate_report(self) -> None:
        """Generate final convergence report."""
        print("\n" + "=" * 60)
        print("SEMANTIC CONVERGENCE REPORT")
        print("=" * 60)

        print(f"\nAI Systems Analyzed: {len(self.ai_systems)}")
        print(f"Convergence Points: {len(self.convergence_points)}")
        print(f"Divergence Points: {len(self.divergence_points)}")
        print(f"Recommendations: {len(self.recommendations)}")

        if self.convergence_points:
            print("\n[CONVERGENCE] Strong agreement:")
            for point in self.convergence_points:
                print(f"  - {point}")

        if self.divergence_points:
            print(f"\n[DIVERGENCE] Areas requiring clarification ({len(self.divergence_points)}):")
            areas = Counter(d["area"] for d in self.divergence_points)
            for area, count in areas.most_common():
                print(f"  - {area}: {count} instances")

        convergence_rate = len(self.convergence_points) / max(len(self.convergence_points) + len(self.divergence_points), 1)
        print(f"\nOverall Convergence Rate: {convergence_rate:.1%}")

        if convergence_rate >= 0.8:
            print("\n[PASS] Ontology demonstrates strong semantic stability across AI systems")
        elif convergence_rate >= 0.6:
            print("\n[PARTIAL] Ontology needs minor clarifications in divergent areas")
        else:
            print("\n[REVIEW] Ontology requires significant tightening to achieve convergence")

    def analyze(self) -> bool:
        """Run full convergence analysis."""
        print("=" * 60)
        print("Phase 11 Step C - Cross-System Semantic Audit Analysis")
        print("=" * 60)

        self.discover_audits()
        self.analyze_regime_state_machine()
        self.analyze_hysteresis_rules()
        self.analyze_safety_violations()
        self.generate_recommendations()
        self.generate_report()

        return len(self.divergence_points) < len(self.convergence_points)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze semantic convergence across AI audits"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    audit_dir = repo_root / "docs" / "phase11_step_c_audits"

    if not audit_dir.exists():
        print(f"Error: Audit directory not found: {audit_dir}")
        sys.exit(1)

    analyzer = ConvergenceAnalyzer(audit_dir)
    success = analyzer.analyze()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
