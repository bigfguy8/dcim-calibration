#!/usr/bin/env python3
"""
generate_safe_master_config.py — Generate a crash-safe LMC 8.4 All-In-One
Master XML by adopting SkinTone_Perfect's proven-safe values for all
crash-critical parameters.

Overrides (proven-safe operational parameters from SkinTone_Perfect):
    pref_frames_hdr_key    : 0     (no HDR burst — prevents buffer overflow)
    pref_camera_hdr_plus_key: auto (stable HDR+ pipeline mode)
    pref_awb_key           : 0     (disables forced AWB override)
    pref_awbrec_key        : 0     (disables AWB recording override)
    cw_rg_key              : 0.5925  (natural white balance)
    cw_rg_key_2            : 0.5925
    cw_rg_key_3            : 0.5925
    cw_rg_key_4            : 0.5925
    cw_rg_key_5            : 0.5925
    lib_sharpgain_key      : 0     (no aggressive sharpening gain)
    lib_sharpmini_key      : 0     (no micro-sharpening)
    lib_sharpnessb_key     : 1.02  (gentle sharpness)
    lib_denoise_key        : 0     (no aggressive denoise)
    lib_denoisesmoothing_key: 0   (no over-smoothing)
    lib_lumadenoise_key    : 0
    lib_lumanoise_key      : 0
    lib_preservinghigh_key : 0
    lib_spatiala_key       : 0
    lib_spatialdenmi2_key  : 0
    pref_color_key         : 0     (no strong color cast)
    pref_gamma_curve_mode_key: -1
    pref_noise_model_key   : 0
    pref_qjpg_key          : 97    (balanced JPEG compression)
    pref_raw_key_main      : 0     (no raw output overhead)

The output is ALWAYS written to CALIB_LMC_DIR so the MGC app can
load it directly.
"""
from __future__ import annotations

import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict


# ---------------------------------------------------------------------------
# Safe overrides — crash-critical parameters from SkinTone_Perfect.
# ---------------------------------------------------------------------------
SAFE_OVERRIDES: Dict[str, str] = {
    # --- High HDR stack sizes (buffer overflow risk) ---
    "pref_frames_hdr_key": "0",
    "pref_camera_hdr_plus_key": "auto",
    "pref_hdrregion_key": "5",

    # --- Forced AWB / white-balance overrides ---
    "pref_awb_key": "0",
    "pref_awbrec_key": "0",
    "cw_rg_key": "0.5925",
    "cw_rg_key_2": "0.5925",
    "cw_rg_key_3": "0.5925",
    "cw_rg_key_4": "0.5925",
    "cw_rg_key_5": "0.5925",

    # --- Aggressive sharpening ---
    "lib_sharpgain_key": "0",
    "lib_sharpmini_key": "0",
    "lib_sharpnessb_key": "1.02",

    # --- Aggressive denoise / smoothing ---
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
}

# Deploy target — LMC 8.4 reads configs from this directory on the device
LMC84_DIR = (
    Path(os.environ["CALIB_LMC_DIR"]).expanduser()
    if os.environ.get("CALIB_LMC_DIR")
    else None
)


def get_elem_value(elem: ET.Element) -> str:
    """Get the value of an element (from 'value' attribute or text)."""
    return elem.attrib.get("value", elem.text or "")


def set_elem_value(elem: ET.Element, value: str) -> None:
    """Set the value of an element, removing 'value' attribute if present."""
    elem.text = value
    if "value" in elem.attrib:
        del elem.attrib["value"]


def generate_safe_master_config(
    input_path: str | Path,
    output_filename: str = "LXX521_IMX682_Safe_Master.xml",
) -> Path:
    """Generate a safe All-In-One Master config and deploy to CALIB_LMC_DIR.

    Returns the path to the deployed file.
    """
    input_path = Path(input_path)

    if not input_path.is_file():
        print(f"Error: Base template {input_path} not found.")
        raise FileNotFoundError(f"Base template {input_path} not found.")

    # Parse the source XML
    tree = ET.parse(input_path)
    root = tree.getroot()

    if root.tag != "map":
        raise ValueError(f"Expected <map> root, got <{root.tag}> in {input_path}")

    # Apply safe overrides to matching <string> elements
    applied = 0
    missing = []
    for key, safe_value in SAFE_OVERRIDES.items():
        found = False
        for elem in root.iter("string"):
            if elem.get("name") == key:
                set_elem_value(elem, safe_value)
                applied += 1
                found = True
                break
        if not found:
            missing.append(key)

    print(f"Applied {applied}/{len(SAFE_OVERRIDES)} safe overrides.")
    if missing:
        print(f"Warning: keys not found in source: {missing}")

    # Ensure deploy directory exists
    if LMC84_DIR is None:
        raise SystemExit("[-] set CALIB_LMC_DIR to the MGC profile directory")
    LMC84_DIR.mkdir(parents=True, exist_ok=True)

    # Write to the configured MGC profile directory
    deploy_path = LMC84_DIR / output_filename
    tree.write(deploy_path, encoding="utf-8", xml_declaration=True)
    print(f"Successfully generated safe All-In-One config at: {deploy_path}")

    # Also keep a local copy next to the source for version tracking
    local_copy = input_path.parent / output_filename
    shutil.copy2(deploy_path, local_copy)
    print(f"Local copy saved: {local_copy}")

    return deploy_path


if __name__ == "__main__":
    # Source AllInOne Master and output path
    source_xml = "configs/xml/LXX521_TEX.xml"
    target_xml = "LXX521_IMX682_Safe_Master.xml"
    generate_safe_master_config(source_xml, target_xml)
