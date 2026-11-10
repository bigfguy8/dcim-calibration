#!/usr/bin/env python3
"""
generate_best_tuned_config.py — Generate a clean, best-tuned LMC 8.4 All-In-One
Master XML configuration for Lava Play Ultra (LXX521) / Sony IMX682 sensor.

Calibrated from DCIM capture analysis:
- R/B ratio fix: AWB enabled with neutral color temperature (cw_rg=0.5725)
- Sharpness: Balanced enhancement (sharpgain=1.0, sharpnessb=1.1)
- Denoise: Balanced noise reduction (denoise=1, lumadenoise=1)
- Dynamic Range: HDR enabled (frames_hdr=2), highlight preservation enabled
- JPEG quality: 95
- Golden ratio grid: enabled (mode=2)
- Camera shutter sound: off

Output: LXX521_IMX682_LMC84_Best.xml deployed to /sdcard/LMC8.4/
"""
from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

LMC84_DIR = Path("/sdcard/LMC8.4")

# Best-tuned parameters for IMX682 + LXX521 from DCIM calibration analysis
BEST_TUNED_PARAMS: Dict[str, str] = {
    # --- AWB / White Balance ---
    "pref_awb_key": "1",
    "pref_awbrec_key": "1",
    "cw_rg_key": "0.5725",
    "cw_rg_key_2": "0.5725",
    "cw_rg_key_3": "0.5725",
    "cw_rg_key_4": "0.5725",
    "cw_rg_key_5": "0.5725",
    # --- Sharpness ---
    "lib_sharpgain_key": "1.0",
    "lib_sharpmini_key": "0.5",
    "lib_sharpnessb_key": "1.1",
    # --- Denoise ---
    "lib_denoise_key": "1",
    "lib_denoisesmoothing_key": "1",
    "lib_lumadenoise_key": "1",
    "lib_lumanoise_key": "1",
    "pref_noise_model_key": "1",
    # --- Dynamic Range ---
    "pref_frames_hdr_key": "2",
    "pref_preservinghigh_key": "1",
    "lib_preservinghigh_key": "1",
    # --- JPEG Quality ---
    "pref_qjpg_key": "95",
    "pref_raw_key_main": "0",
    # --- Best-Practice: Composition & Audio ---
    "pref_camera_grid_lines_mode": "2",
    "pref_camera_single_shot_sound_key": "0",
    # --- Saturation & Contrast ---
    "lib_saturation_key": "0.95",
    "lib_saturation2_key": "0.95",
    "lib_contrast_1_key": "1",
    "lib_contrast_2_key": "1",
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
    output_filename: str = "LXX521_IMX682_LMC84_Best.xml",
) -> Path:
    """Generate the best-tuned LMC 8.4 Master config."""
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

    # Deploy to /sdcard/LMC8.4/
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
    base_path = Path("configs/xml/LXX521_IMX682_LMC84_AllInOne_Master_PATCHED.xml")
    output_filename = "LXX521_IMX682_LMC84_Best.xml"
    generate_best_tuned_config(base_path, output_filename)
