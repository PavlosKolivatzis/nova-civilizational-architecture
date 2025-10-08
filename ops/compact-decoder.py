#!/usr/bin/env python3
"""
Nova Compact-Line Auto-Decoder (stdlib-only)

Reads a compact line from stdin or --line "..." and prints:
- GO/NO-GO decision
- Parsed metrics (hit/deny/rl/reads/active)
- Smart hint based on the failure mode

Usage:
  python ops/compact-decoder.py --line "09:10:46 status=healthy hit=92.1% deny=2.0% rl=0.0% reads=123 active=4"
  python scripts/semantic_mirror_dashboard.py --compact --once | python ops/compact-decoder.py
"""

import argparse
import re
import sys

def parse_pairs(s: str):
    pairs = dict(re.findall(r'(\w+)=([^\s]+)', s))
    return pairs

def pct(text: str) -> float:
    if not text:
        return 0.0
    text = text.replace('%','').replace(',','.')
    try:
        return float(text) / 100.0
    except ValueError:
        return 0.0

def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--line", default=None, help="Compact line; if omitted, read stdin")
    ap.add_argument("--hit", type=float, default=0.85, help="Min hit ratio (0..1)")
    ap.add_argument("--deny", type=float, default=0.05, help="Max deny ratio (0..1)")
    ap.add_argument("--rl", type=float, default=0.005, help="Max rate-limit ratio (0..1)")
    args = ap.parse_args()

    src = args.line if args.line is not None else sys.stdin.read()
    if not src.strip():
        print("NO-GO (empty input)")
        sys.exit(0)

    pairs = parse_pairs(src)
    st = pairs.get("status","unknown")
    hit = pct(pairs.get("hit"))
    deny = pct(pairs.get("deny"))
    rl   = pct(pairs.get("rl"))
    reads  = int(pairs.get("reads","0"))
    active = int(pairs.get("active","0"))

    go = (hit >= args.hit and deny <= args.deny and rl <= args.rl and active > 0)
    print(("GO" if go else "NO-GO"),
          f"| status={st} hit={hit:.3f} deny={deny:.3f} rl={rl:.3f} reads={reads} active={active}")

    # Hints
    if active == 0:
        print("hint: process-scope empty - publish heartbeat in same shell")
    elif deny > 0.10:
        print("hint: ACL drift or key typo - review rules/TTL")
    elif rl > 0.005:
        print("hint: bursty requester - reduce QPM / widen interval")

if __name__ == "__main__":
    main()
