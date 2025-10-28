"""
Rolling checkpoint service for automated Merkle signing.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

import asyncio
import time
from typing import Optional

from .checkpoint_signer import CheckpointSigner, Checkpoint
from .metrics import ledger_checkpoints_total, ledger_checkpoint_verify_failures_total, ledger_checkpoint_latency_ms


class CheckpointService:
    """
    Automated service for creating periodic Merkle checkpoints.

    Runs in background, creating checkpoints based on time or record count thresholds.
    """

    def __init__(
        self,
        signer: CheckpointSigner,
        *,
        every_seconds: int = 300,  # 5 minutes
        min_records: int = 1000,
        enabled: bool = True
    ):
        """
        Initialize checkpoint service.

        Args:
            signer: CheckpointSigner instance
            every_seconds: Minimum time between checkpoints
            min_records: Minimum records to trigger checkpoint
            enabled: Whether service should run
        """
        self.signer = signer
        self.every_seconds = every_seconds
        self.min_records = min_records
        self.enabled = enabled
        self._running = False
        self._last_checkpoint_ts: Optional[float] = None

    async def roll_once(self, start_ts: Optional[str] = None, end_ts: Optional[str] = None) -> Checkpoint:
        """
        Create a single checkpoint.

        Args:
            start_ts: Start timestamp (ISO format). If None, uses last checkpoint end.
            end_ts: End timestamp (ISO format). If None, uses current time.

        Returns:
            Created and signed checkpoint
        """
        if not self.enabled:
            raise RuntimeError("Checkpoint service is disabled")

        start_time = time.perf_counter()

        try:
            # Determine time range
            if start_ts is None:
                start_ts = await self._get_last_checkpoint_end_ts()
            if end_ts is None:
                end_ts = self._current_iso_timestamp()

            # Build and sign checkpoint
            checkpoint = await self.signer.build_and_sign(start_ts, end_ts)

            # Verify immediately
            is_valid, error = await self.signer.verify_range(checkpoint)
            if not is_valid:
                checkpoint_verify_failures.inc()
                raise ValueError(f"Checkpoint verification failed: {error}")

            # Update metrics
            ledger_checkpoints_total.inc()
            self._last_checkpoint_ts = time.time()

            latency_ms = (time.perf_counter() - start_time) * 1000
            ledger_checkpoint_latency_ms.observe(latency_ms)

            return checkpoint

        except Exception as e:
            ledger_checkpoint_verify_failures_total.inc()
            raise

    async def run_forever(self, stop_event: asyncio.Event):
        """
        Run checkpoint service continuously.

        Args:
            stop_event: Event to signal service shutdown
        """
        if not self.enabled:
            return

        self._running = True

        try:
            while not stop_event.is_set():
                try:
                    # Check if we should create a checkpoint
                    should_roll = await self._should_roll_checkpoint()

                    if should_roll:
                        await self.roll_once()
                        # Reset timer after successful checkpoint
                        await asyncio.sleep(0)
                    else:
                        # Wait before checking again
                        await asyncio.wait_for(stop_event.wait(), timeout=self.every_seconds)

                except asyncio.TimeoutError:
                    # Normal timeout, continue loop
                    continue
                except Exception as e:
                    # Log error but continue running
                    print(f"Checkpoint service error: {e}")
                    await asyncio.sleep(self.every_seconds)

        finally:
            self._running = False

    async def _should_roll_checkpoint(self) -> bool:
        """Determine if a checkpoint should be created."""
        # Check time threshold
        now = time.time()
        if self._last_checkpoint_ts is None:
            # First checkpoint
            return True

        time_since_last = now - self._last_checkpoint_ts
        if time_since_last >= self.every_seconds:
            # Check record threshold
            last_end_ts = await self._get_last_checkpoint_end_ts()
            record_count = await self.signer.store.count_records_since(last_end_ts)
            return record_count >= self.min_records

        return False

    async def _get_last_checkpoint_end_ts(self) -> str:
        """Get end timestamp of last checkpoint, or epoch if none."""
        latest = await self.signer.store.get_latest_checkpoint()
        if latest:
            return latest.range_end
        else:
            # Return epoch timestamp for first checkpoint
            return "2025-01-01T00:00:00Z"

    @staticmethod
    def _current_iso_timestamp() -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    @property
    def is_running(self) -> bool:
        """Check if service is currently running."""
        return self._running