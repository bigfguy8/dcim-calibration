#!/usr/bin/env python3
"""Generate full-screen monitor calibration charts for Acer 1920x1080"""
import numpy as np
from PIL import Image, ImageDraw
import os
import json
import hashlib
from datetime import datetime

OUT_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\monitor_calibration\charts"
os.makedirs(OUT_DIR, exist_ok=True)

MON_W = 1920
MON_H = 1080
MON_DPI_EST = 93

def save_png(arr, name):
    path = os.path.join(OUT_DIR, name + ".png")
    img = Image.fromarray(arr.astype(np.uint8))
    img.save(path)
    h = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    print("Saved: " + name + ".png (" + str(arr.shape[1]) + "x" + str(arr.shape[0]) + ") sha256=" + h[:16] + "...")
    return path, h

# ============================================================
# 1. CHECKERBOARD
# ============================================================
sq_w = MON_W // 15
sq_h = MON_H // 8
cols = 15
rows = 8
cb = np.zeros((MON_H, MON_W, 3), dtype=np.uint8)
cb[:] = 255
for iy in range(rows):
    for ix in range(cols):
        x0 = ix * sq_w
        y0 = iy * sq_h
        x1 = min(x0 + sq_w, MON_W)
        y1 = min(y0 + sq_h, MON_H)
        if (ix + iy) % 2 == 0:
            cb[y0:y1, x0:x1] = 0
        else:
            cb[y0:y1, x0:x1] = 255

ruler_h = 60
ruler_y = MON_H - ruler_h
cb[ruler_y:, :] = 200
for x in range(0, MON_W, 100):
    tick_h = 30 if (x % 500 == 0) else 15
    cb[ruler_y:ruler_y+tick_h, x:x+2] = 0
for x in range(0, MON_W, 500):
    cb[ruler_y+35:ruler_y+55, x-1:x+2] = 0

cb_path, cb_hash = save_png(cb, "monitor_checkerboard_15x8")

# ============================================================
# 2. SLANTED EDGE
# ============================================================
se = np.ones((MON_H, MON_W, 3), dtype=np.uint8) * 255
block_w = MON_W // 5
block_h = MON_H // 3
spacing = MON_W // 20
start_x = spacing
start_y = (MON_H - block_h) // 2

for i in range(4):
    x0 = start_x + i * (block_w + spacing)
    y0 = start_y
    x1 = min(x0 + block_w, MON_W)
    y1 = min(y0 + block_h, MON_H)
    slant = np.tan(np.radians(5.0)) * block_h
    for y in range(y0, y1):
        slant_x = x0 + int((y - y0) * np.tan(np.radians(5.0)))
        se[y, x0:min(slant_x, x1)] = 0

se_path, se_hash = save_png(se, "monitor_slanted_edge_5deg")

# ============================================================
# 3. SIEMENS STAR
# ============================================================
ss = np.ones((MON_H, MON_W, 3), dtype=np.uint8) * 255
cx, cy = MON_W // 2, MON_H // 2
radius = min(MON_W, MON_H) // 2 - 50
num_spokes = 36

from matplotlib.patches import Wedge
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(MON_W/100, MON_H/100), dpi=100)
ax.set_xlim(0, MON_W)
ax.set_ylim(0, MON_H)
ax.set_aspect('equal')

for i in range(num_spokes):
    angle_start = i * 360 / num_spokes
    angle_end = (i + 1) * 360 / num_spokes
    if i % 2 == 0:
        wedge = Wedge((cx, cy), radius, angle_start, angle_end, facecolor='black', edgecolor='none')
    else:
        wedge = Wedge((cx, cy), radius, angle_start, angle_end, facecolor='white', edgecolor='none')
    ax.add_patch(wedge)

center_circle = plt.Circle((cx, cy), 30, facecolor='white', edgecolor='black', linewidth=0.5)
ax.add_patch(center_circle)
outer_circle = plt.Circle((cx, cy), radius, fill=False, edgecolor='black', linewidth=1)
ax.add_patch(outer_circle)

ax.set_axis_off()
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
ss_path = os.path.join(OUT_DIR, "monitor_siemens_star_36.png")
fig.savefig(ss_path, dpi=100)
plt.close(fig)
# Re-read to get hash
ss_hash = hashlib.sha256(open(ss_path, 'rb').read()).hexdigest()
print("Saved: monitor_siemens_star_36.png (" + str(MON_W) + "x" + str(MON_H) + ") sha256=" + ss_hash[:16] + "...")

# ============================================================
# 4. GRAYSCALE WEDGE
# ============================================================
gw = np.ones((MON_H, MON_W, 3), dtype=np.uint8) * 255
num_steps = 11
step_w = MON_W // num_steps
bar_h = MON_H // 3
bar_y0 = (MON_H - bar_h) // 2

for i in range(num_steps):
    val = int(i * 255 / (num_steps - 1))
    x0 = i * step_w
    x1 = min(x0 + step_w, MON_W)
    gw[bar_y0:bar_y0+bar_h, x0:x1] = val

ruler_y = bar_y0 + bar_h + 20
gw[ruler_y:ruler_y+2, :] = 0
for x in range(0, MON_W, 100):
    tick_h = 20 if (x % 500 == 0) else 10
    gw[ruler_y:ruler_y+tick_h, x:x+2] = 0

gw_path, gw_hash = save_png(gw, "monitor_grayscale_wedge_11")

# ============================================================
# 5. COLOR PATCHES (synthetic, NOT verified ColorChecker)
# ============================================================
cp = np.ones((MON_H, MON_W, 3), dtype=np.uint8) * 128
patch_size = 200
cols = 6
rows = 4
spacing = 30
total_w = cols * patch_size + (cols-1) * spacing
total_h = rows * patch_size + (rows-1) * spacing
start_x = (MON_W - total_w) // 2
start_y = (MON_H - total_h) // 2

colors = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255),
    (128, 0, 0), (0, 128, 0), (0, 0, 128), (128, 128, 0), (128, 0, 128), (0, 128, 128),
    (255, 128, 0), (128, 255, 0), (0, 128, 255), (255, 0, 128), (128, 0, 255), (0, 255, 128),
    (64, 64, 64), (128, 128, 128), (192, 192, 192), (255, 255, 255), (0, 0, 0), (32, 32, 32),
]

for idx, color in enumerate(colors):
    iy = idx // cols
    ix = idx % cols
    x0 = start_x + ix * (patch_size + spacing)
    y0 = start_y + iy * (patch_size + spacing)
    x1 = x0 + patch_size
    y1 = y0 + patch_size
    cp[y0:y1, x0:x1] = color

cp_path, cp_hash = save_png(cp, "monitor_color_patches_24")

# ============================================================
# MANIFEST
# ============================================================
manifest = {
    "generated": datetime.now().isoformat(),
    "monitor": {
        "brand": "Acer (ACR0FDD)",
        "resolution": f"{MON_W}x{MON_H}",
        "refresh_rate": "120 Hz",
        "physical_size_cm": "53x29",
        "estimated_dpi": MON_DPI_EST,
        "bits_per_pixel": 32,
    },
    "charts": [
        {"name": "Checkerboard", "file": "monitor_checkerboard_15x8.png", "pixels": f"{MON_W}x{MON_H}", "squares": f"{cols}x{rows}", "square_px": f"{sq_w}x{sq_h}", "sha256": cb_hash},
        {"name": "Slanted-Edge", "file": "monitor_slanted_edge_5deg.png", "pixels": f"{MON_W}x{MON_H}", "slant_deg": 5.0, "sha256": se_hash},
        {"name": "Siemens Star", "file": "monitor_siemens_star_36.png", "pixels": f"{MON_W}x{MON_H}", "spokes": 36, "radius_px": radius, "sha256": ss_hash},
        {"name": "Grayscale Wedge", "file": "monitor_grayscale_wedge_11.png", "pixels": f"{MON_W}x{MON_H}", "steps": 11, "sha256": gw_hash},
        {"name": "Color Patches", "file": "monitor_color_patches_24.png", "pixels": f"{MON_W}x{MON_H}", "patches": 24, "sha256": cp_hash, "note": "Synthetic colors, NOT verified ColorChecker references"},
    ],
    "limitations": [
        "Monitor pixel structure (RGB subpixels) affects measurements",
        "Moiré between monitor and camera sensor is present",
        "Display color accuracy depends on monitor calibration",
        "All measurements are comparative estimates, not absolute",
        "No physical dimension verification possible",
        "Color patches are synthetic, not verified reference values",
    ],
}

manifest_path = os.path.join(OUT_DIR, "monitor_chart_manifest.json")
with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)
print("Saved: " + manifest_path)

print_instr = """MONITOR CALIBRATION CAPTURE INSTRUCTIONS
========================================

DISPLAY SETTINGS (Acer Monitor):
  - Native resolution: 1920x1080 @ 120Hz
  - Estimated DPI: ~93 (53x29cm physical)
  - Disable: HDR, dynamic contrast, night mode, auto-brightness
  - Set brightness to fixed level (record value)
  - Set color temperature to 6500K if available

CHART DISPLAY:
  - Display each PNG full-screen (no scaling, no fit-to-screen)
  - Use image viewer in full-screen mode
  - Verify no taskbar/overlays visible
  - Record monitor brightness/contrast settings

CAPTURE PROCEDURE:
  1. Position phone perpendicular to screen, centered
  2. Record distance from phone to screen (cm)
  3. Dim room lighting (screen as sole light source)
  4. Avoid reflections, glare, moire
  5. Focus on chart center
  6. Capture 3 images per chart
  7. Record EXIF: ISO, shutter, aperture, EV
  8. Repeat for each chart

CONFIG: Baseline (default .xml) - verify active before each capture

LIMITATIONS:
  - Monitor pixels create moire with camera sensor
  - Display color is not calibrated (no verified reference)
  - All measurements are comparative, not absolute
  - Do not claim true sensor MTF or absolute color accuracy
"""
instr_path = os.path.join(OUT_DIR, "MONITOR_CAPTURE_INSTRUCTIONS.txt")
with open(instr_path, 'w') as f:
    f.write(print_instr)
print("Saved: " + instr_path)
print("\nAll monitor charts generated in: " + OUT_DIR)
