#!/usr/bin/env python3
"""Scene classification for baseline A/B images using image features"""
import os, json, csv, hashlib
import numpy as np
import cv2
from PIL import Image, ExifTags

BASE = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison\baseline"
OUT = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison"

files = sorted(os.listdir(BASE))

features = []
for f in files:
    path = os.path.join(BASE, f)
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        continue
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Downscale for analysis
    if max(h, w) > 512:
        scale = 512 / max(h, w)
        img_s = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
        gray_s = cv2.cvtColor(img_s, cv2.COLOR_BGR2GRAY)
    else:
        img_s = img
        gray_s = gray

    sh, sw = gray_s.shape

    # Color features
    b, g, r = cv2.split(img_s)
    r_mean = float(np.mean(r))
    g_mean = float(np.mean(g))
    b_mean = float(np.mean(b))

    # Green dominance (foliage indicator)
    green_dominance = float(g_mean - (r_mean + b_mean) / 2)

    # Blue dominance (sky indicator)
    blue_dominance = float(b_mean - (r_mean + g_mean) / 2)

    # Red dominance (warm/indoor indicator)
    red_dominance = float(r_mean - (g_mean + b_mean) / 2)

    # Brightness
    lum_mean = float(np.mean(gray_s))
    lum_std = float(np.std(gray_s))
    lum_p5 = float(np.percentile(gray_s, 5))
    lum_p95 = float(np.percentile(gray_s, 95))
    dynamic_range = lum_p95 - lum_p5

    # Edge features
    edges = cv2.Canny(gray_s.astype(np.uint8), 50, 150)
    edge_density = float(np.sum(edges > 0) / edges.size)

    # Horizontal vs vertical edges (text indicator)
    gx = cv2.Sobel(gray_s.astype(np.uint8), cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_s.astype(np.uint8), cv2.CV_64F, 0, 1, ksize=3)
    h_edges = float(np.sum(np.abs(gx) > 50))
    v_edges = float(np.sum(np.abs(gy) > 50))
    hv_ratio = float(h_edges / v_edges) if v_edges > 0 else 0

    # Texture (Laplacian variance - sharpness/detail)
    laplacian = cv2.Laplacian(gray_s.astype(np.uint8), cv2.CV_64F)
    texture_var = float(np.var(laplacian))

    # Color saturation (std of color channels)
    color_sat = float(np.mean([np.std(r), np.std(g), np.std(b)]))

    # Histogram features (bimodality)
    hist = cv2.calcHist([gray_s.astype(np.uint8)], [0], None, [256], [0, 256]).flatten()
    # Find peaks
    peaks = []
    for i in range(1, 255):
        if hist[i] > hist[i-1] and hist[i] > hist[i+1] and hist[i] > np.mean(hist) * 1.5:
            peaks.append(i)

    # EXIF
    from PIL import Image, ExifTags
    img_pil = Image.open(path)
    exif = img_pil._getexif()
    exif_dict = {}
    if exif:
        for tid, val in exif.items():
            tag = ExifTags.TAGS.get(tid, str(tid))
            exif_dict[tag] = val
    iso = exif_dict.get('ISOSpeedRatings')
    exp = exif_dict.get('ExposureTime')
    ev = None
    if iso and exp:
        try:
            if isinstance(exp, tuple):
                exp_s = exp[0] / exp[1]
            else:
                exp_s = float(exp)
            ev = round(__import__('math').log2(100.0 / int(iso) / exp_s), 3)
        except:
            pass

    sw = exif_dict.get('Software', '')

    features.append({
        'filename': f,
        'r_mean': r_mean, 'g_mean': g_mean, 'b_mean': b_mean,
        'green_dominance': green_dominance,
        'blue_dominance': blue_dominance,
        'red_dominance': red_dominance,
        'lum_mean': lum_mean, 'lum_std': lum_std,
        'lum_p5': lum_p5, 'lum_p95': lum_p95,
        'dynamic_range': dynamic_range,
        'edge_density': edge_density,
        'hv_ratio': hv_ratio,
        'texture_var': texture_var,
        'color_sat': color_sat,
        'num_peaks': len(peaks),
        'iso': int(iso) if iso else None,
        'ev': ev,
        'software': sw,
    })

# Print feature table
print(f"{'Filename':<35} {'GreenDom':>8} {'BlueDom':>8} {'RedDom':>8} {'LumMean':>8} {'LumStd':>8} {'EdgeDen':>8} {'HV_ratio':>8} {'TexVar':>8} {'EV':>6} {'ISO':>6}")
print("-" * 130)
for f in features:
    print(f"{f['filename']:<35} {f['green_dominance']:>8.1f} {f['blue_dominance']:>8.1f} {f['red_dominance']:>8.1f} {f['lum_mean']:>8.1f} {f['lum_std']:>8.1f} {f['edge_density']:>8.3f} {f['hv_ratio']:>8.2f} {f['texture_var']:>8.0f} {str(f['ev']):>6} {str(f['iso']):>6}")

# Save features
import json
with open(os.path.join(OUT, 'scene_features.json'), 'w') as fh:
    json.dump(features, fh, indent=2)
print("\nSaved: scene_features.json")
print(f"Total images analyzed: {len(features)}")
