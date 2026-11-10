#!/usr/bin/env python3
"""
IMX682 OpenCV Camera Calibration Pipeline
Uses OpenCV for checkerboard detection, intrinsic calibration, distortion estimation.
Falls back to PIL for images without cv2-compatible formats.
"""
import os, sys, json, csv, argparse, hashlib, glob
from datetime import datetime
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
        return np.log2(100.0 / iso / exp_s) if iso and exp_s and exp_s>0 else None
    except: return None

def classify_image(img_gray):
    """Classify as checkerboard or natural scene using OpenCV."""
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

def detect_slanted_edge_roi(gray):
    """Auto-detect the strongest slanted edge in a grayscale image.

    Returns a dict with an edge region of interest (x, y, w, h), the edge
    angle in degrees, edge strength, and edge-pixel count; or None when no
    confident slanted edge is present. The ROI is centred on the detected
    edge so a subpixel slanted-edge MTF50 can be run over it.
    """
    h, w = gray.shape
    if min(h, w) < 64:
        return None
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(gx * gx + gy * gy)
    # Edge direction is perpendicular to the gradient, wrapped to [0, 180).
    edge_ang = (np.degrees(np.arctan2(gy, gx)) + 90.0) % 180.0
    # Strong-edge mask: keep the top tail of gradient magnitude.
    thr = np.percentile(mag, 96)
    mask = mag > thr
    if mask.sum() < 40:
        return None
    # Weighted orientation histogram of strong edges.
    bins = np.linspace(0, 180, 37)
    hist, _ = np.histogram(edge_ang[mask], bins=bins, weights=mag[mask])
    total = float(hist.sum())
    if total <= 0:
        return None
    best = int(np.argmax(hist))
    strength = float(hist[best] / total)
    # Require a dominant orientation (not a textureless/grassy scene).
    if strength < 0.30:
        return None
    ang = float((bins[best] + bins[best + 1]) / 2.0)
    # Collect edge pixels aligned with the chosen orientation.
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

def slanted_edge_mtf50(gray, roi=None, oversample=8):
    """Estimate MTF50 (cyc/px) from a slanted edge (ISO 12233-style SFR).

    Builds a subpixel edge-spread function by averaging intensity profiles
    taken normal to the edge across many tangent columns, differentiates to
    the line-spread function, windows it, and FFTs to the MTF. MTF50 is the
    spatial frequency where MTF falls to 0.5.

    Returns a dict with mtf50_cyc_px, the frequency/MTF curves, the edge
    angle and ROI used; or None when no usable edge is found.
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
        sub = gray[y:y + rh, x:x + rw]
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

    crop = gray[y:y + rh, x:x + rw].astype(np.float64)
    gx = cv2.Sobel(crop, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(crop, cv2.CV_64F, 0, 1, ksize=3)

    th = np.radians(angle)
    # Tangent runs along the edge; normal runs across it.
    tx, ty = np.cos(th), np.sin(th)
    nx, ny = -np.sin(th), np.cos(th)

    cy_, cx_ = rh / 2.0, rw / 2.0
    yy, xx = np.mgrid[0:rh, 0:rw]
    t = (xx - cx_) * tx + (yy - cy_) * ty   # along-edge coordinate
    n = (xx - cx_) * nx + (yy - cy_) * ny   # across-edge coordinate
    gn = gx * nx + gy * ny                  # gradient across the edge

    t_min, t_max = float(t.min()), float(t.max())
    n_cols = max(8, int(rw / 4))
    t_edges = np.linspace(t_min, t_max, n_cols + 1)

    samples = []  # (subpixel bin index, intensity)
    for i in range(n_cols):
        m = (t >= t_edges[i]) & (t < t_edges[i + 1])
        if m.sum() < 3:
            continue
        col_n = n[m]
        col_i = crop[m]
        col_gn = gn[m]
        # Edge position = across-edge coordinate of max |gradient|.
        pk = int(np.argmax(np.abs(col_gn)))
        n_edge = float(col_n[pk])
        # Subpixel refine: weighted centroid of |gn| within +-2 px of peak.
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

    # Aggregate mean intensity per subpixel bin -> edge spread function.
    buckets = {}
    for b, val in samples:
        buckets.setdefault(b, []).append(val)
    bmin, bmax = min(buckets), max(buckets)
    esf_profile = np.array(
        [float(np.mean(buckets.get(b, [np.nan])))
         for b in range(bmin, bmax + 1)]
    )
    valid = ~np.isnan(esf_profile)
    if valid.sum() < 10:
        return None
    # Interpolate across empty subpixel bins so the ESF is continuous
    # before differentiating. np.interp clamps the ends to the nearest
    # valid sample, avoiding extrapolation beyond the measured range.
    idx = np.arange(len(esf_profile))
    esf_profile = np.interp(idx, idx[valid], esf_profile[valid])

    # Line spread function = derivative of ESF.
    lsf = np.diff(esf_profile)
    win = np.hanning(len(lsf))
    lsf_w = lsf * win
    n_fft = 1 << (int(len(lsf_w)) - 1).bit_length()
    spectrum = np.fft.rfft(lsf_w, n=n_fft)
    mtf = np.abs(spectrum)
    if mtf[0] > 0:
        mtf = mtf / mtf[0]
    freqs = np.fft.rfftfreq(n_fft, d=1.0 / oversample)  # cyc/px
    pos = freqs > 0
    freqs = freqs[pos]
    mtf = mtf[pos]

    # MTF50 = frequency where MTF crosses 0.5 (linear interpolation).
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

def analyze_image(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
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
    # Metrics
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)[:,:,0]
    lum_mean = float(np.mean(lum))
    lum_std = float(np.std(lum))
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges>0)/edges.size)
    black_clip = float(np.sum(gray <= 5)/gray.size*100)
    white_clip = float(np.sum(gray >= 250)/gray.size*100)
    # Color
    b,g,r = cv2.split(img)
    rb_ratio = float(np.mean(r)/np.mean(b)) if np.mean(b)>0 else 0
    rg_diff = float(np.mean(r)-np.mean(g))
    # Classification
    cls, corners = classify_image(gray)
    # Slanted-edge MTF50 (ISO 12233-style estimate). Returns None when no
    # confident slanted edge is present, so plain natural scenes keep
    # mtf50 unset rather than fabricating a number.
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
        mtfs = [
            r['mtf50_cyc_px'] if r['mtf50_cyc_px'] is not None else 0.0
            for r in results
        ]
        colors = ['green' if r['has_checkerboard'] else 'gray' for r in results]
        ax.barh(range(len(names)), mtfs, color=colors)
        measured = sum(1 for r in results if r['mtf50_cyc_px'] is not None)
        ax.text(
            0.5, 0.5,
            f"MTF50 (cyc/px): {measured}/{len(results)} images measured "
            "(slanted-edge estimate, not chart-certified)",
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
