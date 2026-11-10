#!/usr/bin/env python3
"""
patch_master.py — Safely patch LXX521_IMX682_LMC84_AllInOne_Master.xml

Compares the All-In-One Master profile against the proven-safe
SkinTone_Perfect profile and applies SkinTone's stable values to all
crash-critical parameters that can cause pipeline/viewfinder crashes
on the IMX682 sensor (high HDR stack sizes, forced AWB overrides,
excessive sharpening/denoise, aggressive color casts).

The script retains all Master image-quality parameters that are NOT
crash-critical, only overriding those where SkinTone's value is the
safe, proven-working boundary.

Usage:
    python patch_master.py \
        --master configs/xml/LXX521_IMX682_LMC84_AllInOne_Master.xml \
        --reference configs/xml/LXX521_IMX682_LMC84_SkinTone_Perfect.xml \
        --output configs/xml/LXX521_IMX682_LMC84_AllInOne_Master_PATCHED.xml
"""

from __future__ import annotations

import argparse
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict


# ---------------------------------------------------------------------------
# Crash-critical parameter overrides.
#
# Every key here maps Master's aggressive value to SkinTone's proven-safe
# value. ALL overrides are applied unconditionally — the only criterion
# is that Master differs from SkinTone. We do NOT skip parameters where
# SkinTone's value is numerically higher (e.g. cw_rg_key 0.42->0.5925),
# because for color-temperature/WB keys the "safe" direction is not
# simply "lower".
# ---------------------------------------------------------------------------
CRITICAL_OVERRIDES: Dict[str, str] = {
    # --- High HDR stack sizes (buffer overflow / viewfinder crash) ---
    "pref_frames_hdr_key": "0",           # Master=12 (large HDR burst)
    "pref_camera_hdr_plus_key": "auto",   # Master=enhanced (aggressive HDR+)
    "pref_hdrregion_key": "5",            # Master=8 (heavy HDR region map)

    # --- Forced AWB / white-balance overrides (crash risk) ---
    "pref_awb_key": "0",                  # Master=1 (forced AWB on)
    "pref_awbrec_key": "0",               # Master=1 (AWB recording override)
    "cw_rg_key": "0.5925",                # Master=0.4500 (cool cast)
    "cw_rg_key_2": "0.5925",              # Master=0.4200
    "cw_rg_key_3": "0.5925",              # Master=0.4200
    "cw_rg_key_4": "0.5925",              # Master=0.4200
    "cw_rg_key_5": "0.5925",              # Master=0.4200

    # --- Aggressive sharpening (halos / viewfinder crash) ---
    "lib_sharpgain_key": "0",             # Master=2 (high gain)
    "lib_sharpmini_key": "0",             # Master=2 (high micro-sharpening)
    "lib_sharpnessb_key": "1.02",         # Master=2 (high sharpness)

    # --- Aggressive denoise / smoothing (pipeline crash) ---
    "lib_denoise_key": "0",               # Master=1
    "lib_denoisesmoothing_key": "0",      # Master=2
    "lib_lumadenoise_key": "0",           # Master=1
    "lib_lumanoise_key": "0",             # Master=1

    # --- Other aggressive processing ---
    "lib_preservinghigh_key": "0",        # Master=1
    "lib_spatiala_key": "0",              # Master=1
    "lib_spatialdenmi2_key": "0",         # Master=1
    "pref_color_key": "0",                # Master=-4 (strong color cast)
    "pref_gamma_curve_mode_key": "-1",    # Master=0
    "pref_noise_model_key": "0",          # Master=1
    "pref_qjpg_key": "97",                # Master=100 (max JPEG quality)
    "pref_raw_key_main": "0",             # Master=1 (raw output overhead)
}


def parse_xml(path: Path) -> ET.ElementTree:
    """Parse an LMC 8.4 <map> XML file."""
    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag != "map":
        raise ValueError(f"Expected <map> root, got <{root.tag}> in {path}")
    return tree


def build_param_map(root: ET.Element) -> Dict[str, ET.Element]:
    """Return a dict of param name -> element for quick lookup."""
    params: Dict[str, ET.Element] = {}
    for elem in root.iter("string"):
        name = elem.attrib.get("name")
        if name:
            params[name] = elem
    return params


def get_elem_value(elem: ET.Element) -> str:
    """Get the value of an element (from 'value' attribute or text)."""
    return elem.attrib.get("value", elem.text or "")


def set_elem_value(elem: ET.Element, value: str) -> None:
    """Set the value of an element, removing 'value' attribute if present."""
    elem.text = value
    if "value" in elem.attrib:
        del elem.attrib["value"]


def patch_master(
    master_path: Path,
    reference_path: Path,
    output_path: Path,
    dry_run: bool = False,
) -> None:
    """Patch the Master XML with safe SkinTone values.

    Applies ALL crash-critical overrides from SkinTone to Master
    unconditionally — no numeric comparison logic that could skip
    valid overrides.
    """

    # Load both files
    master_tree = parse_xml(master_path)
    master_root = master_tree.getroot()
    master_params = build_param_map(master_root)

    reference_tree = parse_xml(reference_path)
    reference_root = reference_tree.getroot()
    reference_params = build_param_map(reference_root)

    # Determine which overrides to apply
    overrides_to_apply: Dict[str, str] = {}
    skipped_missing: list[str] = []
    skipped_same: list[str] = []

    for key, safe_value in CRITICAL_OVERRIDES.items():
        if key not in master_params:
            skipped_missing.append(key)
            continue
        current_value = get_elem_value(master_params[key])
        if current_value == safe_value:
            skipped_same.append(key)
            continue
        overrides_to_apply[key] = safe_value

    # Report plan
    print("=== PATCH MASTER PLAN ===")
    print(f"Critical overrides defined: {len(CRITICAL_OVERRIDES)}")
    print(f"Overrides to apply:         {len(overrides_to_apply)}")
    print(f"Skipped (missing in Master): {len(skipped_missing)}")
    print(f"Skipped (already same):      {len(skipped_same)}")
    print()

    if skipped_missing:
        print("  Missing in Master:", ", ".join(skipped_missing))
    if skipped_same:
        print("  Already same:", ", ".join(skipped_same))
    print()

    if not overrides_to_apply:
        print("No changes needed. Master is already safe.")
        return

    # Apply overrides
    print("=== APPLYING OVERRIDES ===")
    for key, safe_value in sorted(overrides_to_apply.items()):
        elem = master_params[key]
        old_value = get_elem_value(elem)
        set_elem_value(elem, safe_value)
        print(f"  {key}: {old_value!r} -> {safe_value!r}")

    # Write output
    if dry_run:
        print("\n=== DRY RUN: no file written ===")
        return

    # Backup original
    backup_path = master_path.with_suffix(master_path.suffix + ".bak")
    shutil.copy2(master_path, backup_path)
    print(f"\nBackup saved: {backup_path}")

    # Write patched XML
    master_tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"Patched XML written: {output_path}")

    # Validation — re-read and verify every override
    print("\n=== VALIDATION ===")
    validate_tree = ET.parse(output_path)
    validate_params = build_param_map(validate_tree.getroot())

    all_applied = True
    for key, safe_value in overrides_to_apply.items():
        actual = validate_params.get(key)
        if actual is None:
            print(f"  FAIL: {key} not found in output!")
            all_applied = False
        else:
            actual_val = get_elem_value(actual)
            if actual_val != safe_value:
                print(f"  FAIL: {key} = {actual_val!r}, expected {safe_value!r}")
                all_applied = False
            else:
                print(f"  OK: {key} = {actual_val!r}")

    # Cross-check against SkinTone reference
    print("\n=== CROSS-CHECK vs SkinTone Reference ===")
    all_match_ref = True
    for key, safe_value in overrides_to_apply.items():
        ref_val = get_elem_value(reference_params.get(key, ET.Element("string")))
        if ref_val != safe_value:
            print(f"  WARN: {key} = {safe_value!r} but SkinTone has {ref_val!r}")
            all_match_ref = False
    if all_match_ref:
        print("All patched values match SkinTone reference.")

    if all_applied:
        print("\nAll overrides applied successfully. Master XML is now crash-safe.")
    else:
        print("\nWARNING: Some overrides did not apply correctly!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Patch LMC 8.4 All-In-One Master XML with safe SkinTone limits",
    )
    parser.add_argument(
        "--master",
        type=Path,
        default=Path("configs/xml/LXX521_IMX682_LMC84_AllInOne_Master.xml"),
        help="Path to the All-In-One Master XML",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path("configs/xml/LXX521_IMX682_LMC84_SkinTone_Perfect.xml"),
        help="Path to the SkinTone Perfect reference XML",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("configs/xml/LXX521_IMX682_LMC84_AllInOne_Master_PATCHED.xml"),
        help="Output path for patched XML",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show plan without writing any file",
    )
    args = parser.parse_args()

    if not args.master.is_file():
        print(f"ERROR: Master XML not found: {args.master}")
        raise SystemExit(1)
    if not args.reference.is_file():
        print(f"ERROR: Reference XML not found: {args.reference}")
        raise SystemExit(1)

    patch_master(
        master_path=args.master,
        reference_path=args.reference,
        output_path=args.output,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
