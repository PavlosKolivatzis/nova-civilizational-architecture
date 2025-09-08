# NOVA Architecture

NOVA's civilizational system centers on an **Orchestrator** and **Slot Loader** that coordinate ten specialized slots. External interfaces like the test framework and WebSocket adapter feed requests into the orchestrator, while each slot contributes focused capabilities such as truth anchoring, cultural synthesis, and distortion protection.

```mermaid
graph LR
  TF[Test Framework]
  WS[WebSocket Interface]
  SL[Slot Loader]
  O[Orchestrator]

  subgraph Slots
    S1[Slot01 – Truth Anchor]
    S2[Slot02 – ΔTHRESH Integration]
    S3[Slot03 – Emotional Matrix]
    S4[Slot04 – TRI Engine]
    S5[Slot05 – Constellation]
    S6[Slot06 – Cultural Synthesis]
    S7[Slot07 – Production Controls]
    S8[Slot08 – Memory Ethics]
    S9[Slot09 – Distortion Protection]
    S10[Slot10 – Civilizational Deployment]
  end

  SL --> S1
  SL --> S2
  SL --> S3
  SL --> S4
  SL --> S5
  SL --> S6
  SL --> S7
  SL --> S8
  SL --> S9
  SL --> S10

  O --> S1
  O --> S2
  O --> S3
  O --> S4
  O --> S5
  O --> S6
  O --> S7
  O --> S8
  O --> S9
  O --> S10

  TF -.-> SL
  TF -.-> O
  TF -.-> WS
  WS -.-> O
```

### Evolvable system map

The following map is generated from [`system_map.yaml`](system_map.yaml) in CI and
uses contract IDs that link to machine-readable definitions under
[`docs/contracts/`](contracts/).

```mermaid
graph LR
  subgraph "Data Plane"
    S02["S02@2.3 ΔTHRESH"]
    S04["S04@1.0 TRI Engine"]
    S05["S05@1.0 Constellation"]
    S06["S06@4.2 Cultural Synthesis"]
    S09["S09@1.0 Distortion Protection"]
    S10["S10@1.0 Deployment"]
  end

  subgraph "Control Plane"
    S03["S03@1.0 Emotional Matrix"]
    S07["S07@1.0 Production Controls"]
    O["O@1.0 Orchestrator"]
  end

  S01["S01@1.0 Truth Anchor"]
  S08["S08@1.0 Memory Ethics"]

  S02 -- "TRI_QUERY" --> S04
  S04 -- "TRI_REPORT(v1)" --> S02
  S02 -- "SIGNALS(v1) (opt)" --> S05
  S04 -- "TRI_REPORT(v1)" --> S05
  S05 -- "CONSTELLATION_STATE(v1)" --> S09
  S02 -- "CONTENT_ANALYSIS(v1)" --> S06
  S06 -- "PLAN_WITH_CONSENT(v1)" --> S10
  S03 -- "EMO_FEEDBACK(v1)" --> S07
  S07 -- "CONTROL_CMDS(v1)" --> O

  S01 -. "truth_anchor" .-> S02
  S01 -. "truth_anchor" .-> S06
  S01 -. "truth_anchor" .-> S10
  S08 -. "memory_ethics" .-> S06
  S08 -. "memory_ethics" .-> S09
  S08 -. "memory_ethics" .-> S10
```

## Slot summaries
- **Slot 1 – Truth Anchor:** core reality lock with recovery protocols.
- **Slot 2 – ΔTHRESH Integration Manager:** threshold detection and pattern analysis pipeline.
- **Slot 3 – Emotional Matrix Safety:** distributed emotional computation with safety bounds.
- **Slot 4 – TRI Engine:** advanced truth measurement with Kalman/Bayesian components.
- **Slot 5 – Constellation Navigation:** phase-space navigation anchored for failover.
- **Slot 6 – Cultural Synthesis:** multicultural adaptation engine with formal contract.
- **Slot 7 – Production Controls:** system orchestration and cross-slot coordination.
- **Slot 8 – Memory Ethics & Protection:** immutable memory safeguards and ethical boundaries.
- **Slot 9 – Distortion Protection:** infrastructure-aware detection and defense.
- **Slot 10 – Civilizational Deployment:** deployment layer wrapping Slot 6 guardrails.

## Slot maturity
| Slot | Name                         | Score | Level      |
| ---: | ---------------------------- | ----: | ---------- |
| 1    | Truth Anchor                 | 4     | Processual |
| 2    | ΔTHRESH Integration Manager  | 4     | Processual |
| 3    | Emotional Matrix Safety      | 2     | Relational |
| 4    | TRI Engine                   | 3     | Structural |
| 5    | Constellation Navigation     | 2     | Relational |
| 6    | Adaptive Synthesis Engine    | 4     | Processual |
| 7    | Production Controls          | 2     | Relational |
| 8    | Memory Lock & IDS Protection | 3     | Structural |
| 9    | Distortion Protection        | 4     | Processual |
| 10   | Deployment & Modeling        | 3     | Structural |

## How data flows
- Test Framework or WebSocket sends a request.
- Slot Loader initializes and loads all slots.
- Orchestrator routes the request to relevant slots.
- Slots process data and return results to the orchestrator.
- Orchestrator composes the final response.

## Legend
- `-->` solid arrow: contract-bound data flow.
- `-.->` dashed arrow: labeled constraint or external interaction.
- `(opt)` denotes an optional flow; `⚗️` marks experimental paths.
- Edge labels like `TRI_REPORT(v1)` map to files in `docs/contracts/`.
- Rectangles: functional components or slots.
