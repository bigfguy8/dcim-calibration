# No-Cost IMX682 Optimization Report — LMC 8.4

**Date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15, SDK 35
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Sensor:** Sony IMX682, rear 5.43mm f/1.89
**Active Config:** `default .xml` (baseline) — NOT changed
**Staged Config:** `LXX521_LMC84_Optimized_Corrected.xml` — NOT imported

## 1. Dataset Summary

| Dataset | Images | Source | Key Metrics |
|---------|--------|--------|-------------|
| DCIM (device) | 39 | Stock + LMC 8.4 | Natural scenes + 1 checkerboard |
| Monitor captures | 32 | LMC 8.4 | Monitor charts (severe moiré) |
| Recapture v12 | 37 | LMC 8.4 + Stock | Mixed natural + checkerboard |
| **Total** | **71** | | |

**LMC 8.4 images:** 50 | **Stock images:** 19 | **Unknown:** 2

## 2. LMC 8.4 vs Stock Camera

| Metric | LMC 8.4 | Stock Camera | Winner |
|--------|---------|--------------|--------|
| Warm cast (R-G mean) | +5.7 | +6.0 | LMC (slightly better) |
| Warm cast (R-G range) | -0.3 to +9.8 | +0.9 to +12.2 | LMC (narrower range) |
| R/B ratio (mean) | 1.041 | 1.047 | LMC (closer to 1.0) |
| Black clip % (mean) | 10.64% | 18.34% | LMC (significantly better) |
| White clip % (mean) | 5.36% | 15.82% | LMC (significantly better) |
| Edge density (mean) | 0.0296 | 0.0516 | Stock (higher) |
| MTF50 (mean) | 0.0012 | 0.0011 | Tie (floor-level) |
| EV range | -0.16 to 3.71 | -2.29 to 7.74 | Stock (wider) |
| ISO range | 288-1860 | 101-4909 | Stock (wider) |

**Conclusion:** LMC 8.4 with HDR+ significantly outperforms stock camera on clipping (black clip 10.64% vs 18.34%, white clip 5.36% vs 15.82%). Stock camera has higher edge density but this is scene-dependent. Warm cast is similar on both (sensor-level).

## 3. Exposure Analysis

### EV Distribution
| EV Bucket | LMC Count | Stock Count | LMC Black Clip | Stock Black Clip |
|-----------|-----------|-------------|----------------|------------------|
| EV ~0 (overexposed) | 7 | 4 | 5.18% | 0.00% |
| EV ~3 (normal) | 37 | 2 | 11.38% | 5.80% |
| EV ~4 (underexposed) | 4 | 4 | 12.69% | 19.47% |
| EV ~5-8 (very underexposed) | 0 | 6 | — | 41-47% |

**Key finding:** LMC 8.4 captures are concentrated in EV 2.8-3.7 range (indoor/low-light). Stock camera has wider EV range including extreme underexposure (EV -2.3 to 7.7).

### Clipping vs EV
- **LMC:** Black clip increases with lower EV (expected). White clip only at very low EV (overexposed monitor captures).
- **Stock:** Severe clipping at both extremes (black clip 40-47% at high EV, white clip 33-55% at low EV).

## 4. ISO vs Noise Analysis

| ISO Range | LMC Count | LMC Lum Std | LMC Black Clip | Stock Count | Stock Lum Std | Stock Black Clip |
|-----------|-----------|-------------|----------------|-------------|---------------|------------------|
| 0-200 | 0 | — | — | 5 | 62.7 | 43.03% |
| 200-400 | 9 | 62.7 | 15.98% | 6 | 85.7 | 20.89% |
| 400-800 | 34 | 85.2 | 10.35% | 3 | 98.8 | 2.69% |
| 800-1600 | 0 | — | — | 3 | 81.3 | 0.00% |
| 1600-3200 | 7 | 106.3 | 5.18% | 1 | 74.5 | 0.00% |
| 3200-10000 | 0 | — | — | 1 | 45.5 | 0.00% |

**Key finding:** LMC 8.4 operates primarily in ISO 400-800 range (34 of 50 images). Higher ISO (1600-3200) shows increased luminance noise (lum_std 106.3 vs 85.2) but lower black clip (5.18% vs 10.35%). Stock camera has wider ISO range but more variable clipping.

## 5. Monitor Moiré Analysis

| Severity | Count | Moiré Score |
|----------|-------|-------------|
| Low (<1000) | 8 | 580.7-946.1 |
| Mid (1000-2000) | 11 | 1273.7-1937.6 |
| High (>=2000) | 13 | 2026.8-3131.8 |

**Mean moiré:** 1794.4. **No image is free of moiré.**

**Best (lowest moiré) images:**
- 20261019_170241_lmc_8.4.jpg: moiré=580.7, EV=2.931, ISO=655, R/B=1.059
- 20261019_170817_lmc_8.4.jpg: moiré=597.0, EV=3.234, ISO=531, R/B=1.069
- 20261019_170816_lmc_8.4.jpg: moiré=606.6, EV=3.029, ISO=612, R/B=1.064

**Moiré mitigation strategies (no-cost):**
1. Increase camera-to-screen distance (may reduce moiré but also resolution)
2. Slight defocus (may reduce moiré but also sharpness)
3. Use lower monitor brightness (may reduce moiré contrast)
4. Avoid exact perpendicular alignment (may reduce moiré but introduces perspective)

## 6. Warm Cast Analysis

| Source | R-G Mean | R-G Range | R/B Mean | R/B Range |
|--------|----------|-----------|----------|-----------|
| LMC 8.4 | +5.7 | -0.3 to +9.8 | 1.041 | 0.901-1.085 |
| Stock | +6.0 | +0.9 to +12.2 | 1.047 | 0.996-1.076 |

**Warm cast is sensor-level** — both LMC and Stock show similar warm bias. LMC 8.4 is slightly better (R-G +5.7 vs +6.0 mean). The variation (-0.3 to +9.8) suggests scene-dependent AWB behavior.

**cw_rg_key tuning:** Reduced from 0.5925 to 0.4500 in Optimized_Corrected.xml. This is a conservative reduction. The suffixed variants (cw_rg_key_2-5) are already at 0.4200 in baseline.

## 7. Config Comparison

### Desktop Baseline (working) vs Optimized_Corrected

| Key | Baseline | Optimized | Change |
|-----|----------|-----------|--------|
| cw_rg_key | 0.5925 | 0.4500 | -0.1425 (reduce warm cast) |
| lib_sharpnessb_key | 0 | 2 | +2 (moderate sharpening) |
| lib_sharpgain_key | 0 | 2 | +2 (sharpening gain) |
| lib_sharpmini_key | 0 | 2 | +2 (micro-sharpening) |

All other 2636 keys identical to Desktop baseline.

### Why Original Optimized.xml Failed
The first `LXX521_LMC84_Optimized.xml` was based on `original_V2_Release_Day.xml` (SHA-256 `d592bed3...`) which differed from the device's working `default .xml` (SHA-256 `f5dde315...`) in 29 keys. The corrected version uses the Desktop `default .xml` as baseline and changes only 4 verified keys.

## 8. Best Images for Each Measurement

| Task | Best File | Metric | Caveat |
|------|-----------|--------|--------|
| Least black clip (LMC) | 20261019_170236_lmc_8.4.jpg | 1.23% | Monitor capture, moiré |
| Most neutral WB (LMC) | 20261019_170755_lmc_8.4__3_.jpg | R/B 1.000, R-G +2.0 | Monitor capture, moiré |
| Lowest moiré | 20261019_170241_lmc_8.4.jpg | 580.8 | Still severe |
| Best MTF50 | All floor-level (0.001) | Not actionable | Monitor pixel structure |
| Least white clip (natural) | IMG_20261019_134758_1.jpg | 0.00% | Very dark, ISO 4909 |

## 9. No-Cost Optimization Recommendations

### Config: LXX521_LMC84_Optimized_Corrected.xml
**Status:** Pushed to device, NOT imported (authorization required)

| Change | Evidence | Expected Impact |
|--------|----------|-----------------|
| cw_rg_key: 0.5925 → 0.4500 | Warm cast R-G +5.7 mean (target <4.0) | Moderate warm cast reduction; may not reach <4.0 (sensor-level) |
| lib_sharpnessb_key: 0 → 2 | Edge density 0.0296 mean (target >0.10) | Modest edge density improvement; scene-limited |
| lib_sharpgain_key: 0 → 2 | Same as above | Complement to sharpnessb |
| lib_sharpmini_key: 0 → 2 | Fine detail preservation | Micro-sharpening for detail |

### What Cannot Be Improved via XML
- **Warm cast to <4.0 R-G:** Sensor-level MT6878 ISP characteristic; cw_rg_key reduction helps but cannot fully correct
- **Edge density to >10%:** Scene-dependent; sharpening helps but cannot create detail that doesn't exist
- **MTF50:** Cannot be measured or improved without physical chart targets
- **Color accuracy (CIEDE2000):** No verified ColorChecker references available

### Monitor Moiré Mitigation (No-Cost)
1. **Increase distance:** Move phone further from screen (reduces moiré but also resolution)
2. **Slight defocus:** Manual focus slightly behind screen (reduces moiré but also sharpness)
3. **Lower brightness:** Reduce monitor brightness (reduces moiré contrast)
4. **Avoid exact perpendicular:** Slight angle (reduces moiré but introduces perspective)
5. **Use lower resolution:** Display charts at lower resolution (fewer beat frequencies)

## 10. Unsupported Measurements

| Measurement | Status | Reason |
|-------------|--------|--------|
| Absolute color accuracy (CIEDE2000) | Not available | No ColorChecker reference values |
| True MTF50 | Not available | Monitor pixel structure dominates |
| Camera intrinsics (mm) | Not available | No physical checkerboard |
| Distortion coefficients (mm) | Not available | No physical checkerboard |
| Sensor-level warm cast correction | Limited | cw_rg_key helps but cannot fully correct |
| Front camera AWB | No data | No front-camera captures |

## 11. Files Generated

| File | Purpose |
|------|---------|
| `no_cost_summary.json` | Summary metrics |
| `no_cost_all_data.csv` | All 71 images with metrics |
| `plots/warm_cast_distribution.png` | Warm cast histogram |
| `plots/black_clip_vs_ev.png` | Black clipping vs EV |
| `plots/moire_distribution.png` | Moiré severity |
| `plots/iso_vs_blackclip.png` | ISO vs black clip |
| `plots/edge_density_distribution.png` | Edge density histogram |
| `no_cost_optimization_report.md` | This report |

## 12. Next Steps (No-Cost)

1. **Test Optimized_Corrected.xml on device** — import via LMC Settings, capture comparison photos
2. **Try monitor moiré mitigation** — increase distance, slight defocus, lower brightness
3. **Capture more natural scenes** with consistent lighting for comparative testing
4. **Analyze warm cast variation** — determine if AWB preset changes help
5. **Do not claim absolute calibration** — all measurements are comparative estimates

**Config state:** Baseline `default .xml` remains active. `LXX521_LMC84_Optimized_Corrected.xml` staged but NOT imported. Authorization required for A/B testing.
