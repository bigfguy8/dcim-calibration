#!/usr/bin/env python3
import os
import cv2

def calculate_sharpness(image_path):
    """Calculate image sharpness using the Laplacian variance method."""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        return cv2.Laplacian(img, cv2.CV_64F).var()
    except Exception as e:
        return 0.0

def main():
    image_dir = "/sdcard/DCIM/Camera"
    print("=================================================================")
    print("  IMX682 DCIM Image Sharpness Benchmark (Termux)")
    print("=================================================================")
    
    if not os.path.exists(image_dir):
        print(f"  [!] Directory not found: {image_dir}")
        return

    print(f"  [i] Analyzing valid still images in {image_dir}...")
    
    # Supported image extensions
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    
    results = []
    for filename in os.listdir(image_dir):
        # Skip hidden files, pending captures, and trashed items
        if filename.startswith('.') or '.pending' in filename or '.trashed' in filename:
            continue
            
        # Skip video formats
        if not filename.lower().endswith(valid_extensions):
            continue
            
        file_path = os.path.join(image_dir, filename)
        if os.path.isfile(file_path):
            score = calculate_sharpness(file_path)
            results.append((filename, score))
            
    # Sort results by sharpness score descending
    results.sort(key=lambda x: x[1], reverse=True)
    
    print("\n  Rank   Sharpness Score    Filename")
    print("  -------------------------------------------------------")
    for idx, (filename, score) in enumerate(results, start=1):
        print(f"  {idx:<6} {score:<18.2f} {filename}")
    print("=================================================================")

if __name__ == "__main__":
    main()
