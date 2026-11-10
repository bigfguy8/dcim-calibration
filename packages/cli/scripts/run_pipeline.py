#!/usr/bin/env python3
"""
Autonomous Calibration & Sync Daemon — entry point.

Usage
-----
# One-shot pipeline pass over current assets, then exit:
    python scripts/run_pipeline.py --once

# Run as a daemon: watch DCIM + configs/xml, run the pipeline on events,
# periodic auto-tune, and commit/push successful runs:
    python scripts/run_pipeline.py --daemon

# Watch only (no pipeline), print events:
    python scripts/run_pipeline.py --watch

Options
-------
--once              Run a single pipeline pass and exit
--daemon            Run continuously with the filesystem watcher
--watch             Print watcher events only (dry run)
--no-git            Disable git commit/push even if enabled in config
--poll-interval     Watcher tick seconds (overrides POLL_INTERVAL)
--backend           polling | watchdog | auto (overrides WATCHER_BACKEND)
--lock-timeout      Seconds to wait for the daemon lock (0 = fail fast)

Configuration is read from environment variables (see scripts/core/config.py).
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# Allow running both as `python scripts/run_pipeline.py` and from an installed
# package context.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import load_config  # noqa: E402
from core.events import (  # noqa: E402
    Event,
    EventDispatcher,
    EV_CAPTURE_NEW,
    EV_CAPTURE_CHANGED,
    EV_PROFILE_NEW,
    EV_PROFILE_CHANGED,
)
from core.gitops import discover_ssh_keys  # noqa: E402
from core.lockfile import LockfileError, file_lock  # noqa: E402
from core.pipeline import PipelineRunner  # noqa: E402
from core.watcher import DirectoryWatcher  # noqa: E402


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# Logger
# --------------------------------------------------------------------------- #
class DaemonLogger:
    """Structured logger: JSONL to logs/pipeline.log plus stdout."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self._lock = threading.Lock()
        log_path.parent.mkdir(parents=True, exist_ok=True)

    def _write(self, level: str, component: str, message: str, extra=None) -> None:
        entry = {
            "ts": _utc_now(),
            "level": level,
            "component": component,
            "message": message,
        }
        if extra:
            entry["extra"] = extra
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            print(line, flush=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def info(self, comp: str, msg: str, extra=None) -> None:
        self._write("INFO", comp, msg, extra)

    def warn(self, comp: str, msg: str, extra=None) -> None:
        self._write("WARN", comp, msg, extra)

    def error(self, comp: str, msg: str, extra=None) -> None:
        self._write("ERROR", comp, msg, extra)

    def debug(self, comp: str, msg: str, extra=None) -> None:
        self._write("DEBUG", comp, msg, extra)


# --------------------------------------------------------------------------- #
# Daemon
# --------------------------------------------------------------------------- #
class CalibrationDaemon:
    def __init__(self, config, log, no_git: bool = False) -> None:
        self.cfg = config
        self.log = log
        self.no_git = no_git
        self._stop = False
        self._watcher_threads: list = []
        self.dispatcher = EventDispatcher(log)
        self.runner = PipelineRunner(config, log, dispatcher=self.dispatcher)

    # -- event handlers ---------------------------------------------------- #
    def _wire_event_handlers(self) -> None:
        """Register watcher->pipeline handlers (daemon mode only)."""
        self.dispatcher.register(EV_CAPTURE_NEW, self._on_capture_event)
        self.dispatcher.register(EV_CAPTURE_CHANGED, self._on_capture_event)
        self.dispatcher.register(EV_PROFILE_NEW, self._on_profile_event)
        self.dispatcher.register(EV_PROFILE_CHANGED, self._on_profile_event)

    # -- event handlers ---------------------------------------------------- #
    def _on_capture_event(self, event) -> None:
        self.log.info("watcher", f"Capture event: {event.path.name if event.path else event.type}")
        self._run_pipeline_triggered(source="capture")

    def _on_profile_event(self, event) -> None:
        self.log.info("watcher", f"Profile event: {event.path.name if event.path else event.type}")
        self._run_pipeline_triggered(source="profile")

    def _run_pipeline_triggered(self, source: str) -> None:
        """Run the pipeline in response to a filesystem event."""
        try:
            state = self.runner.load_state()
            result = self.runner.run_once(state=state)
            self.log.info(
                "pipeline",
                f"Event-triggered run {result.run_id}: "
                f"{len(result.processed)} processed, {len(result.errors)} errors",
                extra={"run_id": result.run_id},
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.log.error("pipeline", f"Event-triggered run failed ({source}): {exc}")

    # -- lifecycle ---------------------------------------------------------- #
    def start_watchers(self) -> None:
        self._wire_event_handlers()
        watchers = [
            (
                self.cfg.configs_xml_path,
                self.cfg.profile_exts,
                self._handle_profile_file,
            ),
            (
                self.cfg.dcim_path,
                self.cfg.image_exts,
                self._handle_capture_file,
            ),
        ]
        for path, exts, handler in watchers:
            w = DirectoryWatcher(
                path,
                exts,
                handler,
                backend=self.cfg.watcher_backend,
                poll_interval=self.cfg.poll_interval,
            )
            w.start()
            self._watcher_threads.append(w)
            self.log.info(
                "watcher",
                f"Watching {path} (backend={w.active_backend}, "
                f"interval={self.cfg.poll_interval}s)",
            )

    def _handle_profile_file(self, event) -> None:
        self.dispatcher.dispatch(
            Event(
                type=EV_PROFILE_NEW if event.kind == "created" else EV_PROFILE_CHANGED,
                source="watcher",
                path=event.path,
                detail={"kind": event.kind},
            )
        )

    def _handle_capture_file(self, event) -> None:
        self.dispatcher.dispatch(
            Event(
                type=EV_CAPTURE_NEW if event.kind == "created" else EV_CAPTURE_CHANGED,
                source="watcher",
                path=event.path,
                detail={"kind": event.kind},
            )
        )

    def stop_watchers(self) -> None:
        for w in self._watcher_threads:
            w.stop()

    # -- modes -------------------------------------------------------------- #
    def run_once(self) -> int:
        state = self.runner.load_state()
        result = self.runner.run_once(state=state)
        status = "OK" if result.success else "FAILED"
        self.log.info(
            "daemon",
            f"One-shot run {result.run_id}: {status} "
            f"({len(result.processed)} processed, {len(result.errors)} errors)",
        )
        for rep in result.reports:
            self.log.info("daemon", f"Report: {rep}")
        return 0 if result.success else 1

    def run_daemon(self) -> int:
        self.log.info("daemon", "Autonomous Calibration & Sync Daemon starting")
        self.log.info("daemon", f"DCIM: {self.cfg.dcim_path}")
        self.log.info("daemon", f"Profiles: {self.cfg.configs_xml_path}")
        self.log.info("daemon", f"Reports: {self.cfg.reports_dir}")
        self.log.info("daemon", f"Git commit: {self.cfg.git_auto_commit and not self.no_git}")
        self.log.info("daemon", f"Git push: {self.cfg.git_auto_push and not self.no_git}")
        self.log.info("daemon", f"Watcher backend: {self.cfg.watcher_backend}")

        self.start_watchers()

        # Periodic auto-tune ticker.
        last_tune = time.monotonic()

        self.log.info("daemon", "Daemon running (Ctrl+C to stop)")
        try:
            while not self._stop:
                time.sleep(0.2)
                # Dispatch any queued events (watcher handlers already dispatch
                # directly; this loop keeps the auto-tune ticker alive).
                now = time.monotonic()
                if (
                    self.cfg.auto_tune_enabled
                    and now - last_tune >= self.cfg.auto_tune_interval
                ):
                    last_tune = now
                    try:
                        state = self.runner.load_state()
                        tune = self.runner.run_auto_tune_if_due(state)
                        if not tune.get("skipped"):
                            self.log.info("auto-tune", str(tune.get("output", "")))
                    except Exception as exc:
                        self.log.error("auto-tune", f"Ticker failed: {exc}")
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_watchers()
            self.log.info("daemon", "Daemon stopped")
        return 0

    def request_stop(self) -> None:
        self._stop = True


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Autonomous Calibration & Sync Daemon for IMX682 / LMC 8.4"
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="single pipeline pass, then exit")
    mode.add_argument("--daemon", action="store_true", help="run continuously with watcher")
    mode.add_argument("--watch", action="store_true", help="print watcher events only")
    p.add_argument("--no-git", action="store_true", help="disable git commit/push")
    p.add_argument("--poll-interval", type=float, help="watcher tick seconds")
    p.add_argument("--backend", choices=["polling", "watchdog", "auto"], help="watcher backend")
    p.add_argument("--lock-timeout", type=float, help="seconds to wait for daemon lock")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config = load_config()
    if args.poll_interval is not None:
        config.poll_interval = args.poll_interval
    if args.backend is not None:
        config.watcher_backend = args.backend
    if args.lock_timeout is not None:
        config.lock_timeout = args.lock_timeout

    log = DaemonLogger(config.pipeline_log)

    # --- watch-only mode ---------------------------------------------------
    if args.watch:
        def show(event):
            print(
                f"[{_utc_now()}] {event.type} {event.path.name if event.path else ''} "
                f"({event.detail.get('kind')})",
                flush=True,
            )
        watchers = [
            DirectoryWatcher(
                config.configs_xml_path,
                config.profile_exts,
                show,
                backend=config.watcher_backend,
                poll_interval=config.poll_interval,
            ),
            DirectoryWatcher(
                config.dcim_path,
                config.image_exts,
                show,
                backend=config.watcher_backend,
                poll_interval=config.poll_interval,
            ),
        ]
        for w in watchers:
            w.start()
        print("Watching (Ctrl+C to stop)...", flush=True)
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        for w in watchers:
            w.stop()
        return 0

    # --- acquire lock (prevents overlapping instances) --------------------
    try:
        with file_lock(config.lockfile_path, timeout=config.lock_timeout) as _:
            log.info("daemon", f"Lock acquired: {config.lockfile_path}")
            daemon = CalibrationDaemon(config, log, no_git=args.no_git)

            def handle_signal(signum, frame):
                log.info("daemon", f"Received signal {signum}; shutting down")
                daemon.request_stop()

            signal.signal(signal.SIGINT, handle_signal)
            signal.signal(signal.SIGTERM, handle_signal)

            if args.once:
                return daemon.run_once()
            # Default and --daemon: run continuously.
            return daemon.run_daemon()
    except LockfileError as exc:
        log.error("daemon", str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
