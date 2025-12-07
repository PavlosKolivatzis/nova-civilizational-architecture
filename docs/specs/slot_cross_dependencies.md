# Slot Cross-Dependencies – Cognitive & Contract Topology

**Purpose:** Provide a clear visual of how Nova slots depend on each other via contracts and cognitive flows, without changing runtime behavior.

This document complements `TREE.md`, `docs/NAVIGATION.md`, and individual `README.md` files by making cross-slot wiring explicit.

---

## 1. High-Level Slot Dependency Graph

The diagram below focuses on **cognitive dependencies** and contract flows, not every implementation detail.

```mermaid
flowchart LR
    subgraph CoreSlots["Nova Core Slots"]
        S1[Slot01 Truth Anchor]
        S2[Slot02 DeltaThresh]
        S3[Slot03 Emotional Matrix]
        S4[Slot04 TRI]
        S5[Slot05 Constellation]
        S6[Slot06 Cultural Synthesis]
        S7[Slot07 Production Controls]
        S8[Slot08 Memory Ethics]
        S9[Slot09 Distortion Protection]
        S10[Slot10 Civilizational Deployment]
    end

    %% Slot02 outputs
    S2 -->|BIAS_REPORT@1 (bias_vector, C_inst, graph_state)| S7
    S2 -->|BIAS_REPORT@1 + VOID state| S9
    S2 -. optional .->|temporal_usm@1 (H_t, rho_t, C_t)| S7

    %% Truth Anchor
    S1 -->|QualityOracle\n(ACCEPT/REJECT)| S7
    S1 -->|Truth anchors / attestations| S9

    %% TRI / Constellation / Flow Mesh
    S4 -->|TRI scores / TRI_REPORT@1| S5
    S5 -->|Spatial context / mesh signals| S6

    %% Governance and distortion
    S6 -->|Cultural guardrail signals| S7
    S7 -->|Flags / routing / gating decisions| S9
    S9 -->|Distortion verdicts / bypass signals| S1

    %% Deployment
    S7 -->|Production posture| S10
    S6 -->|Cultural readiness| S10
```

Key points:

- Slot02 is the **structural & temporal analyzer** (USM, VOID, temporal USM).  
- Slot07 is the **governance hub**, consuming bias reports (and later temporal signals) plus cultural signals.  
- Slot09 is the **distortion protection layer**, heavily informed by VOID.  
- Slot04–05–06 form a **truth/spatial/cultural chain** that informs production and deployment.  

---

## 2. Roles by Slot (Dependency-Oriented)

This is a dependency-focused view (who depends on whom conceptually):

- **Slot01 – Truth Anchor**
  - Trusted source for quality judgments and attestations.  
  - Supplies validation to Slot07 and truth anchors to Slot09.  

- **Slot02 – DeltaThresh**
  - Produces:
    - `BIAS_REPORT@1` (structural bias + collapse score + graph_state).  
    - `temporal_usm@1` (per-stream temporal USM; Phase 14.5).  
  - Direct dependencies:
    - Slot07 (governance decisions).  
    - Slot09 (distortion bypass and risk assessment).  

- **Slot03 – Emotional Matrix**
  - Provides emotional/cognitive framing but is not currently a primary dependency in the USM/VOID/temporal chain.  

- **Slot04 – TRI**
  - Truth Resonance Index engine.  
  - Feeds Slot05 (Constellation) and, via flow mesh, downstream consumers.  

- **Slot05 – Constellation**
  - Spatial navigation / topology node.  
  - Consumes TRI scores; informs Slot06 about where in “cognitive space” events sit.  

- **Slot06 – Cultural Synthesis**
  - Cultural guardrail + adaptation.  
  - Consumes flow mesh outputs (TRI + constellation) and emits cultural readiness to Slot07/Slot10.  

- **Slot07 – Production Controls**
  - Governance loop: orchestrates generator → analyzer (Slot02) → oracle (Slot01) → attestor (Core).  
  - Consumes:
    - Instantaneous USM (BIAS_REPORT@1).  
    - VOID semantics.  
    - Quality oracle decisions.  
    - (Future) temporal USM from `temporal_usm@1` under `NOVA_ENABLE_TEMPORAL_GOVERNANCE`.  

- **Slot08 – Memory Ethics**
  - Manages access controls and ethical memory boundaries.  

- **Slot09 – Distortion Protection**
  - Protects against manipulative / distorted input.  
  - Consumes:
    - VOID state (to bypass when appropriate).  
    - BIAS_REPORT-derived signals.  
    - Governance posture from Slot07.  

- **Slot10 – Civilizational Deployment**
  - Final deployment gate, combining:
    - Truth stability (Slot01/Slot04).  
    - Cultural readiness (Slot06).  
    - Governance posture (Slot07).  

This document is descriptive only and reflects the current conceptual wiring. Runtime connections are always subject to feature flags and the invariants in `.claude/agent.md` and `docs/MISSION.md`.
