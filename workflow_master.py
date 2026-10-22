#!/usr/bin/env python3
"""
IMX682 LMC 8.4 Profile Deployment Tool
Device: Lava Play Ultra (LXX521) | Sensor: Sony IMX682
"""

import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "analysis_results" / "imx682_config"
SDCARD_LMC_DIR = Path("/sdcard/LMC8.4")

def banner(title):
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)

def deploy_profile():
    banner("Deploy Profile to Internal Storage (/sdcard/LMC8.4/)")

    if not CONFIG_DIR.exists():
        print(f"  [!] Config folder missing: {CONFIG_DIR}")
        return

    xml_files = sorted(list(CONFIG_DIR.glob("*.xml")))
    if not xml_files:
        print("  [!] No XML profiles found in config directory.")
        return

    print("Available Profiles:\n")
    for idx, xml in enumerate(xml_files, 1):
        print(f"  [{idx}] {xml.name}")

    try:
        choice = int(input("\nEnter profile number to deploy (0 to cancel): ").strip())
        if choice == 0:
            return

        selected = xml_files[choice - 1]
        SDCARD_LMC_DIR.mkdir(parents=True, exist_ok=True)
        target = SDCARD_LMC_DIR / selected.name

        shutil.copy(selected, target)
        print(f"\n  [✓] Successfully deployed: {selected.name}")
        print(f"  [→] Destination path: {target}")
        print("  [i] Load in LMC 8.4 by double-tapping beside the shutter button.")
    except Exception as e:
        print(f"  [✗] Error: {e}")

def main():
    while True:
        banner("IMX682 LMC 8.4 Deployment Menu")
        print("  [1] Deploy XML Profile to Phone Storage")
        print("  [q] Quit")

        choice = input("\nEnter choice [1 or q]: ").strip().lower()
        if choice == '1':
            deploy_profile()
        elif choice == 'q':
            print("\nExiting workflow. Happy capturing!")
            break

if __name__ == "__main__":
    main()
