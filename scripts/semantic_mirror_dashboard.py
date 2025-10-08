#!/usr/bin/env python3
"""
Nova Semantic Mirror Dashboard

A lightweight monitoring dashboard for the Semantic Mirror system that provides
health status, metrics visualization, and multiple output formats.

Usage Examples:
    python scripts/semantic_mirror_dashboard.py --once
    python scripts/semantic_mirror_dashboard.py --watch --interval 2
    python scripts/semantic_mirror_dashboard.py --serve 8787 --watch
    python scripts/semantic_mirror_dashboard.py --csv mirror_metrics.csv --once
    python scripts/semantic_mirror_dashboard.py --compact --watch

Features:
- ASCII-safe output for Windows CP1252 consoles
- Stdlib-only implementation (Python 3.10-3.13 compatible)
- Multiple output modes: dashboard, CSV, HTTP server, compact
- Graceful fallbacks when semantic_mirror_setup unavailable
- Real-time monitoring with configurable refresh intervals
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, Any, Union


def _get_config_source():
    """Determine source of semantic mirror config flags."""
    # OS env takes precedence
    if "NOVA_SEMANTIC_MIRROR_ENABLED" in os.environ:
        return "env"

    # Check .env.semantic_mirror
    env_file = Path(".env.semantic_mirror")
    if env_file.exists():
        return "dotenv"

    # Check orchestrator.config module
    try:
        from orchestrator.config import config
        if hasattr(config, "SEMANTIC_MIRROR_ENABLED"):
            return "config"
    except (ImportError, AttributeError):
        pass

    return "default"


def _safe_stdout_utf8():
    """Try to reconfigure stdout for UTF-8 on Windows, fallback gracefully."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        # Older Python versions or unsupported platforms
        pass


def _read_health() -> Dict[str, Any]:
    """
    Read Semantic Mirror health status with fallback strategy.

    Returns:
        Dict containing status, issues, metrics, and metadata
    """
    try:
        # Preferred: Use the setup module's health function
        from orchestrator.semantic_mirror_setup import get_semantic_mirror_health
        return get_semantic_mirror_health()
    except ImportError:
        try:
            # Fallback: Synthesize health from semantic mirror metrics
            from orchestrator.semantic_mirror import get_semantic_mirror
            mirror = get_semantic_mirror()
            metrics = mirror.get_metrics()

            # Determine health status based on metrics
            issues = []
            if metrics.get("active_contexts", 0) == 0:
                issues.append("no_active_contexts")

            total_queries = metrics.get("queries_successful", 0) + metrics.get("queries_access_denied", 0)
            if total_queries > 0:
                denial_rate = metrics.get("queries_access_denied", 0) / total_queries
                if denial_rate > 0.1:  # > 10% denial rate
                    issues.append("high_access_denial_rate")

            if metrics.get("queries_rate_limited", 0) > 0:
                issues.append("rate_limiting_active")

            status = "degraded" if issues else "healthy"

            return {
                "status": status,
                "issues": issues,
                "metrics": {
                    "active_contexts": metrics.get("active_contexts", 0),
                    "total_contexts": metrics.get("total_contexts", 0),
                    "queries_successful": metrics.get("queries_successful", 0),
                    "queries_access_denied": metrics.get("queries_access_denied", 0),
                    "queries_not_found": metrics.get("queries_not_found", 0),
                    "queries_rate_limited": metrics.get("queries_rate_limited", 0),
                    "queries_expired": metrics.get("queries_expired", 0),
                    "publications_total": metrics.get("publications_total", 0),
                    "entries_expired": metrics.get("entries_expired", 0)
                },
                "feature_enabled": True,
                "timestamp": time.time()
            }
        except Exception as e:
            # Ultimate fallback: Return error state
            return {
                "status": "error",
                "issues": [f"health_check_failed: {str(e)}"],
                "metrics": {},
                "feature_enabled": False,
                "timestamp": time.time()
            }


def _ratio(numerator: Union[int, float], denominator: Union[int, float]) -> float:
    """Safely compute ratio with zero-denominator protection."""
    return numerator / denominator if denominator > 0 else 0.0


def _bar(percentage: float, width: int = 24, fill: str = "#", empty: str = "-") -> str:
    """Render an ASCII progress bar for the given percentage (0.0-1.0)."""
    filled_width = int(percentage * width)
    return fill * filled_width + empty * (width - filled_width)


def render_snapshot(timestamp: datetime, health_data: Dict[str, Any]) -> str:
    """
    Render a complete dashboard snapshot as ASCII text.

    Args:
        timestamp: Current timestamp
        health_data: Health data from _read_health()

    Returns:
        Formatted dashboard string
    """
    status = health_data.get("status", "unknown")
    issues = health_data.get("issues", [])
    metrics = health_data.get("metrics", {})
    feature_enabled = health_data.get("feature_enabled", False)

    # Extract key metrics with defaults
    active_contexts = metrics.get("active_contexts", 0)
    total_contexts = metrics.get("total_contexts", 0)
    publications_total = metrics.get("publications_total", 0)
    queries_successful = metrics.get("queries_successful", 0)
    queries_not_found = metrics.get("queries_not_found", 0)
    queries_access_denied = metrics.get("queries_access_denied", 0)
    queries_rate_limited = metrics.get("queries_rate_limited", 0)
    queries_expired = metrics.get("queries_expired", 0)
    entries_expired = metrics.get("entries_expired", 0)

    # Calculate total reads and ratios
    mirror_reads_total = queries_successful + queries_not_found + queries_access_denied + queries_rate_limited + queries_expired
    hit_rate = _ratio(queries_successful, mirror_reads_total)
    denial_rate = _ratio(queries_access_denied, mirror_reads_total)
    rate_limit_rate = _ratio(queries_rate_limited, mirror_reads_total)

    # Build dashboard output
    lines = [
        "=" * 72,
        f"Nova Semantic Mirror Dashboard - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 72,
        "",
        f"Status: {status.upper()}",
        f"Config Source: {_get_config_source()}",
        f"Feature Enabled: {'Yes' if feature_enabled else 'No'}",
        f"Issues: {', '.join(issues) if issues else 'None'}",
        "",
        "METRICS:",
        f"  Active Contexts:     {active_contexts:,}",
        f"  Total Contexts:      {total_contexts:,}",
        f"  Publications:        {publications_total:,}",
        f"  Total Reads:         {mirror_reads_total:,}",
        "",
        "QUERY BREAKDOWN:",
        f"  Successful:          {queries_successful:,}",
        f"  Not Found:           {queries_not_found:,}",
        f"  Access Denied:       {queries_access_denied:,}",
        f"  Rate Limited:        {queries_rate_limited:,}",
        f"  Expired:             {queries_expired:,}",
        "",
        "PERFORMANCE RATIOS:",
        f"  Hit Rate:            {hit_rate:6.1%} [{_bar(hit_rate)}]",
        f"  Denial Rate:         {denial_rate:6.1%} [{_bar(denial_rate)}]",
        f"  Rate Limit Rate:     {rate_limit_rate:6.1%} [{_bar(rate_limit_rate)}]",
        "",
        "MAINTENANCE:",
        f"  Entries Expired:     {entries_expired:,}",
        "",
        "=" * 72
    ]

    return "\n".join(lines)


def render_compact(timestamp: datetime, health_data: Dict[str, Any]) -> str:
    """Render a one-line compact summary."""
    status = health_data.get("status", "unknown")
    metrics = health_data.get("metrics", {})

    active_contexts = metrics.get("active_contexts", 0)
    queries_successful = metrics.get("queries_successful", 0)
    queries_access_denied = metrics.get("queries_access_denied", 0)
    queries_rate_limited = metrics.get("queries_rate_limited", 0)
    queries_expired = metrics.get("queries_expired", 0)
    queries_not_found = metrics.get("queries_not_found", 0)

    mirror_reads_total = queries_successful + queries_not_found + queries_access_denied + queries_rate_limited + queries_expired
    hit_rate = _ratio(queries_successful, mirror_reads_total)
    denial_rate = _ratio(queries_access_denied, mirror_reads_total)
    rate_limit_rate = _ratio(queries_rate_limited, mirror_reads_total)

    note_suffix = ""
    if active_contexts == 0:
        note_suffix = " note=stateless_probe(use --serve or publish heartbeat)"

    source = _get_config_source()
    return (f"{timestamp.strftime('%H:%M:%S')} status={status} "
            f"hit={hit_rate:.1%} deny={denial_rate:.1%} rl={rate_limit_rate:.1%} "
            f"reads={mirror_reads_total} active={active_contexts} source={source}{note_suffix}")


def maybe_write_csv(csv_path: str, timestamp: datetime, health_data: Dict[str, Any]) -> None:
    """Write health data to CSV file, creating headers if file doesn't exist."""
    file_exists = os.path.exists(csv_path)

    with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'timestamp', 'status', 'feature_enabled', 'issues_count',
            'active_contexts', 'total_contexts', 'publications_total',
            'queries_successful', 'queries_not_found', 'queries_access_denied',
            'queries_rate_limited', 'queries_expired', 'entries_expired',
            'mirror_reads_total', 'hit_rate', 'denial_rate', 'rate_limit_rate'
        ]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header if file is new
        if not file_exists:
            writer.writeheader()

        # Prepare data row
        metrics = health_data.get("metrics", {})
        mirror_reads_total = (metrics.get("queries_successful", 0) +
                             metrics.get("queries_not_found", 0) +
                             metrics.get("queries_access_denied", 0) +
                             metrics.get("queries_rate_limited", 0) +
                             metrics.get("queries_expired", 0))

        row_data = {
            'timestamp': timestamp.isoformat(),
            'status': health_data.get("status", "unknown"),
            'feature_enabled': health_data.get("feature_enabled", False),
            'issues_count': len(health_data.get("issues", [])),
            'active_contexts': metrics.get("active_contexts", 0),
            'total_contexts': metrics.get("total_contexts", 0),
            'publications_total': metrics.get("publications_total", 0),
            'queries_successful': metrics.get("queries_successful", 0),
            'queries_not_found': metrics.get("queries_not_found", 0),
            'queries_access_denied': metrics.get("queries_access_denied", 0),
            'queries_rate_limited': metrics.get("queries_rate_limited", 0),
            'queries_expired': metrics.get("queries_expired", 0),
            'entries_expired': metrics.get("entries_expired", 0),
            'mirror_reads_total': mirror_reads_total,
            'hit_rate': _ratio(metrics.get("queries_successful", 0), mirror_reads_total),
            'denial_rate': _ratio(metrics.get("queries_access_denied", 0), mirror_reads_total),
            'rate_limit_rate': _ratio(metrics.get("queries_rate_limited", 0), mirror_reads_total)
        }

        writer.writerow(row_data)


class QuietHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler with minimal logging."""

    def log_message(self, format, *args):
        """Override to suppress request logging."""
        pass

    def do_GET(self):
        """Handle GET requests for /health and /metrics endpoints."""
        try:
            if self.path == '/health':
                health_data = _read_health()
                self._send_json_response(health_data)
            elif self.path == '/metrics':
                health_data = _read_health()
                response = {"metrics": health_data.get("metrics", {})}
                self._send_json_response(response)
            else:
                self._send_error_response(404, "Not Found")
        except Exception as e:
            self._send_error_response(500, f"Internal Server Error: {str(e)}")

    def _send_json_response(self, data: Dict[str, Any]):
        """Send JSON response with proper headers."""
        json_data = json.dumps(data, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(json_data)))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))

    def _send_error_response(self, code: int, message: str):
        """Send error response."""
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))


def serve_http(port: int, watch_mode: bool = False, interval: float = 2.0):
    """Start HTTP server for dashboard endpoints."""
    server = HTTPServer(('localhost', port), QuietHTTPRequestHandler)
    print(f"Semantic Mirror Dashboard server starting on http://localhost:{port}")
    print("Endpoints: /health, /metrics")
    print("Press Ctrl+C to stop...")

    if watch_mode:
        print(f"Watch mode enabled with {interval}s refresh interval")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()
        server.server_close()


def main():
    """Main dashboard application."""
    parser = argparse.ArgumentParser(
        description="Nova Semantic Mirror Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/semantic_mirror_dashboard.py --once
  python scripts/semantic_mirror_dashboard.py --watch --interval 2
  python scripts/semantic_mirror_dashboard.py --serve 8787 --watch
  python scripts/semantic_mirror_dashboard.py --csv mirror_metrics.csv --once
  python scripts/semantic_mirror_dashboard.py --compact --watch
        """
    )

    parser.add_argument('--once', action='store_true',
                       help='Print one snapshot and exit (default if --watch not set)')
    parser.add_argument('--watch', action='store_true',
                       help='Continuously refresh until Ctrl+C')
    parser.add_argument('--interval', type=float, default=2.0,
                       help='Refresh interval in seconds (default: 2.0)')
    parser.add_argument('--csv', type=str,
                       help='Append metrics to CSV file (creates with headers if new)')
    parser.add_argument('--serve', type=int,
                       help='Start HTTP server on specified port')
    parser.add_argument('--compact', action='store_true',
                       help='Print one-line compact summary instead of full dashboard')

    args = parser.parse_args()

    # Configure stdout for better Unicode support
    _safe_stdout_utf8()

    # Handle HTTP server mode
    if args.serve:
        serve_http(args.serve, args.watch, args.interval)
        return

    # Determine operation mode
    watch_mode = args.watch
    if not watch_mode and not args.once:
        # Default to --once if neither specified
        watch_mode = False

    try:
        while True:
            timestamp = datetime.now()
            health_data = _read_health()

            # Render output based on mode
            if args.compact:
                output = render_compact(timestamp, health_data)
            else:
                output = render_snapshot(timestamp, health_data)

            print(output)

            # Write to CSV if requested
            if args.csv:
                maybe_write_csv(args.csv, timestamp, health_data)

            # Exit if not in watch mode
            if not watch_mode:
                break

            # Wait for next iteration
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()