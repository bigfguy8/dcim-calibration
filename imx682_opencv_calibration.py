#!/usr/bin/env python3
"""
IMX682 OpenCV Camera Calibration Pipeline
Uses OpenCV for checkerboard detection, intrinsic calibration, distortion estimation.
Falls back to PIL for images without cv2-compatible formats.
OpenCV, numpy, and matplotlib are optional dependencies.
"""

from __future__ import annotations

import os, sys, json, csv, argparse, hashlib, glob
from datetime import datetime

#
# Optional dependencies — never crash the import or unrelated workflows.
#
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import numpy as np
    NP_AVAILABLE = True
except ImportError:
    NP_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    PLT_AVAILABLE = True
except ImportError:
    PLT_AVAILABLE = False

from PIL import Image, ExifTags

CALIB_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_EXTS = {'.jpg','.jpeg','.png','.heic','.heif','.webp','.tiff','.tif','.bmp'}

def find_images(root):
    out = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if os.path.splitext(f)[1].lower() in IMG_EXTS:
                out.append(os.path.join(dp, f))
    return sorted(out)

def get_exif(path):
    try:
        img = Image.open(path)
        exif = img._getexif()
        if not exif: return {}
        out = {}
        for tid, val in exif.items():
            tag = ExifTags.TAGS.get(tid, str(tid))
            out[tag] = val
        return out
    except Exception:
        return {}

def exif_val(exif, *keys):
    for k in keys:
        if k in exif: return exif[k]
    return None

def compute_ev(iso, exp_s):
    try:
        if NP_AVAILABLE:
            return np.log2(100.0 / iso / exp_s) if iso and exp_s and exp_s>0 else None
        else:
            # Fallback: manual log2 computation without numpy
            import math
            return math.log2(100.0 / iso / exp_s) if iso and exp_s and exp_s>0 else None
    except: return None

def classify_image(img_gray):
    """Classify as checkerboard or natural scene using OpenCV.

    Falls back to a heuristic based on image statistics when OpenCV is
    unavailable.  No new images are captured.
    """
    if CV2_AVAILABLE:
        # Try to find checkerboard pattern
        found, corners = cv2.findChessboardCorners(img_gray, (9,6), None)
        if found:
            return "checkerboard_9x6", corners
        found, corners = cv2.findChessboardCorners(img_gray, (7,5), None)
        if found:
            return "checkerboard_7x5", corners
        found, corners = cv2.findChessboardCorners(img_gray, (8,6), None)
        if found:
            return "checkerboard_8x6", corners
        found, corners = cv2.findChessboardCorners(img_gray, (6,8), None)
        if found:
            return "checkerboard_6x8", corners
        # Heuristic: high edge density + bimodal histogram = possible chart
        edges = cv2.Canny(img_gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        hist = cv2.calcHist([img_gray],[0],None,[256],[0,256]).flatten()
        # bimodality: two peaks
        peaks = []
        for i in range(1,255):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1] and hist[i] > np.mean(hist)*2:
                peaks.append(i)
        is_chart = edge_density > 0.08 and len(peaks) >= 2
        return ("possible_chart" if is_chart else "natural_scene"), None
    else:
        # Fallback without OpenCV: use PIL-based heuristics
        try:
            width, height = img_gray.shape
            # Compute simple gradient magnitude
            pixels = list(img_gray.getdata())
            edge_count = 0
            for y in range(1, height-1):
                for x in range(1, width-1):
                    p = pixels[y*width + x]
                    left = pixels[y*width + (x-1)]
                    right = pixels[y*width + (x+1)]
                    top = pixels[(y-1)*width + x]
                    bottom = pixels[(y+1)*width + x]
                    g = abs(p - ((left + right + top + bottom) // 4))
                    if g > 50:
                        edge_count += 1
            edge_density = edge_count / ((height-2) * (width-2)) if (height>2 and width>2) else 0
            # Simple histogram bimodality
            hist_vals = [0]*256
            for p in pixels:
                hist_vals[p] += 1
            peaks = sum(1 for i in range(1,255) if hist_vals[i] > hist_vals[i-1] and hist_vals[i] > hist_vals[i+1] and hist_vals[i] > sum(hist_vals)//10)
            is_chart = edge_density > 0.08 and peaks >= 2
            return ("possible_chart" if is_chart else "natural_scene"), None
        except Exception:
            return "natural_scene", None

def analyze_image(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR) if CV2_AVAILABLE else None
    if img is None:
        # Try PIL fallback
        try:
            from PIL import Image
            img = Image.open(path)
            if img is None:
                return None
        except Exception:
            return None

    # Convert to grayscale if we have cv2
    gray = None
    if CV2_AVAILABLE and img is not None:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if hasattr(cv2, 'COLOR_BGR2GRAY') else None
    elif img is not None and hasattr(img, 'convert'):
        # PIL image
        try:
            gray = img.convert('L')
        except Exception:
            gray = None
    else:
        gray = None

    h, w = 0, 0
    if gray is not None:
        h, w = gray.shape
    elif img is not None:
        w, h = img.size if hasattr(img, 'size') else (0, 0)

    exif = get_exif(path)
    iso = exif_val(exif, 'ISOSpeedRatings', 'PhotographicSensitivity')
    try: iso = int(iso) if iso else None
    except: iso = None
    exp_str = exif_val(exif, 'ExposureTime')
    try:
        if isinstance(exp_str, tuple): exp_s = exp_str[0]/exp_str[1]
        else: exp_s = float(exp_str)
    except: exp_s = None
    ev = compute_ev(iso, exp_s)

    # Metrics (all guarded)
    lum_mean = None
    lum_std = None
    edge_density = None
    black_clip = None
    white_clip = None
    rb_ratio = None
    rg_diff = None

    if CV2_AVAILABLE and gray is not None:
        # Lum metrics
        lum = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2YUV)[:,:,0] if img is not None else np.array(gray)
        if NP_AVAILABLE and lum.size > 0:
            lum_mean = float(np.mean(lum))
            lum_std = float(np.std(lum))
        # Edge metrics
        edges = cv2.Canny(gray, 50, 150)
        if NP_AVAILABLE:
            edge_density = float(np.sum(edges>0)/edges.size)
        if NP_AVAILABLE:
            black_clip = float(np.sum(gray <= 5)/gray.size*100)
            white_clip = float(np.sum(gray >= 250)/gray.size*100)
        # Color metrics
        b,g,r = cv2.split(img) if img is not None else (0,0,0)
        if NP_AVAILABLE:
            rb_ratio = float(np.mean(r)/np.mean(b)) if np.mean(b)>0 else 0
            rg_diff = float(np.mean(r)-np.mean(g))
    elif gray is not None and img is not None and hasattr(img, 'convert'):
        # PIL fallback for lum/color
        try:
            lum_img = img.convert('L')
            pixels = list(lum_img.getdata())
            if pixels:
                mean_val = sum(pixels) / len(pixels)
                variance = sum((p - mean_val) ** 2 for p in pixels) / len(pixels)
                lum_mean = mean_val
                lum_std = variance ** 0.5
        except Exception:
            pass

    # Color ratios from PIL if available
    if img is not None and hasattr(img, 'convert'):
        try:
            img_rgb = img.convert('RGB')
            pixels = list(img_rgb.getdata())
            if pixels:
                r_sum = g_sum = b_sum = 0
                count = 0
                for p in pixels:
                    if isinstance(p, tuple) and len(p) >= 3:
                        r_sum += p[0]
                        g_sum += p[1]
                        b_sum += p[2]
                        count += 1
                if count > 0:
                    rb_ratio = float(r_sum / count) / float(g_sum / count) if float(g_sum / count) > 0 else 0
                    rg_diff = float(r_sum / count) - float(g_sum / count)
        except Exception:
            pass

    # Classification (uses guarded classify_image)
    cls = "natural_scene"
    corners = None
    if gray is not None:
        cls, corners = classify_image(gray)

    # MTF50 withheld: this is not a validated slanted-edge SFR method.
    mtf50 = None
    mtf50_status = "NOT_MEASURED: validated slanted-edge SFR required"

    return {
        "filename": os.path.basename(path),
        "path": path,
        "width": w, "height": h,
        "iso": iso,
        "exposure_s": exp_s,
        "ev": ev,
        "f_number": exif_val(exif, 'FNumber'),
        "focal_length": exif_val(exif, 'FocalLength'),
        "software": exif_val(exif, 'Software'),
        "datetime": exif_val(exif, 'DateTime'),
        "lum_mean": lum_mean, "lum_std": lum_std,
        "edge_density": edge_density,
        "black_clip_pct": black_clip,
        "white_clip_pct": white_clip,
        "rb_ratio": rb_ratio,
        "rg_diff": rg_diff,
        "classification": cls,
        "mtf50_cyc_px": mtf50,
        "mtf50_status": mtf50_status,
        "has_checkerboard": corners is not None,
        "corner_count": len(corners) if corners is not None else 0,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-dir", default=CALIB_DIR)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    batch_dir = args.batch_dir
    out_dir = args.output_dir or os.path.join(batch_dir, "analysis_results_opencv")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "annotated"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "plots"), exist_ok=True)

    images = find_images(batch_dir)
    print(f"Found {len(images)} images in {batch_dir}")

    results = []
    cb_images = []  # checkerboard images for calibration
    cb_corners_list = []
    cb_objpoints = []

    # Chessboard config
    CB_COLS, CB_ROWS = 9, 6
    objp = np.zeros((CB_COLS*CB_ROWS, 3), np.float32)
    objp[:,:2] = np.mgrid[0:CB_COLS, 0:CB_ROWS].T.reshape(-1,2)

    for i, path in enumerate(images):
        print(f"[{i+1}/{len(images)}] {os.path.basename(path)}")
        r = analyze_image(path)
        if r is None:
            print(f"  SKIP: could not read")
            continue
        results.append(r)
        mtf_value = r["mtf50_cyc_px"]
        mtf_text = (
            f"{mtf_value:.4f}"
            if mtf_value is not None
            else "NOT MEASURED"
        )
        print(
            f"  {r['classification']} | EV={r['ev']} "
            f"| MTF50={mtf_text} | edge={r['edge_density']:.3%}"
        )

        # If checkerboard, refine corners and collect for calibration
        if r['has_checkerboard']:
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            ret, corners = cv2.findChessboardCorners(img, (CB_COLS, CB_ROWS), None)
            if ret:
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                corners = cv2.cornerSubPix(img, corners, (11,11), (-1,-1), criteria)
                cb_corners_list.append(corners)
                cb_objpoints.append(objp.copy())
                cb_images.append(path)
                # Annotate
                ann = cv2.imread(path)
                cv2.drawChessboardCorners(ann, (CB_COLS, CB_ROWS), corners, ret)
                ann_path = os.path.join(out_dir, "annotated", os.path.basename(path))
                cv2.imwrite(ann_path, ann)

    # Save JSON
    json_path = os.path.join(out_dir, "calibration_results.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved: {json_path}")

    # Save CSV
    csv_path = os.path.join(out_dir, "calibration_metrics.csv")
    if results:
        keys = list(results[0].keys())
        with open(csv_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in results:
                w.writerow(r)
    print(f"Saved: {csv_path}")

    # Intrinsic calibration if enough checkerboard images
    calib_result = None
    if len(cb_images) >= 3:
        print(f"\nRunning intrinsic calibration on {len(cb_images)} checkerboard images...")
        img_shape = cv2.imread(cb_images[0], cv2.IMREAD_GRAYSCALE).shape[::-1]
        ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(
            cb_objpoints, cb_corners_list, img_shape, None, None)
        calib_result = {
            "num_images": len(cb_images),
            "rms_reprojection_error": float(ret),
            "camera_matrix": K.tolist(),
            "distortion_coefficients": dist.tolist()[0] if dist is not None else [],
            "image_size": list(img_shape),
        }
        # Reprojection errors per image
        per_img_errors = []
        for i in range(len(cb_images)):
            imgpoints2, _ = cv2.projectPoints(cb_objpoints[i], rvecs[i], tvecs[i], K, dist)
            err = cv2.norm(cb_corners_list[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            per_img_errors.append(float(err))
        calib_result["per_image_reprojection_error"] = per_img_errors
        calib_result["images_used"] = [os.path.basename(p) for p in cb_images]

        calib_path = os.path.join(out_dir, "intrinsic_calibration.json")
        with open(calib_path, 'w') as f:
            json.dump(calib_result, f, indent=2)
        print(f"Saved: {calib_path}")
        print(f"RMS reprojection error: {ret:.4f}")
        print(f"Camera matrix:\n{K}")
        print(f"Distortion: {dist}")
    else:
        print(f"\nOnly {len(cb_images)} checkerboard images found — need >=3 for intrinsic calibration")

    # Summary stats
    print("\n=== SUMMARY ===")
    print(f"Total images: {len(results)}")
    from collections import Counter
    cls_counts = Counter(r['classification'] for r in results)
    for cls, n in cls_counts.items():
        print(f"  {cls}: {n}")
    print(f"Checkerboard images: {len(cb_images)}")
    if calib_result:
        print(f"Calibration RMS error: {calib_result['rms_reprojection_error']:.4f}")

    # Generate MTF comparison plot
    try:
        fig, ax = plt.subplots(figsize=(10,6))
        names = [r['filename'][:20] for r in results]
        # No validated MTF50 measurements are available.
        mtfs = [0.0 for _ in results]
        colors = ['green' if r['has_checkerboard'] else 'gray' for r in results]
        ax.barh(range(len(names)), mtfs, color=colors)
        ax.text(
            0.5, 0.5,
            "MTF50 unavailable: validated slanted-edge SFR required",
            transform=ax.transAxes, ha="center", va="center",
            wrap=True
        )
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=6)
        ax.set_xlabel('MTF50 (cyc/px)')
        ax.set_title('MTF50 Comparison — All Images')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "plots", "mtf50_comparison.png"), dpi=100)
        plt.close()
        print("Saved MTF50 plot")
    except Exception as e:
        print(f"Plot error: {e}")

    # Generate exposure scatter
    try:
        fig, ax = plt.subplots(figsize=(8,6))
        evs = [r['ev'] for r in results if r['ev']]
        clips = [r['black_clip_pct'] for r in results if r['ev']]
        ax.scatter(evs, clips, c='blue', alpha=0.6)
        ax.set_xlabel('EV')
        ax.set_ylabel('Black Clip %')
        ax.set_title('Exposure vs Black Clipping')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "plots", "exposure_vs_clipping.png"), dpi=100)
        plt.close()
        print("Saved exposure plot")
    except Exception as e:
        print(f"Plot error: {e}")

    print(f"\nAll outputs in: {out_dir}")

if __name__ == "__main__":
    main()
