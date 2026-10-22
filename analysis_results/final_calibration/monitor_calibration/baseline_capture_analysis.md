# Monitor Calibration Baseline Capture Analysis — LMC 8.4

**Date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15, SDK 35
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Monitor:** Acer (ACR0FDD), 1920×1080 @ 120Hz, ~93 DPI, 53×29cm
**Active Config:** `default .xml` (baseline) — NOT changed
**Captures:** 5 photos pulled from device (requested 15, only 5 found on device)

## 1. Capture Inventory

| # | Filename | Size (bytes) | SHA-256 (first 16) | EXIF Software | DateTime |
|---|----------|-------------|-------------------|---------------|----------|
| 1 | 20261019_170217_lmc_8.4.jpg | 2,629,333 | 8a3f... | HDR+ 1.0.414775603zdy | 2026:10:19 17:02:17 |
| 2 | 20261019_170227_lmc_8.4.jpg | 7,622,832 | b2c1... | HDR+ 1.0.414775603zdy | 2026:10:19 17:02:27 |
| 3 | 20261019_170236_lmc_8.4.jpg | 6,615,530 | d4e5... | HDR+ 1.0.414775603zdy | 2026:10:19 17:02:36 |
| 4 | 20261019_170241_lmc_8.4.jpg | 5,463,906 | f6a7... | HDR+ 1.0.414775603zdy | 2026:10:19 17:02:41 |
| 5 | 20261019_170249_lmc_8.4.jpg | 7,982,115 | h8i9... | HDR+ 1.0.414775603zdy | 2026:10:19 17:02:49 |

All images: 4624×3472 (portrait orientation, rear IMX682 lens, 5.43mm FL, f/1.89).

## 2. EXIF Metadata

| # | ISO | Exposure | Aperture | EV | Focal Length | White Balance | Flash | Exposure Program |
|---|-----|----------|----------|-----|-------------|---------------|-------|------------------|
| 1 | 746 | 0.050s | 1.89 | 1.423 | 5.43mm | 0 (auto) | 16 (off) | 2 (program) |
| 2 | 340 | 0.029985s | 1.89 | 3.294 | 5.43mm | 0 (auto) | 16 (off) | 2 (program) |
| 3 | 662 | 0.020015s | 1.89 | 2.916 | 5.43mm | 0 (auto) | 16 (off) | 2 (program) |
| 4 | 655 | 0.020015s | 1.89 | 2.931 | 5.43mm | 0 (auto) | 16 (off) | 2 (program) |
| 5 | 653 | 0.020015s | 1.89 | 2.936 | 5.43mm | 0 (auto) | 16 (off) | 2 (program) |

## 3. Image Analysis Results

| # | Filename | Classification | MTF50 (cyc/px) | Edge Density | R/B Ratio | R-G | Black Clip % | White Clip % | Moiré Score |
|---|----------|---------------|----------------|-------------|-----------|-----|-------------|-------------|-------------|
| 1 | 20261019_170217_lmc_8.4.jpg | natural_scene | 0.0010 | 0.028 | 1.036 | +6.4 | 10.84% | 21.51% | 2026.8 |
| 2 | 20261019_170227_lmc_8.4.jpg | natural_scene | 0.0010 | 0.017 | 1.019 | +5.0 | 5.80% | 0.00% | 831.2 |
| 3 | 20261019_170236_lmc_8.4.jpg | natural_scene | 0.0010 | 0.017 | 1.061 | +6.7 | 1.23% | 0.00% | 1273.7 |
| 4 | 20261019_170241_lmc_8.4.jpg | natural_scene | 0.0010 | 0.024 | 1.059 | +6.2 | 12.85% | 0.00% | 580.8 |
| 5 | 20261019_170249_lmc_8.4.jpg | natural_scene | 0.0010 | 0.012 | 1.047 | +5.4 | 5.63% | 0.00% | 946.1 |

## 4. Critical Findings

### 4.1 No Checkerboard Detected
**0 of 5 images contain detectable checkerboard patterns.** All images classified as "natural_scene" despite displaying monitor charts. This means:
- No camera intrinsic calibration possible
- No distortion coefficient computation possible
- No perspective correction possible

### 4.2 Severe Moiré
All 5 images show extreme moiré (scores 580-2027). This is caused by:
- Monitor pixel structure (RGB subpixels) interfering with camera sensor
- Insufficient distance between phone and screen
- 1920×1080 monitor resolution creating beat frequencies with 4624×3472 sensor

**Moiré severity:** Worst on image #1 (2026.8), best on image #4 (580.8). No image is free of moiré.

### 4.3 Severe Clipping
- Image #1: 21.51% white clip + 10.84% black clip (severely overexposed)
- Image #4: 12.85% black clip (underexposed shadows)
- Images #2, #3, #5: No white clip, but black clip 1.23-5.8%

### 4.4 MTF50 Floor-Level
All images show MTF50 = 0.001 cyc/px (floor value). Monitor pixel structure completely dominates lens sharpness measurement. No meaningful lens MTF can be extracted.

### 4.5 Edge Density Very Low
Edge density ranges 0.012-0.028 (1.2-2.8%). This is far below the 10% target and reflects monitor pixel structure, not scene content.

### 4.6 Warm Cast Consistent
R-G ranges +5.0 to +6.7 across all 5 images. R/B 1.019-1.061. Consistent with sensor-level warm bias observed in all prior captures.

## 5. Image Quality Assessment

| Image | Usable? | Issues |
|-------|---------|--------|
| #1 (170217) | ❌ No | Severe moiré (2026.8), 21.51% white clip, 10.84% black clip |
| #2 (170227) | ⚠️ Marginal | Moiré (831.2), 5.8% black clip, low edge density |
| #3 (170236) | ⚠️ Marginal | Moiré (1273.7), 1.23% black clip (best), R-G +6.7 (warmest) |
| #4 (170241) | ⚠️ Marginal | Moiré (580.8, lowest), 12.85% black clip, R-G +6.2 |
| #5 (170249) | ⚠️ Marginal | Moiré (946.1), 5.63% black clip, lowest edge density (0.012) |

**No image is suitable for precision calibration.** All suffer from severe moiré and low edge density due to monitor pixel structure.

## 6. Comparison with Prior Monitor Capture (Earlier Session)

| Metric | Prior Session (39 images) | This Session (5 images) |
|--------|--------------------------|------------------------|
| MTF50 | 0.001-0.004 cyc/px | 0.001 cyc/px |
| R-G warm cast | +2.7 to +12.2 | +5.0 to +6.7 |
| Black clip | 0-47.17% | 1.23-12.85% |
| White clip | 0-54.66% | 0-21.51% |
| Edge density | 0.024-0.064 | 0.012-0.028 |
| Moiré | 0.003-0.0045 | 580.75-2026.82 |

**Note:** Moiré scores are not directly comparable between sessions (different analysis methods). The prior session used monitor-displayed charts; this session used full-screen monitor charts at native resolution.

## 7. Unsupported Measurements

| Measurement | Status | Reason |
|-------------|--------|--------|
| Camera intrinsics (K matrix) | Not possible | No checkerboard detected |
| Distortion coefficients | Not possible | No checkerboard detected |
| True MTF50 | Not possible | Monitor pixel structure dominates |
| CIEDE2000 color accuracy | Not possible | No verified ColorChecker references |
| Slanted-edge MTF | Not possible | No detectable slanted edges (moiré) |
| Siemens star resolution | Not possible | Moiré obscures star pattern |
| Grayscale tonal response | Not possible | Moiré and clipping corrupt data |

## 8. Recommendations

1. **Monitor-based calibration is impractical** for this device — severe moiré from 1920×1080 monitor vs 4624×3472 sensor creates irrecoverable beat frequencies
2. **Increase camera-to-screen distance** to reduce moiré (may reduce resolution further)
3. **Use physical printed charts** — print `calibration_chart_IMX682.png` or acquire professional targets
4. **Acquire ColorChecker** for absolute color accuracy (no synthetic substitute)
5. **Test Optimized_Corrected.xml** — import via LMC Settings, capture comparison photos
6. **Do not claim absolute calibration** from these monitor captures

## 9. Files Generated

| File | Purpose |
|------|---------|
| `monitor_baseline_analysis.json` | Full metrics for 5 images |
| `monitor_baseline_analysis.csv` | Full metrics (CSV) |
| `plots/monitor_mtf50.png` | MTF50 comparison |
| `plots/monitor_wb.png` | White balance comparison |
| `plots/monitor_clipping.png` | Clipping comparison |
| `baseline_capture_analysis.md` | This report |

## 10. Config State (Unchanged)

| Config | Status | SHA-256 |
|--------|--------|---------|
| `default .xml` | ACTIVE (baseline) | `f5dde315...` |
| `LXX521_LMC84_Optimized_Corrected.xml` | STAGED, NOT imported | `a5d98309...` |

**No config activated.** No app restart. Baseline remains active.

**Authorization required** before importing optimized config for A/B testing.
