"""Centralized project paths for the DCIM calibration pipeline.

All path constants live here so individual scripts never hardcode
relative locations. Resolve everything relative to this file so the
package works regardless of the current working directory.
"""
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
DEFAULT_MASTER = XML_DIR / "LXX521_IMX682_LMC84_AllRounder.xml"
DEFAULT_TARGET = XML_DIR / "LXX521_IMX682_LMC84_SkinTone_Perfect.xml"
LMC_STORAGE_DIR = Path("/sdcard/LMC8.4")
GCAM_CONFIGS_DIR = Path("/sdcard/GCam/Configs")


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
    "GCAM_CONFIGS_DIR",
    "ensure_dirs",
]
