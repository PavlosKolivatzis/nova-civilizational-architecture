import importlib
import json
from pathlib import Path


def _resolve(path: str):
    mod, attr = path.rsplit('.', 1)
    return getattr(importlib.import_module(mod), attr)


def test_slot_map_paths_are_importable():
    data = json.loads(Path('contracts/slot_map.json').read_text())
    for meta in data.values():
        module = meta.get('module')
        if module:
            _resolve(module)
        adapter = meta.get('adapter')
        if adapter:
            _resolve(adapter)
        health = meta.get('health')
        if health:
            _resolve(health)
