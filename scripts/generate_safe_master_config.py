#!/usr/bin/env python3
"""
generate_safe_master_config.py — Generate a crash-safe LMC 8.4 All-In-One
Master XML by lowering only the most aggressive parameters to safe values.

Overrides (proven-safe operational parameters):
    pref_frames_hdr_key    : 3     (prevents buffer overflow crashes)
    pref_camera_hdr_plus_key: auto (stable HDR+ pipeline mode)
    pref_awb_key           : 0     (disables forced AWB override)
    pref_qjpg_key          : 97    (balanced JPEG compression)

The output is ALWAYS written to /sdcard/LMC84/ so the LMC 8.4 app can
load it directly.
"""
from __future__ import annotations

import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Safe overrides — only the most aggressive crash-causing parameters.
# ---------------------------------------------------------------------------
SAFE_OVERRIDES = {
    "pref_frames_hdr_key": "3",       # Prevents buffer overflow crashes
    "pref_camera_hdr_plus_key": "auto",  # Stable HDR+ pipeline mode
    "pref_awb_key": "0",              # Disables forced AWB override
    "pref_qjpg_key": "97",            # Optimized balanced JPEG compression
}

# Deploy target — LMC 8.4 reads configs from this directory on the device
LMC84_DIR = Path("/sdcard/LMC84")


def generate_safe_master_config(
    input_path: str | Path,
    output_filename: str = "LXX521_IMX682_Safe_Master.xml",
) -> Path:
    """Generate a safe All-In-One Master config and deploy to /sdcard/LMC84/.

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
                elem.text = safe_value
                # Remove 'value' attribute if present; text is authoritative
                if "value" in elem.attrib:
                    del elem.attrib["value"]
                applied += 1
                found = True
                break
        if not found:
            missing.append(key)

    print(f"Applied {applied}/{len(SAFE_OVERRIDES)} safe overrides.")
    if missing:
        print(f"Warning: keys not found in source: {missing}")

    # Ensure deploy directory exists
    LMC84_DIR.mkdir(parents=True, exist_ok=True)

    # Write to /sdcard/LMC84/ (always)
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
    source_xml = "configs/xml/LXX521_IMX682_LMC84_AllInOne_Master.xml"
    target_xml = "LXX521_IMX682_Safe_Master.xml"
    generate_safe_master_config(source_xml, target_xml)
