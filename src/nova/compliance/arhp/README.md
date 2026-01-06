ARHP Diagnostic Module (Non-Operative)
=====================================

This package provides a diagnostic-only compliance checker for ARHP-style
envelopes and expressions. It is intentionally non-authoritative:

- No routing or enforcement.
- No automatic RefusalEvent emission in Nova runtime.
- No request interception.

Use this as a lens, not a lever. Presence or absence of this module must not
change Nova behavior unless a downstream derivative or operator explicitly
chooses to consume its outputs.
