# Monitor Calibration — Complete Baseline Capture Analysis

**Date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15, SDK 35
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Monitor:** Acer (ACR0FDD), 1920×1080 @ 120Hz, ~93 DPI, 53×29cm
**Active Config:** `default .xml` (baseline) — NOT changed
**Captures:** 32 images pulled from device (5 original + 27 new)

## 1. Capture Inventory

| Batch | Time Range | Count | Description |
|-------|------------|-------|-------------|
| Batch 1 | 17:02:17-17:02:49 | 5 | Initial monitor chart captures |
| Batch 2 | 17:07:53-17:07:56 | 7 | Additional captures (burst duplicates) |
| Batch 3 | 17:08:01-17:08:25 | 20 | Additional captures (burst duplicates) |
| **Total** | | **32** | |

All images: 4624×3472, rear IMX682 lens, 5.43mm FL, f/1.89, HDR+ 1.0.414775603zdy.

## 2. Critical Findings

### 2.1 Zero Checkerboard Detections
**0 of 32 images contain detectable checkerboard patterns.** Despite displaying `monitor_checkerboard_15x8.png` full-screen, no checkerboard was detected by OpenCV's `findChessboardCorners` (tested 8 patterns: 9×6, 7×5, 8×6, 6×8, 15×8, 8×15, 10×7, 7×10).

**Cause:** Severe moiré from monitor pixel structure (RGB subpixels) corrupts the checkerboard pattern at the sensor level. The 1920×1080 monitor resolution creates beat frequencies with the 4624×3472 sensor that destroy edge regularity.

### 2.2 Severe Moiré on All Images
| Statistic | Value |
|-----------|-------|
| Moiré score range | 580.7 - 3131.8 |
| Mean moiré score | ~1800 |
| Images with moiré > 2000 | 12 of 32 |
| Images with moiré < 1000 | 3 of 32 |

**No image is free of moiré.** The monitor pixel structure is irrecoverably entangled with the camera sensor output.

### 2.3 MTF50 Floor-Level
All 32 images: MTF50 = 0.001 cyc/px (floor value). Monitor pixel structure completely dominates lens sharpness measurement. **No meaningful lens MTF can be extracted.**

### 2.4 Edge Density Extremely Low
| Statistic | Value |
|-----------|-------|
| Edge density range | 0.006 - 0.028 |
| Mean edge density | ~0.017 |
| Target | >0.10 |

All images are far below the 10% edge density target. Monitor pixel structure, not scene content, determines edge density.

### 2.5 Clipping Analysis

| Image Group | Black Clip % | White Clip % |
|-------------|-------------|-------------|
| Batch 1 (EV 1.4-3.3) | 1.23-12.85% | 0-21.51% |
| Batch 2 (EV -0.1) | 4.69-5.63% | 33.28-34.54% |
| Batch 3 (EV 2.8-3.3) | 8.2-25.49% | 0.0% |

**Severe clipping in all batches:**
- Batch 2: 33-34% white clip (overexposed)
- Batch 3: 8-25% black clip (underexposed shadows)
- Batch 1: Mixed (1.23-12.85% black, 0-21.51% white)

### 2.6 White Balance / Warm Cast

| Statistic | R/B Ratio | R-G (warm cast) |
|-----------|-----------|-----------------|
| Min | 0.998 | +1.5 |
| Max | 1.069 | +8.0 |
| Mean | ~1.04 | ~5.5 |

Warm cast is present in all images (R-G +1.5 to +8.0). Some images show near-neutral (R/B ~1.0) but R-G still positive.

## 3. Per-Batch Analysis

### Batch 1 (5 images, 17:02)
- EV range: 1.423-3.294
- ISO: 340-746
- Moiré: 580.7-2026.8
- Best image: 20261019_170241 (lowest moiré 580.8, R/B 1.059)
- Worst image: 20261019_170217 (highest moiré 2026.8, 21.51% white clip)

### Batch 2 (7 images, 17:07)
- EV: -0.106 (all similar, overexposed)
- ISO: 1793-1860
- Moiré: 2410-2503 (severe)
- White clip: 33-35% (all overexposed)
- R/B near 1.0 (relatively neutral, but R-G +1.5 to +2.0)

### Batch 3 (20 images, 17:08)
- EV range: 2.835-3.534
- ISO: 288-700
- Moiré: 597-3132 (extreme variation)
- Black clip: 8.2-25.49% (severe shadow crushing)
- White clip: 0% (no highlight blowout)
- R-G warm cast: +2.6 to +8.0 (significant variation)

## 4. Unsupported Measurements

| Measurement | Status | Reason |
|-------------|--------|--------|
| Camera intrinsics (K matrix) | Not possible | No checkerboard detected (moiré) |
| Distortion coefficients | Not possible | No checkerboard detected |
| True MTF50 | Not possible | Monitor pixel structure dominates |
| Slanted-edge MTF | Not possible | No detectable slanted edges |
| CIEDE2000 color accuracy | Not possible | No verified ColorChecker references |
| Siemens star resolution | Not possible | Moiré obscures pattern |
| Grayscale tonal response | Not possible | Moiré and clipping corrupt data |
| Absolute white balance | Not possible | Monitor color uncalibrated |

## 5. Key Conclusions

1. **Monitor-based calibration is impractical** for this device — severe moiré from 1920×1080 monitor vs 4624×3472 sensor creates irrecoverable beat frequencies
2. **No image is suitable** for any precision calibration measurement
3. **All 32 images are natural-scene-like** despite displaying monitor charts — moiré destroys all structured patterns
4. **Warm cast is consistently present** (R-G +1.5 to +8.0) — consistent with sensor-level characteristic
5. **Exposure is highly variable** — EV range -0.159 to 3.534 across captures
6. **Physical printed charts are required** for any meaningful calibration

## 6. Recommendations

1. **Do not use monitor-based calibration** for this device — moiré is unrecoverable
2. **Print physical charts** — use `print_targets/` PDFs at 300 DPI on matte cardstock
3. **Measure printed dimensions** with calipers before use
4. **Acquire ColorChecker** for absolute color accuracy
5. **Acquire 18% gray card** for white balance calibration
6. **Use tripod** for consistent framing
7. **Test Optimized_Corrected.xml** — import and capture comparison photos
8. **Do not claim any calibration** from these monitor captures

## 7. Files Generated

| File | Purpose |
|------|---------|
| `monitor_all_captures_analysis.json` | Full metrics for 32 images |
| `monitor_all_captures_analysis.csv` | Full metrics (CSV) |
| `plots/monitor_all_mtf50.png` | MTF50 comparison |
| `plots/monitor_all_wb.png` | White balance comparison |
| `plots/monitor_all_clipping.png` | Clipping comparison |
| `plots/monitor_all_moire.png` | Moiré severity |
| `baseline_capture_analysis.md` | Initial 5-image analysis |
| `monitor_calibration_report.md` | This complete report |

## 8. Config State (Unchanged)

| Config | Status | SHA-256 |
|--------|--------|---------|
| `default .xml` | ACTIVE (baseline) | `f5dde315...` |
| `LXX521_LMC84_Optimized_Corrected.xml` | STAGED, NOT imported | `a5d98309...` |

**No config activated.** No app restart. Baseline remains active.

**Authorization required** before importing optimized config for A/B testing.
