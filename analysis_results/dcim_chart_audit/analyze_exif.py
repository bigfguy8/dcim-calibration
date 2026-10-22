#!/usr/bin/env python3
"""DCIM Calibration Analysis - EXIF only (fast, no OpenCV)"""
import os, sys, json, csv, hashlib
from PIL import Image, ExifTags

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\dcim_chart_audit"
PULL_DIR = os.path.join(BASE_DIR, "device_pulls")
OUT_DIR = BASE_DIR

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
        return out, img.size
    except Exception as e:
        return {"_error": str(e)}, (0, 0)

def exif_val(exif, *keys, default=None):
    for k in keys:
        if k in exif:
            return exif[k]
    return default

def main():
    images = find_images(PULL_DIR)
    print("Found " + str(len(images)) + " images")

    results = []
    for i, path in enumerate(images):
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

        ev = None
        if iso and exp_s and exp_s > 0:
            ev = round(__import__('numpy').log2(100.0 / iso / exp_s), 3)

        r = {
            "filename": os.path.basename(path),
            "path": path,
            "width": size[0],
            "height": size[1],
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
        }
        results.append(r)
        print("[" + str(i+1) + "/" + str(len(images)) + "] " + r["filename"] +
              " | " + str(size[0]) + "x" + str(size[1]) +
              " | ISO=" + str(iso) + " | EV=" + str(ev) +
              " | SW=" + str(exif_val(exif, 'Software')))

    json_path = os.path.join(OUT_DIR, "dcim_exif_inventory.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print("\nSaved EXIF inventory: " + json_path)

    csv_path = os.path.join(OUT_DIR, "dcim_exif_inventory.csv")
    if results:
        keys = list(results[0].keys())
        with open(csv_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in results:
                w.writerow(r)
    print("Saved CSV: " + csv_path)

if __name__ == "__main__":
    main()
