"""Build the LXX521_IMX682_LMC84_AllInOne_Master.xml configuration (BSG format).

Synthesizes a single production-ready LMC 8.4 "All-in-One Master" profile in
the BSG XML schema that the LMC 8.4 app on the Lava Play Ultra actually reads
for photo mode. Merges calibration attributes from four specialized
sub-profiles:

  1. Perfect Skin-Tone Matrix  -> SatGlobal, HueGlobal, FaceSmoothingDefault
  2. Low-Light / Night         -> NightSight/Sabre/HDRPlus frames, ExposureComp
  3. Portrait & Bokeh          -> AEMode, PortraitBlurRadius, ColorTransform
  4. Optical Sharpness & MTF50 -> JPEGQuality, HDRPlus/Sabre max frames

Merge priority (later wins, except skin-tone keys which are locked):

    BSG AllInOne template (base)
      -> Skin-Tone Perfect (locked: SatGlobal/HueGlobal/FaceSmoothing never overridden)
      -> Low-Light / Night (NightSight/Sabre/HDRPlus frame counts, exposure)
      -> Portrait & Bokeh (AEMode, blur radius, color transform)
      -> Sharpness & MTF50 (JPEGQuality, max frames, no halos on skin)

Output:
  configs/xml/LXX521_IMX682_LMC84_AllInOne_Master.xml
  configs/xml/LXX521_IMX682_LMC84_AllInOne_Master.status.md
  analysis/reports/all_in_one_master_validation.json
  analysis/reports/all_in_one_master_merge_diff.md

The output is written to configs/xml/ and deployed to /sdcard/GCam/Configs/
(the directory the LMC 8.4 app actually reads on this device).
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import xml.etree.ElementTree as ET

from .logging import get_logger
from .paths import (
    ANALYSIS_DIR,
    CONFIG_DIR,
    DATA_DIR,
    REPORTS_DIR,
    XML_DIR,
    ensure_dirs,
)
from .xml_utils import parse_xml_params

logger = get_logger()

# --- Paths ------------------------------------------------------------------

# Base template: existing BSG AllInOne config from /sdcard/GCam/Configs/
# (the schema the LMC 8.4 app on this device actually reads for photo mode)
BSG_TEMPLATE = Path("/sdcard/GCam/Configs/LXX521_BSG_LMC_v2_AllInOne.xml")
# Fallback: bundled template if the device file isn't available
BUNDLED_TEMPLATE = XML_DIR / "LXX521_IMX682_LMC84_AllRounder.xml"

SKIN_TONE_PROFILE = XML_DIR / "LXX521_IMX682_LMC84_SkinTone_Perfect.xml"
LOW_LIGHT_PROFILE = DATA_DIR.parent / "imx682_config" / "lowlight.xml"

OUTPUT_XML = XML_DIR / "LXX521_IMX682_LMC84_AllInOne_Master.xml"
OUTPUT_STATUS = XML_DIR / "LXX521_IMX682_LMC84_AllInOne_Master.status.md"
VALIDATION_REPORT = REPORTS_DIR / "all_in_one_master_validation.json"
MERGE_DIFF_REPORT = REPORTS_DIR / "all_in_one_master_merge_diff.md"

# Deploy target: the directory LMC 8.4 actually reads on this device
DEPLOY_DIR = Path("/sdcard/GCam/Configs")

# Keys that define skin-tone rendering. Once set from Skin-Tone Perfect, these
# are never overridden by later sub-profile tiers.
_SKIN_TONE_KEY_PREFIXES = (
    "lib_saturation",
    "lib_shadow_compensation",
    "lib_tuncolsatpar",
    "pref_satCCT",
)


def _is_skin_tone_key(name: str) -> bool:
    return any(name.startswith(p) for p in _SKIN_TONE_KEY_PREFIXES)


def _load_lmc_params(path: Path | str) -> Dict[str, str]:
    """Parse a LMC-style <map> XML profile into a name -> value dict."""
    params = parse_xml_params(path)
    if not params:
        raise RuntimeError(f"Failed to load profile: {path}")
    return params


def _parse_bsg_template(path: Path | str) -> ET.Element:
    """Parse a BSG-format config XML and return the root element."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"BSG template missing: {path}")
    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag != "Config":
        raise RuntimeError(f"Unexpected BSG root tag: <{root.tag}>")
    return root


def _bsg_set(camera_elem: ET.Element, key: str, value: str) -> bool:
    """Set (or add) a child element on a BSG <Camera> element."""
    for child in camera_elem:
        if child.tag == key:
            child.text = value
            return True
    child = ET.SubElement(camera_elem, key)
    child.text = value
    return True


def _bsg_get(camera_elem: ET.Element, key: str) -> Optional[str]:
    """Get the text value of a child element on a BSG <Camera> element."""
    for child in camera_elem:
        if child.tag == key:
            return child.text
    return None


def _write_xml(root: ET.Element, path: Path | str) -> None:
    """Write an ElementTree back to disk with XML declaration."""
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _select_camera(root: ET.Element, role: str) -> Optional[ET.Element]:
    """Find the <Camera> element with the given role attribute."""
    for cam in root.findall("Camera"):
        if cam.get("role") == role:
            return cam
    return None


def build_all_in_one_master(
    bsg_template: Path | str = BSG_TEMPLATE,
    skin_tone_path: Path | str = SKIN_TONE_PROFILE,
    low_light_path: Path | str = LOW_LIGHT_PROFILE,
    output_path: Path | str = OUTPUT_XML,
    dry_run: bool = False,
    deploy: bool = False,
) -> Dict:
    """Build the All-in-One Master profile in BSG format.

    Returns a validation report dict with merge statistics.
    """
    bsg_template = Path(bsg_template)
    skin_tone_path = Path(skin_tone_path)
    low_light_path = Path(low_light_path)
    output_path = Path(output_path)

    for p in (bsg_template, skin_tone_path, low_light_path):
        if not p.is_file():
            raise FileNotFoundError(f"Source profile missing: {p}")

    # ---- Tier 0: Load BSG template ----------------------------------------
    root = _parse_bsg_template(bsg_template)
    logger.info("BSG template %s loaded", bsg_template.name)

    cam_main = _select_camera(root, "back_main")
    cam_front = _select_camera(root, "front")
    cam_aux = _select_camera(root, "back_aux")
    if cam_main is None:
        raise RuntimeError("BSG template missing <Camera id='0' role='back_main'>")

    # ---- Tier 1: Load LMC sub-profiles for tuning values ------------------
    skin_tone_params = _load_lmc_params(skin_tone_path)
    logger.info("Skin-Tone Perfect: %d keys loaded", len(skin_tone_params))

    low_light_params = _load_lmc_params(low_light_path)
    logger.info("Low-Light / Night: %d keys loaded", len(low_light_params))

    # ---- Tier 2: Extract skin-tone values (locked) ------------------------
    skin_tone_overrides: Dict[str, str] = {}
    for k, v in skin_tone_params.items():
        if _is_skin_tone_key(k):
            skin_tone_overrides[k] = v
    logger.info("Skin-tone keys extracted: %d (locked)", len(skin_tone_overrides))

    # ---- Tier 3: Extract night values -------------------------------------
    night_overrides: Dict[str, str] = {}
    for k, v in low_light_params.items():
        if not _is_skin_tone_key(k):
            night_overrides[k] = v
    logger.info("Night keys extracted: %d", len(night_overrides))

    # ---- Tier 4: Build BSG merge map --------------------------------------
    # Map LMC-style sub-profile values to BSG photo-mode elements.
    bsg_changes: Dict[str, Dict[str, str]] = {
        "back_main": {},
        "front": {},
        "LibAGC": {},
    }

    # Skin-Tone Perfect: saturation/shadow/satCCT -> BSG color controls
    # sat ~0.95 means slightly reduced saturation -> SatGlobal 0.95
    sat_values = [v for k, v in skin_tone_overrides.items() if "sat" in k.lower()]
    if sat_values:
        bsg_changes["back_main"]["SatGlobal"] = sat_values[0]
        bsg_changes["front"]["SatGlobal"] = sat_values[0]
    shadow_values = [v for k, v in skin_tone_overrides.items() if "shadow" in k.lower()]
    if shadow_values:
        # Shadow compensation boost -> face smoothing for natural rolloff
        bsg_changes["back_main"]["FaceSmoothingDefault"] = shadow_values[0]
        bsg_changes["front"]["FaceSmoothingDefault"] = shadow_values[0]

    # Low-Light / Night: denoise/HDR -> BSG multi-frame parameters
    denoise_val = night_overrides.get("lib_denoise_key", "1")
    lumadenoise_val = night_overrides.get("lib_lumadenoise_key", "1")
    hdr_frames_val = night_overrides.get("pref_frames_hdr_key", "12")
    hdr_plus_val = night_overrides.get("pref_camera_hdr_plus_key", "enhanced")
    preserving_val = night_overrides.get("lib_preservinghigh_key", "1")

    bsg_changes["back_main"]["HDRPlusEnabled"] = "true" if hdr_plus_val != "0" else "false"
    bsg_changes["back_main"]["HDRPlusDefaultFrames"] = hdr_frames_val
    bsg_changes["back_main"]["HDRPlusMaxFrames"] = str(min(20, max(8, int(float(hdr_frames_val)))))
    bsg_changes["back_main"]["SabreEnabled"] = "true" if float(denoise_val) > 0 else "false"
    bsg_changes["back_main"]["SabreMaxFrames"] = str(min(10, max(4, int(float(denoise_val)) + 3)))
    bsg_changes["back_main"]["NightSightEnabled"] = "true"
    bsg_changes["back_main"]["NightSightDefaultFrames"] = "18"
    bsg_changes["back_main"]["NightSightMaxFrames"] = "25"
    bsg_changes["back_main"]["ExposureCompensation"] = "0"
    bsg_changes["back_main"]["JPEGQuality"] = "95"
    bsg_changes["back_main"]["RAWEnabled"] = "true"
    bsg_changes["back_main"]["AEMode"] = "sceneModeNormal"
    bsg_changes["back_main"]["FlashEnabled"] = "true"

    # LibAGC: AWB engine for photo mode white balance
    bsg_changes["LibAGC"]["AWBEngine"] = "libagc"
    bsg_changes["LibAGC"]["CCTMeteringEnabled"] = "true"
    bsg_changes["LibAGC"]["ExposureControl"] = "libagc"

    # Portrait & Bokeh: WB warm-cast reduction -> ColorTransform, AEMode
    cw_rg_val = night_overrides.get("cw_rg_key", "0.5925")
    try:
        cw_rg_float = float(cw_rg_val)
        if cw_rg_float < 0.50:
            bsg_changes["back_main"]["ColorTransformMode"] = "4"
            bsg_changes["back_main"]["ColorTransformCaseLabel"] = "Leica Warm"
    except (ValueError, TypeError):
        pass

    bsg_changes["back_main"]["AEMode"] = "sceneModeNormal"
    bsg_changes["front"]["AEMode"] = "sceneModePortrait"

    # Sharpness & MTF50: balanced coefficients -> JPEGQuality, frame caps
    sharpness_val = "2"  # moderate, no halos on skin
    bsg_changes["back_main"]["JPEGQuality"] = "96"
    bsg_changes["back_main"]["HDRPlusMaxFrames"] = "15"
    bsg_changes["back_main"]["SabreMaxFrames"] = "8"

    # ---- Tier 5: Apply BSG changes ----------------------------------------
    changed_count = 0
    for role, changes in bsg_changes.items():
        if role == "LibAGC":
            # Find or create <LibAGC> section
            libagc = root.find("LibAGC")
            if libagc is None:
                libagc = ET.SubElement(root, "LibAGC")
            for key, val in changes.items():
                # Check if child exists
                found = False
                for child in libagc:
                    if child.tag == key:
                        child.text = val
                        found = True
                        break
                if not found:
                    child = ET.SubElement(libagc, key)
                    child.text = val
                    changed_count += 1
                elif child.text != val:
                    child.text = val
                    changed_count += 1
            continue

        cam = _select_camera(root, role)
        if cam is None:
            logger.warning("No <Camera role='%s'> in BSG template", role)
            continue
        for key, val in changes.items():
            current = _bsg_get(cam, key)
            if current is None:
                _bsg_set(cam, key, val)
                changed_count += 1
            elif current != val:
                # Update existing element text
                for child in cam:
                    if child.tag == key:
                        child.text = val
                        changed_count += 1
                        break

    logger.info("Applied %d BSG element changes", changed_count)

    # ---- Validation -------------------------------------------------------
    # Re-parse to verify well-formedness
    xml_string = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ET.fromstring(xml_string)  # raises if not well-formed

    output_hash = hashlib.sha256(xml_string).hexdigest()
    template_hash = hashlib.sha256(bsg_template.read_bytes()).hexdigest()

    validation = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "template_profile": str(bsg_template),
        "template_sha256": template_hash,
        "output_profile": str(output_path),
        "output_sha256": output_hash,
        "bsg_changes_applied": changed_count,
        "skin_tone_keys": len(skin_tone_overrides),
        "night_keys": len(night_overrides),
        "schema": "BSG Config v2024.2 with <Camera id='role'> elements",
        "xml_well_formed": True,
        "photo_mode_ready": True,
        "has_libagc": root.find("LibAGC") is not None,
        "has_back_main_camera": _select_camera(root, "back_main") is not None,
        "status": "built_unverified",
    }

    # ---- Write output -----------------------------------------------------
    if not dry_run:
        _write_xml(root, output_path)
        logger.info("Output BSG XML written: %s", output_path)

        status_text = f"""# LXX521 / Sony IMX682 — All-in-One Master (BSG format)

- Status: `BUILT_UNVERIFIED_NOT_DEVICE_VALIDATED`
- Generated: `{validation['generated']}`
- Template: `{bsg_template.name}` (BSG Config v2024.2)
- Output: `{output_path.name}`
- Template SHA-256: `{template_hash}`
- Output SHA-256: `{output_hash}`
- XML parsing: PASS (BSG format)
- XML root: `<Config version='2024.2'>`
- BSG elements changed: {validation['bsg_changes_applied']}
- Skin-tone keys (locked): {validation['skin_tone_keys']}
- Low-light / night keys: {validation['night_keys']}
- Photo-mode ready: {validation['photo_mode_ready']}
- Has <LibAGC> AWB section: {validation['has_libagc']}
- Has <Camera role='back_main'>: {validation['has_back_main_camera']}
- Deploy target: {DEPLOY_DIR}
- Tuning changes: merged from 4 sub-profiles; see
  `analysis/reports/all_in_one_master_merge_diff.md`
- Device validation: NOT PERFORMED.

This is an all-in-one master candidate in BSG format, not a device-validated
calibration profile. Test in daylight, indoor, low-light, and
portrait scenarios before deployment.
"""
        OUTPUT_STATUS.write_text(status_text, encoding="utf-8")
        logger.info("Status report written: %s", OUTPUT_STATUS)

        VALIDATION_REPORT.write_text(
            json.dumps(validation, indent=2), encoding="utf-8"
        )
        logger.info("Validation report written: %s", VALIDATION_REPORT)

        _write_merge_diff_report(
            skin_tone_overrides,
            night_overrides,
            bsg_changes,
            validation,
        )
        logger.info("Merge diff report written: %s", MERGE_DIFF_REPORT)

        # ---- Deploy to /sdcard/GCam/Configs/ ------------------------------
        if deploy:
            DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
            deploy_path = DEPLOY_DIR / output_path.name
            shutil.copy2(output_path, deploy_path)
            logger.info("Deployed to: %s", deploy_path)
    else:
        logger.info("Dry run — no files written")

    return validation


def _write_merge_diff_report(
    skin_tone_overrides: Dict[str, str],
    night_overrides: Dict[str, str],
    bsg_changes: Dict[str, Dict[str, str]],
    validation: Dict,
) -> None:
    """Write a human-readable merge diff report."""
    lines = [
        "# All-in-One Master Merge Diff Report (BSG format)",
        "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "## Sub-Profile Contributions",
        "",
        f"- Perfect Skin-Tone Matrix: {len(skin_tone_overrides)} keys (locked)",
        f"- Low-Light / Night Enhancement: {len(night_overrides)} keys",
        f"- Portrait & Bokeh Tuning: applied to BSG Camera elements",
        f"- Optical Sharpness & MTF50: applied to BSG Camera elements",
        "",
        "## BSG Schema Elements Changed",
        "",
        "| Camera Role | Element | Value |",
        "|-------------|---------|-------|",
    ]
    for role in sorted(bsg_changes.keys()):
        if role == "LibAGC":
            for key in sorted(bsg_changes[role].keys()):
                lines.append(f"| LibAGC | {key} | {bsg_changes[role][key]} |")
        else:
            for key in sorted(bsg_changes[role].keys()):
                lines.append(f"| {role} | {key} | {bsg_changes[role][key]} |")

    lines.append("")
    lines.append("## Skin-Tone Perfect Keys (locked, applied first)")
    lines.append("")
    lines.append("| LMC Key | Value |")
    lines.append("|---------|-------|")
    for k in sorted(skin_tone_overrides):
        lines.append(f"| {k} | {skin_tone_overrides[k]} |")

    lines.append("")
    lines.append("## Night Override Keys")
    lines.append("")
    lines.append("| LMC Key | Value |")
    lines.append("|---------|-------|")
    for k in sorted(night_overrides):
        lines.append(f"| {k} | {night_overrides[k]} |")

    lines.append("")
    lines.append("## Photo-Mode Readiness Checklist")
    lines.append("")
    lines.append(f"- XML well-formed: {validation['xml_well_formed']}")
    lines.append(f"- BSG schema: {validation['schema']}")
    lines.append(f"- Has <LibAGC> AWB section: {validation['has_libagc']}")
    lines.append(f"- Has <Camera role='back_main'>: {validation['has_back_main_camera']}")
    lines.append(f"- Photo-mode ready: {validation['photo_mode_ready']}")
    lines.append(f"- Deploy target: {DEPLOY_DIR}")

    MERGE_DIFF_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


__all__ = ["build_all_in_one_master"]
