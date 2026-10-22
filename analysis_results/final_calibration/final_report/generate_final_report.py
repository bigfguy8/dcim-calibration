#!/usr/bin/env python3
"""Generate final IMX682 calibration report with all verified data"""
import os, json, hashlib, csv
import numpy as np

BASE = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration"
OUT = os.path.join(BASE, "analysis_results", "final_calibration", "final_report")
PLOTS = os.path.join(OUT, "plots")

# Load data
baseline_results = json.load(open(os.path.join(BASE, "analysis_results", "final_calibration", "no_cost_tests", "ab_comparison", "baseline_qualified_results.json")))
baseline_manifest = json.load(open(os.path.join(BASE, "analysis_results", "final_calibration", "no_cost_tests", "ab_comparison", "baseline_selection_manifest.json")))
no_cost_summary = json.load(open(os.path.join(BASE, "analysis_results", "final_calibration", "no_cost_tests", "no_cost_summary.json")))
dcim_data = json.load(open(os.path.join(BASE, "analysis_results", "dcim_chart_audit", "dcim_full_analysis.json")))
monitor_data = json.load(open(os.path.join(BASE, "analysis_results", "final_calibration", "monitor_calibration", "monitor_all_captures_analysis.json")))

# XML verification
import xml.etree.ElementTree as ET
def get_keys(path):
    tree = ET.parse(path)
    keys = {}
    for el in tree.getroot().findall('string'):
        keys[el.get('name')] = el.text
    return keys

desktop_path = r"C:\Users\l\Desktop\default .xml"
opt_path = os.path.join(BASE, "analysis_results", "imx682_config", "LXX521_LMC84_Optimized_Corrected.xml")
base_path = os.path.join(BASE, "analysis_results", "imx682_config", "original_V2_Release_Day.xml")

desktop_keys = get_keys(desktop_path)
opt_keys = get_keys(opt_path)
base_keys = get_keys(base_path)

desktop_hash = hashlib.sha256(open(desktop_path, 'rb').read()).hexdigest()
opt_hash = hashlib.sha256(open(opt_path, 'rb').read()).hexdigest()
base_hash = hashlib.sha256(open(base_path, 'rb').read()).hexdigest()

# Verify changed keys
changed_keys = []
for k in desktop_keys:
    if desktop_keys[k] != opt_keys.get(k):
        changed_keys.append((k, desktop_keys[k], opt_keys.get(k)))

print("Changed keys:", len(changed_keys))
for k, old, new in changed_keys:
    print(f"  {k}: {old} -> {new}")

# Verify key count and schema
print(f"Desktop keys: {len(desktop_keys)}")
print(f"Optimized keys: {len(opt_keys)}")
print(f"Missing keys: {len(set(desktop_keys) - set(opt_keys))}")
print(f"Extra keys: {len(set(opt_keys) - set(desktop_keys))}")

# Baseline metrics
metrics = ['rg_diff', 'rb_ratio', 'edge_density', 'black_clip_pct', 'white_clip_pct', 'lum_std', 'halo_score']
metric_names = ['R-G (warm cast)', 'R/B ratio', 'Edge density', 'Black clip %', 'White clip %', 'Lum noise (std)', 'Halo score']

print("\nBaseline metrics (18 qualified images):")
for m, name in zip(metrics, metric_names):
    vals = [r[m] for r in baseline_results if r.get(m) is not None]
    print(f"  {name}: median={np.median(vals):.4f}, min={min(vals):.4f}, max={max(vals):.4f}, mean={np.mean(vals):.4f}")

# LMC vs Stock comparison
lmc_data = [r for r in dcim_data if r.get('source') == 'LMC_8.4'] + [r for r in monitor_data if r.get('source') == 'LMC_8.4']
stock_data = [r for r in dcim_data if r.get('source') == 'Stock']

print(f"\nLMC images: {len(lmc_data)}, Stock images: {len(stock_data)}")

# Save verification results
verification = {
    "xml_verification": {
        "desktop_baseline": {
            "path": desktop_path,
            "sha256": desktop_hash,
            "key_count": len(desktop_keys),
        },
        "optimized_corrected": {
            "path": opt_path,
            "sha256": opt_hash,
            "key_count": len(opt_keys),
        },
        "original_v2_release": {
            "path": base_path,
            "sha256": base_hash,
            "key_count": len(base_keys),
        },
        "schema_compatible": len(desktop_keys) == len(opt_keys) == 2640,
        "missing_keys": len(set(desktop_keys) - set(opt_keys)),
        "extra_keys": len(set(opt_keys) - set(desktop_keys)),
        "changed_keys": len(changed_keys),
        "changed_key_details": [{"key": k, "old": old, "new": new} for k, old, new in changed_keys],
    },
    "baseline_dataset": {
        "total_images_pulled": 33,
        "qualified_images": 18,
        "excluded_night_mode": 5,
        "extras": 10,
        "shortfall": 6,
        "target_scenes": 8,
        "complete_scenes": 4,
        "partial_scenes": 3,
        "missing_scenes": 1,
    },
    "baseline_metrics": {},
    "lmc_vs_stock": {
        "lmc_images": len(lmc_data),
        "stock_images": len(stock_data),
        "lmc_warm_cast_rg_mean": float(np.mean([r['rg_diff'] for r in lmc_data])),
        "stock_warm_cast_rg_mean": float(np.mean([r['rg_diff'] for r in stock_data])),
        "lmc_black_clip_mean": float(np.mean([r['black_clip_pct'] for r in lmc_data])),
        "stock_black_clip_mean": float(np.mean([r['black_clip_pct'] for r in stock_data])),
        "lmc_white_clip_mean": float(np.mean([r['white_clip_pct'] for r in lmc_data])),
        "stock_white_clip_mean": float(np.mean([r['white_clip_pct'] for r in stock_data])),
        "lmc_edge_density_mean": float(np.mean([r['edge_density'] for r in lmc_data])),
        "stock_edge_density_mean": float(np.mean([r['edge_density'] for r in stock_data])),
    },
    "monitor_moire": {
        "images": len(monitor_data),
        "moire_range": [float(min(r['moire_score'] for r in monitor_data)), float(max(r['moire_score'] for r in monitor_data))],
        "checkerboard_detected": 0,
        "usable_for_calibration": False,
    },
}

for m, name in zip(metrics, metric_names):
    vals = [r[m] for r in baseline_results if r.get(m) is not None]
    verification['baseline_metrics'][name] = {
        "median": float(np.median(vals)),
        "min": float(min(vals)),
        "max": float(max(vals)),
        "mean": float(np.mean(vals)),
        "n": len(vals),
    }

# Save verification
ver_path = os.path.join(OUT, "verification_results.json")
with open(ver_path, 'w') as f:
    json.dump(verification, f, indent=2, default=str)
print("Saved: verification_results.json")

# Create file manifest
all_files = []
for root, dirs, files in os.walk(os.path.join(BASE, "analysis_results")):
    for f in files:
        path = os.path.join(root, f)
        rel = os.path.relpath(path, BASE)
        all_files.append({"path": rel, "size": os.path.getsize(path), "sha256": hashlib.sha256(open(path, 'rb').read()).hexdigest()})

manifest = {
    "generated": __import__('datetime').datetime.now().isoformat(),
    "total_files": len(all_files),
    "files": all_files,
}
manifest_path = os.path.join(OUT, "file_manifest.json")
with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)
print("Saved: file_manifest.json (" + str(len(all_files)) + " files)")

# Generate final comparison table CSV
csv_path = os.path.join(OUT, "config_comparison_table.csv")
rows = [
    ["Parameter", "Desktop Baseline", "Optimized Corrected", "Changed?", "Evidence"],
    ["cw_rg_key", "0.5925", "0.4500", "YES", "Warm cast R-G +5.7 mean (target <4.0)"],
    ["lib_sharpnessb_key", "0", "2", "YES", "Edge density 0.0296 (target >0.10)"],
    ["lib_sharpgain_key", "0", "2", "YES", "Complement to sharpnessb"],
    ["lib_sharpmini_key", "0", "2", "YES", "Fine detail preservation"],
    ["cw_rg_key_2-5", "0.4200", "0.4200", "NO", "Already reduced in baseline"],
    ["cw_rg_key_front", "0.5925", "0.5925", "NO", "No front camera data"],
    ["lib_denoise_key", "0", "0", "NO", "ISO covered by noise modeler"],
    ["pref_camera_hdr_plus_key", "auto", "auto", "NO", "Confirmed working"],
    ["pref_qjpg_key", "97", "97", "NO", "High quality, no evidence for change"],
    ["pref_awb_key", "0", "0", "NO", "Daylight preset matches outdoor range"],
    ["lib_contrast_1_key", "0", "0", "NO", "No strong evidence"],
    ["lib_saturation2_key", "0", "0", "NO", "No color saturation measurement"],
]
with open(csv_path, 'w', newline='') as f:
    w = csv.writer(f)
    for row in rows:
        w.writerow(row)
print("Saved: config_comparison_table.csv")

print("\n=== FINAL VERIFICATION COMPLETE ===")
print("All outputs in: " + OUT)
