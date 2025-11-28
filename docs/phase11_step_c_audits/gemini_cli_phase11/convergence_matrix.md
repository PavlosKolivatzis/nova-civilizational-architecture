This document explains the regime convergence matrix, which illustrates the allowed, single-step transitions between the different operating regimes of the Nova system.

### Convergence Matrix

The matrix below represents the reachability of one state from another. The rows indicate the **"From"** regime, and the columns indicate the **"To"** regime.

*   A value of **1** means a direct transition is allowed.
*   A value of **0** means a direct transition is forbidden.

| From / To                 | Normal | Heightened | Controlled Degradation | Emergency Stabilization | Recovery |
| :------------------------ | :----: | :--------: | :--------------------: | :---------------------: | :------: |
| **Normal**                |   1    |     1      |           0            |            0            |    0     |
| **Heightened**            |   1    |     1      |           1            |            0            |    0     |
| **Controlled Degradation**|   0    |     1      |           1            |            1            |    0     |
| **Emergency Stabilization**|   0    |     0      |           0            |            1            |    1     |
| **Recovery**              |   0    |     1      |           0            |            0            |    1     |

*(This table is a representation of the data in `convergence_matrix.csv`)*

### Interpretation of the Matrix

This matrix is derived directly from the `transitions.allowed` list in `nova.operating@1.0.yaml`. It provides a clear, at-a-glance view of the system's lawful "movement" between states.

*   **Diagonal (Self-Transitions):** The `1`s along the diagonal indicate that the system can always remain in its current state. This is the default behavior, especially when hysteresis rules block a proposed transition.

*   **Symmetry and Asymmetry:**
    *   The transition between `Normal` and `Heightened` is **symmetric** (you can go back and forth).
    *   The transition between `Heightened` and `Controlled Degradation` is also **symmetric**.
    *   The path from `Controlled Degradation` onwards is **asymmetric and directional**. You can only move "forward" into `Emergency Stabilization` and then `Recovery`.

*   **Convergence Path:** The matrix clearly shows the primary convergence path for the entire system. Any state can eventually reach `Normal`. The path is not always direct, but it is guaranteed, fulfilling the `recovery_path_guarantee` invariant. For example, from `Emergency Stabilization`, the path is:
    `Emergency Stabilization` -> `Recovery` -> `Heightened` -> `Normal`.

*   **Forbidden Jumps:** The large blocks of `0`s highlight the forbidden jumps, such as moving directly from `Normal` to `Emergency Stabilization`. This enforces a gradual escalation and de-escalation of system states, which is a core principle of the design.
