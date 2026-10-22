# IMX682 Calibration Analysis Report

**Batch directory:** `C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\bracket_test_1344`
**Analysis date:** 2026-10-19 13:46:38
**Images analyzed:** 5

## Exposure Summary

| File | ISO | Exposure | EV | F# | FL |
|------|-----|----------|----|----|----|
| IMG_20261019_134401_1.jpg | 174 | 0.02001492s | 6.442 | 1.89 | 5.43mm |
| IMG_20261019_134420_1.jpg | 333 | 0.029984616s | 6.795 | 1.89 | 5.43mm |
| IMG_20261019_134408_1.jpg | 246 | 0.02001492s | 6.941 | 1.89 | 5.43mm |
| IMG_20261019_134433_1.jpg | 488 | 0.029984616s | 7.347 | 1.89 | 5.43mm |
| IMG_20261019_134414_1.jpg | 339 | 0.02001492s | 7.404 | 1.89 | 5.43mm |

**Exposure bracket detected:** EV range 6.4 to 7.4

## Image Quality Metrics

| File | Lum Mean | Lum Std | Edge Density | Black Clip | White Clip | R/B Ratio |
|------|----------|---------|-------------|-----------|-----------|----------|
| IMG_20261019_134401_1.jpg | 84.7 | 84.4 | 10.63% | 41.78% | 0.00% | 1.069 |
| IMG_20261019_134420_1.jpg | 111.2 | 94.4 | 11.13% | 7.90% | 0.00% | 1.062 |
| IMG_20261019_134408_1.jpg | 91.7 | 89.2 | 10.97% | 28.96% | 0.00% | 1.067 |
| IMG_20261019_134433_1.jpg | 121.3 | 95.9 | 11.27% | 6.05% | 0.04% | 1.057 |
| IMG_20261019_134414_1.jpg | 103.5 | 93.2 | 11.13% | 11.59% | 0.00% | 1.060 |

## MTF Results

| File | MTF50 (cyc/px) | MTF50 (LWPH) | ESF Contrast | MTF@0.1 | MTF@0.2 | MTF@0.3 |
|------|---------------|-------------|-------------|---------|---------|---------|
| IMG_20261019_134401_1.jpg | 0.0000 | 0.0 | 201.3 | 0.144 | 0.343 | 0.031 |
| IMG_20261019_134420_1.jpg | 0.1438 | 345.3 | 114.0 | 0.626 | 0.481 | 0.249 |
| IMG_20261019_134408_1.jpg | 0.0250 | 60.1 | 110.5 | 0.419 | 0.639 | 0.416 |
| IMG_20261019_134433_1.jpg | 0.0000 | 0.0 | 217.0 | 0.292 | 0.127 | 0.150 |
| IMG_20261019_134414_1.jpg | 0.1125 | 270.2 | 116.1 | 0.514 | 0.293 | 0.584 |

## Distortion Analysis

**IMG_20261019_134401_1.jpg:** Checkerboard detected (6x8), alternation ratio=0.402
**IMG_20261019_134420_1.jpg:** Checkerboard detected (6x8), alternation ratio=0.402
**IMG_20261019_134408_1.jpg:** Checkerboard detected (6x8), alternation ratio=0.415
**IMG_20261019_134433_1.jpg:** No checkerboard detected
**IMG_20261019_134414_1.jpg:** Checkerboard detected (6x8), alternation ratio=0.415

## Limitations

- MTF50 includes monitor pixel structure if chart was photographed on a display
- JPEG compression affects fine detail and MTF
- ISP processing (sharpening, denoising, HDR) cannot be separated from optical performance
- Single-view distortion analysis cannot separate lens distortion from perspective
- No verified ColorChecker reference values for absolute color accuracy
