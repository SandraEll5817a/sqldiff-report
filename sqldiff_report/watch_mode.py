"""watch_mode.py – polls snapshot files/dirs for changes and re-runs the diff."""

from __future__ import annotations

import time
import hashlib
import os
from pathlib import Path
from typing import Callable, Optional


def _file_fingerprint(path: Path) -> str:
    """Return a hash representing the current state of *path* (file or dir)."""
    h = hashlib.md5()
    if path.is_file():
        h.update(path.read_bytes())
    elif path.is_dir():
        for child in sorted(path.rglob("*.sql")):
            h.update(child.read_bytes())
    return h.hexdigest()


def _fingerprints(before: Path, after: Path) -> tuple[str, str]:
    return _file_fingerprint(before), _file_fingerprint(after)


def watch(
    before: Path,
    after: Path,
    callback: Callable[[], None],
    interval: float = 2.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *before* and *after* every *interval* seconds.

    Calls *callback* whenever either path changes.  Runs until interrupted
    (KeyboardInterrupt) or *max_iterations* is reached (useful in tests).
    """
    last = _fingerprints(before, after)
    # Always run once on startup
    callback()

    iterations = 0
    while True:
        if max_iterations is not None and iterations >= max_iterations:
            break
        time.sleep(interval)
        current = _fingerprints(before, after)
        if current != last:
            last = current
            callback()
        iterations += 1
