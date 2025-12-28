"""
VSD-0 Tamper-Evident Audit Log
Version: 0.1
Purpose: Immutable record of all constitutional events
Compliance: DOC v1.0 Section 4.2 (audit trail requirement)

This module implements append-only, tamper-evident logging of:
- Boundary crossings
- Drift events
- Refusal events
- Verification requests

The audit log proves VSD-0's constitutional compliance.
"""

import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AuditEntry:
    """Single entry in the audit log"""
    sequence_number: int
    timestamp: str
    event_type: str  # "drift_event", "refusal_event", "boundary_crossing", "verification"
    event_data: dict
    previous_hash: str
    entry_hash: str

    def to_dict(self) -> dict:
        return {
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class TamperEvidentAuditLog:
    """
    Append-only, hash-chained audit log.

    Properties:
    - Append-only (no modifications, no deletions)
    - Hash-chained (each entry links to previous)
    - Tamper-evident (modification breaks chain)
    - Verifiable (anyone can validate integrity)

    Required by DOC v1.0 Section 4.2:
    - Maintain immutable audit trail of all boundary proximity events
    - Log all monitoring checks with timestamps
    """

    def __init__(self, log_file_path: str):
        """
        Initialize audit log.

        Args:
            log_file_path: Path to audit log file (JSON lines format)
        """
        self.log_file = Path(log_file_path)
        self.sequence_number = 0
        self.last_hash = "0" * 64  # Genesis hash (all zeros)

        # Create log file if it doesn't exist
        if not self.log_file.exists():
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self.log_file.touch()
            self._write_genesis_entry()
        else:
            # Load last entry to continue chain
            self._load_last_entry()

    def _compute_entry_hash(self, entry_data: dict, previous_hash: str) -> str:
        """
        Compute hash for audit entry.

        Hash includes:
        - Sequence number
        - Timestamp
        - Event type
        - Event data
        - Previous hash

        This creates a tamper-evident chain.
        """
        hash_input = json.dumps({
            "sequence_number": entry_data["sequence_number"],
            "timestamp": entry_data["timestamp"],
            "event_type": entry_data["event_type"],
            "event_data": entry_data["event_data"],
            "previous_hash": previous_hash
        }, sort_keys=True)

        return hashlib.sha256(hash_input.encode()).hexdigest()

    def _write_genesis_entry(self):
        """Write genesis entry (log initialization)"""
        genesis = {
            "sequence_number": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "genesis",
            "event_data": {
                "message": "VSD-0 audit log initialized",
                "version": "0.1",
                "compliance": "DOC v1.0"
            },
            "previous_hash": self.last_hash,
            "entry_hash": ""
        }

        genesis["entry_hash"] = self._compute_entry_hash(genesis, self.last_hash)

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(genesis) + "\n")

        self.last_hash = genesis["entry_hash"]

    def _load_last_entry(self):
        """Load last entry from log to continue chain"""
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        last_entry = json.loads(last_line)
                        self.sequence_number = last_entry["sequence_number"]
                        self.last_hash = last_entry["entry_hash"]
        except Exception as e:
            print(f"[AUDIT LOG] Warning: Failed to load last entry: {e}")
            # Start fresh if load fails
            self.sequence_number = 0
            self.last_hash = "0" * 64

    def append(self, event_type: str, event_data: dict):
        """
        Append new entry to audit log.

        Args:
            event_type: Type of event ("drift_event", "refusal_event", etc.)
            event_data: Event data (must be JSON-serializable dict)
        """
        self.sequence_number += 1

        entry_dict = {
            "sequence_number": self.sequence_number,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "event_data": event_data,
            "previous_hash": self.last_hash,
            "entry_hash": ""
        }

        # Compute entry hash
        entry_hash = self._compute_entry_hash(entry_dict, self.last_hash)
        entry_dict["entry_hash"] = entry_hash

        # Write to file (append-only)
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry_dict) + "\n")

        # Update chain
        self.last_hash = entry_hash

    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """
        Verify audit log integrity.

        Checks that:
        - All hashes are valid
        - Chain is unbroken
        - No modifications or deletions

        Returns:
            (is_valid, error_message)
        """
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()

            if not lines:
                return (False, "Audit log is empty")

            previous_hash = "0" * 64  # Genesis hash

            for i, line in enumerate(lines):
                entry = json.loads(line.strip())

                # Check sequence number
                if entry["sequence_number"] != i:
                    return (False, f"Sequence break at entry {i}")

                # Check previous hash
                if entry["previous_hash"] != previous_hash:
                    return (False, f"Hash chain broken at entry {i}")

                # Recompute entry hash
                computed_hash = self._compute_entry_hash(entry, previous_hash)

                if computed_hash != entry["entry_hash"]:
                    return (False, f"Hash mismatch at entry {i} (tampering detected)")

                previous_hash = entry["entry_hash"]

            return (True, None)

        except Exception as e:
            return (False, f"Verification failed: {str(e)}")

    def get_entries(self, event_type: Optional[str] = None,
                   start_seq: int = 0, end_seq: Optional[int] = None) -> List[dict]:
        """
        Get audit log entries.

        Args:
            event_type: Filter by event type (None = all types)
            start_seq: Start sequence number (inclusive)
            end_seq: End sequence number (inclusive, None = end of log)

        Returns:
            List of entries matching filters
        """
        entries = []

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line.strip())

                    # Apply sequence filter
                    if entry["sequence_number"] < start_seq:
                        continue
                    if end_seq and entry["sequence_number"] > end_seq:
                        break

                    # Apply type filter
                    if event_type and entry["event_type"] != event_type:
                        continue

                    entries.append(entry)

        except Exception as e:
            print(f"[AUDIT LOG] Error reading entries: {e}")

        return entries

    def get_stats(self) -> dict:
        """Get audit log statistics"""
        stats = {
            "total_entries": 0,
            "event_types": {},
            "latest_timestamp": None,
            "integrity_verified": False
        }

        try:
            entries = self.get_entries()
            stats["total_entries"] = len(entries)

            for entry in entries:
                event_type = entry["event_type"]
                stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1
                stats["latest_timestamp"] = entry["timestamp"]

            # Verify integrity
            is_valid, error = self.verify_integrity()
            stats["integrity_verified"] = is_valid
            if error:
                stats["integrity_error"] = error

        except Exception as e:
            stats["error"] = str(e)

        return stats

    def export_compliance_report(self, output_path: str):
        """
        Export compliance report (all entries as JSON).

        Used for sovereignty verification.

        Args:
            output_path: Path to write report
        """
        entries = self.get_entries()

        report = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "vsd_version": "0.1",
            "doc_compliance": "v1.0",
            "total_entries": len(entries),
            "integrity_verified": self.verify_integrity()[0],
            "entries": entries
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"[AUDIT LOG] Compliance report exported to {output_path}")


# Convenience function for creating audit log callback
def create_audit_log_callback(log_file: str):
    """
    Create audit log callback function.

    Returns a function that can be passed to drift_monitor and f_domain_filter
    to automatically log events.

    Args:
        log_file: Path to audit log file

    Returns:
        Callback function
    """
    audit_log = TamperEvidentAuditLog(log_file)

    def callback(event_data: dict, event_type: str):
        """Log event to audit log"""
        audit_log.append(event_type, event_data)

    return callback


if __name__ == "__main__":
    # Example: Create audit log and test integrity
    import sys

    if len(sys.argv) < 2:
        print("Usage: python audit_log.py <log_file_path>")
        sys.exit(1)

    log_file = sys.argv[1]

    # Create/load audit log
    audit_log = TamperEvidentAuditLog(log_file)

    # Add test entry
    audit_log.append("test_event", {
        "message": "Test audit entry",
        "test": True
    })

    # Verify integrity
    is_valid, error = audit_log.verify_integrity()

    print(f"=== Audit Log Status ===")
    print(f"Log File: {log_file}")
    print(f"Integrity Valid: {is_valid}")
    if error:
        print(f"Error: {error}")

    # Print stats
    stats = audit_log.get_stats()
    print(f"\nStats:")
    print(f"  Total Entries: {stats['total_entries']}")
    print(f"  Event Types: {stats['event_types']}")
    print(f"  Latest: {stats['latest_timestamp']}")
