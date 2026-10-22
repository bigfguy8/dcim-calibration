#!/usr/bin/env python3
"""Generate Lava crisp & clear IMX682 LMC config"""
import xml.etree.ElementTree as ET
import hashlib
import os
import shutil
from datetime import datetime

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\imx682_config\lava"
DESKTOP_BASELINE = r"C:\Users\l\Desktop\default .xml"
OUTPUT_NAME = "Lava_Crisp_Clear.xml"
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

# Crisp & clear settings: aggressive sharpening, contrast, clarity
changes = {
    'cw_rg_key': 0.4000,          # Warm cast reduction
    'lib_sharpnessb_key': 4,      # Strong sharpening for crispness
    'lib_sharpgain_key': 3,       # Higher sharpening gain
    'lib_sharpmini_key': 3,       # Higher micro-sharpening
    'lib_contrast_1_key': 2,      # Stronger contrast
    'lib_contrast_2_key': 2,      # Stronger contrast
    'pref_iso_noise_key': 3,      # ISO noise handling
    'lib_denoise_key': 1,         # Light denoise to preserve detail
    'lib_lumadenoise_key': 1,     # Light luma denoise
    'lib_lumanoise_key': 1,       # Light luma noise
}

print("Applying crisp & clear changes to working baseline...")
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
    "LAVA CRISP & CLEAR CONFIG - ROLLBACK PROCEDURE",
    "==============================================",
    "",
    "WORKING BASELINE (DO NOT DELETE):",
    "  File: default .xml",
    "  SHA-256: " + baseline_hash,
    "  Location: /sdcard/LMC8.4/default .xml (device) and Desktop (local)",
    "",
    "LAVA CRISP & CLEAR CONFIG:",
    "  File: Lava_Crisp_Clear.xml",
    "  SHA-256: " + new_hash,
    "  Location: analysis_results/imx682_config/lava/ (local)",
    "",
    "CHANGES FROM BASELINE (crisp & clear profile):",
    "  cw_rg_key: 0.5925 -> 0.4000 (warm cast reduction)",
    "  lib_sharpnessb_key: 0 -> 4 (strong sharpening)",
    "  lib_sharpgain_key: 0 -> 3 (higher sharpening gain)",
    "  lib_sharpmini_key: 0 -> 3 (higher micro-sharpening)",
    "  lib_contrast_1_key: 0 -> 2 (stronger contrast)",
    "  lib_contrast_2_key: 0 -> 2 (stronger contrast)",
    "  pref_iso_noise_key: 2 -> 3 (ISO noise handling)",
    "  lib_denoise_key: 0 -> 1 (light denoise)",
    "  lib_lumadenoise_key: 0 -> 1 (light luma denoise)",
    "  lib_lumanoise_key: 0 -> 1 (light luma noise)",
    "",
    "WARNING: Higher sharpening (4) may introduce halos on fine textures.",
    "WARNING: Higher contrast (2) may crush shadows in low light.",
    "Test thoroughly before committing to this config.",
    "",
    "ROLLBACK STEPS:",
    "  1. On device: Settings -> LMC -> Delete config",
    "  2. Or via ADB: adb shell rm /sdcard/LMC8.4/Lava_Crisp_Clear.xml",
    "  3. Re-import baseline: adb push default .xml /sdcard/LMC8.4/",
    "  4. Restart LMC app",
    "  5. Verify: check EXIF Software field for HDR+ 1.0.414775603zdy",
    "",
    "DEPLOYMENT STEPS (When Authorized):",
    "  1. Connect device via ADB",
    "  2. Push config: adb push Lava_Crisp_Clear.xml /sdcard/LMC8.4/",
    "  3. Open LMC app -> Settings -> Load config",
    "  4. Select Lava_Crisp_Clear.xml",
    "  5. Capture test photos in consistent lighting",
    "  6. Pull photos and run ab_analyze.py to compare metrics",
    "",
    "SAFETY:",
    "  - Original baseline preserved at all times",
    "  - No existing files overwritten or deleted",
    "  - Backup available at analysis_results/imx682_config/lava/default_working_backup.xml",
]
rb_path = os.path.join(BASE_DIR, "ROLLBACK_INSTRUCTIONS.txt")
with open(rb_path, 'w') as f:
    f.write("\n".join(rb_lines))
print("Rollback instructions saved: " + rb_path)

print("\nOutput: " + OUTPUT_PATH)
print("Hash: " + new_hash)
print("\nDone.")
