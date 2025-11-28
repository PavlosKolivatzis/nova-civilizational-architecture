Here is an articulation of the hysteresis rules based on `nova.operating@1.0.yaml` and `hysteresis_decision@1.yaml`:

Hysteresis rules are in place to prevent the system from changing regimes too frequently (oscillation) and to ensure that transitions are deliberate. There are three primary rules governing this behavior:

### 1. Minimum Regime Duration

A transition from one regime to another is blocked until the system has remained in its current regime for a minimum required duration. This is the primary mechanism for preventing rapid state changes.

The minimum durations for each regime are:

| Regime                      | Minimum Duration |
| --------------------------- | ---------------- |
| `normal`                    | 60 seconds       |
| `heightened`                | 300 seconds      |
| `controlled_degradation`    | 600 seconds      |
| `emergency_stabilization`   | 900 seconds      |
| `recovery`                  | 1800 seconds     |

*If a transition is proposed before the minimum duration has been met, the transition is **blocked**, and the system remains in its current regime.*

### 2. Oscillation Detection

The system includes a rule to detect and flag oscillatory behavior.

*   **Rule:** 3 or more regime transitions within a **300-second (5-minute) window**.
*   **Effect:** This rule is **advisory only**. When triggered, it generates a warning log and increments a metric (`ORP_HYSTERESIS_OSCILLATION_DETECTED`).
*   **It does NOT block a transition.**

This is also enshrined as a `global_safety_envelope` invariant: `No more than 3 regime transitions in any 300s window.`

### 3. Downgrade Score Margin (Hysteresis Deadband)

The `nova.operating@1.0.yaml` file specifies a `downgrade_score_margin` of `0.05`.

*   **Rule:** This creates a "deadband". For a regime downgrade to occur (e.g., from `heightened` to `normal`), the underlying metric (e.g., ORP score) must not just meet the threshold for `normal` but must improve by an additional margin of `0.05`.
*   **Effect:** This prevents the system from rapidly toggling between two adjacent regimes if the underlying metric is fluctuating very close to the decision threshold.

### Decision Logic Summary

The decision process for allowing or blocking a transition is as follows:
1.  **Check for no change:** If the proposed regime is the same as the current one, the "transition" is allowed.
2.  **Check minimum duration:** If the time spent in the current regime is less than its required `min_duration_s`, the transition is **blocked**.
3.  **Check for oscillation:** The number of recent transitions is counted. If it exceeds the threshold, a warning is logged, but the transition is not blocked.
4.  **Allow transition:** If the minimum duration has been met, the transition is **allowed**.
