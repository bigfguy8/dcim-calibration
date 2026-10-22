# IMX682 LMC 8.4 — Final Calibration & Optimization Report

**Date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15, SDK 35
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Sensor:** Sony IMX682, rear 5.43mm f/1.89, front 3.59mm, UW 1.98mm
**Active Config:** `default .xml` (baseline) — NOT changed throughout
**Staged Config:** `LXX521_LMC84_Optimized_Corrected.xml` — NOT imported

---

## 1. Executive Summary

This report consolidates all calibration, analysis, and optimization work performed on the LAVA LXX521's Sony IMX682 camera using LMC 8.4 Iris R18F1. The project spanned image analysis (71+ images), configuration development (4 XML variants), device testing (ADB), monitor-based calibration (32 captures), and no-cost optimization analysis.

### Key Conclusions

1. **LMC 8.4 significantly outperforms stock camera** on clipping (black clip 10.64% vs 18.34%, white clip 5.36% vs 15.82%) and warm cast (R-G +5.7 vs +6.0 mean).
2. **Warm cast is sensor-level** (MT6878 ISP) — not fully correctable via XML keys alone. cw_rg_key reduction from 0.5925 to 0.4500 may help but cannot reach R-G <4.0 target.
3. **Monitor-based calibration is impractical** — severe moiré (580-3132) from 1920×1080 monitor vs 4624×3472 sensor makes all measurements unreliable.
4. **No physical calibration charts available** — cannot compute camera intrinsics, distortion coefficients, or CIEDE2000 color accuracy.
5. **Optimized config is staged but untested** — 4 key changes (cw_rg_key 0.5925→0.4500, sharpness 0→2) are evidence-based but not validated on device.
6. **Recommendation:** Retain baseline as primary config. Test optimized config via A/B capture when authorized. If optimized shows no improvement, rollback to baseline.

---

## 2. Dataset Summary

| Dataset | Images | Source | Key Findings |
|---------|--------|--------|--------------|
| DCIM (device) | 39 | Stock + LMC 8.4 | Natural scenes + 1 checkerboard (unusable) |
| Monitor captures | 32 | LMC 8.4 | Monitor charts (severe moiré) |
| Recapture v12 | 37 | LMC 8.4 + Stock | Mixed natural + checkerboard (monitor) |
| A/B baseline | 33 (18 qualified) | LMC 8.4 | Natural scenes, 5 night-mode excluded |
| **Total** | **109+** | | |

## 3. LMC 8.4 vs Stock Camera

| Metric | LMC 8.4 (50 imgs) | Stock (19 imgs) | Winner |
|--------|-------------------|-----------------|--------|
| Warm cast (R-G mean) | +5.68 | +6.05 | LMC (slightly) |
| R/B ratio (mean) | 1.041 | 1.047 | LMC (closer to 1.0) |
| Black clip % (mean) | 10.64% | 18.34% | **LMC** (significantly) |
| White clip % (mean) | 5.36% | 15.82% | **LMC** (significantly) |
| Edge density (mean) | 0.0296 | 0.0516 | Stock (scene-dependent) |
| MTF50 (mean) | 0.0012 | 0.0011 | Tie (floor-level) |
| EV range | -0.16 to 3.71 | -2.29 to 7.74 | Stock (wider) |
| ISO range | 288-1860 | 101-4909 | Stock (wider) |

**Conclusion:** LMC 8.4 with HDR+ is clearly superior on exposure control (clipping). Stock camera has wider dynamic range but worse clipping. Warm cast is similar (sensor-level).

## 4. XML Configuration Verification

### 4.1 Working Baseline (Desktop `default .xml`)

| Property | Value |
|----------|-------|
| SHA-256 | `f5dde315f71bb4c28f72ea0b2a5cd3b5385f2e4aeb12b7463416174acb1b5f49` |
| Key count | 2640 |
| File size | 141,566 bytes |
| Schema | `<map>` with `<string name="..." value="..."/>` |
| Source | Genuine device baseline from `/sdcard/LMC8.4/default .xml` |

### 4.2 Optimized Config (`LXX521_LMC84_Optimized_Corrected.xml`)

| Property | Value |
|----------|-------|
| SHA-256 | `a5d98309bdacad6a1f640fb016d4423036a2b85682545c5002f9b8677d4785cd` |
| Key count | 2640 (identical) |
| File size | 143,961 bytes |
| Schema | `<map>` with `<string name="..." value="..."/>` (compatible) |
| Missing keys | 0 |
| Extra keys | 0 |
| Changed keys | 4 |

### 4.3 Changed Keys (Verified)

| Key | Baseline | Optimized | Evidence | Rationale |
|-----|----------|-----------|----------|-----------|
| cw_rg_key | 0.5925 | 0.4500 | Warm cast R-G +5.68 mean (target <4.0) | Reduce red gain on rear camera |
| lib_sharpnessb_key | 0 | 2 | Edge density 0.0296 (target >0.10) | Moderate sharpening increase |
| lib_sharpgain_key | 0 | 2 | Same as above | Sharpening gain complement |
| lib_sharpmini_key | 0 | 2 | Fine detail preservation | Micro-sharpening |

### 4.4 Why Original Optimized.xml Failed

The first `LXX521_LMC84_Optimized.xml` was based on `original_V2_Release_Day.xml` (SHA-256 `d592bed3...`) which differed from the device's working `default .xml` (SHA-256 `f5dde315...`) in **29 keys**. This caused unintended changes including:
- `pref_qjpg_key: 97→100`
- `pref_color_key: 0→-4`
- `pref_camera_hdr_plus_key: auto→enhanced`
- `lib_denoise_key: 0→1`
- `pref_awb_key: 0→1`

The corrected config (`LXX521_LMC84_Optimized_Corrected.xml`) uses the Desktop `default .xml` as the true working baseline and modifies only the 4 verified tuning keys.

### 4.5 Other Variants

| Variant | File | SHA-256 | Key Differences |
|---------|------|---------|-----------------|
| Balanced | `balanced.xml` | `d592bed3...` | Identical to V2 Release baseline |
| Detail | `detail.xml` | `a17bb889...` | Sharpening +3, NR 0 |
| Low-light | `lowlight.xml` | `e285e9e0...` | NR +2, sharpening 0 |

## 5. Baseline Capture Analysis

### 5.1 Capture Summary
- **Images captured:** 33 (24 expected + 9 extra)
- **Qualified for baseline:** 18 (selected by feature-based scene classification)
- **Excluded:** 5 (night-mode captures, ISO 15K-25K)
- **Extras:** 10 (not assigned to target scenes)

### 5.2 Baseline Metrics (18 qualified images, median)

| Metric | Median | Min | Max | Mean |
|--------|--------|-----|-----|------|
| R-G (warm cast) | -5.50 | -17.87 | +10.89 | -3.92 |
| R/B ratio | 1.078 | 0.780 | 1.407 | 1.085 |
| Edge density | 0.100 | 0.021 | 0.221 | 0.112 |
| Black clip % | 0.65 | 0.10 | 12.33 | 3.01 |
| White clip % | 0.10 | 0.00 | 6.83 | 0.53 |
| Lum noise (std) | 55.59 | 38.37 | 89.32 | 60.04 |
| Halo score | 415.1 | 264.2 | 743.4 | 461.2 |

### 5.3 Scene Coverage

| Scene | Target | Selected | Status |
|-------|--------|----------|--------|
| Foliage | 3 | 3 | ✅ Complete |
| Text | 3 | 3 | ✅ Complete |
| Indoor mixed | 3 | 3 | ✅ Complete |
| Skin tone | 3 | 3 | ✅ Complete |
| Fine texture | 3 | 2 | ⚠️ Shortfall 1 |
| Bright highlights | 3 | 2 | ⚠️ Shortfall 1 |
| Low light | 3 | 2 | ⚠️ Shortfall 1 |
| Neutral objects | 3 | 0 | ❌ Missing 3 |
| **Total** | **24** | **18** | **6 shortfall** |

### 5.4 Night-Mode Captures (Excluded)

5 images with impossible ISO (15,094-25,500), very negative EV (-5.2 to -6.0), 0.25s exposure, and `ndy` software suffix. These are genuine night/long-exposure captures with composite ISO from HDR+ pipeline. Excluded from primary A/B comparison.

## 6. Monitor-Based Calibration

### 6.1 Monitor Specs
- **Model:** Acer (ACR0FDD), 1920×1080 @ 120Hz, ~93 DPI, 53×29cm

### 6.2 Results (32 captures)
- **Checkerboard detected:** 0 of 32
- **Moiré score:** 580.7 to 3131.8 (severe on all)
- **MTF50:** 0.001 cyc/px (floor-level)
- **Edge density:** 0.006-0.028 (far below 10% target)

**Conclusion:** Monitor-based calibration is impractical. Severe moiré from monitor pixel structure makes all measurements unreliable. Physical printed charts are required.

## 7. Unsupported Measurements

| Measurement | Status | Reason |
|-------------|--------|--------|
| Absolute color accuracy (CIEDE2000) | Not available | No ColorChecker reference values |
| True MTF50 | Not available | Monitor pixel structure dominates; no physical charts |
| Camera intrinsics (mm) | Not available | No physical checkerboard with known dimensions |
| Distortion coefficients (mm) | Not available | No physical checkerboard |
| Sensor-level warm cast correction | Limited | cw_rg_key helps but cannot fully correct sensor characteristic |
| Front camera AWB | No data | No front-camera captures |
| Optical sharpness improvement | Not measurable | MTF50 floor-level on all captures |

## 8. A/B Test Status

**Status: NOT PERFORMED**

- Baseline captures: 18 qualified images analyzed
- Optimized captures: 0 (authorization required)
- `ab_analyze.py` ready for comparison when both sets available

**To complete A/B test:**
1. Authorize import of `LXX521_LMC84_Optimized_Corrected.xml`
2. Capture 18+ matching optimized images (same scenes)
3. Run `ab_analyze.py`
4. Generate final recommendation

## 9. Final Recommendation

### Primary Recommendation: Retain Baseline, Test Optimized

**Rationale:**
1. The optimized config (`LXX521_LMC84_Optimized_Corrected.xml`) is evidence-based but **untested on device**
2. The 4 changes (cw_rg_key 0.5925→0.4500, sharpness 0→2) are conservative and justified by data
3. However, **no A/B comparison has been performed** — cannot claim improvement
4. Warm cast is **sensor-level** — XML tuning may not reach R-G <4.0 target
5. Edge density is **scene-dependent** — sharpening helps but cannot create detail

### If A/B Test Shows Improvement
- **Recommend:** Switch to `LXX521_LMC84_Optimized_Corrected.xml`
- **Monitor:** Warm cast, clipping, noise, halos on real-world captures
- **Rollback if:** Any metric degrades significantly

### If A/B Test Shows No Improvement or Degradation
- **Recommend:** Retain baseline (`default .xml`)
- **Consider:** Selective changes (cw_rg_key only, or sharpness only)
- **Investigate:** BSG GCam with AWB correction module (requires user authorization)

### Rollback Procedure
1. Delete `LXX521_LMC84_Optimized_Corrected.xml` from device
2. Or re-import baseline: `adb push "default .xml" /sdcard/LMC8.4/`
3. Restart LMC app
4. Verify: check EXIF Software field for `HDR+ 1.0.414775603zdy`

### Deployment Steps (When Authorized)
1. Connect device via ADB
2. Push config: `adb push LXX521_LMC84_Optimized_Corrected.xml /sdcard/LMC8.4/`
3. Open LMC app → Settings → Load config
4. Select `LXX521_LMC84_Optimized_Corrected.xml`
5. Capture test photos in consistent lighting
6. Pull photos and run `ab_analyze.py` to compare metrics

## 10. Files Generated (Complete Inventory)

### Config Files
| File | SHA-256 | Purpose |
|------|---------|---------|
| `original_V2_Release_Day.xml` | `d592bed3...` | Backup of V2 Release baseline |
| `balanced.xml` | `d592bed3...` | V2 Release baseline copy |
| `detail.xml` | `a17bb889...` | Detail variant (sharpness +3, NR 0) |
| `lowlight.xml` | `e285e9e0...` | Low light variant (NR +2, sharpness 0) |
| `LXX521_LMC84_Optimized_Corrected.xml` | `a5d98309...` | **New optimized config** (4 changes) |

### Reports
| File | Purpose |
|------|---------|
| `IMX682_full_calibration_report.md` | Complete calibration summary |
| `config_change_log.md` | All changes from baseline |
| `config_validation_report.md` | Syntax, schema, range validation |
| `measurement_to_setting_table.md` | Measurement-to-setting mapping |
| `baseline_reconciliation_report.md` | Baseline capture reconciliation |
| `baseline_scene_selection_report.md` | Scene selection details |
| `monitor_calibration_report.md` | Monitor calibration analysis |
| `no_cost_optimization_report.md` | No-cost optimization analysis |
| `ab_report.md` | A/B comparison report |
| `DCIM_CHART_AUDIT_REPORT.md` | DCIM photo audit |
| `IMX682_full_audit_report.md` | Full folder audit |

### Data Files
| File | Purpose |
|------|---------|
| `baseline_qualified_results.json` | Full metrics for 18 qualified images |
| `baseline_qualified_results.csv` | Full metrics (CSV) |
| `baseline_selection_manifest.json` | Scene selection manifest |
| `scene_assignments.json` | Feature-based classification |
| `verification_results.json` | XML verification results |
| `file_manifest.json` | Complete file inventory (254 files) |
| `config_comparison_table.csv` | Config comparison table |
| `no_cost_summary.json` | No-cost analysis summary |
| `no_cost_all_data.csv` | All 71 images with metrics |

### Scripts
| File | Purpose |
|------|---------|
| `generate_optimized.py` | Generate optimized config |
| `generate_corrected.py` | Generate corrected config (from Desktop baseline) |
| `apply_variants.py` | Apply variant modifications |
| `verify_configs.py` | Verify all config XMLs |
| `verify_changes.py` | Verify 4 intended changes |
| `verify_corrected.py` | Verify corrected config |
| `analyze_dcim.py` | DCIM image analysis |
| `analyze_opencv.py` | OpenCV analysis (downscaled) |
| `analyze_monitor_baseline.py` | Monitor capture analysis |
| `analyze_all_monitor.py` | All monitor captures analysis |
| `analyze_no_cost.py` | No-cost optimization analysis |
| `ab_analyze.py` | A/B comparison analysis |
| `reconcile_baseline.py` | Baseline reconciliation |
| `select_baseline_v2.py` | Baseline scene selection |
| `classify_scenes.py` | Scene feature extraction |
| `make_contact_sheet.py` | Contact sheet generation |
| `pull_baseline.py` | Pull baseline images from device |
| `fix_lmc_stock.py` | Fix LMC/Stock classification |
| `generate_final_report.py` | Final report generation |

### Plots
| File | Purpose |
|------|---------|
| `warm_cast_distribution.png` | Warm cast histogram |
| `black_clip_vs_ev.png` | Black clipping vs EV |
| `moire_distribution.png` | Moiré severity |
| `iso_vs_blackclip.png` | ISO vs black clip |
| `edge_density_distribution.png` | Edge density histogram |
| `monitor_mtf50.png` | Monitor MTF50 comparison |
| `monitor_wb.png` | Monitor white balance |
| `monitor_clipping.png` | Monitor clipping |
| `monitor_all_mtf50.png` | All monitor MTF50 |
| `monitor_all_wb.png` | All monitor WB |
| `monitor_all_clipping.png` | All monitor clipping |
| `monitor_all_moire.png` | All monitor moiré |
| `ab_comparison.png` | A/B comparison |
| `baseline_qualified_contact.png` | Baseline contact sheet |
| `baseline_contact_sheet.png` | Full baseline contact sheet |

### Contact Sheets
| File | Purpose |
|------|---------|
| `baseline_contact_sheet.png` | Visual contact sheet (33 images) |
| `baseline_inventory_text.png` | Text inventory |
| `baseline_qualified_contact.png` | Qualified images contact sheet |

## 11. Limitations & Uncertainties

1. **No physical calibration charts** — cannot compute intrinsics, distortion, or absolute MTF
2. **No ColorChecker references** — cannot compute CIEDE2000 color accuracy
3. **Monitor captures are unusable** — severe moiré confounds all measurements
4. **A/B test not performed** — optimized config untested on device
5. **Scene classification is feature-based** — may not match actual scene content
6. **Baseline incomplete** — 18 of 24 target images (6 shortfall)
7. **Warm cast is sensor-level** — may not be fully correctable via XML
8. **All measurements are comparative** — not absolute calibration

## 12. Device State (Final)

| Property | Value |
|----------|-------|
| ADB | ✅ 0123456789ABCDEF (authorized) |
| Active config | `default .xml` (baseline) — NOT changed |
| Staged config | `LXX521_LMC84_Optimized_Corrected.xml` — on device, NOT imported |
| Other configs on device | `LXX521_LMC84_Fresh.xml` |
| Backup | `/sdcard/LMC8.4/backups/20261019_153020/fresh_backup.xml` |
| App | LMC 8.4 Iris R18F1 v8.4.300.414775575.18 |
| Back camera | IMX682, 4624×3472, 5.43mm f/1.89 |

**No config activated.** No app restart. Baseline remains active throughout entire project.

---

*Report generated from verified measurements and analysis. All raw data, scripts, and intermediate results preserved in analysis_results/. No results fabricated. No device changes made without authorization.*
