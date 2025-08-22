import os
import re
import difflib
import importlib
from pathlib import Path
from types import ModuleType


def normalize(name: str) -> str:
    """Normalize strings for comparison."""
    cleaned = re.sub(r"[^a-z0-9]", "", name.lower())
    # collapse leading zeros in numeric segments (e.g. slot06 -> slot6)
    return re.sub(r"0+(\d)", r"\1", cleaned)


def find_file(query: str, base_dir: str = ".", extensions=None) -> str:
    """Return the closest matching file path for a query.

    If ``extensions`` is provided, only files with those extensions are
    considered.  ``extensions`` may be a string or an iterable of strings.
    """
    norm_query = normalize(query)
    if isinstance(extensions, str):
        extensions = [extensions]
    best_path = None
    best_score = 0.0
    for root, _, files in os.walk(base_dir):
        for f in files:
            if extensions and not any(f.endswith(ext) for ext in extensions):
                continue
            rel = os.path.join(root, f)
            key = normalize(rel)
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


def load_slot(slot_name: str, base_dir: str = "slots") -> ModuleType:
    """Convenience wrapper to locate and import slot modules."""
    path = find_file(slot_name, base_dir, extensions=[".py"])
    return import_module(path)


def get_engine(slot_name: str, base_dir: str = "slots"):
    """Return the first class ending with 'Engine' from the resolved slot module."""
    mod = load_slot(slot_name, base_dir)
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
