1. **Phase A – Dual Support**  
   Keep `multicultural_truth_synthesis.py` and new `engine.py` side-by-side; mark legacy APIs deprecated.
2. **Phase B – Adapters Update**  
   Redirect `slot6_cultural` adapter to new engine; provide shim for legacy parameters.
3. **Phase C – Removal Gate**  
   CI job `validate-architecture` runs with `NOVA_BLOCK_LEGACY_SLOT6=1`; once stable, remove legacy engine.
4. **Phase D – Contract Freeze**  
   Freeze `CULTURAL_PROFILE@1` schema; add regression tests.
5. **Phase E – Cleanup**  
   Drop `legacy_engine.py` and old docs; archive in `legacy/` branch.
