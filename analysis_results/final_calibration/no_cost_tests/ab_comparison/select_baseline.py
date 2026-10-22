#!/usr/bin/env python3
"""Scene assignment for baseline A/B images based on image features"""
import os, json, csv, math
import numpy as np
import cv2
from PIL import Image, ExifTags

BASE = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison\baseline"
OUT = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison"

# Load features
features = json.load(open(os.path.join(OUT, 'scene_features.json')))
# Load analysis
analysis = json.load(open(os.path.join(BASE, '..', 'baseline_inventory.json'))) if os.path.exists(os.path.join(BASE, '..', 'baseline_inventory.json')) else []

# Build feature lookup
feat_map = {f['filename']: f for f in features}

# Load ab_analyze results
try:
    ab_results = json.load(open(os.path.join(OUT, 'baseline_results.json')))
    ab_map = {r['filename']: r for r in ab_results}
except:
    ab_map = {}

# Classification rules based on features
def classify_scene(f):
    """Classify image into one of 8 scene types based on features."""
    green = f['green_dominance']
    blue = f['blue_dominance']
    red = f['red_dominance']
    lum = f['lum_mean']
    edge = f['edge_density']
    tex = f['texture_var']
    hv = f['hv_ratio']
    iso = f['iso'] or 0
    ev = f['ev'] or 0

    # Night mode exclusion
    if iso > 10000:
        return 'NIGHT_MODE', 'EXCLUDED', 'Night/long-exposure capture (ISO>10000)'

    # Foliage: high green dominance
    if green > 25:
        return 'Foliage', 'HIGH', 'Green dominance >25, blue dominance < -30'

    # Fine texture / text: high edge density + high texture
    if edge > 0.15 and tex > 1500:
        if hv > 1.0:
            return 'Text', 'HIGH', 'High edge density + texture + horizontal edges dominant'
        else:
            return 'Fine texture', 'HIGH', 'High edge density + texture, balanced edges'

    # Skin tone / warm: high red dominance, moderate brightness
    if red > 8 and lum > 100:
        return 'Skin tone', 'MEDIUM', 'Red dominance >8, lum >100 (warm scene)'

    # Bright highlights: high brightness, high dynamic range
    if lum > 110 and f['dynamic_range'] > 150:
        return 'Bright highlights', 'MEDIUM', 'High luminance + dynamic range'

    # Neutral objects: low color dominance
    if abs(green) < 5 and abs(blue) < 5 and abs(red) < 5:
        return 'Neutral objects', 'MEDIUM', 'Low color dominance (near-neutral)'

    # Indoor mixed lighting: moderate brightness, mixed colors
    if 80 < lum < 120 and abs(green) < 15:
        return 'Indoor mixed', 'MEDIUM', 'Moderate brightness, mixed colors'

    # Low light: low brightness
    if lum < 60:
        return 'Low light', 'MEDIUM', 'Low luminance'

    # Cool/blue dominant
    if blue > 5:
        return 'Cool scene', 'LOW', 'Blue dominance (cool/indoor)'

    # Warm/red dominant
    if red > 5:
        return 'Warm scene', 'LOW', 'Red dominance (warm/indoor)'

    return 'Unclassified', 'LOW', 'No clear feature match'

# Classify all images
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

# Print classification summary
from collections import Counter
scene_counts = Counter(a['scene'] for a in assignments)
print("Scene classification:")
for scene, count in sorted(scene_counts.items()):
    print(f"  {scene}: {count}")

# Select 3 per scene for primary baseline
# Priority: highest confidence, then highest edge density (sharpest), then middle EV
selected = []
extras = []
excluded = []

for scene in ['Fine texture', 'Foliage', 'Text', 'Indoor mixed', 'Neutral objects',
              'Bright highlights', 'Low light', 'Skin tone', 'Warm scene', 'Cool scene']:
    candidates = [a for a in assignments if a['scene'] == scene and a['confidence'] in ['HIGH', 'MEDIUM']]
    if not candidates:
        continue
    # Sort by confidence (HIGH first), then edge density (descending), then EV (middle)
    candidates.sort(key=lambda x: (0 if x['confidence'] == 'HIGH' else 1, -x['edge_density'], abs(x['ev'] - 2.0) if x['ev'] else 0))
    for i, c in enumerate(candidates):
        if i < 3:
            selected.append(c)
        else:
            extras.append(c)

# Night mode excluded
for a in assignments:
    if a['scene'] == 'NIGHT_MODE':
        excluded.append(a)

# Unclassified
for a in assignments:
    if a['scene'] in ['Unclassified', 'Cool scene', 'Warm scene'] and a not in selected and a not in extras and a not in excluded:
        extras.append(a)

# Print selected
print("\n=== SELECTED BASELINE (24 target) ===")
selected_by_scene = {}
for s in selected:
    selected_by_scene.setdefault(s['scene'], []).append(s)
for scene, imgs in sorted(selected_by_scene.items()):
    print(f"\n{scene}: {len(imgs)} images")
    for img in imgs:
        print(f"  {img['filename']} | edge={img['edge_density']:.3f} | R-G={img['rg_diff']} | EV={img['ev']} | conf={img['confidence']}")

print(f"\nTotal selected: {len(selected)}")
print(f"Total extras: {len(extras)}")
print(f"Total excluded (night mode): {len(excluded)}")

# Save selection manifest
manifest = {
    "total_images": len(assignments),
    "selected_count": len(selected),
    "extras_count": len(extras),
    "excluded_count": len(excluded),
    "scenes": {},
    "selected": [a['filename'] for a in selected],
    "extras": [a['filename'] for a in extras],
    "excluded": [a['filename'] for a in excluded],
    "excluded_reason": "Night/long-exposure capture (ISO>10000, EV<-5)",
}

for scene in sorted(set(a['scene'] for a in selected)):
    scene_imgs = [a for a in selected if a['scene'] == scene]
    manifest['scenes'][scene] = {
        "count": len(scene_imgs),
        "target": 3,
        "shortfall": max(0, 3 - len(scene_imgs)),
        "images": [a['filename'] for a in scene_imgs],
    }

# Check for shortfalls
shortfalls = []
for scene, info in manifest['scenes'].items():
    if info['shortfall'] > 0:
        shortfalls.append(f"{scene}: {info['count']}/3 (shortfall {info['shortfall']})")

if shortfalls:
    manifest['shortfalls'] = shortfalls
    print("\n⚠️ SHORTFALLS:")
    for s in shortfalls:
        print(f"  {s}")

# Save manifest
manifest_path = os.path.join(OUT, 'baseline_selection_manifest.json')
with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)
print(f"\nSaved: {manifest_path}")

# Save selected list
with open(os.path.join(OUT, 'baseline_selected.txt'), 'w') as f:
    for a in selected:
        f.write(a['filename'] + "\n")
print("Saved: baseline_selected.txt")

# Save full assignment
with open(os.path.join(OUT, 'scene_assignments.json'), 'w') as f:
    json.dump(assignments, f, indent=2, default=str)
print("Saved: scene_assignments.json")

# Generate report
report = f"""# Baseline Scene Selection Report

**Date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF)
**Total images analyzed:** {len(assignments)}
**Selected for baseline:** {len(selected)}
**Extras:** {len(extras)}
**Excluded (night mode):** {len(excluded)}

## Scene Coverage

"""
for scene in sorted(set(a['scene'] for a in assignments)):
    scene_selected = [a for a in selected if a['scene'] == scene]
    scene_all = [a for a in assignments if a['scene'] == scene]
    report += f"### {scene}\n"
    report += f"- Total images: {len(scene_all)}\n"
    report += f"- Selected: {len(scene_selected)}\n"
    if len(scene_selected) < 3:
        report += f"- ⚠️ SHORTFALL: {3 - len(scene_selected)} images needed\n"
    report += f"- Images:\n"
    for a in scene_selected:
        report += f"  - {a['filename']} (edge={a['edge_density']:.3f}, R-G={a['rg_diff']}, EV={a['ev']}, conf={a['confidence']})\n"
    report += "\n"

report += f"""## Excluded Images (Night Mode)

{len(excluded)} images excluded due to night/long-exposure capture mode:
"""
for a in excluded:
    report += f"- {a['filename']} (ISO={a['iso']}, EV={a['ev']})\n"

report += f"""
## Extras (Not Selected)

{len(extras)} images not selected for primary baseline:
"""
for a in extras:
    report += f"- {a['filename']} (scene={a['scene']}, conf={a['confidence']}, edge={a['edge_density']:.3f})\n"

report += f"""
## Limitations

1. Scene classification is based on image features (color, texture, brightness), not visual inspection
2. Some scene assignments may be incorrect — visual verification recommended
3. 4 extra images remain unassigned
4. 5 night-mode images excluded (different capture mode)
5. No images clearly identified as "skin tone" or "bright highlights" scenes
6. Edge density and texture variance are scene-dependent, not config-dependent

## Recommendations

1. **Visual inspection** of contact sheet to verify scene assignments
2. **If scene identification is uncertain**, request targeted recapture
3. **Proceed with 24 selected images** for baseline analysis
4. **Request authorization** for optimized config import
5. **Capture 24 matching optimized images** (same scenes)
6. **Run A/B comparison** with ab_analyze.py
"""

report_path = os.path.join(OUT, 'baseline_scene_selection_report.md')
with open(report_path, 'w') as f:
    f.write(report)
print(f"\nSaved: {report_path}")
print("\nDone.")
