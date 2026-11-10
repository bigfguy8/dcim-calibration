#!/usr/bin/env python3
"""DCIM Calibration Chart Photo Analysis - Batch Processor"""
import os, sys, json, csv, hashlib
from datetime import datetime
from PIL import Image, ExifTags
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\dcim_chart_audit"
PULL_DIR = os.path.join(BASE_DIR, "device_pulls")
OUT_DIR = BASE_DIR
ANNOTATED_DIR = os.path.join(BASE_DIR, "annotated")
PLOT_DIR = os.path.join(BASE_DIR, "plots")

IMG_EXTS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp', '.tiff', '.tif', '.bmp'}

def find_images(root):
    out = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if os.path.splitext(f)[1].lower() in IMG_EXTS:
                out.append(os.path.join(dp, f))
    return sorted(out)

def file_hash(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()

def get_exif(path):
    try:
        img = Image.open(path)
        exif = img._getexif()
        if not exif:
            return {}
        out = {}
        for tid, val in exif.items():
            tag = ExifTags.TAGS.get(tid, str(tid))
            out[tag] = val
        return out
    except Exception as e:
        return {"_error": str(e)}

def exif_val(exif, *keys, default=None):
    for k in keys:
        if k in exif:
            return exif[k]
    return default

def compute_ev(iso, exp_s):
    try:
        if iso and exp_s and exp_s > 0:
            return round(np.log2(100.0 / iso / exp_s), 3)
    except:
        pass
    return None

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
        if isinstance(exp_str, tuple):
            exp_s = exp_str[0] / exp_str[1]
        else:
            exp_s = float(exp_str)
    except:
        exp_s = None

    ev = compute_ev(iso, exp_s)

    lum = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)[:,:,0].astype(float)
    lum_mean = float(np.mean(lum))
    lum_std = float(np.std(lum))
    lum_p5 = float(np.percentile(lum, 5))
    lum_p95 = float(np.percentile(lum, 95))

    gray_uint8 = gray.astype(np.uint8)
    black_clip = float(np.sum(gray_uint8 <= 5) / gray_uint8.size * 100)
    white_clip = float(np.sum(gray_uint8 >= 250) / gray_uint8.size * 100)

    edges = cv2.Canny(gray_uint8, 50, 150)
    edge_density = float(np.sum(edges > 0) / edges.size)

    b, g, r = cv2.split(img)
    r_mean = float(np.mean(r))
    g_mean = float(np.mean(g))
    b_mean = float(np.mean(b))
    rb_ratio = float(r_mean / b_mean) if b_mean > 0 else 0
    rg_diff = float(r_mean - g_mean)
    gb_diff = float(g_mean - b_mean)

    cb_info = None
    for pattern in [(9,6), (7,5), (8,6), (6,8), (9,7), (7,9)]:
        found, corners = cv2.findChessboardCorners(gray_uint8, pattern, None)
        if found:
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners = cv2.cornerSubPix(gray_uint8, corners, (11,11), (-1,-1), criteria)
            cb_info = {
                "pattern": pattern,
                "corners_found": len(corners),
            }
            break

    gx = cv2.Sobel(gray_uint8, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_uint8, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(gx**2 + gy**2)
    edge_rows = np.argsort(mag.mean(axis=1))[-10:]
    mtf50 = 0.0
    if len(edge_rows) > 0:
        row = int(edge_rows[-1])
        esf = gray_uint8[row, :].astype(float)
        lsf = np.abs(np.diff(esf))
        if lsf.max() > 0:
            lsf = lsf / lsf.max()
            mtf = np.abs(np.fft.rfft(lsf))
            mtf = mtf / mtf[0] if mtf[0] > 0 else mtf
            freqs = np.fft.rfftfreq(len(lsf))
            idx = np.where(mtf < 0.5)[0]
            mtf50 = float(freqs[idx[0]]) if len(idx) > 0 else float(freqs[-1])

    classification = "natural_scene"
    if cb_info:
        classification = "checkerboard_" + str(cb_info["pattern"][0]) + "x" + str(cb_info["pattern"][1])

    ann_path = None
    if cb_info:
        ann = img.copy()
        cv2.drawChessboardCorners(ann, cb_info["pattern"], corners, True)
        ann_name = os.path.basename(path) + ".annotated.jpg"
        ann_path = os.path.join(ANNOTATED_DIR, ann_name)
        cv2.imwrite(ann_path, ann)

    return {
        "filename": os.path.basename(path),
        "path": path,
        "width": w,
        "height": h,
        "sha256": file_hash(path),
        "iso": iso,
        "exposure_s": exp_s,
        "ev": ev,
        "f_number": str(exif_val(exif, 'FNumber')),
        "focal_length": str(exif_val(exif, 'FocalLength')),
        "software": str(exif_val(exif, 'Software')),
        "datetime": str(exif_val(exif, 'DateTime')),
        "make": str(exif_val(exif, 'Make')),
        "model": str(exif_val(exif, 'Model')),
        "white_balance": str(exif_val(exif, 'WhiteBalance')),
        "flash": str(exif_val(exif, 'Flash')),
        "exposure_program": str(exif_val(exif, 'ExposureProgram')),
        "scene_capture": str(exif_val(exif, 'SceneCaptureType')),
        "color_space": str(exif_val(exif, 'ColorSpace')),
        "lum_mean": lum_mean,
        "lum_std": lum_std,
        "lum_p5": lum_p5,
        "lum_p95": lum_p95,
        "r_mean": r_mean,
        "g_mean": g_mean,
        "b_mean": b_mean,
        "rb_ratio": rb_ratio,
        "rg_diff": rg_diff,
        "gb_diff": gb_diff,
        "edge_density": edge_density,
        "black_clip_pct": black_clip,
        "white_clip_pct": white_clip,
        "checkerboard_detected": cb_info is not None,
        "checkerboard_pattern": str(cb_info["pattern"]) if cb_info else None,
        "corner_count": cb_info["corners_found"] if cb_info else 0,
        "classification": classification,
        "mtf50_cyc_px": mtf50,
        "annotated_path": ann_path,
    }

def main(batch_size=None):
    images = find_images(PULL_DIR)
    if batch_size:
        images = images[:batch_size]
    print("Processing " + str(len(images)) + " images...")

    results = []
    for i, path in enumerate(images):
        print("[" + str(i+1) + "/" + str(len(images)) + "] " + os.path.basename(path), flush=True)
        r = analyze_image(path)
        if r is None:
            print("  SKIP: could not read")
            continue
        results.append(r)
        print("  " + r["classification"] + " | EV=" + str(r["ev"]) +
              " | ISO=" + str(r["iso"]) + " | MTF50=" + str(round(r["mtf50_cyc_px"],4)) +
              " | edge=" + str(round(r["edge_density"],3)) +
              " | R/B=" + str(round(r["rb_ratio"],3)))

    # Load existing results if any
    json_path = os.path.join(OUT_DIR, "dcim_inventory.json")
    existing = []
    if os.path.exists(json_path):
        try:
            existing = json.load(open(json_path))
        except:
            existing = []

    # Merge: avoid duplicates by filename
    existing_names = {r['filename'] for r in existing}
    for r in results:
        if r['filename'] not in existing_names:
            existing.append(r)

    # Save JSON
    with open(json_path, 'w') as f:
        json.dump(existing, f, indent=2, default=str)
    print("\nSaved: " + json_path + " (" + str(len(existing)) + " images)")

    # Save CSV
    csv_path = os.path.join(OUT_DIR, "dcim_inventory.csv")
    if existing:
        keys = list(existing[0].keys())
        with open(csv_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in existing:
                w.writerow(r)
    print("Saved: " + csv_path)

    # Summary
    from collections import Counter
    cls_counts = Counter(r['classification'] for r in existing)
    print("\n=== SUMMARY ===")
    print("Total images: " + str(len(existing)))
    for cls, n in cls_counts.items():
        print("  " + cls + ": " + str(n))

    cb_images = [r for r in existing if r['checkerboard_detected']]
    print("Checkerboard images: " + str(len(cb_images)))

    if existing:
        best_sharp = max(existing, key=lambda r: r['mtf50_cyc_px'])
        print("Best MTF50: " + best_sharp['filename'] + " = " + str(best_sharp['mtf50_cyc_px']))

        least_black = min(existing, key=lambda r: r['black_clip_pct'])
        print("Least black clip: " + least_black['filename'] + " = " + str(round(least_black['black_clip_pct'],2)) + "%")

        least_white = min(existing, key=lambda r: r['white_clip_pct'])
        print("Least white clip: " + least_white['filename'] + " = " + str(round(least_white['white_clip_pct'],2)) + "%")

        most_neutral = min(existing, key=lambda r: abs(r['rb_ratio'] - 1.0))
        print("Most neutral R/B: " + most_neutral['filename'] + " = " + str(round(most_neutral['rb_ratio'],3)))

    print("\nDone. Outputs in: " + OUT_DIR)

if __name__ == "__main__":
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(batch)
