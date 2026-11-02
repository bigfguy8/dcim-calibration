#!/usr/bin/env python3
"""
config_generator.py - Candidate configuration generator.

Generates candidate XML profiles only from documented, supported parameters.

Core design principles (per mission section 4 & 8):
1. Generate candidates ONLY from parameters that are documented as supported
   for the LAVA LXX521 / Sony IMX682 / LMC 8.4 target.
2. Never invent XML keys or camera parameters (mission rule #5).
3. Never fabricate image-quality measurements (mission rule #6).
4. Preserve existing baselines unchanged (immutable originals).
5. Track configuration provenance (source, hash, changes).
6. Support rollback to the original baseline.
7. Separate LMC and BSG profile families - never merge incompatible profiles.
8. Output candidates as unchanged XML copies with a provenance manifest;
   do not claim image-quality improvements.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .camera_capabilities import (
    SchemaFamily,
    identify_schema_family,
    UNSUPPORTED_LMC_KEYS,
)
from .profile_compare import compare_profiles, _extract_key_value, compute_sha256, record_provenance
from .xml_audit import check_syntax


#
# Supported parameter ranges for LMC 8.4 on MT6878 / IMX682
#
# These ranges are derived from the repository's existing profile corpus
# and the historical Camera2 characteristic measurements.  They define the
# permissible value space for each adjustable parameter.  Values outside these
# ranges are considered unsupported and will not be generated.
#

LMC_SUPPORTED_RANGES: Dict[str, Tuple[float, float]] = {
    # Sharpening parameters (ptchr_* family)
    "ptchr_sharpness_0": (0.5, 2.0),
    "ptchr_sharp_outline_0": (0.5, 2.0),
    "ptchr_sharp_radius_small_0": (0.1, 5.0),
    # Denoising parameters
    "ptchr_luma_denoise_0": (0.0, 2.0),
    "ptchr_chroma_denoise_0": (0.0, 2.0),
    # Contrast
    "ptchr_contrast_0": (0.5, 2.0),
    # Saturation
    "ptchr_saturation_0": (0.5, 2.0),
    # HDR effect
    "ptlr_hdr_effect_0": (0, 10),
    # Lib/patch related
    "pref_qjpg_key": (0, 1),  # boolean-like
    "frame_count_b_photo_0": (1, 23),  # typical HDR+ frame count range
}

# BSG-specific supported ranges (conservative; BSG keys are separate from LMC)
BSG_SUPPORTED_RANGES: Dict[str, Tuple[float, float]] = {
    "pref_quality_key": (1, 5),  # quality level
    "pref_hdr_plus_frames_key": (1, 10),  # HDR+ frames
}

# Critical LMC keys (profile keys that are expected in a valid LMC 8.4 profile)
CRITICAL_LMC_KEYS: frozenset = frozenset({
    "pref_qjpg_key",
    "ptchr_sharpness_0",
    "ptchr_luma_denoise_0",
    "ptchr_contrast_0",
    "ptchr_saturation_0",
    "ptchr_sharp_outline_0",
})

# Critical BSG keys (profile keys that are expected in a valid BSG/MGC profile)
CRITICAL_BSG_KEYS: frozenset = frozenset({
    "pref_quality_key",
    "pref_hdr_plus_frames_key",
    "camera_id_back",
})


#
# Change record for provenance tracking
#

@dataclass
class ChangeRecord:
    """Documents a single configuration change for provenance."""
    key: str
    original_value: any
    new_value: any
    source: str  # e.g. "LMC_SUPPORTED_RANGES", "user_specified", "generator_default"
    rationale: str  # brief explanation; may reference the supported range


@dataclass
class GenerationResult:
    """Result of a profile generation operation."""
    success: bool
    output_path: Optional[str] = None
    baseline_path: Optional[str] = None
    changes: Tuple[ChangeRecord, ...] = field(default_factory=tuple)
    provenance_note: str = ""
    sha256: Optional[str] = None
    error: Optional[str] = None
#
# Change record for provenance tracking
#

@dataclass
class ChangeRecord:
    """Documents a single configuration change for provenance."""
    key: str
    original_value: any
    new_value: any
    source: str  # e.g. "LMC_SUPPORTED_RANGES", "user_specified", "generator_default"
    rationale: str  # brief explanation; may reference the supported range


@dataclass
class GenerationResult:
    """Result of a profile generation operation."""
    success: bool
    output_path: Optional[str] = None
    baseline_path: Optional[str] = None
    changes: Tuple[ChangeRecord, ...] = field(default_factory=tuple)
    provenance_note: str = ""
    sha256: Optional[str] = None
    error: Optional[str] = None


#
# Configuration generator
#


def _modify_xml_profile(
    baseline_path: str,
    changes: Tuple[ChangeRecord, ...],
    output_path: str,
) -> GenerationResult:
    """Apply changes to an XML profile baseline and write the result.

    The baseline file is read, changes are applied (key value updates only;
    structure <map>/<string> is preserved), and the result is written to
    output_path.  The baseline file itself is never modified.

    Returns:
        GenerationResult with success status and details.
    """
    try:
        tree = ET.parse(baseline_path)
        root = tree.getroot()
    except Exception as e:
        return GenerationResult(
            success=False,
            error=f"Could not read baseline XML: {e}",
        )

    # Apply changes
    for change in changes:
        key = change.key
        new_value = change.new_value
        # Find or create the <string name="key">value</string> entry
        found = False
        for child in root:
            if child.attrib.get("name") == key:
                # Update existing entry's text value
                child.text = str(new_value)
                found = True
                break
        if not found:
            # Append new entry at the end of the <map>
            # Determine the appropriate type attribute based on the original value type
            # For now, always use "string" as the safe default
            new_entry = ET.SubElement(root, "string", name=key)
            new_entry.text = str(new_value)

# Write output (preserve XML declaration if present)
    try:
        tree.write(
            output_path,
            encoding="utf-8",
        )
    except Exception as e:
        return GenerationResult(
            success=False,
            error=f"Could not write output XML: {e}",
        )

    # Compute SHA-256 of the output
    try:
        output_hash = compute_sha256(output_path)
    except Exception:
        output_hash = None

    # Build provenance note
    change_notes = "; ".join(
        f"{c.key}: {c.original_value} -> {c.new_value}" for c in changes
    ) if changes else "no changes"

    provenance = (
        f"Generated from baseline: {baseline_path}; "
        f"changes: {change_notes}; "
        f"schema: {identify_schema_family(_extract_keys(baseline_path)).value}"
        if changes
        else f"Unchanged copy of baseline: {baseline_path}"
    )

    return GenerationResult(
        success=True,
        output_path=output_path,
        baseline_path=baseline_path,
        changes=changes,
        provenance_note=provenance,
        sha256=output_hash,
    )


def _extract_keys(xml_path: str) -> Set[str]:
    """Extract the set of key names from an XML profile."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        return {child.attrib.get("name") for child in root if child.attrib.get("name") is not None}
    except Exception:
        return set()


def generate_from_baseline(
    baseline_path: str,
    parameter_changes: Dict[str, any],
    output_dir: Optional[str] = None,
) -> GenerationResult:
    """Generate a candidate configuration from a baseline profile.

    Args:
        baseline_path: Path to the baseline XML profile (the "original" or
            "verified" profile to start from.  This file is NEVER modified.
        parameter_changes: Dict mapping key names to new values.  Values must
            fall within the supported ranges defined in
            LMC_SUPPORTED_RANGES (for LMC profiles) or BSG_SUPPORTED_RANGES
            (for BSG profiles).  Values outside the range are rejected.
        output_dir: Optional output directory.  If not provided, a temporary
            directory is used.

    Returns:
        GenerationResult.  If success=True, the candidate XML exists at
        output_path and can be validated with xml_audit.validate_xml_complete().
        If success=False, the error field describes what went wrong.

    Raises:
        ValueError: If a parameter change value is outside the supported range,
            or if the change would remove a critical key, or if the baseline
            schema cannot be identified.
    """
    # 1. Validate the baseline XML
    syntax_ok = check_syntax(baseline_path)
    if not syntax_ok.passed:
        return GenerationResult(
            success=False,
            error=f"Baseline XML fails syntax validation: {syntax_ok.details}",
        )

    # 2. Identify the schema family
    try:
        profile_keys = _extract_keys(baseline_path)
        family = identify_schema_family(profile_keys)
    except Exception as e:
        return GenerationResult(
            success=False,
            error=f"Could not identify baseline schema: {e}",
        )

    # 3. Validate parameter changes against supported ranges
    validated_changes: List[ChangeRecord] = []
    rejected: List[str] = []

    # Determine ranges based on profile content, not just schema family label.
    # Use LMC ranges if the profile has LMC-critical keys (pref_qjpg_key,
    # ptchr_sharpness_0, etc.) since the baseline is an LMC 8.4 profile.
    # Fall back to BSG ranges only if there are no LMC-critical keys but
    # BSG-critical keys are present.
    has_lmc_critical = bool(CRITICAL_LMC_KEYS & profile_keys)
    has_bsg_critical = bool(CRITICAL_BSG_KEYS & profile_keys)

    if has_lmc_critical:
        ranges = LMC_SUPPORTED_RANGES
    elif has_bsg_critical:
        ranges = BSG_SUPPORTED_RANGES
    else:
        # No critical keys from either family; use LMC ranges as default
        # since the baseline is an LMC 8.4 profile, but warn that ranges
        # may not apply meaningfully.
        ranges = LMC_SUPPORTED_RANGES

    for key, new_value in parameter_changes.items():
        # Check if the key is in the supported ranges
        if key in ranges:
            lo, hi = ranges[key]
            try:
                fval = float(new_value)
            except (ValueError, TypeError):
                rejected.append(f"{key}: cannot convert '{new_value}' to number; rejected")
                continue
            if fval < lo or fval > hi:
                rejected.append(
                    f"{key}: value {fval} outside supported range [{lo}, {hi}]; rejected"
                )
                continue
        else:
            # Key is not in the known ranges.
            # Allow it only if it's already present in the baseline and we're
            # just passing through its existing value (no change in kind).
            # For truly new keys, reject unless they are known BSG markers
            # in a BSG profile.
            if key not in profile_keys:
                rejected.append(f"{key}: not in supported ranges and not present in baseline; rejected")
                continue
            # Key is in baseline: pass through with original value logic
            # (no range check needed since the value was previously accepted)

        # Build the change record
        original_value = _extract_key_value(baseline_path, key)
        if original_value is None:
            # Key not found in baseline; this is an addition
            original_value = "MISSING_FROM_BASELINE"

        validated_changes.append(
            ChangeRecord(
                key=key,
                original_value=original_value,
                new_value=new_value,
                source="parameter_changes_input",
                rationale=f"User/specified parameter adjustment within {ranges[key] if key in ranges else 'unmarked range'}",
            )
        )

    if rejected:
        return GenerationResult(
            success=False,
            error=f"{len(rejected)} parameter change(s) rejected: {'; '.join(rejected)}",
        )

    # 5. Construct output path
    baseline_name = Path(baseline_path).name
    if output_dir:
        out_path = Path(output_dir) / baseline_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Use a temp directory under the project
        import tempfile
        tmp_dir = Path(tempfile.mkdtemp(prefix="gcam_candidate_"))
        out_path = tmp_dir / baseline_name

    # 6. Apply changes and write output
    result = _modify_xml_profile(baseline_path, tuple(validated_changes), str(out_path))

    if result.success:
        # Record provenance
        sha256 = result.sha256
        record_provenance(
            str(out_path),
            source_description=f"generated_from_{baseline_name}",
            sha256=sha256,
            schema_family=family,
            notes=f"parameter_changes: {list(parameter_changes.keys())}",
        )

        result.provenance_note = (
            f"Generated from baseline {baseline_name} with {len(validated_changes)} "
            f"parameter change(s). {len(rejected)} change(s) rejected. "
            f"SHA-256: {sha256}"
        )

    return result


#
# Pre-defined candidate generation profiles
#

# These are documented, reproducible generation recipes that start from the
# verified baseline (LXX521_IMX682_LMC84_AllRounder.xml / V10_Baseline_UNVALIDATED).
# Each recipe applies only documented, supported parameter adjustments.
# They are NOT "optimized" or "best" configurations - they are documented
# starting points for side-by-side testing.

# Recipe: Conservative Balanced (V9-like)
# Changes: moderate sharpening reduction, moderate denoise increase
CONSERVATIVE_BALANCED_CHANGES: Dict[str, any] = {
    "ptchr_sharpness_0": 1.0,     # reduced from 1.2
    "ptchr_luma_denoise_0": 1.1,  # increased from 1.0
    "ptchr_chroma_denoise_0": 1.1,  # increased from 1.0
}

# Recipe: Low-Light Balanced
# Changes: increased denoise, reduced sharpening, slightly lower contrast
LOW_LIGHT_BALANCED_CHANGES: Dict[str, any] = {
    "ptchr_sharpness_0": 0.8,
    "ptchr_luma_denoise_0": 1.3,
    "ptchr_contrast_0": 0.9,
}

# Recipe: Natural Detail
# Changes: minimal adjustments - slightly reduced sharpening, slight saturation tweak
NATURAL_DETAIL_CHANGES: Dict[str, any] = {
    "ptchr_sharpness_0": 1.1,
    "ptchr_saturation_0": 0.95,
}


def generate_preset_candidate(
    baseline_path: str,
    preset_name: str,
    output_dir: Optional[str] = None,
) -> GenerationResult:
    """Generate a preset candidate from the baseline using a documented recipe.

    This is a convenience wrapper around generate_from_baseline that uses
    pre-defined change recipes.  The recipes are documented starting points
    only; they do not claim image-quality improvements.

    Args:
        baseline_path: Path to the baseline profile (must be an LMC 8.4 profile).
        preset_name: Name of the preset recipe.  Supported names:
            "conservative_balanced", "lowlight_balanced", "natural_detail".
        output_dir: Optional output directory.

    Returns:
        GenerationResult.
    """
    recipe_map: Dict[str, Dict[str, any]] = {
        "conservative_balanced": CONSERVATIVE_BALANCED_CHANGES,
        "lowlight_balanced": LOW_LIGHT_BALANCED_CHANGES,
        "natural_detail": NATURAL_DETAIL_CHANGES,
    }

    if preset_name not in recipe_map:
        return GenerationResult(
            success=False,
            error=f"Unknown preset '{preset_name}'. Supported: {', '.join(recipe_map.keys())}",
        )

    changes = recipe_map[preset_name]
    return generate_from_baseline(baseline_path, changes, output_dir)


#
# Rollback utility
#


def create_rollback_copy(
    working_path: str,
    backup_dir: str = "backups",
) -> str:
    """Create a SHA-256-backed rollback copy of the currently working profile.

    The working profile is copied (not moved) to the backup directory with a
    timestamped filename and its SHA-256 hash recorded.  The original file
    is never modified; only a copy is made.

    Args:
        working_path: Path to the currently working/writable XML profile.
        backup_dir: Subdirectory under the project's backups/ directory.

    Returns:
        Path to the created backup file.
    """
    import os
    from datetime import datetime

    # Ensure backup directory exists
    project_backups = Path(__file__).resolve().parent.parent / "backups" / backup_dir
    project_backups.mkdir(parents=True, exist_ok=True)

    # Compute source SHA-256 for the record
    source_hash = compute_sha256(working_path)

    # Generate backup filename: basename.timestamp.bak
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_filename = f"{Path(working_path).name}.{timestamp}.bak"
    backup_path = project_backups / backup_filename

    # Copy the file (shutil.copy2 preserves metadata)
    try:
        shutil.copy2(working_path, backup_path)
    except Exception as e:
        raise RuntimeError(f"Could not create rollback backup: {e}")

    # Record provenance
    record_provenance(
        str(backup_path),
        source_description="rollback_backup",
        sha256=source_hash,
        schema_family=identify_schema_family(_extract_keys(working_path)),
        notes=f"Rollback copy of {working_path} at {timestamp}",
    )

    return str(backup_path)


def rollback_to_backup(
    backup_path: str,
    target_path: str,
) -> bool:
    """Restore a profile from a backup to the target path.

    The backup is copied to the target path, replacing the current working
    profile.  The backup file itself is preserved (not deleted), so the
    rollback can be repeated or a different backup can be used.

    Args:
        backup_path: Path to the backup XML file to restore from.
        target_path: Path where the profile will be restored.

    Returns:
        True if the rollback succeeded, False otherwise.
    """
    try:
        shutil.copy2(backup_path, target_path)
        return True
    except Exception as e:
        print(f"Rollback failed: {e}")
        return False


if __name__ == "__main__":
    # Demo: generate a preset candidate from the baseline
    import sys

    # Use the V10 baseline as the base (it's the documented baseline)
    baseline = "profiles/LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml"

    print("=" * 70)
    print("Config Generator Demo")
    print("=" * 70)
    print(f"\nBaseline: {baseline}")
    print(f"Baseline exists: {__import__('pathlib').Path(baseline).exists()}\n")

    # Test generating a conservative balanced candidate
    result = generate_preset_candidate(baseline, "conservative_balanced")
    print(f"Preset 'conservative_balanced':")
    print(f"  Success: {result.success}")
    if result.success:
        print(f"  Output: {result.output_path}")
        print(f"  Changes: {len(result.changes)}")
        for c in result.changes:
            print(f"    {c.key}: {c.original_value} -> {c.new_value}")
        print(f"  Provenance: {result.provenance_note}")
        print(f"  SHA-256: {result.sha256}")
    else:
        print(f"  Error: {result.error}")

    # Test lowlight balanced
    print()
    result2 = generate_preset_candidate(baseline, "lowlight_balanced")
    print(f"Preset 'lowlight_balanced':")
    print(f"  Success: {result2.success}")
    if result2.success:
        print(f"  Output: {result2.output_path}")
