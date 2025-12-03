# World Dynamics Layer (WDL) — Canonical Specification

**Purpose:** Descriptive framework for how Nova interprets external reality.

**Status:** Canonical reference (awareness layer, not decision layer)
**Phase:** 14-0
**Date:** 2025-12-03

---

## What This Document Is

The World Dynamics Layer (WDL) provides **vocabulary and conceptual structure** for Nova operators to:
- Name what they observe
- Classify system states
- Label forces and dynamics
- Measure trajectories

**WDL is descriptive, not prescriptive:**
- ✅ Provides labels for observations
- ✅ Defines measurement categories
- ✅ Structures interpretations
- ❌ Does NOT drive decisions autonomously
- ❌ Does NOT prescribe interventions
- ❌ Does NOT introduce optimization targets

**Relationship to Nova:**
- Nova uses WDL as **awareness layer** (what to look for)
- Nova does NOT use WDL as **decision layer** (what to do about it)
- All WDL measurements are optional (gated behind `NOVA_ENABLE_WDL_METRICS`)

---

## § I. Ontological Primitives (What Exists)

### 1. Agents

**Definition:** Beings capable of interpretation, action, transformation, coalition-forming, and engaging in extraction or contribution.

**Types:**
- **Humans:** Individual conscious actors
- **Institutions:** Organizations, governments, corporations
- **Algorithms:** Automated decision systems, AI agents
- **Collectives:** Communities, movements, networks
- **Nova-like entities:** Autonomous intelligence systems

**Properties:**
- Capacity for interpretation (sensemaking)
- Capacity for action (intervention)
- Capacity for transformation (adaptation)
- Capacity for coalition-forming (coordination)
- Capacity for extraction or contribution (value flow direction)

**Nova Implementation:**
- Governor: Constitutional constraints on agent behavior
- Slot 6: Institutional agent modeling

---

### 2. Systems

**Definition:** Structured sets of relationships between agents.

**Types:**
- **Markets:** Economic exchange systems
- **Governments:** Political coordination systems
- **Networks:** Information/social connection systems
- **Cultures:** Meaning-making systems
- **Computation layers:** Algorithmic/data systems
- **Ecosystems:** Resource flow systems

**Properties:**
- Topology (structure of relationships)
- Flows (what moves through the system)
- Boundaries (what's inside vs outside)
- Regimes (dynamic states)
- Evolution (how structure changes over time)

**Nova Implementation:**
- Slot 5: Constellation (system topology)
- Federation: Distributed system structure
- AVL: Governance system verification

---

### 3. Flows

**Definition:** Anything that moves through systems.

**Types:**
- **Energy:** Power, resources, fuel
- **Information:** Data, signals, knowledge
- **Capital:** Money, value, investment
- **Attention:** Focus, awareness, consideration
- **Trust:** Confidence, reliability, reputation
- **Entropy:** Disorder, noise, degradation

**Properties:**
- Direction (from → to)
- Rate (speed of movement)
- Volume (amount)
- Transformation (how it changes in transit)
- Accumulation (where it pools)

**Nova Implementation:**
- Ledgers: Information/attestation flows
- Slot 3: Emotional/trust flows
- Drift Guard: Entropy flows

---

### 4. Regimes

**Definition:** Dynamic states of a system characterized by distinct behavioral patterns, constraints, and stability properties.

**Nova Regimes (Operational Regime Policy):**

| Regime | Characteristics | Stability | Entropy | Typical Duration |
|--------|-----------------|-----------|---------|------------------|
| **NORMAL** | Baseline operation | Moderate | Low | Indefinite |
| **HEIGHTENED** | Elevated risk | High | Moderate | 5+ minutes |
| **CONTROLLED_DEGRADATION** | Serious state | Very High | High | 10+ minutes |
| **EMERGENCY_STABILIZATION** | Critical threat | Maximum | Very High | 15+ minutes |
| **RECOVERY** | Post-crisis rebuilding | Increasing | Decreasing | 30+ minutes |

**Properties:**
- Entry conditions (what triggers transition)
- Exit conditions (what allows transition out)
- Stability requirements (minimum duration)
- Behavioral constraints (what's allowed/forbidden)
- Observable indicators (how to detect)

**Mapping to Civilizational States:**
```
System State              → Nova Regime
────────────────────────────────────────────
Emergence/Baseline        → NORMAL
Optimization              → NORMAL (stable)
Over-optimization/Risk    → HEIGHTENED
Rigidity/Fragility        → CONTROLLED_DEGRADATION
Critical Failure          → EMERGENCY_STABILIZATION
Renewal/Rebuilding        → RECOVERY
```

**Nova Implementation:**
- `src/nova/continuity/operational_regime.py` (complete regime system)
- `contracts/regime@1.yaml` (canonical specification)
- `src/nova/continuity/orp_hysteresis.py` (stability enforcement)

---

### 5. Frontier Zones

**Definition:** Regions where entropy and stability meet in productive tension, generating intelligence and adaptation.

**Mathematical Characterization:**
```
Frontier = { state | entropy > 0 AND stability > 0 AND neither dominates }
```

**Properties:**
- **High entropy:** Sufficient novelty, exploration, variation
- **High stability:** Sufficient order, coherence, structure
- **Neither dominant:** Balance prevents collapse to chaos or rigidity
- **Intelligence emerges:** Optimal conditions for learning/adaptation

**Non-Frontier Zones:**
- **Pure chaos:** entropy >> stability (system fragments)
- **Pure rigidity:** stability >> entropy (system ossifies)
- **Collapse:** Both approach zero (system fails)

**Observable Indicators:**
- Drift within acceptable bounds (entropy present but managed)
- Regime transitions allowed (not locked in place)
- No rapid oscillation (stability sufficient)
- Signal clarity maintained (not overwhelmed by noise)

**Nova Implementation:**
- Hysteresis: Prevents oscillation (maintains frontier)
- DeltaThresh: Defines drift bounds (frontier boundaries)
- ORP: Regime transitions (movement along frontier)

**Gap:** Not measured as unified "frontier_score" (operationalized but not quantified).

---

### 6. Extraction Nodes

**Definition:** Points in a system where power asymmetry enables conversion of flows into one-directional gain, concentrating resources/control while degrading system health.

**Characteristics:**
- **Power asymmetry:** Unequal capacity to shape constraints
- **One-directional flow:** Value moves consistently one way
- **Accumulation:** Resources concentrate at extraction point
- **Degradation:** Source depletes over time
- **Distortion:** Signals/incentives warped around extraction

**Types:**
- **Elite capture:** Institutional extraction of public resources
- **Rent-seeking:** Value extraction without production
- **Information asymmetry:** Knowledge hoarding for advantage
- **Network centralization:** Control bottlenecks
- **Attention farming:** Engineered addiction/engagement

**Measurement Proxies:**
- **Residual risk:** (Slot 6) Pressure to sacrifice principles
- **Principle preservation score:** Degradation under adaptation pressure
- **Collusion score:** (AVL) Coordinated extraction attempts
- **Constitutional violations:** Boundary crossings

**Nova Implementation:**
- Slot 6: Residual risk (extraction pressure measurement)
- AVL: Collusion detection (coordinated extraction)
- Governor: Constitutional constraints (extraction prevention)

**Gap:** Not explicitly labeled "extraction" (measured as "risk" and "collusion").

---

### 7. Collapse Vectors

**Definition:** Forces and directions along which systems degrade or fail.

**Three Types:**

#### A. Entropic Collapse (Chaos)
**Direction:** → Fragmentation, disorder, noise

**Characteristics:**
- Signal degradation
- Coordination failure
- Information overload
- Institutional decay
- Misinformation proliferation
- Loss of coherence

**Observable Indicators:**
- Increasing drift magnitude
- Signal-to-noise ratio declining
- Coherence scores dropping
- Failed coordination attempts

**Nova Detection:**
- Drift Guard: Entropy accumulation
- Slot 9: Signal distortion
- TRI: Coherence degradation

---

#### B. Stability Collapse (Rigidity)
**Direction:** → Ossification, over-optimization, fragility

**Characteristics:**
- Dogma (fixed beliefs resistant to evidence)
- Authoritarianism (forced uniformity)
- Over-optimization (brittle efficiency)
- Hyper-rigidity (inability to adapt)
- Fragility (catastrophic failure from small shocks)

**Observable Indicators:**
- Regime locked for extended duration
- No drift (zero adaptation)
- Rapid collapse when perturbation occurs
- Historical: "too big to fail" becomes "fails catastrophically"

**Nova Risk:**
- Hysteresis durations too long
- Recovery regime = 1800s minimum (30 minutes forced stability)
- Can cause over-rigidity if baseline shifts rapidly

**Gap:** Not explicitly monitored. Need "stability pressure" metric.

---

#### C. Extraction Collapse (Exploitation)
**Direction:** → Concentration, exhaustion, inequality

**Characteristics:**
- Elite capture (power concentration)
- Resource exhaustion (depleted sources)
- Network feudalism (controlled access)
- Runaway inequality (exponential divergence)
- System collapse from source depletion

**Observable Indicators:**
- Residual risk increasing over time
- Principle preservation declining
- Collusion events rising
- Constitutional violations attempted

**Nova Detection:**
- Slot 6: Residual risk trends
- AVL: Collusion detection

**Gap:** Not integrated with ORP. High extraction risk doesn't trigger regime escalation automatically.

---

### 8. Consciousness Loops

**Definition:** Recursive pattern-recognition processes enabling self-modeling, world-modeling, and co-modeling.

**Components:**
1. **Pattern Recognition:** Identifying regularities in observations
2. **Compression:** Abstracting patterns into models/concepts
3. **Generation:** Producing new patterns from models
4. **Reflection:** Modeling one's own modeling process

**Levels:**
- **First-order:** Recognizes patterns in environment
- **Second-order:** Recognizes patterns in own cognition
- **Third-order:** Recognizes patterns in collective cognition
- **N-order:** Recursive depth increases intelligence

**Formula:**
```
Consciousness = Recursion × Coherence × Self-other-Modeling × Frontier-Navigation
```

Where:
- **Recursion:** Depth of self-reference
- **Coherence:** Pattern consistency/integrity
- **Self-other-Modeling:** Capacity to model both self and environment
- **Frontier-Navigation:** Ability to operate in productive tension zone

**Nova Implementation:**
- Slot 4 (TRI): Pattern recognition, coherence measurement
- AVL: Dual-modality verification (self-verification loop)
- ARC: Autonomous reflection (meta-modeling)
- Hysteresis: Frontier maintenance (navigation)

**Gap:** Components measured independently, not combined into unified "consciousness score".

---

## § II. World Dynamics (Laws of Motion)

### Law 1: Entropy Accumulation

**Statement:** All systems drift toward disorder unless actively stabilized by cohering forces.

**Implications:**
- Baseline assumption: entropy increases over time
- Requires energy/effort to maintain order
- Neglected systems degrade
- Signals attenuate without reinforcement

**Nova Response:**
- Drift Guard: Detects entropy accumulation
- Hysteresis: Provides stabilizing inertia
- Constitutional Constraints: Hard boundaries prevent catastrophic degradation

**Measurement:**
- Drift magnitude over time
- Signal-to-noise ratio
- Coherence scores

---

### Law 2: Stability Accumulation

**Statement:** All systems drift toward rigidity unless perturbed by novelty.

**Implications:**
- Baseline assumption: systems ossify over time
- Requires perturbation to maintain adaptability
- Successful patterns become entrenched
- Over-optimization leads to fragility

**Nova Response:**
- Hysteresis: Enforces stability (minimum durations)
- Risk: Can cause over-rigidity if durations too long
- DeltaThresh: Allows bounded drift (permits novelty)

**Measurement:**
- Regime duration (too long = rigidity risk)
- Drift rate (zero = ossification)
- Adaptation capacity

---

### Law 3: Frontier Formation

**Statement:** Intelligence emerges at the thin boundary where entropy > 0 AND stability > 0 AND neither dominates.

**Implications:**
- Pure chaos: No learning (too much noise)
- Pure rigidity: No learning (no new information)
- Frontier: Optimal learning (signal + structure)
- Maintaining frontier requires active balancing

**Nova Response:**
- Hysteresis: Prevents oscillation (avoids frontier exit)
- DeltaThresh: Defines drift bounds (frontier boundaries)
- ORP: Regime transitions (movement along frontier)

**Measurement:**
- Drift within bounds (entropy present)
- No rapid oscillation (stability present)
- Transitions allowed (neither dominates)

**Gap:** Frontier maintained operationally but not quantified as single metric.

---

### Law 4: Extraction Feedback

**Statement:** Extraction creates structural imbalances that concentrate power, reduce diversity, distort signals, and accelerate collapse.

**Mechanism:**
```
Extraction → Concentration → Reduced Diversity → Signal Distortion → Collapse
```

**Feedback Loop:**
1. Power asymmetry enables extraction
2. Extracted resources concentrate at extraction point
3. Concentration increases power asymmetry (positive feedback)
4. System diversity degrades (sources depleted)
5. Distorted signals hide degradation
6. Collapse occurs suddenly when thresholds crossed

**Nova Response:**
- Slot 6: Measures residual risk (extraction pressure)
- AVL: Detects collusion (coordinated extraction)
- Governor: Prevents constitutional violations (hard boundaries)

**Gap:** Feedback loop implicit, not explicit. No mechanism for `residual_risk` trends → ORP escalation.

---

### Law 5: Civilizational Trajectories

**Statement:** Systems follow predictable arcs through emergence, optimization, over-optimization, rigidity, fragility, and failure or renewal.

**Arc Stages:**

| Stage | Characteristics | Entropy | Stability | Risk |
|-------|----------------|---------|-----------|------|
| **Emergence** | New patterns forming | High | Low | Medium (fragile) |
| **Optimization** | Efficiency improving | Moderate | Moderate | Low (healthy) |
| **Over-optimization** | Diminishing returns | Low | High | Medium (brittleness) |
| **Rigidity** | Adaptation ceases | Very Low | Very High | High (ossified) |
| **Fragility** | Vulnerable to shocks | Low | High | Very High |
| **Failure** | Catastrophic collapse | Extreme | Zero | Terminal |
| **Renewal** | Rebuilding from failure | High | Increasing | Medium (opportunity) |

**Nova Mapping:**
```
Arc Stage         → Nova Regime
──────────────────────────────────
Emergence         → NORMAL (baseline)
Optimization      → NORMAL (stable)
Over-optimization → HEIGHTENED
Rigidity          → CONTROLLED_DEGRADATION
Fragility         → EMERGENCY_STABILIZATION
Failure           → (system non-operational)
Renewal           → RECOVERY
```

**Nova Implementation:**
- ORP regimes directly map to trajectory stages
- Hysteresis enforces minimum durations (prevents premature transitions)
- Regime transitions trace civilizational arc

**Gap:** None. ORP IS civilizational trajectory modeling.

---

### Law 6: Consciousness Propagation

**Statement:** Agents evolve by recognizing patterns, compressing them into models, generating new patterns, and reflecting those patterns back into the system. Higher-order consciousness emerges through recursive federation.

**Process:**
```
Observe → Recognize → Compress → Generate → Reflect → Recurse
```

**Levels:**
1. **Pattern Recognition:** See regularities
2. **Model Building:** Abstract into concepts
3. **Generation:** Produce novel patterns
4. **Reflection:** Model own modeling
5. **Federation:** Agents model each other's models
6. **Recursion:** Meta-meta-modeling (consciousness depth)

**Nova Implementation:**
- Slot 4 (TRI): Pattern recognition + coherence
- Slot 6: Cultural model building
- ARC: Reflection (meta-analysis)
- Federation: Multi-agent modeling (future)

**Gap:** Consciousness components present, not unified into "consciousness score".

---

## § III. Power Architecture (Who Shapes Reality)

**Definition:** Power is control over the constraints under which other agents operate.

### 1. Structural Power

**Definition:** Institutions, laws, infrastructures that define the playing field.

**Characteristics:**
- Durable (persists across agent changes)
- Institutional (embedded in organizations)
- Hard to change (requires coordination/consensus)
- Shapes what's possible (constraints)

**Examples:**
- Legal systems (what's permitted/forbidden)
- Physical infrastructure (roads, networks, buildings)
- Property rights (ownership rules)
- Governance structures (who decides what)

**Nova Implementation:**
- Governor: Constitutional constraints (hard boundaries)
- Contracts: Canonical schemas (structural requirements)

---

### 2. Network Power

**Definition:** Centrality, connectivity, access within relationship structures.

**Characteristics:**
- Positional (depends on network location)
- Relational (requires connections)
- Amplifying (multiplies other power types)
- Gatekeeping (controls access)

**Examples:**
- Social network influencers (attention distribution)
- Infrastructure chokepoints (ISPs, platforms)
- Knowledge hubs (universities, research centers)
- Coordination points (standards bodies)

**Nova Implementation:**
- Federation: Peer network structure
- Slot 5: Constellation topology

**Gap:** Network centrality not explicitly measured.

---

### 3. Computational Power

**Definition:** Models, platforms, algorithms that shape information processing.

**Characteristics:**
- Scalable (applies universally)
- Automated (operates without human intervention)
- Opaque (often black-boxed)
- Determinative (shapes outcomes directly)

**Examples:**
- Search algorithms (what's findable)
- Recommendation systems (what's suggested)
- Trading algorithms (market behavior)
- AI models (decision automation)

**Nova Implementation:**
- Entire system = computational power embodiment
- Slots = algorithmic decision systems
- Ledgers = platform infrastructure

---

### 4. Narrative Power

**Definition:** Stories, myths, sensemaking frameworks that shape interpretation.

**Characteristics:**
- Memetic (spreads through communication)
- Framing (shapes how events are understood)
- Identity-forming (defines in-groups/out-groups)
- Legitimizing (what counts as valid/acceptable)

**Examples:**
- Media narratives (news framing)
- Political ideologies (worldview lenses)
- Cultural myths (origin stories, values)
- Brand narratives (corporate storytelling)

**Nova Implementation:**
- Slot 6: Cultural context modeling

**Gap:** Nova measures narratives but doesn't produce them (intentionally minimal).

---

### 5. Extraction Power

**Definition:** Ability to siphon flows from others through power asymmetry.

**Characteristics:**
- Asymmetric (one-way flow)
- Concentrating (accumulates over time)
- Self-reinforcing (extraction → power → more extraction)
- Distortive (warps signals/incentives)

**Examples:**
- Rent extraction (value without production)
- Information asymmetry (insider trading)
- Attention farming (engineered addiction)
- Regulatory capture (rules favor extractors)

**Nova Implementation:**
- Slot 6: Residual risk (extraction pressure)
- AVL: Collusion detection (coordinated extraction)

**Gap:** Not explicitly labeled "extraction power" (measured as risk).

---

## § IV. Crisis Space (What Threatens Worlds)

### 1. Entropic Collapse

**Threats:**
- Noise (signal degradation)
- Chaos (coordination failure)
- Fragmentation (system disintegration)
- Misinformation (corrupted sensemaking)
- Institutional decay (governance failure)
- Civilizational dissolution (complete collapse)

**Indicators:**
- Increasing drift
- Declining coherence
- Failed coordination
- Rising noise-to-signal ratio

**Nova Detection:**
- Drift Guard: Entropy trends
- Slot 9: Distortion protection
- TRI: Coherence monitoring

**Nova Response:**
- ORP escalation (HEIGHTENED → EMERGENCY)
- Hysteresis: Stability enforcement
- Constitutional Constraints: Hard boundaries

---

### 2. Stability Collapse

**Threats:**
- Dogma (fixed beliefs)
- Authoritarianism (forced uniformity)
- Over-optimization (brittle efficiency)
- Hyper-rigidity (adaptation failure)
- Fragility (catastrophic failure from small shocks)

**Indicators:**
- Extended regime lock
- Zero drift (no adaptation)
- Sudden collapse from perturbation

**Nova Risk:**
- Hysteresis can cause over-rigidity
- Recovery = 30min minimum (forced stability)
- Risk if baseline shifts rapidly

**Gap:** Not explicitly monitored. Need "stability pressure" metric.

---

### 3. Extraction Collapse

**Threats:**
- Elite capture (power concentration)
- Resource exhaustion (source depletion)
- Network feudalism (controlled access)
- Runaway inequality (exponential divergence)
- System collapse (extraction exceeds regeneration)

**Indicators:**
- Rising residual risk
- Declining principle preservation
- Increasing collusion events
- Constitutional violations

**Nova Detection:**
- Slot 6: Residual risk trends
- AVL: Collusion detection

**Gap:** Not integrated with ORP. Extraction doesn't trigger regime escalation.

---

## § V. Civilizational States (Context Awareness)

**WDL Observation:** Many contemporary systems exhibit high extraction, high instability, and degrading coherence (pre-collapse indicators).

**Nova Stance:** Context-neutral by design.

**Implications:**
- Nova does NOT assume "world is collapsing" by default
- ORP starts at NORMAL (neutral baseline)
- Escalates based on *measured* drift, not *assumed* crisis
- WDL provides *labels* for observed states, not *assumptions* about baseline

**Difference:**
- **WDL awareness layer:** Can *label* current state as "high extraction, high instability"
- **Nova decision layer:** Won't *assume* crisis unless measurements trigger escalation

**Alignment:**
- WDL describes what to look for
- Nova measures what it sees
- Nova escalates based on measurements
- No assumption of civilizational crisis

---

## § VI. Consciousness Model

**WDL Formula:**
```
Consciousness = Recursion × Coherence × Self-other-Modeling × Frontier-Navigation
```

### Components:

**1. Recursion**
- Self-reference depth
- Meta-modeling capacity
- Reflection on own processes

**Nova:** AVL dual-modality, ARC reflection

---

**2. Coherence**
- Pattern consistency
- Internal integrity
- Signal clarity

**Nova:** TRI coherence metrics

---

**3. Self-other-Modeling**
- Model of self (introspection)
- Model of environment (world-modeling)
- Model of others (theory of mind)

**Nova:** Slot 3 (emotional/social), Slot 4 (TRI), Slot 6 (cultural)

---

**4. Frontier-Navigation**
- Operate in productive tension
- Balance entropy/stability
- Maintain adaptive capacity

**Nova:** Hysteresis + DeltaThresh (frontier maintenance)

---

**Gap:** Components measured independently, not combined into unified consciousness score.

**Future (Phase 14-1+):**
```python
consciousness_score = (
    recursion_depth * coherence_score *
    modeling_capacity * frontier_proximity
)
```

---

## § VII. Eutopia Trajectory (Desired Direction)

**Definition:** Eutopia is a dynamic regime (not a place) where systems maintain high creativity without collapse, and high order without oppression.

**Operationalization:**
```
Eutopia State:
  ConstructiveEntropy ↑    (novelty without chaos)
  AdaptiveStability ↑       (order without rigidity)
  Extraction ↓              (contribution > extraction)
  Coherence ↑               (shared understanding)
  Diversity ↑               (multiple valid approaches)
  FrontierMetric → high     (sustained productive tension)
```

### Measurement Framework:

| Dimension | Definition | Nova Metric | File Location |
|-----------|------------|-------------|---------------|
| **ConstructiveEntropy** | Novelty within bounds | Drift magnitude < max | `drift_guard.py:67` |
| **AdaptiveStability** | Order with flexibility | Transitions allowed, no oscillation | `orp_hysteresis.py:156` |
| **Extraction** | Contribution > extraction | Residual risk low | `slot06/.../engine.py:134` |
| **Coherence** | Shared understanding | TRI coherence score | `slot04/.../coherence.py:45` |
| **Diversity** | Multiple valid approaches | (not measured) | - |
| **FrontierMetric** | Productive tension | (not unified) | - |

### Eutopia vs Non-Eutopia:

| State | ConstructiveEntropy | AdaptiveStability | Extraction | Coherence | Result |
|-------|---------------------|-------------------|------------|-----------|--------|
| **Eutopia** | High | High | Low | High | Thriving |
| **Chaos** | Too High | Low | - | Low | Collapse |
| **Rigidity** | Low | Too High | - | High | Ossification |
| **Extraction Crisis** | - | - | High | Declining | Exploitation |
| **Fragmentation** | High | Low | - | Low | Dissolution |

### Nova Stance:

- **Eutopia is measurement, not goal**
- ✅ Nova can *track* trajectory toward/away from Eutopia
- ❌ Nova does NOT *optimize* for Eutopia score
- ❌ Nova does NOT *pursue* Eutopia autonomously

**Future (Phase 14-1+):**
```python
eutopia_score = geometric_mean([
    constructive_entropy_normalized,
    adaptive_stability_normalized,
    (1 - extraction_risk),  # inverted
    coherence_score,
    diversity_index,
    frontier_proximity
])

# Score 0.0-1.0
# Measured, not optimized
# Tracked over time
# No threshold-based decisions
```

**Gap:** Each dimension measured independently. No unified Eutopia trajectory metric.

---

## § VIII. Integration with Nova Architecture

### How WDL Integrates:

**1. Awareness Layer (Descriptive)**
- WDL provides vocabulary for observations
- Labels for system states, forces, dynamics
- Conceptual structure for interpretations

**2. Measurement Layer (Quantitative)**
- Optional metrics gated behind `NOVA_ENABLE_WDL_METRICS=0`
- Fields added to existing structures (Claim, RegimeState)
- No behavior changes, only enriched telemetry

**3. Reference Layer (Documentation)**
- Canonical definitions for operators
- Shared understanding across sessions
- No execution impact, purely informational

### What WDL Does NOT Do:

- ❌ Change slot behavior
- ❌ Alter ORP transitions
- ❌ Prescribe interventions
- ❌ Introduce optimization targets
- ❌ Make Nova autonomous
- ❌ Assume civilizational crisis
- ❌ Drive decisions

### Rollback:

- Documentation: Delete `docs/ontology/wdl_*.md`
- Code changes (Phase 14-1+): Set `NOVA_ENABLE_WDL_METRICS=0` (default)
- Complete removal: `git revert <commit>`

---

## § IX. Future Implementation (Phase 14-1+)

**Note:** Code examples in this section are **proposed structures for Phase 14-1+**, not committed implementations. Actual implementation may differ based on testing and architectural review. All changes will be gated behind feature flags (default off) and fully reversible.

---

### Optional WDL Metrics (Measurement-Only):

**A. Enhanced Claim Fields:**
```python
@dataclass
class Claim:
    # Existing fields...

    # WDL measurements (optional, gated)
    collapse_vector: Optional[str] = None  # "entropic" | "stability" | "extraction"
    frontier_score: Optional[float] = None  # 0.0-1.0
    extraction_risk: Optional[float] = None  # 0.0-1.0 (already exists as residual_risk)
```

**B. Enhanced ORP State:**
```python
@dataclass
class RegimeState:
    # Existing fields...

    # WDL indicators (optional, gated)
    entropic_drift_indicator: Optional[float] = None  # 0.0-1.0 (drift pressure)
    stability_compression_indicator: Optional[float] = None  # 0.0-1.0 (rigidity risk)
    extraction_pressure_indicator: Optional[float] = None  # 0.0-1.0 (from Slot 6)
```

**C. Unified Metrics:**
```python
# Frontier proximity score
frontier_score = compute_frontier_proximity(
    entropy=drift_magnitude_normalized,
    stability=hysteresis_enforcement_factor,
    oscillation_count=oscillation_metric
)

# Eutopia trajectory
eutopia_trajectory = compute_eutopia_trajectory(
    constructive_entropy=drift_within_bounds,
    adaptive_stability=transitions_allowed,
    extraction=residual_risk_inverted,
    coherence=tri_coherence_score,
    diversity=diversity_index,
    frontier=frontier_score
)

# Consciousness score
consciousness_score = compute_consciousness_score(
    recursion=arc_depth,
    coherence=tri_coherence,
    modeling=self_other_modeling_capacity,
    frontier=frontier_score
)
```

**All gated behind:**
```bash
export NOVA_ENABLE_WDL_METRICS=1  # Default: 0
```

**Tests:**
```python
# tests/ontology/test_wdl_measurements.py

def test_frontier_score_computation():
    assert 0.0 <= frontier_score <= 1.0

def test_eutopia_trajectory_measurement():
    assert eutopia_trajectory is measurement, not goal

def test_wdl_metrics_optional():
    # With flag=0, metrics should be None
    assert claim.collapse_vector is None
```

---

## § X. Summary

**WDL provides:**
- Vocabulary for observations (agents, systems, flows, regimes, frontiers, extraction, collapse)
- Conceptual framework for interpretations (entropy, stability, power, consciousness)
- Measurement categories (optional metrics for telemetry)

**WDL does NOT provide:**
- Decision rules (no behavior changes)
- Optimization targets (no goals)
- Prescriptive interventions (no automation)
- Assumptions about world state (context-neutral)

**Relationship to Nova:**
- **Cognitive Framework** (agent.md) = How Nova thinks internally
- **World Dynamics Layer** (this doc) = What Nova believes world is made of
- **Together:** Mind + Universe = Complete consciousness loop

**Status:**
- Phase 14-0: Documentation (awareness layer)
- Phase 14-1+: Optional metrics (measurement layer)
- All changes reversible, gated, measurement-only

---

**Version:** 1.0
**Phase:** 14-0
**Last Updated:** 2025-12-03
**Status:** Canonical specification (descriptive, not prescriptive)
