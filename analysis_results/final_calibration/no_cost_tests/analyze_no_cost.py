#!/usr/bin/env python3
"""No-Cost IMX682 Optimization Analysis"""
import os, sys, json, csv, hashlib
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import Counter, defaultdict

BASE = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration"
OUT = os.path.join(BASE, "analysis_results", "final_calibration", "no_cost_tests")
PLOTS = os.path.join(OUT, "plots")
os.makedirs(PLOTS, exist_ok=True)

# Load all analysis data
dcim_data = json.load(open(os.path.join(BASE, "analysis_results", "dcim_chart_audit", "dcim_full_analysis.json")))
monitor_data = json.load(open(os.path.join(BASE, "analysis_results", "final_calibration", "monitor_calibration", "monitor_all_captures_analysis.json")))

# Also load recapture_v12 data
recapture_path = os.path.join(BASE, "recapture_v12", "Camera", "analysis", "analysis_results.json")
recapture_data = json.load(open(recapture_path)) if os.path.exists(recapture_path) else []

print("Loaded datasets:")
print(f"  DCIM: {len(dcim_data)} images")
print(f"  Monitor: {len(monitor_data)} images")
print(f"  Recapture: {len(recapture_data)} images")

# ============================================================
# 1. CATEGORIZE BY CAMERA SOURCE
# ============================================================
def classify_source(r):
    sw = str(r.get('software', '')).lower()
    if 'hdr+' in sw:
        return 'LMC_8.4'
    elif 'mediatek' in sw:
        return 'Stock'
    else:
        return 'Unknown'

# Combine all data
all_data = []
for r in dcim_data:
    r['source'] = classify_source(r)
    r['dataset'] = 'dcim'
    all_data.append(r)
for r in monitor_data:
    r['source'] = classify_source(r)
    r['dataset'] = 'monitor'
    all_data.append(r)

print(f"\nTotal images: {len(all_data)}")
sources = Counter(r['source'] for r in all_data)
for s, n in sources.items():
    print(f"  {s}: {n}")

# ============================================================
# 2. LMC vs STOCK COMPARISON
# ============================================================
print("\n" + "="*60)
print("LMC 8.4 vs STOCK CAMERA COMPARISON")
print("="*60)

for src in ['LMC_8.4', 'Stock']:
    subset = [r for r in all_data if r['source'] == src]
    if not subset:
        continue
    print(f"\n--- {src} ({len(subset)} images) ---")

    # Warm cast
    rg_diffs = [r['rg_diff'] for r in subset if r.get('rg_diff') is not None]
    rb_ratios = [r['rb_ratio'] for r in subset if r.get('rb_ratio') is not None]
    print(f"  R-G warm cast: min={min(rg_diffs):.1f}, max={max(rg_diffs):.1f}, mean={np.mean(rg_diffs):.1f}")
    print(f"  R/B ratio: min={min(rb_ratios):.3f}, max={max(rb_ratios):.3f}, mean={np.mean(rb_ratios):.3f}")

    # Clipping
    black_clips = [r['black_clip_pct'] for r in subset]
    white_clips = [r['white_clip_pct'] for r in subset]
    print(f"  Black clip %: min={min(black_clips):.2f}, max={max(black_clips):.2f}, mean={np.mean(black_clips):.2f}")
    print(f"  White clip %: min={min(white_clips):.2f}, max={max(white_clips):.2f}, mean={np.mean(white_clips):.2f}")

    # Edge density
    edges = [r['edge_density'] for r in subset]
    print(f"  Edge density: min={min(edges):.4f}, max={max(edges):.4f}, mean={np.mean(edges):.4f}")

    # MTF50
    mtfs = [r['mtf50_cyc_px'] for r in subset]
    print(f"  MTF50 (cyc/px): min={min(mtfs):.4f}, max={max(mtfs):.4f}, mean={np.mean(mtfs):.4f}")

    # EV range
    evs = [r['ev'] for r in subset if r.get('ev') is not None]
    print(f"  EV range: {min(evs):.2f} to {max(evs):.2f}")

    # ISO range
    isos = [r['iso'] for r in subset if r.get('iso') is not None]
    print(f"  ISO range: {min(isos)} to {max(isos)}")

# ============================================================
# 3. EXPOSURE ANALYSIS
# ============================================================
print("\n" + "="*60)
print("EXPOSURE ANALYSIS")
print("="*60)

# Group by EV buckets
ev_buckets = defaultdict(list)
for r in all_data:
    ev = r.get('ev')
    if ev is not None:
        bucket = round(ev)
        ev_buckets[bucket].append(r)

print("\nImages by EV bucket:")
for bucket in sorted(ev_buckets.keys()):
    rs = ev_buckets[bucket]
    lmc = [r for r in rs if r['source'] == 'LMC_8.4']
    stock = [r for r in rs if r['source'] == 'Stock']
    print(f"  EV ~{bucket}: LMC={len(lmc)}, Stock={len(stock)}, total={len(rs)}")
    if lmc:
        print(f"    LMC black_clip={np.mean([r['black_clip_pct'] for r in lmc]):.2f}%, white_clip={np.mean([r['white_clip_pct'] for r in lmc]):.2f}%")
    if stock:
        print(f"    Stock black_clip={np.mean([r['black_clip_pct'] for r in stock]):.2f}%, white_clip={np.mean([r['white_clip_pct'] for r in stock]):.2f}%")

# ============================================================
# 4. ISO vs NOISE ANALYSIS
# ============================================================
print("\n" + "="*60)
print("ISO vs NOISE ANALYSIS")
print("="*60)

iso_buckets = [(0, 200), (200, 400), (400, 800), (800, 1600), (1600, 3200), (3200, 10000)]
for lo, hi in iso_buckets:
    subset = [r for r in all_data if r.get('iso') and lo <= r['iso'] < hi]
    if not subset:
        continue
    lmc = [r for r in subset if r['source'] == 'LMC_8.4']
    stock = [r for r in subset if r['source'] == 'Stock']
    print(f"\nISO {lo}-{hi}:")
    print(f"  Total: {len(subset)} (LMC={len(lmc)}, Stock={len(stock)})")
    if lmc:
        print(f"  LMC: lum_std={np.mean([r['lum_std'] for r in lmc]):.1f}, black_clip={np.mean([r['black_clip_pct'] for r in lmc]):.2f}%")
    if stock:
        print(f"  Stock: lum_std={np.mean([r['lum_std'] for r in stock]):.1f}, black_clip={np.mean([r['black_clip_pct'] for r in stock]):.2f}%")

# ============================================================
# 5. MONITOR MOIRÉ ANALYSIS
# ============================================================
print("\n" + "="*60)
print("MONITOR MOIRÉ ANALYSIS")
print("="*60)

monitor = [r for r in all_data if r['dataset'] == 'monitor']
print(f"Monitor captures: {len(monitor)}")
print(f"Moiré score range: {min(r['moire_score'] for r in monitor):.1f} to {max(r['moire_score'] for r in monitor):.1f}")
print(f"Mean moiré: {np.mean([r['moire_score'] for r in monitor]):.1f}")

# Group by moiré severity
low_moire = [r for r in monitor if r['moire_score'] < 1000]
mid_moire = [r for r in monitor if 1000 <= r['moire_score'] < 2000]
high_moire = [r for r in monitor if r['moire_score'] >= 2000]
print(f"Low moiré (<1000): {len(low_moire)} images")
print(f"Mid moiré (1000-2000): {len(mid_moire)} images")
print(f"High moiré (>=2000): {len(high_moire)} images")

if low_moire:
    print(f"\nBest (lowest moiré) images:")
    for r in sorted(low_moire, key=lambda x: x['moire_score'])[:5]:
        print(f"  {r['filename']}: moire={r['moire_score']:.1f}, EV={r['ev']}, ISO={r['iso']}, R/B={r['rb_ratio']:.3f}")

# ============================================================
# 6. CONFIG COMPARISON (Baseline vs Optimized)
# ============================================================
print("\n" + "="*60)
print("CONFIG COMPARISON — Baseline vs Optimized")
print("="*60)

import xml.etree.ElementTree as ET
base_path = os.path.join(BASE, "analysis_results", "imx682_config", "original_V2_Release_Day.xml")
opt_path = os.path.join(BASE, "analysis_results", "imx682_config", "LXX521_LMC84_Optimized_Corrected.xml")
desktop_path = r"C:\Users\l\Desktop\default .xml"

def get_keys(path):
    tree = ET.parse(path)
    keys = {}
    for el in tree.getroot().findall('string'):
        keys[el.get('name')] = el.text
    return keys

base_keys = get_keys(base_path)
opt_keys = get_keys(opt_path)
desktop_keys = get_keys(desktop_path)

print("\nDesktop baseline (working) vs Optimized_Corrected:")
diff = []
for k in desktop_keys:
    if desktop_keys[k] != opt_keys.get(k):
        diff.append((k, desktop_keys[k], opt_keys.get(k)))
print(f"  Total differing keys: {len(diff)}")
for k, old, new in diff:
    print(f"  {k}: {old} -> {new}")

# ============================================================
# 7. GENERATE PLOTS
# ============================================================
print("\n" + "="*60)
print("GENERATING PLOTS")
print("="*60)

# Plot 1: LMC vs Stock R-G warm cast distribution
fig, ax = plt.subplots(figsize=(10, 6))
lmc_rg = [r['rg_diff'] for r in all_data if r['source'] == 'LMC_8.4']
stock_rg = [r['rg_diff'] for r in all_data if r['source'] == 'Stock']
ax.hist(lmc_rg, bins=20, alpha=0.6, label=f'LMC 8.4 (n={len(lmc_rg)})', color='blue')
ax.hist(stock_rg, bins=20, alpha=0.6, label=f'Stock (n={len(stock_rg)})', color='red')
ax.set_xlabel('R-G (warm cast)')
ax.set_ylabel('Count')
ax.set_title('Warm Cast Distribution — LMC vs Stock')
ax.axvline(x=4.0, color='green', linestyle='--', label='Target <4.0')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(PLOTS, "warm_cast_distribution.png"), dpi=150)
plt.close()
print("Saved: warm_cast_distribution.png")

# Plot 2: Black clip vs EV (LMC vs Stock)
fig, ax = plt.subplots(figsize=(10, 6))
for src, color, label in [('LMC_8.4', 'blue', 'LMC 8.4'), ('Stock', 'red', 'Stock')]:
    subset = [r for r in all_data if r['source'] == src and r.get('ev') is not None]
    evs = [r['ev'] for r in subset]
    clips = [r['black_clip_pct'] for r in subset]
    ax.scatter(evs, clips, c=color, alpha=0.5, label=label, s=30)
ax.set_xlabel('EV')
ax.set_ylabel('Black Clip %')
ax.set_title('Black Clipping vs Exposure — LMC vs Stock')
ax.axhline(y=3.0, color='orange', linestyle='--', alpha=0.5, label='3% target')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(PLOTS, "black_clip_vs_ev.png"), dpi=150)
plt.close()
print("Saved: black_clip_vs_ev.png")

# Plot 3: Moiré severity distribution
fig, ax = plt.subplots(figsize=(10, 6))
moires = [r['moire_score'] for r in monitor]
ax.hist(moires, bins=20, alpha=0.7, color='purple')
ax.set_xlabel('Moiré Score')
ax.set_ylabel('Count')
ax.set_title('Moiré Severity — Monitor Captures (32 images)')
ax.axvline(x=1000, color='orange', linestyle='--', alpha=0.5, label='1000 (moderate)')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(PLOTS, "moire_distribution.png"), dpi=150)
plt.close()
print("Saved: moire_distribution.png")

# Plot 4: ISO vs Black Clip
fig, ax = plt.subplots(figsize=(10, 6))
for src, color, label in [('LMC_8.4', 'blue', 'LMC 8.4'), ('Stock', 'red', 'Stock')]:
    subset = [r for r in all_data if r['source'] == src and r.get('iso')]
    isos = [r['iso'] for r in subset]
    clips = [r['black_clip_pct'] for r in subset]
    ax.scatter(isos, clips, c=color, alpha=0.5, label=label, s=30)
ax.set_xlabel('ISO')
ax.set_ylabel('Black Clip %')
ax.set_xscale('log')
ax.set_title('Noise/Clipping vs ISO — LMC vs Stock')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(PLOTS, "iso_vs_blackclip.png"), dpi=150)
plt.close()
print("Saved: iso_vs_blackclip.png")

# Plot 5: Edge density by source
fig, ax = plt.subplots(figsize=(10, 6))
lmc_edges = [r['edge_density'] for r in all_data if r['source'] == 'LMC_8.4']
stock_edges = [r['edge_density'] for r in all_data if r['source'] == 'Stock']
ax.hist(lmc_edges, bins=20, alpha=0.6, label=f'LMC 8.4 (n={len(lmc_edges)})', color='blue')
ax.hist(stock_edges, bins=20, alpha=0.6, label=f'Stock (n={len(stock_edges)})', color='red')
ax.set_xlabel('Edge Density')
ax.set_ylabel('Count')
ax.set_title('Edge Density Distribution — LMC vs Stock')
ax.axvline(x=0.10, color='green', linestyle='--', label='10% target')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(PLOTS, "edge_density_distribution.png"), dpi=150)
plt.close()
print("Saved: edge_density_distribution.png")

# ============================================================
# 8. SAVE SUMMARY METRICS
# ============================================================
summary = {
    "total_images": len(all_data),
    "lmc_images": len([r for r in all_data if r['source'] == 'LMC_8.4']),
    "stock_images": len([r for r in all_data if r['source'] == 'Stock']),
    "lmc_warm_cast_rg": {
        "min": float(min(r['rg_diff'] for r in all_data if r['source'] == 'LMC_8.4')),
        "max": float(max(r['rg_diff'] for r in all_data if r['source'] == 'LMC_8.4')),
        "mean": float(np.mean([r['rg_diff'] for r in all_data if r['source'] == 'LMC_8.4'])),
    },
    "stock_warm_cast_rg": {
        "min": float(min(r['rg_diff'] for r in all_data if r['source'] == 'Stock')),
        "max": float(max(r['rg_diff'] for r in all_data if r['source'] == 'Stock')),
        "mean": float(np.mean([r['rg_diff'] for r in all_data if r['source'] == 'Stock'])),
    },
    "lmc_black_clip_mean": float(np.mean([r['black_clip_pct'] for r in all_data if r['source'] == 'LMC_8.4'])),
    "stock_black_clip_mean": float(np.mean([r['black_clip_pct'] for r in all_data if r['source'] == 'Stock'])),
    "lmc_white_clip_mean": float(np.mean([r['white_clip_pct'] for r in all_data if r['source'] == 'LMC_8.4'])),
    "stock_white_clip_mean": float(np.mean([r['white_clip_pct'] for r in all_data if r['source'] == 'Stock'])),
    "monitor_moire_range": [float(min(r['moire_score'] for r in monitor)), float(max(r['moire_score'] for r in monitor))],
    "monitor_checkerboard_count": 0,
    "config_comparison": {
        "desktop_baseline_hash": hashlib.sha256(open(desktop_path, 'rb').read()).hexdigest(),
        "optimized_corrected_hash": hashlib.sha256(open(opt_path, 'rb').read()).hexdigest(),
        "keys_changed": len(diff),
    },
}

summary_path = os.path.join(OUT, "no_cost_summary.json")
with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2)
print("\nSaved: " + summary_path)

# Save CSV of all data
csv_path = os.path.join(OUT, "no_cost_all_data.csv")
keys = ['filename', 'source', 'dataset', 'iso', 'ev', 'rb_ratio', 'rg_diff', 'black_clip_pct', 'white_clip_pct', 'edge_density', 'mtf50_cyc_px', 'moire_score']
with open(csv_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    for r in all_data:
        w.writerow({k: r.get(k) for k in keys})
print("Saved: " + csv_path)

print("\n=== NO-COST ANALYSIS COMPLETE ===")
print("Outputs in: " + OUT)
