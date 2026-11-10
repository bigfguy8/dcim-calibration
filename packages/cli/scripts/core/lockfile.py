"""
Cross-process mutual exclusion via fcntl.flock.

The lockfile holds the owning PID so a stale lock (dead process) can be detected
and broken automatically. Designed for Linux/Termux where fcntl is available.
"""

from __future__ import annotations

import fcntl
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class LockfileError(RuntimeError):
    """Raised when the lock cannot be acquired within the timeout."""


def _pid_alive(pid: int) -> bool:
    """Return True if a process with the given PID exists (Linux /proc check)."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we cannot signal it.
        return True
    except OSError:
        return False
    return True


@contextmanager
def file_lock(lock_path: Path, timeout: float = 0.0) -> Iterator[None]:
    """
    Acquire an exclusive flock on *lock_path*.

    Parameters
    ----------
    lock_path:
        Path to the lockfile (created if missing).
    timeout:
        Seconds to wait for the lock. 0 means fail fast. A negative value waits
        forever.

    Raises
    ------
    LockfileError
        If the lock cannot be acquired within *timeout*.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        deadline = time.monotonic() + timeout if timeout >= 0 else None
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                # Lock held by another process. Check for staleness.
                try:
                    content = os.read(fd, 64).decode("ascii", errors="replace").strip()
                    holder_pid = int(content.split()[0]) if content else 0
                except (OSError, ValueError):
                    holder_pid = 0
                if holder_pid and not _pid_alive(holder_pid):
                    # Stale lock: truncate and retry immediately.
                    try:
                        os.ftruncate(fd, 0)
                    except OSError:
                        pass
                    continue
                if timeout == 0:
                    raise LockfileError(
                        f"Lock held by PID {holder_pid or '<unknown>'}; "
                        f"use LOCK_TIMEOUT>0 to wait or remove {lock_path}"
                    )
                if deadline is not None and time.monotonic() >= deadline:
                    raise LockfileError(
                        f"Timed out waiting for lock {lock_path} "
                        f"(held by PID {holder_pid or '<unknown>'})"
                    )
                time.sleep(min(0.05, timeout / 10 if timeout > 0 else 0.05))
        # Write our PID so others can detect staleness.
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode("ascii"))
        os.fsync(fd)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
            # Best-effort removal; leave file if another process recreated it.
            try:
                if lock_path.exists():
                    lock_path.unlink()
            except OSError:
                pass
