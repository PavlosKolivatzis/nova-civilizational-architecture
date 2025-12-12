### Phase 15 – Temporal Governance Readiness Checklist

  - **Evidence review**
    - Confirm RT-00X coverage: at least 10–20 extraction-present rows
  and several benign baselines across different domains (authority,
  paternalistic, dependency, gaslighting, creative, AI-as-tool).
    - Re-check that, for extraction cases, operator judgment still aligns
  with "low / one-way ρ_t + soft C_t band ⇒ `Extraction_present=True`".

  - **Metric sanity**
    - Verify temporal_usm@1 (H_t, ρ_t, C_t) remains stable across new Nova
  deployments (no drift in ranges or obvious encoding issues).
  sample and spot-check that labels + RT archetypes still make sense.

  - **Governance design**
    - Keep Slot02 as the annotation engine (emit `extraction_present` and

  - **Rollback & audit**
    - Define a simple rollback trigger (e.g., "if more than X% of Slot07
  escalations are judged benign by operators over N sessions, disable
  temporal governance and revisit RT calibration").
  If you're happy with this, you can paste it as-is; we then treat Phase 14
  as calibrated and documented, with Phase 15 clearly scoped around Slot07
  integration.