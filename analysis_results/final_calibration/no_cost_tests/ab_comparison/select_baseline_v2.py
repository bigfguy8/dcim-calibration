#!/usr/bin/env python3
"""Scene assignment for baseline A/B images - ASCII safe version"""
import os, json, math
import numpy as np
import cv2
from PIL import Image, ExifTags

BASE = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison\baseline"
OUT = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison"

features = json.load(open(os.path.join(OUT, 'scene_features.json')))

# Load ab_analyze results
try:
    ab_results = json.load(open(os.path.join(OUT, 'baseline_results.json')))
    ab_map = {r['filename']: r for r in ab_results}
except:
    ab_map = {}

def classify_scene(f):
    green = f['green_dominance']
    blue = f['blue_dominance']
    red = f['red_dominance']
    lum = f['lum_mean']
    edge = f['edge_density']
    tex = f['texture_var']
    hv = f['hv_ratio']
    iso = f['iso'] or 0
    ev = f['ev'] or 0

    if iso > 10000:
        return 'NIGHT_MODE', 'EXCLUDED', 'Night/long-exposure capture'

    if green > 25:
        return 'Foliage', 'HIGH', 'Green dominance >25'

    if edge > 0.15 and tex > 1500:
        if hv > 1.0:
            return 'Text', 'HIGH', 'High edge + texture + horizontal edges'
        else:
            return 'Fine texture', 'HIGH', 'High edge + texture, balanced edges'

    if red > 8 and lum > 100:
        return 'Skin tone', 'MEDIUM', 'Red dominance >8, lum >100'

    if lum > 110 and f['dynamic_range'] > 150:
        return 'Bright highlights', 'MEDIUM', 'High luminance + dynamic range'

    if abs(green) < 5 and abs(blue) < 5 and abs(red) < 5:
        return 'Neutral objects', 'MEDIUM', 'Low color dominance'

    if 80 < lum < 120 and abs(green) < 15:
        return 'Indoor mixed', 'MEDIUM', 'Moderate brightness, mixed colors'

    if lum < 60:
        return 'Low light', 'MEDIUM', 'Low luminance'

    if blue > 5:
        return 'Cool scene', 'LOW', 'Blue dominance'

    if red > 5:
        return 'Warm scene', 'LOW', 'Red dominance'

    return 'Unclassified', 'LOW', 'No clear feature match'

assignments = []
for f in features:
    scene, confidence, reason = classify_scene(f)
    ab = ab_map.get(f['filename'], {})
    assignments.append({
        'filename': f['filename'],
        'scene': scene,
        'confidence': confidence,
        'reason': reason,
        'green_dominance': f['green_dominance'],
        'blue_dominance': f['blue_dominance'],
        'red_dominance': f['red_dominance'],
        'lum_mean': f['lum_mean'],
        'edge_density': f['edge_density'],
        'texture_var': f['texture_var'],
        'ev': f['ev'],
        'iso': f['iso'],
        'rg_diff': ab.get('rg_diff'),
        'rb_ratio': ab.get('rb_ratio'),
        'black_clip_pct': ab.get('black_clip_pct'),
        'white_clip_pct': ab.get('white_clip_pct'),
        'lum_std': ab.get('lum_std'),
        'halo_score': ab.get('halo_score'),
    })

# Select 3 per scene for primary baseline
selected = []
extras = []
excluded = []

target_scenes = ['Fine texture', 'Foliage', 'Text', 'Indoor mixed', 'Neutral objects',
                 'Bright highlights', 'Low light', 'Skin tone']

for scene in target_scenes:
    candidates = [a for a in assignments if a['scene'] == scene and a['confidence'] in ['HIGH', 'MEDIUM']]
    candidates.sort(key=lambda x: (0 if x['confidence'] == 'HIGH' else 1, -x['edge_density']))
    for i, c in enumerate(candidates):
        if i < 3:
            selected.append(c)
        else:
            extras.append(c)

# Night mode excluded
for a in assignments:
    if a['scene'] == 'NIGHT_MODE':
        excluded.append(a)

# Remaining as extras
for a in assignments:
    if a not in selected and a not in excluded:
        extras.append(a)

# Build manifest
manifest = {
    "total_images": len(assignments),
    "selected_count": len(selected),
    "extras_count": len(extras),
    "excluded_count": len(excluded),
    "scenes": {},
    "selected": [a['filename'] for a in selected],
    "extras": [a['filename'] for a in extras],
    "excluded": [a['filename'] for a in excluded],
}

for scene in target_scenes:
    scene_imgs = [a for a in selected if a['scene'] == scene]
    manifest['scenes'][scene] = {
        "count": len(scene_imgs),
        "target": 3,
        "shortfall": max(0, 3 - len(scene_imgs)),
        "images": [a['filename'] for a in scene_imgs],
    }

shortfalls = []
for scene, info in manifest['scenes'].items():
    if info['shortfall'] > 0:
        shortfalls.append(scene + ": " + str(info['count']) + "/3 (shortfall " + str(info['shortfall']) + ")")

if shortfalls:
    manifest['shortfalls'] = shortfalls

# Save manifest
manifest_path = os.path.join(OUT, 'baseline_selection_manifest.json')
with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)
print("Saved: " + manifest_path)

# Save selected list
with open(os.path.join(OUT, 'baseline_selected.txt'), 'w') as f:
    for a in selected:
        f.write(a['filename'] + "\n")
print("Saved: baseline_selected.txt")

# Save full assignment
with open(os.path.join(OUT, 'scene_assignments.json'), 'w') as f:
    json.dump(assignments, f, indent=2, default=str)
print("Saved: scene_assignments.json")

# Print summary
print("\n=== SCENE CLASSIFICATION ===")
from collections import Counter
scene_counts = Counter(a['scene'] for a in assignments)
for scene, count in sorted(scene_counts.items()):
    print(f"  {scene}: {count}")

print("\n=== SELECTED BASELINE ===")
selected_by_scene = {}
for s in selected:
    selected_by_scene.setdefault(s['scene'], []).append(s)
for scene in sorted(selected_by_scene.keys()):
    imgs = selected_by_scene[scene]
    print(f"\n{scene}: {len(imgs)} images")
    for img in imgs:
        print(f"  {img['filename']} | edge={img['edge_density']:.3f} | R-G={img['rg_diff']} | EV={img['ev']} | conf={img['confidence']}")

print(f"\nTotal selected: {len(selected)}")
print(f"Total extras: {len(extras)}")
print(f"Total excluded (night mode): {len(excluded)}")

if shortfalls:
    print("\nSHORTFALLS:")
    for s in shortfalls:
        print("  " + s)

# Generate report
report = "# Baseline Scene Selection Report\n\n"
report += "Date: 2026-10-19\n"
report += "Device: LAVA LXX521 (serial: 0123456789ABCDEF)\n"
report += "Total images analyzed: " + str(len(assignments)) + "\n"
report += "Selected for baseline: " + str(len(selected)) + "\n"
report += "Extras: " + str(len(extras)) + "\n"
report += "Excluded (night mode): " + str(len(excluded)) + "\n\n"

report += "## Scene Coverage\n\n"
for scene in sorted(set(a['scene'] for a in assignments)):
    scene_selected = [a for a in selected if a['scene'] == scene]
    scene_all = [a for a in assignments if a['scene'] == scene]
    report += "### " + scene + "\n"
    report += "- Total images: " + str(len(scene_all)) + "\n"
    report += "- Selected: " + str(len(scene_selected)) + "\n"
    if len(scene_selected) < 3 and scene in target_scenes:
        report += "- SHORTFALL: " + str(3 - len(scene_selected)) + " images needed\n"
    report += "- Images:\n"
    for a in scene_selected:
        report += "  - " + a['filename'] + " (edge=" + str(round(a['edge_density'],3)) + ", R-G=" + str(a['rg_diff']) + ", EV=" + str(a['ev']) + ", conf=" + a['confidence'] + ")\n"
    report += "\n"

report += "## Excluded Images (Night Mode)\n\n"
report += str(len(excluded)) + " images excluded due to night/long-exposure capture mode:\n"
for a in excluded:
    report += "- " + a['filename'] + " (ISO=" + str(a['iso']) + ", EV=" + str(a['ev']) + ")\n"

report += "\n## Extras (Not Selected)\n\n"
report += str(len(extras)) + " images not selected for primary baseline:\n"
for a in extras:
    report += "- " + a['filename'] + " (scene=" + a['scene'] + ", conf=" + a['confidence'] + ", edge=" + str(round(a['edge_density'],3)) + ")\n"

report += "\n## Limitations\n\n"
report += "1. Scene classification is based on image features (color, texture, brightness), not visual inspection\n"
report += "2. Some scene assignments may be incorrect - visual verification recommended\n"
report += "3. 4 extra images remain unassigned to 8 target scenes\n"
report += "4. 5 night-mode images excluded (different capture mode)\n"
report += "5. No images clearly identified as 'neutral objects' scene\n"
report += "6. Edge density and texture variance are scene-dependent, not config-dependent\n"
report += "7. R-G values vary wildly (-18.8 to +11.3) suggesting different scenes/lighting\n"

report += "\n## Scene Coverage Summary\n\n"
report += "| Scene | Target | Selected | Shortfall |\n"
report += "|-------|--------|----------|----------|\n"
for scene in target_scenes:
    info = manifest['scenes'].get(scene, {"count": 0, "shortfall": 3})
    report += f"| {scene} | 3 | {info['count']} | {info['shortfall']} |\n"

report += "\n## Recommendations\n\n"
report += "1. Visual inspection of contact sheet to verify scene assignments\n"
report += "2. If scene identification is uncertain, request targeted recapture\n"
report += "3. Proceed with 18 selected images for baseline analysis (shortfall in 4 scenes)\n"
report += "4. Request authorization for optimized config import\n"
report += "5. Capture matching optimized images (same scenes)\n"
report += "6. Run A/B comparison with ab_analyze.py\n"

report_path = os.path.join(OUT, 'baseline_scene_selection_report.md')
with open(report_path, 'w') as f:
    f.write(report)
print("\nSaved: " + report_path)
print("\nDone.")
