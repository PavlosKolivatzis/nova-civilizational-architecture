import os
import re
import difflib

def _norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', s.lower())

def find_file(query: str, base: str = "."):
    q = _norm(query)
    pool = {}
    for root, _, files in os.walk(base):
        for f in files:
            pool[os.path.join(root, f)] = _norm(f"{os.path.basename(root)}/{f}")
    if not pool:
        raise FileNotFoundError("Empty repository tree")
    match = difflib.get_close_matches(q, pool.values(), n=1, cutoff=0.5)
    if not match:
        raise FileNotFoundError(f"No close match: {query}")
    for p, n in pool.items():
        if n == match[0]:
            return p

if __name__ == "__main__":
    print(find_file("slot6 cultural synthesis"))
