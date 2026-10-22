# IMX682 Calibration Analysis Report

**Batch directory:** `C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\target_1210`
**Analysis date:** 2026-10-19 14:57:27
**Images analyzed:** 3

## Exposure Summary

| File | ISO | Exposure | EV | F# | FL |
|------|-----|----------|----|----|----|
| _  20261019_121039_lmc_8.4.jpg | 519 | 0.020015s | 8.019 | 1.89 | 5.43mm |
| _  20261019_121034_lmc_8.4.jpg | 527 | 0.020015s | 8.041 | 1.89 | 5.43mm |
| _  20261019_121043_lmc_8.4.jpg | 534 | 0.020015s | 8.06 | 1.89 | 5.43mm |

**Note:** All images share similar exposure settings (not an exposure bracket)

## Image Quality Metrics

| File | Lum Mean | Lum Std | Edge Density | Black Clip | White Clip | R/B Ratio |
|------|----------|---------|-------------|-----------|-----------|----------|
| _  20261019_121039_lmc_8.4.jpg | 112.4 | 79.2 | 6.36% | 3.21% | 0.00% | 1.078 |
| _  20261019_121034_lmc_8.4.jpg | 114.5 | 80.3 | 6.32% | 1.89% | 0.00% | 1.083 |
| _  20261019_121043_lmc_8.4.jpg | 109.0 | 82.3 | 6.05% | 2.67% | 0.00% | 1.096 |

## MTF Results

| File | MTF50 (cyc/px) | MTF50 (LWPH) | ESF Contrast | MTF@0.1 | MTF@0.2 | MTF@0.3 |
|------|---------------|-------------|-------------|---------|---------|---------|
| _  20261019_121039_lmc_8.4.jpg | 0.0063 | 20.0 | 153.0 | 0.356 | 0.216 | 0.665 |
| _  20261019_121034_lmc_8.4.jpg | 0.0063 | 20.0 | 149.3 | 0.198 | 0.339 | 0.189 |
| _  20261019_121043_lmc_8.4.jpg | 0.0063 | 20.0 | 145.5 | 0.569 | 0.441 | 0.525 |

## Distortion Analysis

**_  20261019_121039_lmc_8.4.jpg:** No checkerboard detected
**_  20261019_121034_lmc_8.4.jpg:** No checkerboard detected
**_  20261019_121043_lmc_8.4.jpg:** No checkerboard detected

## Limitations

- MTF50 includes monitor pixel structure if chart was photographed on a display
- JPEG compression affects fine detail and MTF
- ISP processing (sharpening, denoising, HDR) cannot be separated from optical performance
- Single-view distortion analysis cannot separate lens distortion from perspective
- No verified ColorChecker reference values for absolute color accuracy
