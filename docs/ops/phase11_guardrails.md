# Phase 11 Guardrails (Rollback-Invariant)

- Roll back ANR instantly:
  xport NOVA_ANR_ENABLED=0
- Roll back META_LENS instantly:
  xport NOVA_ENABLE_META_LENS=0
- No new protocols; only native slot extensions.
- Epoch base: v10.0-complete; all deviations must be flag-gated.
