#!/usr/bin/env python3
"""
IMX682 DCIM Image Sharpness Benchmark (Termux Native)
Scans phone storage (/sdcard/DCIM/Camera/), computes Laplacian variance,
and ranks images by sharpness.
"""

import os
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    print("[!] OpenCV or NumPy missing. Install via: pip install opencv-python numpy")
    sys.exit(1)

DCIM_DIR = Path("/sdcard/DCIM/Camera")

def compute_sharpness(image_path):
    """Compute Laplacian variance as a measure of edge sharpness."""
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0
    return float(cv2.Laplacian(img, cv2.CV_64F).var())

def main():
    print("=" * 65)
    print("  IMX682 DCIM Image Sharpness Benchmark (Termux)")
    print("=" * 65)

    target_dir = DCIM_DIR
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])

    if not target_dir.exists():
        print(f"  [!] Directory not found: {target_dir}")
        print("  [i] Make sure storage permission is granted (termux-setup-storage)")
        return

    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    images = [p for p in target_dir.iterdir() if p.suffix.lower() in image_extensions]

    if not images:
        print(f"  [!] No images found in: {target_dir}")
        return

    print(f"  [i] Analyzing {len(images)} images in {target_dir}...\n")
    results = []

    for img_path in images:
        score = compute_sharpness(img_path)
        results.append((img_path.name, score))

    # Sort descending by sharpness score (highest score = sharpest edges)
    results.sort(key=lambda x: x[1], reverse=True)

    print(f"  {'Rank':<6} {'Sharpness Score':<18} {'Filename'}")
    print("  " + "-" * 55)
    for rank, (name, score) in enumerate(results, 1):
        print(f"  {rank:<6} {score:<18.2f} {name}")
    print("=" * 65)

if __name__ == "__main__":
    main()
