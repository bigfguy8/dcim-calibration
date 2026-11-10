"""
Event types, queue and dispatcher for event-driven pipeline execution.

Events are produced by the filesystem watcher and dispatched to handlers that
run the core calibration scripts (:mod:`scripts.core.pipeline`, auto-tune,
validation, etc.).
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Callable, Optional

# Canonical event types produced/consumed by the daemon.
EV_CAPTURE_NEW = "capture.new"
EV_CAPTURE_CHANGED = "capture.changed"
EV_PROFILE_NEW = "profile.new"
EV_PROFILE_CHANGED = "profile.changed"
EV_AUTO_TUNE = "auto_tune.run"
EV_PIPELINE_DONE = "pipeline.done"
EV_PIPELINE_FAILED = "pipeline.failed"
EV_REPORT_ARCHIVED = "report.archived"
EV_GIT_PUSHED = "git.pushed"


@dataclass(frozen=True)
class Event:
    """A single event in the daemon's event bus."""
    type: str
    source: str
    path: Optional[Path] = None
    timestamp: float = field(default_factory=time)
    detail: dict = field(default_factory=dict)


class EventQueue:
    """Thread-safe FIFO of events."""

    def __init__(self) -> None:
        self._q: queue.Queue[Event] = queue.Queue()

    def put(self, event: Event) -> None:
        self._q.put(event)

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Optional[Event]:
        try:
            return self._q.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def task_done(self) -> None:
        self._q.task_done()

    def qsize(self) -> int:
        return self._q.qsize()


Handler = Callable[[Event], None]


class EventDispatcher:
    """
    Dispatches events to registered handlers.

    Handlers are registered per event type (or ``"*"`` for all events). A handler
    raising an exception is caught and logged so one bad handler cannot kill the
    dispatch loop.
    """

    def __init__(self, log) -> None:
        self._log = log
        self._handlers: dict[str, list[Handler]] = {}
        self._lock = threading.Lock()

    def register(self, event_type: str, handler: Handler) -> None:
        with self._lock:
            self._handlers.setdefault(event_type, []).append(handler)

    def dispatch(self, event: Event) -> None:
        handlers: list[Handler]
        with self._lock:
            handlers = list(self._handlers.get(event.type, [])) + list(
                self._handlers.get("*", [])
            )
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:  # pragma: no cover - defensive
                self._log.error(
                    "events",
                    f"Handler {getattr(handler, '__name__', handler)!r} failed for "
                    f"{event.type}: {exc}",
                )
