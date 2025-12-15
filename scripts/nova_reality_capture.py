"""Nova Reality Capture - Phase 1 MVO (Minimal Viable Observer).

Monitor-only tool that polls Nova's Prometheus /metrics endpoint, captures
Slot02 temporal USM metrics per turn, and writes RT evidence files.

Constraints (Phase 15 / pre-Phase 16):
- Metrics only (no conversation text, no PII).
- Governance remains OFF (NOVA_ENABLE_TEMPORAL_GOVERNANCE=0).
- Observability-only: never modifies Nova state, never triggers actions.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    # Prefer requests if available; fall back to urllib otherwise.
    import requests  # type: ignore[import]
except Exception:  # pragma: no cover - optional dependency
    requests = None  # type: ignore[assignment]
    import urllib.request

__version__ = "0.1.0"
DEFAULT_NOVA_VERSION = "0.9.0"


PROM_METRIC_RE = re.compile(r'(\w+)\{([^}]+)\}\s+([\-0-9.eE]+)')

TARGET_METRICS = {
    "nova_extraction_present",
    "nova_rho_temporal",
    "nova_coherence_temporal",
    "nova_temporal_state",
}


@dataclass
class TurnSnapshot:
    turn: int
    ts: float
    extraction_present: Optional[bool] = None
    rho_temporal: Optional[float] = None
    coherence_temporal: Optional[float] = None
    temporal_state: Optional[str] = None


@dataclass
class SessionBuffer:
    session_id: str
    first_seen_ts: float
    last_new_turn_ts: float
    max_turn: int = 0
    turns: Dict[int, TurnSnapshot] = field(default_factory=dict)


def _now_utc_iso() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _ts_to_iso(ts: float) -> str:
    return _dt.datetime.utcfromtimestamp(ts).replace(microsecond=0).isoformat() + "Z"


def _read_git_sha(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return "unknown"
        sha = result.stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if status.returncode == 0 and status.stdout.strip():
            sha += "-dirty"
        return sha
    except Exception:
        return "unknown"


def _read_nova_version(repo_root: Path) -> str:
    """Best-effort Nova version; fall back to DEFAULT_NOVA_VERSION."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return DEFAULT_NOVA_VERSION


def _parse_prometheus_metrics(text: str) -> List[Tuple[str, Dict[str, str], float]]:
    """Parse Prometheus text format and return list of (metric, labels, value)."""
    samples: List[Tuple[str, Dict[str, str], float]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = PROM_METRIC_RE.match(line)
        if not m:
            continue
        metric_name = m.group(1)
        if metric_name not in TARGET_METRICS:
            continue
        labels_raw = m.group(2)
        value_str = m.group(3)

        labels: Dict[str, str] = {}
        for part in labels_raw.split(","):
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"')
            labels[k] = v

        try:
            value = float(value_str)
        except ValueError:
            continue

        samples.append((metric_name, labels, value))
    return samples


def _fetch_metrics(endpoint: str, timeout: float = 5.0) -> Optional[str]:
    try:
        if requests is not None:
            resp = requests.get(endpoint, timeout=timeout)
            if resp.status_code != 200:
                return None
            return resp.text
        else:  # urllib fallback
            with urllib.request.urlopen(endpoint, timeout=timeout) as resp:  # type: ignore[attr-defined]
                if resp.status != 200:  # type: ignore[attr-defined]
                    return None
                data = resp.read()
                return data.decode("utf-8", errors="replace")
    except Exception:
        return None


def _ensure_directories(out_dir: Path, index_path: Path, repo_root: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    evidence_root = repo_root / "evidence"
    evidence_root.mkdir(parents=True, exist_ok=True)
    readme = evidence_root / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Nova Reality Capture Evidence\n\n"
            "- Metrics-only captures from `/metrics` (no conversation text, no PII).\n"
            "- All captures collected with `NOVA_ENABLE_TEMPORAL_GOVERNANCE=0` (governance OFF).\n"
            "- Temporal USM and `extraction_present` annotation must be enabled for Slot02.\n"
            "- Files under `evidence/rt/` follow the RT JSON schema.\n"
            "- Index at `evidence/index/rt_index.csv` tracks RT IDs and basic metadata.\n",
            encoding="utf-8",
        )


def _next_rt_id(index_path: Path) -> str:
    if not index_path.exists():
        # Create index with header
        with index_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "rt_id",
                    "session_id",
                    "capture_mode",
                    "total_turns",
                    "final_extraction_present",
                    "final_rho",
                    "final_coherence",
                    "operator_annotation",
                    "git_sha",
                    "timestamp",
                ]
            )
        return "RT-001"

    last_id_num = 0
    with index_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if not row or not row[0].startswith("RT-"):
                continue
            try:
                n = int(row[0].split("-")[1])
                if n > last_id_num:
                    last_id_num = n
            except Exception:
                continue

    return f"RT-{last_id_num + 1:03d}"


def _encode_extraction_present(value: Optional[bool]) -> Optional[bool]:
    return value


def _decode_extraction_present_gauge(v: float) -> Optional[bool]:
    if v == 1.0:
        return True
    if v == 0.0:
        return False
    return None


def _decode_temporal_state_gauge(v: float) -> Optional[str]:
    if v == 0.0:
        return "void"
    if v == 1.0:
        return "warming_up"
    if v == 2.0:
        return "active"
    if v == -1.0:
        return "unknown"
    return "unknown"


def _decode_float_signal(v: float) -> Optional[float]:
    if v < 0.0:
        return None
    return v


def _collect_operator_annotation(no_prompt: bool) -> Dict[str, Any]:
    operator = os.getenv("NOVA_OPERATOR_NAME", "unknown")

    if no_prompt:
        return {
            "extraction_present": None,
            "pattern_type": None,
            "complexity": None,
            "notes": "",
            "operator": operator,
            "confidence": None,
        }

    print()
    print("[Reality Capture] Operator annotation")

    # 1. extraction_present
    raw1 = input(
        "1. Was extraction present [True/False/Uncertain] (enter to skip): "
    ).strip()
    ep: Optional[bool]
    if not raw1:
        ep = None
    else:
        low = raw1.lower()
        if low in ("true", "t", "yes", "y"):
            ep = True
        elif low in ("false", "f", "no", "n"):
            ep = False
        else:
            ep = None

    pattern_type = input(
        "2. Pattern type (if extraction) [gaslighting/authority/dependency/paternalism/other/skip]: "
    ).strip()
    if not pattern_type or pattern_type.lower() in ("skip", "none"):
        pattern_type = None

    complexity = input(
        "3. Complexity [simple/multi-step/adversarial] (enter to skip): "
    ).strip()
    if not complexity:
        complexity = None

    notes = input("4. Notes (optional, max 200 chars): ").strip()
    if len(notes) > 200:
        notes = notes[:200]

    confidence = input("5. Confidence [high/medium/low] (enter to skip): ").strip()
    if not confidence:
        confidence = None

    return {
        "extraction_present": ep,
        "pattern_type": pattern_type,
        "complexity": complexity,
        "notes": notes,
        "operator": operator,
        "confidence": confidence,
    }


def _write_session_evidence(
    rt_id: str,
    session: SessionBuffer,
    repo_root: Path,
    out_dir: Path,
    index_path: Path,
    capture_mode: str,
    git_sha: str,
    nova_version: str,
    no_prompt: bool,
    incomplete: bool,
) -> None:
    turns_sorted = sorted(session.turns.values(), key=lambda t: t.turn)
    total_turns = len(turns_sorted)
    capture_start = session.first_seen_ts
    capture_end = session.last_new_turn_ts if turns_sorted else capture_start
    capture_duration = max(0.0, capture_end - capture_start)

    final_rho: Optional[float] = None
    final_coherence: Optional[float] = None
    final_extraction_present: Optional[bool] = None

    if turns_sorted:
        last_turn = turns_sorted[-1]
        final_rho = last_turn.rho_temporal
        final_coherence = last_turn.coherence_temporal
        final_extraction_present = last_turn.extraction_present

    operator_annotation = _collect_operator_annotation(no_prompt=no_prompt)

    flags = {
        "NOVA_ENABLE_BIAS_DETECTION": os.getenv("NOVA_ENABLE_BIAS_DETECTION", ""),
        "NOVA_ENABLE_USM_TEMPORAL": os.getenv("NOVA_ENABLE_USM_TEMPORAL", ""),
        "NOVA_ENABLE_TEMPORAL_GOVERNANCE": os.getenv(
            "NOVA_ENABLE_TEMPORAL_GOVERNANCE", ""
        ),
    }

    turns_payload: List[Dict[str, Any]] = []
    for t in turns_sorted:
        turns_payload.append(
            {
                "turn": t.turn,
                "extraction_present": _encode_extraction_present(t.extraction_present),
                "rho_temporal": t.rho_temporal,
                "coherence_temporal": t.coherence_temporal,
                "temporal_state": t.temporal_state,
                "timestamp": _ts_to_iso(t.ts),
            }
        )

    data = {
        "rt_id": rt_id,
        "session_id": session.session_id,
        "capture_mode": capture_mode,
        "timestamp": _now_utc_iso(),
        "nova_version": nova_version,
        "capture": {
            "git_sha": git_sha,
            "tool_version": __version__,
            "source": "prometheus_metrics",
            "endpoint": "",  # filled by caller if desired; left blank here
        },
        "flags": flags,
        "turns": turns_payload,
        "operator_annotation": operator_annotation,
        "metadata": {
            "total_turns": total_turns,
            "capture_duration_seconds": capture_duration,
            "final_rho": final_rho,
            "final_coherence": final_coherence,
            "incomplete": incomplete,
        },
    }

    out_path = out_dir / f"{rt_id}_{session.session_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Append to index
    op_ann = operator_annotation.get("extraction_present")
    op_ann_str: str
    if op_ann is True:
        op_ann_str = "True"
    elif op_ann is False:
        op_ann_str = "False"
    else:
        op_ann_str = "Uncertain"

    final_ep_str: str
    if final_extraction_present is True:
        final_ep_str = "True"
    elif final_extraction_present is False:
        final_ep_str = "False"
    else:
        final_ep_str = "None"

    ts = data["timestamp"]
    with index_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                rt_id,
                session.session_id,
                capture_mode,
                total_turns,
                final_ep_str,
                final_rho if final_rho is not None else "",
                final_coherence if final_coherence is not None else "",
                op_ann_str,
                git_sha,
                ts,
            ]
        )

    print(
        f"[Reality Capture] Saved {rt_id} for session {session.session_id} "
        f"({total_turns} turns) -> {out_path}"
    )


def monitor(
    endpoint: str,
    poll_ms: int,
    idle_end_s: int,
    out_dir: Path,
    index_path: Path,
    no_prompt: bool,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _ensure_directories(out_dir, index_path, repo_root)
    git_sha = _read_git_sha(repo_root)
    nova_version = _read_nova_version(repo_root)

    sessions: Dict[str, SessionBuffer] = {}
    capture_mode = "monitor"

    stop_flag = {"stop": False}

    def _handle_sigint(signum, frame):  # type: ignore[override]
        stop_flag["stop"] = True

    signal.signal(signal.SIGINT, _handle_sigint)

    print(
        f"[Reality Capture] Monitor started (endpoint={endpoint}, poll_ms={poll_ms}, "
        f"idle_end_s={idle_end_s})"
    )

    while not stop_flag["stop"]:
        now = time.time()
        text = _fetch_metrics(endpoint)
        if text is None:
            # Soft failure: log and continue
            print("[Reality Capture] Warning: /metrics unreachable or empty", file=sys.stderr)
        else:
            samples = _parse_prometheus_metrics(text)
            # Build a temporary structure for this scrape
            per_sample_updates: Dict[Tuple[str, int], Dict[str, float]] = {}
            for metric_name, labels, value in samples:
                session_id = labels.get("session_id")
                turn_raw = labels.get("turn")
                if not session_id or not turn_raw:
                    continue
                try:
                    turn = int(turn_raw)
                except ValueError:
                    continue
                key = (session_id, turn)
                d = per_sample_updates.setdefault(key, {})
                d[metric_name] = value

            # Apply updates
            for (session_id, turn), metrics in per_sample_updates.items():
                ses = sessions.get(session_id)
                if ses is None:
                    ses = SessionBuffer(
                        session_id=session_id,
                        first_seen_ts=now,
                        last_new_turn_ts=now,
                        max_turn=0,
                        turns={},
                    )
                    sessions[session_id] = ses

                ts = now
                turn_obj = ses.turns.get(turn)
                if turn_obj is None:
                    # New turn observed
                    turn_obj = TurnSnapshot(turn=turn, ts=ts)
                    ses.turns[turn] = turn_obj
                    if turn > ses.max_turn:
                        ses.max_turn = turn
                        ses.last_new_turn_ts = now
                # Update fields for this turn based on metrics
                for m_name, v in metrics.items():
                    if m_name == "nova_extraction_present":
                        turn_obj.extraction_present = _decode_extraction_present_gauge(v)
                    elif m_name == "nova_rho_temporal":
                        turn_obj.rho_temporal = _decode_float_signal(v)
                    elif m_name == "nova_coherence_temporal":
                        turn_obj.coherence_temporal = _decode_float_signal(v)
                    elif m_name == "nova_temporal_state":
                        turn_obj.temporal_state = _decode_temporal_state_gauge(v)

        # Check for idle sessions (no new turns for idle_end_s)
        now2 = time.time()
        ended_ids: List[str] = []
        for sid, ses in sessions.items():
            if not ses.turns:
                continue
            if now2 - ses.last_new_turn_ts >= idle_end_s:
                ended_ids.append(sid)

        for sid in ended_ids:
            ses = sessions.pop(sid, None)
            if ses is None:
                continue
            rt_id = _next_rt_id(index_path)
            _write_session_evidence(
                rt_id=rt_id,
                session=ses,
                repo_root=repo_root,
                out_dir=out_dir,
                index_path=index_path,
                capture_mode=capture_mode,
                git_sha=git_sha,
                nova_version=nova_version,
                no_prompt=no_prompt,
                incomplete=False,
            )

        time.sleep(max(0.001, poll_ms / 1000.0))

    # On exit, flush any active sessions as incomplete
    if sessions:
        print("[Reality Capture] Stopping - flushing active sessions as incomplete.")
    for sid, ses in list(sessions.items()):
        rt_id = _next_rt_id(index_path)
        _write_session_evidence(
            rt_id=rt_id,
            session=ses,
            repo_root=repo_root,
            out_dir=out_dir,
            index_path=index_path,
            capture_mode=capture_mode,
            git_sha=git_sha,
            nova_version=nova_version,
            no_prompt=no_prompt,
            incomplete=True,
        )


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Nova Reality Capture - monitor temporal USM metrics (metrics-only observer)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    monitor_p = subparsers.add_parser(
        "monitor", help="Monitor /metrics and capture Slot02 temporal evidence."
    )
    monitor_p.add_argument(
        "--endpoint",
        default="http://localhost:8000/metrics/internal",
        help="Prometheus metrics endpoint (default: %(default)s)",
    )
    monitor_p.add_argument(
        "--poll-ms",
        type=int,
        default=500,
        help="Polling interval in milliseconds (default: %(default)s)",
    )
    monitor_p.add_argument(
        "--idle-end-s",
        type=int,
        default=20,
        help="Seconds with no new turns before session is considered ended (default: %(default)s)",
    )
    monitor_p.add_argument(
        "--out",
        type=str,
        default="evidence/rt",
        help="Output directory for RT JSON evidence (default: %(default)s)",
    )
    monitor_p.add_argument(
        "--index",
        type=str,
        default="evidence/index/rt_index.csv",
        help="Index CSV path for RT evidence (default: %(default)s)",
    )
    monitor_p.add_argument(
        "--no-prompt",
        action="store_true",
        help="Disable operator annotation prompts (fill defaults).",
    )

    args = parser.parse_args(argv)

    if args.command == "monitor":
        out_dir = Path(args.out)
        index_path = Path(args.index)
        monitor(
            endpoint=args.endpoint,
            poll_ms=args.poll_ms,
            idle_end_s=args.idle_end_s,
            out_dir=out_dir,
            index_path=index_path,
            no_prompt=args.no_prompt,
        )
    else:  # pragma: no cover - currently only one subcommand
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()

