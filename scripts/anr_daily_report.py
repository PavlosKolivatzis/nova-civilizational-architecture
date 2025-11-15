#!/usr/bin/env python3
"""
ANR Daily Report Generator

Analyzes NDJSON ledger of ANR decisions to generate RSI, rollback, and live-rate metrics.
Outputs JSON summary and CSV for Grafana/Loki ingestion.
"""

import os
import sys
import json
import csv
import argparse
import datetime as dt

def main():
    parser = argparse.ArgumentParser(description="Generate ANR daily metrics report")
    parser.add_argument("--ledger", default="run/anr_ledger.ndjson",
                       help="Path to ANR ledger NDJSON file")
    parser.add_argument("--lookback-min", type=int, default=1440,
                       help="Lookback window in minutes (default: 24h)")
    parser.add_argument("--out-csv", default="run/anr_daily_report.csv",
                       help="Output CSV file path")
    args = parser.parse_args()

    now = dt.datetime.utcnow()
    start = now - dt.timedelta(minutes=args.lookback_min)

    # Metrics counters
    count = live = agree = rollbacks = 0
    rows = []

    try:
        with open(args.ledger, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Filter by timestamp if available
                ts = entry.get("t")
                if ts:
                    try:
                        t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                        if t < start:
                            continue
                    except (ValueError, TypeError):
                        pass  # Skip malformed timestamps

                count += 1

                # Extract decision details
                live_route = (entry.get("live") or {}).get("route")
                shadow_argmax = (entry.get("shadow") or {}).get("argmax")

                if live_route:
                    live += 1

                if live_route and shadow_argmax and live_route == shadow_argmax:
                    agree += 1

                # Extract rollback indicator
                rollback = (((entry.get("rewards") or {}).get("deployment") or {}).get("rollback") or 0)
                if rollback > 0:
                    rollbacks += 1

                # Add to CSV rows
                rows.append([
                    entry.get("id", ""),
                    ts or "",
                    live_route or "",
                    shadow_argmax or "",
                    int(rollback > 0)
                ])

    except FileNotFoundError:
        print(f"Warning: Ledger file not found: {args.ledger}", file=sys.stderr)

    # Generate summary
    summary = {
        "window_minutes": args.lookback_min,
        "decisions": count,
        "live_rate": round(live / count, 4) if count > 0 else None,
        "rsi": round(agree / live, 4) if live > 0 else None,
        "rollbacks": rollbacks,
        "generated_at": now.isoformat() + "Z"
    }

    # Output JSON summary
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # Write CSV report
    os.makedirs(os.path.dirname(args.out_csv) or ".", exist_ok=True)
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "t", "live_route", "shadow_argmax", "rollback"])
        writer.writerows(rows)

    print(f"\nCSV report written: {args.out_csv}", file=sys.stderr)

if __name__ == "__main__":
    main()
