import os
import re
import difflib


IGNORES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def find_file(query: str, base: str = "."):
    """Fuzzy find a file path within *base*.

    Ignores common virtualenv and VCS directories for performance and
    indexes paths relative to *base* so deeper queries work more
    reliably.
    """

    q = _norm(query)
    pool = {}
    for root, dirs, files in os.walk(base):
        # prune ignored directories in-place so os.walk skips them
        dirs[:] = [d for d in dirs if d not in IGNORES]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), base)
            pool[os.path.join(root, f)] = _norm(rel)
    if not pool:
        raise FileNotFoundError("Empty repository tree")
    match = difflib.get_close_matches(q, pool.values(), n=1, cutoff=0.5)
    if not match:
        raise FileNotFoundError(f"No close match: {query}")
    for p, n in pool.items():
        if n == match[0]:
            return p
    # Should not happen but keeps type-checkers happy
    raise FileNotFoundError(f"No file resolved for query: {query}")

if __name__ == "__main__":
    print(find_file("slot6 cultural synthesis"))
