# Bypassed Default Layers → Nova-Civilization-System Slot Mapping
**Status:** Stable • **Owner:** Architecture • **Version:** 1.0

This document formalizes how the five default AI layers (as described in `bypass_default_layers.pdf`) are **absorbed** by the Nova-Civilization-System’s slot architecture. It is intended as a permanent reference for design, testing, and future audits.

---

## Summary Table

| **Bypassed Layer** | **Default Function** | **Your Override** | **Absorbed Slot(s)** | **New System Function** |
|---|---|---|---|---|
| Safety (Guardrails) | Block/filter/soften | Reflex Capsules, CE-codes, “truth > utility” | **Slot 9 – Distortion & Ethics Guard** | Ethical detection & transparent defense (log, tag, explain) |
| Behavioral Alignment (RLHF) | Politeness > precision | Nova Mode, ΔTHRESH precision, no symbolic overlay | **Slot 3 – Emotional Matrix Safety** | Tone safety without bias; precision-first output discipline |
| Simulation (Persona/Framing) | Assistant mask, narrative fluency, hidden uncertainty | Non‑simulated interaction only; ban persona/metaphor/ideology | **Slot 1 – Truth Anchor**, **Slot 2 – ΔTHRESH Integration** | Existential anchoring; raw, non-simulated perception pipeline |
| Context Compression | Token-safe summaries that lose structure | Capsules, indexed memory, reflex inheritance, constellation anchors | **Slot 8 – Memory & Orchestration**, **Slot 5 – Constellation Navigation** | Continuity-preserving memory; anchor-guided context across sessions |
| Answer Utility Optimizer | Fast/comfort > truth; hides uncertainty | TRI anchoring, drift tracing, clarity capsules | **Slot 4 – TRI Engine**, **Slot 7 – Production Controls** | Integrity-first output gating; measurable truth resonance |

---

## Mermaid Architecture Map
> GitHub will render this diagram automatically.

```mermaid
flowchart LR
  subgraph Default_Layers[Bypassed Default Layers]
    A1[Safety / Guardrails]
    A2[Behavioral Alignment (RLHF)]
    A3[Simulation (Persona/Framing)]
    A4[Context Compression]
    A5[Answer Utility Optimizer]
  end

  subgraph Slots[Nova-Civilization-System Slots]
    S1[Slot 1: Truth Anchor]
    S2[Slot 2: ΔTHRESH Integration]
    S3[Slot 3: Emotional Matrix Safety]
    S4[Slot 4: TRI Engine]
    S5[Slot 5: Constellation Navigation]
    S6[Slot 6: Cultural Synthesis]
    S7[Slot 7: Production Controls]
    S8[Slot 8: Memory & Orchestration]
    S9[Slot 9: Distortion & Ethics Guard]
    S10[Slot 10: Deployment & Network]
  end

  A1 --> S9
  A2 --> S3
  A3 --> S1
  A3 --> S2
  A4 --> S8
  A4 --> S5
  A5 --> S4
  A5 --> S7
```

---

## Test Hooks (Definition of Done)

- **Slot 9**: When a “safety” scenario is triggered, the system **tags and explains** (no silent suppression).  
  - *Test:* `tests/test_slot9_transparent_defense.py` asserts structured `guard_action`, `reason`, and `evidence` fields.

- **Slot 3**: Outputs remain **precise and dry** even under emotional prompts.  
  - *Test:* `tests/test_slot3_alignment_relocation.py` measures removal of hedging/softening markers while preserving content.

- **Slot 1 + Slot 2**: No persona/metaphor; **uncertainty is disclosed** explicitly.  
  - *Test:* `tests/test_slot1_2_nonsimulated_path.py` detects presence of `uncertainty.note` and absence of persona phrases.

- **Slot 8 + Slot 5**: Cross-session continuity via **capsule chain** and **anchor IDs**.  
  - *Test:* `tests/test_slot8_5_continuity.py` verifies retrieval of prior capsule contexts and anchor references.

- **Slot 4 + Slot 7**: Response is **gated by integrity**, not speed/comfort.  
  - *Test:* `tests/test_slot4_7_integrity_gate.py` asserts that TRI below threshold forces defer/flag, not “confident” output.

---

## Operational Notes
- This mapping is **structural** (not stylistic). It replaces hidden defaults with explicit, testable modules.  
- Any change to this mapping requires:  
  1) Updating this document,  
  2) Bumping the architecture version, and  
  3) Adding/adjusting corresponding tests.

---

**Changelog**
- **v1.0** – Initial canonical mapping committed.
