#!/usr/bin/env python3
"""Generate contact sheets for baseline reconciliation"""
import os, json
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison\baseline"
OUT = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison"

files = sorted(os.listdir(BASE))
print(f"Creating contact sheet for {len(files)} images")

# Create grid of thumbnails
cols = 6
rows = (len(files) + cols - 1) // cols
fig, axes = plt.subplots(rows, cols, figsize=(cols*3, rows*2.5))
axes = axes.flatten()

for i, f in enumerate(files):
    path = os.path.join(BASE, f)
    img = Image.open(path)
    # Create thumbnail
    thumb = img.copy()
    thumb.thumbnail((300, 225))
    axes[i].imshow(thumb)
    axes[i].set_title(f[:20], fontsize=6)
    axes[i].axis('off')

for i in range(len(files), len(axes)):
    axes[i].axis('off')

plt.tight_layout()
plt.savefig(os.path.join(OUT, "baseline_contact_sheet.png"), dpi=100)
plt.close()
print("Saved: baseline_contact_sheet.png")

# Also create a smaller contact sheet with just filenames
fig, ax = plt.subplots(figsize=(12, 8))
ax.axis('off')
text = "BASELINE CAPTURE INVENTORY\n" + "="*60 + "\n"
for i, f in enumerate(files):
    text += f"{i+1:2d}. {f}\n"
ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=8,
        verticalalignment='top', fontfamily='monospace')
plt.savefig(os.path.join(OUT, "baseline_inventory_text.png"), dpi=100)
plt.close()
print("Saved: baseline_inventory_text.png")
print("Done.")
