#!/usr/bin/env python3
"""Generate HDR Video-only IMX682 LMC config"""
import xml.etree.ElementTree as ET
import hashlib
import os
import shutil
from datetime import datetime

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\imx682_config\hdr_video"
DESKTOP_BASELINE = r"C:\Users\l\Desktop\default .xml"
OUTPUT_NAME = "Lava_HDR_Video.xml"
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

# HDR Video settings: combine HDR optimization with video settings
changes = {
    # Video settings
    'pref_video_resolution': 'RES_1080P',
    'pref_video_fps_4k_key': 'FPS_30',
    'pref_video_fps_cm_key': 'FPS_30',
    'pref_video_fps_p2018_key': 'FPS_AUTO',
    'pref_vffps_high_key': 30,
    'pref_vffps_low_key': 15,
    'pref_video_aspect_ratio': 'SIXTEEN_BY_NINE',
    'pref_video_hevc_setting_key': 0,
    'pref_bitrate_key': 0,
    # HDR settings
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
    'pref_camera_hdr_plus_key': 'enhanced',
    'pref_hdrregion_key': 8,
    'pref_frames_hdr_key': 12,
    'pref_gamma_curve_mode_key': 0,
}

print("Applying HDR Video settings to working baseline...")
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

backup_path = os.path.join(BASE_DIR, "default_working_backup.xml")
shutil.copy2(DESKTOP_BASELINE, backup_path)

rb_lines = [
    "HDR VIDEO CONFIG - ROLLBACK PROCEDURE",
    "====================================",
    "",
    "WORKING BASELINE (DO NOT DELETE):",
    "  File: default .xml",
    "  SHA-256: " + baseline_hash,
    "  Location: /sdcard/LMC8.4/default .xml (device) and Desktop (local)",
    "",
    "HDR VIDEO CONFIG:",
    "  File: Lava_HDR_Video.xml",
    "  SHA-256: " + new_hash,
    "  Location: analysis_results/imx682_config/hdr_video/ (local)",
    "",
    "VIDEO SETTINGS:",
    "  Resolution: 1080P",
    "  FPS: 30 (auto for p2018)",
    "  Aspect ratio: 16:9",
    "  HEVC: 0 (default)",
    "  Bitrate: 0 (auto)",
    "",
    "HDR SETTINGS:",
    "  HDR+: enhanced (was auto)",
    "  HDR region: 8 (was 5)",
    "  HDR frames: 12 (was 0)",
    "  Gamma curve: 0 (was -1)",
    "  cw_rg_key: 0.45 (warm cast reduction)",
    "  Sharpness: 2, Contrast: 1, NR: 1",
    "  Preserve highlights: 1",
    "",
    "ROLLBACK STEPS:",
    "  1. On device: Settings -> LMC -> Delete config",
    "  2. Or via ADB: adb shell rm /sdcard/LMC8.4/Lava_HDR_Video.xml",
    "  3. Re-import baseline: adb push default .xml /sdcard/LMC8.4/",
    "  4. Restart LMC app",
    "",
    "DEPLOYMENT STEPS (When Authorized):",
    "  1. Connect device via ADB",
    "  2. Push config: adb push Lava_HDR_Video.xml /sdcard/LMC8.4/",
    "  3. Open LMC app -> Settings -> Load config",
    "  4. Select Lava_HDR_Video.xml",
    "  5. Record test video in consistent lighting",
    "  6. Compare with baseline video",
    "",
    "SAFETY:",
    "  - Original baseline preserved at all times",
    "  - No existing files overwritten or deleted",
    "  - STATUS: UNVERIFIED - no A/B test performed",
]
rb_path = os.path.join(BASE_DIR, "ROLLBACK_INSTRUCTIONS.txt")
with open(rb_path, 'w') as f:
    f.write("\n".join(rb_lines))
print("Rollback instructions saved: " + rb_path)

print("\nOutput: " + OUTPUT_PATH)
print("Hash: " + new_hash)
print("\nDone.")
