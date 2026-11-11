"""Safety guards for operations that touch phone/shared storage.

Mandatory rules enforced here:

1. No mutating operation may target a filesystem root or storage mount
   point (``/``, ``/sdcard``, ``/storage``, ``/data``, ``/system``,
   ``/vendor``, ``/product``, ``/mnt``, ``/apex``, ``$HOME``).
2. Deletion targets must resolve to a path strictly *inside* an explicit,
   caller-provided workspace directory (e.g. ``/tmp/...`` or the repo).
3. Every deploy/write to phone storage must go through
   :func:`check_deploy_target`, so an accidental parent mount can never be
   created or overwritten.

These guards fail closed: any violation raises :class:`GuardError`.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

# Exact mount/root points that must never be used as an operation target.
FORBIDDEN_ROOTS = frozenset(
    str(Path(p).resolve())
    for p in (
        "/",
        "/sdcard",
        "/storage",
        "/data",
        "/system",
        "/vendor",
        "/product",
        "/mnt",
        "/apex",
        str(Path.home()),
    )
)


class GuardError(RuntimeError):
    """Raised when a path fails a safety guard check."""


def resolved(path: "str | Path") -> Path:
    """Resolve *path* (expanduser + resolve) without requiring existence."""
    return Path(path).expanduser().resolve()


def is_forbidden_path(path: "str | Path") -> bool:
    """True if *path* resolves exactly to a forbidden root/mount point."""
    return str(resolved(path)) in FORBIDDEN_ROOTS


def check_deploy_target(path: "str | Path") -> Path:
    """Validate a deploy/write directory. Returns the resolved path.

    Raises GuardError if the resolved path is empty, a filesystem root, or
    a forbidden storage mount point. Subdirectories (e.g. ``/sdcard/lmc8.4``)
    are allowed — they are the explicit, user-facing deploy location.
    """
    p = resolved(path)
    if str(p) in ("", "."):
        raise GuardError(f"refusing empty deploy target: {path!r}")
    if is_forbidden_path(p):
        raise GuardError(
            f"refusing deploy target at forbidden root/mount: {p} "
            f"(set DCIM_LMC_DIR to a dedicated subdirectory)"
        )
    if p == p.anchor and len(p.parts) <= 1:
        raise GuardError(f"refusing deploy target at filesystem anchor: {p}")
    return p


def checked_rmtree(path: "str | Path", allowed_base: "str | Path") -> Path:
    """Delete *path* recursively, only if strictly inside *allowed_base*.

    Both paths are resolved first. Raises GuardError unless *path* is a
    non-trivial descendant of *allowed_base* (never the base itself, never a
    root mount). Intended for scratch cleanup under ``/tmp`` or the repo.
    """
    p = resolved(path)
    base = resolved(allowed_base)

    if is_forbidden_path(p) or is_forbidden_path(base):
        raise GuardError(f"refusing to delete forbidden path: {p}")
    if p == base:
        raise GuardError(f"refusing to delete the allowed base itself: {p}")
    try:
        p.relative_to(base)
    except ValueError as exc:
        raise GuardError(f"{p} is not inside allowed base {base}") from exc
    if len(p.parts) < 3:
        raise GuardError(f"refusing shallow delete target: {p}")

    shutil.rmtree(p)
    return p


def is_phone_path(path: "str | Path") -> bool:
    """True if *path* resolves to shared/phone storage.

    Writes to such paths require explicit authorization (``--deploy`` or
    ``DCIM_DEPLOY=1``) — they touch the live Android shared-storage mount.
    """
    p = str(resolved(path))
    return (
        p == "/sdcard"
        or p.startswith("/sdcard/")
        or p == "/storage"
        or p.startswith("/storage/")
        or p == "/data/media"
        or p.startswith("/data/media/")
        or p == "/mnt/sdcard"
        or p.startswith("/mnt/sdcard/")
    )


def deploy_enabled(flag: bool) -> bool:
    """True when phone-storage writes are explicitly authorized.

    Enabled by the ``--deploy`` CLI flag *or* ``DCIM_DEPLOY=1`` in the
    environment. Never enabled implicitly.
    """
    return bool(flag) or os.environ.get("DCIM_DEPLOY", "").strip() == "1"
