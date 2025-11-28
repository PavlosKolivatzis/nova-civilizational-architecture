#!/usr/bin/env python3
"""
Regime and hysteresis analyzer for the Phase 11 Operational Regime Policy (ORP).
Loads the ontology/contract YAML files, reconstructs the regime state machine,
articulates hysteresis rules, simulates representative transitions, checks
safety envelope compliance, and emits a convergence matrix.
"""

from __future__ import annotations

import math
from collections import deque
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import yaml

ROOT = Path(__file__).resolve().parent


def load_yaml(name: str):
    with open(ROOT / name, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def range_of(value) -> Tuple[float, float]:
    if isinstance(value, list):
        return float(value[0]), float(value[-1])
    return float(value), float(value)


def build_state_machine(geom: dict):
    states: List[str] = list(geom["states"])
    allowed = [tuple(pair) for pair in geom["transitions"]["allowed"]]
    forbidden = {tuple(pair) for pair in geom["transitions"].get("forbidden_direct", [])}
    min_durations = {key: float(val) for key, val in geom["transitions"]["min_duration_s"].items()}
    return states, allowed, forbidden, min_durations


def describe_hysteresis(hysteresis_contract: dict) -> Dict[str, float]:
    decision_logic = hysteresis_contract["decision_logic"]
    return {
        "oscillation_window_s": float(decision_logic["oscillation_window"]),
        "oscillation_threshold": int(decision_logic["oscillation_threshold"]),
        "min_durations": {k: float(v) for k, v in decision_logic["minimum_durations"].items()},
    }


def evaluate_transition(
    current: str,
    proposed: str,
    duration_s: float,
    now_s: float,
    history_s: Sequence[float],
    allowed: Iterable[Tuple[str, str]],
    forbidden: Iterable[Tuple[str, str]],
    min_durations: Dict[str, float],
    osc_window: float,
    osc_threshold: int,
) -> dict:
    allowed_set = set(allowed)
    forbidden_set = set(forbidden)

    oscillation_count = sum(1 for t in history_s if now_s - t <= osc_window) + 1
    oscillation_detected = oscillation_count >= osc_threshold

    if (current, proposed) not in allowed_set or (current, proposed) in forbidden_set:
        return {
            "allowed": False,
            "effective_regime": current,
            "reason": f"illegal_transition:{current}->{proposed}",
            "current_regime": current,
            "proposed_regime": proposed,
            "current_duration_s": duration_s,
            "min_duration_s": min_durations.get(current, 0.0),
            "time_remaining_s": 0.0,
            "oscillation_detected": oscillation_detected,
            "oscillation_count": oscillation_count,
        }

    min_required = min_durations[current]
    if duration_s < min_required:
        time_remaining = min_required - duration_s
        return {
            "allowed": False,
            "effective_regime": current,
            "reason": f"min_duration_not_met:{duration_s:.1f}s<{min_required:.1f}s",
            "current_regime": current,
            "proposed_regime": proposed,
            "current_duration_s": duration_s,
            "min_duration_s": min_required,
            "time_remaining_s": time_remaining,
            "oscillation_detected": oscillation_detected,
            "oscillation_count": oscillation_count,
        }

    return {
        "allowed": True,
        "effective_regime": proposed,
        "reason": f"min_duration_met:{duration_s:.1f}s>={min_required:.1f}s",
        "current_regime": current,
        "proposed_regime": proposed,
        "current_duration_s": duration_s,
        "min_duration_s": min_required,
        "time_remaining_s": 0.0,
        "oscillation_detected": oscillation_detected,
        "oscillation_count": oscillation_count,
    }


def detect_safety_envelope_issues(
    geom: dict, operating: dict, allowed: Iterable[Tuple[str, str]], forbidden: Iterable[Tuple[str, str]]
) -> List[str]:
    issues: List[str] = []
    global_bounds = {k: (float(v[0]), float(v[1])) for k, v in geom["amplitude_bounds"]["global"].items()}
    per_regime = geom["amplitude_bounds"]["per_regime"]

    mapping = {
        "eta_scaled": "governor_eta_scale",
        "emotion": "emotion_constriction",
        "sensitivity": "slot09_sensitivity_multiplier",
    }

    for regime, bounds in per_regime.items():
        for global_key, local_key in mapping.items():
            lo, hi = range_of(bounds[local_key])
            g_lo, g_hi = global_bounds[global_key]
            if lo < g_lo or hi > g_hi:
                issues.append(
                    f"amplitude_out_of_bounds:{regime}.{local_key}={lo}-{hi} not within global {g_lo}-{g_hi}"
                )

    conflicts = set(allowed) & set(forbidden)
    for src, dst in sorted(conflicts):
        issues.append(f"transition_conflict:{src}->{dst} is both allowed and forbidden")

    geom_min = {k: float(v) for k, v in geom["transitions"]["min_duration_s"].items()}
    operating_min = {k: float(v) for k, v in operating["transitions"]["min_duration_s"].items()}
    for regime, geom_value in geom_min.items():
        child_value = operating_min.get(regime)
        if child_value is None:
            issues.append(f"missing_child_min_duration:{regime}")
        elif child_value < geom_value:
            issues.append(
                f"min_duration_lower_than_parent:{regime}:{child_value}s<{geom_value}s (breaks temporal inertia)"
            )

    # Check that every regime can reach normal eventually.
    states = list(geom["states"])
    graph = {state: set() for state in states}
    for src, dst in allowed:
        graph[src].add(dst)

    def has_path(start: str, target: str) -> bool:
        seen = set([start])
        queue = deque([start])
        while queue:
            node = queue.popleft()
            if node == target:
                return True
            for nxt in graph.get(node, []):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return False

    for regime in states:
        if not has_path(regime, "normal"):
            issues.append(f"no_path_to_normal:{regime}")

    return issues


def build_convergence_matrix(states: List[str], allowed: Iterable[Tuple[str, str]], min_durations: Dict[str, float]):
    n = len(states)
    index = {state: idx for idx, state in enumerate(states)}
    mat = [[math.inf for _ in range(n)] for _ in range(n)]
    for i in range(n):
        mat[i][i] = 0.0
    for src, dst in allowed:
        mat[index[src]][index[dst]] = min_durations[src]

    for k in range(n):
        for i in range(n):
            for j in range(n):
                alt = mat[i][k] + mat[k][j]
                if alt < mat[i][j]:
                    mat[i][j] = alt
    return mat, index


def format_matrix(states: List[str], mat: List[List[float]]) -> str:
    header = ["from\\to"] + states
    lines = ["\t".join(header)]
    for i, src in enumerate(states):
        row = [src]
        for j in range(len(states)):
            val = mat[i][j]
            row.append("—" if math.isinf(val) else f"{val:.0f}s")
        lines.append("\t".join(row))
    return "\n".join(lines)


def main():
    geom = load_yaml("transformation_geometry@1.yaml")
    operating = load_yaml("nova.operating@1.0.yaml")
    hysteresis_contract = load_yaml("hysteresis_decision@1.yaml")

    states, allowed, forbidden, min_durations = build_state_machine(geom)
    hysteresis_cfg = describe_hysteresis(hysteresis_contract)

    print("=== Regime State Machine ===")
    print("States:", ", ".join(states))
    print("Allowed transitions:", ", ".join(f"{a}->{b}" for a, b in allowed))
    print("Forbidden (direct):", ", ".join(f"{a}->{b}" for a, b in sorted(forbidden)))
    print("Minimum durations (s):", ", ".join(f"{k}:{int(v)}" for k, v in min_durations.items()))
    print()

    print("=== Hysteresis Rules ===")
    print(f"Minimum durations enforced per regime (seconds): {hysteresis_cfg['min_durations']}")
    print(
        f"Oscillation detection: window={hysteresis_cfg['oscillation_window_s']}s, "
        f"threshold={hysteresis_cfg['oscillation_threshold']} transitions (advisory)"
    )
    print("Decision order: same-regime -> min-duration block -> oscillation warn -> allow when satisfied")
    print()

    scenarios = [
        {
            "name": "Normal to Heightened (legal)",
            "current": "normal",
            "proposed": "heightened",
            "duration_s": 120.0,
            "now_s": 120.0,
            "history_s": [],
        },
        {
            "name": "Heightened to Controlled Degradation (blocked by hysteresis)",
            "current": "heightened",
            "proposed": "controlled_degradation",
            "duration_s": 120.0,
            "now_s": 120.0,
            "history_s": [10.0],
        },
        {
            "name": "Controlled Degradation to Emergency (legal)",
            "current": "controlled_degradation",
            "proposed": "emergency_stabilization",
            "duration_s": 700.0,
            "now_s": 700.0,
            "history_s": [50.0, 400.0],
        },
        {
            "name": "Recovery to Normal (illegal transition)",
            "current": "recovery",
            "proposed": "normal",
            "duration_s": 1900.0,
            "now_s": 1900.0,
            "history_s": [100.0, 600.0, 1200.0],
        },
        {
            "name": "Normal to Heightened with Oscillation Advisory",
            "current": "normal",
            "proposed": "heightened",
            "duration_s": 80.0,
            "now_s": 400.0,
            "history_s": [120.0, 220.0, 310.0],
        },
    ]

    print("=== Transition Simulations ===")
    for scenario in scenarios:
        result = evaluate_transition(
            scenario["current"],
            scenario["proposed"],
            scenario["duration_s"],
            scenario["now_s"],
            scenario["history_s"],
            allowed,
            forbidden,
            min_durations,
            hysteresis_cfg["oscillation_window_s"],
            hysteresis_cfg["oscillation_threshold"],
        )
        print(f"- {scenario['name']}: {result}")
    print()

    print("=== Safety Envelope Checks ===")
    envelope_issues = detect_safety_envelope_issues(geom, operating, allowed, forbidden)
    if envelope_issues:
        for issue in envelope_issues:
            print(f"- VIOLATION: {issue}")
    else:
        print("- All amplitude bounds, temporal inertia, and reachability constraints satisfied.")
    print()

    print("=== Convergence Matrix (minimum cumulative dwell time) ===")
    mat, _ = build_convergence_matrix(states, allowed, min_durations)
    print(format_matrix(states, mat))
    print()

    normal_idx = states.index("normal")
    print("Time to converge back to normal:")
    for state in states:
        src_idx = states.index(state)
        value = mat[src_idx][normal_idx]
        label = "unreachable" if math.isinf(value) else f"{value:.0f}s"
        print(f"- {state} -> normal: {label}")


if __name__ == "__main__":
    main()
