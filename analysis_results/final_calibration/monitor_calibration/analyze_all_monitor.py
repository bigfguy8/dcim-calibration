#!/usr/bin/env python3
"""Analyze all monitor calibration captures (original + new)"""
import os, sys, json, csv, hashlib
from datetime import datetime
from PIL import Image, ExifTags
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\monitor_calibration"
CAPTURES_DIR = os.path.join(BASE_DIR, "captures")
CAPTURES2_DIR = os.path.join(BASE_DIR, "captures2")
OUT_DIR = BASE_DIR
ANNOTATED_DIR = os.path.join(BASE_DIR, "annotated")
PLOT_DIR = os.path.join(BASE_DIR, "plots")

os.makedirs(ANNOTATED_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)

IMG_EXTS = {'.jpg', '.jpeg', '.png'}

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
            return {}, img.size
        out = {}
        for tid, val in exif.items():
            tag = ExifTags.TAGS.get(tid, str(tid))
            out[tag] = val
        return out, img.size
    except Exception as e:
        return {"_error": str(e)}, (0, 0)

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

def detect_moire(img_gray):
    f = np.fft.fft2(img_gray.astype(float))
    fshift = np.fft.fftshift(f)
    magnitude = np.abs(fshift)
    h, w = magnitude.shape
    cy, cx = h // 2, w // 2
    mask = np.ones_like(magnitude, dtype=bool)
    mask[cy-5:cy+5, cx-5:cx+5] = False
    masked_mag = magnitude.copy()
    masked_mag[~mask] = 0
    flat_idx = np.argsort(masked_mag.flatten())[-5:][::-1]
    peaks = []
    for idx in flat_idx:
        y, x = divmod(idx, w)
        peaks.append({"x": int(x - cx), "y": int(y - cy), "magnitude": float(masked_mag[y, x])})
    mean_mag = np.mean(masked_mag[mask])
    max_peak = masked_mag.flatten()[flat_idx[0]] if len(flat_idx) > 0 else 0
    moire_score = float(max_peak / mean_mag) if mean_mag > 0 else 0
    return moire_score, peaks

def analyze_image(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    exif, size = get_exif(path)

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

    if max(h, w) > 1024:
        scale = 1024 / max(h, w)
        img_small = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
        gray_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)
    else:
        img_small = img
        gray_small = gray

    sh, sw = gray_small.shape

    lum = cv2.cvtColor(img_small, cv2.COLOR_BGR2YUV)[:,:,0].astype(float)
    lum_mean = float(np.mean(lum))
    lum_std = float(np.std(lum))
    lum_p5 = float(np.percentile(lum, 5))
    lum_p95 = float(np.percentile(lum, 95))

    gray_uint8 = gray_small.astype(np.uint8)
    black_clip = float(np.sum(gray_uint8 <= 5) / gray_uint8.size * 100)
    white_clip = float(np.sum(gray_uint8 >= 250) / gray_uint8.size * 100)

    edges = cv2.Canny(gray_uint8, 50, 150)
    edge_density = float(np.sum(edges > 0) / edges.size)

    b, g, r = cv2.split(img_small)
    r_mean = float(np.mean(r))
    g_mean = float(np.mean(g))
    b_mean = float(np.mean(b))
    rb_ratio = float(r_mean / b_mean) if b_mean > 0 else 0
    rg_diff = float(r_mean - g_mean)
    gb_diff = float(g_mean - b_mean)

    cb_info = None
    corners = None
    for pattern in [(9,6), (7,5), (8,6), (6,8), (15,8), (8,15), (10,7), (7,10)]:
        found, c = cv2.findChessboardCorners(gray_uint8, pattern, None)
        if found:
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            c = cv2.cornerSubPix(gray_uint8, c, (11,11), (-1,-1), criteria)
            cb_info = {"pattern": pattern, "corners_found": len(c)}
            corners = c
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

    moire_score, moire_peaks = detect_moire(gray_small)

    ann_path = None
    if cb_info and corners is not None:
        ann = img_small.copy()
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
        "classification": "checkerboard_" + str(cb_info["pattern"][0]) + "x" + str(cb_info["pattern"][1]) if cb_info else "natural_scene",
        "mtf50_cyc_px": mtf50,
        "moire_score": moire_score,
        "moire_peaks": moire_peaks,
        "annotated_path": ann_path,
    }

def main():
    # Collect all images from both captures directories
    all_images = []
    for d in [CAPTURES_DIR, CAPTURES2_DIR]:
        if os.path.exists(d):
            all_images.extend(find_images(d))
    all_images = sorted(set(all_images))
    print("Total images to analyze: " + str(len(all_images)))

    results = []
    for i, path in enumerate(all_images):
        print("[" + str(i+1) + "/" + str(len(all_images)) + "] " + os.path.basename(path), flush=True)
        r = analyze_image(path)
        if r is None:
            print("  SKIP: could not read")
            continue
        results.append(r)
        print("  " + r["classification"] + " | EV=" + str(r["ev"]) +
              " | ISO=" + str(r["iso"]) + " | MTF50=" + str(round(r["mtf50_cyc_px"],4)) +
              " | edge=" + str(round(r["edge_density"],3)) +
              " | R/B=" + str(round(r["rb_ratio"],3)) +
              " | R-G=" + str(round(r["rg_diff"],1)) +
              " | black_clip=" + str(round(r["black_clip_pct"],2)) + "%" +
              " | white_clip=" + str(round(r["white_clip_pct"],2)) + "%" +
              " | moire=" + str(round(r["moire_score"],1)))

    # Save JSON
    json_path = os.path.join(OUT_DIR, "monitor_all_captures_analysis.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print("\nSaved: " + json_path + " (" + str(len(results)) + " images)")

    # Save CSV
    csv_path = os.path.join(OUT_DIR, "monitor_all_captures_analysis.csv")
    if results:
        keys = list(results[0].keys())
        with open(csv_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in results:
                w.writerow(r)
    print("Saved CSV: " + csv_path)

    from collections import Counter
    cls_counts = Counter(r['classification'] for r in results)
    print("\n=== SUMMARY ===")
    print("Total images: " + str(len(results)))
    for cls, n in cls_counts.items():
        print("  " + cls + ": " + str(n))

    cb_images = [r for r in results if r['checkerboard_detected']]
    print("Checkerboard images: " + str(len(cb_images)))

    if results:
        best_sharp = max(results, key=lambda r: r['mtf50_cyc_px'])
        print("Best MTF50: " + best_sharp['filename'] + " = " + str(best_sharp['mtf50_cyc_px']))

        least_black = min(results, key=lambda r: r['black_clip_pct'])
        print("Least black clip: " + least_black['filename'] + " = " + str(round(least_black['black_clip_pct'],2)) + "%")

        least_white = min(results, key=lambda r: r['white_clip_pct'])
        print("Least white clip: " + least_white['filename'] + " = " + str(round(least_white['white_clip_pct'],2)) + "%")

        most_neutral = min(results, key=lambda r: abs(r['rb_ratio'] - 1.0))
        print("Most neutral R/B: " + most_neutral['filename'] + " = " + str(round(most_neutral['rb_ratio'],3)))

        least_moire = min(results, key=lambda r: r['moire_score'])
        print("Least moiré: " + least_moire['filename'] + " = " + str(round(least_moire['moire_score'],1)))

    # Generate plots
    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        names = [r['filename'][:30] for r in results]
        mtfs = [r['mtf50_cyc_px'] for r in results]
        colors = ['green' if r['checkerboard_detected'] else 'blue' for r in results]
        ax.barh(range(len(names)), mtfs, color=colors)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=5)
        ax.set_xlabel('MTF50 (cyc/px)')
        ax.set_title('Monitor Captures — MTF50 Comparison (' + str(len(results)) + ' images)')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, "monitor_all_mtf50.png"), dpi=150)
        plt.close()
        print("\nSaved MTF50 plot")
    except Exception as e:
        print("Plot error: " + str(e))

    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        names = [r['filename'][:30] for r in results]
        rbs = [r['rb_ratio'] for r in results]
        ax.barh(range(len(names)), rbs, color='orange')
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=5)
        ax.set_xlabel('R/B Ratio')
        ax.set_title('Monitor Captures — White Balance (' + str(len(results)) + ' images)')
        ax.axvline(x=1.0, color='black', linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, "monitor_all_wb.png"), dpi=150)
        plt.close()
        print("Saved WB plot")
    except Exception as e:
        print("Plot error: " + str(e))

    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        names = [r['filename'][:30] for r in results]
        bclips = [r['black_clip_pct'] for r in results]
        wclips = [r['white_clip_pct'] for r in results]
        x = np.arange(len(names))
        width = 0.35
        ax.bar(x - width/2, bclips, width, label='Black clip %', color='red', alpha=0.7)
        ax.bar(x + width/2, wclips, width, label='White clip %', color='blue', alpha=0.7)
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=90, fontsize=4)
        ax.set_ylabel('Clip %')
        ax.set_title('Monitor Captures — Clipping (' + str(len(results)) + ' images)')
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, "monitor_all_clipping.png"), dpi=150)
        plt.close()
        print("Saved clipping plot")
    except Exception as e:
        print("Plot error: " + str(e))

    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        names = [r['filename'][:30] for r in results]
        moires = [r['moire_score'] for r in results]
        ax.barh(range(len(names)), moires, color='purple', alpha=0.7)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=5)
        ax.set_xlabel('Moiré Score')
        ax.set_title('Monitor Captures — Moiré Severity (' + str(len(results)) + ' images)')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, "monitor_all_moire.png"), dpi=150)
        plt.close()
        print("Saved moiré plot")
    except Exception as e:
        print("Plot error: " + str(e))

    print("\nAll outputs in: " + OUT_DIR)

if __name__ == "__main__":
    main()
