"""Centralized logging for the DCIM calibration pipeline.

Provides a single logger factory so every module emits consistent,
timestamped messages with an optional verbose mode for detailed
diagnostics. Errors are always surfaced; verbose messages are opt-in.
"""
from __future__ import annotations

import logging
import sys
from typing import Optional

_DEFAULT_FORMAT = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_LOGGER: Optional[logging.Logger] = None


def setup_logger(verbose: bool = False, log_file=None) -> logging.Logger:
    """Return the process-wide logger, configuring it on first call.

    Parameters
    ----------
    verbose:
        When True, emit DEBUG-level diagnostics; otherwise only INFO and
        above are shown.
    log_file:
        Optional path to also write logs to (useful for audit runs).
    """
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger("dcim_calibration")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False

    fmt = logging.Formatter(_DEFAULT_FORMAT, datefmt=_DATE_FORMAT)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    _LOGGER = logger
    return logger


def get_logger() -> logging.Logger:
    """Return the configured logger, initializing with defaults if needed."""
    if _LOGGER is None:
        return setup_logger(verbose=False)
    return _LOGGER


__all__ = ["setup_logger", "get_logger"]
