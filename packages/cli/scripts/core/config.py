"""
Runtime configuration for the Autonomous Calibration & Sync Daemon.

All values are sourced from environment variables with sensible defaults, so the
daemon can be dropped onto Termux / Ubuntu PRoot without editing any file.

Environment variables
---------------------
BASE_DIR            project working directory  (default: dir of this file's parent)
DCIM_PATH           source camera capture folder  (default /sdcard/DCIM/Camera)
CONFIGS_XML_PATH    profile XML folder          (default <repo>/configs/xml)
CAPTURES_DIR        local capture staging dir   (default <base>/captures)
LOGS_DIR            transient log dir           (default <base>/logs)
REPORTS_DIR         archived reports dir        (default <base>/analysis/reports)
STATE_DIR           persistent state dir        (default <base>/state)
METRICS_DIR         metrics dir                 (default <base>/metrics)
POLL_INTERVAL       watcher tick in seconds     (default 1.0)
WATCHER_BACKEND     polling | watchdog | inotify | auto  (default auto)
GIT_AUTO_COMMIT     stage+commit on success     (default true)
GIT_AUTO_PUSH       push to origin on success   (default false)
GIT_REMOTE          git remote name             (default origin)
GIT_BRANCH          git branch                  (default main)
GIT_SSH_KEY         path to SSH private key     (default none -> ssh-agent/default)
LOCKFILE_PATH       lockfile path               (default <base>/.daemon.lock)
LOCK_TIMEOUT        seconds to wait for lock    (default 0 = fail fast)
MAX_RETRIES         max retries per flaky op    (default 3)
RETRY_BACKOFF       base backoff seconds        (default 1.0)
BASELINE_PROFILE    reference profile name      (default LXX521_TEX.xml)
CONFIGS_XML_PATH    directory holding the active XML (default <repo>/configs/xml)
AUTO_TUNE_INTERVAL  seconds between auto-tune   (default 30.0)
AUTO_TUNE_ENABLED   run auto-tune in daemon     (default true)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Set

IMAGE_EXTS: Set[str] = {
    ".jpg", ".jpeg", ".png", ".dng", ".webp", ".tiff", ".tif", ".bmp",
}
PROFILE_EXTS: Set[str] = {".xml"}

_DEFAULT_BASELINE = "LXX521_TEX.xml"


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default).lower()).lower() == "true"


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_set(name: str, default: Set[str]) -> Set[str]:
    raw = os.getenv(name)
    if not raw:
        return set(default)
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


@dataclass
class DaemonConfig:
    """Fully resolved daemon configuration."""

    # --- paths ---------------------------------------------------------
    base_dir: Path
    dcim_path: Path
    configs_xml_path: Path
    captures_dir: Path
    logs_dir: Path
    reports_dir: Path
    state_dir: Path
    metrics_dir: Path
    pipeline_log: Path
    events_log: Path
    state_file: Path
    lockfile_path: Path

    # --- watcher -------------------------------------------------------
    poll_interval: float
    watcher_backend: str

    # --- git -----------------------------------------------------------
    git_auto_commit: bool
    git_auto_push: bool
    git_remote: str
    git_branch: str
    git_ssh_key: str | None
    git_commit_message_prefix: str

    # --- reliability ---------------------------------------------------
    max_retries: int
    retry_backoff: float
    lock_timeout: float

    # --- calibration ---------------------------------------------------
    baseline_profile: str
    auto_tune_interval: float
    auto_tune_enabled: bool

    # --- file extensions (defaults last, dataclass ordering) -----------
    image_exts: Set[str] = field(default_factory=lambda: set(IMAGE_EXTS))
    profile_exts: Set[str] = field(default_factory=lambda: set(PROFILE_EXTS))


def load_config() -> DaemonConfig:
    """Load configuration from environment variables with defaults."""
    base_dir = Path(_env("BASE_DIR", str(Path(__file__).resolve().parent.parent.parent))).resolve()
    # scripts/core/ -> scripts/ -> packages/cli  =>  BASE_DIR = packages/cli
    dcim_path = Path(_env("DCIM_PATH", "/sdcard/DCIM/Camera")).expanduser().resolve()
    default_xml_dir = base_dir.parents[1] / "configs" / "xml"
    configs_xml_path = Path(_env("CONFIGS_XML_PATH", str(default_xml_dir))).expanduser().resolve()
    captures_dir = Path(_env("CAPTURES_DIR", str(base_dir / "captures"))).resolve()
    logs_dir = Path(_env("LOGS_DIR", str(base_dir / "logs"))).resolve()
    reports_dir = Path(_env("REPORTS_DIR", str(base_dir / "analysis" / "reports"))).resolve()
    state_dir = Path(_env("STATE_DIR", str(base_dir / "state"))).resolve()
    metrics_dir = Path(_env("METRICS_DIR", str(base_dir / "metrics"))).resolve()

    pipeline_log = logs_dir / "pipeline.log"
    events_log = logs_dir / "events.jsonl"
    state_file = state_dir / "daemon_state.json"
    lockfile_path = Path(_env("LOCKFILE_PATH", str(base_dir / ".daemon.lock")))

    return DaemonConfig(
        base_dir=base_dir,
        dcim_path=dcim_path,
        configs_xml_path=configs_xml_path,
        captures_dir=captures_dir,
        logs_dir=logs_dir,
        reports_dir=reports_dir,
        state_dir=state_dir,
        metrics_dir=metrics_dir,
        pipeline_log=pipeline_log,
        events_log=events_log,
        state_file=state_file,
        lockfile_path=lockfile_path,
        poll_interval=_env_float("POLL_INTERVAL", 1.0),
        watcher_backend=_env("WATCHER_BACKEND", "auto").lower(),
        image_exts=_env_set("IMAGE_EXTS", set(IMAGE_EXTS)),
        profile_exts=_env_set("PROFILE_EXTS", set(PROFILE_EXTS)),
        git_auto_commit=_env_bool("GIT_AUTO_COMMIT", True),
        git_auto_push=_env_bool("GIT_AUTO_PUSH", False),
        git_remote=_env("GIT_REMOTE", "origin"),
        git_branch=_env("GIT_BRANCH", "main"),
        git_ssh_key=_env("GIT_SSH_KEY", "") or None,
        git_commit_message_prefix=_env("GIT_COMMIT_PREFIX", "daemon(calibration):"),
        max_retries=_env_float("MAX_RETRIES", 3),
        retry_backoff=_env_float("RETRY_BACKOFF", 1.0),
        lock_timeout=_env_float("LOCK_TIMEOUT", 0.0),
        baseline_profile=_env("BASELINE_PROFILE", _DEFAULT_BASELINE),
        auto_tune_interval=_env_float("AUTO_TUNE_INTERVAL", 30.0),
        auto_tune_enabled=_env_bool("AUTO_TUNE_ENABLED", True),
    )
