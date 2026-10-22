#!/usr/bin/env python3
"""Generate special IMX682 LMC config"""
import xml.etree.ElementTree as ET
import hashlib
import os
import shutil
from datetime import datetime

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\imx682_config\special"
DESKTOP_BASELINE = r"C:\Users\l\Desktop\default .xml"
OUTPUT_NAME = "LXX521_LMC84_Special.xml"
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

# Apply changes: 4 verified + additional conservative tuning
changes = {
    'cw_rg_key': 0.4000,          # More aggressive warm cast reduction (was 0.45)
    'lib_sharpnessb_key': 2,      # Moderate sharpening
    'lib_sharpgain_key': 2,       # Sharpening gain
    'lib_sharpmini_key': 2,       # Micro-sharpening
    'lib_contrast_1_key': 1,      # Slight contrast boost
    'lib_contrast_2_key': 1,      # Slight contrast boost
    'pref_iso_noise_key': 3,      # Slightly higher ISO noise handling
}

print("Applying changes to working baseline...")
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

# Rollback instructions
rb_lines = [
    "SPECIAL CONFIG - ROLLBACK PROCEDURE",
    "====================================",
    "",
    "WORKING BASELINE (DO NOT DELETE):",
    "  File: default .xml",
    "  SHA-256: " + baseline_hash,
    "  Location: /sdcard/LMC8.4/default .xml (device) and Desktop (local)",
    "",
    "SPECIAL CONFIG:",
    "  File: LXX521_LMC84_Special.xml",
    "  SHA-256: " + new_hash,
    "  Location: analysis_results/imx682_config/special/ (local)",
    "",
    "CHANGES FROM BASELINE:",
    "  cw_rg_key: 0.5925 -> 0.4000 (more aggressive warm cast reduction)",
    "  lib_sharpnessb_key: 0 -> 2 (moderate sharpening)",
    "  lib_sharpgain_key: 0 -> 2 (sharpening gain)",
    "  lib_sharpmini_key: 0 -> 2 (micro-sharpening)",
    "  lib_contrast_1_key: 0 -> 1 (slight contrast boost)",
    "  lib_contrast_2_key: 0 -> 1 (slight contrast boost)",
    "  pref_iso_noise_key: 2 -> 3 (slightly higher ISO noise handling)",
    "",
    "ROLLBACK STEPS:",
    "  1. On device: Settings -> LMC -> Delete config",
    "  2. Or via ADB: adb shell rm /sdcard/LMC8.4/LXX521_LMC84_Special.xml",
    "  3. Re-import baseline: adb push default .xml /sdcard/LMC8.4/",
    "  4. Restart LMC app",
    "  5. Verify: check EXIF Software field for HDR+ 1.0.414775603zdy",
    "",
    "DEPLOYMENT STEPS (When Authorized):",
    "  1. Connect device via ADB",
    "  2. Push config: adb push LXX521_LMC84_Special.xml /sdcard/LMC8.4/",
    "  3. Open LMC app -> Settings -> Load config",
    "  4. Select LXX521_LMC84_Special.xml",
    "  5. Capture test photos in consistent lighting",
    "  6. Pull photos and run ab_analyze.py to compare metrics",
    "",
    "SAFETY:",
    "  - Original baseline preserved at all times",
    "  - No existing files overwritten or deleted",
    "  - Backup available at analysis_results/imx682_config/special/default_working_backup.xml",
]
rb_path = os.path.join(BASE_DIR, "ROLLBACK_INSTRUCTIONS.txt")
with open(rb_path, 'w') as f:
    f.write("\n".join(rb_lines))
print("Rollback instructions saved: " + rb_path)

print("\nOutput: " + OUTPUT_PATH)
print("Hash: " + new_hash)
print("\nDone.")
