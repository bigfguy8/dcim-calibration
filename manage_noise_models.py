#!/usr/bin/env python3
"""
IMX682 LMC 8.4 Noise Model Manager
Helps deploy and verify custom .noise.png profiles for Sony IMX682.
"""

import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "analysis_results" / "imx682_config"
SDCARD_LMC_DIR = Path("/sdcard/LMC8.4")

def banner(title):
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)

def check_noise_setup():
    banner("IMX682 Noise Model Status")

    # Check local config dir for any .noise or profile files
    noise_files = list(CONFIG_DIR.glob("*.noise*")) + list(BASE_DIR.glob("*.noise*"))

    print(f"  [i] Local workspace noise files found: {len(noise_files)}")
    for nf in noise_files:
        print(f"      - {nf.name}")

    # Check phone storage
    if SDCARD_LMC_DIR.exists():
        phone_noise = list(SDCARD_LMC_DIR.glob("*.noise*"))
        print(f"  [i] Phone storage ({SDCARD_LMC_DIR}) noise files found: {len(phone_noise)}")
        for pn in phone_noise:
            print(f"      - {pn.name}")
    else:
        print(f"  [!] Phone directory not found: {SDCARD_LMC_DIR}")

def create_noise_stub():
    banner("Generating IMX682 Noise Model Template Guide")
    guide_path = BASE_DIR / "noise_model_guide.md"

    content = """# Sony IMX682 Custom Noise Model Guide for LMC 8.4

To achieve optimal noise reduction without losing detail on your Lava Play Ultra (IMX682):

1. **Obtain an IMX682 Noise Profile**:
   - Compatible `.noise.png` files for Sony 64MP sensors can be sourced from community repositories (like Celso Azevedo's noise profile collection or Telegram GCam groups).
2. **Placement**:
   - Place the `.noise.png` file directly into your phone's `/sdcard/LMC8.4/` directory alongside your XML profiles (`LXX521_UltimateSpeedCrisp.xml`).
3. **Linking in LMC 8.4**:
   - Open LMC Settings → Libpatcher → Noise Model / Custom Noise, and select the IMX682 profile.
"""
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Created guide: {guide_path.name}")

if __name__ == "__main__":
    check_noise_setup()
    create_noise_stub()
