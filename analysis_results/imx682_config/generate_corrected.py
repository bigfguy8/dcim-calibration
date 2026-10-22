#!/usr/bin/env python3
"""Generate corrected optimized IMX682 LMC config from Desktop working baseline."""
import xml.etree.ElementTree as ET
import hashlib
import os

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\imx682_config"
# Use Desktop default .xml as the working baseline (matches device)
DESKTOP_BASELINE = r"C:\Users\l\Desktop\default .xml"
OUTPUT_PATH = os.path.join(BASE_DIR, "LXX521_LMC84_Optimized_Corrected.xml")

def set_key(root, name, value):
    """Set the first string element with the given name."""
    for el in root.findall('string'):
        if el.get('name') == name:
            el.text = str(value)
            return True
    return False

def main():
    tree = ET.parse(DESKTOP_BASELINE)
    root = tree.getroot()

    changes = {}

    # === AWB / Color ===
    # cw_rg_key: 0.5925 → 0.4500
    # Evidence: Warm cast R-G +3.3 to +6.8 across all LMC photos.
    # Reduce red gain on rear camera to compensate sensor-level warm bias.
    changes['cw_rg_key'] = 0.4500

    # === Sharpening ===
    # lib_sharpnessb_key: 0 → 2
    # Evidence: Best MTF50 0.1438 cyc/px at EV 6.8; edge density 3.9-12.7%.
    # Moderate sharpening increase for detail retention without halo artifacts.
    changes['lib_sharpnessb_key'] = 2
    # lib_sharpgain_key: 0 → 2
    changes['lib_sharpgain_key'] = 2
    # lib_sharpmini_key: 0 → 2
    changes['lib_sharpmini_key'] = 2

    # Apply changes
    print("Applying changes to Desktop baseline...")
    total_modified = 0
    missing = []
    for name, value in changes.items():
        if set_key(root, name, value):
            total_modified += 1
            print("  " + name + ": " + str(value) + " (set)")
        else:
            missing.append(name)
            print("  " + name + ": KEY NOT FOUND in baseline")

    # Save new config
    tree.write(OUTPUT_PATH, xml_declaration=True, encoding='utf-8')

    # Verify
    verify_tree = ET.parse(OUTPUT_PATH)
    verify_root = verify_tree.getroot()

    print("\n=== Verification ===")
    for name in changes:
        val = None
        for el in verify_root.findall('string'):
            if el.get('name') == name:
                val = el.text
                break
        print("  " + name + ": " + val)

    # Hash
    new_h = hashlib.sha256(open(OUTPUT_PATH, 'rb').read()).hexdigest()
    baseline_h = hashlib.sha256(open(DESKTOP_BASELINE, 'rb').read()).hexdigest()

    print("\nOutput: " + OUTPUT_PATH)
    print("Desktop baseline hash: " + baseline_h)
    print("New config hash: " + new_h)
    print("Different from baseline: " + str(new_h != baseline_h))
    print("Key count: " + str(len(verify_root.findall('string'))))

    # Count differences
    baseline_keys = {}
    for el in root.findall('string'):
        baseline_keys[el.get('name')] = el.text
    new_keys = {}
    for el in verify_root.findall('string'):
        new_keys[el.get('name')] = el.text
    diff_keys = [k for k in baseline_keys if baseline_keys[k] != new_keys.get(k)]
    print("Keys differing from baseline: " + str(len(diff_keys)))
    for k in diff_keys:
        print("  " + k + ": " + baseline_keys[k] + " -> " + new_keys[k])

if __name__ == "__main__":
    main()
