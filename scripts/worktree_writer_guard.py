#!/usr/bin/env python3
"""Cross-process operation guard for spec-141 local worktree writer authority.

The durable writer lease records interruption/owner metadata. This module owns a
separate stable OS lock file that is never unlinked and whose exclusion is
released automatically by the operating system when the holder process exits.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator


class WriterGuardBusy(RuntimeError):
    """Raised when another process currently owns the stable worktree guard."""


@contextmanager
def exclusive_writer_guard(
    path: Path,
    *,
    busy_error: Callable[[], BaseException] | None = None,
) -> Iterator[None]:
    """Acquire one stable per-worktree OS exclusion guard without waiting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    handle = os.fdopen(fd, "r+b", buffering=0)
    locked = False
    try:
        try:
            if os.name == "nt":
                import msvcrt

                if os.fstat(handle.fileno()).st_size == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except OSError as exc:
            if busy_error is not None:
                raise busy_error() from exc
            raise WriterGuardBusy("worktree writer operation guard is busy") from exc

        yield
    finally:
        if locked:
            try:
                if os.name == "nt":
                    import msvcrt

                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()
        else:
            handle.close()


__all__ = ["WriterGuardBusy", "exclusive_writer_guard"]
