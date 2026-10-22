#!/usr/bin/env python3
"""
IMX682 & LMC 8.4 Crisp Image Calibration Pipeline
Automated Setup, Analysis, and Profile Deployer
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "analysis_results" / "imx682_config"
SDCARD_LMC = Path("/sdcard/LMC8.4")

def banner(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def verify_environment():
    banner("1. Environment & Package Check")
    required = ["numpy", "cv2", "PIL", "matplotlib"]
    missing = [pkg for pkg in required if not __import__("importlib.util").util.find_spec("cv2" if pkg=="cv2" else "PIL" if pkg=="PIL" else pkg)]

    if missing:
        print(f"Installing missing packages: {missing}")
        install_map = {"cv2": "opencv-python", "PIL": "pillow"}
        to_install = [install_map.get(p, p) for p in missing]
        subprocess.run([sys.executable, "-m", "pip", "install"] + to_install, check=True)
    print("  [✓] Python dependencies ready.")

def display_online_guidelines():
    banner("2. Online Tuning Guidelines for Crisp GCam (IMX682)")
    print("""
    [Online Best Practice Checklist for LMC 8.4 Sharpness & Clarity]:
    • Lib Patcher Sharpness: Set Sharp Gain safely between 1.2x - 1.5x. Avoid
      over-sharpening sliders to prevent digital halos and high chroma noise.
    • Noise Reduction (Luma/Chroma): Keep moderate settings. Excessive noise
      reduction smudges fine textures on the 64MP Sony IMX682 sensor.
    • HDR+ Enhanced: Use for static shots, urban details, and high dynamic range
      scenarios to maximize multi-frame merging detail.
    • AWB Models: Match AWB with your lighting source (e.g., Pixel 7 Pro profile
      for balanced natural skin tones and white balance accuracy).
    """)

def execute_analysis():
    banner("3. Running Unified Analysis Pipeline")
    target_script = BASE_DIR / "unified_analysis.py"
    if target_script.exists():
        subprocess.run([sys.executable, str(target_script)])
    else:
        print("  [!] unified_analysis.py not found. Skipping image metric review.")

def deploy_sharp_profile():
    banner("4. Deploy Crisp XML Profile to Phone")
    if not CONFIG_DIR.exists():
        print(f"  [!] Config folder missing: {CONFIG_DIR}")
        return

    xmls = list(CONFIG_DIR.glob("*.xml"))
    if not xmls:
        print("  [!] No XML profiles available to deploy.")
        return

    print("Available Sharpness Profiles:\n")
    for i, x in enumerate(xmls, 1):
        print(f"  [{i}] {x.name}")

    choice = input("\nSelect profile number to push to /sdcard/LMC8.4/ (or 'q' to skip): ").strip()
    if choice.lower() == 'q':
        return

    try:
        idx = int(choice) - 1
        selected = xmls[idx]
        SDCARD_LMC.mkdir(parents=True, exist_ok=True)
        dest = SDCARD_LMC / selected.name
        shutil.copy(selected, dest)
        print(f"\n  [✓] Successfully deployed: {selected.name}")
        print(f"  [→] Target path: {dest}")
        print("  [i] In LMC 8.4, double-tap the dark space beside the shutter button to load it.")
    except Exception as e:
        print(f"  [✗] Deployment failed: {e}")

if __name__ == "__main__":
    verify_environment()
    display_online_guidelines()
    execute_analysis()
    deploy_sharp_profile()
    print("\n[✓] Pipeline complete! Ready for crisp shots.")
