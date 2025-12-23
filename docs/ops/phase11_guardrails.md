# Phase 11 Guardrails (Rollback-Invariant)

> **Perimeter + Flags:** Phase 11 behavior (ORP, ANR, META_LENS) is governed solely by NOVA_* environment flags and deployment configuration. FastAPI and related control endpoints assume perimeter enforcement; Nova does not implement internal role-based access control.

- Roll back ANR instantly:
  xport NOVA_ANR_ENABLED=0
- Roll back META_LENS instantly:
  xport NOVA_ENABLE_META_LENS=0
- No new protocols; only native slot extensions.
- Epoch base: v10.0-complete; all deviations must be flag-gated.
