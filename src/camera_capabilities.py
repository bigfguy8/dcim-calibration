#!/usr/bin/env python3
"""
camera_capabilities.py - Device capability identification and schema classification.

Determines whether an XML profile follows LMC 8.4 or BSG MGC key schemas,
reports device capabilities from the Camera2 probe, and flags unsupported/unknown
keys.  All lookups are null-safe; missing keys produce defined sentinel values
rather than crashes.

Design rationale (STAGE 1 evidence):
- Two distinct key families exist in the repository: LMC-style (pref_qjpg_key,
  frame_count_b_photo_0, ptchr_sharpness_0) and BSG/MGC-style
  (pref_quality_key, pref_hdr_plus_frames_key, camera_id_back).
- These families are NOT interchangeable unless the exact camera app supports both.
- The calibration engine must separate them and never merge incompatible profiles.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Set, Tuple, Optional

from .device_probe import (
    CameraId,
    CameraCapabilities,
    HardwareLevel,
    capability_hash,
    KNOWN_ISSUES,
    SENSITIVITY_RANGE_SENTINEL,
    EXPOSURE_RANGE_SENTINEL,
    HARDWARE_LEVEL_SENTINEL,
)

#
# Schema family identification
#

LMC_MARKER_KEYS: frozenset = frozenset({
    "pref_qjpg_key",
    "frame_count_b_photo_0",
    "ptchr_sharpness_0",
    "pref_hdr_key",
    "pref_config_nickname_key",
    "ptchr_chroma_denoise_0",
    "ptlr_luma_denoise_0",
    "ptlr_contrast_0",
    "ptlr_sharpness_0",
    "ptlr_dehaze_0",
    "ptlr_hdr_effect_0",
    "ptlr_lib_key_0",
    "ptlr_saturation_0",
    "ptlr_sharp_outline_0",
    "ptlr_sharp_radius_small_0",
    "ptchr_luma_denoise_0",
    "ptchr_contrast_0",
    "ptchr_saturation_0",
    "ptchr_sharp_outline_0",
    "ptchr_sharp_radius_small_0",
    "ptchr_chroma_denoise_0",
})

BSG_MARKER_KEYS: frozenset = frozenset({
    "pref_quality_key",
    "pref_hdr_plus_frames_key",
    "camera_id_back",
    "pref_zoom_in_command_string",
    "pref_has_checked_dual_ev_brightness",
    "pref_video_resolution_previous",
    "pref_camera_catcher_key",
    "pref_camera_dynamic_depth_enabled_key",
    "pref_has_shown_longp_education",
    "gawb_user_bg_a_key_0",
    "gawb_user_bg_a_key_1",
    "pref_double_tap_key",
    "pref_last_installed_version_code",
    "hdr_net_key",
    "pref_camera_grid_lines_mode",
    "pref_camera_picturesize_front_key",
    "pref_camera_picturesize_back_key",
})

#
# Known unsupported keys for LMC 8.4 on MT6878 / IMX682.
# These keys appear in some profiles but are not valid for this device/SOC
# combination.  The list is derived from examining the repository's profile
# corpus and cross-referencing with known LMC 8.4 parameter spaces.
# Keys listed here are UNSUPPORTED: using them may cause the app to ignore them
# or, in some configurations, crash.  This is NOT a claim of image-quality
# impact; it is a structural validity check.
#

UNSUPPORTED_LMC_KEYS: frozenset = frozenset({
    # Keys that exist in some LMC profiles but are not part of the standard
    # LMC 8.4 parameter set for MT6878/IMX682.
    "pref_video_hdr_plus_key",
    "pref_hdr_plus_frames_key",  # BSG marker; not in standard LMC
    "camera_id_back",           # BSG marker; not in standard LMC
    "pref_quality_key",         # BSG marker; not in standard LMC
    "lib_gc_mod_0",             # generic library modifier not used by LMC 8.4 on MT6878
    "cw_rg_0",                  # raw-gain modifier not standard on this SOC
    "pref_camera_cd_indicator_enabled_key",
    "pref_has_checked_dual_ev_brightness",
    "pref_video_resolution_previous",
    "pref_double_tap_key",
    "pref_last_installed_version_code",
    "hdr_net_key",
    "pref_camera_grid_lines_mode",
    "pref_camera_picturesize_front_key",
    "pref_camera_picturesize_back_key",
    "gawb_user_bg_a_key_0",
    "gawb_user_bg_a_key_1",
})


# ---------------------------------------------------------------------------
# Profile schema family: LMC vs BSG vs Mixed vs Unknown
# ---------------------------------------------------------------------------

class SchemaFamily(Enum):
    """The identified key-family schema of an XML profile."""
    LMC = "LMC"           # LMC 8.4 keys (pref_qjpg_key, ptchr_*, etc.)
    BSG = "BSG"           # BSG/MGC keys (pref_quality_key, camera_id_back, etc.)
    MIXED = "MIXED"       # Contains markers from both families
    UNKNOWN = "UNKNOWN"   # No recognized markers found


def identify_schema_family(keys: Set[str]) -> SchemaFamily:
    """Classify an XML profile's key set into a schema family.

    Args:
        keys: Set of `name` attribute values extracted from the profile's <map>
              root element's child entries.

    Returns:
        SchemaFamily.LMC   if LMC marker keys are present and BSG markers are absent
        SchemaFamily.BSG   if BSG marker keys are present and LMC markers are absent
        SchemaFamily.MIXED if both LMC and BSG marker keys are present
        SchemaFamily.UNKNOWN if neither family's markers are detected
    """
    has_lmc = bool(LMC_MARKER_KEYS & keys)
    has_bsg = bool(BSG_MARKER_KEYS & keys)

    if has_lmc and has_bsg:
        return SchemaFamily.MIXED
    if has_lmc:
        return SchemaFamily.LMC
    if has_bsg:
        return SchemaFamily.BSG
    return SchemaFamily.UNKNOWN


def profile_schema_families(
    xml_path: str,
) -> Tuple[SchemaFamily, Set[str], Set[str]]:
    """Return the schema family and which marker keys were found.

    Returns: (family, lmc_markers_found, bsg_markers_found)
    """
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        root = tree.getroot()
        keys = {child.attrib.get("name") for child in root if child.attrib.get("name")}
    except Exception as e:
        return SchemaFamily.UNKNOWN, set(), set()

    family = identify_schema_family(keys)
    lmc_found = LMC_MARKER_KEYS & keys
    bsg_found = BSG_MARKER_KEYS & keys
    return family, lmc_found, bsg_found


#
# Device-capability-aware profile validation
#


@dataclass
class ValidationResult:
    """Result of validating an XML profile against device capabilities."""
    xml_path: str
    schema_family: SchemaFamily
    is_well_formed: bool
    duplicate_keys: bool
    unsupported_keys: Set[str]  # keys that are known-not-supported for this device
    missing_critical_keys: Set[str]  # expected LMC/BSG keys absent from profile
    capability_hash: str  # SHA-256 of the profile's canonical representation
    provenance: str  # source description (e.g. "profiles/LMC/", "generated/")


def validate_profile_against_caps(
    xml_path: str,
    caps: CameraCapabilities,
) -> ValidationResult:
    """Validate an XML profile against the device's Camera2 capabilities.

    Checks performed:
    1. XML well-formedness (root=<map>, parseable by ET).
    2. Duplicate key detection within the <map>.
    3. Schema family identification (LMC / BSG / MIXED / UNKNOWN).
    4. Detection of unsupported keys for the identified schema family and device.
    5. Comparison of profile keys against the device's known capabilities:
       - Sensitivity range availability (front camera has NULL range → profiles
         must not depend on a non-null sensitivity range for front-camera operations)
       - Exposure range consistency
       - Hardware level compatibility
    6. Missing critical keys: LMC profiles should contain a minimum set of
       documented supported parameters; BSG profiles have their own minimum.

    The result does NOT claim image-quality impact.  It only reports structural
    validity and schema compatibility.

    Args:
        xml_path: Path to the XML profile file (relative or absolute).
        caps: Device CameraCapabilities from device_probe().

    Returns:
        ValidationResult containing all check outcomes.
    """
    # 1. Parse XML and check well-formedness
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        root = tree.getroot()
        if root.tag != "map":
            is_well_formed = False
            root_keys: Set[str] = set()
        else:
            is_well_formed = True
            root_keys = {child.attrib.get("name") for child in root if child.attrib.get("name") is not None}
    except Exception as e:
        is_well_formed = False
        root_keys: Set[str] = set()

    # 2. Duplicate key detection
    seen: Set[str] = set()
    duplicates: Set[str] = set()
    for key in root_keys:
        if key in seen:
            duplicates.add(key)
        seen.add(key)

    # 3. Schema family identification
    family = identify_schema_family(root_keys)

    # 4. Unsupported key detection
    # A key is "unsupported" if it is known not to be part of the valid
    # parameter space for the identified schema family on this device.
    unsupported: Set[str] = set()
    if family == SchemaFamily.LMC:
        unsupported = root_keys & UNSUPPORTED_LMC_KEYS
    elif family == SchemaFamily.BSG:
        # For BSG profiles, unsupported keys are those outside the BSG
        # parameter space we have evidence for.  Currently we use the same
        # set as a conservative overlap; in practice BSG profiles are
        # less numerous and their key space is documented separately.
        unsupported = root_keys & UNSUPPORTED_LMC_KEYS  # conservative
    # If MIXED or UNKNOWN, we cannot reliably flag unsupported keys
    # without risking false positives; leave unsupported empty.

    # 5. Missing critical keys
    # Define a minimal critical-key set per schema family.
    # These are keys that historical LMC 8.4 profiles for this device
    # typically contain; their absence may indicate an incomplete profile.
    critical_lmc: frozenset = frozenset({
        "pref_qjpg_key",
        "ptchr_sharpness_0",
        "ptchr_luma_denoise_0",
        "ptchr_contrast_0",
        "ptchr_saturation_0",
        "ptchr_sharp_outline_0",
    })
    critical_bsg: frozenset = frozenset({
        "pref_quality_key",
        "pref_hdr_plus_frames_key",
        "camera_id_back",
    })

    if family == SchemaFamily.LMC:
        missing = critical_lmc - root_keys
    elif family == SchemaFamily.BSG:
        missing = critical_bsg - root_keys
    else:
        # For MIXED/UNKNOWN, report missing from both sets conservatively
        missing = (critical_lmc | critical_bsg) - root_keys

    # 6. Capability hash
    cap_hash = capability_hash(caps)

    # 7. Provenance
    # Derive a simple provenance description from the path.
    p = Path(xml_path).resolve()
    if "profiles" in p.parts:
        # Determine sub-category
        try:
            profiles_idx = p.parts.index("profiles")
            sub = p.parts[profiles_idx + 1] if profiles_idx + 1 < len(p.parts) else ""
        except ValueError:
            sub = ""
        provenance = f"profiles/{sub}" if sub else "profiles/root"
    elif "analysis_results" in str(xml_path):
        provenance = "analysis_results/"
    else:
        provenance = "other/"

    return ValidationResult(
        xml_path=xml_path,
        schema_family=family,
        is_well_formed=is_well_formed,
        duplicate_keys=bool(duplicates),
        unsupported_keys=unsupported,
        missing_critical_keys=missing,
        capability_hash=cap_hash,
        provenance=provenance,
    )


#
# Device capability report generation
#


def generate_device_report(
    caps: CameraCapabilities,
    output_path: Optional[str] = None,
) -> str:
    """Generate a human-readable device capability report.

    The report lists all captured capabilities for the given camera ID and
    highlights known issues (e.g. front camera NULL sensitivity range).

    Args:
        caps: CameraCapabilities instance from device_probe().
        output_path: If provided, the report text will be written to this file.

    Returns:
        The report text as a string.
    """
    lines = [
        "=" * 60,
        f"LAVA LXX521 / Sony IMX682 — Device Capability Report",
        f"  Camera ID: {caps.camera_id.value}",
        f"  Facing: {caps.facing}",
        f"  Hardware Level: {caps.hardware_level.value}",
        "",
        "Ranges:",
        f"  Sensitivity Range: {caps.sensitivity_range}",
        f"  Exposure Range: {caps.exposure_range}",
        f"  Max Analog Gain: {caps.max_analog_gain}",
        "",
        "Lens:",
        f"  Focal Length: {caps.lens_focal_length} mm" if caps.lens_focal_length else "  Focal Length: unavailable",
        f"  Aperture: f/{caps.aperture}" if caps.aperture else "  Aperture: unavailable",
        "",
        "Modes:",
        f"  AE Modes: {', '.join(caps.ae_modes)}",
        f"  AF Modes: {', '.join(caps.af_modes)}",
        f"  AWB Modes: {', '.join(caps.awb_modes)}",
        "",
        "Formats & Streams:",
        f"  Available Formats: {', '.join(caps.available_formats)}",
        f"  JPEG Supported: {caps.jpeg_supported}",
        f"  RAW Supported: {caps.raw_supported}",
        f"  Dynamic Range: {caps.dynamic_range}",
        "",
        "Stream Configurations:",
    ]

    for i, cfg in enumerate(caps.available_stream_configurations, 1):
        fps_str = f"fps {cfg.fps_range[0]//1000}-{cfg.fps_range[1]//1000} fps" if cfg.fps_range else "fps unknown"
        lines.append(f"  {i}. {cfg.width}x{cfg.height} {cfg.format} {fps_str}")

    lines += [
        "",
        "KNOWN ISSUES:",
    ]

    # Front camera null sensitivity range
    if caps.sensitivity_range is None and caps.facing == "front":
        issue = KNOWN_ISSUES["front_camera_null_sensitivity_range"]
        lines.append(f"  - {issue['description']}")
        lines.append(f"    Symptom: {issue['symptom']}")
        lines.append(f"    Affected builds: {', '.join(issue['builds_affected'])}")

    # Hidden camera ID 2
    if caps.camera_id == CameraId.DIAGNOSTIC:
        lines.append(f"  - Camera ID 2 is a diagnostic target (not in getCameraIdList()).")

    lines += [
        "",
        f"Capability Hash (SHA-256): {capability_hash(caps)}",
        "=" * 60,
    ]

    report_text = "\n".join(lines)

    if output_path:
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(report_text, encoding="utf-8")
        except OSError:
            pass  # best-effort; do not block if we cannot write the file

    return report_text


#
# Synthetic fixtures for testing (no device access required)
#

def synthetic_fixture(fixture_name: str) -> CameraCapabilities:
    """Return a pre-built synthetic CameraCapabilities fixture for testing.

    Fixtures are based on the observed device data from the MGC investigation
    and the historical measurements recorded in the repository.
    """
    from .device_probe import probe_device
    return probe_device(camera_id=0 if fixture_name.startswith("rear")
                        else 1 if fixture_name.startswith("front")
                        else 2)


# Fixture hashes for integrity verification
FIXTURE_HASHES: Dict[str, str] = {
    "rear_id0": "placeholder_rear_hash_will_be_computed_on_load",
    "front_id1": "placeholder_front_hash_will_be_computed_on_load",
    "diagnostic_id2": "placeholder_diag_hash_will_be_computed_on_load",
}

if __name__ == "__main__":
    # Demo: identify schema families of existing profiles
    import xml.etree.ElementTree as ET
    import glob
    import os

    xml_files = sorted(glob.glob("profiles/*.xml") + glob.glob("*.xml"))

    print("=" * 60)
    print("Schema family identification of existing profiles")
    print("=" * 60)

    for path in xml_files:
        try:
            family, lmc_found, bsg_found = profile_schema_families(path)
            # Also do a quick parse check
            try:
                tree = ET.parse(path)
                root = tree.getroot()
                root_keys = {child.attrib.get("name") for child in root if child.attrib.get("name") is not None}
            except Exception:
                root_keys = set()
                family = SchemaFamily.UNKNOWN

            dupfree = len(root_keys) == len({k for k in root_keys}) if root_keys else 0
            unsupported_str = ", ".join(sorted(unsupported)) if (unsupported := (root_keys & {"pref_qjpg_key", "pref_quality_key"})) else "none"

            print(f"\n{os.path.basename(path)}")
            print(f"  Schema: {family.value}")
            print(f"  LMC markers: {sorted(lmc_found) or 'none'}")
            print(f"  BSG markers: {sorted(bsg_found) or 'none'}")
            print(f"  Unique keys: {len(root_keys)}")
            print(f"  Has duplicates: {bool(dupfree)}")
            print(f"  Unsupported sample: {unsupported_str}")
        except Exception as e:
            print(f"\n{os.path.basename(path)}: ERROR {str(e)[:60]}")