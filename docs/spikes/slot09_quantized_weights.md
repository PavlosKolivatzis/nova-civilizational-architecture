# Spike Plan: Slot09 Quantized Weights

Status: Draft (2025-10-07)
Owner: @paulk / Codex Agent
Related Doc: docs/grok_integration_opportunities.md (item 1 completed)

## Goals
- Quantify potential impact of 8-bit checkpoint storage for Slot09 (Distortion Protection).
- Validate that `QuantizedWeight8bit` can represent Slot09 model tensors without breaking inference.
- Establish performance baselines (load time, memory footprint) for before/after comparison.

## Questions to Answer
1. Where are Slot09 weights persisted today? (Code search + audit artifacts)
2. Can we extract representative tensors for experimentation (e.g., policy matrices, IDS weights)?
3. Does quantising to 8-bit maintain acceptable output parity (deterministic tests)?
4. What is the size/time delta when serializing with vs. without quantization?

## Work Plan
1. **Inventory current storage**
   - Grep Slot09 modules for weight loading/serialization paths.
   - Check audit artifacts for Slot09 checkpoint dumps.
2. **Prototype quantization**
   - Select a representative tensor (or fabricate a synthetic weight if none exist yet).
   - Apply `QuantizedWeight8bit` + baseline round-trip.
   - Measure numerical drift vs. float32.
3. **Benchmark I/O**
   - Serialize the tensor with and without quantization (pickle or JSON) and time load/save.
   - Capture size/time metrics.
4. **Document findings**
   - Add results to this file and update docs/grok_integration_opportunities.md with recommendation (adopt/defer).
5. **Decide next steps**
   - If results are promising, schedule production integration (adapter changes, CI tests).

## Metrics to Capture
- Tensor size (float vs. quantized) in bytes.
- Load/save time (float vs. quantized) on developer machine.
- Maximum absolute/relative error after quantize → dequantize.

## Open Items
- Identify or generate actual Slot09 weight tensors.
- Confirm there is a deterministic test harness for Slot09 outputs (IDS policy evaluation).

## Notes
- No code changes committed by this spike until data supports production work.
- Keep Apache 2.0 headers if importing additional Grok snippets.
