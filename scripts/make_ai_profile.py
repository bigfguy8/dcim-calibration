#!/usr/bin/env python3
"""Generate ``LXX521_AI.xml`` (balanced variant) from ``LXX521_TEX.xml``.

MGC 8.9's settings map has no dedicated ML/AI key namespace, so the "AI"
profile is the *balanced* companion to the texture-first profile: it keeps
TEX's calibrated white balance and colour rendering, but enables multi-frame
merging, in-loop denoise and moderate sharpening so the auto/AI shooting
modes have a stable, less brittle baseline.

The delta set is intentionally small and reviewable:

==========================================  ===========  ==========
Key family                                  TEX          AI
==========================================  ===========  ==========
pref_frames_hdr_key*                        0            2
pref_qjpg_key                               97           95
lib_denoise_key*                            0            1
lib_denoisesmoothing_key*                   0            1
lib_lumadenoise_key*                        0            1
lib_sharpgain_key*                          0            1.0
lib_sharpmini_key*                          0            0.5
lib_sharpnessb_key*                         0            1.1
==========================================  ===========  ==========

Every other key is copied verbatim, including TEX's ``cw_rg_key`` = 0.5725
so the calibrated IMX682 white balance is preserved.

Usage:
    python3 scripts/make_ai_profile.py [--source PATH] [--output PATH] [--check]
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO_ROOT / "configs" / "xml" / "LXX521_TEX.xml"
DEFAULT_OUTPUT = REPO_ROOT / "configs" / "xml" / "LXX521_AI.xml"
STATUS_PATH = REPO_ROOT / "configs" / "xml" / "LXX521_AI.status.md"

_SUFFIX = r"(?:_front|_pro|_ldr|_[2-9])?"


@dataclass(frozen=True)
class Delta:
    key: str
    old: str
    new: str
    rationale: str


DELTAS: tuple[Delta, ...] = (
    Delta("pref_frames_hdr_key", "0", "2", "enable multi-frame HDR+ merge"),
    Delta("pref_qjpg_key", "97", "95", "smaller JPEGs, no visible quality loss"),
    Delta("lib_denoise_key", "0", "1", "enable luminance/chroma denoise"),
    Delta("lib_denoisesmoothing_key", "0", "1", "smooth denoise transitions"),
    Delta("lib_lumadenoise_key", "0", "1", "enable luma denoise at high ISO"),
    Delta("lib_sharpgain_key", "0", "1.0", "moderate post-denoise sharpening"),
    Delta("lib_sharpmini_key", "0", "0.5", "protect fine texture from halos"),
    Delta("lib_sharpnessb_key", "0", "1.1", "restore micro-contrast after denoise"),
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
        "# LXX521_AI.xml - status",
        "",
        f"Derived from `{source.name}` by `scripts/make_ai_profile.py`.",
        "Balanced companion to the V4.1 texture-first production profile.",
        "",
        "## Deltas",
        "",
        "| Key family | TEX | AI | Rationale |",
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
            "- All colour, tone-curve, HDR-region and lens keys not listed above",
            "",
            "## Quality gates",
            "",
            "- MTF50 center >= 0.30 cy/px, edge >= 0.22 cy/px",
            "- Mean luma 100-140 DN, highlight clipping < 1%",
            "- Green sigma <= 1.5 DN @ ISO 100 and <= 12 DN @ ISO 3200",
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
