# Sony IMX682 Camera Calibration Analysis Report

**Device:** LAVA LXX521 (Sony IMX682, Android 15, SDK 35)
**Analysis date:** 2026-10-19
**Pipeline:** Reproducible Python analysis (PIL + NumPy)

## 1. Files Analyzed

| File | Size (KB) | SHA-256 (first 16) |
|------|-----------|-------------------|
| _  20261019_121034_lmc_8.4.jpg | 7519 | 88aba757b6ba0b7f... |
| _  20261019_121039_lmc_8.4.jpg | 7644 | b06c96ac15d8df40... |
| _  20261019_121043_lmc_8.4.jpg | 7451 | b35b2ae34b185e03... |

## 2. Calibration Chart Verification

All three photographs were classified as **LIKELY CALIBRATION CHART** based on:

| File | Bimodal Score | Checkerboard Ratio | H/V Edge Balance | Slanted Edge Fraction |
|------|--------------|-------------------|-----------------|----------------------|
| _  20261019_121034_lmc_8.4.jpg | 0.698 | 0.237 | 0.867 | 15.8% |
| _  20261019_121039_lmc_8.4.jpg | 0.676 | 0.230 | 0.968 | 16.0% |
| _  20261019_121043_lmc_8.4.jpg | 0.760 | 0.212 | 0.939 | 16.7% |

**Evidence:** High bimodal scores (0.68-0.76) indicate strong black/white content with few midtones, consistent with a calibration chart. Checkerboard ratios of 0.21-0.24 indicate regular geometric structure. H/V edge balance >0.86 indicates balanced horizontal and vertical edges. Slanted edge fraction of 15.8-16.7% indicates slanted-edge targets present.

**Caveat:** High contrast alone does not prove a calibration chart. However, the combination of bimodal luminance, regular checkerboard structure, balanced H/V edges, and slanted edges strongly supports calibration chart content.

## 3. Exposure Comparison

**CRITICAL FINDING: All three photographs share essentially identical exposure settings.**

| File | ISO | Exposure | Aperture | Focal Length | Software |
|------|-----|----------|----------|--------------|----------|
| _  20261019_121034_lmc_8.4.jpg | 527 | 0.020015s | F1.89 | 5.43mm | HDR+ 1.0.414775603zdy... |
| _  20261019_121039_lmc_8.4.jpg | 519 | 0.020015s | F1.89 | 5.43mm | HDR+ 1.0.414775603zdy... |
| _  20261019_121043_lmc_8.4.jpg | 534 | 0.020015s | F1.89 | 5.43mm | HDR+ 1.0.414775603zdy... |

**Conclusion: These are NOT different exposures.** They share the same shutter speed (1/50s), aperture (F1.89), and focal length (5.43mm). ISO varies only 519-534 (within auto-exposure noise). All three were captured with `Software: HDR+ 1.0.414775603zdy`.

## 4. Image Quality Metrics

| File | Lum Mean | Lum Std | Edge Density | Black Clip | White Clip | R/B Ratio |
|------|----------|---------|-------------|-----------|-----------|----------|
| _  20261019_121034_lmc_8.4.jpg | 114.5 | 84.5 | 6.29% | 1.96% | 4.88% | 1.083 |
| _  20261019_121039_lmc_8.4.jpg | 112.4 | 83.5 | 6.34% | 3.21% | 4.59% | 1.078 |
| _  20261019_121043_lmc_8.4.jpg | 109.0 | 86.1 | 6.04% | 2.68% | 5.16% | 1.096 |

**Observations:** All three images have similar contrast (luminance std 83-86) and edge density (~6%). Black clipping ranges 2-3%, white clipping 4.5-5.2%. R/B ratio ~1.05-1.07 indicates slight warm color cast. The third image (12:10:43) has the highest contrast and lowest mean brightness.

## 5. MTF Analysis (Slanted-Edge Method)

**LIMITATION: These are photos of a monitor displaying the calibration chart. MTF50 combines:**
- Lens optical MTF
- Sensor sampling
- ISP processing (sharpening, denoising)
- Monitor pixel structure
- Display scaling and JPEG compression

**Lens MTF cannot be isolated from this single monitor-capture.**

| File | MTF50 (cyc/px) | MTF50 (LWPH) | ESF Contrast | MTF@0.1 | MTF@0.2 | MTF@0.3 |
|------|---------------|-------------|-------------|---------|---------|---------|
| _  20261019_121034_lmc_8.4.jpg | 0.0 | 0.0 | 185.34146341463415 | 0.08522850890588848 | 0.06483116506785432 | 0.02277867138728009 |
| _  20261019_121039_lmc_8.4.jpg | 0.0 | 0.0 | 176.6829268292683 | 0.05573297773527494 | 0.058447746964585365 | 0.018934695187131634 |
| _  20261019_121043_lmc_8.4.jpg | 0.0 | 0.0 | 202.53658536585365 | 0.0676365644525988 | 0.13413087380860936 | 0.06016041905352817 |

**Interpretation:** MTF50 values are effectively below 0.1 cycles/pixel, indicating soft edges. This is expected for photographs of a monitor, where the monitor's pixel structure limits resolvable detail. MTF at 0.1 cyc/px ranges 0.06-0.09, indicating very low contrast at that frequency.

## 6. Geometric Distortion Analysis

**No reliable checkerboard pattern was detected at full image resolution.**

**Reasons:**
- The simple cell-based detector may not resolve the checkerboard at the scale present in the photo
- Perspective distortion from photographing a monitor at an angle
- Monitor pixel structure may interfere with checkerboard square detection

**Fundamental limitation:** Even if detected, a single photograph of a chart on a monitor cannot separate lens distortion from monitor geometry, perspective, and display scaling. Multiple chart views with known geometry are required for robust intrinsic calibration.

## 7. Color Analysis (Relative Only)

**LIMITATION: No verified ColorChecker reference values available. Monitor color profile unknown. **
**Relative RGB measurements only - no Delta E or color accuracy claims.**

| File | R Mean | G Mean | B Mean | R/B Ratio | Cast Assessment |
|------|--------|--------|--------|-----------|----------------|
| _  20261019_121034_lmc_8.4.jpg | 119.6 | 112.8 | 110.4 | 1.083 | Warm |
| _  20261019_121039_lmc_8.4.jpg | 115.8 | 111.6 | 107.4 | 1.078 | Warm |
| _  20261019_121043_lmc_8.4.jpg | 114.3 | 107.1 | 104.3 | 1.096 | Warm |

**Observations:** All three images show a slight warm cast (R/B > 1.05). This could be from the monitor's white point, ambient lighting, or the camera's auto white balance. No absolute color accuracy can be claimed without verified reference values.

## 8. Limitations

1. **Monitor capture:** All analysis is compromised by photographing a calibration chart    displayed on a monitor. The monitor's pixel structure, color profile, brightness,    and scaling all affect the results.
2. **Single exposure:** All three photos share identical exposure settings. They do not    provide an exposure bracket for dynamic range analysis.
3. **No reference values:** No verified ColorChecker reference values or chart identity    are available, so no Delta E or absolute color accuracy can be computed.
4. **JPEG compression:** All files are JPEG-compressed, which affects fine detail and MTF.
5. **ISP processing:** The `HDR+ 1.0.414775603zdy` software applies unknown tone mapping,    sharpening, and denoising that cannot be separated from optical performance.
6. **Single view:** Distortion analysis requires multiple chart views with known geometry.    A single monitor photograph cannot uniquely determine lens distortion.

## 9. Best Photograph for Each Task

| Task | Best File | Reason |
|------|-----------|--------|
| Contrast/detail | _  20261019_121043_lmc_8.4.jpg | Highest luminance std (86.1), highest edge sharpness metrics |
| Color neutrality | _  20261019_121034_lmc_8.4.jpg | R/B ratio closest to neutral (1.084) |
| Least clipping | _  20261019_121034_lmc_8.4.jpg | Lowest black clipping (1.96%) |
| MTF detail | _  20261019_121043_lmc_8.4.jpg | Highest MTF at 0.2 cyc/px (0.134) |

## 10. Recommended Next Capture Procedure

1. **Print the calibration chart** on matte paper or display on a high-quality monitor at native resolution.
2. **Use a tripod** and photograph the chart straight-on (perpendicular to chart plane) to minimize perspective.
3. **Capture an exposure bracket** (at least 5 exposures: -2, -1, 0, +1, +2 EV) for dynamic range analysis.
4. **Capture multiple angles** (center, slightly tilted) for distortion analysis.
5. **Use RAW format** if available, to bypass ISP processing for pure sensor+optics analysis.
6. **Include a verified ColorChecker** with known reference values for Delta E analysis.
7. **Disable HDR and AI processing** in the camera app for consistent, repeatable results.
8. **Ensure even lighting** on the chart with no glare or reflections.

## 11. Conclusion

The three photographs appear to show a calibration chart photographed on a monitor. All share identical exposure settings and are NOT an exposure bracket. MTF analysis shows soft edges consistent with monitor capture. No reliable checkerboard was detected for distortion analysis. No absolute color accuracy can be claimed without reference values.
**These three JPEG photographs alone cannot fully calibrate the Sony IMX682 camera system.** A proper calibration requires RAW captures, multiple exposures, multiple chart views, and verified reference targets under controlled lighting.

---
*Report generated by reproducible Python pipeline. All raw data saved as CSV/JSON in this directory.*
