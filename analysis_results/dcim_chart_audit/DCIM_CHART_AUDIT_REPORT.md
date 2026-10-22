# DCIM Calibration Chart Photo Audit — Sony IMX682 / LMC 8.4

**Date:** 2026-10-19
**Device:** LAVA LXX521 (Lava Play Ultra), Android 15, SDK 35
**Sensor:** Sony IMX682, rear 5.43mm f/1.89
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Analysis:** 39 images pulled from /sdcard/DCIM/Camera/ on device
**Downscale:** OpenCV metrics computed at max 1024px dimension (full-res EXIF preserved)

## 1. Image Inventory

| Source | Count | Software Tag | EV Range | ISO Range |
|--------|-------|--------------|----------|-----------|
| Stock Camera (MediaTek) | 18 | MediaTek Camera Application | -2.295 to 7.736 | 101 to 4909 |
| LMC 8.4 (HDR+) | 20 | HDR+ 1.0.414775603zdy | 1.883 to 3.709 | 357 to 678 |
| LavaPlayUltra_IMX682_Pro | 4 | HDR+ 1.0.414775603zdy | 2.896 to 2.983 | 632 to 671 |
| **Total** | **39** | | **-2.295 to 7.736** | **101 to 4909** |

All images: 4624×3468 or 3468×4624 (portrait/landscape orientation varies).

## 2. Critical Finding: No Calibration Charts Detected

**38 of 39 images are natural scenes**, not calibration charts. Only 1 image contains a checkerboard pattern:

| File | Pattern | EV | ISO | Notes |
|------|---------|-----|-----|-------|
| IMG_20261019_134758_1.jpg | 8×6 | -2.295 | 4909 | Very dark capture; checkerboard barely visible |

**Conclusion:** None of the 39 DCIM images are suitable calibration targets. They are all natural scene captures. No ISO 12233 slanted-edge MTF, no radial distortion calibration, and no ColorChecker color accuracy measurement can be performed from this dataset.

## 3. White Balance Analysis

### LMC 8.4 Images (20 photos)
| Metric | Min | Max | Mean |
|--------|-----|-----|------|
| R/B Ratio | 1.031 | 1.085 | 1.063 |
| R-G (warm cast) | +4.5 | +9.8 | +7.4 |
| Black Clip % | 0.56% | 13.06% | ~3.5% |
| White Clip % | 0.00% | 0.00% | 0.00% |

**Warm cast confirmed:** All LMC images show R/G bias (R-G +4.5 to +9.8). The warmest is `20261019_145510_lmc_8.4.jpg` at R-G +9.8, R/B 1.078.

### Stock Camera Images (18 photos)
| Metric | Min | Max | Mean |
|--------|-----|-----|------|
| R/B Ratio | 1.012 | 1.076 | 1.057 |
| R-G (warm cast) | +2.7 | +12.2 | +7.2 |
| Black Clip % | 0.00% | 47.17% | ~19% |
| White Clip % | 0.00% | 54.66% | ~17% |

**Stock camera shows wider variation** including extreme clipping cases (up to 54.66% white clip, 47.17% black clip).

## 4. Exposure & Clipping Analysis

### LMC 8.4 (HDR+ enhanced)
- EV range: 1.883 to 3.709 (narrow, indoor/low-light conditions)
- Black clip: 0.56% to 13.06% — 2 images exceed 3% target
- White clip: 0.00% on all images — no highlight blowout
- HDR+ confirmed active via EXIF: `HDR+ 1.0.414775603zdy`

### Stock Camera (auto exposure)
- EV range: -2.295 to 7.736 (wide bracket)
- Black clip: 0% to 47.17% — severe shadow crushing in multiple images
- White clip: 0% to 54.66% — severe highlight blowout in multiple images

**Best LMC images (lowest clipping):**
- `20261019_145500_lmc_8.4.jpg`: black clip 0.56%, white clip 0%
- `020261019_133814_LavaPlayUltra_IMX682_Pro.jpg`: black clip 1.31%, white clip 0%

**Worst LMC images (highest clipping):**
- `_  20261019_132920_lmc_8.4.jpg`: black clip 13.06%, white clip 8.21%

## 5. Sharpness / MTF Analysis

**All MTF50 values are floor-level** (0.001-0.004 cyc/px) because these are natural scenes without slanted-edge targets. No meaningful lens sharpness measurement is possible.

| Image | MTF50 (cyc/px) | Notes |
|-------|----------------|-------|
| `_  20261019_132923_lmc_8.4.jpg` | 0.0039 | Best (but still floor-level) |
| `IMG_20261019_142650_1.jpg` | 0.001 | Typical natural scene |
| `020261019_133814_LavaPlayUltra_IMX682_Pro.jpg` | 0.001 | Typical natural scene |

**MTF50 < 0.1 cyc/px** on all images — cannot assess lens optical performance.

## 6. Edge Density Analysis

| Source | Min | Max | Mean | Target (>10%) |
|--------|-----|-----|------|---------------|
| LMC 8.4 | 2.8% | 6.4% | ~5.5% | NOT MET |
| Stock Camera | 2.4% | 6.3% | ~5.4% | NOT MET |

No image meets the >10% edge density target — consistent with natural scene content lacking high-frequency detail.

## 7. Checkerboard / Distortion Analysis

Only 1 checkerboard detected:
- `IMG_20261019_134758_1.jpg`: 8×6 pattern, EV -2.295 (very dark, ISO 4909)
- **Not usable for calibration** — too dark, single view, monitor geometry confounds lens distortion

No radial distortion coefficients can be computed from this dataset.

## 8. Best Images for Each Measurement (with caveats)

| Task | Best File | Metric | Caveat |
|------|-----------|--------|--------|
| Least black clip (LMC) | `20261019_145500_lmc_8.4.jpg` | 0.56% | Natural scene, not chart |
| Most neutral WB (LMC) | `_  20261019_132924_lmc_8.4.jpg` | R/B 1.031, R-G +4.5 | Still warm cast |
| Best MTF50 | `_  20261019_132923_lmc_8.4.jpg` | 0.0039 cyc/px | Floor-level, not actionable |
| Least white clip | All LMC images | 0.00% | HDR+ working |

## 9. Correlation with LXX521_LMC84_Optimized_Corrected.xml

The corrected config (4 changes from Desktop baseline):
- `cw_rg_key`: 0.5925 → 0.4500 (reduce warm cast)
- `lib_sharpnessb_key`: 0 → 2 (moderate sharpening)
- `lib_sharpgain_key`: 0 → 2 (sharpening gain)
- `lib_sharpmini_key`: 0 → 2 (micro-sharpening)

**Expected impact based on DCIM data:**
- Warm cast R-G +4.5 to +9.8 → cw_rg_key 0.4500 should reduce but may not reach <4.0 target (sensor-level limitation)
- Edge density 2.8-6.4% → sharpness +2 should improve modestly but won't reach >10% target (scene-limited)
- Black clip 0.56-13.06% → no NR changes in corrected config; maintain baseline NR=0
- White clip 0% → HDR+ unchanged at "auto" (baseline setting)

## 10. Unsupported Measurements

| Measurement | Status | Reason |
|-------------|--------|--------|
| Absolute color accuracy (CIEDE2000) | Not available | No ColorChecker reference values |
| ISO 12233 MTF50 | Not possible | No slanted-edge targets in any image |
| Radial distortion coefficients | Not possible | Only 1 checkerboard, too dark, single view |
| Intrinsic camera matrix | Not possible | No valid checkerboard calibration data |
| Sensor-level warm cast correction | Limited | Sensor characteristic, not fully correctable via XML |
| Front camera AWB | No data | No front-camera images in dataset |

## 11. Remaining Uncertainties

1. **Warm cast may persist** — R-G target <4.0 likely not achievable via XML alone (MT6878 ISP sensor characteristic)
2. **No calibration chart data** — All 39 images are natural scenes; controlled chart captures needed
3. **Config not yet tested on device** — Optimized_Corrected.xml pushed but not imported
4. **MTF50 floor-level** — Cannot validate sharpening changes without proper chart targets

## 12. Files Generated

| File | Purpose |
|------|---------|
| `dcim_exif_inventory.json` | EXIF metadata for all 39 images |
| `dcim_exif_inventory.csv` | EXIF metadata (CSV) |
| `dcim_full_analysis.json` | Full OpenCV metrics for all 39 images |
| `dcim_full_analysis.csv` | Full metrics (CSV) |
| `plots/mtf50_all.png` | MTF50 comparison chart |
| `plots/rb_vs_ev.png` | White balance vs EV scatter |
| `plots/black_clip_vs_ev.png` | Black clipping vs EV scatter |
| `plots/edge_density_all.png` | Edge density comparison |
| `plots/iso_vs_ev.png` | ISO vs EV scatter |
| `annotated/` | Checkerboard annotated images (1 image) |

## 13. Recommendations

1. **Capture physical calibration charts** — ISO 12233 slanted-edge + ColorChecker under controlled lighting
2. **Use tripod + perpendicular chart alignment** — Avoid monitor-displayed charts
3. **Capture exposure bracket** — At least 5 exposures (-2 to +2 EV) for dynamic range analysis
4. **Test Optimized_Corrected.xml on device** — Import and capture comparison photos
5. **If warm cast persists** — Consider BSG GCam with AWB correction module (requires user authorization)

**Do not claim sensor-level calibration from these 39 natural-scene JPEGs.**
