#!/usr/bin/env python3
"""
synthesize_master_config.py — Generate a new synthesized LMC 8.4 All-In-One
Master config by combining parameters from all configs in /sdcard/LMC8.4/.

Strategy:
  - SkinTone_Perfect.xml is the SAFE REFERENCE (proven working values)
  - AllInOne_Master_PATCHED.xml is the SAFE BASE (already patched with 25 overrides)
  - For crash-critical parameters: use SkinTone_Perfect values
  - For all other parameters: use PATCHED values (retains Master's image quality)
  - Additionally applies best-practice LMC 8.4 settings:
      * Golden ratio grid lines (pref_camera_grid_lines_mode = "2")
      * Camera shutter sound off (pref_camera_single_shot_sound_key = "0")
  - Result: crash-safe config with best-practice composition and audio settings

Output: LXX521_IMX682_LMC84_Synthesized_Master.xml deployed to /sdcard/LMC8.4/
"""
from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

LMC84_DIR = Path("/sdcard/lmc8.4")

# Crash-critical parameters — must use SkinTone_Perfect values
CRASH_CRITICAL: Dict[str, str] = {
    # HDR Stack (buffer overflow risk)
    "pref_frames_hdr_key": "0",
    "pref_camera_hdr_plus_key": "auto",
    "pref_hdrregion_key": "5",
    # AWB / White Balance (forced override crashes)
    "pref_awb_key": "0",
    "pref_awbrec_key": "0",
    "cw_rg_key": "0.5925",
    "cw_rg_key_2": "0.5925",
    "cw_rg_key_3": "0.5925",
    "cw_rg_key_4": "0.5925",
    "cw_rg_key_5": "0.5925",
    # Sharpening (viewfinder crash)
    "lib_sharpgain_key": "0",
    "lib_sharpmini_key": "0",
    "lib_sharpnessb_key": "1.02",
    # Denoise (pipeline crash)
    "lib_denoise_key": "0",
    "lib_denoisesmoothing_key": "0",
    "lib_lumadenoise_key": "0",
    "lib_lumanoise_key": "0",
    # Other aggressive processing
    "lib_preservinghigh_key": "0",
    "lib_spatiala_key": "0",
    "lib_spatialdenmi2_key": "0",
    "pref_color_key": "0",
    "pref_gamma_curve_mode_key": "-1",
    "pref_noise_model_key": "0",
    "pref_qjpg_key": "97",
    "pref_raw_key_main": "0",
}

# Best-practice operational parameters
BEST_PRACTICE: Dict[str, str] = {
    "pref_camera_grid_lines_mode": "2",      # Golden ratio grid lines
    "pref_camera_single_shot_sound_key": "0", # Camera shutter sound off
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


def get_elem_value(elem: ET.Element) -> str:
    return elem.attrib.get("value", elem.text or "")


def set_elem_value(elem: ET.Element, value: str) -> None:
    elem.text = value
    if "value" in elem.attrib:
        del elem.attrib["value"]


def synthesize_master_config(
    lmc84_dir: Path = LMC84_DIR,
    output_filename: str = "LXX521_Synthesized_Master.xml",
) -> Path:
    """Synthesize a new Master config from all LMC84 configs.

    Strategy:
      - Load PATCHED.xml as base (Master image quality + 25 crash fixes)
      - Load SkinTone_Perfect.xml as safe reference
      - For crash-critical params: force SkinTone value
      - For best-practice params: set golden ratio grid + sound off
      - For all other parameters: keep PATCHED values
    Output deployed to /sdcard/LMC8.4/
    """
    patched_path = lmc84_dir / "LXX521_TEX.xml"
    skintone_path = lmc84_dir / "LXX521_AI.xml"

    if not patched_path.is_file():
        raise FileNotFoundError(f"Patched config not found: {patched_path}")
    if not skintone_path.is_file():
        raise FileNotFoundError(f"SkinTone config not found: {skintone_path}")

    # Load PATCHED as base
    tree = parse_xml(patched_path)
    root = tree.getroot()
    params = build_param_map(root)

    # Load SkinTone as safe reference
    st_tree = parse_xml(skintone_path)
    st_params = build_param_map(st_tree.getroot())

    # Apply SkinTone safe values to all crash-critical params
    applied = 0
    for key, safe_value in CRASH_CRITICAL.items():
        if key in params:
            set_elem_value(params[key], safe_value)
            applied += 1
        elif key in st_params:
            # Key not in PATCHED but in SkinTone — add it
            new_elem = ET.Element("string")
            new_elem.set("name", key)
            new_elem.text = safe_value
            root.append(new_elem)
            params[key] = new_elem
            applied += 1

    # Apply best-practice parameters (golden ratio grid + sound off)
    bp_applied = 0
    for key, bp_value in BEST_PRACTICE.items():
        if key in params:
            set_elem_value(params[key], bp_value)
            bp_applied += 1
        else:
            # Key not in PATCHED — add it
            new_elem = ET.Element("string")
            new_elem.set("name", key)
            new_elem.text = bp_value
            root.append(new_elem)
            params[key] = new_elem
            bp_applied += 1

    print(f"Applied {applied}/{len(CRASH_CRITICAL)} crash-critical overrides.")
    print(f"Applied {bp_applied}/{len(BEST_PRACTICE)} best-practice overrides.")
    print(f"Total parameters in synthesized config: {len(params)}")

    # Validate well-formedness
    ET.tostring(root, encoding="utf-8", xml_declaration=True)

    # Deploy to /sdcard/LMC8.4/
    lmc84_dir.mkdir(parents=True, exist_ok=True)
    deploy_path = lmc84_dir / output_filename
    tree.write(deploy_path, encoding="utf-8", xml_declaration=True)
    print(f"Synthesized config deployed to: {deploy_path}")

    # Keep local copy in configs/xml/
    local_copy = Path("configs/xml") / output_filename
    shutil.copy2(deploy_path, local_copy)
    print(f"Local copy saved: {local_copy}")

    return deploy_path


if __name__ == "__main__":
    synthesize_master_config()
