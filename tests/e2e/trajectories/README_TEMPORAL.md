# Temporal Invariance Trajectories

These trajectories test time-scale independence of ORP physics.

## Generating Temporal Trajectories

Temporal trajectories are derived from `canonical_recovery_to_normal.json` by:

1. **temporal_10s_intervals**: Resample at 10s intervals (6x more frequent)
2. **temporal_60s_intervals**: Keep original 60s intervals (baseline)
3. **temporal_compressed_2x**: Drop every 2nd step
4. **temporal_expanded_interpolated**: Add interpolated midpoints

## Expected Behavior

Regime transitions should occur at the same absolute timestamps across all variants.

Example:
- If transition happens at t=360s in 60s-interval version
- It must also happen at t=360s in 10s-interval version
- Even though 10s version has 36 steps vs 60s version's 6 steps

This validates that ORP physics depend on absolute time (seconds), not evaluation frequency.

## Implementation

Run `scripts/generate_temporal_trajectories.py` to create these from canonical source.

**Status:** TODO - implement generator script in Step 3
