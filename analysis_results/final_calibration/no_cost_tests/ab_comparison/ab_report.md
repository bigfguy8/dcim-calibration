# IMX682 A/B Configuration Comparison — Final Report

**Date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15, SDK 35
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Sensor:** Sony IMX682, rear 5.43mm f/1.89

## 1. Configs Under Test

| Config | File | SHA-256 | Status |
|--------|------|---------|--------|
| Baseline (Control) | `default .xml` | `f5dde315...` | ACTIVE on device |
| Optimized (Treatment) | `LXX521_LMC84_Optimized_Corrected.xml` | `a5d98309...` | Pushed, NOT imported |

### 4 Changes in Optimized
| Key | Baseline | Optimized | Evidence Base |
|-----|----------|-----------|---------------|
| cw_rg_key | 0.5925 | 0.4500 | Warm cast R-G +5.7 mean (target <4.0) |
| lib_sharpnessb_key | 0 | 2 | Edge density 0.0296 (target >0.10) |
| lib_sharpgain_key | 0 | 2 | Complement to sharpnessb |
| lib_sharpmini_key | 0 | 2 | Fine detail preservation |

## 2. Baseline Capture Results

### 2.1 Capture Summary
- **Images captured:** 33 (24 expected + 9 extra)
- **Qualified for baseline:** 18 (selected by feature-based scene classification)
- **Excluded:** 5 (night-mode captures, ISO 15K-25K)
- **Extras:** 10 (not assigned to target scenes)
- **All images:** 4624×3472, rear IMX682, HDR+ active

### 2.2 Baseline Metrics (18 qualified images)

| Metric | Median | Min | Max | Mean | Target |
|--------|--------|-----|-----|------|--------|
| R-G (warm cast) | -5.50 | -17.87 | +10.89 | -3.92 | <4.0 |
| R/B ratio | 1.078 | 0.780 | 1.407 | 1.085 | ~1.0 |
| Edge density | 0.100 | 0.021 | 0.221 | 0.112 | >0.10 |
| Black clip % | 0.65 | 0.10 | 12.33 | 3.01 | <3% |
| White clip % | 0.10 | 0.00 | 6.83 | 0.53 | <5% |
| Lum noise (std) | 55.59 | 38.37 | 89.32 | 60.04 | — |
| Halo score | 415.1 | 264.2 | 743.4 | 461.2 | — |

### 2.3 Scene Coverage

| Scene | Target | Selected | Status |
|-------|--------|----------|--------|
| Fine texture | 3 | 2 | PARTIAL (shortfall 1) |
| Foliage | 3 | 3 | COMPLETE |
| Text | 3 | 3 | COMPLETE |
| Indoor mixed | 3 | 3 | COMPLETE |
| Neutral objects | 3 | 0 | MISSING (shortfall 3) |
| Bright highlights | 3 | 2 | PARTIAL (shortfall 1) |
| Low light | 3 | 2 | PARTIAL (shortfall 1) |
| Skin tone | 3 | 3 | COMPLETE |
| **Total** | **24** | **18** | **6 shortfall** |

### 2.4 Baseline Limitations

1. **Scene classification is feature-based, not visual** — assignments may be incorrect
2. **No "Neutral objects" scene identified** — feature classifier found no low-color-dominance images
3. **Shortfall in 4 scenes** — 6 images needed for complete 24-image baseline
4. **R-G varies wildly** (-17.9 to +10.9) — suggests different scenes/lighting, not config effect
5. **Edge density is scene-dependent** — cannot attribute to config differences
6. **No visual inspection performed** — contact sheet available for manual review
7. **MTF50 is floor-level** (0.001 cyc/px) — cannot assess optical sharpness

## 3. Optimized Config Status

**NOT imported.** `LXX521_LMC84_Optimized_Corrected.xml` is on device at `/sdcard/LMC8.4/` but has NOT been activated. No optimized captures exist.

**Authorization required** before importing optimized config and capturing comparison photos.

## 4. A/B Comparison

**Status: NOT PERFORMED** — requires:
1. Baseline capture verification (18 qualified images analyzed)
2. Authorization to import optimized config
3. 18+ matching optimized captures
4. Run `ab_analyze.py` for comparison

## 5. Config State

| Config | Status | SHA-256 |
|--------|--------|---------|
| `default .xml` | ACTIVE (baseline) | `f5dde315...` |
| `LXX521_LMC84_Optimized_Corrected.xml` | STAGED, NOT imported | `a5d98309...` |

**No config activated.** No app restart. Baseline remains active.

## 6. Recommendations

1. **Visual inspection** of `baseline_contact_sheet.png` to verify scene assignments
2. **If scene identification is uncertain**, request targeted recapture
3. **Proceed with 18 qualified images** for baseline analysis (with documented shortfalls)
4. **Request authorization** for optimized config import
5. **Capture 18+ matching optimized images** (same scenes)
6. **Run A/B comparison** with `ab_analyze.py`
7. **Generate final recommendation** based on repeatable evidence

## 7. Important Constraints

- **Do NOT switch configs without authorization**
- **Do NOT claim improved optical sharpness** — MTF50 is floor-level
- **Do NOT claim sensor-level correction** — warm cast is sensor characteristic
- **Do NOT use monitor captures** for A/B comparison (moiré confounds)
- **Report only repeatable improvements** — single-image differences are noise
- **If optimized is worse, recommend rollback** to baseline

## 8. Files Generated

| File | Purpose |
|------|---------|
| `baseline_qualified_results.json` | Full metrics for 18 qualified images |
| `baseline_qualified_results.csv` | Full metrics (CSV) |
| `baseline_selection_manifest.json` | Scene selection manifest |
| `scene_assignments.json` | Full feature-based classification |
| `baseline_contact_sheet.png` | Visual contact sheet |
| `baseline_scene_selection_report.md` | Scene selection details |
| `baseline_reconciliation_report.md` | Reconciliation analysis |
| `ab_test_plan.md` | Full A/B test protocol |
| `ab_analyze.py` | Analysis script |
| `ab_report.md` | This report |

## 9. Next Steps

1. **Review baseline metrics** above
2. **Request authorization** to import optimized config
3. **Capture matching optimized images** (same 18 scenes)
4. **Run `ab_analyze.py`** for comparison
5. **Generate final recommendation**

**Authorization required** before importing optimized config or switching active settings.
