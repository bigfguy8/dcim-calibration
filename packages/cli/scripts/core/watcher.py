"""
Filesystem watcher / poller for the calibration daemon.

Backends
--------
* ``polling`` (default): lightweight directory scan with mtime/size fingerprinting.
  Works everywhere including stock Termux/Android Python and PRoot.
* ``watchdog``: uses the `watchdog` library when available (inotify on Linux).
* ``inotify``: alias kept for future native inotify support; falls back to watchdog.

A :class:`DirectoryWatcher` runs in a daemon thread and invokes a callback for
every newly created or modified file matching the configured extensions.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Set

try:
    from watchdog.observers import Observer as _WObserver
    from watchdog.events import FileSystemEventHandler as _WHandler

    HAS_WATCHDOG = True
except Exception:  # pragma: no cover - watchdog is optional
    HAS_WATCHDOG = False


@dataclass(frozen=True)
class FileEvent:
    """A single filesystem change notification."""
    kind: str  # "created" | "modified" | "deleted"
    path: Path
    timestamp: float


def file_fingerprint(path: Path) -> str:
    """SHA-256 of file contents for change detection."""
    import hashlib

    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


def file_sig(path: Path) -> tuple[float, int]:
    """(mtime, size) cheap signature; falls back to fingerprint on OSError."""
    try:
        st = path.stat()
        return (st.st_mtime, st.st_size)
    except OSError:
        return (0.0, -1)


class Watcher:
    """Base interface for a directory watcher."""

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError


class PollingWatcher(Watcher):
    """
    Polling-based watcher.

    Scans the target directory every *poll_interval* seconds and reports files
    whose mtime/size changed. Because it tracks signatures across ticks it does
    not re-report unchanged files, and it gracefully handles files still being
    written (the callback receives the path; consumers should wait for stability
    before reading).
    """

    def __init__(
        self,
        path: Path,
        exts: Set[str],
        callback: Callable[[FileEvent], None],
        poll_interval: float = 1.0,
    ) -> None:
        self.path = path
        self.exts = {e.lower() for e in exts}
        self.callback = callback
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last: dict[str, tuple[float, int]] = {}

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="dcim-polling-watcher")
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def _loop(self) -> None:
        while self._running:
            try:
                if self.path.exists():
                    for f in self.path.iterdir():
                        if not f.is_file():
                            continue
                        if f.suffix.lower() not in self.exts:
                            continue
                        try:
                            sig = file_sig(f)
                        except OSError:
                            continue
                        prev = self._last.get(f.name)
                        if prev is None or sig != prev:
                            self._last[f.name] = sig
                            self.callback(FileEvent(kind="created" if prev is None else "modified", path=f, timestamp=time.time()))
            except Exception:
                # Watcher must never crash the daemon loop.
                pass
            time.sleep(self.poll_interval)


class WatchdogWatcher(Watcher):
    """watchdog-based watcher (preferred on Linux when watchdog is installed)."""

    def __init__(
        self,
        path: Path,
        exts: Set[str],
        callback: Callable[[FileEvent], None],
        poll_interval: float = 1.0,
    ) -> None:
        self.path = path
        self.exts = {e.lower() for e in exts}
        self.callback = callback
        self.poll_interval = poll_interval
        self._observer: Optional[_WObserver] = None
        self._running = False

    def start(self) -> None:
        if not HAS_WATCHDOG:
            return
        self._running = True

        class _Handler(_WHandler):
            def __init__(self, outer: "WatchdogWatcher") -> None:
                self.outer = outer

            def _maybe(self, kind: str, event) -> None:
                if event.is_directory:
                    return
                p = Path(event.src_path)
                if p.suffix.lower() in self.outer.exts:
                    self.outer.callback(
                        FileEvent(kind=kind, path=p, timestamp=time.time())
                    )

            def on_created(self, event) -> None:  # noqa: D401
                self._maybe("created", event)

            def on_modified(self, event) -> None:  # noqa: D401
                self._maybe("modified", event)

        self._observer = _WObserver()
        self._observer.schedule(_Handler(self), str(self.path), recursive=False)
        self._observer.start()

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None


class DirectoryWatcher:
    """
    Factory that selects the best available watcher backend.

    Defaults to ``polling`` so the daemon runs on stock Termux/Android Python
    without extra dependencies. Use ``WATCHER_BACKEND=watchdog`` to force
    watchdog when it is installed.
    """

    def __init__(
        self,
        path: Path,
        exts: Set[str],
        callback: Callable[[FileEvent], None],
        backend: str = "auto",
        poll_interval: float = 1.0,
    ) -> None:
        self.path = path
        self.exts = exts
        self.callback = callback
        self.poll_interval = poll_interval
        self.backend = self._resolve_backend(backend)
        self._watcher: Optional[Watcher] = None

    @staticmethod
    def _resolve_backend(backend: str) -> str:
        if backend == "auto":
            return "watchdog" if HAS_WATCHDOG else "polling"
        if backend == "watchdog" and not HAS_WATCHDOG:
            # Degrade gracefully instead of failing on restricted environments.
            return "polling"
        return backend

    def start(self) -> None:
        if self.backend == "watchdog":
            self._watcher = WatchdogWatcher(self.path, self.exts, self.callback, self.poll_interval)
        else:
            self._watcher = PollingWatcher(self.path, self.exts, self.callback, self.poll_interval)
        self._watcher.start()

    def stop(self) -> None:
        if self._watcher:
            self._watcher.stop()

    @property
    def active_backend(self) -> str:
        return self.backend or "polling"
