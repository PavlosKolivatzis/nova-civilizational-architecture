# Flow Mesh Overview – TRI, Constellation, Cultural Synthesis

**Purpose:** Clarify Nova’s **flow mesh** as a first-class architectural concept: how Slot04, Slot05, and Slot06 coordinate truth, spatial navigation, and cultural synthesis, and how other slots relate to this mesh.

This is a documentation-only summary derived from:

- `src/nova/slots/slot04_tri/README.md`  
- `src/nova/slots/slot05_constellation/README.md`  
- `src/nova/slots/slot06_cultural_synthesis/README.md`  
- `docs/# Nova Civilizational Architecture — Visual Map.md`  

---

## 1. What the Flow Mesh Is

The **flow mesh** is Nova’s internal coordination fabric for:

- Truth resonance (TRI).  
- Spatial/graph positioning (Constellation).  
- Cultural guardrails (Cultural Synthesis).  

It is **not** the entire system—rather, it is a **sub-network** of slots that exchange rich signals about structure, coherence, and culture.

---

## 2. Flow Mesh Participants

### 2.1 Active Mesh Nodes

- **Slot04 – TRI**
  - Status: **Active flow mesh participant**.  
  - Role: Central truth calculation node.  
  - Provides real-time TRI scores, drift signals, and safe-mode notifications.  
  - Flag: `NOVA_ENABLE_TRI_LINK` controls flow mesh connectivity.  

- **Slot05 – Constellation**
  - Status: **Active flow mesh participant**.  
  - Role: Central spatial navigation node.  
  - Consumes TRI scores, builds spatial/topological context (constellation), acts as a hub for flow mesh signals.  
  - Flag: `NOVA_ENABLE_TRI_LINK` controls TRI-linked mesh participation.  

- **Slot06 – Cultural Synthesis**
  - Status: **Downstream consumer** of flow mesh outputs.  
  - Role: Cultural validation gateway.  
  - Consumes flow mesh data (TRI reports, constellation state) to derive cultural readiness and guardrail decisions.  

### 2.2 Not Yet Connected to Active Flow Mesh

- **Slot01 – Truth Anchor**
  - Foundational truth reference, but **not yet wired** into the active flow mesh as a dynamic participant.  

- **Slot02 – DeltaThresh**
  - Documented as “Not connected to active flow mesh”; a specialized service that could be integrated later if needed.  

Other slots (07–10) consume outputs that may be influenced by flow mesh participants, but are not themselves part of the flow mesh’s inner loop.

---

## 3. Flow Mesh Diagram

```mermaid
flowchart LR
    subgraph FlowMesh["Flow Mesh Cluster"]
        S4[Slot04 TRI\nTruth Resonance Index]
        S5[Slot05 Constellation\nSpatial Navigation]
        S6[Slot06 Cultural Synthesis\nCultural Guardrails]
    end

    S4 <-->|TRI_REPORT@1 (TRI scores, drift)| S5
    S5 -->|Spatial context (mesh signals)| S6
    S4 -->|Safe mode / TRI health| S6

    subgraph NonMesh["Non-Mesh Core"]
        S1[Slot01 Truth Anchor\n(not in active mesh)]
        S2[Slot02 DeltaThresh\n“Not connected to active flow mesh”]
        S7[Slot07 Production Controls]
        S9[Slot09 Distortion Protection]
        S10[Slot10 Deployment]
    end

    S4 -. truth scores .-> S7
    S5 -. spatial summaries .-> S7
    S6 -. cultural readiness .-> S7

    S6 -->|Guardrail decisions| S10
    S7 -->|Governance posture| S10
```

This diagram intentionally omits low-level calls and focuses on **mesh membership** and information flow:

- Slot04 and Slot05 are central in the mesh.  
- Slot06 is a downstream consumer.  
- Slot07 and Slot10 feel the mesh indirectly (via signals), but do not participate in TRI/Constellation coordination loops.  

---

## 4. Flags & Safety

The flow mesh is **feature-flagged** to preserve safety and reversibility:

- `NOVA_ENABLE_TRI_LINK` – primary flag for Slot04/Slot05 mesh connectivity.  
  - When `"1"`: TRI + Constellation integration is active for the mesh.  
  - When `"0"`: Flow mesh behavior degrades to standalone components.  

Mesh participants are required to:

- Respect Safe Mode (e.g., TRI “safe mode” in Slot04).  
- Avoid pushing unstable signals into downstream consumers when flags indicate degraded or experimental operation.  

This document does not introduce new flags—it summarizes the current pattern so operators and agents can see how flow mesh relates to the rest of Nova.
