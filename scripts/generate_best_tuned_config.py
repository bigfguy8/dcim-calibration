#!/usr/bin/env python3
"""
generate_best_tuned_config.py — Generate a clean, best-tuned LMC 8.4 All-In-One
Master XML for Lava Play Ultra (LXX521) / Sony IMX682 sensor.

Calibrated from DCIM capture analysis:
- R/B ratio fix: AWB auto, cw_rg ~0.5725
- Sharpness: lib_sharpgain_key=1.0, lib_sharpnessb_key=1.1, lib_sharpmini_key=0.5
- Denoise: lib_denoise_key=1, lib_lumadenoise_key=1, pref_noise_model_key=1
- Dynamic Range: pref_frames_hdr_key=2, pref_preservinghigh_key=1
- JPEG Quality: pref_qjpg_key=95
- Golden ratio grid: pref_camera_grid_lines_mode=2
- Camera shutter sound: pref_camera_single_shot_sound_key=0
- Bokeh / Portrait Mode: pref_Copmode_portrait_key=1, pref_opmode_portrait_key=1,
  lib_depth1_key=1, lib_depth2_key=1, lib_sharpeningedge_key=1

Output: LXX521_IMX682_LMC84_Best.xml deployed to CALIB_LMC_DIR
"""
from __future__ import annotations

import argparse
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

LMC84_DIR = (
    Path(os.environ["CALIB_LMC_DIR"]).expanduser()
    if os.environ.get("CALIB_LMC_DIR")
    else None
)

# Best-tuned parameters for IMX682 + LXX521 (calibrated from DCIM data)
BEST_TUNED_PARAMS: dict[str, str] = {
    # --- AWB / White Balance (fix warm cast: R/B up to 1.37) ---
    "pref_awb_key": "1",            # Auto AWB
    "pref_awbrec_key": "1",         # AWB recording
    "cw_rg_key": "0.5725",          # Neutral-warm balance (was 0.5925)
    "cw_rg_key_2": "0.5725",
    "cw_rg_key_3": "0.5725",
    "cw_rg_key_4": "0.5725",
    "cw_rg_key_5": "0.5725",
    # --- Sharpness (fix inconsistent 19.9-298.4) ---
    "lib_sharpgain_key": "1.0",     # Balanced sharpness gain
    "lib_sharpmini_key": "0.5",     # Light micro-sharpening
    "lib_sharpnessb_key": "1.1",    # Balanced sharpness
    # --- Denoise (fix high ISO noise up to ISO 6200) ---
    "lib_denoise_key": "1",
    "lib_denoisesmoothing_key": "1",
    "lib_lumadenoise_key": "1",
    "lib_lumanoise_key": "1",
    "pref_noise_model_key": "1",
    # --- Dynamic Range (fix black clip up to 12.56%) ---
    "pref_frames_hdr_key": "2",
    "pref_preservinghigh_key": "1",
    "lib_preservinghigh_key": "1",
    # --- JPEG Quality ---
    "pref_qjpg_key": "95",
    "pref_raw_key_main": "0",
    # --- Best-Practice: Composition & Audio ---
    "pref_camera_grid_lines_mode": "2",      # Golden ratio grid
    "pref_camera_single_shot_sound_key": "0", # Camera sound off
    # --- Saturation & Contrast ---
    "lib_saturation_key": "0.95",
    "lib_saturation2_key": "0.95",
    "lib_contrast_1_key": "1",
    "lib_contrast_2_key": "1",
    # --- Bokeh / Portrait Mode ---
    "pref_Copmode_portrait_key": "1",
    "pref_Copmode_portrait_key_2": "1",
    "pref_Copmode_portrait_key_3": "1",
    "pref_Copmode_portrait_key_4": "1",
    "pref_Copmode_portrait_key_5": "1",
    "pref_Copmode_portrait_key_front": "1",
    "pref_opmode_portrait_key": "1",
    "pref_opmode_portrait_key_2": "1",
    "pref_opmode_portrait_key_3": "1",
    "pref_opmode_portrait_key_4": "1",
    "pref_opmode_portrait_key_5": "1",
    "pref_opmode_portrait_key_front": "1",
    "lib_depth1_key": "1",
    "lib_depth1_key_2": "1",
    "lib_depth1_key_3": "1",
    "lib_depth1_key_4": "1",
    "lib_depth1_key_5": "1",
    "lib_depth1_key_front": "1",
    "lib_depth1_pro_key": "1",
    "lib_depth2_key": "1",
    "lib_depth2_key_2": "1",
    "lib_depth2_key_3": "1",
    "lib_depth2_key_4": "1",
    "lib_depth2_key_5": "1",
    "lib_depth2_key_front": "1",
    "lib_depth2_pro_key": "1",
    "lib_sharpeningedge_key": "1",
    "lib_sharpeningedge_key_2": "1",
    "lib_sharpeningedge_key_3": "1",
    "lib_sharpeningedge_key_4": "1",
    "lib_sharpeningedge_key_5": "1",
    "lib_sharpeningedge_key_front": "1",
    "lib_sharpeningedge_pro_key": "1",
}


def parse_xml(path: Path) -> ET.ElementTree:
    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag != "map":
        raise ValueError(f"Expected <map> root, got <{root.tag}> in {path}")
    return tree


def build_param_map(root: ET.Element) -> dict[str, ET.Element]:
    params: dict[str, ET.Element] = {}
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
    output_filename: str = "LXX521_IMX682_LMC84_Best.xml",
) -> Path:
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

    # Deploy to the configured MGC profile directory
    if LMC84_DIR is None:
        raise SystemExit("[-] set CALIB_LMC_DIR to the MGC profile directory")
    LMC84_DIR.mkdir(parents=True, exist_ok=True)
    deploy_path = LMC84_DIR / output_filename
    tree.write(deploy_path, encoding="utf-8", xml_declaration=True)
    print(f"Best-tuned config deployed to: {deploy_path}")

    # Keep local copy
    local_copy = Path("configs/xml") / output_filename
    shutil.copy2(deploy_path, local_copy)
    print(f"Local copy saved: {local_copy}")

    return deploy_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate LMC 8.4 IMX682 best-tuned calibration XML"
    )
    parser.add_argument(
        "--base",
        default="configs/xml/LXX521_TEX.xml",
        help="Path to base XML profile",
    )
    parser.add_argument(
        "--output",
        default="LXX521_IMX682_LMC84_Best.xml",
        help="Output filename (deployed to CALIB_LMC_DIR)",
    )
    args = parser.parse_args()

    generate_best_tuned_config(args.base, args.output)
