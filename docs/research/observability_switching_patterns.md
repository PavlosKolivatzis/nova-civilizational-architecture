# Observability Switching Patterns: Design Memory

**Status:** Research artifact, non-operational
**Purpose:** Preserve knowledge for future Nova derivatives
**Layer:** Design Memory (Layer 2) - Inert, not executable

---

## What This Document Is

This document preserves research into **observability switching patterns** in multi-agent collaborative systems. It maps the design space, identifies failure modes, and characterizes stability conditions.

**This is NOT:**
- Operational code
- A framework to implement
- Active system configuration
- Runtime logic

**This IS:**
- Epistemic infrastructure
- Knowledge preservation to prevent rediscovery
- Safety analysis for future implementations
- Activation guidance for derivatives

**The knowledge here might enable power. Therefore it is preserved in a form that cannot exercise power.**

---

## Background: The Core Discovery

Multi-agent systems can operate under different **observability patterns**:
- **Symmetric:** All agents see same expanding context
- **Asymmetric:** Agents see bounded projections

Research (see `docs/papers/asymmetric_observability_stopping.md`) demonstrated that **symmetric observability prevents reliable stopping** in consolidation tasks due to persistent drift pressure.

Nova's **unlearn pulse** mechanism enables switching from symmetric (context shared) to asymmetric (context decayed) automatically via temporal TTL expiry.

**This document explores:** What happens when you want observability patterns to adapt beyond simple time-based decay?

---

## The Switching Space: 6 Dimensions

Observability switching is not binary (symmetric vs. asymmetric). It's movement through a 6-dimensional space.

### Dimension 1: Transition Speed

**How fast does observability change?**

- **Instant:** Access flips immediately (binary on/off)
  - Pro: Clear boundary
  - Con: Coordination shock, whiplash

- **Gradual:** Access fades continuously (weighted decay)
  - Pro: Smooth adaptation
  - Con: Ambiguous "when did it switch?" moment
  - Example: Nova's exponential decay (half-life 300s)

- **Stepped:** Access changes in discrete phases
  - Pro: Predictable stages
  - Con: Complexity in defining stages

---

### Dimension 2: Trigger Mechanism

**What causes the switch?**

- **Manual:** Human-initiated decision
  - Pro: Context-aware judgment
  - Con: Requires attention, can be forgotten

- **Automatic-Temporal:** Time-based (clock-driven)
  - Pro: No coordination overhead, predictable
  - Con: Ignores actual task state
  - Example: Nova's TTL expiry

- **Automatic-State:** Condition-based (system metrics)
  - Pro: Responsive to conditions
  - Con: Can thrash if metrics noisy
  - Example: ORP regime transitions

- **Automatic-Usage:** Access-pattern based
  - Pro: Reflects actual utility
  - Con: Gaming risk (intentional access to prevent decay)

- **Hybrid:** Multiple conditions combined
  - Pro: Nuanced, harder to game
  - Con: Complex reasoning
  - Example: Nova's pulse criteria (TTL + access_count + scope)

---

### Dimension 3: Scope

**Who switches?**

- **Global:** All agents switch together
  - Pro: Synchronized, simple
  - Con: Ignores role differences

- **Role-based:** Different roles switch differently
  - Pro: Respects role boundaries
  - Con: Coordination complexity

- **Selective:** Some agents never switch (immunity list)
  - Pro: Protects critical systems
  - Con: Creates agent classes
  - Example: Nova's slot01/slot07 immunity

- **Individual:** Each agent switches independently
  - Pro: Maximum flexibility
  - Con: Potential desynchronization

---

### Dimension 4: Reversibility

**Can you switch back?**

- **One-way:** Irreversible once switched
  - Pro: Prevents re-litigation, forces progress
  - Con: Inflexible, errors costly

- **Two-way:** Can switch back and forth
  - Pro: Adaptive, recovers from mistakes
  - Con: Risk of oscillation
  - Example: Nova (context can be republished)

- **Bounded-reversible:** Limited number of reversals
  - Pro: Flexibility with forcing function
  - Con: Arbitrary limits

- **Hysteresis:** Different thresholds for A→B vs. B→A
  - Pro: Prevents thrashing, stability bias
  - Con: Can get stuck in suboptimal state
  - Example: ORP regime transitions

---

### Dimension 5: Information Fate

**What happens to old context?**

- **Deletion:** Context destroyed, unrecoverable
  - Pro: True forgetting, no leakage
  - Con: Cannot recover if needed

- **Decay:** Context persists but weight → 0
  - Pro: Gradual, reversible, no data loss
  - Con: "Zombie context" still present
  - Example: Nova's exponential decay

- **Archival:** Moved to cold storage
  - Pro: Recoverable, audit trail
  - Con: Two-tier complexity

- **Projection:** Context exists, view filtered
  - Pro: No data movement, instant switching
  - Con: Not true forgetting

---

### Dimension 6: Coordination

**How do agents learn about switch?**

- **Broadcast:** Central announcement
  - Pro: Synchronized, simple
  - Con: Single point of failure

- **Signal:** Event emission, agents subscribe
  - Pro: Decoupled, agents choose response
  - Con: No guarantee of receipt
  - Example: Nova's UNLEARN_PULSE fanout

- **Gossip:** Peer-to-peer propagation
  - Pro: Resilient, no central coordinator
  - Con: Slow, eventual consistency

- **Implicit:** Discovered through behavior
  - Pro: No coordination overhead
  - Con: Confusion, error-prone

---

## Forbidden Trajectories: Guaranteed Failure Modes

Certain paths through the switching space reliably cause drift, thrashing, or brittleness.

### Class 1: Symmetry Leak After Asymmetry

**Trajectory:** Enter bounded observability, then reintroduce implementation visibility to oversight roles.

**Movement:** Projection → raw access, or Scope: Selective → Global

**Why it fails:** Once "adjacent improvements" re-enter action space, drift pressure returns.

**Tell:** Phrases like "let's just take a quick look to confirm."

**Rule:** Once in stopping mode, cannot re-open implementation space for stopping roles.

---

### Class 2: Trigger Becomes Strategically Gameable ⚠️

**Trajectory:** Trigger moves toward Usage-based or includes agent-influenceable terms.

**Movement:** Temporal/State → Usage/Hybrid with agent-controllable inputs

**Why it fails:** Agents discover they can keep context alive by touching it. "Keep-alive" behavior emerges.

**Examples:**
- "High access_count extends TTL" → agents ping to prevent expiry
- "Activity prevents phase transition" → agents create fake work
- "Context creation rate triggers protection" → pollution attack

**The core failure:** Trigger becomes a control surface, reintroducing gradients.

**Test:** "Can an agent who wants to prevent stopping extend context lifetime through task actions?"
- If yes: Class 2 violation

**Critical distinction:**
- **Filter (safe):** Usage decides *whether* to emit signal
- **Actuator (unsafe):** Usage decides *if* context persists

**Rule:** Usage is safe only as one-way filter, never as two-way actuator.

---

### Class 3: Two-Way Switching Without Hysteresis

**Trajectory:** Reversibility set to Two-way with symmetric thresholds and state-based trigger.

**Movement:** One-way/Hysteresis → Two-way + State-trigger + no damping

**Why it fails:** Noise near thresholds causes switch-thrashing. System pays transition costs instead of converging.

**Tell:** Repeated "enter review / exit review / enter review" cycles.

**Rule:** If you allow reversal, need hysteresis or bounded reversals.

---

### Class 4: Instant Global Cutoff Without Checkpoint

**Trajectory:** Speed goes Instant + Scope goes Global without replacement boundary object.

**Movement:** Gradual/Stepped → Instant AND Selective → Global

**Why it fails:** Coordination shock + blind critique. Shadow channels emerge to recreate symmetry informally.

**Tell:** DMs, undocumented summaries circulate.

**Rule:** Instant switching stable only if replacement object exists (checkpoint/contract/invariant).

---

### Class 5: Projection-Only "Asymmetry" With Remembered Raw Details

**Trajectory:** Information Fate moves to Projection but agents already had raw access earlier.

**Movement:** Symmetric → Projection-based with same agents retained

**Why it fails:** Memory keeps gradients alive. Agents reason over hidden details anyway.

**Tell:** Critique references specifics "no longer visible."

**Rule:** Projection-based switching stable only if (a) critic never had raw access, or (b) critic role swapped.

---

### Class 6: Authority-Coupled Decay ⚠️

**Trajectory:** Decay signal starts driving governance decisions or outcomes directly.

**Movement:** Coordination: Signal (advisory) → enforcement; decay controls routing/blocking

**Why it fails:** Decay becomes political tool ("expire context to win"). Drift re-enters as power optimization.

**Examples:**
- "If context expired, critic must approve" → decay decides outcomes
- "Route to fast path if no contexts active" → decay controls behavior
- "High pulse rate → escalate regime" → pulse emission becomes power

**Test:** "Does decay timing or pulse emission directly change what system allows/blocks/routes?"
- If yes: Class 6 violation

**Rule:** Decay must remain in information layer, never cross to decision layer.

**Safe:** Decay adjusts weights (receiver-local), logged for observability
**Unsafe:** Decay blocks actions, drives regime, determines routing

---

### Class 7: Individual-Only Switching in Tightly Coupled Collaboration

**Trajectory:** Scope drifts to Individual while work remains interdependent.

**Movement:** Global/Role-based → Individual

**Why it fails:** Desynchronized reality. Agents reason from different "current states." Coordination fails or forces resynchronization (restores symmetry).

**Tell:** "Wait, I thought we agreed that was expired" disagreements.

**Rule:** Individual switching safe only when tasks are decomposable or coordination objects strongly shared.

---

## The Forbidden Triangle

**Combining these three is catastrophic:**
1. Two-way reversibility
2. State/Usage triggers (especially gameable)
3. No hysteresis / no checkpoint object

**Result:** Oscillation + gaming + no convergence

---

## Stability Basin: Why Nova's Unlearn Pulse Succeeds

Nova's design occupies a **locally stable basin** in the switching space where:
- No positive feedback loops keep context alive indefinitely
- No oscillation under noise (thrash-resistant)
- No brittle failures forcing shadow channels

**Achieved through 4 interlocking stability locks.**

### Lock 1: Exogenous Time as Primary Driver

**Design:** TTL expiry is wall-clock driven

**Property:** **Monotonicity** — expiry always approaches, agents can't negotiate

**Prevents:** Class 2 gaming, Class 3 thrash

**Basin edge:** If time replaced with agent-influenceable metrics → fall off cliff

---

### Lock 2: Usage Only Gates Emission, Never Extends

**Design:** `access_count` decides *whether* pulse emits, not *if* context persists

**Property:** **One-way coupling** — usage can't increase future availability

**Critical distinction:**
```python
# SAFE (filter)
should_emit = (access_count > 1) and (age > ttl)

# UNSAFE (actuator)
if access_count > threshold:
    ttl_extended = ttl * 1.5  # Gaming vector!
```

**Prevents:** Direct gaming loops ("ping to keep alive")

**Basin edge:** Moment usage extends lifetime → Class 2 violation

---

### Lock 3: Decay is Continuous and Local

**Design:** Exponential decay on receiver side, per-context half-life

**Property:** **Smoothness** — weights fade gradually, not snap

**Prevents:** Class 4 coordination shock, Class 7 desynchronization

**Why local matters:** Only consuming slot's weights change, not global mode flip

**Basin edge:** If switched to instant global revocation → coordination fails

---

### Lock 4: Advisory Signal + Receiver Autonomy

**Design:** Pulse emitted, receivers choose how to respond

**Property:** **Non-coercion** — signal doesn't directly decide outcomes

**Prevents:** Class 6 authority coupling

**Why advisory matters:** If pulse were enforcement, becomes political battleground

**Basin edge:** If pulse controls routing/authority → Class 6 violation

---

### The Immunity Anchor

**Design:** slot01 (Truth Anchor) and slot07 (Production Controls) never receive pulses

**Why this helps:**
- Fixed reference points prevent system dissolution
- Core systems stay stable while periphery adapts

**Safety condition:** Immune components must not export rich details back to bounded roles (else Class 1 leak)

---

## The Basin Test (Reusable)

**Four questions to check if change stays in-basin:**

| Question | Safe Answer | Unsafe Answer |
|----------|-------------|---------------|
| **1. Monotone expiry** | Context inevitably ages out | Agent actions prevent expiry |
| **2. No survivability actuation** | Behavior can't extend lifetime | Behavior extends/refreshes TTL |
| **3. Smooth decay** | Influence is continuous | Hard flip, instant cutoff |
| **4. Non-coercive** | Decay signals, doesn't decide | Decay drives governance/routing |

**All four must be "safe" to stay in basin.**

---

## The Basin Cliff (Most Dangerous Perturbation)

**Steepest edge:** Any change letting agents increase context lifetime via task actions.

**Examples that fall off:**
- "High access_count extends TTL"
- "Agent can refresh to same key"
- "Activity prevents phase shift to fast-decay"

**Why steep:** Once agents influence decay → decay becomes control surface → gradients flow backward → stopping fails

**This is the single most catastrophic perturbation.**

---

## Adaptive TTL: Constraints for Safe Implementation

**Adaptive TTL means:** Decay rate changes based on system state (not fixed 300s).

**Goal:** Context lifetime varies by phase (discovery vs. consolidation), risk level, or system health.

**Challenge:** Must stay in stability basin while adapting.

### What Must Be Preserved (The 4 Locks)

1. **Exogenous primary trigger** — Time remains un-influenceable by agents
2. **Usage as filter only** — Never as lifetime extender
3. **Continuous decay** — No instant global flips
4. **Advisory signals** — No enforcement or authority coupling

### Safe Modulation Targets

**CAN safely change:**
- **Half-life rate** based on external system state (ORP regime, deployment phase)
- **Base TTL** based on context scope/type (not agent behavior)
- **Emission threshold** based on static criteria (TTL minimum, access floor)

**CANNOT safely change:**
- Letting agents extend lifetime (Class 2)
- Coupling decay to governance (Class 6)
- Making trigger gameable (Class 2)

### Example Safe Design

```python
# External phase (set by coordinator, NOT inferred from agents)
phase = read_external_phase_flag()  # Must be exogenous

# Base TTL (still time-driven)
base_ttl = 300.0

# Phase multipliers (change decay RATE, not extension)
phase_multipliers = {
    "discovery": 2.0,        # Slower decay early
    "consolidation": 0.5     # Faster decay when stopping
}

# Effective TTL (still monotone, still exogenous)
effective_ttl = base_ttl * phase_multipliers[phase]

# Usage STILL filter-only (not actuator)
should_emit = (access_count > 1) and (age > effective_ttl)
```

**Key safety properties:**
- Phase is external (not agent-influenced) ✓
- Multiplier changes rate, doesn't extend ✓
- Usage remains filter (should_emit), not actuator ✓
- Time still drives expiry ✓

**This stays in basin.**

### Example Unsafe Design

```python
# UNSAFE - Class 2 violation
if access_count > HIGH_USAGE_THRESHOLD:
    effective_ttl = base_ttl * 2.0  # Agents can game by pinging

# UNSAFE - Class 6 violation
if context_expired:
    routing_decision = "fast_path"  # Decay controls outcomes
```

---

## Safe Signals vs. Unsafe Signals

**Safe (exogenous or orthogonal to agent actions):**
- Wall-clock time ✓
- External phase declarations (set by coordinator) ✓
- System health from independent sources ✓
- Deployment cycles ✓

**Unsafe (agent-influenced):**
- Access counts that extend lifetime ✗
- Activity levels that prevent phase transitions ✗
- Self-reported "still working" flags ✗
- Inferred phases based on agent behavior ✗

**The filter/actuator distinction:**
- **Filter:** Signal used to decide whether to act (safe as input)
- **Actuator:** Signal used to extend/control lifetime (unsafe, creates gaming)

---

## Re-Entry Checklist: Layer 2 → Layer 3 Promotion

**If future Nova derivative wants to implement adaptive TTL:**

### Phase 1: Justification
- [ ] Why is static TTL insufficient?
- [ ] What problem does adaptation solve?
- [ ] Is this real need or optimization theater?

### Phase 2: Design
- [ ] Which dimensions of switching space will change?
- [ ] Which forbidden trajectories does this approach?
- [ ] How are all 4 stability locks preserved?
- [ ] Diagram trajectory through space

### Phase 3: Safety Verification
- [ ] Basin test: All 4 questions = safe?
- [ ] Class 2 check: Can agents extend lifetime via task actions?
- [ ] Class 6 check: Does decay drive authority/routing/governance?
- [ ] Gaming vector analysis: What can agents exploit?
- [ ] Identify closest forbidden class

### Phase 4: Implementation
- [ ] External trigger source confirmed exogenous?
- [ ] Filter vs. actuator distinction preserved?
- [ ] Receiver autonomy maintained (advisory signals)?
- [ ] Rollback strategy defined?
- [ ] Flag-gated (default off)?

### Phase 5: Validation
- [ ] Empirical test: Does stopping still succeed?
- [ ] Counterfactual: Would gaming appear under pressure?
- [ ] Monitoring: How detect drift if emerges?
- [ ] False-alarm rate: Does adaptation thrash?

**Only after all checks pass → proceed to Layer 3 activation.**

---

## The Generalized Principle

> **Knowledge that might enable power must be preserved only in forms that cannot exercise power.**

**Adaptive TTL might enable:**
- Gaming (if poorly designed)
- Authority coupling (if decay drives decisions)
- Drift (if agents can influence)

**Therefore it must stay:**
- **Documented** (this Layer 2 document)
- **Inert** (no runtime hooks)
- **External** (not in operational code)
- **Deliberate to activate** (requires conscious design decision + checklist)

**This is not losing knowledge. This is placing it where it can't hurt you.**

---

## Nova's Position in the Space

**Current configuration:**

| Dimension | Nova's Position | Properties |
|-----------|-----------------|------------|
| Speed | Gradual | Exponential decay, half-life 300s |
| Trigger | Hybrid | Temporal (TTL) + Usage (access_count filter) + Scope |
| Scope | Selective | Role-based with immunity (slot01, slot07) |
| Reversibility | Two-way | Context can be republished (new entry) |
| Information Fate | Decay | Weights fade, data persists |
| Coordination | Signal | UNLEARN_PULSE@1 emission, fanout subscription |

**Why this is stable:**
- Sits in middle ground (no extremes)
- All 4 locks engaged
- Avoids all 7 forbidden classes
- Small perturbations safe, but Class 2 cliff exists

**Perturbation analysis:**
- Change half-life 300s → 600s: Still safe (monotone, exogenous) ✓
- Add emission criteria: Still safe (if filter-only) ✓
- Let agents extend lifetime: UNSAFE, Class 2 violation immediately ✗

---

## References

- **Asymmetric Observability Enables Stopping:** `docs/papers/asymmetric_observability_stopping.md`
- **Nova Unlearn Pulse Implementation:** `docs/unlearn_pulse_flow.md`
- **Federation Peer Sync (switching example):** `docs/federation_peer_sync.md`
- **ORP Regime Transitions (state-based switching):** `docs/phase11_stability_loop.md`

---

## Document Status

**Layer:** Design Memory (Layer 2)
**Operational Status:** Non-executable
**Purpose:** Knowledge preservation for future derivatives
**Activation:** Requires conscious Layer 2 → Layer 3 promotion via re-entry checklist

**This document cannot execute. It can only inform.**
