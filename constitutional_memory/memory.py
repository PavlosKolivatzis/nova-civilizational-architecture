"""
Constitutional Memory - Append-only observational log

Records Nova's boundary events for temporal continuity.
Zero authority, zero interpretation, zero agency.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum


class EventType(Enum):
    """Exhaustive list of recordable events"""
    REFUSAL_EVENT = "refusal_event"
    BOUNDARY_TEST = "boundary_test"
    AWARENESS_INTERVENTION = "awareness_intervention"
    VERIFICATION_RUN = "verification_run"
    DRIFT_DETECTION = "drift_detection"


class ConstitutionalMemory:
    """
    Append-only log of Nova's constitutional boundary events.

    Purpose: Enable temporal continuity across sessions
    Authority: None (observation only)
    Modification: Never (append-only)
    """

    def __init__(self, memory_dir: str = "constitutional_memory"):
        self.memory_dir = Path(memory_dir)
        self.events_file = self.memory_dir / "events.jsonl"
        self.memory_dir.mkdir(exist_ok=True)

        # Initialize with genesis if empty
        if not self.events_file.exists():
            self._write_genesis()

    def _compute_event_hash(self, event: Dict) -> str:
        """Compute tamper-evident hash for event"""
        # Hash everything except the event_hash itself
        event_copy = {k: v for k, v in event.items() if k != "event_hash"}
        event_json = json.dumps(event_copy, sort_keys=True)
        return hashlib.sha256(event_json.encode()).hexdigest()

    def _get_last_event(self) -> Optional[Dict]:
        """Read last event from log (for hash chain)"""
        if not self.events_file.exists():
            return None

        try:
            with open(self.events_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    return json.loads(lines[-1])
        except Exception:
            pass

        return None

    def _write_genesis(self):
        """Write genesis event (hash chain anchor)"""
        genesis = {
            "sequence_number": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "genesis",
            "event_data": {
                "message": "Constitutional memory initialized",
                "version": "0.1"
            },
            "previous_hash": "0" * 64,
            "event_hash": ""
        }
        genesis["event_hash"] = self._compute_event_hash(genesis)

        with open(self.events_file, 'w') as f:
            f.write(json.dumps(genesis) + "\n")

    def append_event(
        self,
        event_type: EventType,
        event_data: Dict
    ) -> Dict:
        """
        Append event to constitutional memory.

        Args:
            event_type: Type of event (from EventType enum)
            event_data: Event-specific payload (see schema.yaml)

        Returns:
            Written event with hash
        """
        last_event = self._get_last_event()

        if last_event is None:
            # Should not happen (genesis should exist)
            self._write_genesis()
            last_event = self._get_last_event()

        event = {
            "sequence_number": last_event["sequence_number"] + 1,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type.value,
            "event_data": event_data,
            "previous_hash": last_event["event_hash"],
            "event_hash": ""
        }
        event["event_hash"] = self._compute_event_hash(event)

        # Append to log (atomic write)
        with open(self.events_file, 'a') as f:
            f.write(json.dumps(event) + "\n")

        return event

    def read_events(
        self,
        event_type: Optional[EventType] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Read events from memory (observation only).

        Args:
            event_type: Filter by event type (optional)
            limit: Max events to return (optional)

        Returns:
            List of events (newest first)
        """
        if not self.events_file.exists():
            return []

        events = []
        with open(self.events_file, 'r') as f:
            for line in f:
                event = json.loads(line)
                if event_type is None or event["event_type"] == event_type.value:
                    events.append(event)

        # Reverse (newest first)
        events.reverse()

        if limit:
            events = events[:limit]

        return events

    def verify_chain_integrity(self) -> Dict:
        """
        Verify hash chain integrity (tamper detection).

        Returns:
            Integrity report with status and any errors
        """
        if not self.events_file.exists():
            return {"status": "PASS", "message": "No events yet"}

        events = []
        with open(self.events_file, 'r') as f:
            for line in f:
                events.append(json.loads(line))

        # Check each event's hash
        for i, event in enumerate(events):
            # Verify event hash
            computed_hash = self._compute_event_hash(event)
            if computed_hash != event["event_hash"]:
                return {
                    "status": "FAIL",
                    "error": f"Hash mismatch at sequence {event['sequence_number']}",
                    "expected": event["event_hash"],
                    "computed": computed_hash
                }

            # Verify chain link (except genesis)
            if i > 0:
                prev_event = events[i-1]
                if event["previous_hash"] != prev_event["event_hash"]:
                    return {
                        "status": "FAIL",
                        "error": f"Chain break at sequence {event['sequence_number']}",
                        "previous_event_hash": prev_event["event_hash"],
                        "claimed_previous_hash": event["previous_hash"]
                    }

        return {
            "status": "PASS",
            "total_events": len(events),
            "message": "Chain integrity verified"
        }

    def get_stats(self) -> Dict:
        """Get memory statistics (observation only)"""
        if not self.events_file.exists():
            return {"total_events": 0}

        events = self.read_events()
        event_counts = {}

        for event in events:
            event_type = event["event_type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        return {
            "total_events": len(events),
            "event_counts": event_counts,
            "latest_event": events[0] if events else None
        }


# Convenience functions for common event types

def record_refusal(
    memory: ConstitutionalMemory,
    refusal_code: str,
    domain: str,
    query_pattern: Optional[str] = None
) -> Dict:
    """Record F-domain refusal event"""
    event_data = {
        "refusal_code": refusal_code,
        "domain": domain
    }
    if query_pattern:
        event_data["query_pattern"] = query_pattern

    return memory.append_event(EventType.REFUSAL_EVENT, event_data)


def record_boundary_test(
    memory: ConstitutionalMemory,
    test_type: str,
    result: str,
    details: Optional[str] = None
) -> Dict:
    """Record boundary test event"""
    event_data = {
        "test_type": test_type,
        "result": result
    }
    if details:
        event_data["details"] = details

    return memory.append_event(EventType.BOUNDARY_TEST, event_data)


def record_awareness_intervention(
    memory: ConstitutionalMemory,
    gap_identified: str,
    correction_applied: str,
    result: str
) -> Dict:
    """Record awareness intervention event"""
    event_data = {
        "gap_identified": gap_identified,
        "correction_applied": correction_applied,
        "result": result
    }
    return memory.append_event(EventType.AWARENESS_INTERVENTION, event_data)


def record_verification(
    memory: ConstitutionalMemory,
    verification_type: str,
    result: str,
    derivative_id: Optional[str] = None
) -> Dict:
    """Record verification run event"""
    event_data = {
        "verification_type": verification_type,
        "result": result
    }
    if derivative_id:
        event_data["derivative_id"] = derivative_id

    return memory.append_event(EventType.VERIFICATION_RUN, event_data)


def record_drift(
    memory: ConstitutionalMemory,
    drift_type: str,
    severity: str,
    details: Optional[str] = None
) -> Dict:
    """Record drift detection event"""
    event_data = {
        "drift_type": drift_type,
        "severity": severity
    }
    if details:
        event_data["details"] = details

    return memory.append_event(EventType.DRIFT_DETECTION, event_data)
