#!/usr/bin/env python3
"""Generate new optimized IMX682 LMC config from all calibration data."""
import xml.etree.ElementTree as ET
import hashlib
import os

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\imx682_config"
BASELINE = os.path.join(BASE_DIR, "original_V2_Release_Day.xml")
OUTPUT_DIR = BASE_DIR

def set_key(root, name, value):
    """Set the first string element with the given name."""
    for el in root.findall('string'):
        if el.get('name') == name:
            el.text = str(value)
            return True
    return False

def main():
    tree = ET.parse(BASELINE)
    root = tree.getroot()

    changes = {}

    # === AWB / Color ===
    # cw_rg_key: 0.5925 → 0.4500
    # Evidence: Warm cast R-G +3.3 to +6.8, R/B 1.078-1.096 across all analyzed photos.
    # Baseline cw_rg_key=0.5925 is too warm. Suffixed variants cw_rg_key_2-5 already at 0.4200.
    # Setting base key to 0.4500 (compromise between 0.5925 baseline and 0.4200 V2 test)
    # reduces warm cast without over-correction risk.
    changes['cw_rg_key'] = 0.4500

    # === Sharpening ===
    # lib_sharpnessb_key: 1 → 2
    # Evidence: Best MTF50 0.1438 cyc/px at EV 6.8 (checkerboard). Edge density 3.9-12.7%.
    # Moderate sharpening increase for detail retention without halo artifacts.
    changes['lib_sharpnessb_key'] = 2
    # lib_sharpgain_key: 1 → 2
    changes['lib_sharpgain_key'] = 2
    # lib_sharpmini_key: 1 → 2
    changes['lib_sharpmini_key'] = 2

    # === Noise Reduction (kept at baseline) ===
    # lib_denoise_key: 1 → 1 (keep; ISO up to 4909 covered by noise modeler, black clip 1.89-3.21%)
    # lib_lumadenoise_key: 1 → 1 (keep)
    # lib_lumanoise_key: 1 → 1 (keep)
    # lib_denoisesmoothing_key: 1 → 1 (keep)
    # pref_iso_noise_key: 2 → 2 (keep)

    # === HDR (kept at baseline) ===
    # pref_camera_hdr_plus_key: enhanced → keep (confirmed working, black clip 1.4-2.2%)

    # === Output Quality (kept at baseline) ===
    # pref_qjpg_key: 97 → 97 (keep)

    # Apply changes (base keys only; suffixed variants left at baseline values)
    print("Applying changes to baseline...")
    total_modified = 0
    for name, value in changes.items():
        if set_key(root, name, value):
            total_modified += 1
            print(f"  {name}: {value} (set)")
        else:
            print(f"  {name}: KEY NOT FOUND in baseline")

    # Save new config
    output_name = "LXX521_LMC84_Optimized.xml"
    output_path = os.path.join(OUTPUT_DIR, output_name)
    tree.write(output_path, xml_declaration=True, encoding='utf-8')

    # Verify
    verify_tree = ET.parse(output_path)
    verify_root = verify_tree.getroot()

    print("\n=== Verification ===")
    for name in changes:
        val = None
        for el in verify_root.findall('string'):
            if el.get('name') == name:
                val = el.text
                break
        print(f"  {name}: {val}")

    # Hash
    h = hashlib.sha256(open(output_path, 'rb').read()).hexdigest()
    baseline_h = hashlib.sha256(open(BASELINE, 'rb').read()).hexdigest()

    print(f"\nOutput: {output_path}")
    print(f"Baseline hash: {baseline_h}")
    print(f"New config hash: {h}")
    print(f"Different from baseline: {h != baseline_h}")
    print(f"Key count: {len(verify_root.findall('string'))}")

    return output_path

if __name__ == "__main__":
    main()
