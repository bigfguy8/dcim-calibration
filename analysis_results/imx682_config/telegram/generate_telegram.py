#!/usr/bin/env python3
"""Generate Telegram-postable LMC 8.4 config for LXX521/IMX682"""
import xml.etree.ElementTree as ET
import hashlib
import os
import shutil
from datetime import datetime

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\imx682_config\telegram"
DESKTOP_BASELINE = r"C:\Users\l\Desktop\default .xml"
OUTPUT_NAME = "LXX521_IMX682_Telegram.xml"
OUTPUT_PATH = os.path.join(BASE_DIR, OUTPUT_NAME)

os.makedirs(BASE_DIR, exist_ok=True)

def set_key(root, name, value):
    for el in root.findall('string'):
        if el.get('name') == name:
            el.text = str(value)
            return True
    return False

def get_keys(path):
    tree = ET.parse(path)
    keys = {}
    for el in tree.getroot().findall('string'):
        keys[el.get('name')] = el.text
    return keys

tree = ET.parse(DESKTOP_BASELINE)
root = tree.getroot()
baseline_keys = get_keys(DESKTOP_BASELINE)

# Telegram config: balanced all-rounder settings
changes = {
    'cw_rg_key': 0.4500,
    'lib_sharpnessb_key': 2,
    'lib_sharpgain_key': 2,
    'lib_sharpmini_key': 2,
    'lib_contrast_1_key': 1,
    'lib_contrast_2_key': 1,
    'pref_iso_noise_key': 3,
    'lib_denoise_key': 1,
    'lib_lumadenoise_key': 1,
    'lib_lumanoise_key': 1,
    'lib_preservinghigh_key': 1,
    'pref_gamma_curve_mode_key': 0,
    'pref_awb_key': 1,
    'pref_color_key': -1,
    'cw_rg_key_2': 0.5200,
    'cw_rg_key_3': 0.5200,
    'cw_rg_key_4': 0.5200,
    'cw_rg_key_5': 0.5200,
    'pref_hdrregion_key': 6,
    'pref_hdrregion_key_2': 6,
    'pref_hdrregion_key_3': 6,
    'pref_hdrregion_key_4': 6,
    'pref_hdrregion_key_5': 6,
    'pref_hdrregion_key_front': 6,
}

print("Applying Telegram config changes to working baseline...")
for name, value in changes.items():
    if set_key(root, name, value):
        print(f"  {name}: {baseline_keys[name]} -> {value} (set)")
    else:
        print(f"  {name}: KEY NOT FOUND")

tree.write(OUTPUT_PATH, xml_declaration=True, encoding='utf-8')

verify_tree = ET.parse(OUTPUT_PATH)
verify_keys = get_keys(OUTPUT_PATH)
new_hash = hashlib.sha256(open(OUTPUT_PATH, 'rb').read()).hexdigest()
baseline_hash = hashlib.sha256(open(DESKTOP_BASELINE, 'rb').read()).hexdigest()

print(f"\nKey count: {len(verify_keys)} (baseline: {len(baseline_keys)})")
print(f"Missing keys: {len(set(baseline_keys) - set(verify_keys))}")
print(f"Extra keys: {len(set(verify_keys) - set(baseline_keys))}")
print(f"Keys changed: {sum(1 for k in baseline_keys if baseline_keys[k] != verify_keys.get(k))}")
print(f"Baseline hash: {baseline_hash}")
print(f"New config hash: {new_hash}")

# Backup
backup_path = os.path.join(BASE_DIR, "default_working_backup.xml")
shutil.copy2(DESKTOP_BASELINE, backup_path)

# Create guide
guide = """LXX521 IMX682 LMC 8.4 Config - Telegram Share
==================================================

Device: LAVA LXX521 (Lava Play Ultra)
Sensor: Sony IMX682 (64MP, 1/1.73")
Camera App: LMC 8.4 Iris R18F1
Config: LXX521_IMX682_Telegram.xml
SHA-256: """ + new_hash + """

HOW TO INSTALL:
1. Download LMC 8.4 Iris R18F1 APK
2. Create folder: /sdcard/LMC8.4/
3. Copy LXX521_IMX682_Telegram.xml to /sdcard/LMC8.4/
4. Open LMC 8.4 -> Settings -> Config -> Import
5. Select LXX521_IMX682_Telegram.xml
6. Verify settings load and persist

WHAT THIS CONFIG DOES:
- Reduces warm color cast (cw_rg_key 0.45)
- Moderate sharpening for detail (lib_sharpnessb 2)
- Light noise reduction (lib_denoise 1)
- Slight contrast boost (lib_contrast 1)
- Preserves highlights in HDR (lib_preservinghigh 1)
- Daylight AWB for consistent colors
- Slight color saturation reduction (-1)

TUNED FOR:
- Natural colors and skin tones
- Good detail without halos
- Clean shadows without over-smoothing
- Balanced HDR performance
- Low-light usability

NOTE: This config is based on analysis of 70+ photos on LXX521.
Results may vary. Test before committing. Keep original config as backup.

ROLLBACK:
- Delete config from LMC settings
- Or re-import original default .xml
- Restart LMC app

Credits: LXX521 IMX682 calibration project
"""
guide_path = os.path.join(BASE_DIR, "TELEGRAM_GUIDE.txt")
with open(guide_path, 'w') as f:
    f.write(guide)
print("Guide saved: " + guide_path)

# Push to device
import subprocess
ADB = r"C:\Users\l\android-sdk\platform-tools\adb.exe"
r = subprocess.run([ADB, "push", OUTPUT_PATH, "/sdcard/LMC8.4/LXX521_IMX682_Telegram.xml"], capture_output=True, text=True)
if r.returncode == 0:
    print("Pushed to device: /sdcard/LMC8.4/LXX521_IMX682_Telegram.xml")
else:
    print("Push failed: " + r.stderr)

# Verify device hash
r2 = subprocess.run([ADB, "shell", "sha256sum /sdcard/LMC8.4/LXX521_IMX682_Telegram.xml"], capture_output=True, text=True)
print("Device hash: " + r2.stdout.strip())

print("\nOutput: " + OUTPUT_PATH)
print("Hash: " + new_hash)
print("\nDone.")
