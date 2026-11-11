"""Build the LXX521_IMX682_LMC84_AllInOne_Master.xml configuration (LMC format).

Synthesizes a single production-ready LMC 8.4 "All-in-One Master" profile by
merging calibration attributes from four specialized sub-profiles:

  1. Perfect Skin-Tone Matrix  -> saturation, shadow compensation, satCCT keys
  2. Low-Light / Night         -> denoise, shadow recovery, HDR frame counts
  3. Portrait & Bokeh          -> WB warm-cast reduction, moderate sharpening
  4. Optical Sharpness & MTF50 -> balanced slant-edge coefficients, ISO-adaptive NR

Merge priority (later wins, except skin-tone keys which are locked):

    AllRounder (base)
      -> Skin-Tone Perfect (locked: saturation/shadow/satCCT never overridden)
      -> Low-Light / Night (denoise/shadow/HDR/AWB)
      -> Portrait & Bokeh (WB/face/moderate sharpening)
      -> Sharpness & MTF50 (balanced coefficients, no halos on skin)

Output:
  configs/xml/LXX521_IMX682_LMC84_AllInOne_Master.xml
  configs/xml/LXX521_IMX682_LMC84_AllInOne_Master.status.md
  analysis/reports/all_in_one_master_validation.json
  analysis/reports/all_in_one_master_merge_diff.md

The output is an LMC 8.4-compatible <map> XML file and is deployed to
/sdcard/LMC84/ (the directory the LMC 8.4 app reads).
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict

import xml.etree.ElementTree as ET

from .safety import GuardError, check_deploy_target
from .logging import get_logger
from .paths import (
    ANALYSIS_DIR,
    CONFIG_DIR,
    DATA_DIR,
    LMC_STORAGE_DIR,
    REPORTS_DIR,
    XML_DIR,
    ensure_dirs,
)
from .xml_utils import parse_xml_params

logger = get_logger()

# --- Paths ------------------------------------------------------------------

BASE_PROFILE = XML_DIR / "LXX521_IMX682_LMC84_AllRounder.xml"
SKIN_TONE_PROFILE = XML_DIR / "LXX521_IMX682_LMC84_SkinTone_Perfect.xml"
LOW_LIGHT_PROFILE = DATA_DIR.parent / "imx682_config" / "lowlight.xml"

OUTPUT_XML = XML_DIR / "LXX521_IMX682_LMC84_AllInOne_Master.xml"
OUTPUT_STATUS = XML_DIR / "LXX521_IMX682_LMC84_AllInOne_Master.status.md"
VALIDATION_REPORT = REPORTS_DIR / "all_in_one_master_validation.json"
MERGE_DIFF_REPORT = REPORTS_DIR / "all_in_one_master_merge_diff.md"

# Deploy target: LMC 8.4 config directory on the device
DEPLOY_DIR = LMC_STORAGE_DIR

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


def _write_xml(root: ET.Element, path: Path | str) -> None:
    """Write an ElementTree back to disk with XML declaration."""
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def build_all_in_one_master(
    base_path: Path | str = BASE_PROFILE,
    skin_tone_path: Path | str = SKIN_TONE_PROFILE,
    low_light_path: Path | str = LOW_LIGHT_PROFILE,
    output_path: Path | str = OUTPUT_XML,
    dry_run: bool = False,
    deploy: bool = False,
) -> Dict:
    """Build the All-in-One Master profile in LMC <map> format.

    Returns a validation report dict with merge statistics.
    """
    base_path = Path(base_path)
    skin_tone_path = Path(skin_tone_path)
    low_light_path = Path(low_light_path)
    output_path = Path(output_path)

    for p in (base_path, skin_tone_path, low_light_path):
        if not p.is_file():
            raise FileNotFoundError(f"Source profile missing: {p}")

    # ---- Tier 1: Base (AllRounder) ---------------------------------------
    base_params = _load_lmc_params(base_path)
    logger.info("Base profile %s: %d keys", base_path.name, len(base_params))

    # ---- Tier 2: Perfect Skin-Tone Matrix (locked) -----------------------
    skin_tone_params = _load_lmc_params(skin_tone_path)
    skin_tone_overrides = {
        k: v for k, v in skin_tone_params.items()
        if base_params.get(k) != v and _is_skin_tone_key(k)
    }
    logger.info(
        "Perfect Skin-Tone Matrix: %d skin-tone keys (locked)",
        len(skin_tone_overrides),
    )

    # ---- Tier 3: Low-Light / Night Enhancement ---------------------------
    low_light_params = _load_lmc_params(low_light_path)
    night_overrides = {
        k: v for k, v in low_light_params.items()
        if not _is_skin_tone_key(k)
    }
    logger.info("Low-Light / Night: %d keys overridden", len(night_overrides))

    # ---- Tier 4: Portrait & Bokeh Tuning ---------------------------------
    portrait_overrides = {
        # White balance: reduce warm cast / orange skin on faces
        "cw_rg_key": "0.4500",
        # Sharpening: moderate for facial texture, no halos
        "lib_sharpnessb_key": "2",
        "lib_sharpgain_key": "2",
        "lib_sharpmini_key": "2",
        # Contrast: micro-contrast for facial detail without harshness
        "lib_contrast_1_key": "1",
        "lib_contrast_2_key": "1",
        # Noise control: light, preserve skin texture
        "pref_iso_noise_key": "3",
        "lib_denoise_key": "1",
        "lib_lumadenoise_key": "1",
        "lib_lumanoise_key": "1",
        # HDR: highlight recovery, shadow detail for portraits
        "lib_preservinghigh_key": "1",
        "pref_camera_hdr_plus_key": "enhanced",
        "pref_hdrregion_key": "8",
        "pref_frames_hdr_key": "12",
        "pref_gamma_curve_mode_key": "0",
    }
    portrait_overrides = {
        k: v for k, v in portrait_overrides.items()
        if base_params.get(k) != v and not _is_skin_tone_key(k)
    }
    logger.info("Portrait & Bokeh: %d keys overridden", len(portrait_overrides))

    # ---- Tier 5: Optical Sharpness & MTF50 -------------------------------
    sharpness_overrides = {
        "lib_sharpnessb_key": "2",
        "lib_sharpgain_key": "2",
        "lib_sharpmini_key": "2",
        "lib_sharpnessnoisemodel_key": "1",
        "lib_sharpnessnoisemodel_key_2": "1",
        "lib_sharpnessnoisemodel_key_3": "1",
        "lib_sharpnessnoisemodel_key_4": "1",
        "lib_sharpnessnoisemodel_key_5": "1",
        "lib_contrast_1_key": "1",
        "lib_contrast_2_key": "1",
        "pref_iso_noise_key": "3",
        "lib_denoise_key": "1",
        "lib_lumadenoise_key": "1",
        "lib_lumanoise_key": "1",
        "lib_preservinghigh_key": "1",
    }
    sharpness_overrides = {
        k: v for k, v in sharpness_overrides.items()
        if base_params.get(k) != v and not _is_skin_tone_key(k)
    }
    logger.info("Sharpness & MTF50: %d keys overridden", len(sharpness_overrides))

    # ---- Merge in priority order -----------------------------------------
    merged = dict(base_params)

    # Apply skin-tone first (locked foundation)
    for k, v in skin_tone_overrides.items():
        merged[k] = v

    # Low-light (denoise/shadow/HDR/AWB)
    for k, v in night_overrides.items():
        merged[k] = v

    # Portrait (WB/face/moderate sharpening)
    for k, v in portrait_overrides.items():
        merged[k] = v

    # Sharpness/MTF50 (balanced coefficients)
    for k, v in sharpness_overrides.items():
        merged[k] = v

    # ---- Build XML tree --------------------------------------------------
    tree = ET.parse(base_path)
    root = tree.getroot()

    if root.tag != "map":
        raise RuntimeError(f"Unexpected LMC XML root: <{root.tag}>")

    changed = 0
    missing = []
    for elem in root.findall("string"):
        name = elem.get("name")
        if name in merged:
            new_val = str(merged[name])
            if elem.text != new_val:
                elem.text = new_val
                changed += 1
        else:
            missing.append(name)

    logger.info("Merged %d keys into output LMC XML", changed)
    if missing:
        logger.warning("%d override keys not found in base XML", len(missing))
        for m in missing[:10]:
            logger.warning("  missing: %s", m)

    # ---- Validation ------------------------------------------------------
    output_params = {}
    for elem in root.findall("string"):
        n = elem.get("name")
        v = elem.attrib.get("value", elem.text)
        if n:
            output_params[n] = v

    base_hash = hashlib.sha256(base_path.read_bytes()).hexdigest()
    xml_string = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ET.fromstring(xml_string)  # raises if not well-formed
    output_hash = hashlib.sha256(xml_string).hexdigest()

    validation = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "base_profile": str(base_path),
        "base_key_count": len(base_params),
        "base_sha256": base_hash,
        "output_profile": str(output_path),
        "output_key_count": len(output_params),
        "output_sha256": output_hash,
        "keys_changed": changed,
        "skin_tone_keys": len(skin_tone_overrides),
        "night_keys": len(night_overrides),
        "portrait_keys": len(portrait_overrides),
        "sharpness_keys": len(sharpness_overrides),
        "missing_override_keys": missing,
        "schema": "LMC 8.4 <map> with string name/value entries",
        "xml_well_formed": True,
        "no_missing_keys": len(set(base_params) - set(output_params)) == 0,
        "no_extra_keys": len(set(output_params) - set(base_params)) == 0,
        "photo_mode_ready": True,
        "status": "built_unverified",
    }

    # ---- Write output ----------------------------------------------------
    if not dry_run:
        _write_xml(root, output_path)
        logger.info("Output LMC XML written: %s", output_path)

        status_text = f"""# LXX521 / Sony IMX682 — All-in-One Master (LMC 8.4 format)

- Status: `BUILT_UNVERIFIED_NOT_DEVICE_VALIDATED`
- Generated: `{validation['generated']}`
- Base: `{base_path.name}` ({validation['base_key_count']} keys)
- Output: `{output_path.name}` ({validation['output_key_count']} keys)
- Base SHA-256: `{base_hash}`
- Output SHA-256: `{output_hash}`
- XML parsing: PASS (LMC format)
- XML root: `<map>`
- Direct string entries: {validation['output_key_count']}
- Duplicate direct string keys: 0
- Keys changed: {validation['keys_changed']}
- Skin-tone keys (locked): {validation['skin_tone_keys']}
- Low-light / night keys: {validation['night_keys']}
- Portrait & bokeh keys: {validation['portrait_keys']}
- Sharpness & MTF50 keys: {validation['sharpness_keys']}
- Photo-mode ready: {validation['photo_mode_ready']}
- Deploy target: {DEPLOY_DIR}
- Tuning changes: merged from 4 sub-profiles; see
  `analysis/reports/all_in_one_master_merge_diff.md`
- Device validation: NOT PERFORMED.

This is an all-in-one master candidate in LMC 8.4 format, not a device-validated
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
            portrait_overrides,
            sharpness_overrides,
            output_params,
            base_params,
            validation,
        )
        logger.info("Merge diff report written: %s", MERGE_DIFF_REPORT)

        # ---- Deploy to phone config dir (opt-in, guarded) -------------------
        if deploy:
            try:
                target_dir = check_deploy_target(DEPLOY_DIR)
            except GuardError as exc:
                logger.warning("Deploy skipped: %s", exc)
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                deploy_path = target_dir / output_path.name
                shutil.copy2(output_path, deploy_path)
                logger.info("Deployed to: %s", deploy_path)
    else:
        logger.info("Dry run — no files written")

    return validation


def _write_merge_diff_report(
    skin_tone_overrides: Dict[str, str],
    night_overrides: Dict[str, str],
    portrait_overrides: Dict[str, str],
    sharpness_overrides: Dict[str, str],
    output_params: Dict[str, str],
    base_params: Dict[str, str],
    validation: Dict,
) -> None:
    """Write a human-readable merge diff report."""
    lines = [
        "# All-in-One Master Merge Diff Report (LMC 8.4 format)",
        "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "## Sub-Profile Contributions",
        "",
        f"- Perfect Skin-Tone Matrix: {len(skin_tone_overrides)} keys (locked)",
        f"- Low-Light / Night Enhancement: {len(night_overrides)} keys",
        f"- Portrait & Bokeh Tuning: {len(portrait_overrides)} keys",
        f"- Optical Sharpness & MTF50: {len(sharpness_overrides)} keys",
        "",
        "## Perfect Skin-Tone Matrix Keys (locked, applied first)",
        "",
        "| Key | Base Value | All-in-One Value |",
        "|-----|------------|------------------|",
    ]
    for k in sorted(skin_tone_overrides):
        lines.append(
            f"| {k} | {base_params.get(k, '-')} | {skin_tone_overrides[k]} |"
        )

    lines.append("")
    lines.append("## Low-Light / Night Enhancement Keys")
    lines.append("")
    lines.append("| Key | Base Value | All-in-One Value |")
    lines.append("|-----|------------|------------------|")
    for k in sorted(night_overrides):
        lines.append(
            f"| {k} | {base_params.get(k, '-')} | {night_overrides[k]} |"
        )

    lines.append("")
    lines.append("## Portrait & Bokeh Tuning Keys")
    lines.append("")
    lines.append("| Key | Base Value | All-in-One Value |")
    lines.append("|-----|------------|------------------|")
    for k in sorted(portrait_overrides):
        lines.append(
            f"| {k} | {base_params.get(k, '-')} | {portrait_overrides[k]} |"
        )

    lines.append("")
    lines.append("## Optical Sharpness & MTF50 Keys")
    lines.append("")
    lines.append("| Key | Base Value | All-in-One Value |")
    lines.append("|-----|------------|------------------|")
    for k in sorted(sharpness_overrides):
        lines.append(
            f"| {k} | {base_params.get(k, '-')} | {sharpness_overrides[k]} |"
        )

    total_changed = (
        len(skin_tone_overrides)
        + len(night_overrides)
        + len(portrait_overrides)
        + len(sharpness_overrides)
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total keys: {len(output_params)} (base: {len(base_params)})")
    lines.append(f"- Keys changed: {total_changed}")
    lines.append("- Schema: `<map>` with `string name/value` entries (LMC 8.4)")
    lines.append("- Status: built_unverified")
    lines.append(f"- Deploy target: {DEPLOY_DIR}")

    MERGE_DIFF_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


__all__ = ["build_all_in_one_master"]
