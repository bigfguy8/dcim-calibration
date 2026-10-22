#!/usr/bin/env python3
"""A/B Config Comparison Analysis Script"""
import os, sys, json, csv, hashlib
from datetime import datetime
from PIL import Image, ExifTags
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison"
BASELINE_DIR = os.path.join(BASE, "baseline")
OPTIMIZED_DIR = os.path.join(BASE, "optimized")
PLOT_DIR = os.path.join(BASE, "plots")
OUT_DIR = BASE

os.makedirs(PLOT_DIR, exist_ok=True)

IMG_EXTS = {'.jpg', '.jpeg', '.png'}

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

    lum = cv2.cvtColor(img_small, cv2.COLOR_BGR2YUV)[:,:,0].astype(float)
    lum_mean = float(np.mean(lum))
    lum_std = float(np.std(lum))

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

    # Sharpening halo detection (gradient magnitude at edges)
    gx = cv2.Sobel(gray_uint8, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_uint8, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(gx**2 + gy**2)
    halo_score = float(np.percentile(grad_mag, 99))  # high gradient = potential halo

    return {
        "filename": os.path.basename(path),
        "width": w, "height": h,
        "iso": iso, "exposure_s": exp_s, "ev": ev,
        "f_number": str(exif_val(exif, 'FNumber')),
        "focal_length": str(exif_val(exif, 'FocalLength')),
        "software": str(exif_val(exif, 'Software')),
        "datetime": str(exif_val(exif, 'DateTime')),
        "lum_mean": lum_mean, "lum_std": lum_std,
        "r_mean": r_mean, "g_mean": g_mean, "b_mean": b_mean,
        "rb_ratio": rb_ratio, "rg_diff": rg_diff,
        "edge_density": edge_density,
        "black_clip_pct": black_clip, "white_clip_pct": white_clip,
        "halo_score": halo_score,
    }

def main():
    baseline_imgs = find_images(BASELINE_DIR)
    optimized_imgs = find_images(OPTIMIZED_DIR)

    print("Baseline images: " + str(len(baseline_imgs)))
    print("Optimized images: " + str(len(optimized_imgs)))

    if len(baseline_imgs) == 0 and len(optimized_imgs) == 0:
        print("\nNo images found. Please capture images first.")
        print("Place baseline captures in: " + BASELINE_DIR)
        print("Place optimized captures in: " + OPTIMIZED_DIR)
        return

    # Analyze baseline
    print("\nAnalyzing baseline images...")
    baseline_results = []
    for path in baseline_imgs:
        r = analyze_image(path)
        if r:
            r['config'] = 'baseline'
            baseline_results.append(r)
            print("  " + r['filename'] + " | R-G=" + str(round(r['rg_diff'],1)) + " | edge=" + str(round(r['edge_density'],3)) + " | black=" + str(round(r['black_clip_pct'],2)) + "% | white=" + str(round(r['white_clip_pct'],2)) + "% | lum_std=" + str(round(r['lum_std'],1)))

    # Analyze optimized
    print("\nAnalyzing optimized images...")
    optimized_results = []
    for path in optimized_imgs:
        r = analyze_image(path)
        if r:
            r['config'] = 'optimized'
            optimized_results.append(r)
            print("  " + r['filename'] + " | R-G=" + str(round(r['rg_diff'],1)) + " | edge=" + str(round(r['edge_density'],3)) + " | black=" + str(round(r['black_clip_pct'],2)) + "% | white=" + str(round(r['white_clip_pct'],2)) + "% | lum_std=" + str(round(r['lum_std'],1)))

    # Save individual results
    with open(os.path.join(OUT_DIR, "baseline_results.json"), 'w') as f:
        json.dump(baseline_results, f, indent=2, default=str)
    with open(os.path.join(OUT_DIR, "optimized_results.json"), 'w') as f:
        json.dump(optimized_results, f, indent=2, default=str)

    # Comparison
    if baseline_results and optimized_results:
        print("\n" + "="*60)
        print("A/B COMPARISON SUMMARY")
        print("="*60)

        metrics = ['rg_diff', 'rb_ratio', 'edge_density', 'black_clip_pct', 'white_clip_pct', 'lum_std', 'halo_score']
        metric_names = ['R-G (warm cast)', 'R/B ratio', 'Edge density', 'Black clip %', 'White clip %', 'Lum noise (std)', 'Halo score']

        print(f"\n{'Metric':<20} {'Baseline (median)':<20} {'Optimized (median)':<20} {'Winner':<15}")
        print("-" * 75)

        comparison = []
        for m, name in zip(metrics, metric_names):
            b_vals = [r[m] for r in baseline_results if r.get(m) is not None]
            o_vals = [r[m] for r in optimized_results if r.get(m) is not None]
            if not b_vals or not o_vals:
                continue
            b_med = np.median(b_vals)
            o_med = np.median(o_vals)

            # Determine winner (lower is better for warm cast, clipping, noise, halo; higher is better for edge density, R/B closer to 1.0)
            if m in ['rg_diff', 'black_clip_pct', 'white_clip_pct', 'lum_std', 'halo_score']:
                winner = 'Optimized' if o_med < b_med else 'Baseline' if b_med < o_med else 'Tie'
            elif m == 'edge_density':
                winner = 'Optimized' if o_med > b_med else 'Baseline' if b_med > o_med else 'Tie'
            elif m == 'rb_ratio':
                winner = 'Optimized' if abs(o_med - 1.0) < abs(b_med - 1.0) else 'Baseline' if abs(b_med - 1.0) < abs(o_med - 1.0) else 'Tie'
            else:
                winner = 'Tie'

            comparison.append({
                'metric': name,
                'baseline_median': float(b_med),
                'optimized_median': float(o_med),
                'baseline_min': float(min(b_vals)),
                'baseline_max': float(max(b_vals)),
                'optimized_min': float(min(o_vals)),
                'optimized_max': float(max(o_vals)),
                'winner': winner,
                'baseline_n': len(b_vals),
                'optimized_n': len(o_vals),
            })

            print(f"{name:<20} {b_med:<20.4f} {o_med:<20.4f} {winner:<15}")

        # Save comparison
        with open(os.path.join(OUT_DIR, "ab_comparison.json"), 'w') as f:
            json.dump(comparison, f, indent=2)

        # Count wins
        wins = Counter(c['winner'] for c in comparison)
        print(f"\nWins: Baseline={wins.get('Baseline',0)}, Optimized={wins.get('Optimized',0)}, Tie={wins.get('Tie',0)}")

        # Generate comparison plot
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            x = np.arange(len(comparison))
            width = 0.35
            b_vals = [c['baseline_median'] for c in comparison]
            o_vals = [c['optimized_median'] for c in comparison]
            ax.bar(x - width/2, b_vals, width, label='Baseline', color='blue', alpha=0.7)
            ax.bar(x + width/2, o_vals, width, label='Optimized', color='orange', alpha=0.7)
            ax.set_xticks(x)
            ax.set_xticklabels([c['metric'] for c in comparison], rotation=45, ha='right', fontsize=8)
            ax.set_title('A/B Comparison — Baseline vs Optimized (Median)')
            ax.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(PLOT_DIR, "ab_comparison.png"), dpi=150)
            plt.close()
            print("Saved: ab_comparison.png")
        except Exception as e:
            print("Plot error: " + str(e))

        # Generate per-metric box plots
        for m, name in zip(metrics, metric_names):
            b_vals = [r[m] for r in baseline_results if r.get(m) is not None]
            o_vals = [r[m] for r in optimized_results if r.get(m) is not None]
            if not b_vals or not o_vals:
                continue
            try:
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.boxplot([b_vals, o_vals], labels=['Baseline', 'Optimized'])
                ax.set_title(name)
                ax.set_ylabel(name)
                plt.tight_layout()
                safe_name = name.replace(' ', '_').replace('(', '').replace(')', '').replace('%', 'pct')
                plt.savefig(os.path.join(PLOT_DIR, f"ab_boxplot_{safe_name}.png"), dpi=150)
                plt.close()
            except Exception as e:
                print("Plot error: " + str(e))

        print("\nAll outputs in: " + OUT_DIR)
    else:
        print("\nNeed both baseline and optimized images for comparison.")
        print("Place baseline captures in: " + BASELINE_DIR)
        print("Place optimized captures in: " + OPTIMIZED_DIR)

if __name__ == "__main__":
    main()
