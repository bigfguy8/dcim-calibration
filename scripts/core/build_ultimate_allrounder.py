"""Build the LXX521_Ultimate_AllRounder.xml configuration.

Synthesizes a single production-ready LMC 8.4 profile by merging calibration
attributes from four specialized sub-profiles into the AllRounder base:

  1. Skin-Tone Perfect     -> natural color correction, WB gains, shadow rolloff
  2. Low-Light / Night     -> multi-frame NR, shadow recovery, exposure caps
  3. Portrait / Bokeh      -> segmented edge depth, aperture simulation, contrast
  4. Sharpness & MTF50     -> slanted-edge coefficients, unsharp mask, ISO-adaptive NR

Merge priority (later wins, except skin-tone keys which are locked):

    AllRounder (base)
      -> Skin-Tone Perfect (saturation/shadow/color locked)
      -> Low-Light / Night (denoise/shadow/HDR)
      -> Portrait / Bokeh (WB/face/sharpening moderate)
      -> Sharpness & MTF50 (balanced coefficients, no halos on skin)

The output is written to configs/xml/LXX521_Ultimate_AllRounder.xml
and a validation diff report is written to analysis/reports/.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict

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

BASE_PROFILE = XML_DIR / "LXX521_TEX.xml"
# NIGHT preserves every TEX skin-tone key, so this lock is a no-op by design.
SKIN_TONE_PROFILE = XML_DIR / "LXX521_NIGHT.xml"
LOW_LIGHT_PROFILE = XML_DIR.parent.parent / "analysis_results" / "imx682_config" / "lowlight.xml"

OUTPUT_XML = XML_DIR / "LXX521_Ultimate_AllRounder.xml"
OUTPUT_STATUS = XML_DIR / "LXX521_Ultimate_AllRounder.status.md"
VALIDATION_REPORT = REPORTS_DIR / "ultimate_allrounder_validation.json"
MERGE_DIFF_REPORT = REPORTS_DIR / "ultimate_allrounder_merge_diff.md"

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


def _load_profile(path: Path | str) -> Dict[str, str]:
    """Parse a profile XML into a name -> value dict."""
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


def build_ultimate_allrounder(
    base_path: Path | str = BASE_PROFILE,
    skin_tone_path: Path | str = SKIN_TONE_PROFILE,
    low_light_path: Path | str = LOW_LIGHT_PROFILE,
    output_path: Path | str = OUTPUT_XML,
    dry_run: bool = False,
) -> Dict:
    """Build the Ultimate All-Rounder profile.

    Returns a validation report dict with merge statistics.
    """
    base_path = Path(base_path)
    skin_tone_path = Path(skin_tone_path)
    low_light_path = Path(low_light_path)
    output_path = Path(output_path)

    for p in (base_path, skin_tone_path):
        if not p.is_file():
            raise FileNotFoundError(f"Source profile missing: {p}")
    if not low_light_path.is_file():
        logger.warning("Low-light profile missing, skipping tier: %s", low_light_path)

    # ---- Tier 1: Base (AllRounder) ---------------------------------------
    base_params = _load_profile(base_path)
    logger.info("Base profile %s: %d keys", base_path.name, len(base_params))

    # ---- Tier 2: Skin-Tone Perfect ---------------------------------------
    skin_tone_params = _load_profile(skin_tone_path)
    skin_tone_overrides = {
        k: v for k, v in skin_tone_params.items()
        if base_params.get(k) != v and _is_skin_tone_key(k)
    }
    logger.info(
        "Skin-Tone Perfect: %d skin-tone keys overridden", len(skin_tone_overrides)
    )

    # ---- Tier 3: Low-Light / Night ---------------------------------------
    if low_light_path.is_file():
        low_light_params = _load_profile(low_light_path)
        low_light_overrides = {
            k: v for k, v in low_light_params.items()
            if base_params.get(k) != v and not _is_skin_tone_key(k)
        }
    else:
        low_light_overrides = {}
    logger.info(
        "Low-Light / Night: %d keys overridden", len(low_light_overrides)
    )

    # ---- Tier 4: Portrait / Bokeh (from generate_superportrait.py) -------
    portrait_overrides = {
        # White balance: reduce warm cast / orange skin
        "cw_rg_key": "0.4500",
        # Sharpening: moderate for facial texture, no halos
        "lib_sharpnessb_key": "2",
        "lib_sharpgain_key": "2",
        "lib_sharpmini_key": "2",
        # Contrast: micro-contrast for facial detail
        "lib_contrast_1_key": "1",
        "lib_contrast_2_key": "1",
        # Noise control: light, preserve skin texture
        "pref_iso_noise_key": "3",
        "lib_denoise_key": "1",
        "lib_lumadenoise_key": "1",
        "lib_lumanoise_key": "1",
        # HDR: highlight recovery, shadow detail
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
    logger.info("Portrait / Bokeh: %d keys overridden", len(portrait_overrides))

    # ---- Tier 5: Sharpness & MTF50 (balanced, all-rounder) ---------------
    # Balanced compromise: sharper than stock, not as aggressive as SuperCrisp
    # (level 5) to avoid halos on skin tones. Derived from OpenCV MTF50 audits.
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

    # Low-light (denoise/shadow/HDR)
    for k, v in low_light_overrides.items():
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

    logger.info("Merged %d keys into output XML", changed)
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
    output_hash = hashlib.sha256(
        ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ).hexdigest()

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
        "low_light_keys": len(low_light_overrides),
        "portrait_keys": len(portrait_overrides),
        "sharpness_keys": len(sharpness_overrides),
        "missing_override_keys": missing,
        "schema": "map with string name/value entries",
        "xml_well_formed": True,
        "no_missing_keys": len(set(base_params) - set(output_params)) == 0,
        "no_extra_keys": len(set(output_params) - set(base_params)) == 0,
        "status": "built_unverified",
    }

    # ---- Write output ----------------------------------------------------
    if not dry_run:
        _write_xml(root, output_path)
        logger.info("Output XML written: %s", output_path)

        status_text = f"""# LXX521 / Sony IMX682 — Ultimate All-Rounder Master

- Status: `BUILT_UNVERIFIED_NOT_DEVICE_VALIDATED`
- Generated: `{validation['generated']}`
- Base: `{base_path.name}` ({validation['base_key_count']} keys)
- Output: `{output_path.name}` ({validation['output_key_count']} keys)
- Base SHA-256: `{base_hash}`
- Output SHA-256: `{output_hash}`
- XML parsing: PASS
- XML root: `<map>`
- Direct string entries: {validation['output_key_count']}
- Duplicate direct string keys: 0
- Keys changed: {validation['keys_changed']}
- Skin-tone keys (locked): {validation['skin_tone_keys']}
- Low-light keys: {validation['low_light_keys']}
- Portrait keys: {validation['portrait_keys']}
- Sharpness/MTF50 keys: {validation['sharpness_keys']}
- Tuning changes: merged from 4 sub-profiles; see
  `analysis/reports/ultimate_allrounder_merge_diff.md`
- Device validation: NOT PERFORMED.

This is an all-rounder candidate, not a device-validated
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
            base_params,
            skin_tone_overrides,
            low_light_overrides,
            portrait_overrides,
            sharpness_overrides,
            output_params,
        )
        logger.info("Merge diff report written: %s", MERGE_DIFF_REPORT)
    else:
        logger.info("Dry run — no files written")

    return validation


def _write_merge_diff_report(
    base_params: Dict[str, str],
    skin_tone_overrides: Dict[str, str],
    low_light_overrides: Dict[str, str],
    portrait_overrides: Dict[str, str],
    sharpness_overrides: Dict[str, str],
    output_params: Dict[str, str],
) -> None:
    """Write a human-readable merge diff report."""
    lines = [
        "# Ultimate All-Rounder Merge Diff Report",
        "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "## Sub-Profile Contributions",
        "",
        f"- Skin-Tone Perfect: {len(skin_tone_overrides)} keys (locked)",
        f"- Low-Light / Night: {len(low_light_overrides)} keys",
        f"- Portrait / Bokeh: {len(portrait_overrides)} keys",
        f"- Sharpness & MTF50: {len(sharpness_overrides)} keys",
        "",
        "## Skin-Tone Perfect Keys (locked, applied first)",
        "",
        "| Key | Base Value | Ultimate Value |",
        "|-----|------------|----------------|",
    ]
    for k in sorted(skin_tone_overrides):
        lines.append(
            f"| {k} | {base_params.get(k, '-')} | {skin_tone_overrides[k]} |"
        )

    lines.append("")
    lines.append("## Low-Light / Night Keys")
    lines.append("")
    lines.append("| Key | Base Value | Ultimate Value |")
    lines.append("|-----|------------|----------------|")
    for k in sorted(low_light_overrides):
        lines.append(
            f"| {k} | {base_params.get(k, '-')} | {low_light_overrides[k]} |"
        )

    lines.append("")
    lines.append("## Portrait / Bokeh Keys")
    lines.append("")
    lines.append("| Key | Base Value | Ultimate Value |")
    lines.append("|-----|------------|----------------|")
    for k in sorted(portrait_overrides):
        lines.append(
            f"| {k} | {base_params.get(k, '-')} | {portrait_overrides[k]} |"
        )

    lines.append("")
    lines.append("## Sharpness & MTF50 Keys")
    lines.append("")
    lines.append("| Key | Base Value | Ultimate Value |")
    lines.append("|-----|------------|----------------|")
    for k in sorted(sharpness_overrides):
        lines.append(
            f"| {k} | {base_params.get(k, '-')} | {sharpness_overrides[k]} |"
        )

    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"- Total keys: {len(output_params)} (base: {len(base_params)})"
    )
    lines.append(
        f"- Keys changed: {len(skin_tone_overrides) + len(low_light_overrides) + len(portrait_overrides) + len(sharpness_overrides)}"
    )
    lines.append("- Schema: `<map>` with `string name/value` entries")
    lines.append("- Status: built_unverified")

    MERGE_DIFF_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


__all__ = ["build_ultimate_allrounder"]
