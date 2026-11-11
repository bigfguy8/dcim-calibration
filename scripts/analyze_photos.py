#!/usr/bin/env python3
"""
analyze_photos.py — Extract image resolution and color channel metrics
from DCIM capture images for LMC 8.4 calibration analysis.

Scans /sdcard/DCIM/Camera/ for JPEG/PNG images and reports:
- Image dimensions (width x height)
- Per-channel mean RGB values
- Overall exposure statistics
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

DCIM_DIR = Path("/sdcard/DCIM/Camera")


def analyze_image(path: Path) -> dict:
    """Analyze a single image: resolution + per-channel color stats."""
    img = Image.open(path).convert("RGB")
    width, height = img.size

    # Sample pixels efficiently for color stats
    pixels = list(img.getdata())
    total = len(pixels)

    r_sum = g_sum = b_sum = 0
    r2_sum = g2_sum = b2_sum = 0
    for r, g, b in pixels:
        r_sum += r
        g_sum += g
        b_sum += b
        r2_sum += r * r
        g2_sum += g * g
        b2_sum += b * b

    r_mean = r_sum / total
    g_mean = g_sum / total
    b_mean = b_sum / total

    r_var = r2_sum / total - r_mean * r_mean
    g_var = g2_sum / total - g_mean * g_mean
    b_var = b2_sum / total - b_mean * b_mean
    r_std = max(0.0, r_var) ** 0.5
    g_std = max(0.0, g_var) ** 0.5
    b_std = max(0.0, b_var) ** 0.5

    lum_mean = 0.299 * r_mean + 0.587 * g_mean + 0.114 * b_mean

    return {
        "filename": path.name,
        "width": width,
        "height": height,
        "r_mean": round(r_mean, 2),
        "g_mean": round(g_mean, 2),
        "b_mean": round(b_mean, 2),
        "r_std": round(r_std, 2),
        "g_std": round(g_std, 2),
        "b_std": round(b_std, 2),
        "lum_mean": round(lum_mean, 2),
        "file_size": int(path.stat().st_size),
    }


def analyze_directory(cam_dir: Path, limit: int | None = None) -> list[dict]:
    """Analyze all JPEG/PNG images in the directory, most recent first."""
    images = sorted(
        (
            f
            for f in cam_dir.iterdir()
            if f.is_file()
            and f.suffix.lower() in (".jpg", ".jpeg", ".png")
            and not f.name.startswith(".")
        ),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if limit is not None:
        images = images[:limit]

    results = []
    for img_path in images:
        try:
            results.append(analyze_image(img_path))
        except Exception as exc:  # noqa: BLE001
            print(f"WARNING: Failed to analyze {img_path.name}: {exc}")
    return results


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze DCIM camera images: resolution + color channel metrics"
    )
    parser.add_argument(
        "--camera-dir",
        default="/sdcard/DCIM/Camera",
        help="Directory containing camera images",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max number of most recent images to analyze (default: 20)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file path (default: print to stdout)",
    )
    args = parser.parse_args()

    cam_dir = Path(args.camera_dir)
    if not cam_dir.is_dir():
        print(f"ERROR: Camera directory not found: {cam_dir}")
        raise SystemExit(1)

    results = analyze_directory(cam_dir, args.limit)

    results.sort(key=lambda r: r["filename"])

    print("=== DCIM Camera Image Analysis ===")
    print(f"Directory: {cam_dir}")
    print(f"Images analyzed: {len(results)}")
    print()

    if results:
        print(f"{'Filename':<42} {'Size':<14} {'R':>6} {'G':>6} {'B':>6} {'Lum':>6}")
        print("-" * 85)
        for r in results:
            print(
                f"{r['filename'][:40]:<42} "
                f"{r['width']}x{r['height']:<7}"
                f"{r['r_mean']:>6.1f} {r['g_mean']:>6.1f} {r['b_mean']:>6.1f} "
                f"{r['lum_mean']:>6.1f}"
            )

        r_vals = [r["r_mean"] for r in results]
        g_vals = [r["g_mean"] for r in results]
        b_vals = [r["b_mean"] for r in results]
        lum_vals = [r["lum_mean"] for r in results]

        print()
        print("=== Aggregate Statistics ===")
        print(
            f"  R mean: {sum(r_vals)/len(r_vals):.2f} "
            f"(min={min(r_vals):.2f}, max={max(r_vals):.2f})"
        )
        print(
            f"  G mean: {sum(g_vals)/len(g_vals):.2f} "
            f"(min={min(g_vals):.2f}, max={max(g_vals):.2f})"
        )
        print(
            f"  B mean: {sum(b_vals)/len(b_vals):.2f} "
            f"(min={min(b_vals):.2f}, max={max(b_vals):.2f})"
        )
        print(
            f"  Lum mean: {sum(lum_vals)/len(lum_vals):.2f} "
            f"(min={min(lum_vals):.2f}, max={max(lum_vals):.2f})"
        )
        r_avg = sum(r_vals) / len(r_vals)
        b_avg = sum(b_vals) / len(b_vals)
        rb_ratio = r_avg / max(b_avg, 0.01)
        print(f"  R/B ratio: {rb_ratio:.3f}")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, indent=2))
        print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
