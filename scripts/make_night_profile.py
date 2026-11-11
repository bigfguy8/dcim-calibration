#!/usr/bin/env python3
"""Generate ``LXX521_NIGHT.xml`` (handheld night profile) from ``LXX521_TEX.xml``.

MGC 8.9's settings map has no dedicated "night" namespace; night behaviour is
expressed through HDR+ frame stacking, in-loop denoise, exposure lift and
edge-aware sharpening suppression. ``LXX521_NIGHT`` keeps TEX's calibrated
white balance and colour rendering and changes only the keys that govern
low-light capture.

Target use case: **handheld city / nightscape photography** — no tripod, mixed
artificial light, deep shadows and small bright light sources.

The delta set is intentionally small and reviewable:

==========================================  ===========  ==========
Key family                                  TEX          NIGHT
==========================================  ===========  ==========
pref_camera_hdr_plus_key                    auto         enhanced
pref_frames_hdr_key*                        0            8
pref_noise_model_key*                       1            0
pref_hdrregion_key*                         5            6
lib_denoise_key*                            0            3
lib_denoisesmoothing_key*                   0            1
lib_lumadenoise_key*                        0            3
lib_lumanoise_key*                          1            3
lib_sharpgain_key*                          0            1
lib_sharpmini_key*                          0            1
lib_sharpnessb_key*                         0            1
lib_sharpnessnoisemodel_key*                1            0
lib_sharpeningedge_key*                     1            0
lib_hdrbrightness_key*                      0            1
lib_darkenlight_key*                        0            1
lib_lightfix_key*                           1            0
lib_exposure_key*                           0            1
lib_night_mode_gain_key*                    0            1
lib_nightmodeexposition_key*                0            1
pref_gamma_curve_mode_key*                  -1           0
==========================================  ===========  ==========

Every other key is copied verbatim, including TEX's ``cw_rg_key`` = 0.5725
so the calibrated IMX682 white balance is preserved.

Usage:
    python3 scripts/make_night_profile.py [--source PATH] [--output PATH] [--check]
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "configs" / "xml" / "LXX521_TEX.xml"
DEFAULT_OUTPUT = REPO_ROOT / "configs" / "xml" / "LXX521_NIGHT.xml"
STATUS_PATH = REPO_ROOT / "configs" / "xml" / "LXX521_NIGHT.status.md"

_SUFFIX = r"(?:_front|_pro|_ldr|_[2-9])?"


@dataclass(frozen=True)
class Delta:
    key: str
    old: str
    new: str
    rationale: str


DELTAS: tuple[Delta, ...] = (
    Delta(
        "pref_camera_hdr_plus_key", "auto", "enhanced",
        "force HDR+ enhanced so night frames are always merged",
    ),
    Delta(
        "pref_frames_hdr_key", "0", "8",
        "stack 8 frames to cut shot noise without a tripod",
    ),
    Delta(
        "pref_noise_model_key", "1", "0",
        "use the tuned denoiser instead of the generic noise model",
    ),
    Delta(
        "pref_hdrregion_key", "5", "6",
        "wider HDR region so shadows lift while lights stay controlled",
    ),
    Delta(
        "lib_denoise_key", "0", "3",
        "strong luma/chroma denoise at high ISO",
    ),
    Delta(
        "lib_denoisesmoothing_key", "0", "1",
        "smooth denoise transitions on flat night sky",
    ),
    Delta(
        "lib_lumadenoise_key", "0", "3",
        "luma denoise tuned for ISO 1600-6400 grain",
    ),
    Delta(
        "lib_lumanoise_key", "1", "3",
        "raise the luma noise threshold before detail is smoothed",
    ),
    Delta(
        "lib_sharpgain_key", "0", "1",
        "minimal post-denoise sharpening gain",
    ),
    Delta(
        "lib_sharpmini_key", "0", "1",
        "protect fine highlights (street lamps, neon) from halos",
    ),
    Delta(
        "lib_sharpnessb_key", "0", "1",
        "restore only low-level micro-contrast after denoise",
    ),
    Delta(
        "lib_sharpnessnoisemodel_key", "1", "0",
        "do not sharpen the estimated noise floor",
    ),
    Delta(
        "lib_sharpeningedge_key", "1", "0",
        "disable edge sharpening to avoid amplifying night grain",
    ),
    Delta(
        "lib_hdrbrightness_key", "0", "1",
        "lift midtones in the HDR merge for night ambience",
    ),
    Delta(
        "lib_darkenlight_key", "0", "1",
        "guard small bright sources against clipping",
    ),
    Delta(
        "lib_lightfix_key", "1", "0",
        "disable light-fix so point lights keep their real colour",
    ),
    Delta(
        "lib_exposure_key", "0", "1",
        "enable the night exposure bias path",
    ),
    Delta(
        "lib_night_mode_gain_key", "0", "1",
        "enable night-mode gain compensation",
    ),
    Delta(
        "lib_nightmodeexposition_key", "0", "1",
        "enable night-mode exposure adjustment",
    ),
    Delta(
        "pref_gamma_curve_mode_key", "-1", "0",
        "use the tone curve that preserves shadow detail at night",
    ),
)


def _pattern(key: str) -> re.Pattern[str]:
    return re.compile(
        rf'(<string name="{re.escape(key)}{_SUFFIX}">)([^<]*)(</string>)'
    )


def apply_deltas(source_text: str) -> tuple[str, list[dict[str, object]]]:
    changes: list[dict[str, object]] = []
    output = source_text
    for delta in DELTAS:
        pattern = _pattern(delta.key)
        applied: list[str] = []

        def replace(match: re.Match[str]) -> str:
            current = match.group(2)
            if current != delta.old:
                return match.group(0)
            name = re.search(r'name="([^"]+)"', match.group(1))
            if name:
                applied.append(name.group(1))
            return f"{match.group(1)}{delta.new}{match.group(3)}"

        output = pattern.sub(replace, output)
        if not applied:
            raise SystemExit(
                f"[-] {delta.key}: no key with value {delta.old!r} found in source"
            )
        changes.append(
            {
                "key": delta.key,
                "changed_keys": applied,
                "old": delta.old,
                "new": delta.new,
                "rationale": delta.rationale,
            }
        )
    return output, changes


def validate_profile(text: str) -> None:
    import xml.etree.ElementTree as ET

    root = ET.fromstring(text)
    if root.tag != "map":
        raise SystemExit(f"[-] unexpected root element: <{root.tag}>")
    if len(list(root)) < 100:
        raise SystemExit("[-] profile looks truncated (<100 keys)")
    for element in root:
        if "name" not in element.attrib:
            raise SystemExit(f"[-] element without name: <{element.tag}>")


def render_status(changes: list[dict[str, object]], source: Path) -> str:
    lines = [
        "# LXX521_NIGHT.xml - status",
        "",
        f"Derived from `{source.name}` by `scripts/make_night_profile.py`.",
        "Handheld city / nightscape profile for MGC 8.9 (BSG).",
        "",
        "## Deltas",
        "",
        "| Key family | TEX | NIGHT | Rationale |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for change in changes:
        lines.append(
            "| `{key}` | {old} | {new} | {why} |".format(
                key=change["key"],
                old=change["old"],
                new=change["new"],
                why=change["rationale"],
            )
        )
    lines.extend(
        [
            "",
            "## Preserved",
            "",
            "- `cw_rg_key*` = `0.5725` (calibrated IMX682 white balance)",
            "- `lib_saturation_key*` = `0.95` (no colour desaturation)",
            "- `lib_shadow_compensation_key*` = `0.95`",
            "- `lib_preservinghigh_key*` (highlight roll-off) unchanged",
            "- All lens, colour-matrix and tone-preset keys not listed above",
            "",
            "## Quality gates (night)",
            "",
            "- Mean luma 70-120 DN (night scenes are legitimately darker)",
            "- Highlight clipping < 2% (small bright sources)",
            "- Green sigma <= 15 DN @ ISO 3200",
            "- MTF50 center >= 0.18 cy/px, edge >= 0.12 cy/px (denoise costs acuity)",
            "- No visible colour cast: keep green/magenta balance neutral",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail (1) if the output is missing or differs from a fresh build",
    )
    args = parser.parse_args(argv)

    if not args.source.is_file():
        print(f"[-] source profile not found: {args.source}", file=sys.stderr)
        return 2

    source_text = args.source.read_text(encoding="utf-8")
    output_text, changes = apply_deltas(source_text)
    validate_profile(output_text)

    if args.check:
        if not args.output.is_file():
            print(f"[-] missing {args.output}", file=sys.stderr)
            return 1
        if args.output.read_text(encoding="utf-8") != output_text:
            print(f"[-] {args.output} is out of date", file=sys.stderr)
            return 1
        print(f"[*] {args.output.name} is up to date")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output_text, encoding="utf-8")
    STATUS_PATH.write_text(render_status(changes, args.source), encoding="utf-8")
    print(f"[*] wrote {args.output}")
    print(f"[*] wrote {STATUS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
