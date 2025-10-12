"""Slot loader utilities for NOVA."""

from __future__ import annotations

import difflib
import importlib
import os
import re
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Tuple

from src_bootstrap import ensure_src_on_path

_LEADING_ZERO_RE = re.compile(r"(?<!\d)0+(?=\d)")

# Cache of indexed files per base directory. Mapping of base directory to a
# list of tuples of (relative path, normalized key).
_FILE_CACHE: Dict[str, List[Tuple[str, str]]] = {}


def normalize(name: str) -> str:
    """Normalize strings for comparison."""
    cleaned = re.sub(r"[^a-z0-9]", "", name.lower())
    return _LEADING_ZERO_RE.sub("", cleaned)


def _index_files(base_dir: str) -> List[Tuple[str, str]]:
    """Return cached file info for ``base_dir``; build cache if missing."""
    if base_dir not in _FILE_CACHE:
        entries: List[Tuple[str, str]] = []
        if not os.path.isdir(base_dir):
            _FILE_CACHE[base_dir] = entries
            return entries
        for root, _, files in os.walk(base_dir):
            for filename in files:
                rel = os.path.join(root, filename)
                entries.append((rel, normalize(rel)))
        _FILE_CACHE[base_dir] = entries
    return _FILE_CACHE[base_dir]


def find_file(
    query: str,
    base_dir: str,
    extensions=None,
    refresh: bool = False,
) -> str:
    """Return the closest matching file path for a query within ``base_dir``."""

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
    raise FileNotFoundError(f"No close match found for: {query} in {base_dir}")


def import_module(path: str) -> ModuleType:
    """Import a Python module from a given file path."""
    repo_root = Path('.').resolve()
    full = Path(path).resolve()
    dotted = '.'.join(full.relative_to(repo_root).with_suffix('').parts)
    return importlib.import_module(dotted)


def load_slot(slot_name: str, base_dirs: tuple[str, ...] = ("src/nova/slots", "slots"), refresh: bool = False) -> ModuleType:
    """Return the slot module for ``slot_name``.

    Attempts to import ``nova.slots.<slot_name>`` directly before falling back
    to file-system discovery inside ``base_dirs`` (defaulting to the src tree
    first, then the legacy shims).
    """

    ensure_src_on_path()
    normalized = slot_name.replace('/', '.').replace('\\', '.')

    # Direct import through the namespaced package if available.
    try:
        return importlib.import_module(f"nova.slots.{normalized}")
    except ModuleNotFoundError:
        pass

    # Fallback: search for a matching file in the provided base directories.
    for base_dir in base_dirs:
        try:
            path = find_file(slot_name, base_dir, extensions=[".py"], refresh=refresh)
        except FileNotFoundError:
            continue
        return import_module(path)

    raise FileNotFoundError(f"Unable to resolve slot module: {slot_name}")


def get_engine(slot_name: str, base_dirs: tuple[str, ...] = ("src/nova/slots", "slots"), refresh: bool = False):
    """Return the first attribute ending with ``Engine`` from the slot module."""
    mod = load_slot(slot_name, base_dirs=base_dirs, refresh=refresh)
    for attr in dir(mod):
        if attr.lower().endswith("engine"):
            return getattr(mod, attr)
    raise AttributeError(f"No engine class found in {mod.__name__}")


if __name__ == "__main__":
    target = os.environ.get("SLOT_QUERY", "slot06_cultural_synthesis")
    try:
        module = load_slot(target)
        print(f"Found module: {module.__name__}")
    except Exception as exc:  # pragma: no cover - diagnostic helper
        print(exc)
