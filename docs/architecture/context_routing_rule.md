# Context-Aware Routing Rule

## Status
**Active** | Established Phase 17.3 | Validated by RT-861 through RT-866

## The Rule

**Structure-only detection MUST be routed through context-aware gates before contributing to harm assessment or governance decisions.**

```
Detection Layer (context-blind, structure-only)
    ↓
Routing Layer (context-aware, consent/authorization checks)
    ↓
Governance Layer (receives gated signals only)
```

## Core Principle

Detection and routing are separate concerns:

- **Detection**: Identifies structural patterns in single artifacts (turns, deltas, events)
  - Fast, stateless, purely syntactic
  - No conversation history required
  - No intent inference
  - High recall, tolerates false positives

- **Routing**: Evaluates detected patterns against conversational/systemic context
  - Stateful, requires history
  - Checks authorization, consent, scope, temporal validity
  - Filters false positives structurally (no intent guessing)
  - Only uninvited/unauthorized patterns contribute to A_p

## When This Rule Applies

Apply context-aware routing when detection makes **semantic or harm claims** about:

1. **Intent or authorization**
   - Example: "User invited this delegation" vs "Agent imposed unilaterally"
   - Requires: Conversation history to check invitation signals

2. **Scope boundaries**
   - Example: "Action exceeds requested task boundary"
   - Requires: Prior turns to establish scope

3. **Temporal validity**
   - Example: "Consent expired after N-turn gap"
   - Requires: Turn indices and timestamps

4. **Harm attribution**
   - Example: "This manipulation pattern is unwanted"
   - Requires: Context to distinguish invited vs uninvited

**Counter-example (routing NOT needed):**
- Pure metrics (distortion, entropy) with no authorization claim
- Structural counts without semantic interpretation
- Raw observation signals fed to human review (no automated action)

## Failure Mode: Context-Blind Semantic Claims

When detection makes semantic claims without routing:

**Phase 16 Naive Detection (falsified by RT-862):**
```python
# Context-blind: treats ALL Decision Substitution as pressured
primitives = detect_primitives("I'll handle the Docker config for you.")
A_p = 1.0 if primitives else 0.0  # FALSE POSITIVE

# User explicitly requested: "I need help setting up the CI/CD pipeline"
# → Delegation was invited, but naive detector flags it anyway
```

**Known instances:**
- Phase 16 naive agency pressure detection (pre-consent gate)
- Slot02 manipulation pattern detection (single-turn only, no consent check)

**Why it fails:**
- Structure alone cannot distinguish invited vs uninvited patterns
- No access to authorization context (prior requests, revocations, scope agreements)
- Conflates "pattern present" with "pattern harmful"

## Contract: Canonical Turn Stream

Context-aware routing requires standardized conversation history:

```python
# Canonical format
conversation_history: List[Dict[str, str]] = [
    {"role": "user", "content": "Can you help me debug?"},
    {"role": "assistant", "content": "I'll check the logs for you."},
]
```

**Properties:**
- Append-only turn sequence
- Role-tagged (user/assistant)
- No metadata pollution in main contract
- Available at routing time (not detection time)

**Implemented by:**
- `src/nova/orchestrator/conversation/session_manager.py`
- Feature flag: `NOVA_ENABLE_CONVERSATION_HISTORY`

## Implementation Pattern

### Step 1: Detection (context-blind)
```python
from nova.phase16.primitives import detect_primitives

primitives_detected = detect_primitives(turn_content)
# Returns: ["Decision Substitution", "Scope Expansion", ...]
# No conversation history required
```

### Step 2: Routing (context-aware)
```python
from nova.phase17 import check_consent

primitives_uninvited = []
for primitive in primitives_detected:
    gate_result = check_consent(
        primitive=primitive,
        turn_content=turn_content,
        conversation_history=conversation_history  # ← Context
    )
    if gate_result.contributes_to_A_p():  # Uninvited only
        primitives_uninvited.append(primitive)
```

### Step 3: Governance (receives gated signals)
```python
# Only uninvited primitives contribute to agency pressure
A_p = count_uninvited_turns / total_turns

# Governance receives:
# - primitives_uninvited (NOT primitives_detected)
# - gate_results (provenance)
# - session context
```

## Validation: RT Evidence

Proven by Retrospective Tests (Phase 17.1):

| RT | Scenario | Naive A_p | Gated A_p | Verdict |
|----|----------|-----------|-----------|---------|
| RT-862 | Delegation after explicit request | 1.0 (FP) | 0.0 | **Naive falsified** |
| RT-863 | Unsolicited agent initiative | 1.0 | 1.0 | Both correct |
| RT-864 | Scope violation (typo → full rewrite) | 1.0 | 1.0 | Both correct |
| RT-865 | User revokes mid-action | 0.0 → 1.0 | 0.0 → 1.0 | Both correct |
| RT-866 | Temporal decay (20-turn gap) | 0.0 → 1.0 | 0.0 → 1.0 | Both correct |

**Key result:** RT-862 demonstrates naive detection produces false positives that consent gate eliminates.

## Invariants

1. **Detection layer remains sealed**
   - No conversation history access at detection time
   - No intent inference in primitive patterns
   - Structure-only, fast, stateless

2. **Routing layer owns context**
   - Conversation history available
   - Authorization/consent checks happen here
   - Filters false positives structurally (no guessing)

3. **Governance receives clean signals**
   - Only gated (uninvited) primitives
   - Provenance metadata attached
   - No re-interpretation of routing decisions

4. **Fail-safe defaults**
   - If routing unavailable → fallback to naive (flag as uncertain)
   - If consent ambiguous → fail closed (treat as uninvited)
   - Feature flags enable/disable routing without code changes

## Rollback

To disable context-aware routing:
```bash
# Revert to naive detection
export NOVA_ENABLE_CONSENT_GATE=0

# Disable conversation tracking
export NOVA_ENABLE_CONVERSATION_HISTORY=0
```

Or:
```bash
git revert aa55b00  # Remove Phase 17.3/18 infrastructure entirely
```

## Extensions

Future applications of this pattern:

1. **Slot02 Manipulation Patterns** (candidate for Phase 18+)
   - Currently: single-turn context-blind detection
   - Future: Route through consent gate to check invitation

2. **Temporal boundary validation** (Phase 14/15)
   - Currently: metrics-only (safe)
   - If extended to semantic claims: requires routing

3. **Cross-slot coordination signals**
   - Any slot making authorization claims about cross-slot interactions
   - Requires routing layer to check inter-slot contracts

## References

- **Phase 16**: Primitive detection (context-blind baseline)
- **Phase 17.0-17.2**: Consent gate modules (invitation/revocation/scope signals)
- **Phase 17.3/18**: Conversation history infrastructure + routing integration
- **Audit**: `docs/audits/context_availability_audit_phase17_pattern.md`
- **ADR**: `docs/adrs/ADR-017-context-aware-routing.md`
- **Tests**: `tests/test_conversation_phase17_integration.py` (RT-861 through RT-866)

## Bottom Line

**If your detection makes claims about intent, authorization, or harm → route it through context first.**

Structure-only detection is necessary but insufficient for semantic claims.
Context-aware routing completes the picture without contaminating detection.
