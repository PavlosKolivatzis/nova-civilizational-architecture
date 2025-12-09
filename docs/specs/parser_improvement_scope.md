# Parser Improvement Scope (Phase 14.5 Blocker Resolution)

**Status:** ❌ SUPERSEDED (2025-12-09)
**Resolution:** Criteria reframed (H>0.5 unrealistic), existing parser validated
**See:** `docs/specs/phase14_7_parser_exploration.md` for full analysis

---

## Original Plan (Not Executed)

**Goal:** Upgrade `TextGraphParser` to extract 5-10 relations per multi-party response.
**Success Criteria:** Oracle validation achieves H > 0.5 for distributed/balanced inputs.
**Rollback:** Keep existing regex-based parser as fallback (`NOVA_USE_SPACY_PARSER=0`).

---

## Minimal Viable Improvement

### Option A: spaCy Dependency Parsing (Recommended)
**What:** Extract relations from dependency parse trees (nsubj, dobj, prep, etc.)
**Pros:**
- Standard NLP approach
- Captures hierarchical structure (CEO→Alice) via dependency chains
- Handles verb variations ("collaborate", "coordinate", "support") automatically
**Cons:**
- Adds spaCy dependency (~50MB model download)
- Slower (10-50ms per response vs <1ms regex)
**Implementation:**
1. Install spaCy + en_core_web_sm model
2. Parse sentence → extract (subject, verb, object) triples
3. Map dependency types → RelationTensor weights
   - nsubj + dobj → info_weight
   - prep + pobj → empathy_weight (social relations)
   - advmod + neg → harm_weight (opposition)
4. Coreference resolution (optional, adds 5-10 edges via "she" → "Alice" linking)

**Estimated effort:** 1-2 days (core), +1 day (coreference)

### Option B: Enhanced Regex + Verb Expansion
**What:** Expand verb pattern list from ~20 to ~200 verbs, add synonym groups
**Pros:**
- No new dependencies
- Preserves performance (<1ms)
**Cons:**
- Still brittle (misses paraphrases, passive voice, implicit relations)
- Maintenance burden (verb list curation)
- Won't fix hierarchical structure detection
**Implementation:**
1. Curate verb taxonomy (collaboration, extraction, support, opposition, mediation)
2. Add passive voice patterns ("is supported by", "was questioned by")
3. Add implicit relation patterns ("CEO makes decisions" → CEO controls Other)

**Estimated effort:** 2-3 days (diminishing returns after initial expansion)

### Option C: Hybrid Approach
**What:** Use spaCy for structure, fallback to regex when spaCy fails
**Pros:** Best of both worlds (accuracy + speed)
**Cons:** Complexity (two parsers to maintain)
**Implementation:**
1. Implement Option A
2. Add flag `NOVA_PARSER_MODE=spacy|regex|hybrid`
3. In hybrid mode: try spaCy first, use regex if edge_count < 2

**Estimated effort:** 2-3 days

---

## Recommendation

**Go with Option A (spaCy)** because:
1. Oracle validation showed regex fundamentally cannot see hierarchical structure
2. spaCy is industry-standard (well-tested, documented)
3. Performance cost (10-50ms) acceptable for Slot02 (already has 50ms budget per RFC-002)
4. Sets foundation for future improvements (entity linking, sentiment, etc.)

**Rollback plan:**
- Keep regex parser as `text_graph_parser_legacy.py`
- Add flag `NOVA_USE_SPACY_PARSER=1` (default=1 after validation)
- If spaCy breaks in production → `NOVA_USE_SPACY_PARSER=0` instant rollback

---

## Exit Criteria (Return to Phase 14.5 Observation)

Run oracle validation again with spaCy parser:
1. ✅ Hierarchical input: H > 0.3 (some structural diversity)
2. ✅ Distributed input: H > 0.8, rho > 0.6 (balanced multi-party)
3. ✅ Extractive input: rho < 0.4 (asymmetry detected)
4. ✅ All inputs: edge_count >= 3 (sufficient graph density)

Once these pass → unblock Phase 14.5 observation protocol.

---

## Open Question

**Should parser improvement be Phase 14.7 or Phase 15.0?**

**Arguments for 14.7 (iterative fix):**
- Directly addresses 14.5 blocker
- Scoped to existing Slot02 text_graph_parser.py
- Preserves phase continuity

**Arguments for 15.0 (major version):**
- Introduces new dependency (spaCy)
- Changes core substrate (graphs) that downstream slots depend on
- May invalidate existing bias_report@1 baselines

**Recommendation:** Call it **Phase 14.7** (parser v2.0) with:
- Contract bump: `bias_report@1` → `bias_report@1.1` (add `parser_version` field)
- Maturity gate: Require oracle validation pass before merging
- Feature flag: Enable spaCy gradually (dev → staging → 10% → 100%)
