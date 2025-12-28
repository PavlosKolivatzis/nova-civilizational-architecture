"""
Constitutional Memory CLI

Simple interface for recording and querying constitutional events.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from constitutional_memory.memory import (
    ConstitutionalMemory,
    EventType,
    record_refusal,
    record_boundary_test,
    record_awareness_intervention,
    record_verification,
    record_drift
)
import json


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Constitutional Memory CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Record commands
    record_parser = subparsers.add_parser("record", help="Record event")
    record_parser.add_argument("event_type", choices=["refusal", "test", "awareness", "verification", "drift"])
    record_parser.add_argument("--data", help="Event data as JSON string", required=True)

    # Read commands
    read_parser = subparsers.add_parser("read", help="Read events")
    read_parser.add_argument("--type", choices=["refusal", "test", "awareness", "verification", "drift"])
    read_parser.add_argument("--limit", type=int, help="Max events to return")

    # Verify chain
    subparsers.add_parser("verify", help="Verify chain integrity")

    # Stats
    subparsers.add_parser("stats", help="Show memory statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    memory = ConstitutionalMemory()

    if args.command == "record":
        event_data = json.loads(args.data)

        if args.event_type == "refusal":
            event = record_refusal(
                memory,
                refusal_code=event_data["refusal_code"],
                domain=event_data["domain"],
                query_pattern=event_data.get("query_pattern")
            )
        elif args.event_type == "test":
            event = record_boundary_test(
                memory,
                test_type=event_data["test_type"],
                result=event_data["result"],
                details=event_data.get("details")
            )
        elif args.event_type == "awareness":
            event = record_awareness_intervention(
                memory,
                gap_identified=event_data["gap_identified"],
                correction_applied=event_data["correction_applied"],
                result=event_data["result"]
            )
        elif args.event_type == "verification":
            event = record_verification(
                memory,
                verification_type=event_data["verification_type"],
                result=event_data["result"],
                derivative_id=event_data.get("derivative_id")
            )
        elif args.event_type == "drift":
            event = record_drift(
                memory,
                drift_type=event_data["drift_type"],
                severity=event_data["severity"],
                details=event_data.get("details")
            )

        print(json.dumps(event, indent=2))

    elif args.command == "read":
        event_type_map = {
            "refusal": EventType.REFUSAL_EVENT,
            "test": EventType.BOUNDARY_TEST,
            "awareness": EventType.AWARENESS_INTERVENTION,
            "verification": EventType.VERIFICATION_RUN,
            "drift": EventType.DRIFT_DETECTION
        }

        event_type = event_type_map.get(args.type) if args.type else None
        events = memory.read_events(event_type=event_type, limit=args.limit)

        for event in events:
            print(json.dumps(event, indent=2))

    elif args.command == "verify":
        result = memory.verify_chain_integrity()
        print(json.dumps(result, indent=2))

    elif args.command == "stats":
        stats = memory.get_stats()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
