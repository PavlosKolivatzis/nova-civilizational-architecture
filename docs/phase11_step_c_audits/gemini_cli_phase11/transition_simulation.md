Here is a simulation of legal and illegal regime transitions based on the reconstructed state machine and hysteresis rules.

The simulation is presented as a timeline of events, showing how the system state evolves and how the rules are applied.

### Scenario: A complete cycle from Normal to Recovery and back

This scenario illustrates a sequence of valid transitions, starting from a stable state, degrading to an emergency, and then recovering.

| Time (s) | Current Regime            | Proposed Regime           | Duration in Regime (s) | Min Duration (s) | Allowed? | Reason                                                              | **Effective Regime**      |
| :------- | :------------------------ | :------------------------ | :--------------------- | :--------------- | :------- | :------------------------------------------------------------------ | :------------------------ |
| 0        | `normal`                  | `heightened`              | 120                    | 60               | ✅ Yes   | Minimum duration met (`120s >= 60s`). Triggered by elevated risk.  | `heightened`              |
| 120      | `heightened`              | `controlled_degradation`  | 350                    | 300              | ✅ Yes   | Minimum duration met (`350s >= 300s`). Risk increased further.     | `controlled_degradation`  |
| 470      | `controlled_degradation`  | `emergency_stabilization` | 700                    | 600              | ✅ Yes   | Minimum duration met (`700s >= 600s`). Critical instability.       | `emergency_stabilization` |
| 1170     | `emergency_stabilization` | `recovery`                | 1000                   | 900              | ✅ Yes   | Minimum duration met (`1000s >= 900s`). Stabilization successful. | `recovery`                |
| 2170     | `recovery`                | `heightened`              | 2000                   | 1800             | ✅ Yes   | Minimum duration met (`2000s >= 1800s`). Recovery complete.       | `heightened`              |
| 4170     | `heightened`              | `normal`                  | 310                    | 300              | ✅ Yes   | Minimum duration met (`310s >= 300s`). System returned to normal.  | `normal`                  |

---

### Illegal Transition Examples

These examples show transitions that would be blocked by the system's rules.

#### Example 1: Directly Forbidden Transition

The system attempts to jump from `normal` directly to `emergency_stabilization`, which is forbidden.

| Time (s) | Current Regime | Proposed Regime           | Duration in Regime (s) | Min Duration (s) | Allowed? | Reason                                                      | **Effective Regime** |
| :------- | :------------- | :------------------------ | :--------------------- | :--------------- | :------- | :---------------------------------------------------------- | :------------------- |
| 0        | `normal`       | `emergency_stabilization` | 500                    | 60               | ❌ No    | **Forbidden direct transition** (`normal` -> `emergency_stabilization`). | `normal`             |

#### Example 2: Hysteresis Violation (Minimum Duration)

The system is in the `heightened` state, and conditions improve, suggesting a return to `normal`. However, the transition is proposed too early.

| Time (s) | Current Regime | Proposed Regime | Duration in Regime (s) | Min Duration (s) | Allowed? | Reason                                                   | **Effective Regime** |
| :------- | :------------- | :-------------- | :--------------------- | :--------------- | :------- | :------------------------------------------------------- | :------------------- |
| 0        | `heightened`   | `normal`        | 120                    | 300              | ❌ No    | **Hysteresis Block:** Minimum duration not met (`120s < 300s`). | `heightened`         |

The system remains in the `heightened` state. The transition to `normal` would only be allowed after spending at least 300 seconds in the `heightened` state.

#### Example 3: Oscillation Warning

This example shows a series of rapid (but allowed) transitions that trigger the oscillation warning.

| Time (s) | Event                                    | Transitions in last 300s | Warning?                                | Note                                                              |
| :------- | :--------------------------------------- | :----------------------- | :-------------------------------------- | :---------------------------------------------------------------- |
| 0        | Transition `normal` -> `heightened`      | 1                        | No                                      |                                                                   |
| 65       | Transition `heightened` -> `normal`      | 2                        | No                                      | System is flapping, but still within limits.                      |
| 130      | Transition `normal` -> `heightened`      | **3**                    | ✅ **Yes** (Oscillation Detected) | The transition is **allowed**, but a warning is logged.           |
| 195      | Transition `heightened` -> `normal`      | **4**                    | ✅ **Yes** (Oscillation Detected) | Another warning. The system is unstable. The transitions are allowed. |

Even though the transitions are allowed because the minimum duration for `normal` (60s) is met each time, the high frequency triggers the advisory warning.
