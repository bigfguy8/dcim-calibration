#!/usr/bin/env python3
"""Verify corrected optimized IMX682 LMC config."""
import xml.etree.ElementTree as ET
import hashlib
import os

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\imx682_config"
DESKTOP_BASELINE = r"C:\Users\l\Desktop\default .xml"
CORRECTED = os.path.join(BASE_DIR, "LXX521_LMC84_Optimized_Corrected.xml")

def get_keys(path):
    tree = ET.parse(path)
    keys = {}
    for el in tree.getroot().findall('string'):
        keys[el.get('name')] = el.text
    return keys

baseline_keys = get_keys(DESKTOP_BASELINE)
new_keys = get_keys(CORRECTED)

print("=== Corrected Config Verification ===")
print("Baseline: " + DESKTOP_BASELINE)
print("Baseline hash: " + hashlib.sha256(open(DESKTOP_BASELINE, 'rb').read()).hexdigest())
print("Baseline keys: " + str(len(baseline_keys)))
print()
print("Corrected: " + CORRECTED)
print("Corrected hash: " + hashlib.sha256(open(CORRECTED, 'rb').read()).hexdigest())
print("Corrected keys: " + str(len(new_keys)))
print()

# Check specific changes
changes = ["cw_rg_key", "lib_sharpnessb_key", "lib_sharpgain_key", "lib_sharpmini_key"]
print("Intended changes:")
for k in changes:
    print("  " + k + ": " + baseline_keys[k] + " -> " + new_keys[k])
print()

# Count ALL differences
diff_keys = [k for k in baseline_keys if baseline_keys[k] != new_keys.get(k)]
print("Total keys differing from baseline: " + str(len(diff_keys)))
for k in diff_keys:
    print("  " + k + ": " + baseline_keys[k] + " -> " + new_keys[k])
print()

# Check for missing or extra keys
missing = [k for k in baseline_keys if k not in new_keys]
extra = [k for k in new_keys if k not in baseline_keys]
print("Missing keys: " + str(len(missing)))
print("Extra keys: " + str(len(extra)))
