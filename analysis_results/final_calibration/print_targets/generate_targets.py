#!/usr/bin/env python3
"""Generate print-ready calibration targets for IMX682"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
import numpy as np
import os
import hashlib
import json
from datetime import datetime

OUT_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\print_targets"
os.makedirs(OUT_DIR, exist_ok=True)

DPI = 300
PAGE_W = 8.27
PAGE_H = 11.69

SQUARE_MM = 20.0
SQUARE_IN = SQUARE_MM / 25.4
SQUARE_PX = int(SQUARE_IN * DPI)

CB_COLS = 9
CB_ROWS = 6
CB_SQUARES_X = CB_COLS + 1
CB_SQUARES_Y = CB_ROWS + 1
CB_WIDTH_IN = CB_SQUARES_X * SQUARE_IN
CB_HEIGHT_IN = CB_SQUARES_Y * SQUARE_IN

# ============================================================
# 1. CHECKERBOARD
# ============================================================
fig, ax = plt.subplots(figsize=(PAGE_W, PAGE_H))
ax.set_xlim(0, PAGE_W)
ax.set_ylim(0, PAGE_H)
ax.set_aspect('equal')

cb_x0 = (PAGE_W - CB_WIDTH_IN) / 2
cb_y0 = (PAGE_H - CB_HEIGHT_IN) / 2 - 0.5

for iy in range(CB_SQUARES_Y):
    for ix in range(CB_SQUARES_X):
        x = cb_x0 + ix * SQUARE_IN
        y = cb_y0 + (CB_SQUARES_Y - 1 - iy) * SQUARE_IN
        if (ix + iy) % 2 == 0:
            rect = plt.Rectangle((x, y), SQUARE_IN, SQUARE_IN, facecolor='black', edgecolor='none')
        else:
            rect = plt.Rectangle((x, y), SQUARE_IN, SQUARE_IN, facecolor='white', edgecolor='none')
        ax.add_patch(rect)

border = plt.Rectangle((cb_x0, cb_y0), CB_WIDTH_IN, CB_HEIGHT_IN,
                        fill=False, edgecolor='black', linewidth=1)
ax.add_patch(border)

ax.text(PAGE_W/2, PAGE_H - 0.3, "Checkerboard Calibration Target", ha='center', va='top',
        fontsize=14, fontweight='bold')
ax.text(PAGE_W/2, PAGE_H - 0.5, f"Internal corners: {CB_COLS}x{CB_ROWS} | Squares: {CB_SQUARES_X}x{CB_SQUARES_Y} | Nominal square: {SQUARE_MM}mm",
        ha='center', va='top', fontsize=9)

ruler_y = cb_y0 - 0.6
ruler_x0 = cb_x0
ruler_len = CB_WIDTH_IN
ax.plot([ruler_x0, ruler_x0 + ruler_len], [ruler_y, ruler_y], 'k-', linewidth=1)
for mm in range(0, int(CB_WIDTH_IN * 25.4) + 1, 10):
    x = ruler_x0 + mm / 25.4
    if mm % 50 == 0:
        ax.plot([x, x], [ruler_y, ruler_y - 0.15], 'k-', linewidth=1)
        ax.text(x, ruler_y - 0.2, f'{mm}mm', ha='center', va='top', fontsize=7)
    else:
        ax.plot([x, x], [ruler_y, ruler_y - 0.08], 'k-', linewidth=0.5)

ax.text(PAGE_W/2, 0.3, "PRINT INSTRUCTIONS: 100% scale, no fit-to-page, matte paper. Verify square dimensions with calipers after printing.",
        ha='center', va='bottom', fontsize=8, style='italic')

ax.set_axis_off()
cb_path = os.path.join(OUT_DIR, "checkerboard_9x6_20mm.pdf")
fig.savefig(cb_path, dpi=DPI, bbox_inches='tight', pad_inches=0.1)
plt.close(fig)
print("Saved: " + cb_path)

# ============================================================
# 2. SLANTED-EDGE TARGET
# ============================================================
fig, ax = plt.subplots(figsize=(PAGE_W, PAGE_H))
ax.set_xlim(0, PAGE_W)
ax.set_ylim(0, PAGE_H)
ax.set_aspect('equal')

edge_block_size = 2.0
num_edges = 4
spacing = 0.3
total_w = num_edges * edge_block_size + (num_edges-1) * spacing
start_x = (PAGE_W - total_w) / 2
start_y = PAGE_H / 2 - 0.5

for i in range(num_edges):
    x = start_x + i * (edge_block_size + spacing)
    y = start_y
    slant = np.tan(np.radians(5.0)) * edge_block_size
    pts_slant = np.array([
        [x, y],
        [x + edge_block_size, y + slant],
        [x + edge_block_size, y + edge_block_size + slant],
        [x, y + edge_block_size],
    ])
    rect_white = plt.Rectangle((x, y), edge_block_size, edge_block_size, facecolor='white', edgecolor='black', linewidth=0.5)
    ax.add_patch(rect_white)
    poly_black = plt.Polygon(pts_slant, facecolor='black', edgecolor='none')
    ax.add_patch(poly_black)

ax.text(PAGE_W/2, PAGE_H - 0.3, "Slanted-Edge MTF Target (ISO 12233 Style)", ha='center', va='top',
        fontsize=14, fontweight='bold')
ax.text(PAGE_W/2, PAGE_H - 0.5, "Slant angle: 5 deg | Edge blocks: 4 | Block size: 2.0 in (50.8mm)",
        ha='center', va='top', fontsize=9)

ruler_y = start_y - 0.5
ruler_x0 = start_x
ruler_len = total_w
ax.plot([ruler_x0, ruler_x0 + ruler_len], [ruler_y, ruler_y], 'k-', linewidth=1)
for mm in range(0, int(ruler_len * 25.4) + 1, 10):
    x = ruler_x0 + mm / 25.4
    if mm % 50 == 0:
        ax.plot([x, x], [ruler_y, ruler_y - 0.15], 'k-', linewidth=1)
        ax.text(x, ruler_y - 0.2, f'{mm}mm', ha='center', va='top', fontsize=7)
    else:
        ax.plot([x, x], [ruler_y, ruler_y - 0.08], 'k-', linewidth=0.5)

ax.text(PAGE_W/2, 0.3, "PRINT INSTRUCTIONS: 100% scale, no fit-to-page, matte paper. Slant angle 5 deg for MTF analysis.",
        ha='center', va='bottom', fontsize=8, style='italic')

ax.set_axis_off()
se_path = os.path.join(OUT_DIR, "slanted_edge_iso12233.pdf")
fig.savefig(se_path, dpi=DPI, bbox_inches='tight', pad_inches=0.1)
plt.close(fig)
print("Saved: " + se_path)

# ============================================================
# 3. SIEMENS STAR
# ============================================================
fig, ax = plt.subplots(figsize=(PAGE_W, PAGE_H))
ax.set_xlim(0, PAGE_W)
ax.set_ylim(0, PAGE_H)
ax.set_aspect('equal')

star_center = (PAGE_W/2, PAGE_H/2 - 0.3)
star_radius = 3.0
num_spokes = 36

for i in range(num_spokes):
    angle_start = i * 360 / num_spokes
    angle_end = (i + 1) * 360 / num_spokes
    if i % 2 == 0:
        wedge = Wedge(star_center, star_radius, angle_start, angle_end, facecolor='black', edgecolor='none')
    else:
        wedge = Wedge(star_center, star_radius, angle_start, angle_end, facecolor='white', edgecolor='none')
    ax.add_patch(wedge)

center_circle = plt.Circle(star_center, 0.15, facecolor='white', edgecolor='black', linewidth=0.5)
ax.add_patch(center_circle)
outer_circle = plt.Circle(star_center, star_radius, fill=False, edgecolor='black', linewidth=1)
ax.add_patch(outer_circle)

ax.text(PAGE_W/2, PAGE_H - 0.3, "Siemens Star Resolution Target", ha='center', va='top',
        fontsize=14, fontweight='bold')
ax.text(PAGE_W/2, PAGE_H - 0.5, f"Spokes: {num_spokes} | Diameter: {star_radius*2:.1f} in ({star_radius*2*25.4:.0f}mm)",
        ha='center', va='top', fontsize=9)

ruler_y = star_center[1] - star_radius - 0.6
ruler_x0 = star_center[0] - star_radius
ruler_len = star_radius * 2
ax.plot([ruler_x0, ruler_x0 + ruler_len], [ruler_y, ruler_y], 'k-', linewidth=1)
for mm in range(0, int(ruler_len * 25.4) + 1, 10):
    x = ruler_x0 + mm / 25.4
    if mm % 50 == 0:
        ax.plot([x, x], [ruler_y, ruler_y - 0.15], 'k-', linewidth=1)
        ax.text(x, ruler_y - 0.2, f'{mm}mm', ha='center', va='top', fontsize=7)
    else:
        ax.plot([x, x], [ruler_y, ruler_y - 0.08], 'k-', linewidth=0.5)

ax.text(PAGE_W/2, 0.3, "PRINT INSTRUCTIONS: 100% scale, no fit-to-page, matte paper. Siemens star for resolution/aliasing test.",
        ha='center', va='bottom', fontsize=8, style='italic')

ax.set_axis_off()
ss_path = os.path.join(OUT_DIR, "siemens_star_36spoke.pdf")
fig.savefig(ss_path, dpi=DPI, bbox_inches='tight', pad_inches=0.1)
plt.close(fig)
print("Saved: " + ss_path)

# ============================================================
# 4. GRAYSCALE STEP WEDGE
# ============================================================
fig, ax = plt.subplots(figsize=(PAGE_W, PAGE_H))
ax.set_xlim(0, PAGE_W)
ax.set_ylim(0, PAGE_H)
ax.set_aspect('equal')

num_steps = 11
step_w = 1.5
step_h = 1.0
total_w = num_steps * step_w
start_x = (PAGE_W - total_w) / 2
start_y = PAGE_H / 2 - 0.5

for i in range(num_steps):
    val = int(i * 255 / (num_steps - 1))
    x = start_x + i * step_w
    y = start_y
    rect = plt.Rectangle((x, y), step_w, step_h, facecolor=str(val/255), edgecolor='black', linewidth=0.5)
    ax.add_patch(rect)
    ax.text(x + step_w/2, y - 0.15, f'{val}', ha='center', va='top', fontsize=8)
    ax.text(x + step_w/2, y + step_h + 0.05, f'{val/255*100:.0f}%', ha='center', va='bottom', fontsize=7)

ax.text(PAGE_W/2, PAGE_H - 0.3, "Grayscale Step Wedge (Relative Tonal Response)", ha='center', va='top',
        fontsize=14, fontweight='bold')
ax.text(PAGE_W/2, PAGE_H - 0.5, f"Steps: {num_steps} (0 to 255) | Step width: {step_w} in ({step_w*25.4:.0f}mm)",
        ha='center', va='top', fontsize=9)

ruler_y = start_y - 0.5
ruler_x0 = start_x
ruler_len = total_w
ax.plot([ruler_x0, ruler_x0 + ruler_len], [ruler_y, ruler_y], 'k-', linewidth=1)
for mm in range(0, int(ruler_len * 25.4) + 1, 10):
    x = ruler_x0 + mm / 25.4
    if mm % 50 == 0:
        ax.plot([x, x], [ruler_y, ruler_y - 0.15], 'k-', linewidth=1)
        ax.text(x, ruler_y - 0.2, f'{mm}mm', ha='center', va='top', fontsize=7)
    else:
        ax.plot([x, x], [ruler_y, ruler_y - 0.08], 'k-', linewidth=0.5)

ax.text(PAGE_W/2, 0.3, "PRINT INSTRUCTIONS: 100% scale, no fit-to-page, matte paper. Grayscale steps for relative tonal analysis.",
        ha='center', va='bottom', fontsize=8, style='italic')

ax.set_axis_off()
gw_path = os.path.join(OUT_DIR, "grayscale_step_wedge.pdf")
fig.savefig(gw_path, dpi=DPI, bbox_inches='tight', pad_inches=0.1)
plt.close(fig)
print("Saved: " + gw_path)

# ============================================================
# MANIFEST + HASHES
# ============================================================
manifest = {
    "generated": datetime.now().isoformat(),
    "dpi": DPI,
    "page_size": "A4 (8.27 x 11.69 in)",
    "targets": [
        {
            "name": "Checkerboard",
            "file": "checkerboard_9x6_20mm.pdf",
            "internal_corners": f"{CB_COLS}x{CB_ROWS}",
            "squares": f"{CB_SQUARES_X}x{CB_SQUARES_Y}",
            "nominal_square_mm": SQUARE_MM,
            "nominal_square_in": round(SQUARE_IN, 4),
            "board_width_in": round(CB_WIDTH_IN, 4),
            "board_height_in": round(CB_HEIGHT_IN, 4),
            "purpose": "Camera intrinsics, distortion calibration",
            "note": "Measure actual square dimensions after printing"
        },
        {
            "name": "Slanted-Edge",
            "file": "slanted_edge_iso12233.pdf",
            "slant_angle_deg": 5.0,
            "edge_blocks": 4,
            "block_size_in": 2.0,
            "purpose": "MTF50, sharpness analysis",
            "note": "Print at 100% scale, measure block dimensions"
        },
        {
            "name": "Siemens Star",
            "file": "siemens_star_36spoke.pdf",
            "spokes": 36,
            "diameter_in": star_radius * 2,
            "purpose": "Resolution limit, aliasing detection",
            "note": "Print at 100% scale, measure diameter"
        },
        {
            "name": "Grayscale Step Wedge",
            "file": "grayscale_step_wedge.pdf",
            "steps": num_steps,
            "step_width_in": step_w,
            "purpose": "Relative tonal response, exposure analysis",
            "note": "Print at 100% scale; values are 0-255 sRGB nominal"
        }
    ],
    "print_instructions": {
        "scale": "100% (no fit-to-page, no auto-scale)",
        "paper": "Matte cardstock, 200-300 gsm",
        "color_mode": "sRGB",
        "dpi": DPI,
        "verification": "Measure printed dimensions with calipers after printing"
    },
    "calibration_limitations": [
        "All dimensions are NOMINAL (designed), not measured",
        "Physical print dimensions must be verified with calipers",
        "Color patches are NOT verified ColorChecker references",
        "No absolute color accuracy claim without verified reference values",
        "MTF50 from printed targets includes printer resolution effects"
    ]
}

manifest_path = os.path.join(OUT_DIR, "target_manifest.json")
with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)
print("Saved: " + manifest_path)

print("\n=== SHA-256 Hashes ===")
for fname in ["checkerboard_9x6_20mm.pdf", "slanted_edge_iso12233.pdf", "siemens_star_36spoke.pdf", "grayscale_step_wedge.pdf", "target_manifest.json"]:
    path = os.path.join(OUT_DIR, fname)
    if os.path.exists(path):
        h = hashlib.sha256(open(path, 'rb').read()).hexdigest()
        print(f"  {fname}: {h}")

print_instr = """IMX682 CALIBRATION TARGET PRINT INSTRUCTIONS
============================================

FILES:
  checkerboard_9x6_20mm.pdf      - 9x6 internal corners, 20mm nominal squares
  slanted_edge_iso12233.pdf      - 5 deg slanted edges for MTF50
  siemens_star_36spoke.pdf       - 36-spoke Siemens star
  grayscale_step_wedge.pdf       - 11-step grayscale (0-255)
  target_manifest.json           - Target specifications and hashes

PRINT SETTINGS (CRITICAL):
  - Scale: 100% (DO NOT use "fit to page" or "auto scale")
  - DPI: 300 minimum
  - Paper: Matte cardstock, 200-300 gsm
  - Color mode: sRGB
  - Quality: High/Best

AFTER PRINTING:
  1. Measure checkerboard square dimensions with digital calipers
  2. Record actual square size in mm (±0.01mm precision)
  3. Verify chart geometry (measure multiple squares for consistency)
  4. Document all measurements in capture log
  5. Do NOT assume printer scaling is accurate
  6. Use only measured dimensions for calibration

VERIFICATION CHECKLIST:
  [ ] Checkerboard squares measured and recorded
  [ ] Slanted-edge block dimensions measured
  [ ] Siemens star diameter measured
  [ ] Grayscale step widths measured
  [ ] Chart mounted on flat rigid board
  [ ] Lighting verified even, no glare
  [ ] Camera distance measured and recorded

CALIBRATION LIMITATIONS:
  - All dimensions are NOMINAL (designed), not measured
  - Physical print dimensions MUST be verified with calipers
  - Color patches are NOT verified ColorChecker references
  - No absolute color accuracy claim without verified reference values
  - MTF50 from printed targets includes printer resolution effects
"""
instr_path = os.path.join(OUT_DIR, "PRINT_INSTRUCTIONS.txt")
with open(instr_path, 'w') as f:
    f.write(print_instr)
print("\nSaved: " + instr_path)
print("\nAll print targets generated in: " + OUT_DIR)
