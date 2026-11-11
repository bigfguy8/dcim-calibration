"""Centralized project paths for the DCIM calibration pipeline.

All path constants live here so individual scripts never hardcode
relative locations. Resolve everything relative to this file so the
package works regardless of the current working directory.
"""
import os
from pathlib import Path

# Root of the dcim-calibration repository (parent of scripts/).
ROOT = Path(__file__).resolve().parent.parent.parent

# --- Configuration ---
CONFIG_DIR = ROOT / "configs"
XML_DIR = CONFIG_DIR / "xml"

# --- Analysis outputs ---
ANALYSIS_DIR = ROOT / "analysis"
REPORTS_DIR = ANALYSIS_DIR / "reports"
DATA_DIR = ANALYSIS_DIR / "data"

# --- Transient execution artifacts ---
LOGS_DIR = ROOT / "logs"
RUNS_DIR = ROOT / "runs"

# --- Defaults ---
DEFAULT_MASTER = XML_DIR / "LXX521_TEX.xml"
DEFAULT_TARGET = XML_DIR / "LXX521_AI.xml"
# Phone deploy directory (directory the MGC app reads). There is deliberately
# no default: set CALIB_LMC_DIR (preferred) or DCIM_LMC_DIR to the app's config
# folder. Validated by scripts.core.safety before any write. Never a
# filesystem root/mount point.
def configured_lmc_dir() -> "Path | None":
    raw = os.environ.get("CALIB_LMC_DIR") or os.environ.get("DCIM_LMC_DIR")
    return Path(raw).expanduser() if raw else None


LMC_STORAGE_DIR = configured_lmc_dir()


def ensure_dirs() -> None:
    """Create every standardized directory if missing."""
    for directory in (
        XML_DIR,
        REPORTS_DIR,
        DATA_DIR,
        LOGS_DIR,
        RUNS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


__all__ = [
    "ROOT",
    "CONFIG_DIR",
    "XML_DIR",
    "ANALYSIS_DIR",
    "REPORTS_DIR",
    "DATA_DIR",
    "LOGS_DIR",
    "RUNS_DIR",
    "DEFAULT_MASTER",
    "DEFAULT_TARGET",
    "LMC_STORAGE_DIR",
    "configured_lmc_dir",
    "ensure_dirs",
]
