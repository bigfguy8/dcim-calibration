#!/usr/bin/env python3
"""Fix LMC vs Stock classification and regenerate verification"""
import os, json, hashlib
import numpy as np

BASE = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration"
OUT = os.path.join(BASE, "analysis_results", "final_calibration", "final_report")

dcim_data = json.load(open(os.path.join(BASE, "analysis_results", "dcim_chart_audit", "dcim_full_analysis.json")))
monitor_data = json.load(open(os.path.join(BASE, "analysis_results", "final_calibration", "monitor_calibration", "monitor_all_captures_analysis.json")))

def classify_source(r):
    sw = str(r.get('software', '')).lower()
    if 'hdr+' in sw:
        return 'LMC_8.4'
    elif 'mediatek' in sw:
        return 'Stock'
    else:
        return 'Unknown'

for r in dcim_data:
    r['source'] = classify_source(r)
for r in monitor_data:
    r['source'] = classify_source(r)

lmc_data = [r for r in dcim_data if r['source'] == 'LMC_8.4'] + [r for r in monitor_data if r['source'] == 'LMC_8.4']
stock_data = [r for r in dcim_data if r['source'] == 'Stock']

print(f"LMC images: {len(lmc_data)}")
print(f"Stock images: {len(stock_data)}")

# Update verification results
ver = json.load(open(os.path.join(OUT, "verification_results.json")))
ver['lmc_vs_stock'] = {
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
    "lmc_rb_ratio_mean": float(np.mean([r['rb_ratio'] for r in lmc_data])),
    "stock_rb_ratio_mean": float(np.mean([r['rb_ratio'] for r in stock_data])),
    "lmc_mtf50_mean": float(np.mean([r['mtf50_cyc_px'] for r in lmc_data])),
    "stock_mtf50_mean": float(np.mean([r['mtf50_cyc_px'] for r in stock_data])),
}

with open(os.path.join(OUT, "verification_results.json"), 'w') as f:
    json.dump(ver, f, indent=2, default=str)
print("Updated verification_results.json")

# Print summary
print("\nLMC vs Stock Summary:")
for k, v in ver['lmc_vs_stock'].items():
    print(f"  {k}: {v}")
