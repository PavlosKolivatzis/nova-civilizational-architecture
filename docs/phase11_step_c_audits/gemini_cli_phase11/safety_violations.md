This document outlines how to detect violations of the `global_safety_envelope` defined in `nova.operating@1.0.yaml`, using the detailed invariants from `phase11_system_invariants.md` as a reference.

A safety envelope violation occurs when one of the system's core invariants is broken. Here is a list of the violations and the methods to detect them.

### 1. Destructive Oscillation

*   **Invariant ID:** `no_destructive_oscillation`
*   **Rule:** No more than 3 regime transitions in any 300-second window.
*   **Violation:** The system changes regime 4 or more times within 300 seconds.
*   **Detection Method:**
    1.  Monitor the regime transition ledger (`src/nova/continuity/regime_transitions.jsonl`).
    2.  Maintain a rolling list of timestamps for transitions occurring in the last 300 seconds.
    3.  If the count of transitions in this window exceeds 3, a **violation** is detected.
    4.  As per `hysteresis_decision@1.yaml`, this should trigger an `oscillation_detected` warning.

### 2. Uncontrolled Acceleration

*   **Invariant ID:** `no_uncontrolled_acceleration`
*   **Rule:** Learning rate (η) cannot increase during instability (`regime.ordinal >= 1`). The `eta_multiplier` must be less than or equal to 1.0.
*   **Violation:** The `eta_multiplier` is greater than 1.0 while the system is in any regime other than `normal`.
*   **Detection Method:**
    1.  Continuously monitor the current regime and the applied `eta_multiplier`.
    2.  If `current_regime` is `heightened`, `controlled_degradation`, `emergency_stabilization`, or `recovery`, and the `eta_multiplier` is observed to be `> 1.0`, a **violation** has occurred.
    3.  This can also be checked at configuration time by inspecting the `amplitude_triad` values.

### 3. Noise Amplification

*   **Invariant ID:** `no_noise_amplification`
*   **Rule:** Detection sensitivity must not increase during instability (`regime.ordinal >= 1`). The `sensitivity_multiplier` must be greater than or equal to 1.0.
*   **Violation:** The `sensitivity_multiplier` is less than 1.0 while the system is in an unstable regime.
*   **Detection Method:**
    1.  Continuously monitor the current regime and the applied `slot09_sensitivity_multiplier`.
    2.  If `current_regime` is `heightened`, `controlled_degradation`, `emergency_stabilization`, or `recovery`, and the `sensitivity_multiplier` is observed to be `< 1.0`, a **violation** has occurred.
    3.  This can also be checked at configuration time by inspecting the `amplitude_triad` values.

### 4. Amplitude Bounds Violation

*   **Invariant ID:** `amplitude_bounds`
*   **Rule:** All core amplitude multipliers must stay within their predefined safe ranges.
*   **Violation:** One of the final scaled amplitude values falls outside its absolute bounds.
*   **Detection Method:**
    Monitor the following final values after all calculations and clamping:
    *   `eta_scaled`: Must be in `[0.25, 1.0]`. A **violation** occurs if it's outside this range.
    *   `emotion_constriction`: Must be in `[0.5, 1.0]`. A **violation** occurs if it's outside this range.
    *   `slot09_sensitivity_multiplier`: Must be in `[1.0, 1.5]`. A **violation** occurs if it's outside this range.

### 5. Temporal Inertia Violation

*   **Invariant ID:** `temporal_inertia`
*   **Rule:** Child systems cannot declare shorter minimum regime durations than the parent (`nova.operating@1.0.yaml`).
*   **Violation:** A downstream component that implements the regime logic specifies a `min_duration_s` for any regime that is less than the canonical value.
*   **Detection Method:**
    This is a configuration or static analysis check, not a runtime one.
    1.  At system startup or during a CI/CD process, audit the configuration of all subsystems that are subject to the ORP.
    2.  For each subsystem and each regime, compare its `min_duration_s` with the value in `nova.operating@1.0.yaml`.
    3.  If `min_duration_child[regime] < min_duration_operating[regime]`, a **violation** exists.

### 6. Continuity Collapse

*   **Invariant ID:** `continuity_preservation`
*   **Rule:** The Continuity Stability Index (`csi_value`) must remain within the range `[0.0, 1.0]`.
*   **Violation:** The `csi_value` is observed to be less than 0.0 or greater than 1.0.
*   **Detection Method:**
    1.  Continuously monitor the `csi_value` signal, which is referenced as `nova.frameworks.ContinuityStabilityIndex`.
    2.  If this value ever goes outside the `[0.0, 1.0]` bounds, a critical **violation** has occurred.

### 7. No Path to Recovery

*   **Invariant ID:** `recovery_path_guarantee`
*   **Rule:** Every regime must have a defined path back to the `normal` regime.
*   **Violation:** A regime exists from which it's impossible to eventually reach `normal` by following the allowed transitions.
*   **Detection Method:**
    This is a static graph analysis check on the state machine definition itself.
    1.  Construct the state transition graph from the `transitions.allowed` list.
    2.  For each regime (node) in the graph, perform a graph traversal (e.g., Breadth-First Search or Depth-First Search).
    3.  Verify that the `normal` node is reachable from every starting node.
    4.  If `normal` is not reachable from any node, a design-time **violation** exists. (Note: The current configuration satisfies this invariant).
