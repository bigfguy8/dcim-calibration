#!/usr/bin/env python3
"""Generate diagnostic plots and report for DCIM analysis"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\dcim_chart_audit"
PLOT_DIR = os.path.join(BASE_DIR, "plots")
JSON_PATH = os.path.join(BASE_DIR, "dcim_full_analysis.json")

os.makedirs(PLOT_DIR, exist_ok=True)

results = json.load(open(JSON_PATH))

# Separate LMC vs Stock
lmc = [r for r in results if 'lmc' in r.get('software', '').lower() or 'HDR+' in str(r.get('software', ''))]
stock = [r for r in results if 'MediaTek' in str(r.get('software', ''))]

# Plot 1: MTF50 by image
fig, ax = plt.subplots(figsize=(14, 6))
names = [r['filename'][:30] for r in results]
mtfs = [r['mtf50_cyc_px'] for r in results]
colors = ['green' if r['checkerboard_detected'] else ('blue' if 'lmc' in r.get('software', '').lower() else 'red') for r in results]
ax.bar(range(len(names)), mtfs, color=colors)
ax.set_xticks(range(len(names)))
ax.set_xticklabels(names, rotation=90, fontsize=5)
ax.set_ylabel('MTF50 (cyc/px)')
ax.set_title('MTF50 — All 39 DCIM Images (downscaled to 1024px max)')
ax.axhline(y=0.1, color='orange', linestyle='--', alpha=0.5, label='0.1 cyc/px reference')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "mtf50_all.png"), dpi=150)
plt.close()

# Plot 2: R/B ratio vs EV
fig, ax = plt.subplots(figsize=(10, 6))
for group, label, color in [(lmc, 'LMC 8.4', 'blue'), (stock, 'Stock Camera', 'red')]:
    evs = [r['ev'] for r in group if r.get('ev') is not None]
    rbs = [r['rb_ratio'] for r in group if r.get('ev') is not None]
    ax.scatter(evs, rbs, c=color, alpha=0.6, label=label, s=50)
ax.set_xlabel('EV')
ax.set_ylabel('R/B Ratio')
ax.set_title('White Balance vs Exposure — LMC vs Stock')
ax.axhline(y=1.0, color='black', linestyle='--', alpha=0.3, label='Neutral')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "rb_vs_ev.png"), dpi=150)
plt.close()

# Plot 3: Black clip vs EV
fig, ax = plt.subplots(figsize=(10, 6))
for group, label, color in [(lmc, 'LMC 8.4', 'blue'), (stock, 'Stock Camera', 'red')]:
    evs = [r['ev'] for r in group if r.get('ev') is not None]
    bclips = [r['black_clip_pct'] for r in group if r.get('ev') is not None]
    ax.scatter(evs, bclips, c=color, alpha=0.6, label=label, s=50)
ax.set_xlabel('EV')
ax.set_ylabel('Black Clip %')
ax.set_title('Black Clipping vs Exposure — LMC vs Stock')
ax.axhline(y=3.0, color='orange', linestyle='--', alpha=0.5, label='3% target')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "black_clip_vs_ev.png"), dpi=150)
plt.close()

# Plot 4: Edge density by image
fig, ax = plt.subplots(figsize=(14, 6))
names = [r['filename'][:30] for r in results]
edges = [r['edge_density'] for r in results]
colors = ['green' if r['checkerboard_detected'] else ('blue' if 'lmc' in r.get('software', '').lower() else 'red') for r in results]
ax.bar(range(len(names)), edges, color=colors)
ax.set_xticks(range(len(names)))
ax.set_xticklabels(names, rotation=90, fontsize=5)
ax.set_ylabel('Edge Density')
ax.set_title('Edge Density — All 39 DCIM Images')
ax.axhline(y=0.10, color='orange', linestyle='--', alpha=0.5, label='10% target')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "edge_density_all.png"), dpi=150)
plt.close()

# Plot 5: ISO vs EV
fig, ax = plt.subplots(figsize=(10, 6))
for group, label, color in [(lmc, 'LMC 8.4', 'blue'), (stock, 'Stock Camera', 'red')]:
    isos = [r['iso'] for r in group if r.get('iso') is not None]
    evs = [r['ev'] for r in group if r.get('ev') is not None]
    ax.scatter(evs, isos, c=color, alpha=0.6, label=label, s=50)
ax.set_xlabel('EV')
ax.set_ylabel('ISO')
ax.set_yscale('log')
ax.set_title('ISO vs Exposure — LMC vs Stock')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "iso_vs_ev.png"), dpi=150)
plt.close()

print("All plots saved to: " + PLOT_DIR)

# Print summary table
print("\n=== LMC 8.4 Images Summary ===")
print(f"{'Filename':<40} {'ISO':<6} {'EV':<6} {'R/B':<6} {'R-G':<6} {'Black%':<7} {'White%':<7} {'Edge%':<7} {'MTF50':<8} {'CB'}")
for r in sorted(lmc, key=lambda x: x.get('datetime', '')):
    print(f"{r['filename']:<40} {str(r.get('iso','')):<6} {str(r.get('ev','')):<6} {r['rb_ratio']:<6.3f} {r['rg_diff']:<6.1f} {r['black_clip_pct']:<7.2f} {r['white_clip_pct']:<7.2f} {r['edge_density']*100:<7.2f} {r['mtf50_cyc_px']:<8.4f} {str(r['checkerboard_detected'])}")

print("\n=== Stock Camera Images Summary ===")
print(f"{'Filename':<40} {'ISO':<6} {'EV':<6} {'R/B':<6} {'R-G':<6} {'Black%':<7} {'White%':<7} {'Edge%':<7} {'MTF50':<8} {'CB'}")
for r in sorted(stock, key=lambda x: x.get('datetime', '')):
    print(f"{r['filename']:<40} {str(r.get('iso','')):<6} {str(r.get('ev','')):<6} {r['rb_ratio']:<6.3f} {r['rg_diff']:<6.1f} {r['black_clip_pct']:<7.2f} {r['white_clip_pct']:<7.2f} {r['edge_density']*100:<7.2f} {r['mtf50_cyc_px']:<8.4f} {str(r['checkerboard_detected'])}")
