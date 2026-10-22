# IMX682 Calibration Analysis Report

**Batch directory:** `C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\monitor_test_1338`
**Analysis date:** 2026-10-19 13:42:08
**Images analyzed:** 6

## Exposure Summary

| File | ISO | Exposure | EV | F# | FL |
|------|-----|----------|----|----|----|
| 020261019_133816_LavaPlayUltra_IMX682_Pro.jpg | 632 | 0.020015s | 8.303 | 1.89 | 5.43mm |
| 020261019_133821_LavaPlayUltra_IMX682_Pro.jpg | 632 | 0.020015s | 8.303 | 1.89 | 5.43mm |
| 020261019_133846_lmc_8.4.jpg | 645 | 0.020015s | 8.332 | 1.89 | 5.43mm |
| 020261019_133814_LavaPlayUltra_IMX682_Pro.jpg | 654 | 0.020015s | 8.352 | 1.89 | 5.43mm |
| 020261019_133843_lmc_8.4.jpg | 654 | 0.020015s | 8.352 | 1.89 | 5.43mm |
| 020261019_133819_LavaPlayUltra_IMX682_Pro.jpg | 671 | 0.020015s | 8.389 | 1.89 | 5.43mm |

**Note:** All images share similar exposure settings (not an exposure bracket)

## Image Quality Metrics

| File | Lum Mean | Lum Std | Edge Density | Black Clip | White Clip | R/B Ratio |
|------|----------|---------|-------------|-----------|-----------|----------|
| 020261019_133816_LavaPlayUltra_IMX682_Pro.jpg | 111.4 | 87.5 | 11.46% | 6.49% | 0.01% | 1.065 |
| 020261019_133821_LavaPlayUltra_IMX682_Pro.jpg | 109.4 | 87.2 | 11.25% | 7.10% | 0.00% | 1.060 |
| 020261019_133846_lmc_8.4.jpg | 113.5 | 84.5 | 11.59% | 3.66% | 0.00% | 1.058 |
| 020261019_133814_LavaPlayUltra_IMX682_Pro.jpg | 124.9 | 78.8 | 12.05% | 1.36% | 0.00% | 1.073 |
| 020261019_133843_lmc_8.4.jpg | 116.9 | 80.8 | 11.60% | 2.24% | 0.00% | 1.063 |
| 020261019_133819_LavaPlayUltra_IMX682_Pro.jpg | 111.2 | 88.3 | 11.28% | 6.91% | 0.01% | 1.053 |

## MTF Results

| File | MTF50 (cyc/px) | MTF50 (LWPH) | ESF Contrast | MTF@0.1 | MTF@0.2 | MTF@0.3 |
|------|---------------|-------------|-------------|---------|---------|---------|
| 020261019_133816_LavaPlayUltra_IMX682_Pro.jpg | 0.0000 | 0.0 | 217.9 | 0.601 | 0.213 | 0.090 |
| 020261019_133821_LavaPlayUltra_IMX682_Pro.jpg | 0.0000 | 0.0 | 208.1 | 1.000 | 0.439 | 0.111 |
| 020261019_133846_lmc_8.4.jpg | 0.0000 | 0.0 | 198.1 | 1.000 | 0.136 | 0.096 |
| 020261019_133814_LavaPlayUltra_IMX682_Pro.jpg | 0.0000 | 0.0 | 197.6 | 0.499 | 0.270 | 0.073 |
| 020261019_133843_lmc_8.4.jpg | 0.0188 | 45.0 | 164.8 | 0.682 | 0.336 | 0.571 |
| 020261019_133819_LavaPlayUltra_IMX682_Pro.jpg | 0.0063 | 15.0 | 209.5 | 0.436 | 0.108 | 0.087 |

## Distortion Analysis

**020261019_133816_LavaPlayUltra_IMX682_Pro.jpg:** Checkerboard detected (6x8), alternation ratio=0.415
**020261019_133821_LavaPlayUltra_IMX682_Pro.jpg:** Checkerboard detected (6x8), alternation ratio=0.439
**020261019_133846_lmc_8.4.jpg:** Checkerboard detected (6x10), alternation ratio=0.452
**020261019_133814_LavaPlayUltra_IMX682_Pro.jpg:** No checkerboard detected
**020261019_133843_lmc_8.4.jpg:** Checkerboard detected (6x10), alternation ratio=0.413
**020261019_133819_LavaPlayUltra_IMX682_Pro.jpg:** Checkerboard detected (6x8), alternation ratio=0.415

## Limitations

- MTF50 includes monitor pixel structure if chart was photographed on a display
- JPEG compression affects fine detail and MTF
- ISP processing (sharpening, denoising, HDR) cannot be separated from optical performance
- Single-view distortion analysis cannot separate lens distortion from perspective
- No verified ColorChecker reference values for absolute color accuracy
