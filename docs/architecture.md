# NOVA Architecture (Light Runtime)

```mermaid
graph LR
  %% Top controls
  TF[Test Framework]
  SL[Slot Loader]
  O[Orchestrator<br/>Core System]
  WS[WebSocket Interface]

  %% Specialized modules band
  subgraph SM[Specialized Modules]
    S10[Slot10<br/>Civilizational Deployment]
    S02[Slot02<br/>DeltaThresh]
    S03[Slot03<br/>Emotional Matrix]
    S04[Slot04<br/>Tri-Engine]
    S05[Slot05<br/>Constellation]
    S06[Slot06<br/>Cultural Synthesis]
    S07[Slot07<br/>Production Controls]
    S08[Slot08<br/>Memory Ethics]
    S09[Slot09<br/>Distortion Protection]
    S01[Slot01<br/>Truth Anchor]
  end

  %% Core analysis/synthesis
  ASE[Adaptive Synthesis Engine]
  CA[Content Analysis]

  %% Wiring
  SL --> S10 & S02 & S03 & S04 & S05 & S06 & S07 & S08 & S09 & S01
  O  --> S10 & S02 & S03 & S04 & S05 & S06 & S07 & S08 & S09 & S01

  S06 --> ASE
  ASE --> SM
  CA --> ASE

  %% External surfaces
  WS -.-> O
  TF -.-> SL
  TF -.-> O
  TF -.-> WS
```

> The **Light Runtime** adds tracing on the EventBus, a central **PerformanceMonitor**, and an **AdaptiveRouter** (with optional circuit breaker) without changing slot contracts.
