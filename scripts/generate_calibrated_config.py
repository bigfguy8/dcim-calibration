#!/usr/bin/env python3
"""Generate a calibrated, import-safe LMC 8.4 config for LXX521 / IMX682.

Strategy
--------
The only config that is *proven* to load and shoot on this device is the one
exported by the app itself (``configs/xml/LXX521_IMX682.xml``).  Every other
profile in this repo is a derivative of it, and several "aggressive" variants
are known to crash the pipeline (HDR burst 12, forced color -4, JPEG 100,
RAW on).

So the calibrated config is produced by *minimal textual patching* of the
device export:

* the key set is never changed (no invented keys -> the app cannot reject
  the profile);
* only values listed in :data:`CALIBRATION` are touched;
* the byte layout, element order and ``<set>`` block stay identical, so the
  diff is exactly the number of calibrated keys.

Every applied value is cross-checked against all reference profiles in
``configs/xml``: a value must already occur for that key in at least one
profile (i.e. it is a value the app has accepted before).  Crash-critical
keys are additionally asserted against :data:`STABILITY_LIMITS`.

Usage
-----
    python3 scripts/generate_calibrated_config.py                 # build V5
    python3 scripts/generate_calibrated_config.py --variant v3     # noise-first
    python3 scripts/generate_calibrated_config.py --variant v4     # night/high-ISO
    python3 scripts/generate_calibrated_config.py --dry-run        # delta only
    python3 scripts/generate_calibrated_config.py --deploy         # copy to phone

Output
------
    configs/xml/<OUTPUT_STEM>.xml
    configs/xml/<OUTPUT_STEM>.status.md
    configs/xml/<OUTPUT_STEM>.report.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Make ``scripts.core`` importable when run as a plain file.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.paths import XML_DIR, LMC_STORAGE_DIR  # noqa: E402
from core.safety import GuardError, check_deploy_target  # noqa: E402
from core.xml_utils import parse_xml_params  # noqa: E402

BASE_NAME = "LXX521_TEX.xml"
DEFAULT_VARIANT = "v3"

# ---------------------------------------------------------------------------
# V3 — noise-first delta.  Each entry is (new_value, rationale).
#
# V2 (the profile that looked grainy) kept the device's sharpening cluster:
# sharpgain 1.0 + micro-sharpen 0.5 + sharpness B 1.1.  Those stages apply
# unsharp masking, which multiplies sensor grain.  V3 switches the two
# amplifiers off and raises NR smoothing.
#
# Measured effect: the V3 shot at ISO 1207 had 3x lower noise than the V2
# shot at ISO 2825 (flat-block sigma 1.18 vs 3.10), but its Laplacian
# variance fell to 30 (V2: 69), i.e. V3 is over-smoothed.  Hence V5 below.
# ---------------------------------------------------------------------------
V3_DELTA: "dict[str, tuple[str, str]]" = {
    "lib_sharpgain_key": (
        "0",
        "Sharpening gain 1.0->0: unsharp masking was amplifying sensor grain.",
    ),
    "lib_sharpmini_key": (
        "0",
        "Micro-sharpen 0.5->0: second noise-amplifying sharpener, now off.",
    ),
    "lib_sharpnessb_key": (
        "1.02",
        "Global sharpness 1.1->1.02: keeps edge definition without "
        "multiplying noise.",
    ),
    "lib_denoisesmoothing_key": (
        "2",
        "NR smoothing 1->2: stronger clean-up of the denoised result.",
    ),
    "pref_qjpg_key": (
        "97",
        "JPEG quality 95->97: fewer compression artefacts around edges.",
    ),
    "cw_rg_key_front": (
        "0.5725",
        "Front AWB 0.5925->0.5725: measured front captures were warm; "
        "matches the calibrated main sensor.",
    ),
}

# ---------------------------------------------------------------------------
# HIGH_RES_LAYER — mandatory baseline applied to EVERY variant going forward.
# All future configs lock in high resolution:
#
#   * pref_camera_picturesize_back_key  = 3264x2448  (device max for IMX682)
#   * pref_camera_picturesize_front_key = 3264x2448  (device max)
#   * pref_camera_resolution            = full       (full-resolution path)
#   * pref_preservinghigh_key           = 1          (preserve high-frequency detail)
#   * lib_downsamplebybeforemerge_key   = 0          (no downsample before merge)
#   * pref_camera_raw_output_key        = 0          (RAW off — memory pressure)
#
# Every value is proven (appears in every profile in this repo), so the app
# cannot reject them.  Variants merge HIGH_RES_LAYER first, then their own
# delta overrides — so a variant can still change e.g. pref_qjpg_key if it
# wants a different JPEG quality.
# ---------------------------------------------------------------------------
HIGH_RES_LAYER: "dict[str, tuple[str, str]]" = {
    "pref_camera_picturesize_back_key": (
        "3264x2448",
        "High resolution: max back-camera picture size (device max 3264x2448).",
    ),
    "pref_camera_picturesize_front_key": (
        "3264x2448",
        "High resolution: max front-camera picture size (device max).",
    ),
    "pref_camera_resolution": (
        "full",
        "High resolution: full-resolution capture path (device max).",
    ),
    "pref_preservinghigh_key": (
        "1",
        "High resolution: preserve high-frequency detail at full resolution.",
    ),
    "lib_downsamplebybeforemerge_key": (
        "0",
        "High resolution: no downsampling before HDR/merge (keeps detail).",
    ),
    "pref_camera_raw_output_key": (
        "0",
        "High resolution: RAW off (adds memory pressure, not needed for JPEG).",
    ),
}

# ---------------------------------------------------------------------------
# iPhone-like delta.  iPhone look: natural colors, balanced processing,
# Smart HDR-style burst, minimal sharpening gain (iPhones don't amplify
# grain), gentle edge definition.
# ---------------------------------------------------------------------------
IPHONE_DELTA: "dict[str, tuple[str, str]]" = {
    "lib_sharpgain_key": (
        "0",
        "iPhone-like: no sharpening gain (iPhones avoid grain amplification).",
    ),
    "lib_sharpmini_key": (
        "0",
        "iPhone-like: no micro-sharpen.",
    ),
    "lib_sharpnessb_key": (
        "1.02",
        "iPhone-like: gentle global sharpness, keeps edges clean.",
    ),
    "lib_denoise_key": (
        "1",
        "iPhone-like: NR on for clean shadows.",
    ),
    "lib_denoisesmoothing_key": (
        "1",
        "iPhone-like: normal NR smoothing.",
    ),
    "lib_spatiala_key": (
        "0",
        "iPhone-like: spatial denoise off (iPhone uses different pipeline).",
    ),
    "lib_spatialdenmi2_key": (
        "0",
        "iPhone-like: spatial denoise B off.",
    ),
    "pref_frames_hdr_key": (
        "2",
        "iPhone-like: Smart HDR burst (2 frames).",
    ),
    "pref_camera_hdr_plus_key": (
        "auto",
        "iPhone-like: HDR+ on auto.",
    ),
    "pref_qjpg_key": (
        "97",
        "iPhone-like: JPEG 97 for clean compression.",
    ),
    "pref_color_key": (
        "0",
        "iPhone-like: natural color (0 = no cast).",
    ),
}

# ---------------------------------------------------------------------------
# DSLR-like delta.  DSLR look: minimal processing, raw-like output, no
# sharpening or NR, single exposure, preserve high detail.
# ---------------------------------------------------------------------------
DSLR_DELTA: "dict[str, tuple[str, str]]" = {
    "lib_sharpgain_key": (
        "0",
        "DSLR-like: no sharpening gain (raw-like).",
    ),
    "lib_sharpmini_key": (
        "0",
        "DSLR-like: no micro-sharpen.",
    ),
    "lib_sharpnessb_key": (
        "0",
        "DSLR-like: no global sharpness boost.",
    ),
    "lib_denoise_key": (
        "0",
        "DSLR-like: NR off (single exposure).",
    ),
    "lib_denoisesmoothing_key": (
        "0",
        "DSLR-like: no NR smoothing.",
    ),
    "lib_spatiala_key": (
        "0",
        "DSLR-like: spatial denoise off.",
    ),
    "lib_spatialdenmi2_key": (
        "0",
        "DSLR-like: spatial denoise B off.",
    ),
    "pref_frames_hdr_key": (
        "0",
        "DSLR-like: no HDR burst (single shot).",
    ),
    "pref_camera_hdr_plus_key": (
        "auto",
        "DSLR-like: HDR+ on auto.",
    ),
    "pref_qjpg_key": (
        "97",
        "DSLR-like: JPEG 97 for maximum detail.",
    ),
    "pref_preservinghigh_key": (
        "1",
        "DSLR-like: preserve high-frequency detail.",
    ),
}

# ---------------------------------------------------------------------------
# Pixel-like delta.  Pixel look: HDR+ computational photography, Night Sight
# spatial denoise, strong NR for clean low-light, moderate sharpening.
# ---------------------------------------------------------------------------
PIXEL_DELTA: "dict[str, tuple[str, str]]" = {
    "lib_sharpgain_key": (
        "0",
        "Pixel-like: no sharpening gain (Pixel uses minimal sharpening).",
    ),
    "lib_sharpmini_key": (
        "0",
        "Pixel-like: no micro-sharpen.",
    ),
    "lib_sharpnessb_key": (
        "1.02",
        "Pixel-like: gentle global sharpness.",
    ),
    "lib_denoise_key": (
        "1",
        "Pixel-like: NR on.",
    ),
    "lib_denoisesmoothing_key": (
        "2",
        "Pixel-like: strong NR smoothing (Night Sight style).",
    ),
    "lib_spatiala_key": (
        "1",
        "Pixel-like: spatial denoise A on (Night Sight shadows).",
    ),
    "lib_spatialdenmi2_key": (
        "1",
        "Pixel-like: spatial denoise B on (pairs with A).",
    ),
    "pref_frames_hdr_key": (
        "2",
        "Pixel-like: HDR+ burst (2 frames).",
    ),
    "pref_camera_hdr_plus_key": (
        "auto",
        "Pixel-like: HDR+ on auto.",
    ),
    "pref_qjpg_key": (
        "97",
        "Pixel-like: JPEG 97 for clean compression.",
    ),
}

# ---------------------------------------------------------------------------
# All-in-one delta.  Balanced for all scenarios: minimal sharpening gain,
# gentle NR, Smart HDR burst, natural colors.  NOT the crash-prone
# AllInOne_Master (frames=12, q=100) — this is the safe, proven version.
# ---------------------------------------------------------------------------
ALLINONE_DELTA: "dict[str, tuple[str, str]]" = {
    "lib_sharpgain_key": (
        "0",
        "All-in-one: no sharpening gain (balanced, no grain amplification).",
    ),
    "lib_sharpmini_key": (
        "0",
        "All-in-one: no micro-sharpen.",
    ),
    "lib_sharpnessb_key": (
        "1.02",
        "All-in-one: gentle global sharpness.",
    ),
    "lib_denoise_key": (
        "1",
        "All-in-one: NR on.",
    ),
    "lib_denoisesmoothing_key": (
        "1",
        "All-in-one: normal NR smoothing.",
    ),
    "lib_spatiala_key": (
        "0",
        "All-in-one: spatial denoise off (balanced).",
    ),
    "lib_spatialdenmi2_key": (
        "0",
        "All-in-one: spatial denoise B off.",
    ),
    "pref_frames_hdr_key": (
        "2",
        "All-in-one: Smart HDR burst (2 frames).",
    ),
    "pref_camera_hdr_plus_key": (
        "auto",
        "All-in-one: HDR+ on auto.",
    ),
    "pref_qjpg_key": (
        "97",
        "All-in-one: JPEG 97 for clean compression.",
    ),
    "pref_color_key": (
        "0",
        "All-in-one: natural color (0 = no cast).",
    ),
}

# ---------------------------------------------------------------------------
# DSLR_64MP_DELTA — DSLR Ultra-Crisp & Full Resolution.
#
# Design targets:
#   1. Full sensor pipeline resolution (proven device max 3264x2448 — note:
#      the device export does not contain a proven 64MP/9280x6944 value, so
#      we lock the proven max resolution with full pipeline + no downsample
#      rather than invent an unproven 64MP key that could crash).
#   2. DSLR-style tone curve: neutral preset (-1/0 are the only proven
#      values; custom curve matrices are not exposed as safe keys).
#   3. Minimal spatial NR for maximum MTF50/high-frequency detail:
#      denoise, denoise-smoothing, luma-denoise and spatial denoise all OFF.
#   4. Neutral daylight AWB: cw_rg_key_front aligned to main (0.5725 ≈ D50
#      daylight), killing the front-camera warm cast.
#   5. Zero in-camera sharpening (sharpgain/sharpmini/sharpnessb all 0) so
#      you own the MTF50 in post — no grain amplification, no halo.
# ---------------------------------------------------------------------------
DSLR_64MP_DELTA: "dict[str, tuple[str, str]]" = {
    # --- Resolution (HIGH_RES_LAYER covers these; restated for clarity) ---
    # pref_camera_picturesize_back_key:  "3264x2448",  # in HIGH_RES_LAYER
    # pref_camera_picturesize_front_key: "3264x2448",  # in HIGH_RES_LAYER
    # pref_camera_resolution:            "full",       # in HIGH_RES_LAYER
    # pref_preservinghigh_key:           "1",          # in HIGH_RES_LAYER
    # lib_downsamplebybeforemerge_key:   "0",          # in HIGH_RES_LAYER
    # pref_camera_raw_output_key:        "0",          # in HIGH_RES_LAYER
    # --- NR minimization (detail first) ---
    "lib_denoise_key": (
        "0",
        "DSLR: denoise OFF — preserve raw high-frequency detail.",
    ),
    "lib_denoisesmoothing_key": (
        "0",
        "DSLR: NR smoothing OFF — no blur of fine texture.",
    ),
    "lib_lumadenoise_key": (
        "0",
        "DSLR: luma denoise OFF — keep luminance detail.",
    ),
    "lib_spatiala_key": (
        "0",
        "DSLR: spatial denoise A OFF.",
    ),
    "lib_spatialdenmi2_key": (
        "0",
        "DSLR: spatial denoise B OFF.",
    ),
    # --- Zero in-camera sharpening (you sharpen in post) ---
    "lib_sharpgain_key": (
        "0",
        "DSLR: sharpening gain OFF — no grain amplification/halo.",
    ),
    "lib_sharpmini_key": (
        "0",
        "DSLR: micro-sharpen OFF.",
    ),
    "lib_sharpnessb_key": (
        "0",
        "DSLR: global sharpness OFF — pure sensor MTF50.",
    ),
    # --- Neutral DSLR tone curve (proven values only) ---
    "pref_tone_curve_mode_key": (
        "-1",
        "DSLR: tone-curve mode default (-1, only proven value).",
    ),
    "pref_tonecurve_preset_key": (
        "0",
        "DSLR: neutral tone-curve preset (0 = standard, only proven value).",
    ),
    # --- Neutral daylight AWB (kill warm cast) ---
    "pref_awb_key": (
        "1",
        "DSLR: AWB auto (daylight-neutral matrix).",
    ),
    "cw_rg_key_front": (
        "0.5725",
        "DSLR: front AWB aligned to main (0.5725 ≈ D50 daylight), neutral "
        "front-camera color.",
    ),
    # --- JPEG quality high but proven ---
    "pref_qjpg_key": (
        "97",
        "DSLR: JPEG 97 for clean compression without MTF loss.",
    ),
}

# ---------------------------------------------------------------------------
# DSLR_MAX_DELTA — DSLR Ultra-Crisp MAXIMUM detail.
#
# Pushes every sharpening/detail parameter to the maximum proven value while
# keeping NR off and resolution locked at the device-proven maximum.  This is
# the highest-MTF50 profile in the set — intended for tripod/daylight shooting
# where you want the absolute sharpest possible output and will manage any
# grain in post.
#
#   * lib_sharpgain_key:     1.0   (max proven within stability limits)
#   * lib_sharpmini_key:     0.5   (max proven)
#   * lib_sharpnessb_key:    1.1   (max proven within stability limits)
#   * All denoise keys:      0     (off — preserve raw high-frequency detail)
#   * Resolution:            full / 3264x2448  (HIGH_RES_LAYER)
#   * JPEG quality:          97    (max proven)
# ---------------------------------------------------------------------------
DSLR_MAX_DELTA: "dict[str, tuple[str, str]]" = {
    # --- Resolution (inherited from HIGH_RES_LAYER) ---
    # pref_camera_picturesize_back_key:  "3264x2448",  # HIGH_RES_LAYER
    # pref_camera_picturesize_front_key: "3264x2448",  # HIGH_RES_LAYER
    # pref_camera_resolution:            "full",       # HIGH_RES_LAYER
    # pref_preservinghigh_key:           "1",          # HIGH_RES_LAYER
    # lib_downsamplebybeforemerge_key:   "0",          # HIGH_RES_LAYER
    # pref_camera_raw_output_key:        "0",          # HIGH_RES_LAYER
    # --- NR minimization (detail first, zero NR) ---
    "lib_denoise_key": (
        "0",
        "DSLR_MAX: denoise OFF — maximum raw detail retention.",
    ),
    "lib_denoisesmoothing_key": (
        "0",
        "DSLR_MAX: NR smoothing OFF.",
    ),
    "lib_lumadenoise_key": (
        "0",
        "DSLR_MAX: luma denoise OFF.",
    ),
    "lib_spatiala_key": (
        "0",
        "DSLR_MAX: spatial denoise A OFF.",
    ),
    "lib_spatialdenmi2_key": (
        "0",
        "DSLR_MAX: spatial denoise B OFF.",
    ),
    # --- Maximum proven sharpening for maximum MTF50 ---
    "lib_sharpgain_key": (
        "1.0",
        "DSLR_MAX: sharpening gain 1.0 — maximum proven edge emphasis.",
    ),
    "lib_sharpmini_key": (
        "0.5",
        "DSLR_MAX: micro-sharpen 0.5 — maximum proven fine-edge boost.",
    ),
    "lib_sharpnessb_key": (
        "1.1",
        "DSLR_MAX: global sharpness 1.1 — maximum proven within limits.",
    ),
    # --- Neutral DSLR tone curve (proven values only) ---
    "pref_tone_curve_mode_key": (
        "-1",
        "DSLR_MAX: tone-curve mode default (-1, only proven value).",
    ),
    "pref_tonecurve_preset_key": (
        "0",
        "DSLR_MAX: neutral tone-curve preset (0 = standard).",
    ),
    # --- Neutral daylight AWB ---
    "pref_awb_key": (
        "1",
        "DSLR_MAX: AWB auto (daylight-neutral matrix).",
    ),
    "cw_rg_key_front": (
        "0.5725",
        "DSLR_MAX: front AWB aligned to main (0.5725 ≈ D50 daylight).",
    ),
    # --- JPEG quality ---
    "pref_qjpg_key": (
        "97",
        "DSLR_MAX: JPEG 97 for clean compression.",
    ),
}

# ---------------------------------------------------------------------------
# IPHONE_MAX_DELTA — iPhone-like MAXIMUM: max MP, low noise, crisp.
#
# Combines iPhone natural color science with maximum proven resolution,
# low-noise processing, and crisp edge definition.  Intended for daylight
# and general shooting where you want clean, crisp, color-accurate output.
#
#   * Resolution:            full / 3264x2448  (HIGH_RES_LAYER — max MP)
#   * Denoise:               1                 (NR on — low noise)
#   * Denoise smoothing:     2                 (stronger smoothing — cleaner shadows)
#   * Luma denoise:          1                 (luminance noise control)
#   * Sharpening gain:       0                 (no grain amplification)
#   * Micro-sharpen:         0                 (no noise multiplication)
#   * Global sharpness:      1.02              (gentle crisp edges)
#   * Tone curve:            neutral (-1/0)    (natural iPhone rendering)
#   * AWB:                   auto / 0.5725     (daylight-neutral front camera)
#   * JPEG quality:          97                (clean compression)
#   * Color:                 0                 (natural color, no cast)
#   * HDR burst:             2 frames          (Smart HDR style)
# ---------------------------------------------------------------------------
IPHONE_MAX_DELTA: "dict[str, tuple[str, str]]" = {
    # --- Resolution (inherited from HIGH_RES_LAYER) ---
    # pref_camera_picturesize_back_key:  "3264x2448",  # HIGH_RES_LAYER
    # pref_camera_picturesize_front_key: "3264x2448",  # HIGH_RES_LAYER
    # pref_camera_resolution:            "full",       # HIGH_RES_LAYER
    # pref_preservinghigh_key:           "1",          # HIGH_RES_LAYER
    # lib_downsamplebybeforemerge_key:   "0",          # HIGH_RES_LAYER
    # pref_camera_raw_output_key:        "0",          # HIGH_RES_LAYER
    # --- Low noise (clean shadows, minimal grain) ---
    "lib_denoise_key": (
        "1",
        "iPhone_MAX: denoise ON — clean low-noise shadows.",
    ),
    "lib_denoisesmoothing_key": (
        "2",
        "iPhone_MAX: NR smoothing 2 — stronger clean-up for low noise.",
    ),
    "lib_lumadenoise_key": (
        "1",
        "iPhone_MAX: luma denoise ON — luminance grain control.",
    ),
    "lib_spatiala_key": (
        "0",
        "iPhone_MAX: spatial denoise A OFF.",
    ),
    "lib_spatialdenmi2_key": (
        "0",
        "iPhone_MAX: spatial denoise B OFF.",
    ),
    # --- Crisp edges without grain amplification ---
    "lib_sharpgain_key": (
        "0",
        "iPhone_MAX: sharpening gain OFF — no grain amplification.",
    ),
    "lib_sharpmini_key": (
        "0",
        "iPhone_MAX: micro-sharpen OFF.",
    ),
    "lib_sharpnessb_key": (
        "1.02",
        "iPhone_MAX: gentle global sharpness — crisp edges, clean noise.",
    ),
    # --- Neutral iPhone tone curve ---
    "pref_tone_curve_mode_key": (
        "-1",
        "iPhone_MAX: tone-curve mode default (-1, only proven value).",
    ),
    "pref_tonecurve_preset_key": (
        "0",
        "iPhone_MAX: neutral tone-curve preset (0 = standard).",
    ),
    # --- Neutral daylight AWB / natural color ---
    "pref_awb_key": (
        "1",
        "iPhone_MAX: AWB auto (daylight-neutral matrix).",
    ),
    "cw_rg_key_front": (
        "0.5725",
        "iPhone_MAX: front AWB aligned to main (0.5725 ≈ D50 daylight).",
    ),
    "pref_color_key": (
        "0",
        "iPhone_MAX: natural color (0 = no cast).",
    ),
    # --- Smart HDR burst + JPEG quality ---
    "pref_frames_hdr_key": (
        "2",
        "iPhone_MAX: Smart HDR burst (2 frames).",
    ),
    "pref_camera_hdr_plus_key": (
        "auto",
        "iPhone_MAX: HDR+ on auto.",
    ),
    "pref_qjpg_key": (
        "97",
        "iPhone_MAX: JPEG 97 for clean compression.",
    ),
}

# ---------------------------------------------------------------------------
# TEXTURE_FIRST_DELTA — v4.0 Texture-First Calibration.
#
# Strictly prioritizes raw texture preservation, zero spatial smoothing, and
# maximum micro-detail retention.  All noise reduction and artificial
# sharpening stages are disabled so the IMX682 sensor detail passes through
# unfiltered for post-processing control.
#
# v4.0 parameter rules:
#   * lib_denoise_key           = 0   (Disable primary noise reduction)
#   * lib_denoisesmoothing_key  = 0   (Disable smoothing passes that blur fine lines)
#   * lib_lumadenoise_key       = 0   (Disable luminance noise filtering)
#   * lib_spatiala_key          = 0   (Disable spatial denoise matrices)
#   * lib_spatialdenmi2_key     = 0   (Disable spatial denoise matrices)
#   * lib_sharpgain_key         = 0   (Prevent artificial grain amplification)
#   * lib_sharpmini_key         = 0   (Prevent artificial grain amplification)
#   * lib_sharpnessb_key        = 0   (Neutral in-camera sharpening for post control)
#   * pref_frames_hdr_key       = 0   (No multi-frame stacking — proven value 0;
#                                      v4.0 spec says 1 but 1 is not proven in any
#                                      repo profile; 0 = no burst = even better texture)
#   * Resolution                = 3264x2448 / full  (HIGH_RES_LAYER — proven max)
# ---------------------------------------------------------------------------
TEXTURE_FIRST_DELTA: "dict[str, tuple[str, str]]" = {
    # --- Resolution (inherited from HIGH_RES_LAYER) ---
    # pref_camera_picturesize_back_key:  "3264x2448",  # HIGH_RES_LAYER
    # pref_camera_picturesize_front_key: "3264x2448",  # HIGH_RES_LAYER
    # pref_camera_resolution:            "full",       # HIGH_RES_LAYER
    # pref_preservinghigh_key:           "1",          # HIGH_RES_LAYER
    # lib_downsamplebybeforemerge_key:   "0",          # HIGH_RES_LAYER
    # pref_camera_raw_output_key:        "0",          # HIGH_RES_LAYER
    # --- Zero noise reduction (raw texture preservation) ---
    "lib_denoise_key": (
        "0",
        "v4.0: denoise OFF — raw texture preservation, no smudging.",
    ),
    "lib_denoisesmoothing_key": (
        "0",
        "v4.0: NR smoothing OFF — no blur of fine lines.",
    ),
    "lib_lumadenoise_key": (
        "0",
        "v4.0: luma denoise OFF — luminance detail retained.",
    ),
    "lib_spatiala_key": (
        "0",
        "v4.0: spatial denoise A OFF.",
    ),
    "lib_spatialdenmi2_key": (
        "0",
        "v4.0: spatial denoise B OFF.",
    ),
    # --- Zero in-camera sharpening (post-processing control) ---
    "lib_sharpgain_key": (
        "0",
        "v4.0: sharpening gain OFF — no artificial grain amplification.",
    ),
    "lib_sharpmini_key": (
        "0",
        "v4.0: micro-sharpen OFF — no noise multiplication.",
    ),
    "lib_sharpnessb_key": (
        "0",
        "v4.0: global sharpness OFF — neutral sensor MTF50.",
    ),
    # --- Minimal HDR burst (no motion ghosting / texture smudging) ---
    "pref_frames_hdr_key": (
        "0",
        "v4.0: no HDR burst — proven value 0 prevents motion ghosting and "
        "texture smudging (v4.0 spec prefers 1 but 1 is not repo-proven; "
        "0 = no burst = best texture).",
    ),
    # --- Neutral daylight AWB / natural color ---
    "pref_awb_key": (
        "1",
        "v4.0: AWB auto (daylight-neutral matrix).",
    ),
    "cw_rg_key_front": (
        "0.5725",
        "v4.0: front AWB aligned to main (0.5725 ≈ D50 daylight), fixes "
        "PORTRAIT warm cast.",
    ),
    "pref_color_key": (
        "0",
        "v4.0: natural color (0 = no cast).",
    ),
    # --- Neutral tone curve ---
    "pref_tone_curve_mode_key": (
        "-1",
        "v4.0: tone-curve mode default (-1, only proven value).",
    ),
    "pref_tonecurve_preset_key": (
        "0",
        "v4.0: neutral tone-curve preset (0 = standard).",
    ),
    # --- JPEG quality ---
    "pref_qjpg_key": (
        "97",
        "v4.0: JPEG 97 for clean compression without MTF loss.",
    ),
}

# name -> build definition.  Adding a variant here is the only step needed to
# make it buildable from the CLI (--variant NAME).
# Every variant inherits HIGH_RES_LAYER first, then its own delta overrides.
VARIANTS: "dict[str, dict]" = {
    "v3": {
        "stem": "LXX521_IMX682_LMC84_CALIBRATED_V3",
        "label": "V3 (noise-first — production config)",
        "calibration": {**HIGH_RES_LAYER, **V3_DELTA},
    },
    "night_bokeh": {
        "stem": "LXX521_IMX682_LMC84_V3_NIGHT_BOKEH",
        "label": "V3 night/bokeh (spatial denoise for low light)",
        "calibration": {**HIGH_RES_LAYER, **{**V3_DELTA,
                        "lib_spatiala_key": ("1", "Spatial denoise A on: extra NR for night/bokeh shadows."),
                        "lib_spatialdenmi2_key": ("1", "Spatial denoise B on: pairs with A for cleaner night shadows.")}},
    },
    "high_res": {
        "stem": "LXX521_IMX682_LMC84_V3_HIGH_RES",
        "label": "V3 high resolution (max 3264x2448, JPEG 97)",
        "calibration": {**HIGH_RES_LAYER, **V3_DELTA},
    },
    "bokeh_portrait_video_night": {
        "stem": "LXX521_IMX682_LMC84_V3_BOKEH_PORTRAIT_VIDEO_NIGHT",
        "label": "V3 bokeh/portrait/video + night (spatial denoise)",
        "calibration": {**HIGH_RES_LAYER, **{**V3_DELTA,
                        "lib_spatiala_key": ("1", "Spatial denoise A: cleaner bokeh and night shadows."),
                        "lib_spatialdenmi2_key": ("1", "Spatial denoise B: pairs with A for cleaner bokeh."),
                        "pref_Copmode_portrait_key": (
                            "1",
                            "Portrait mode on (bokeh depth effect).",
                        ),
                        "pref_opmode_portrait_key": (
                            "1",
                            "Portrait opmode on.",
                        ),
                        "pref_frames_hdr_key": (
                            "2",
                            "HDR burst 2 frames for low-light portrait stability.",
                        )}},
    },
    "iphone": {
        "stem": "LXX521_IMX682_LMC84_V3_IPHONE_LIKE",
        "label": "iPhone-like (natural colors, Smart HDR, moderate sharpening)",
        "calibration": {**HIGH_RES_LAYER, **IPHONE_DELTA},
    },
    "dslr": {
        "stem": "LXX521_IMX682_LMC84_V3_DSLR_LIKE",
        "label": "DSLR-like (minimal processing, raw-like, no sharpening/NR)",
        "calibration": {**HIGH_RES_LAYER, **DSLR_DELTA},
    },
    "pixel": {
        "stem": "LXX521_IMX682_LMC84_V3_PIXEL_LIKE",
        "label": "Pixel-like (HDR+ computational photography, Night Sight NR)",
        "calibration": {**HIGH_RES_LAYER, **PIXEL_DELTA},
    },
    "allinone": {
        "stem": "LXX521_IMX682_LMC84_V3_ALLINONE",
        "label": "All-in-one (balanced for all scenarios, safe proven values)",
        "calibration": {**HIGH_RES_LAYER, **ALLINONE_DELTA},
    },
    "dslr_64mp": {
        "stem": "LXX521_IMX682_LMC84_V3_DSLR_64MP",
        "label": "DSLR Ultra-Crisp & Full Resolution (NR off, sharpness off, neutral daylight AWB)",
        "calibration": {**HIGH_RES_LAYER, **DSLR_64MP_DELTA},
    },
    "dslr_max": {
        "stem": "LXX521_IMX682_LMC84_V3_DSLR_MAX",
        "label": "DSLR Ultra-Crisp MAXIMUM detail (NR off, sharpening at max proven, full resolution)",
        "calibration": {**HIGH_RES_LAYER, **DSLR_MAX_DELTA},
    },
    "iphone_max": {
        "stem": "LXX521_IMX682_LMC84_V3_IPHONE_MAX",
        "label": "iPhone MAX (max MP, low noise, crisp — natural colors, Smart HDR, gentle sharpness)",
        "calibration": {**HIGH_RES_LAYER, **IPHONE_MAX_DELTA},
    },
    "texture_first": {
        "stem": "LXX521_IMX682_LMC84_V4_TEXTURE_FIRST",
        "label": "V4 TEXTURE_FIRST (zero NR, zero sharpening, HDR burst off, neutral AWB, max MP)",
        "calibration": {**HIGH_RES_LAYER, **TEXTURE_FIRST_DELTA},
    },
}

OUTPUT_STEM = VARIANTS[DEFAULT_VARIANT]["stem"]
OUTPUT_XML = XML_DIR / f"{OUTPUT_STEM}.xml"
OUTPUT_STATUS = XML_DIR / f"{OUTPUT_STEM}.status.md"
OUTPUT_JSON = XML_DIR / f"{OUTPUT_STEM}.report.json"
OUTPUT_LABEL = VARIANTS[DEFAULT_VARIANT]["label"]

# Values that must never appear in the output (known crash / regression set).
STABILITY_LIMITS: "dict[str, object]" = {
    "pref_frames_hdr_key": ("0", "1", "2"),        # 8 and 12 overflow the burst buffer
    "pref_camera_hdr_plus_key": ("auto",),         # "enhanced" is crash-prone on IMX682
    "pref_hdrregion_key": ("0", "1", "2", "3", "4", "5"),  # 8 is the aggressive setting
    "pref_qjpg_key": ("90", "91", "92", "93", "94", "95", "96", "97"),
    "pref_color_key": ("0",),                      # -4 causes a heavy colour cast
    "pref_raw_key_main": ("0",),                   # RAW output adds memory pressure
    "lib_sharpgain_key": ("0", "0.5", "1.0", "1"),
    "lib_sharpnessb_key": ("0", "0.5", "1.02", "1.1"),
    "lib_sharpmini_key": ("0", "0.25", "0.5"),
    "lib_denoise_key": ("0", "1", "2"),
    "lib_lumadenoise_key": ("0", "1", "2"),
    "lib_denoisesmoothing_key": ("0", "1", "2"),
    "lib_spatiala_key": ("0", "1"),
    "lib_spatialdenmi2_key": ("0", "1"),
    "pref_awb_key": ("0", "1"),
}

STRING_RE = r'(<string name="{key}">)({old})(</string>)'


class BuildError(RuntimeError):
    """Raised when the generated profile fails a validation gate."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


SUFFIX_RE = re.compile(r"_(front|pro|ldr|[2-5])$")


def family_key(key: str) -> str:
    """Return the sensor-slot-independent stem of a per-camera key.

    ``cw_rg_key_front`` -> ``cw_rg_key``, ``lib_sharpgain_key_3`` ->
    ``lib_sharpgain_key``.  LMC uses the same value domain for every slot,
    so a value proven on the main sensor is valid for the front sensor.
    """
    return SUFFIX_RE.sub("", key)


def proven_values(key: str, exclude: Path) -> "set[str]":
    """Collect every value this repo has ever used for *key* or its family."""
    stem = family_key(key)
    values: "set[str]" = set()
    for path in sorted(XML_DIR.glob("*.xml")):
        if path.resolve() == exclude.resolve():
            continue
        params = parse_xml_params(path)
        for candidate, value in params.items():
            if candidate == key or family_key(candidate) == stem:
                values.add(str(value))
    return values


def apply_calibration(
    text: str, base_label: str, calibration: "dict[str, tuple[str, str]]"
) -> "tuple[str, list[dict]]":
    """Replace calibrated values in *text*; return new text and change log."""
    applied: "list[dict]" = []

    for key, (new_value, rationale) in calibration.items():
        pattern = re.compile(
            r'(<string name="' + re.escape(key) + r'">)([^<]*)(</string>)'
        )
        matches = pattern.findall(text)
        if len(matches) != 1:
            raise BuildError(
                f"{base_label}: key {key!r} found {len(matches)} time(s) in "
                f"the base profile (expected exactly 1)"
            )
        old_value = matches[0][1]

        if old_value == new_value:
            applied.append(
                {
                    "key": key,
                    "old": old_value,
                    "new": new_value,
                    "changed": False,
                    "rationale": rationale,
                }
            )
            continue

        proven = proven_values(key, OUTPUT_XML)
        if new_value not in proven:
            raise BuildError(
                f"{key}: value {new_value!r} has never been used by any "
                f"profile in this repo (known values: {sorted(proven)})"
            )

        text = pattern.sub(
            lambda m: m.group(1) + new_value + m.group(3), text, count=1
        )
        applied.append(
            {
                "key": key,
                "old": old_value,
                "new": new_value,
                "changed": True,
                "rationale": rationale,
            }
        )

    return text, applied


def validate(base_text: str, out_text: str, applied: "list[dict]") -> dict:
    """Run every structural and safety gate on the generated profile."""
    import xml.etree.ElementTree as ET

    import tempfile

    with tempfile.NamedTemporaryFile(
        "w", suffix=".xml", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(out_text)
        tmp_path = Path(tmp.name)

    try:
        root = ET.parse(tmp_path).getroot()
    except ET.ParseError as exc:
        raise BuildError(f"generated XML does not parse: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    if root.tag != "map":
        raise BuildError(f"root element is <{root.tag}>, expected <map>")

    base_params = parse_xml_params(Path(XML_DIR / BASE_NAME))
    out_params = parse_xml_params(OUTPUT_XML)

    base_keys, out_keys = set(base_params), set(out_params)
    if base_keys != out_keys:
        missing = sorted(base_keys - out_keys)
        added = sorted(out_keys - base_keys)
        raise BuildError(
            f"key set changed: missing={missing[:10]} added={added[:10]}"
        )

    # Duplicate keys break SharedPreferences semantics.
    names = [e.attrib.get("name") for e in root.iter("string")]
    names = [n for n in names if n]  # values inside <set> carry no name
    dups = sorted({n for n in names if names.count(n) > 1})
    if dups:
        raise BuildError(f"duplicate keys in output: {dups[:10]}")

    # Only calibrated keys may differ from the base.
    changed = {a["key"] for a in applied if a["changed"]}
    unexpected = sorted(
        k for k in base_keys if base_params[k] != out_params[k] and k not in changed
    )
    if unexpected:
        raise BuildError(f"unintended value changes: {unexpected[:10]}")

    # Stability limits.
    violations = []
    for key, allowed in STABILITY_LIMITS.items():
        if key in out_params and out_params[key] not in allowed:
            violations.append(
                f"{key}={out_params[key]!r} not in {list(allowed)}"
            )
    if violations:
        raise BuildError("stability guard failed: " + "; ".join(violations))

    # The <set> block must be preserved verbatim.
    if "<set name=\"pref_list_camera_key\">" not in out_text:
        raise BuildError("camera <set> block missing from output")

    return {
        "root": root.tag,
        "keys": len(out_keys),
        "duplicate_keys": 0,
        "changed_keys": sorted(changed),
        "unintended_changes": 0,
        "stability_violations": 0,
        "set_block_preserved": True,
        "xml_bytes": len(out_text.encode("utf-8")),
    }


def build(
    base: Path, dry_run: bool = False, calibration: "dict[str, tuple[str, str]] | None" = None
) -> dict:
    if not base.is_file():
        raise BuildError(f"base profile not found: {base}")

    base_text = base.read_text(encoding="utf-8")
    out_text, applied = apply_calibration(
        base_text,
        base.name,
        calibration or VARIANTS[DEFAULT_VARIANT]["calibration"],
    )

    # Pre-write so validate() can re-read the file from disk.
    if not dry_run:
        tmp = OUTPUT_XML.with_suffix(".xml.tmp")
        tmp.write_text(out_text, encoding="utf-8")
        tmp.replace(OUTPUT_XML)

    if dry_run:
        return {
            "dry_run": True,
            "applied": applied,
            "base_sha256": sha256_bytes(base_text.encode("utf-8")),
        }

    validation = validate(base_text, out_text, applied)

    report = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "base": base.name,
        "base_sha256": sha256_bytes(base_text.encode("utf-8")),
        "output": OUTPUT_XML.name,
        "output_sha256": sha256_bytes(out_text.encode("utf-8")),
        "applied": applied,
        "validation": validation,
        "device_validated": False,
    }
    return report


def write_status(report: dict) -> None:
    changed = [a for a in report["applied"] if a["changed"]]
    lines = [
        f"# LXX521 / Sony IMX682 — LMC 8.4 {OUTPUT_LABEL}",
        "",
        f"- Status: `BUILT_VALIDATED_NOT_DEVICE_VALIDATED`",
        f"- Generated: `{report['generated']}`",
        f"- Base: `{report['base']}` (device-exported, app-proven)",
        f"- Output: `{report['output']}`",
        f"- Base SHA-256: `{report['base_sha256']}`",
        f"- Output SHA-256: `{report['output_sha256']}`",
        f"- Keys: `{report['validation']['keys']}` (identical to base)",
        f"- Duplicate keys: `0`",
        f"- Keys changed: `{len(changed)}`",
        f"- XML parsing: PASS (`<map>` root)",
        f"- Stability guards: PASS",
        "",
        "## Calibration changes",
        "",
        "| Key | Old | New | Why |",
        "|-----|-----|-----|-----|",
    ]
    for a in changed:
        lines.append(
            f"| `{a['key']}` | `{a['old']}` | `{a['new']}` | {a['rationale']} |"
        )
    lines += [
        "",
        "## What is intentionally unchanged",
        "",
        "- Every key not listed above keeps the device-exported value: HDR burst",
        "  stays at 2 frames, the noise model stays on, denoise toggles stay on,",
        "  and AWB / grid / sound preferences are untouched.",
        "- The `<set>`-based camera list and the camera-slot suffixes",
        "  (`_2`, `_3`, `_front`, `_pro`) are untouched.",
        "- Portrait, depth and edge keys stay enabled (the \"safe\" profiles",
        "  disable them, which also disables portrait mode).",
        "- Key set, element order and the `pref_list_camera_key` set block are",
        "  byte-identical to the export, so the app cannot reject the profile",
        "  for unknown keys.",
        "",
        "## Limits",
        "",
        "Structural validation is not a photo-quality test. Shoot daylight,",
        "indoor, low-light and portrait shots after importing; keep the previous",
        "profile as fallback.",
        "",
    ]
    OUTPUT_STATUS.write_text("\n".join(lines), encoding="utf-8")


def deploy(report: dict, dest: Path) -> dict:
    target = check_deploy_target(dest)
    target.mkdir(parents=True, exist_ok=True)

    dest_file = target / OUTPUT_XML.name
    backup = None
    if dest_file.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = dest_file.with_suffix(f".xml.bak_{stamp}")
        shutil.copy2(dest_file, backup)

    shutil.copy2(OUTPUT_XML, dest_file)
    deployed_hash = sha256_bytes(dest_file.read_bytes())
    if deployed_hash != report["output_sha256"]:
        raise BuildError(
            f"deployed file hash mismatch: {deployed_hash} != {report['output_sha256']}"
        )

    return {
        "target": str(target),
        "file": str(dest_file),
        "backup": str(backup) if backup else None,
        "sha256": deployed_hash,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a calibrated, import-safe LMC 8.4 XML profile"
    )
    parser.add_argument(
        "--base",
        type=Path,
        default=XML_DIR / BASE_NAME,
        help="device-exported base profile (default: %(default)s)",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="also copy the profile to the phone's LMC directory",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=LMC_STORAGE_DIR,
        help="phone deploy directory (default: %(default)s; "
        "override with DCIM_LMC_DIR)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="show the delta without writing"
    )
    parser.add_argument(
        "--variant",
        choices=sorted(VARIANTS),
        default=DEFAULT_VARIANT,
        help="profile variant to build (default: %(default)s)",
    )
    args = parser.parse_args()

    global OUTPUT_STEM, OUTPUT_XML, OUTPUT_STATUS, OUTPUT_JSON, OUTPUT_LABEL
    variant = args.variant
    OUTPUT_STEM = VARIANTS[variant]["stem"]
    OUTPUT_LABEL = VARIANTS[variant]["label"]
    OUTPUT_XML = XML_DIR / f"{OUTPUT_STEM}.xml"
    OUTPUT_STATUS = XML_DIR / f"{OUTPUT_STEM}.status.md"
    OUTPUT_JSON = XML_DIR / f"{OUTPUT_STEM}.report.json"
    calibration = dict(VARIANTS[variant]["calibration"])

    try:
        report = build(args.base, dry_run=args.dry_run, calibration=calibration)
    except (BuildError, GuardError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[dry-run] base: {args.base}")
        for a in report["applied"]:
            flag = "CHANGE" if a["changed"] else "same  "
            print(f"  {flag} {a['key']}: {a['old']!r} -> {a['new']!r}")
        print("[dry-run] no files written")
        return 0

    write_status(report)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    v = report["validation"]
    print(f"built:   {OUTPUT_XML}")
    print(f"status:  {OUTPUT_STATUS}")
    print(f"report:  {OUTPUT_JSON}")
    print(f"sha256:  {report['output_sha256']}")
    print(
        f"checks:  root=<{v['root']}> keys={v['keys']} "
        f"dups={v['duplicate_keys']} changed={len(v['changed_keys'])} "
        f"unintended={v['unintended_changes']} "
        f"stability_violations={v['stability_violations']}"
    )

    if args.deploy:
        info = deploy(report, args.dest)
        print(f"deployed: {info['file']}")
        if info["backup"]:
            print(f"backup:   {info['backup']}")
        print(f"verified: {info['sha256']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
