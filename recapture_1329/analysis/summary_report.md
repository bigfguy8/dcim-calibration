# IMX682 Calibration Analysis Report

**Batch directory:** `C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\recapture_1329`
**Analysis date:** 2026-10-19 13:30:29
**Images analyzed:** 3

## Exposure Summary

| File | ISO | Exposure | EV | F# | FL |
|------|-----|----------|----|----|----|
| _  20261019_132920_lmc_8.4.jpg | 678 | 0.039992s | 7.405 | 1.89 | 5.43mm |
| _  20261019_132923_lmc_8.4.jpg | 382 | 0.020015s | 7.576 | 1.89 | 5.43mm |
| _  20261019_132924_lmc_8.4.jpg | 384 | 0.020015s | 7.584 | 1.89 | 5.43mm |

**Note:** All images share similar exposure settings (not an exposure bracket)

## Image Quality Metrics

| File | Lum Mean | Lum Std | Edge Density | Black Clip | White Clip | R/B Ratio |
|------|----------|---------|-------------|-----------|-----------|----------|
| _  20261019_132920_lmc_8.4.jpg | 108.2 | 102.1 | 4.96% | 10.79% | 5.62% | 0.901 |
| _  20261019_132923_lmc_8.4.jpg | 147.5 | 67.4 | 8.82% | 0.66% | 0.00% | 1.056 |
| _  20261019_132924_lmc_8.4.jpg | 147.4 | 70.2 | 8.68% | 1.12% | 0.00% | 1.031 |

## MTF Results

| File | MTF50 (cyc/px) | MTF50 (LWPH) | ESF Contrast | MTF@0.1 | MTF@0.2 | MTF@0.3 |
|------|---------------|-------------|-------------|---------|---------|---------|
| _  20261019_132920_lmc_8.4.jpg | 0.0000 | 0.0 | 115.5 | 0.048 | 0.893 | 0.434 |
| _  20261019_132923_lmc_8.4.jpg | 0.0063 | 20.0 | 163.1 | 0.092 | 0.300 | 0.271 |
| _  20261019_132924_lmc_8.4.jpg | 0.0063 | 20.0 | 176.9 | 0.335 | 0.937 | 0.414 |

## Distortion Analysis

**_  20261019_132920_lmc_8.4.jpg:** Checkerboard detected (6x8), alternation ratio=0.402
**_  20261019_132923_lmc_8.4.jpg:** No checkerboard detected
**_  20261019_132924_lmc_8.4.jpg:** No checkerboard detected

## Limitations

- MTF50 includes monitor pixel structure if chart was photographed on a display
- JPEG compression affects fine detail and MTF
- ISP processing (sharpening, denoising, HDR) cannot be separated from optical performance
- Single-view distortion analysis cannot separate lens distortion from perspective
- No verified ColorChecker reference values for absolute color accuracy
