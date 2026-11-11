#!/usr/bin/env python3
"""Aggregate ``analyze.py`` output into a calibration audit (Markdown + JSON).

Metrics are grouped by **profile x camera x ISO** and compared against the
provisional quality gates in the MGC 8.9 (BSG) specification:

======================  ==========================================
Gate                    Threshold
======================  ==========================================
MTF50 (center)          >= 0.30 cycles/px
MTF50 (peripheral edge) >= 0.22 cycles/px
Mean luma               100 - 140 (8-bit DN)
Highlight clipping      < 1.0 %
Green-channel sigma     <= 1.5 DN @ ISO 100, <= 12 DN @ ISO 3200
                        (log-linear interpolation between the two)
======================  ==========================================

CLI
---
    python3 scripts/report.py <analysis.json | directory> ... [-o OUTDIR]
                              [--title TEXT] [--fail-on-gate]

Both ``calibration_report.md`` and ``calibration_report.json`` are written to
``OUTDIR`` (default: ``analysis/reports``).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1

GATES: dict[str, Any] = {
    "mtf50_center_min_cpp": 0.30,
    "mtf50_edge_min_cpp": 0.22,
    "mean_luma_min": 100.0,
    "mean_luma_max": 140.0,
    "highlight_clipping_max_pct": 1.0,
    "noise_green_iso100_max_dn": 1.5,
    "noise_green_iso3200_max_dn": 12.0,
}

_METRIC_LABELS = {
    "mtf50_center": "MTF50 center (cy/px)",
    "mtf50_edge": "MTF50 edge (cy/px)",
    "noise_green": "Noise sigma G (DN)",
    "mean_luma": "Mean luma (DN)",
    "highlight_clipping_pct": "Highlight clip (%)",
}


# --------------------------------------------------------------------------- #
# Gate helpers
# --------------------------------------------------------------------------- #
def noise_gate(iso: float | None) -> float:
    """Log-linear green-noise threshold between ISO 100 and ISO 3200."""
    lo, hi = 100.0, 3200.0
    if iso is None or iso <= 0:
        return float(GATES["noise_green_iso100_max_dn"])
    iso = min(max(float(iso), lo), hi)
    fraction = math.log2(iso / lo) / math.log2(hi / lo)
    low = float(GATES["noise_green_iso100_max_dn"])
    high = float(GATES["noise_green_iso3200_max_dn"])
    return low * (high / low) ** fraction


def _mean(values: Iterable[float | None]) -> float | None:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return sum(clean) / len(clean) if clean else None


def _state(value: float | None, checks: list[tuple[str, bool]]) -> str:
    if value is None:
        return "n/a"
    return "pass" if all(ok for _, ok in checks) else "fail"


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_records(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    sources: list[str] = []

    def ingest(payload: Any, origin: str) -> None:
        if isinstance(payload, list):
            records.extend(item for item in payload if isinstance(item, dict))
        elif isinstance(payload, dict):
            if isinstance(payload.get("records"), list):
                records.extend(
                    item for item in payload["records"] if isinstance(item, dict)
                )
            elif "file" in payload:
                records.append(payload)
        sources.append(origin)

    for path in paths:
        if path.is_dir():
            candidates = sorted(path.glob("*.json"))
            if not candidates:
                raise FileNotFoundError(f"no JSON files in {path}")
        else:
            candidates = [path]
        for candidate in candidates:
            if candidate.name.startswith("calibration_report"):
                continue
            try:
                payload = json.loads(candidate.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(f"cannot read {candidate}: {exc}") from exc
            ingest(payload, str(candidate))
    return records, sources


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #
def _record_iso(record: dict[str, Any]) -> int | None:
    value = record.get("iso")
    try:
        return int(float(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


def build_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    analysed = [r for r in records if r.get("status", "ok") == "ok"]
    groups: dict[tuple[str, str, int | None], list[dict[str, Any]]] = defaultdict(list)
    for record in analysed:
        key = (
            str(record.get("profile") or "unknown"),
            str(record.get("camera") or "unknown"),
            _record_iso(record),
        )
        groups[key].append(record)

    group_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for (profile, camera, iso), items in sorted(
        groups.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2] or 0)
    ):
        mtf_center = _mean(r.get("mtf50_center") for r in items)
        mtf_edge = _mean(r.get("mtf50_edge") for r in items)
        noise_green = _mean(
            (r.get("noise_sigma") or {}).get("g") for r in items
        )
        mean_luma = _mean(r.get("mean_luma") for r in items)
        clip = _mean(r.get("highlight_clipping_pct") for r in items)
        shadow = _mean(r.get("shadow_clipping_pct") for r in items)
        threshold = noise_gate(iso)

        checks = {
            "mtf50_center": _state(
                mtf_center,
                [("mtf50_center", (mtf_center or 0) >= GATES["mtf50_center_min_cpp"])],
            ),
            "mtf50_edge": _state(
                mtf_edge,
                [("mtf50_edge", (mtf_edge or 0) >= GATES["mtf50_edge_min_cpp"])],
            ),
            "noise_green": _state(
                noise_green, [("noise_green", (noise_green or 0) <= threshold)]
            ),
            "mean_luma": _state(
                mean_luma,
                [
                    (
                        "mean_luma",
                        GATES["mean_luma_min"]
                        <= (mean_luma or 0)
                        <= GATES["mean_luma_max"],
                    )
                ],
            ),
            "highlight_clipping_pct": _state(
                clip,
                [("highlight_clipping", (clip or 0) < GATES["highlight_clipping_max_pct"])],
            ),
        }

        for metric, status in checks.items():
            if status == "fail":
                failures.append(
                    {
                        "profile": profile,
                        "camera": camera,
                        "iso": iso,
                        "metric": metric,
                        "label": _METRIC_LABELS[metric],
                    }
                )

        group_rows.append(
            {
                "profile": profile,
                "camera": camera,
                "iso": iso,
                "image_count": len(items),
                "mtf50_center": mtf_center,
                "mtf50_edge": mtf_edge,
                "noise_green": noise_green,
                "noise_gate": threshold,
                "mean_luma": mean_luma,
                "highlight_clipping_pct": clip,
                "shadow_clipping_pct": shadow,
                "checks": checks,
                "status": "pass"
                if all(status != "fail" for status in checks.values())
                else "fail",
            }
        )

    skipped = [r for r in records if r.get("status", "ok") != "ok"]
    return {
        "record_count": len(records),
        "analysed_count": len(analysed),
        "skipped_count": len(skipped),
        "groups": group_rows,
        "failures": failures,
        "overall_pass": not failures and bool(group_rows),
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def _fmt(value: float | None, digits: int = 2, suffix: str = "") -> str:
    if value is None or not math.isfinite(float(value)):
        return "n/a"
    return f"{float(value):.{digits}f}{suffix}"


def _badge(status: str) -> str:
    return {"pass": "PASS", "fail": "FAIL", "n/a": "n/a"}.get(status, status)


def render_markdown(
    summary: dict[str, Any],
    records: list[dict[str, Any]],
    sources: list[str],
    title: str,
    generated_at: str,
) -> str:
    lines: list[str] = [f"# {title}", ""]
    lines.append(f"Generated: `{generated_at}`  ")
    lines.append(
        f"Records: **{summary['record_count']}** "
        f"(analysed {summary['analysed_count']}, skipped {summary['skipped_count']})  "
    )
    lines.append(f"Sources: {', '.join(f'`{s}`' for s in sources)}")
    lines.append("")
    lines.append(
        "Overall: **PASS**" if summary["overall_pass"] else "Overall: **FAIL**"
    )
    lines.append("")

    lines.append("## Quality gates")
    lines.append("")
    lines.append("| Metric | Target |")
    lines.append("| :--- | :--- |")
    lines.append(f"| MTF50 center | >= {GATES['mtf50_center_min_cpp']:.2f} cy/px |")
    lines.append(f"| MTF50 edge | >= {GATES['mtf50_edge_min_cpp']:.2f} cy/px |")
    lines.append(
        f"| Mean luma | {GATES['mean_luma_min']:.0f} - "
        f"{GATES['mean_luma_max']:.0f} DN |"
    )
    lines.append(
        f"| Highlight clipping | < {GATES['highlight_clipping_max_pct']:.1f} % |"
    )
    lines.append(
        f"| Green sigma | <= {GATES['noise_green_iso100_max_dn']:.1f} DN @ ISO 100, "
        f"<= {GATES['noise_green_iso3200_max_dn']:.0f} DN @ ISO 3200 |"
    )
    lines.append("")

    lines.append("## Summary by profile / camera / ISO")
    lines.append("")
    if summary["groups"]:
        lines.append(
            "| Profile | Camera | ISO | n | MTF50 C | MTF50 E | sigma G | Gate | "
            "Luma | Clip | Status |"
        )
        lines.append(
            "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |"
        )
        for row in summary["groups"]:
            lines.append(
                "| {profile} | {camera} | {iso} | {n} | {mc} | {me} | {ng} | {gate} | "
                "{luma} | {clip} | {status} |".format(
                    profile=row["profile"],
                    camera=row["camera"],
                    iso=row["iso"] if row["iso"] is not None else "n/a",
                    n=row["image_count"],
                    mc=_fmt(row["mtf50_center"], 3),
                    me=_fmt(row["mtf50_edge"], 3),
                    ng=_fmt(row["noise_green"], 2),
                    gate=_fmt(row["noise_gate"], 2),
                    luma=_fmt(row["mean_luma"], 1),
                    clip=_fmt(row["highlight_clipping_pct"], 2, "%"),
                    status=_badge(row["status"]),
                )
            )
    else:
        lines.append("_No analysed records._")
    lines.append("")

    if summary["failures"]:
        lines.append("## Gate failures")
        lines.append("")
        for failure in summary["failures"]:
            lines.append(
                f"- **{failure['label']}** - profile `{failure['profile']}`, "
                f"camera `{failure['camera']}`, ISO {failure['iso']}"
            )
        lines.append("")

    if records:
        lines.append("## Per-image results")
        lines.append("")
        lines.append(
            "| File | Profile | Camera | ISO | MTF50 C | MTF50 E | sigma G | Luma | "
            "Clip | Status |"
        )
        lines.append(
            "| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |"
        )
        for record in records:
            noise = record.get("noise_sigma") or {}
            lines.append(
                "| {file} | {profile} | {camera} | {iso} | {mc} | {me} | {ng} | {luma} | "
                "{clip} | {status} |".format(
                    file=record.get("file", "?"),
                    profile=record.get("profile", "unknown"),
                    camera=record.get("camera", "unknown"),
                    iso=record.get("iso") if record.get("iso") is not None else "n/a",
                    mc=_fmt(record.get("mtf50_center"), 3),
                    me=_fmt(record.get("mtf50_edge"), 3),
                    ng=_fmt(noise.get("g"), 2),
                    luma=_fmt(record.get("mean_luma"), 1),
                    clip=_fmt(record.get("highlight_clipping_pct"), 2, "%"),
                    status=record.get("status", "ok"),
                )
            )
        lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Markdown + JSON calibration audit from analyze.py output."
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="analysis JSON or directory")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "analysis" / "reports",
        help="directory for calibration_report.{md,json}",
    )
    parser.add_argument("--title", default="MGC 8.9 Optical Calibration Audit")
    parser.add_argument(
        "--fail-on-gate", action="store_true", help="exit 1 when any gate fails"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        records, sources = load_records(args.inputs)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[-] {exc}", file=sys.stderr)
        return 2
    if not records:
        print("[-] no records found in the supplied inputs", file=sys.stderr)
        return 2

    summary = build_summary(records)
    generated_at = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "title": args.title,
        "sources": sources,
        "gates": GATES,
        "summary": summary,
        "records": records,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "calibration_report.json"
    md_path = args.output_dir / "calibration_report.md"
    json_path.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    md_path.write_text(
        render_markdown(summary, records, sources, args.title, generated_at) + "\n"
    )

    print(f"[*] report -> {md_path}")
    print(f"[*] data   -> {json_path}")
    print(
        "[*] overall: {}".format("PASS" if summary["overall_pass"] else "FAIL")
    )
    if args.fail_on_gate and not summary["overall_pass"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
