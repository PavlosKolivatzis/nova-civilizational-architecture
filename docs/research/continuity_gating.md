# Continuity Gate (Expression-Layer Gating)

## Definition

A Continuity Gate is a pre-reasoning constraint that decides whether continuation is legitimate right now. Reasoning is enabled only when the gate admits it. This operates at the expression layer, not at the model or architecture layer.

Default stance:

- `continuation_assumed = false`

Admission criteria (any one is sufficient):

- A violation exists
- A gap exists
- A contradiction exists
- An explicit mandate exists

Explicit rejection of momentum (not valid admission criteria):

- Proximity ("we are already here")
- Effort invested
- Time remaining
- Ease of implementation
- Curiosity
- Aesthetic improvement

No inheritance:

- Approval at time T does not lower the gate at time T+1
- Authority does not accumulate

## Observed Parameters

- `continuation_assumed = false`
- `momentum_carries_forward = false`
- `authority_accumulates = false`
- `reasoning_enabled_only_if_legitimate = true`

## Failure Modes Without It

- Drift
- Scope creep
- "One more thing"
- Endless adjacent improvements

## Why It Is Expression-Layer Only

- Same model, different outcome
- No weight change required
- Fragile by design (permission can be withdrawn without retraining)

## Relation to Nova

Isomorphic to:

- Advisory signals
- Non-coercive governance
- Observability without authority

Not a runtime feature.

## Activation Warning

This gate is expensive. It is not suitable for brainstorming or low-stakes work. Use requires an explicit legitimacy trigger. Activation is contextual and revocable; disabling the gate does not require justification.

## Exclusions

This document does not include:

- "How to prompt it" recipes
- Templates
- Automation suggestions
- Claims of superiority

## Clean Rule

Reasoning should not be the default action of an intelligent system. Continuation should be gated, not assumed.
