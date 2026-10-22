#!/usr/bin/env python3
"""Run baseline analysis on qualified (selected) images only"""
import os, sys, json, csv, hashlib
from datetime import datetime
from PIL import Image, ExifTags
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison"
QUALIFIED_DIR = os.path.join(BASE, "baseline_qualified")
OUT_DIR = BASE
PLOT_DIR = os.path.join(BASE, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)

# Reuse ab_analyze functions
sys.path.insert(0, BASE)
from ab_analyze import analyze_image, get_exif, exif_val, compute_ev

images = sorted(os.listdir(QUALIFIED_DIR))
images = [os.path.join(QUALIFIED_DIR, f) for f in images if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
print("Analyzing " + str(len(images)) + " qualified baseline images...")

results = []
for i, path in enumerate(images):
    r = analyze_image(path)
    if r:
        r['config'] = 'baseline'
        results.append(r)
        print("  " + r['filename'] + " | R-G=" + str(round(r['rg_diff'],1)) + " | edge=" + str(round(r['edge_density'],3)) + " | black=" + str(round(r['black_clip_pct'],2)) + "% | white=" + str(round(r['white_clip_pct'],2)) + "% | lum_std=" + str(round(r['lum_std'],1)) + " | halo=" + str(round(r['halo_score'],1)))

# Save results
with open(os.path.join(OUT_DIR, "baseline_qualified_results.json"), 'w') as f:
    json.dump(results, f, indent=2, default=str)
print("\nSaved: baseline_qualified_results.json (" + str(len(results)) + " images)")

# Summary statistics
print("\n=== BASELINE QUALIFIED SUMMARY ===")
print("Images: " + str(len(results)))
metrics = ['rg_diff', 'rb_ratio', 'edge_density', 'black_clip_pct', 'white_clip_pct', 'lum_std', 'halo_score']
for m in metrics:
    vals = [r[m] for r in results if r.get(m) is not None]
    if vals:
        print(f"  {m}: median={np.median(vals):.4f}, min={min(vals):.4f}, max={max(vals):.4f}, mean={np.mean(vals):.4f}")

# Save CSV
csv_path = os.path.join(OUT_DIR, "baseline_qualified_results.csv")
keys = list(results[0].keys()) if results else []
with open(csv_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    for r in results:
        w.writerow(r)
print("Saved: baseline_qualified_results.csv")

# Generate contact sheet of qualified images
try:
    from PIL import Image as PILImage
    fig, axes = plt.subplots(3, 6, figsize=(18, 9))
    axes = axes.flatten()
    for i, r in enumerate(results):
        img = PILImage.open(r['path'])
        thumb = img.copy()
        thumb.thumbnail((200, 150))
        axes[i].imshow(thumb)
        axes[i].set_title(r['filename'][:18], fontsize=7)
        axes[i].axis('off')
    for i in range(len(results), len(axes)):
        axes[i].axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "baseline_qualified_contact.png"), dpi=100)
    plt.close()
    print("Saved: baseline_qualified_contact.png")
except Exception as e:
    print("Contact sheet error: " + str(e))

print("\nDone.")
