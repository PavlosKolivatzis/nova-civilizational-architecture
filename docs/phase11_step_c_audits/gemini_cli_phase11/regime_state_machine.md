Here is the reconstructed regime state machine based on `nova.operating@1.0.yaml`:

```mermaid
graph TD
    A[Normal] --&gt; B(Heightened);
    B --&gt; A;
    B --&gt; C(Controlled Degradation);
    C --&gt; B;
    C --&gt; D(Emergency Stabilization);
    D --&gt; E(Recovery);
    E --&gt; B;

    subgraph "Regime Details"
        A_desc("Ordinal: 0<br>Nominal operation; all continuity<br>signals within expected ranges.")
        B_desc("Ordinal: 1<br>Elevated risk; tighter thresholds<br>and mild capacity reduction.")
        C_desc("Ordinal: 2<br>Significant instability; controlled<br>capacity reduction and deployment freeze.")
        D_desc("Ordinal: 3<br>Critical instability; safe_mode bias,<br>strong damping, and hard freezes.")
        E_desc("Ordinal: 4<br>Post-emergency recovery; gradual return<br>toward normal with minimal learning.")
    end

    style A fill:#c9ffc9,stroke:#333,stroke-width:2px
    style B fill:#ffffc9,stroke:#333,stroke-width:2px
    style C fill:#ffc9c9,stroke:#333,stroke-width:2px
    style D fill:#ff9999,stroke:#333,stroke-width:2px
    style E fill:#c9c9ff,stroke:#333,stroke-width:2px

```

### State Descriptions:

*   **Normal (0):** Nominal operation. All signals are within expected ranges.
*   **Heightened (1):** Elevated risk. Thresholds are tightened, and there's a mild capacity reduction.
*   **Controlled Degradation (2):** Significant instability. Involves a controlled capacity reduction and a freeze on deployments.
*   **Emergency Stabilization (3):** Critical instability. Biases toward safe mode, with strong damping and hard freezes.
*   **Recovery (4):** Post-emergency recovery. A gradual return to normal with minimal learning.

### Allowed Transitions:

The state machine allows the following transitions:

*   `Normal` <=> `Heightened`
*   `Heightened` <=> `Controlled Degradation`
*   `Controlled Degradation` => `Emergency Stabilization`
*   `Emergency Stabilization` => `Recovery`
*   `Recovery` => `Heightened`

This completes the reconstruction of the regime state machine.
