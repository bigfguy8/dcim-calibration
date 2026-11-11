"""OpenCV optical calibration metrics for the Sony IMX682.

Provides:
- EXIF extraction and exposure-value computation
- Scene classification (checkerboard vs. natural vs. possible chart)
- Slanted-edge MTF50 estimation (ISO 12233-style SFR)
- Laplacian-variance sharpness proxy

Refactored from imx682_opencv_calibration.py and upgrade_calibration.py.
"""
from __future__ import annotations

import csv
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import cv2  # type: ignore
except ImportError:  # Termux: OpenCV is optional; MTF fallbacks live in analyze.py
    cv2 = None  # type: ignore

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: E402
except ImportError:  # plotting is optional
    matplotlib = None  # type: ignore
    plt = None  # type: ignore
import numpy as np
from PIL import Image, ExifTags

from .logging import get_logger
from .paths import DATA_DIR, REPORTS_DIR

logger = get_logger()

IMG_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".tiff", ".tif", ".bmp"}


def find_images(root: Path | str) -> List[Path]:
    """Return sorted image paths under ``root``."""
    root = Path(root)
    out: List[Path] = []
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            if os.path.splitext(f)[1].lower() in IMG_EXTS:
                out.append(Path(dp) / f)
    return sorted(out)


def get_exif(path: Path | str) -> dict:
    """Extract EXIF tags from an image, returning {} on failure."""
    try:
        img = Image.open(path)
        exif = img._getexif()
        if not exif:
            return {}
        return {ExifTags.TAGS.get(tid, str(tid)): val for tid, val in exif.items()}
    except Exception:
        return {}


def exif_val(exif: dict, *keys: str):
    """Return the first matching EXIF value among ``keys``."""
    for k in keys:
        if k in exif:
            return exif[k]
    return None


def compute_ev(iso, exp_s) -> Optional[float]:
    """Compute exposure value from ISO and shutter seconds."""
    try:
        if iso and exp_s and exp_s > 0:
            return float(np.log2(100.0 / iso / exp_s))
    except Exception:
        pass
    return None


def classify_image(img_gray: np.ndarray):
    """Classify a grayscale image as checkerboard / possible chart / natural scene."""
    found, corners = cv2.findChessboardCorners(img_gray, (9, 6), None)
    if found:
        return "checkerboard_9x6", corners
    found, corners = cv2.findChessboardCorners(img_gray, (7, 5), None)
    if found:
        return "checkerboard_7x5", corners
    found, corners = cv2.findChessboardCorners(img_gray, (8, 6), None)
    if found:
        return "checkerboard_8x6", corners
    found, corners = cv2.findChessboardCorners(img_gray, (6, 8), None)
    if found:
        return "checkerboard_6x8", corners

    edges = cv2.Canny(img_gray, 50, 150)
    edge_density = float(np.sum(edges > 0) / edges.size)
    hist = cv2.calcHist([img_gray], [0], None, [256], [0, 256]).flatten()
    peaks = [
        i
        for i in range(1, 255)
        if hist[i] > hist[i - 1]
        and hist[i] > hist[i + 1]
        and hist[i] > np.mean(hist) * 2
    ]
    is_chart = edge_density > 0.08 and len(peaks) >= 2
    return ("possible_chart" if is_chart else "natural_scene"), None


# --- Slanted-edge MTF50 -----------------------------------------------------


def detect_slanted_edge_roi(gray: np.ndarray):
    """Auto-detect the strongest slanted edge in a grayscale image.

    Returns a dict with roi (x, y, w, h), angle_deg, strength, edge_px;
    or None when no confident slanted edge is present.
    """
    h, w = gray.shape
    if min(h, w) < 64:
        return None
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(gx * gx + gy * gy)
    edge_ang = (np.degrees(np.arctan2(gy, gx)) + 90.0) % 180.0

    thr = np.percentile(mag, 96)
    mask = mag > thr
    if mask.sum() < 40:
        return None

    bins = np.linspace(0, 180, 37)
    hist, _ = np.histogram(edge_ang[mask], bins=bins, weights=mag[mask])
    total = float(hist.sum())
    if total <= 0:
        return None
    best = int(np.argmax(hist))
    strength = float(hist[best] / total)
    if strength < 0.30:
        return None
    ang = float((bins[best] + bins[best + 1]) / 2.0)

    d = np.abs(edge_ang - ang)
    d = np.minimum(d, 180.0 - d)
    emask = mask & (d <= 25.0)
    ys, xs = np.nonzero(emask)
    if len(xs) < 60:
        return None
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    pad = 32
    x = max(0, x0 - pad)
    y = max(0, y0 - pad)
    rw = min(w, x1 + pad) - x
    rh = min(h, y1 + pad) - y
    return {
        "roi": (x, y, rw, rh),
        "angle_deg": ang,
        "strength": strength,
        "edge_px": int(len(xs)),
    }


def slanted_edge_mtf50(gray: np.ndarray, roi=None, oversample: int = 8):
    """Estimate MTF50 (cyc/px) from a slanted edge (ISO 12233-style SFR).

    Returns a dict with mtf50_cyc_px, mtf50_reached, frequencies, mtf,
    edge_angle_deg, roi; or None when no usable edge is found.
    """
    h, w = gray.shape
    if roi is None:
        det = detect_slanted_edge_roi(gray)
        if det is None:
            return None
        roi = det["roi"]
        angle = det["angle_deg"]
    else:
        x, y, rw, rh = [int(v) for v in roi]
        sub = gray[y : y + rh, x : x + rw]
        if sub.size == 0:
            return None
        gx = cv2.Sobel(sub, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(sub, cv2.CV_64F, 0, 1, ksize=3)
        mag = np.sqrt(gx * gx + gy * gy)
        edge_ang = (np.degrees(np.arctan2(gy, gx)) + 90.0) % 180.0
        thr = np.percentile(mag, 96)
        mask = mag > thr
        if mask.sum() < 20:
            return None
        bins = np.linspace(0, 180, 37)
        hist, _ = np.histogram(edge_ang[mask], bins=bins, weights=mag[mask])
        total = float(hist.sum())
        if total <= 0:
            return None
        best = int(np.argmax(hist))
        if float(hist[best] / total) < 0.25:
            return None
        angle = float((bins[best] + bins[best + 1]) / 2.0)

    x, y, rw, rh = [int(v) for v in roi]
    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))
    rw = max(1, min(rw, w - x))
    rh = max(1, min(rh, h - y))
    if rw < 16 or rh < 16:
        return None

    crop = gray[y : y + rh, x : x + rw].astype(np.float64)
    gx = cv2.Sobel(crop, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(crop, cv2.CV_64F, 0, 1, ksize=3)

    th = np.radians(angle)
    tx, ty = np.cos(th), np.sin(th)
    nx, ny = -np.sin(th), np.cos(th)
    cy_, cx_ = rh / 2.0, rw / 2.0
    yy, xx = np.mgrid[0:rh, 0:rw]
    t = (xx - cx_) * tx + (yy - cy_) * ty
    n = (xx - cx_) * nx + (yy - cy_) * ny
    gn = gx * nx + gy * ny

    t_min, t_max = float(t.min()), float(t.max())
    n_cols = max(8, int(rw / 4))
    t_edges = np.linspace(t_min, t_max, n_cols + 1)

    samples = []
    for i in range(n_cols):
        m = (t >= t_edges[i]) & (t < t_edges[i + 1])
        if m.sum() < 3:
            continue
        col_n = n[m]
        col_i = crop[m]
        col_gn = gn[m]
        pk = int(np.argmax(np.abs(col_gn)))
        n_edge = float(col_n[pk])
        m2 = (col_n >= n_edge - 2.0) & (col_n <= n_edge + 2.0)
        if m2.sum() >= 3:
            wts = np.abs(col_gn[m2])
            if wts.sum() > 0:
                n_edge = float(np.sum(col_n[m2] * wts) / wts.sum())
        rel = col_n - n_edge
        phase = rel * oversample
        for jj in range(len(rel)):
            samples.append((int(np.floor(phase[jj])), float(col_i[jj])))

    if len(samples) < 20:
        return None

    buckets = {}
    for b, val in samples:
        buckets.setdefault(b, []).append(val)
    bmin, bmax = min(buckets), max(buckets)
    esf_profile = np.array(
        [float(np.mean(buckets.get(b, [np.nan]))) for b in range(bmin, bmax + 1)]
    )
    valid = ~np.isnan(esf_profile)
    if valid.sum() < 10:
        return None
    idx = np.arange(len(esf_profile))
    esf_profile = np.interp(idx, idx[valid], esf_profile[valid])

    lsf = np.diff(esf_profile)
    win = np.hanning(len(lsf))
    lsf_w = lsf * win
    n_fft = 1 << (int(len(lsf_w)) - 1).bit_length()
    spectrum = np.fft.rfft(lsf_w, n=n_fft)
    mtf = np.abs(spectrum)
    if mtf[0] > 0:
        mtf = mtf / mtf[0]
    freqs = np.fft.rfftfreq(n_fft, d=1.0 / oversample)
    pos = freqs > 0
    freqs = freqs[pos]
    mtf = mtf[pos]

    mtf50 = None
    if mtf.size >= 2 and mtf[0] >= 0.5:
        below = np.where(mtf <= 0.5)[0]
        if below.size:
            i = int(below[0])
            if i == 0:
                mtf50 = float(freqs[0])
            else:
                m0, m1 = float(mtf[i - 1]), float(mtf[i])
                f0, f1 = float(freqs[i - 1]), float(freqs[i])
                if m1 != m0:
                    mtf50 = f0 + (0.5 - m0) * (f1 - f0) / (m1 - m0)
                else:
                    mtf50 = f0

    return {
        "mtf50_cyc_px": float(mtf50) if mtf50 is not None else None,
        "mtf50_reached": mtf50 is not None,
        "frequencies": freqs.tolist(),
        "mtf": mtf.tolist(),
        "edge_angle_deg": float(angle),
        "roi": [x, y, rw, rh],
    }


# --- Sharpness proxy --------------------------------------------------------


def sharpness_laplacian(gray: np.ndarray) -> float:
    """Laplacian-variance sharpness proxy (higher = sharper)."""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


# --- Image analysis ---------------------------------------------------------


def analyze_image(path: Path | str) -> Optional[dict]:
    """Produce a metric dictionary for a single image."""
    path = Path(path)
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        logger.warning("Could not read image: %s", path)
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    exif = get_exif(path)
    iso = exif_val(exif, "ISOSpeedRatings", "PhotographicSensitivity")
    try:
        iso = int(iso) if iso else None
    except (TypeError, ValueError):
        iso = None
    exp_str = exif_val(exif, "ExposureTime")
    try:
        exp_s = exp_str[0] / exp_str[1] if isinstance(exp_str, tuple) else float(exp_str)
    except (TypeError, ValueError, ZeroDivisionError):
        exp_s = None
    ev = compute_ev(iso, exp_s)

    lum = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)[:, :, 0]
    lum_mean = float(np.mean(lum))
    lum_std = float(np.std(lum))
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges > 0) / edges.size)
    black_clip = float(np.sum(gray <= 5) / gray.size * 100)
    white_clip = float(np.sum(gray >= 250) / gray.size * 100)

    b, g, r = cv2.split(img)
    rb_ratio = float(np.mean(r) / np.mean(b)) if np.mean(b) > 0 else 0.0
    rg_diff = float(np.mean(r) - np.mean(g))

    cls, corners = classify_image(gray)
    mtf_result = slanted_edge_mtf50(gray)
    mtf50 = mtf_result["mtf50_cyc_px"] if mtf_result else None
    if mtf_result:
        mtf50_status = (
            "ESTIMATE: slanted-edge SFR (ISO 12233-style), not chart-certified"
        )
    else:
        mtf50_status = (
            "NOT_MEASURED: no confident slanted edge found; validated chart "
            "SFR required for absolute MTF50"
        )

    return {
        "filename": path.name,
        "path": str(path),
        "width": w,
        "height": h,
        "iso": iso,
        "exposure_s": exp_s,
        "ev": ev,
        "f_number": exif_val(exif, "FNumber"),
        "focal_length": exif_val(exif, "FocalLength"),
        "software": exif_val(exif, "Software"),
        "datetime": exif_val(exif, "DateTime"),
        "lum_mean": lum_mean,
        "lum_std": lum_std,
        "edge_density": edge_density,
        "black_clip_pct": black_clip,
        "white_clip_pct": white_clip,
        "rb_ratio": rb_ratio,
        "rg_diff": rg_diff,
        "classification": cls,
        "mtf50_cyc_px": mtf50,
        "mtf50_status": mtf50_status,
        "sharpness_laplacian": sharpness_laplacian(gray),
        "has_checkerboard": corners is not None,
        "corner_count": len(corners) if corners is not None else 0,
    }


def analyze_image_dir(
    batch_dir: Path | str,
    output_dir: Path | str | None = None,
    save_json: bool = True,
    save_csv: bool = True,
    make_plots: bool = True,
) -> List[dict]:
    """Run the full calibration analysis over every image in ``batch_dir``.

    Returns the list of result dicts. Optionally writes JSON, CSV, and
    plots to ``output_dir`` (defaults to ``analysis/data/``).
    """
    batch_dir = Path(batch_dir)
    out_dir = Path(output_dir) if output_dir else DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    images = find_images(batch_dir)
    logger.info("Found %d images in %s", len(images), batch_dir)

    results: List[dict] = []
    cb_images: List[Path] = []
    cb_corners_list = []
    cb_objpoints = []

    CB_COLS, CB_ROWS = 9, 6
    objp = np.zeros((CB_COLS * CB_ROWS, 3), np.float32)
    objp[:, :2] = np.mgrid[0:CB_COLS, 0:CB_ROWS].T.reshape(-1, 2)

    for i, path in enumerate(images):
        logger.info("[%d/%d] %s", i + 1, len(images), path.name)
        r = analyze_image(path)
        if r is None:
            continue
        results.append(r)
        mtf_text = f"{r['mtf50_cyc_px']:.4f}" if r["mtf50_cyc_px"] is not None else "NOT MEASURED"
        logger.info(
            "  %s | EV=%s | MTF50=%s | edge=%.3f%% | sharp=%.2f",
            r["classification"],
            r["ev"],
            mtf_text,
            r["edge_density"] * 100,
            r["sharpness_laplacian"],
        )
        if r["has_checkerboard"]:
            img_gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            ret, corners = cv2.findChessboardCorners(img_gray, (CB_COLS, CB_ROWS), None)
            if ret:
                criteria = (
                    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                    30,
                    0.001,
                )
                corners = cv2.cornerSubPix(img_gray, corners, (11, 11), (-1, -1), criteria)
                cb_corners_list.append(corners)
                cb_objpoints.append(objp.copy())
                cb_images.append(path)

    # ---- intrinsic calibration -------------------------------------------
    calib_result = None
    if len(cb_images) >= 3:
        logger.info(
            "Running intrinsic calibration on %d checkerboard images...",
            len(cb_images),
        )
        img_shape = cv2.imread(str(cb_images[0]), cv2.IMREAD_GRAYSCALE).shape[::-1]
        ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(
            cb_objpoints, cb_corners_list, img_shape, None, None
        )
        calib_result = {
            "num_images": len(cb_images),
            "rms_reprojection_error": float(ret),
            "camera_matrix": K.tolist(),
            "distortion_coefficients": dist.tolist()[0] if dist is not None else [],
            "image_size": list(img_shape),
        }
        per_img_errors = []
        for i in range(len(cb_images)):
            imgpoints2, _ = cv2.projectPoints(cb_objpoints[i], rvecs[i], tvecs[i], K, dist)
            err = cv2.norm(cb_corners_list[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            per_img_errors.append(float(err))
        calib_result["per_image_reprojection_error"] = per_img_errors
        calib_result["images_used"] = [p.name for p in cb_images]
        calib_path = out_dir / "intrinsic_calibration.json"
        calib_path.write_text(json.dumps(calib_result, indent=2), encoding="utf-8")
        logger.info("Saved: %s", calib_path)
        logger.info("RMS reprojection error: %.4f", ret)
    else:
        logger.info(
            "Only %d checkerboard images found — need >=3 for intrinsic calibration",
            len(cb_images),
        )

    # ---- persist outputs --------------------------------------------------
    if save_json and results:
        json_path = out_dir / "calibration_results.json"
        json_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
        logger.info("Saved: %s", json_path)
    if save_csv and results:
        csv_path = out_dir / "calibration_metrics.csv"
        keys = list(results[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in results:
                w.writerow(r)
        logger.info("Saved: %s", csv_path)

    if make_plots:
        _make_plots(results, out_dir)

    # ---- summary ----------------------------------------------------------
    logger.info("=== SUMMARY ===")
    logger.info("Total images: %d", len(results))
    cls_counts = Counter(r["classification"] for r in results)
    for cls, n in cls_counts.items():
        logger.info("  %s: %d", cls, n)
    logger.info("Checkerboard images: %d", len(cb_images))
    if calib_result:
        logger.info("Calibration RMS error: %.4f", calib_result["rms_reprojection_error"])
    measured = sum(1 for r in results if r["mtf50_cyc_px"] is not None)
    logger.info("MTF50 measured: %d/%d images", measured, len(results))
    logger.info("All outputs in: %s", out_dir)

    return results


def _make_plots(results: List[dict], out_dir: Path) -> None:
    """Generate MTF50 comparison and exposure-vs-clipping plots."""
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        names = [r["filename"][:20] for r in results]
        mtfs = [r["mtf50_cyc_px"] if r["mtf50_cyc_px"] is not None else 0.0 for r in results]
        colors = ["green" if r["has_checkerboard"] else "gray" for r in results]
        ax.barh(range(len(names)), mtfs, color=colors)
        measured = sum(1 for r in results if r["mtf50_cyc_px"] is not None)
        ax.text(
            0.5,
            0.5,
            f"MTF50 (cyc/px): {measured}/{len(results)} images measured "
            "(slanted-edge estimate, not chart-certified)",
            transform=ax.transAxes,
            ha="center",
            va="center",
            wrap=True,
        )
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=6)
        ax.set_xlabel("MTF50 (cyc/px)")
        ax.set_title("MTF50 Comparison — All Images")
        plt.tight_layout()
        plt.savefig(plots_dir / "mtf50_comparison.png", dpi=100)
        plt.close()
        logger.info("Saved MTF50 plot")
    except Exception as exc:
        logger.warning("MTF50 plot error: %s", exc)

    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        evs = [r["ev"] for r in results if r["ev"]]
        clips = [r["black_clip_pct"] for r in results if r["ev"]]
        ax.scatter(evs, clips, c="blue", alpha=0.6)
        ax.set_xlabel("EV")
        ax.set_ylabel("Black Clip %")
        ax.set_title("Exposure vs Black Clipping")
        plt.tight_layout()
        plt.savefig(plots_dir / "exposure_vs_clipping.png", dpi=100)
        plt.close()
        logger.info("Saved exposure plot")
    except Exception as exc:
        logger.warning("Exposure plot error: %s", exc)


__all__ = [
    "find_images",
    "get_exif",
    "exif_val",
    "compute_ev",
    "classify_image",
    "detect_slanted_edge_roi",
    "slanted_edge_mtf50",
    "sharpness_laplacian",
    "analyze_image",
    "analyze_image_dir",
]
