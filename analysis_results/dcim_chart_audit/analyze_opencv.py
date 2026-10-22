#!/usr/bin/env python3
"""DCIM Calibration Analysis - OpenCV metrics on downscaled images"""
import os, sys, json, csv, hashlib
import numpy as np
import cv2
from PIL import Image, ExifTags

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\dcim_chart_audit"
PULL_DIR = os.path.join(BASE_DIR, "device_pulls")
OUT_DIR = BASE_DIR
ANNOTATED_DIR = os.path.join(BASE_DIR, "annotated")

IMG_EXTS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp', '.tiff', '.tif', '.bmp'}
MAX_DIM = 1024  # Downscale for fast OpenCV processing

def find_images(root):
    out = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if os.path.splitext(f)[1].lower() in IMG_EXTS:
                out.append(os.path.join(dp, f))
    return sorted(out)

def file_hash(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()

def load_and_downscale(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        return None
    h, w = img.shape[:2]
    if max(h, w) > MAX_DIM:
        scale = MAX_DIM / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return img

def analyze_image(path):
    img = load_and_downscale(path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    lum = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)[:,:,0].astype(float)
    lum_mean = float(np.mean(lum))
    lum_std = float(np.std(lum))

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

    cb_info = None
    corners = None
    for pattern in [(9,6), (7,5), (8,6), (6,8), (9,7), (7,9)]:
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
        "width": w,
        "height": h,
        "sha256": file_hash(path),
        "lum_mean": lum_mean,
        "lum_std": lum_std,
        "r_mean": r_mean,
        "g_mean": g_mean,
        "b_mean": b_mean,
        "rb_ratio": rb_ratio,
        "rg_diff": rg_diff,
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

def main():
    images = find_images(PULL_DIR)
    print("Processing " + str(len(images)) + " images at max dim " + str(MAX_DIM) + "...")

    # Load existing EXIF data
    exif_data = {}
    exif_path = os.path.join(OUT_DIR, "dcim_exif_inventory.json")
    if os.path.exists(exif_path):
        exif_list = json.load(open(exif_path))
        for e in exif_list:
            exif_data[e['filename']] = e

    results = []
    for i, path in enumerate(images):
        print("[" + str(i+1) + "/" + str(len(images)) + "] " + os.path.basename(path), flush=True)
        r = analyze_image(path)
        if r is None:
            print("  SKIP")
            continue
        # Merge EXIF data
        fname = r['filename']
        if fname in exif_data:
            for k, v in exif_data[fname].items():
                if k not in r or r[k] is None:
                    r[k] = v
        results.append(r)
        print("  " + r["classification"] + " | MTF50=" + str(round(r["mtf50_cyc_px"],4)) +
              " | edge=" + str(round(r["edge_density"],3)) +
              " | R/B=" + str(round(r["rb_ratio"],3)) +
              " | black_clip=" + str(round(r["black_clip_pct"],2)) + "%")

    json_path = os.path.join(OUT_DIR, "dcim_full_analysis.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print("\nSaved: " + json_path + " (" + str(len(results)) + " images)")

    csv_path = os.path.join(OUT_DIR, "dcim_full_analysis.csv")
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

if __name__ == "__main__":
    main()
