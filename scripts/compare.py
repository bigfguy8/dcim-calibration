#!/usr/bin/env python3
"""Side-by-side comparison of multiple ``analyze.py`` outputs.

    compare.py <a.json> <b.json> [<c.json> ...] [--out md|json]

Loads one or more analysis JSON files, groups records by
**profile x camera x ISO**, computes mean metrics per group, and prints a
side-by-side table with a per-metric delta (each file vs. the first) and a
gate verdict for every file.  Inputs are never mutated.

CLI
---
    python3 scripts/compare.py a.json b.json [--out md]   # markdown to stdout
    python3 scripts/compare.py a.json b.json --out json   # JSON to stdout
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import report  # noqa: E402

_METRICS = [
    ("mtf50_center", "MTF50 center (cy/px)", ">="),
    ("mtf50_edge", "MTF50 edge (cy/px)", ">="),
    ("noise_green", "Noise sigma G (DN)", "<="),
    ("mean_luma", "Mean luma (DN)", "range"),
    ("highlight_clipping_pct", "Highlight clip (%)", "<"),
    ("gray_patch_delta_e00", "Gray-patch deltaE00", "<="),
]


def _load_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return [r for r in payload["records"] if isinstance(r, dict)]
    if isinstance(payload, dict) and "file" in payload:
        return [payload]
    raise ValueError(f"cannot read records from {path}")


def _mean(values: list[float | None]) -> float | None:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return sum(clean) / len(clean) if clean else None


def _group_means(records: list[dict[str, Any]]) -> dict[tuple[str, str, int | None], dict[str, float | None]]:
    groups: dict[tuple[str, str, int | None], list[dict[str, Any]]] = {}
    for record in records:
        if record.get("status", "ok") != "ok":
            continue
        key = (
            str(record.get("profile") or "unknown"),
            str(record.get("camera") or "unknown"),
            int(float(record["iso"])) if record.get("iso") is not None else None,
        )
        groups.setdefault(key, []).append(record)

    out: dict[tuple[str, str, int | None], dict[str, float | None]] = {}
    for key, items in groups.items():
        noise = [(r.get("noise_sigma") or {}).get("g") for r in items]
        de = [(r.get("gray_patch") or {}).get("delta_e00") for r in items]
        out[key] = {
            "n": len(items),
            "mtf50_center": _mean(r.get("mtf50_center") for r in items),
            "mtf50_edge": _mean(r.get("mtf50_edge") for r in items),
            "noise_green": _mean(noise),
            "mean_luma": _mean(r.get("mean_luma") for r in items),
            "highlight_clipping_pct": _mean(r.get("highlight_clipping_pct") for r in items),
            "gray_patch_delta_e00": _mean(de),
        }
    return out


def _verdict(metric: str, value: float | None, gates: dict[str, Any]) -> str:
    if value is None or not math.isfinite(value):
        return "n/a"
    if metric == "mtf50_center":
        return "pass" if value >= gates["mtf50_center_min_cpp"] else "fail"
    if metric == "mtf50_edge":
        return "pass" if value >= gates["mtf50_edge_min_cpp"] else "fail"
    if metric == "noise_green":
        return "pass" if value <= gates["noise_green_iso100_max_dn"] else "fail"
    if metric == "mean_luma":
        return "pass" if gates["mean_luma_min"] <= value <= gates["mean_luma_max"] else "fail"
    if metric == "highlight_clipping_pct":
        return "pass" if value < gates["highlight_clipping_max_pct"] else "fail"
    if metric == "gray_patch_delta_e00":
        return "pass" if value <= gates["gray_patch_delta_e00_max"] else "fail"
    return "n/a"


def compare(inputs: list[Path]) -> dict[str, Any]:
    per_file: list[dict[str, Any]] = []
    day_gates, _night_gates = report.load_gates()
    gates = day_gates
    for path in inputs:
        records = _load_records(path)
        per_file.append({"path": str(path), "groups": _group_means(records)})

    all_keys: set[tuple[str, str, int | None]] = set()
    for entry in per_file:
        all_keys.update(entry["groups"].keys())

    rows: list[dict[str, Any]] = []
    for key in sorted(all_keys):
        profile, camera, iso = key
        for metric, label, _op in _METRICS:
            cells: list[dict[str, Any]] = []
            baseline = None
            for entry in per_file:
                value = entry["groups"].get(key, {}).get(metric)
                cells.append(
                    {"file": Path(entry["path"]).name, "value": value,
                     "verdict": _verdict(metric, value, gates)}
                )
                if baseline is None:
                    baseline = value
            delta = None
            if len(cells) > 1 and cells[-1]["value"] is not None and baseline is not None:
                delta = cells[-1]["value"] - baseline
            rows.append(
                {
                    "profile": profile,
                    "camera": camera,
                    "iso": iso,
                    "metric": metric,
                    "label": label,
                    "cells": cells,
                    "delta": delta,
                }
            )
    return {"schema_version": 1, "inputs": [str(p) for p in inputs],
            "gates": gates, "rows": rows}


def _fmt(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "n/a"
    return f"{value:.4f}"


def render_markdown(comp: dict[str, Any]) -> str:
    lines = ["# Profile comparison", ""]
    lines.append("Inputs: " + ", ".join(f"`{Path(i).name}`" for i in comp["inputs"]))
    lines.append("")
    if not comp["rows"]:
        lines.append("_No comparable groups._")
        return "\n".join(lines)
    header = ["Group", "Metric"] + [c["file"] for c in comp["rows"][0]["cells"]] + ["Delta", "Verdict"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join("---" for _ in header) + "|")
    for row in comp["rows"]:
        group = f"{row['profile']}/{row['camera']}/ISO {row['iso'] if row['iso'] is not None else 'n/a'}"
        vals = [_fmt(c["value"]) for c in row["cells"]]
        delta = _fmt(row["delta"]) if row["delta"] is not None else "n/a"
        verdicts = {c["verdict"] for c in row["cells"]}
        verdict = "fail" if "fail" in verdicts else ("pass" if verdicts == {"pass"} else "n/a")
        lines.append(
            "| " + " | ".join([group, row["label"]] + vals + [delta, verdict]) + " |"
        )
    lines.append("")
    return "\n".join(lines)


def render_json(comp: dict[str, Any]) -> str:
    return json.dumps(comp, indent=2) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Side-by-side comparison of analyze.py calibration outputs."
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="analysis.json file(s)")
    parser.add_argument(
        "--out", choices=["md", "json"], default="md",
        help="output format (default: markdown)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for p in args.inputs:
        if not p.is_file():
            print(f"[-] not found: {p}", file=sys.stderr)
            return 2
    comp = compare(list(args.inputs))
    text = render_markdown(comp) if args.out == "md" else render_json(comp)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
