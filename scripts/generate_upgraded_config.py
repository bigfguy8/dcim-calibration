#!/usr/bin/env python3
"""
generate_upgraded_config.py — Generate an upgraded LMC 8.4 All-In-One Master
XML based on DCIM calibration analysis of the Lava Play Ultra (LXX521) /
Sony IMX682 sensor.

Analysis findings from /sdcard/DCIM/Camera captures:
  - R/B ratio: 7.6-9.5 (portraits) → Severe warm cast, target ~0.61
  - Sharpness: 19.9-298.4 → Highly inconsistent across lighting
  - MTF50: Not measurable → No edge detail
  - Black clip: Up to 12.56% → Crushed shadows
  - Edge density: 2-17% → Low texture detail

Optimizations applied:
  - AWB: pref_awb_key=1 (auto AWB), cw_rg_key=0.5725 (neutral white balance)
  - Sharpness: lib_sharpgain_key=1.0, lib_sharpnessb_key=1.1, lib_sharpmini_key=0.5
  - Denoise: lib_denoise_key=1, lib_lumadenoise_key=1, pref_noise_model_key=1
  - Dynamic range: pref_frames_hdr_key=2, pref_preservinghigh_key=1
  - JPEG quality: pref_qjpg_key=95
  - Golden ratio grid: pref_camera_grid_lines_mode=2
  - Sound off: pref_camera_single_shot_sound_key=0

Output: LXX521_IMX682_LMC84_Upgraded_Master.xml deployed to /sdcard/LMC8.4/
"""
from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

LMC84_DIR = Path("/sdcard/LMC8.4")

# Best-tuned parameters for IMX682 + LXX521 based on DCIM calibration analysis
UPGRADED_PARAMS: Dict[str, str] = {
    # --- White Balance (fix warm cast: R/B 7.6-9.5 → target ~0.61) ---
    "pref_awb_key": "1",           # Enable auto AWB (was 0)
    "pref_awbrec_key": "1",        # Enable AWB recording
    "cw_rg_key": "0.5725",         # Neutral RG balance (was 0.5925)
    "cw_rg_key_2": "0.5725",
    "cw_rg_key_3": "0.5725",
    "cw_rg_key_4": "0.5725",
    "cw_rg_key_5": "0.5725",
    # --- Sharpness (fix inconsistent 19.9-298.4) ---
    "lib_sharpgain_key": "1.0",    # Moderate sharpening gain (was 0)
    "lib_sharpmini_key": "0.5",    # Light micro-sharpening (was 0)
    "lib_sharpnessb_key": "1.1",   # Balanced sharpness (was 1.02)
    # --- Denoise (fix noise in low light) ---
    "lib_denoise_key": "1",        # Light denoise (was 0)
    "lib_denoisesmoothing_key": "1", # Light denoise smoothing
    "lib_lumadenoise_key": "1",    # Light luma denoise (was 0)
    "lib_lumanoise_key": "1",      # Light luma noise processing
    "pref_noise_model_key": "1",   # Enable noise model
    # --- Dynamic Range (fix black clip up to 12.56%) ---
    "pref_frames_hdr_key": "2",    # Multi-frame HDR (was 0)
    "pref_preservinghigh_key": "1",# Preserve highlights (was 0)
    "lib_preservinghigh_key": "1",
    # --- JPEG Quality ---
    "pref_qjpg_key": "95",         # Balanced quality (was 97)
    # --- Best-practice: Composition & Audio ---
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


def set_elem_value(elem: ET.Element, value: str) -> None:
    elem.text = value
    if "value" in elem.attrib:
        del elem.attrib["value"]


def generate_upgraded_config(
    base_path: Path,
    output_filename: str = "LXX521_IMX682_LMC84_Upgraded_Master.xml",
) -> Path:
    """Generate the best-tuned LMC 8.4 Master config.

    Starts from the PATCHED master and overlays calibration-optimized
    parameters derived from DCIM capture analysis of the IMX682 sensor
    on the LXX521 platform.
    """
    base_path = Path(base_path)

    if not base_path.is_file():
        raise FileNotFoundError(f"Base profile not found: {base_path}")

    tree = parse_xml(base_path)
    root = tree.getroot()
    params = build_param_map(root)

    applied = 0
    missing = []
    for key, val in UPGRADED_PARAMS.items():
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

    print(f"Applied {applied}/{len(UPGRADED_PARAMS)} upgraded parameters.")
    if missing:
        print(f"Warning: {len(missing)} keys not found and not added.")

    # Validate well-formedness
    ET.tostring(root, encoding="utf-8", xml_declaration=True)

    # Deploy to /sdcard/LMC8.4/
    LMC84_DIR.mkdir(parents=True, exist_ok=True)
    deploy_path = LMC84_DIR / output_filename
    tree.write(deploy_path, encoding="utf-8", xml_declaration=True)
    print(f"Upgraded config deployed to: {deploy_path}")

    # Keep local copy in configs/xml/
    local_copy = Path("configs/xml") / output_filename
    shutil.copy2(deploy_path, local_copy)
    print(f"Local copy saved: {local_copy}")

    return deploy_path


if __name__ == "__main__":
    base_path = Path("configs/xml/LXX521_IMX682_LMC84_AllInOne_Master_PATCHED.xml")
    output_filename = "LXX521_IMX682_LMC84_Upgraded_Master.xml"
    generate_upgraded_config(base_path, output_filename)
