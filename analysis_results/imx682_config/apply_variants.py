#!/usr/bin/env python3
"""Apply variant-specific tuning changes to IMX682 LMC XML configs."""
import xml.etree.ElementTree as ET
import hashlib
import os

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\imx682_config"
BASELINE = os.path.join(BASE_DIR, "original_V2_Release_Day.xml")

def set_key(root, name, value):
    """Set the first string element with the given name."""
    for el in root.findall('string'):
        if el.get('name') == name:
            el.text = str(value)
            return True
    return False

def save(tree, path):
    tree.write(path, xml_declaration=True, encoding='utf-8')

def apply_variant(variant_name, changes):
    tree = ET.parse(BASELINE)
    root = tree.getroot()

    applied = 0
    missing = []
    for name, value in changes.items():
        if set_key(root, name, value):
            applied += 1
        else:
            missing.append(name)

    dst = os.path.join(BASE_DIR, f"{variant_name}.xml")
    save(tree, dst)

    if missing:
        print(f"  {variant_name}.xml: {applied}/{applied+len(missing)} keys modified, MISSING: {missing}")
    else:
        print(f"  {variant_name}.xml: {applied}/{applied} keys modified")
    return variant_name, dst

if __name__ == "__main__":
    detail_changes = {
        # Sharpening: increase for maximum detail
        'lib_sharpnessb_key': 3,
        'lib_sharpnessb_key_front': 3,
        'lib_sharpnessb_key_2': 3,
        'lib_sharpnessb_key_3': 3,
        'lib_sharpnessb_key_4': 3,
        'lib_sharpnessb_key_5': 3,
        'lib_sharpgain_key': 2,
        'lib_sharpmini_key': 2,
        # Noise reduction: reduce to preserve fine detail
        'lib_denoise_key': 0,
        'lib_lumadenoise_key': 0,
        'lib_lumanoise_key': 0,
        'lib_denoisesmoothing_key': 0,
        'pref_iso_noise_key': 1,
    }

    lowlight_changes = {
        # Noise reduction: increase for low light
        'lib_denoise_key': 2,
        'lib_lumadenoise_key': 2,
        'lib_lumanoise_key': 2,
        'lib_denoisesmoothing_key': 2,
        'pref_iso_noise_key': 4,
        # Sharpening: reduce to avoid amplifying noise
        'lib_sharpnessb_key': 0,
        'lib_sharpnessb_key_front': 0,
        'lib_sharpnessb_key_2': 0,
        'lib_sharpnessb_key_3': 0,
        'lib_sharpnessb_key_4': 0,
        'lib_sharpnessb_key_5': 0,
        'lib_sharpgain_key': 0,
        'lib_sharpmini_key': 0,
    }

    print("Applying variant modifications...")
    apply_variant("detail", detail_changes)
    apply_variant("lowlight", lowlight_changes)

    # Verify hashes now differ
    print("\nSHA-256 verification:")
    for name in ["original_V2_Release_Day", "balanced", "detail", "lowlight"]:
        path = os.path.join(BASE_DIR, f"{name}.xml")
        h = hashlib.sha256(open(path, 'rb').read()).hexdigest()
        print(f"  {name}: {h}")
