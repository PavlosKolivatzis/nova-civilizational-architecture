import os
import re
import difflib
import importlib
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Tuple


_LEADING_ZERO_RE = re.compile(r"(?<!\d)0+(?=\d)")


def normalize(name: str) -> str:
    """Normalize strings for comparison."""
    cleaned = re.sub(r"[^a-z0-9]", "", name.lower())
    # collapse only leading zeros in numeric segments (e.g. slot06 -> slot6)
    # avoid stripping zeros that are preceded by another digit
    return _LEADING_ZERO_RE.sub("", cleaned)


# Cache of indexed files per base directory.  Mapping of base directory to a
# list of tuples of (relative path, normalized key).
_FILE_CACHE: Dict[str, List[Tuple[str, str]]] = {}


def _index_files(base_dir: str) -> List[Tuple[str, str]]:
    """Return cached file info for ``base_dir``; build cache if missing."""
    if base_dir not in _FILE_CACHE:
        entries: List[Tuple[str, str]] = []
        for root, _, files in os.walk(base_dir):
            for f in files:
                rel = os.path.join(root, f)
                entries.append((rel, normalize(rel)))
        _FILE_CACHE[base_dir] = entries
    return _FILE_CACHE[base_dir]


def find_file(
    query: str,
    base_dir: str = ".",
    extensions=None,
    refresh: bool = False,
) -> str:
    """Return the closest matching file path for a query.

    Files under ``base_dir`` are indexed on first use and cached for subsequent
    lookups.  Set ``refresh`` to ``True`` to rebuild the cache.  If
    ``extensions`` is provided, only files with those extensions are
    considered.  ``extensions`` may be a string or an iterable of strings.
    """

    norm_query = normalize(query)
    if isinstance(extensions, str):
        extensions = [extensions]

    if refresh and base_dir in _FILE_CACHE:
        del _FILE_CACHE[base_dir]

    best_path = None
    best_score = 0.0
    for rel, key in _index_files(base_dir):
        if extensions and not any(rel.endswith(ext) for ext in extensions):
            continue
        score = difflib.SequenceMatcher(a=norm_query, b=key).ratio()
        if norm_query in key:
            score += 0.5
        if score > best_score:
            best_score, best_path = score, rel
    if best_path and best_score >= 0.5:
        return best_path
    raise FileNotFoundError(f"No close match found for: {query}")


def import_module(path: str) -> ModuleType:
    """Import a Python module from a given file path."""
    repo_root = Path(".").resolve()
    full = Path(path).resolve()
    dotted = ".".join(full.relative_to(repo_root).with_suffix("").parts)
    return importlib.import_module(dotted)


def load_slot(slot_name: str, base_dir: str = "slots", refresh: bool = False) -> ModuleType:
    """Convenience wrapper to locate and import slot modules."""
    path = find_file(slot_name, base_dir, extensions=[".py"], refresh=refresh)
    return import_module(path)


def get_engine(slot_name: str, base_dir: str = "slots", refresh: bool = False):
    """Return the first class ending with 'Engine' from the resolved slot module."""
    mod = load_slot(slot_name, base_dir, refresh=refresh)
    for attr in dir(mod):
        if attr.lower().endswith("engine"):
            return getattr(mod, attr)
    raise AttributeError(f"No engine class found in {mod.__name__}")


if __name__ == "__main__":
    target = os.environ.get("SLOT_QUERY", "multicultural truth synthesis")
    try:
        mod = load_slot(target)
        print(f"Found module: {mod.__name__}")
    except Exception as e:
        print(e)
