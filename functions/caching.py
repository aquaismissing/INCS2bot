import json
from pathlib import Path
from typing import Any


__all__ = ['load_cache', 'dump_cache', 'dump_cache_changes']


def load_cache(path: Path) -> dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def dump_cache(path: Path, cache: dict[str, Any]):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)


def dump_cache_changes(path: Path, changes: dict[str, Any]):
    dump_cache(path, load_cache(path) | changes)
