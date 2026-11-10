#!/usr/bin/env python3
"""
generate_best_tuned_config.py — Generate the best-tuned LMC 8.4 All-In-One
Master XML for Lava Play Ultra (LXX521) / Sony IMX682 sensor.

This profile synthesizes calibration findings from DCIM capture analysis:

  CRITICAL FIXES (from DCIM analysis):
  - pref_awb_key=0          : Disable forced AWB (was causing R/B ratio 7.6-9.5)
  - cw_rg_key*=0.5925       : Natural white balance (was 0.42-0.45 cool cast)
  - pref_frames_hdr_key=0   : Disable HDR burst (was 12 — buffer overflow risk)
  - pref_camera_hdr_plus_key=auto : Stable HDR+ (was enhanced)
  - lib_sharpgain_key=0     : No aggressive sharpening gain (was 2)
  - lib_sharpnessb_key=1.02 : Gentle sharpness (was 2 — inconsistent 19.9-298.4)
  - lib_denoise_key=0       : No aggressive denoise (was 1)
  - pref_qjpg_key=97        : Balanced JPEG (was 100)

  BEST-PRACTICE SETTINGS:
  - pref_camera_grid_lines_mode=2 : Golden ratio composition grid
  - pref_camera_single_shot_sound_key=0 : Camera shutter sound off

Output: LXX521_IMX682_LMC84_Best_Tuned_Master.xml deployed to /sdcard/LMC8.4/
"""
from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

LMC84_DIR = Path("/sdcard/LMC8.4")

# All calibration-optimized parameters for IMX682 + LXX521
BEST_TUNED_PARAMS: Dict[str, str] = {
    # --- Crash-critical: HDR Stack (buffer overflow risk) ---
    "pref_frames_hdr_key": "0",
    "pref_camera_hdr_plus_key": "auto",
    "pref_hdrregion_key": "5",
    # --- Crash-critical: AWB / White Balance (forced override crashes) ---
    "pref_awb_key": "0",
    "pref_awbrec_key": "0",
    "cw_rg_key": "0.5925",
    "cw_rg_key_2": "0.5925",
    "cw_rg_key_3": "0.5925",
    "cw_rg_key_4": "0.5925",
    "cw_rg_key_5": "0.5925",
    # --- Crash-critical: Sharpening (halos / viewfinder crash) ---
    "lib_sharpgain_key": "0",
    "lib_sharpmini_key": "0",
    "lib_sharpnessb_key": "1.02",
    # --- Crash-critical: Denoise (pipeline crash) ---
    "lib_denoise_key": "0",
    "lib_denoisesmoothing_key": "0",
    "lib_lumadenoise_key": "0",
    "lib_lumanoise_key": "0",
    # --- Other aggressive processing ---
    "lib_preservinghigh_key": "0",
    "lib_spatiala_key": "0",
    "lib_spatialdenmi2_key": "0",
    "pref_color_key": "0",
    "pref_gamma_curve_mode_key": "-1",
    "pref_noise_model_key": "0",
    "pref_qjpg_key": "97",
    "pref_raw_key_main": "0",
    # --- Best-practice: Composition & Audio ---
    "pref_camera_grid_lines_mode": "2",
    "pref_camera_single_shot_sound_key": "0",
}


def parse_xml(path: Path) -> ET.ElementTree:
    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag != "map":
        raise ValueError(f"Expected <map> root, got <{root.tag}> in {path}")
    return tree


def build_param_map(root: ET.Element) -> Dict[str, ET.Element]:
    params: Dict[str, ET.Element] = {}
    for elem in root.iter("string"):
        name = elem.attrib.get("name")
        if name:
            params[name] = elem
    return params


def set_elem_value(elem: ET.Element, value: str) -> None:
    elem.text = value
    if "value" in elem.attrib:
        del elem.attrib["value"]


def generate_best_tuned_config(
    base_path: Path,
    output_filename: str = "LXX521_IMX682_LMC84_Best_Tuned_Master.xml",
) -> Path:
    """Generate the best-tuned LMC 8.4 Master config.

    Starts from the PATCHED master (which already has 25 crash-critical
    fixes applied) and overlays best-practice parameters for IMX682 +
    LXX521 hardware.
    """
    base_path = Path(base_path)

    if not base_path.is_file():
        raise FileNotFoundError(f"Base profile not found: {base_path}")

    tree = parse_xml(base_path)
    root = tree.getroot()
    params = build_param_map(root)

    applied = 0
    missing = []
    for key, val in BEST_TUNED_PARAMS.items():
        if key in params:
            set_elem_value(params[key], val)
            applied += 1
        else:
            # Add missing key
            new_elem = ET.Element("string")
            new_elem.set("name", key)
            new_elem.text = val
            root.append(new_elem)
            params[key] = new_elem
            applied += 1

    print(f"Applied {applied}/{len(BEST_TUNED_PARAMS)} best-tuned parameters.")
    if missing:
        print(f"Warning: {len(missing)} keys not found and not added.")

    # Validate well-formedness
    ET.tostring(root, encoding="utf-8", xml_declaration=True)

    # Deploy to /sdcard/LMC8.4/
    LMC84_DIR.mkdir(parents=True, exist_ok=True)
    deploy_path = LMC84_DIR / output_filename
    tree.write(deploy_path, encoding="utf-8", xml_declaration=True)
    print(f"Best-tuned config deployed to: {deploy_path}")

    # Keep local copy in configs/xml/
    local_copy = Path("configs/xml") / output_filename
    shutil.copy2(deploy_path, local_copy)
    print(f"Local copy saved: {local_copy}")

    return deploy_path


if __name__ == "__main__":
    base_path = Path("configs/xml/LXX521_IMX682_LMC84_AllInOne_Master_PATCHED.xml")
    output_filename = "LXX521_IMX682_LMC84_Best_Tuned_Master.xml"
    generate_best_tuned_config(base_path, output_filename)
