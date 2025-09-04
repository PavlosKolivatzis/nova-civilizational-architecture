#!/usr/bin/env python3
"""
maturity_check.py — Slot Maturity Model (SMM) validator & dashboard

Examples:
  python tools/maturity_check.py docs/maturity.yaml --min-slot 2 --min-core 2.0
  python tools/maturity_check.py docs/maturity.yaml --diff docs/prev.yaml
  python tools/maturity_check.py docs/maturity.yaml --diff-against origin/main --fail-on-worsen
  python tools/maturity_check.py docs/maturity.yaml --badge-json build/maturity_badge.json

Exit codes:
  0 OK
  2 Any slot score < --min-slot
  3 Core anchors avg < --min-core
  4 YAML schema/format error
  5 File not found / unreadable / git show failed
  6 Diff detected worsening (when --fail-on-worsen)
"""

import argparse, json, subprocess, sys
from pathlib import Path
from typing import Dict, Any, Tuple, List

try:
    import yaml  # PyYAML
except Exception:
    print("ERROR: PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(5)

LEVEL_ORDER = ["Missing", "Anchor", "Relational", "Structural", "Processual"]

def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr); sys.exit(5)
    try:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except Exception as e:
        print(f"ERROR: failed to read/parse YAML: {e}", file=sys.stderr); sys.exit(4)

def load_yaml_from_git(ref: str, repo_path: Path, file_path: str) -> Dict[str, Any]:
    """Load a file at git ref without checking out."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_path), "show", f"{ref}:{file_path}"],
            stderr=subprocess.STDOUT
        ).decode("utf-8", errors="replace")
        return yaml.safe_load(out)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: git show {ref}:{file_path} failed:\n{e.output.decode()}", file=sys.stderr)
        sys.exit(5)

def validate_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    if not isinstance(data, dict): return False, ["Top-level YAML must be a mapping"]
    if "meta" not in data or "slots" not in data:
        errs.append("Missing 'meta' or 'slots' keys"); return False, errs
    slots = data["slots"]
    if not isinstance(slots, dict) or not slots:
        errs.append("'slots' must be a non-empty mapping"); return False, errs
    for k, v in slots.items():
        if not isinstance(v, dict):
            errs.append(f"{k}: slot entry must be a mapping"); continue
        for req in ("name", "score", "level"):
            if req not in v: errs.append(f"{k}: missing required field '{req}'")
        s = v.get("score")
        if not isinstance(s, int) or not (0 <= s <= 4):
            errs.append(f"{k}: 'score' must be int in [0,4]")
        lvl = v.get("level")
        if lvl not in LEVEL_ORDER:
            errs.append(f"{k}: 'level' must be one of {LEVEL_ORDER}, got {lvl}")
    return len(errs) == 0, errs

def compute_averages(slots: Dict[str, Any]) -> Dict[str, float]:
    def g(n: int) -> Dict[str, Any]: return slots.get(f"slot{n}", {})
    def avg(ns: List[int]) -> float:
        vals = [g(n).get("score", 0) for n in ns]; return round(sum(vals)/len(vals), 2)
    return {
        "core_anchors": avg([1,2,3,4,5]),
        "safeguards":   avg([6,7,8,9]),
        "deployment":   avg([10]),
        "overall":      round(sum([g(i).get("score",0) for i in range(1,11)]) / 10.0, 2),
    }

def grade(score: int) -> str:
    return LEVEL_ORDER[score] if 0 <= score < len(LEVEL_ORDER) else "Unknown"

def text_dashboard(path: Path, meta: Dict[str, Any], slots: Dict[str, Any], avgs: Dict[str, float]) -> str:
    lines = [f"# Slot Maturity Model — {path.name}",
             f"Version: {meta.get('version','?')} | Updated: {meta.get('updated','?')} | Maintainer: {meta.get('maintainer','?')}", ""]
    for i in range(1, 11):
        s = slots.get(f"slot{i}", {})
        name, score = s.get("name", f"Slot {i}"), s.get("score", 0)
        level = s.get("level", grade(score))
        rationale = (s.get("rationale") or "").strip().splitlines()[0:1]
        lines += [f"## Slot {i} — {name}", f"- Score: **{score}/4** ({level})"]
        if rationale: lines.append(f"- Note: {rationale[0]}")
        lines.append("")
    lines += ["## Averages",
              f"- Core anchors (1–5): **{avgs['core_anchors']}**",
              f"- Safeguards (6–9): **{avgs['safeguards']}**",
              f"- Deployment (10): **{avgs['deployment']}**",
              f"- Overall (1–10): **{avgs['overall']}**"]
    return "\n".join(lines)

def evaluate_thresholds(slots: Dict[str, Any], avgs: Dict[str, float], min_slot: int, min_core: float) -> int:
    rc = 0
    low = [f"slot{i}" for i in range(1,11) if slots.get(f"slot{i}",{}).get("score",0) < min_slot]
    if low:
        print(json.dumps({"reason_code":"LOW_SLOT_SCORE","min_slot":min_slot,"failing_slots":low}))
        rc = 2
    if avgs["core_anchors"] < min_core:
        print(json.dumps({"reason_code":"LOW_CORE_ANCHOR_AVG","min_core":min_core,"core_avg":avgs["core_anchors"]}))
        rc = max(rc, 3)
    return rc

def diff_slots(curr: Dict[str, Any], prev: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for i in range(1, 11):
        k = f"slot{i}"
        cs, ps = curr["slots"].get(k, {}), prev["slots"].get(k, {})
        out[k] = {
            "name": cs.get("name", ps.get("name", k)),
            "prev": ps.get("score", 0),
            "curr": cs.get("score", 0),
            "delta": cs.get("score", 0) - ps.get("score", 0)
        }
    return out

def write_badge_json(path: Path, overall: float) -> None:
    color = "red"
    if overall >= 3.5: color = "brightgreen"
    elif overall >= 3.0: color = "green"
    elif overall >= 2.5: color = "yellowgreen"
    elif overall >= 2.0: color = "yellow"
    elif overall >= 1.5: color = "orange"
    payload = {"schemaVersion": 1, "label": "maturity", "message": f"{overall:.2f}/4", "color": color}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    print(f"Wrote badge JSON → {path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Path to current maturity.yaml")
    ap.add_argument("--min-slot", type=int, default=2)
    ap.add_argument("--min-core", type=float, default=2.0)
    ap.add_argument("--format", choices=["text","json"], default="text")
    ap.add_argument("--diff", help="Compare against another maturity.yaml")
    ap.add_argument("--diff-against", help="Git ref to compare (uses git show <ref>:<path>)")
    ap.add_argument("--repo-root", default=".", help="Repo root for --diff-against (default: .)")
    ap.add_argument("--fail-on-worsen", action="store_true", help="Exit 6 if any slot score decreased vs diff target")
    ap.add_argument("--badge-json", help="Write Shields-style JSON badge to this file")
    args = ap.parse_args()

    curr = load_yaml(Path(args.path))
    ok, errs = validate_schema(curr)
    if not ok:
        print("SCHEMA ERRORS:", file=sys.stderr)
        for e in errs: print(f"- {e}", file=sys.stderr)
        sys.exit(4)

    prev = None
    if args.diff:
        prev = load_yaml(Path(args.diff))
    elif args.diff_against:
        prev = load_yaml_from_git(args.diff_against, Path(args.repo_root), args.path)

    slots = curr["slots"]; meta = curr.get("meta", {})
    avgs = compute_averages(slots)

    if args.format == "text":
        print(text_dashboard(Path(args.path), meta, slots, avgs))
    else:
        print(json.dumps({"meta": meta, "averages": avgs,
                          "slots": {k: {"name": v.get("name"), "score": v.get("score"), "level": v.get("level")}
                                    for k,v in slots.items()}}, indent=2))

    rc = evaluate_thresholds(slots, avgs, args.min_slot, args.min_core)

    if prev is not None:
        ok2, errs2 = validate_schema(prev)
        if not ok2:
            print("DIFF TARGET SCHEMA ERRORS:", file=sys.stderr)
            for e in errs2: print(f"- {e}", file=sys.stderr)
            sys.exit(4)
        d = diff_slots(curr, prev)
        print("\n# Diff vs target")
        worsened = []
        for i in range(1, 11):
            k = f"slot{i}"
            row = d[k]
            delta = row["delta"]
            sign = "+" if delta > 0 else ("" if delta == 0 else "")
            print(f"- Slot {i} ({row['name']}): {row['prev']} → {row['curr']} ({sign}{delta})")
            if delta < 0: worsened.append(k)
        if args.fail-on-worsen and worsened:
            print(json.dumps({"reason_code":"SLOT_WORSENED","slots":worsened}))
            rc = max(rc, 6)

    if args.badge_json:
        write_badge_json(Path(args.badge_json), avgs["overall"])

    sys.exit(rc)

if __name__ == "__main__":
    main()
