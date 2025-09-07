#!/usr/bin/env python3
"""
Fuzzy repo utility for NOVA:
- Fuzzy path resolution for slightly-wrong filenames/paths
- Git-safe move/rename/delete with dry-run
- Python API to resolve modules and optionally import them

Usage (CLI):
  python tools/fuzzy_repo.py find "slot6 cultural synthesis"
  python tools/fuzzy_repo.py find "slot10 deployment mls"
  python tools/fuzzy_repo.py move "slot6 meta yaml" --to slots/slot06_cultural_synthesis/slot6.meta.yaml --apply
  python tools/fuzzy_repo.py rm "civilization_deployment" --apply
  python tools/fuzzy_repo.py print "app py"
  python tools.fuzzy_repo.py fix-import "slots.slot06_cultural_synthesis.adapter"

Python API:
  from tools.fuzzy_repo import resolve_path, auto_import
  path = resolve_path("slot6 meta yaml").best
  mod  = auto_import("slots.slot06_cultural_synthesis.adapter",
                     alt_queries=["engine", "slot6 cultural synthesis"])
"""

from __future__ import annotations
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

# ---------- indexing & normalization ----------

IGNORES = {
    ".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".DS_Store", ".idea", ".vscode", "node_modules", "dist", "build",
}

def _norm(s: str) -> str:
    s = s.lower()
    s = s.replace("-", " ").replace("_", " ").replace(".", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def _token_key(p: Path) -> str:
    # Combine path parts for better matching
    parts = [*p.parts]
    return _norm(" ".join(parts))

def _iter_repo_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        # prune ignored dirs
        dirnames[:] = [d for d in dirnames if d not in IGNORES]
        for f in filenames:
            yield Path(dirpath) / f

@dataclass
class MatchResult:
    query: str
    candidates: List[Tuple[float, Path]]  # (score, path)

    @property
    def best(self) -> Optional[Path]:
        return self.candidates[0][1] if self.candidates else None

def _score(q: str, key: str) -> float:
    # Mix ratio and token containment for robust ranking
    r = difflib.SequenceMatcher(a=q, b=key).ratio()
    bonus = 0.0
    for tok in q.split():
        if tok and tok in key:
            bonus += 0.05
    return min(1.0, r + bonus)

def resolve_path(query: str, base: str = ".", k: int = 8, threshold: float = 0.52) -> MatchResult:
    """
    Fuzzy resolve a file path from a human-ish query.
    - threshold ~0.52 balances typos vs. noise
    """
    root = Path(base).resolve()
    qn = _norm(query)
    scored: List[Tuple[float, Path]] = []
    for p in _iter_repo_files(root):
        key = _token_key(p.relative_to(root))
        s = _score(qn, key)
        if s >= threshold:
            scored.append((s, p))
    scored.sort(key=lambda t: (-t[0], len(str(t[1]))))
    return MatchResult(query=query, candidates=scored[:k])

# ---------- git-safe ops ----------

def _run_git(args: List[str]) -> Tuple[int, str]:
    proc = subprocess.run(["git", *args], capture_output=True, text=True)
    out = proc.stdout.strip() + ("\n" + proc.stderr.strip() if proc.stderr else "")
    return proc.returncode, out.strip()

def git_move(src: Path, dst: Path, apply: bool = False) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if apply:
        code, out = _run_git(["mv", str(src), str(dst)])
        if code != 0:
            # fall back to os.rename if not a git repo
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                os.rename(src, dst)
                return f"[os.rename] {src} -> {dst}"
            except Exception as e:
                return f"[ERROR] mv {src} -> {dst}: {e}\n{out}"
        return f"[git mv] {src} -> {dst}\n{out}"
    return f"[DRY-RUN] mv {src} -> {dst}"

def git_rm(path: Path, apply: bool = False) -> str:
    if apply:
        code, out = _run_git(["rm", "-f", str(path)])
        if code != 0:
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    # dangerous to rm -r automatically; skip dirs
                    return f"[ERROR] refusing to delete directory non-interactively: {path}"
                return f"[os.remove] {path}"
            except Exception as e:
                return f"[ERROR] rm {path}: {e}\n{out}"
        return f"[git rm] {path}\n{out}"
    return f"[DRY-RUN] rm {path}"

# ---------- printing/preview ----------

def print_file(path: Path, max_bytes: int = 100_000) -> str:
    try:
        data = path.read_bytes()[:max_bytes]
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return f"[BINARY or non-UTF8] {path} ({len(data)} bytes shown)"
        return f"----- {path} -----\n{text}\n----- end -----"
    except Exception as e:
        return f"[ERROR] cannot read {path}: {e}"

# ---------- import helper ----------

def auto_import(
    dotted: str,
    alt_queries: Optional[List[str]] = None,
    base: str = ".",
):
    """
    Try to import a module by its full dotted path. If that fails, fuzzy-search files
    suggested by alt_queries (or pieces of dotted) and add their parent to sys.path.
    """
    try:
        return __import__(dotted, fromlist=["*"])
    except Exception:
        pass

    queries = alt_queries or []
    if not queries:
        # derive queries from dotted tokens
        toks = [t for t in re.split(r"[.\-_]+", dotted) if t]
        queries = [" ".join(toks[-2:]), toks[-1], " ".join(toks)]

    for q in queries:
        res = resolve_path(q, base=base, k=3)
        for _, p in res.candidates:
            parent = str(p.parent.resolve())
            if parent not in sys.path:
                sys.path.insert(0, parent)
            try:
                return __import__(dotted, fromlist=["*"])
            except Exception:
                continue
    # last attempt: direct load by file path
    res = resolve_path(queries[0], base=base, k=1)
    if res.best and res.best.suffix == ".py":
        parent = str(res.best.parent.resolve())
        if parent not in sys.path:
            sys.path.insert(0, parent)
        mod_name = res.best.stem
        try:
            return __import__(mod_name)
        except Exception:
            pass
    raise ImportError(f"auto_import failed for {dotted}; tried {queries}")

# ---------- CLI ----------

def _cmd_find(args):
    res = resolve_path(args.query, base=args.base, k=args.k, threshold=args.threshold)
    payload = {
        "query": res.query,
        "matches": [{"score": round(s, 4), "path": str(p)} for s, p in res.candidates],
        "best": str(res.best) if res.best else None,
    }
    print(json.dumps(payload, indent=2))

def _cmd_move(args):
    src = resolve_path(args.query, base=args.base, k=1, threshold=args.threshold).best
    if not src:
        print(f"[ERROR] no match for '{args.query}'")
        return
    dst = Path(args.to)
    print(git_move(src, dst, apply=args.apply))

def _cmd_rm(args):
    tgt = resolve_path(args.query, base=args.base, k=1, threshold=args.threshold).best
    if not tgt:
        print(f"[ERROR] no match for '{args.query}'")
        return
    print(git_rm(tgt, apply=args.apply))

def _cmd_print(args):
    tgt = resolve_path(args.query, base=args.base, k=1, threshold=args.threshold).best
    if not tgt:
        print(f"[ERROR] no match for '{args.query}'")
        return
    print(print_file(tgt))

def _cmd_fix_import(args):
    try:
        mod = auto_import(args.dotted, base=args.base)
        print(json.dumps({"status": "ok", "module": repr(mod)}, indent=2))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}, indent=2))

def main():
    ap = argparse.ArgumentParser(description="NOVA fuzzy repo utility")
    ap.add_argument("--base", default=".", help="Repo root (default: .)")
    ap.add_argument("--threshold", type=float, default=0.52)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("find", help="Find a file by fuzzy query")
    sp.add_argument("query")
    sp.add_argument("--k", type=int, default=8)
    sp.set_defaults(func=_cmd_find)

    sp = sub.add_parser("move", help="Git-safe move/rename (dry-run by default)")
    sp.add_argument("query")
    sp.add_argument("--to", required=True, help="Destination path")
    sp.add_argument("--apply", action="store_true", help="Actually perform git mv/os.rename")
    sp.set_defaults(func=_cmd_move)

    sp = sub.add_parser("rm", help="Git-safe remove (dry-run by default)")
    sp.add_argument("query")
    sp.add_argument("--apply", action="store_true", help="Actually perform git rm/os.remove")
    sp.set_defaults(func=_cmd_rm)

    sp = sub.add_parser("print", help="Print (preview) a matched file")
    sp.add_argument("query")
    sp.set_defaults(func=_cmd_print)

    sp = sub.add_parser("fix-import", help="Try to import a dotted path with fuzzy fallback")
    sp.add_argument("dotted")
    sp.set_defaults(func=_cmd_fix_import)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
