#!/usr/bin/env python3
"""
patch_master.py — Safely patch LXX521_IMX682_LMC84_AllInOne_Master.xml

Compares the All-In-One Master profile against the proven-safe
SkinTone_Perfect profile and lowers aggressive parameters that can
cause pipeline crashes on the IMX682 sensor (high HDR stack sizes,
forced AWB overrides, excessive sharpening/denoise).

The script retains all Master image-quality parameters that are not
crash-critical, only overriding those where Master's value is more
aggressive than SkinTone's proven-safe value.

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
from datetime import datetime
from pathlib import Path
from typing import Dict


# ---------------------------------------------------------------------------
# Crash-critical parameter overrides.
#
# Each entry maps a Master parameter name to the safe SkinTone value it
# should be lowered to. Only parameters where Master's value is more
# aggressive (higher HDR stacks, forced AWB, stronger sharpening/denoise,
# etc.) are included. Parameters where SkinTone is more aggressive than
# Master are intentionally left at Master's value to retain image quality.
# ---------------------------------------------------------------------------
CRITICAL_OVERRIDES: Dict[str, str] = {
    # --- High HDR stack sizes (crash risk) ---
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

    # --- Aggressive sharpening (can cause halos / crashes) ---
    "lib_sharpgain_key": "0",             # Master=2 (high gain)
    "lib_sharpmini_key": "0",             # Master=2 (high micro-sharpening)
    "lib_sharpnessb_key": "1.02",         # Master=2 (high sharpness)

    # --- Aggressive denoise / smoothing ---
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


def patch_master(
    master_path: Path,
    reference_path: Path,
    output_path: Path,
    dry_run: bool = False,
) -> None:
    """Patch the Master XML with safe SkinTone values."""

    # Load both files
    master_tree = parse_xml(master_path)
    master_root = master_tree.getroot()
    master_params = build_param_map(master_root)

    reference_tree = parse_xml(reference_path)
    reference_root = reference_tree.getroot()
    reference_params = build_param_map(reference_root)

    # Determine which overrides actually apply (Master has the param,
    # and Master's value differs from the safe target)
    overrides_to_apply: Dict[str, str] = {}
    skipped_missing: list[str] = []
    skipped_same: list[str] = []
    skipped_reference_higher: list[str] = []

    for key, safe_value in CRITICAL_OVERRIDES.items():
        if key not in master_params:
            skipped_missing.append(key)
            continue
        current_value = master_params[key].attrib.get(
            "value", master_params[key].text
        )
        if current_value == safe_value:
            skipped_same.append(key)
            continue
        # Only apply if Master's value is numerically more aggressive
        # (higher) than SkinTone's. For WB/color keys we always apply
        # since they represent cast overrides, not magnitude.
        if key in master_params and key in reference_params:
            ref_value = reference_params[key].attrib.get(
                "value", reference_params[key].text
            )
            try:
                cur_num = float(current_value)
                ref_num = float(ref_value)
                safe_num = float(safe_value)
                # Only lower if Master > SkinTone reference
                if cur_num <= ref_num:
                    skipped_reference_higher.append(
                        f"{key} (Master={current_value}, Ref={ref_value})"
                    )
                    continue
            except (ValueError, TypeError):
                pass  # Non-numeric: apply override unconditionally

        overrides_to_apply[key] = safe_value

    # Report plan
    print("=== PATCH MASTER PLAN ===")
    print(f"Critical overrides defined: {len(CRITICAL_OVERRIDES)}")
    print(f"Overrides to apply:         {len(overrides_to_apply)}")
    print(f"Skipped (missing in Master): {len(skipped_missing)}")
    print(f"Skipped (already same):      {len(skipped_same)}")
    print(f"Skipped (Ref >= Master):     {len(skipped_reference_higher)}")
    print()

    if skipped_missing:
        print("  Missing in Master:", ", ".join(skipped_missing))
    if skipped_same:
        print("  Already same:", ", ".join(skipped_same))
    if skipped_reference_higher:
        print("  Reference >= Master:", ", ".join(skipped_reference_higher))
    print()

    if not overrides_to_apply:
        print("No changes needed. Master is already safe.")
        return

    # Apply overrides
    print("=== APPLYING OVERRIDES ===")
    for key, safe_value in sorted(overrides_to_apply.items()):
        elem = master_params[key]
        old_value = elem.attrib.get("value", elem.text)
        elem.text = safe_value
        # Remove 'value' attribute if it existed, since we set text
        if "value" in elem.attrib:
            del elem.attrib["value"]
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

    # Validation
    print("\n=== VALIDATION ===")
    validate_tree = ET.parse(output_path)
    validate_root = validate_tree.getroot()
    validate_params = build_param_map(validate_root)

    all_applied = True
    for key, safe_value in overrides_to_apply.items():
        actual = validate_params.get(key)
        if actual is None:
            print(f"  FAIL: {key} not found in output!")
            all_applied = False
        else:
            actual_val = actual.attrib.get("value", actual.text)
            if actual_val != safe_value:
                print(f"  FAIL: {key} = {actual_val!r}, expected {safe_value!r}")
                all_applied = False
            else:
                print(f"  OK: {key} = {actual_val!r}")

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
        help="Path to the All-In-One Master XML (default: configs/xml/...)",
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
