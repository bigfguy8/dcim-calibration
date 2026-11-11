#!/usr/bin/env python3
"""check_clicked_photos.py — inspect photos shot with an LMC profile.

Extracts exposure metadata and measures the image-quality signals that matter
when tuning an LMC config:

* exposure: ISO, shutter, aperture, brightness
* noise: Immerkaer sigma, flat-block sigma (median + p90), per-luminance-band
* chroma noise: U/V standard deviation in flat blocks
* sharpness: Laplacian variance and normalised gradient energy
* colour: channel means, R/B ratio
* clipping: black/white percentages

Outputs JSON, CSV and downscaled previews so results can be compared across
config revisions.  Read-only with respect to the photo directory.

Usage
-----
    python3 scripts/check_clicked_photos.py
    python3 scripts/check_clicked_photos.py --dir /sdcard/DCIM/Camera --since 2026-11-11
    python3 scripts/check_clicked_photos.py --compare A.jpg B.jpg

Exit codes: 0 = ok, 2 = no photos found, 1 = error.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ExifTags

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core.paths import REPORTS_DIR  # noqa: E402

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
EXIF_TAGS = {v: k for k, v in ExifTags.TAGS.items()}
BLOCK = 32
FLAT_STD = 6.0


def exif_summary(path: Path) -> dict:
    """Return the exposure fields we tune against, tolerating missing EXIF."""
    out = {
        "iso": None,
        "exposure_s": None,
        "f_number": None,
        "brightness": None,
        "software": None,
        "datetime": None,
    }
    try:
        exif = Image.open(path).getexif()
        ifd = exif.get_ifd(0x8769)
    except Exception as exc:  # noqa: BLE001 - EXIF is best-effort
        print(f"  warning: EXIF unreadable for {path.name}: {exc}")
        return out

    def get(tag_name):
        tag = EXIF_TAGS.get(tag_name)
        if tag is None:
            return None
        return ifd.get(tag, exif.get(tag))

    iso = get("ISOSpeedRatings") or get("PhotographicSensitivity")
    exp = get("ExposureTime")
    try:
        out["iso"] = int(iso) if iso is not None else None
    except (TypeError, ValueError):
        out["iso"] = None
    try:
        if isinstance(exp, tuple) and len(exp) == 2 and exp[1]:
            out["exposure_s"] = round(exp[0] / exp[1], 5)
        elif exp is not None:
            out["exposure_s"] = round(float(exp), 5)
    except (TypeError, ValueError, ZeroDivisionError):
        out["exposure_s"] = None
    fnum = get("FNumber")
    try:
        out["f_number"] = round(float(fnum), 2) if fnum is not None else None
    except (TypeError, ValueError):
        out["f_number"] = None
    bright = get("BrightnessValue")
    try:
        out["brightness"] = round(float(bright), 2) if bright is not None else None
    except (TypeError, ValueError):
        out["brightness"] = None
    out["software"] = str(get("Software")) if get("Software") else None
    dt = get("DateTimeOriginal") or get("DateTime")
    out["datetime"] = str(dt) if dt else None
    return out


def flat_blocks(gray: np.ndarray) -> "list[tuple[float, float]]":
    """Return (mean_luminance, noise_sigma) for every flat block."""
    h, w = gray.shape
    blocks = []
    for y in range(0, h - BLOCK, BLOCK):
        for x in range(0, w - BLOCK, BLOCK):
            b = gray[y : y + BLOCK, x : x + BLOCK]
            if float(b.std()) < FLAT_STD:
                lap = cv2.Laplacian(b, cv2.CV_64F)
                blocks.append((float(b.mean()), float(lap.std() / np.sqrt(6.0))))
    return blocks


def immerkaer_sigma(gray: np.ndarray) -> float:
    """Fast global noise estimate (Immerkaer 1996)."""
    kernel = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=np.float64)
    conv = cv2.filter2D(gray.astype(np.float64), -1, kernel)
    return float(np.sqrt(np.pi / 2.0) * np.mean(np.abs(conv)) / 6.0)


def analyse(path: Path, preview_dir: Path) -> dict:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f"cannot decode {path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_f = gray.astype(np.float64)
    yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
    b, g, r = cv2.split(img.astype(np.float64))

    blocks = flat_blocks(gray)
    if blocks:
        noise = np.array([n for _, n in blocks])
        lum = np.array([m for m, _ in blocks])
        noise_med = float(np.median(noise))
        noise_p90 = float(np.percentile(noise, 90))
        chroma = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        cflat = np.zeros_like(gray, dtype=bool)
        cflat[:] = False
        for y in range(0, gray.shape[0] - BLOCK, BLOCK):
            for x in range(0, gray.shape[1] - BLOCK, BLOCK):
                blk = gray[y : y + BLOCK, x : x + BLOCK]
                if float(blk.std()) < FLAT_STD:
                    cflat[y : y + BLOCK, x : x + BLOCK] = True
        u_std = float(chroma[:, :, 1][cflat].std()) if cflat.any() else 0.0
        v_std = float(chroma[:, :, 2][cflat].std()) if cflat.any() else 0.0
        bands = {}
        for lo in range(0, 240, 40):
            mask = (lum >= lo) & (lum < lo + 40)
            bands[f"{lo}-{lo+40}"] = (
                round(float(np.median(noise[mask])), 2) if mask.any() else None
            )
    else:
        noise_med = noise_p90 = u_std = v_std = None
        bands = {}

    gx = cv2.Sobel(gray_f, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_f, cv2.CV_64F, 0, 1, ksize=3)
    grad = np.sqrt(gx * gx + gy * gy)
    grad_energy = float(np.mean(grad)) / max(float(gray_f.mean()), 1.0)

    h, w = gray.shape
    preview = cv2.resize(img, (max(1, w // 6), max(1, h // 6)),
                         interpolation=cv2.INTER_AREA)
    preview_path = preview_dir / f"preview_{path.stem}.jpg"
    cv2.imwrite(str(preview_path), preview, [cv2.IMWRITE_JPEG_QUALITY, 88])

    result = {
        "filename": path.name,
        "path": str(path),
        "width": int(w),
        "height": int(h),
        **exif_summary(path),
        "lum_mean": round(float(gray_f.mean()), 1),
        "lum_std": round(float(gray_f.std()), 1),
        "black_clip_pct": round(float((gray <= 5).mean() * 100), 2),
        "white_clip_pct": round(float((gray >= 250).mean() * 100), 2),
        "r_mean": round(float(r.mean()), 1),
        "g_mean": round(float(g.mean()), 1),
        "b_mean": round(float(b.mean()), 1),
        "rb_ratio": round(float(r.mean() / max(float(b.mean()), 1.0)), 3),
        "noise_immerkaer": round(immerkaer_sigma(gray), 3),
        "noise_flat_median": None if noise_med is None else round(noise_med, 3),
        "noise_flat_p90": None if noise_p90 is None else round(noise_p90, 3),
        "noise_by_luma": bands,
        "noise_over_lum": None
        if noise_med is None
        else round(noise_med / max(float(gray_f.mean()), 1.0), 5),
        "chroma_u_std": None if u_std is None else round(u_std, 2),
        "chroma_v_std": None if v_std is None else round(v_std, 2),
        "sharp_laplacian": round(float(cv2.Laplacian(gray_f, cv2.CV_64F).var()), 1),
        "grad_energy_per_lum": round(grad_energy, 4),
        "preview": str(preview_path),
    }
    return result


def parse_since(value: str | None) -> "datetime | None":
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"unrecognised --since value: {value!r}")


def collect(directory: Path, since: "datetime | None", limit: int) -> "list[Path]":
    if not directory.is_dir():
        raise FileNotFoundError(f"photo directory not found: {directory}")
    files = [
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]
    if since is not None:
        files = [p for p in files if datetime.fromtimestamp(p.stat().st_mtime) >= since]
    files.sort(key=lambda p: p.stat().st_mtime)
    return files[-limit:] if limit > 0 else files


def print_table(results: "list[dict]") -> None:
    header = (
        f"{'file':38} {'ISO':>5} {'exp':>6} {'lum':>5} {'noise':>6} "
        f"{'n/lum':>7} {'sharp':>7} {'R/B':>5} {'blk%':>5} {'wht%':>5}"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['filename'][:38]:38} "
            f"{str(r['iso'] or '-'):>5} "
            f"{str(r['exposure_s'] or '-'):>6} "
            f"{r['lum_mean']:>5} "
            f"{str(r['noise_flat_median'] if r['noise_flat_median'] is not None else '-'):>6} "
            f"{str(r['noise_over_lum'] if r['noise_over_lum'] is not None else '-'):>7} "
            f"{r['sharp_laplacian']:>7} "
            f"{r['rb_ratio']:>5} "
            f"{r['black_clip_pct']:>5} "
            f"{r['white_clip_pct']:>5}"
        )


def write_outputs(results: "list[dict]", out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "photo_check.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    keys = [
        "filename", "iso", "exposure_s", "f_number", "brightness",
        "width", "height", "lum_mean", "lum_std", "black_clip_pct",
        "white_clip_pct", "r_mean", "g_mean", "b_mean", "rb_ratio",
        "noise_immerkaer", "noise_flat_median", "noise_flat_p90",
        "noise_over_lum", "chroma_u_std", "chroma_v_std",
        "sharp_laplacian", "grad_energy_per_lum", "software", "datetime",
    ]
    with open(out_dir / "photo_check.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    print(f"json: {out_dir / 'photo_check.json'}")
    print(f"csv:  {out_dir / 'photo_check.csv'}")
    print(f"prev: {out_dir / 'previews'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure clicked photos")
    parser.add_argument("--dir", type=Path, default=Path("/sdcard/DCIM/Camera"))
    parser.add_argument("--since", default=None,
                        help="only files newer than YYYY-MM-DD [HH:MM]")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--outdir", type=Path, default=None)
    args = parser.parse_args()

    try:
        since = parse_since(args.since)
        files = collect(args.dir, since, args.limit)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if not files:
        print(f"no photos found in {args.dir}")
        return 2

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = args.outdir or (REPORTS_DIR / f"photo_check_{stamp}")
    preview_dir = out_dir / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for path in files:
        try:
            results.append(analyse(path, preview_dir))
            print(f"analysed: {path.name}")
        except (RuntimeError, OSError, cv2.error) as exc:
            print(f"  skip {path.name}: {exc}", file=sys.stderr)

    if not results:
        print("no analysable photos", file=sys.stderr)
        return 1

    print()
    print_table(results)
    write_outputs(results, out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
