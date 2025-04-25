import json
from pathlib import Path

import filelock

__all__ = ['load_cache', 'dump_cache', 'dump_cache_changes']


def get_filelock(path: Path, *, timeout: int = 10):
    return filelock.FileLock(path.with_suffix(path.suffix + '.lock'), timeout=timeout)


def load_cache(path: Path, *, timeout: int = 10) -> dict[str, ...]:
    with get_filelock(path, timeout=timeout):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)


def dump_cache(path: Path, cache: dict[str, ...], *, timeout: int = 5):
    with get_filelock(path, timeout=timeout):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)


def dump_cache_changes(path: Path, changes: dict[str, ...], *, timeout: int = 10):
    dump_cache(path, load_cache(path, timeout=timeout) | changes, timeout=timeout)
