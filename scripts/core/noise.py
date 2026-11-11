"""IMX682 LMC 8.4 noise model management.

Refactored from manage_noise_models.py. Discovers local and phone-storage
noise profiles and writes a template guide.
"""
from __future__ import annotations

from pathlib import Path

from .logging import get_logger
from .paths import LMC_STORAGE_DIR, ROOT

logger = get_logger()

GUIDE_PATH = ROOT / "noise_model_guide.md"


def check_noise_setup() -> None:
    """Report noise-model files found locally and on phone storage."""
    logger.info("IMX682 Noise Model Status")
    local_noise = list(ROOT.glob("*.noise*"))
    phone_noise = (
        list(LMC_STORAGE_DIR.glob("*.noise*"))
        if LMC_STORAGE_DIR is not None and LMC_STORAGE_DIR.exists()
        else []
    )
    noise_files = local_noise + phone_noise
    logger.info("Local workspace noise files found: %d", len(noise_files))
    for nf in noise_files:
        logger.info("  - %s", nf.name)

    if LMC_STORAGE_DIR is None:
        logger.warning("CALIB_LMC_DIR not set; skipping phone noise-file scan")
    elif LMC_STORAGE_DIR.exists():
        phone_noise = list(LMC_STORAGE_DIR.glob("*.noise*"))
        logger.info("Phone storage (%s) noise files found: %d", LMC_STORAGE_DIR, len(phone_noise))
        for pn in phone_noise:
            logger.info("  - %s", pn.name)
    else:
        logger.warning("Phone directory not found: %s", LMC_STORAGE_DIR)


def create_noise_stub() -> Path:
    """Write the IMX682 noise model template guide and return its path."""
    content = """# Sony IMX682 Custom Noise Model Guide for LMC 8.4

To achieve optimal noise reduction without losing detail on your Lava Play Ultra (IMX682):

1. **Obtain an IMX682 Noise Profile**:
   - Compatible `.noise.png` files for Sony 64MP sensors can be sourced from community repositories (like Celso Azevedo's noise profile collection or Telegram GCam groups).
2. **Placement**:
   - Place the `.noise.png` file directly into the MGC profile directory
     (`CALIB_LMC_DIR`) alongside your XML profiles.
3. **Linking in LMC 8.4**:
   - Open LMC Settings → Libpatcher → Noise Model / Custom Noise, and select the IMX682 profile.
"""
    GUIDE_PATH.write_text(content, encoding="utf-8")
    logger.info("Created guide: %s", GUIDE_PATH.name)
    return GUIDE_PATH


__all__ = ["check_noise_setup", "create_noise_stub"]
