"""Meta-lens integration for Slot2 plugin - add this to get_contract_adapters()"""

def _meta_lens_analyze(payload):
    """Generate meta-lens analysis report with fixed-point iteration."""
    import os
    from datetime import datetime, timezone

    # Check if meta-lens is enabled
    if os.getenv("NOVA_ENABLE_META_LENS", "0") not in ("1", "true", "TRUE"):
        return {
            "schema_version": "1.0.0",
            "source_slot": "S2",
            "meta_lens_analysis": {"cognitive_level": "analysis", "lenses_applied": [], "state_vector": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
            "iteration": {"epoch": 0, "converged": False, "residual": 1.0, "max_iters": 3, "alpha": 0.5, "epsilon": 0.02, "frozen_inputs": {"padel_ref": "", "infinity_ref": ""}},
            "risk_assessment": {"level": "unknown", "vectors": []},
            "integrity": {"hash": "sha256:", "signed_by": "slot01_truth_anchor", "timestamp": ""},
            "disabled": True,
            "reason": "NOVA_ENABLE_META_LENS not enabled"
        }

    try:
        from .meta_lens_processor import run_fixed_point, create_base_state, hash_report
        # Strict/permissive validation mode
        strict_validation = os.getenv("META_LENS_STRICT_VALIDATION", "0") in ("1", "true", "TRUE")

        try:
            from contracts.validators.meta_lens_validator import validate_meta_lens_report
            VALIDATION_AVAILABLE = True
        except ImportError:
            if strict_validation:
                raise ImportError("META_LENS_STRICT_VALIDATION=1 requires fastjsonschema but it's not available")
            VALIDATION_AVAILABLE = False
            def validate_meta_lens_report(report):
                # Log warning in permissive mode
                print("[WARN] META_LENS validation disabled - fastjsonschema not available (set META_LENS_STRICT_VALIDATION=0 to suppress)")
                pass  # No-op validation

        # Extract content and prepare input
        if isinstance(payload, dict):
            content = payload.get("content", payload.get("text", ""))
            context = payload.get("context", {})
        else:
            content = str(payload)
            context = {}

        input_hash = hash_report({"text": content})

        # Create base state with frozen inputs (mock for initial implementation)
        padel_ref = f"padel_{input_hash[:8]}"
        infinity_ref = f"inf_{input_hash[:8]}"

        base_state = create_base_state(
            input_hash=input_hash,
            padel_req_id=padel_ref,
            infinity_req_id=infinity_ref,
            cognitive_level="synthesis"
        )

        # Always attempt real adapters if a registry is provided
        adapter_registry = context.get("adapter_registry")

        try:
            from .adapter_integration_patch import create_real_adapter_functions, create_mock_functions
            if adapter_registry is not None:
                tri_fn, const_fn, culture_fn, distort_fn, emo_fn = create_real_adapter_functions(content, context)
                context["_meta_lens_mode"] = "real_adapters"
            else:
                tri_fn, const_fn, culture_fn, distort_fn, emo_fn = create_mock_functions()
                context["_meta_lens_mode"] = "mock_adapters"
        except Exception as e:
            # If anything goes wrong with the real import, log + fallback to mocks
            import logging
            logging.getLogger("slot2.meta_lens").warning(f"META_LENS: using mock adapters (import error: {e})")
            from .adapter_integration_patch import create_mock_functions
            tri_fn, const_fn, culture_fn, distort_fn, emo_fn = create_mock_functions()
            context["_meta_lens_mode"] = "mock_adapters_import_error"

        # Test enforcement flag
        enforce_real = os.getenv("NOVA_META_LENS_TEST_ENFORCE_REAL", "0") in ("1", "true", "TRUE")
        if enforce_real and context.get("_meta_lens_mode") != "real_adapters":
            raise RuntimeError(f"META_LENS: expected real adapters in test, but mode is {context.get('_meta_lens_mode')}")

        # Run fixed-point iteration
        lightclock_tick = context.get("lightclock_tick", 1000)

        final_report, snapshots = run_fixed_point(
            input_ref=input_hash,
            base_state=base_state,
            tri_fn=tri_fn,
            const_fn=const_fn,
            culture_fn=culture_fn,
            distort_fn=distort_fn,
            emo_fn=emo_fn,
            lightclock_tick=lightclock_tick
        )

        # Add processing metadata
        final_report["notes"].append(f"Processed {len(content)} chars with {final_report['iteration']['epoch']} iterations")
        final_report["notes"].append(f"Adapter mode: {context.get('_meta_lens_mode', 'unknown')}")
        final_report["snapshots_count"] = len(snapshots)

        # Add UX softening banner if unstable
        instability_detected = (
            final_report["iteration"].get("watchdog", {}).get("abort_triggered", False) or
            not final_report["iteration"].get("converged", True) or
            final_report["iteration"].get("residual", 0.0) > final_report["iteration"].get("epsilon", 0.02)
        )

        if instability_detected:
            final_report["ux_banner"] = {
                "type": "instability_warning",
                "message": "Meta-lens detected instability; response adjusted for caution.",
                "technical_details": {
                    "converged": final_report["iteration"].get("converged"),
                    "residual": final_report["iteration"].get("residual"),
                    "abort_triggered": final_report["iteration"].get("watchdog", {}).get("abort_triggered", False)
                }
            }

        # Validate before returning
        validate_meta_lens_report(final_report)

        return final_report

    except Exception as e:
        import traceback
        from datetime import datetime, timezone

        # Extract trace information for logging
        trace_info = {
            "input_hash": hash_report({"text": content}) if 'content' in locals() else "unknown",
            "lightclock_tick": context.get("lightclock_tick", 0) if 'context' in locals() else 0,
            "error_type": type(e).__name__,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }

        # Log trace information (in production, this would go to structured logging)
        print(f"[ERROR] META_LENS processing failed: {trace_info}")

        return {
            "schema_version": "1.0.0",
            "source_slot": "S2",
            "meta_lens_analysis": {"cognitive_level": "error", "lenses_applied": [], "state_vector": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0]},
            "iteration": {"epoch": 0, "converged": False, "residual": 1.0, "max_iters": 3, "alpha": 0.5, "epsilon": 0.02, "frozen_inputs": {"padel_ref": "", "infinity_ref": ""}},
            "risk_assessment": {"level": "critical", "vectors": ["processing_error"]},
            "integrity": {"hash": "sha256:", "signed_by": "slot01_truth_anchor", "timestamp": trace_info["timestamp"]},
            "error": str(e),
            "traceback": traceback.format_exc(),
            "trace_info": trace_info
        }