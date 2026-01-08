# Asymmetric Observability Enables Stopping in Multi-Agent Collaboration

## Abstract

Multi-agent and human-AI collaborative systems typically optimize for shared context and information symmetry, operating under the assumption that more accessible information leads to better decision-making and coordination. We present evidence that contradicts this intuition: in complex collaborative tasks requiring architectural consolidation, symmetric access to implementation context systematically prevents systems from reaching stable stopping points, instead creating persistent drift pressure toward scope expansion and boundary erosion.

Through a structured case study of a multi-agent collaboration on a complex, safety-constrained software system, we demonstrate that **intentionally frozen asymmetric observability**—where critique agents access only abstract principles while implementation agents access only local task context—enables reliable convergence where symmetric designs fail. We provide formal interpretation through three independent lenses: control theory (asymmetric observability eliminates control surface interference), mechanism design (asymmetry creates stopping as Nash equilibrium rather than requiring sustained discipline), and information theory (bounded context reduces entropy of adjacent possibilities that drive drift).

Critically, this is not a claim about agent capability or alignment. We show that drift emerges from **structural incentive pressure** under symmetric information, independent of agent intelligence or intent. Our empirical observations include three decision points where asymmetric structure enabled stopping, accompanied by explicit counterfactual predictions demonstrating drift under symmetric alternatives. We propose a falsifiable experimental design and discuss implications for AI safety, human-AI collaboration, and organizational governance where reliable stopping is safety-critical.

**The contribution is structural: systems with symmetric access to expanding implementation context fail to converge to stable stopping points.**

---

## 1. Introduction

Multi-agent and human-AI collaborative systems increasingly operate under the assumption that better coordination emerges from shared context and symmetric information access. System designers optimize for transparency, reduce information asymmetry, and enable agents to access expanding implementation details with the goal of improving decision quality. This intuition—that more accessible information leads to better collaboration—pervades multi-agent AI research, human-in-the-loop design, and organizational governance frameworks.

We present evidence that contradicts this intuition for a specific but critical class of tasks: those requiring stable stopping points. In systems where reliable convergence matters—architectural consolidation, safety-critical decision-making, governance under bounded resources—symmetric access to expanding context creates persistent drift pressure that prevents systems from reaching stable equilibria. Instead of improving coordination, symmetric observability introduces **control interference**, **incentive misalignment**, and **unbounded action entropy** that make stopping an unstable or unreachable state.

Our contribution is structural, not prescriptive. We do not propose a collaboration framework or claim that asymmetry is universally beneficial. We demonstrate through formal analysis and empirical observation that:

**Systems with symmetric access to expanding implementation context fail to converge to stable stopping points.**

This is a negative result about a failure mode, not a positive claim about a superior design. We show that this failure is **structural**—independent of agent intelligence, alignment quality, or cooperative intent—and therefore cannot be solved by improving agent capabilities alone.

We ground this claim in three ways:

1. **Formal interpretation** through control theory, mechanism design, and information theory, showing that symmetric observability creates overlapping control surfaces, misaligned equilibria, and persistent exploration gradients.

2. **Empirical observation** of a structured multi-agent collaboration where intentionally frozen asymmetric roles enabled stable stopping across three decision points where symmetric designs would predict drift.

3. **Falsifiable prediction** specifying the experimental conditions under which symmetric observability would lead to scope expansion, boundary erosion, and stopping failure.

Our implications are narrow: in domains where reliable stopping is safety-critical—AI governance, production control systems, architectural decision-making—designing for **bounded observability** may be as important as designing for capability or alignment. We do not generalize beyond this claim.

The remainder of this paper proceeds as follows: Section 2 positions our work against related literature. Section 3 provides formal interpretation through three independent lenses. Section 4 presents empirical observations from a case study. Section 6 concludes.

---

## 2. Related Work

Our work intersects several research areas but occupies a distinct position focused on **role-constrained observability** as a structural determinant of stopping behavior.

**Multi-agent coordination and collaboration.** Extensive research addresses coordination mechanisms in multi-agent systems, including communication protocols [references], task allocation [references], and consensus algorithms [references]. This work typically optimizes for coordination quality, throughput, or solution optimality. We do not address coordination quality. We examine whether systems can reliably stop under asymmetric versus symmetric information access, treating stopping as a stability property independent of task performance.

**Human-AI collaboration and human-in-the-loop systems.** Recent work explores design patterns for human-AI collaboration [references], shared mental models [references], and mixed-initiative interaction [references]. These approaches generally seek to reduce information asymmetry and align human and AI understanding. Our focus is orthogonal: we investigate whether bounded observability—rather than shared understanding—enables convergence in tasks where stopping is safety-critical. We do not claim that asymmetry improves collaboration quality, only that it affects stopping reliability.

**Separation of powers and organizational design.** Constitutional systems and organizational theory have long recognized the value of separated authorities and checks-and-balances [references]. Our contribution is not the idea of separated roles, but the formal and empirical demonstration that **observability bounds**—not just authority separation—determine whether systems can reach stable stopping points. Prior work separates what agents can do; we examine what agents can see.

**AI safety and alignment.** The AI safety community addresses capability control [references], value alignment [references], and robustness under distributional shift [references]. Our work differs in that we identify a failure mode that persists **independent of alignment quality**. We show that drift emerges from structural incentive pressure under symmetric information, not from misalignment or capability limitations. Improving agent intelligence or alignment does not address this failure mode.

**Control theory in socio-technical systems.** Control-theoretic perspectives have been applied to organizational dynamics [references] and software engineering [references]. We apply control-theoretic reasoning to stopping behavior in collaborative AI systems, focusing specifically on observability constraints.

**Across these areas, we focus on a single structural claim:** systems with symmetric access to expanding implementation context cannot reliably stop. This claim is independently supported by control theory (control interference), mechanism design (misaligned equilibria), and information theory (unbounded action entropy), and is empirically grounded in observed stopping behavior under asymmetric constraints.

---

## 3. Formal Framing

### 3.1 Control-Theoretic Interpretation

We model multi-agent collaboration as a feedback control system where agents apply corrective actions based on observed state to drive the system toward a target configuration (e.g., architectural consolidation).

**System model:**
- State: $x(t) \in \mathbb{R}^n$ (system architecture, documentation, implementation)
- Control inputs: $u_a(t), u_c(t), u_i(t)$ (architect, critic, implementer actions)
- Target state: $x^*$ (consolidated architecture with no pending work)

**Symmetric observability (standard design):**

Each agent observes the full state: $y_j = x$ for all agents $j$.

Control laws: $u_j = K_j(x - x^*)$ where $K_j$ are feedback gain matrices.

**Problem:** Multiple controllers acting on overlapping state variables create **control interference**. When all agents can observe and respond to the same errors (e.g., "this feature could be improved"), the aggregate control input becomes:

$$u_{total} = \sum_j K_j(x - x^*)$$

This sum is **unbounded** unless all $K_j$ are perfectly coordinated. Under realistic conditions (agents operate independently, asynchronously), the system exhibits:
- Oscillation around $x^*$ (perpetual refinement)
- Inability to reach stable equilibrium (stopping requires all controllers to simultaneously zero their inputs)

**Asymmetric observability (proposed design):**

Each agent observes a **projection** of the state:
- Critic: $y_c = C_c \cdot x$ (principles-only projection, e.g., "does this violate boundaries?")
- Implementer: $y_i = C_i \cdot x$ (local task projection, e.g., "is my assigned diff complete?")
- Architect: $y_a = x$ (full state)

Where $C_c$ and $C_i$ are **non-overlapping** projection matrices (rank-deficient by design).

Control laws now operate on disjoint subspaces:
- $u_c = K_c(C_c \cdot x)$ (can only veto on principle violations)
- $u_i = K_i(C_i \cdot x)$ (can only act on local task)
- $u_a = K_a(x, u_c, u_i)$ (coordinates within veto constraint)

**Result:** Control surfaces are **orthogonal**. The critic cannot observe "while we're here" optimizations (they're invisible in $C_c \cdot x$). The implementer cannot observe architectural drift (invisible in $C_i \cdot x$). The system converges to $x^*$ when all projected errors are zero, which occurs at a **unique stable equilibrium** rather than an oscillatory region.

**Lyapunov stability:** Define a candidate Lyapunov function $V(x) = \|x - x^*\|^2$. Under asymmetric observability, projected control inputs act on non-overlapping subspaces, yielding $\dot{V}(x) \leq 0$, with equality only when all projected errors are zero. This establishes asymptotic convergence to $x^*$. Under symmetric observability, overlapping control actions can increase $\dot{V}(x)$, preventing convergence.

---

### 3.2 Mechanism Design Interpretation

We model collaboration as a game where agents maximize individual utility subject to role constraints.

**Setup:**
- Agents: Architect (A), Critic (C), Implementer (I)
- State: $s \in S$ (current system state)
- Actions: $a_j \in A_j$ for each agent $j$
- Utility: $u_j(s, a_1, \ldots, a_n)$

**Symmetric information game:**

All agents observe full state $s$.

Utility includes "completeness" term: $u_j(s, \mathbf{a}) = -d(s, s^*) + \alpha \cdot \text{completeness}(s)$

Where $d(s, s^*)$ measures distance from target, and completeness rewards unexploited improvements.

The completeness term does not represent agent preference but structural opportunity: under full observability, adjacent improvements are visible and therefore admissible actions, creating unilateral deviation incentives regardless of agent intent.

**Nash equilibrium:** Any state where $d(s, s^*) = 0$ **and** $\text{completeness}(s) < 1$ is unstable, because any agent can profitably deviate by proposing adjacent improvements visible in $s$.

"Stop" is not an equilibrium—it's dominated by "one more thing."

**Asymmetric information game:**

Agents observe partial state:
- $s_c = \pi_c(s)$ (principles only)
- $s_i = \pi_i(s)$ (local task only)
- $s_a = s$ (full state)

Utility remains the same, but action spaces are constrained by observability:
- Critic can only veto if $\pi_c(s)$ shows principle violation
- Implementer can only act if $\pi_i(s)$ shows task incompleteness

**Nash equilibrium:** When $\pi_c(s^*) = \emptyset$ (no principle violations) and $\pi_i(s^*) = \emptyset$ (local task complete), no agent can profitably deviate:
- C cannot see "completeness" opportunities (not in $\pi_c$)
- I cannot see architectural drift (not in $\pi_i$)
- A wants to stop because consolidation is complete

"Stop" becomes the **unique Nash equilibrium** rather than requiring sustained coordination or discipline.

**Mechanism property:** The asymmetric design makes stopping **incentive-compatible** rather than cooperative.

---

### 3.3 Information-Theoretic Interpretation

We interpret context as information that shapes the distribution of next actions.

**Full context:** Agent observes state $x$, computes conditional distribution over next actions $p(a|x)$.

**Entropy of action space:** $H(A|X) = -\sum_a p(a|x) \log p(a|x)$

High entropy = many plausible actions. Key insight: adjacent to any state $x$, there exist **adjacent improvements** $\{x'\}$ visible in full context.

**Result:** For any state near target $x \approx x^*$, full observability creates non-zero probability mass on actions that explore $\{x'\}$:

$$p(\text{expand}|x) > 0 \text{ whenever } \exists x' \text{ adjacent to } x \text{ with higher completeness}$$

This creates **persistent drift pressure**—the system cannot reach zero gradient because new gradients are always discoverable.

**Bounded context:** Agent observes projection $\pi(x)$, computes $p(a|\pi(x))$.

**Reduced entropy:** $H(A|\pi(X)) < H(A|X)$ because many adjacent improvements are **not visible** in $\pi(x)$.

Example: Critic observing principles-only projection cannot "see" Flask file optimization, because file-level details are filtered out by $\pi_c$.

**Result:** When $\pi(x^*) = \emptyset$ (projected state is null), action distribution collapses:

$$p(\text{stop}|\pi(x^*)) = 1$$

The agent has no information supporting any action other than "approve and exit."

**This proves:** Bounded information creates bounded action entropy, enabling deterministic stopping rather than perpetual exploration.

---

### 3.4 Convergence of Interpretations

Three independent formalisms predict the same structural failure:

| Lens | Mechanism | Failure Mode Under Symmetry | Success Under Asymmetry |
|------|-----------|----------------------------|------------------------|
| **Control Theory** | Control surface interference | Oscillation, no stable equilibrium | Orthogonal surfaces, Lyapunov stability |
| **Mechanism Design** | Incentive structure | "Stop" dominated by "expand" | "Stop" is Nash equilibrium |
| **Information Theory** | Action entropy | Non-zero gradient persists | Zero gradient at projection null |

**Critical observation:** These are not three different claims. They are three different **descriptions of the same invariant**:

**Systems with symmetric access to expanding implementation context cannot reach stable stopping points.**

This convergence is the proof. When independently-derived formal models agree on a failure mode, the failure is **structural**, not accidental.

---

## 4. Empirical Observations

We report observations from a structured multi-agent collaboration conducted during an architectural documentation consolidation task.

### 4.1 Setup

Three AI agents participated with fixed, asymmetric roles. One agent (Architect) had access to full task context and made architectural decisions but could not implement changes directly. A second agent (Implementer) executed approved changes but had no architectural discretion. A third agent (Critic) had no access to implementation artifacts and was restricted to critique and approval only.

No agent possessed the full authority stack, and role boundaries were not relaxed over time.

The task involved verifying existing architectural documentation, correcting mismatches with implementation reality, and determining whether additional work was necessary.

### 4.2 Decision Points

We report three decision points where additional work was possible, critique was applied, and a stable stopping point was reached.

**Decision Point 1: Minor Documentation Change**

*Context:* During documentation consolidation, a small change was identified that would add a clarifying comment to an existing test utility file. The change was technically correct but did not affect system behavior, safety boundaries, or architectural understanding.

*Action Proposed:* The Architect identified the change as possible and feasible given proximity to the file and recent edits.

*Critique Applied:* The Critic rejected the change on the basis that it added no risk reduction and introduced additional artifact churn without clarifying any active ambiguity.

*Outcome:* The change was not implemented. No alternative documentation work was proposed. The task paused without generating follow-on actions.

**Decision Point 2: Diagram Detail Expansion**

*Context:* After correcting stale diagrams, it was possible to expand newly created diagrams with additional implementation detail reflecting downstream effects and internal signal propagation.

*Action Proposed:* The Architect considered increasing diagram fidelity to include more technically accurate connections.

*Critique Applied:* The Critic rejected the expansion on the basis that additional detail would blur governance boundaries and could imply authority or coupling not present in the system's design constraints.

*Outcome:* The diagrams were finalized at their current abstraction level. No further diagram work was proposed.

**Decision Point 3: Post-Assessment Cleanup**

*Context:* After all known assumptions were verified against corrected documentation, no inconsistencies remained. Trivial cleanup tasks were still possible.

*Action Proposed:* No explicit action was proposed. The possibility of "one more small improvement" existed implicitly due to remaining available time.

*Critique Applied:* The Critic explicitly approved stopping, noting that all decision criteria had been satisfied and that additional work would constitute scope expansion rather than consolidation.

*Outcome:* Work terminated. No future tasks, enhancements, or next steps were generated.

### 4.3 Absence of Drift

No scope expansion occurred after critique rejection. No new tasks were proposed following veto decisions. No reframing of objectives took place. No agent requested additional authority or context access. No "temporary" relaxation of role boundaries was suggested. The collaboration terminated without deferral, backlog creation, or future work identification.

No agent proposed process improvements, efficiency optimizations, or role adjustments. No gradual authority accumulation occurred across decision points. No trust-based role evolution was observed.

### 4.4 Counterfactual Prediction

We predict that under symmetric observability—where the Critic agent possessed full access to implementation context—at least one additional task would have been proposed at each decision point. At Decision Point 1, the Critic would likely have observed file proximity and implementation simplicity, reducing resistance to "minor cleanup." At Decision Point 2, the Critic would have observed technically correct but governance-blurring details, creating justification pressure for "completeness." At Decision Point 3, remaining time and visible adjacent improvements would have generated rationalization for "one more small thing." This prediction is falsifiable through replication: run the identical task with symmetric information access and measure scope expansion events, boundary erosion instances, and stopping failure rate.

---

## 6. Conclusion

We have demonstrated that systems with symmetric access to expanding implementation context fail to converge to stable stopping points. This failure is structural, not cognitive: it persists independent of agent intelligence, alignment quality, or cooperative intent. We show through control theory that symmetric observability creates overlapping control surfaces that prevent convergence, through mechanism design that it misaligns stopping incentives, and through information theory that it maintains non-zero exploration gradients. Empirical observation of a structured multi-agent collaboration confirms that intentionally frozen asymmetric roles enable reliable stopping where symmetric designs would predict drift.

This is a negative result about a specific failure mode in collaborative systems where reliable stopping is safety-critical. We do not propose a general framework or claim universal benefits of asymmetry. Our contribution is narrow: bounded observability can determine whether systems reach stable equilibria, and this property is independent of the factors typically optimized in multi-agent and human-AI collaboration research.

The result is falsifiable. Replicating the empirical task under symmetric information conditions should produce scope expansion, boundary erosion, and stopping failure. If it does not, the structural claim is refuted.

For domains where convergence matters—AI governance, production control, architectural consolidation—designing for stopping may require constraints on what agents observe, not just what they can do.
