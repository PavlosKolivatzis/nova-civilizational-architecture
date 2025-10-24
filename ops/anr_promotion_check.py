#!/usr/bin/env python3
"""Phase 11 ANR promotion readiness check."""

from __future__ import annotations

import sys

import requests


METRIC_NAMES = {
    "rsi": "nova_anr_rsi",
    "rollbacks": "nova_anr_rollbacks_per_1k",
    "tri_median": "nova_anr_median_tri_delta",
    "fast_cap": "nova_anr_fast_cap_prob",
}


def extract_metric(metrics_blob: str, name: str) -> float | None:
    """Return metric value from Prometheus text exposition."""
    needle = f"{name} "
    for line in metrics_blob.splitlines():
        if line.startswith(needle):
            try:
                return float(line.split()[-1])
            except ValueError:
                return None
    return None


def main() -> int:
    try:
        resp = requests.get("http://127.0.0.1:8000/metrics", timeout=5)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - we want a single rollback path
        print(f"Failed to retrieve metrics: {exc}")
        return 1

    metrics = resp.text
    values = {alias: extract_metric(metrics, metric) for alias, metric in METRIC_NAMES.items()}

    print(
        "RSI={rsi} rollbacks_per_1k={rollbacks} "
        "TRIΔ_median={tri_median} fast_cap={fast_cap}".format(**values)
    )

    ok = (
        (values["rsi"] is not None and values["rsi"] >= 0.85)
        and (values["rollbacks"] is not None and values["rollbacks"] <= 0.1)
        and (values["tri_median"] is not None and values["tri_median"] >= 0.0)
        and (values["fast_cap"] is not None and values["fast_cap"] <= 0.15)
    )

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
