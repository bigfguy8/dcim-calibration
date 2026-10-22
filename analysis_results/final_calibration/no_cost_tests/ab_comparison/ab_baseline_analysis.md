# A/B Baseline Capture Analysis — LMC 8.4

**Date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15, SDK 35
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Active Config:** `default .xml` (baseline) — NOT changed

## 1. Pull Summary

| Property | Value |
|----------|-------|
| Photos pulled | 33 |
| Expected (8 scenes × 3) | 24 |
| Extra photos | 9 |
| Pull directory | `ab_comparison/baseline/` |
| Phone originals | Preserved (not deleted) |

## 2. EXIF Metadata Analysis

### 2.1 Software Tag Variation

| Software Tag | Count | Images |
|-------------|-------|--------|
| `HDR+ 1.0.414775603zdy` | 20 | Normal HDR+ processing |
| `HDR+ 1.0.414775603ndy` | 13 | Unusual suffix — possible different processing mode |

**⚠️ Discrepancy:** 13 images have `ndy` suffix instead of `zdy`. This may indicate:
- Different HDR+ processing mode
- Different config active during capture
- Different camera mode (night mode, etc.)

### 2.2 ISO Anomalies

| Image | ISO | EV | Notes |
|-------|-----|-----|-------|
| 20261019_172306_lmc_8.4.jpg | 24,219 | -5.92 | Impossible ISO for phone camera |
| 20261019_172334_lmc_8.4.jpg | 15,094 | -5.24 | Impossible ISO for phone camera |
| 20261019_172342_lmc_8.4.jpg | 25,500 | -5.99 | Impossible ISO for phone camera |
| 20261019_172405_lmc_8.4.jpg | 25,500 | -5.99 | Impossible ISO for phone camera |
| 20261019_172422_lmc_8.4.jpg | 23,349 | -5.87 | Impossible ISO for phone camera |

**⚠️ These 5 images have impossible ISO values** (max realistic ISO for IMX682 is ~6400-12800). They also have `ndy` software suffix. These may be from a different capture mode or processing pipeline.

### 2.3 Capture Time Groups

| Time Range | Count | ISO Range | EV Range | Software |
|------------|-------|-----------|----------|----------|
| 17:20:24-17:20:44 | 4 | 442-1453 | 0.549-1.837 | Mixed (zdy/ndy) |
| 17:21:01-17:21:37 | 8 | 498-1929 | -0.783 to 3.327 | Mixed (zdy/ndy) |
| 17:22:02-17:22:34 | 8 | 638-1552 | 0.103-1.648 | Mixed (zdy/ndy) |
| 17:23:06-17:24:22 | 5 | 15094-25500 | -5.994 to -5.238 | All ndy |
| 17:24:51-17:25:14 | 8 | 399-793 | 1.335-3.060 | Mixed (zdy/ndy) |

## 3. Image Quality Analysis

### 3.1 Metrics Summary (33 images)

| Metric | Min | Max | Mean | Median |
|--------|-----|-----|------|--------|
| R-G (warm cast) | -18.8 | +11.3 | -3.5 | -5.5 |
| R/B ratio | 0.901 | 1.109 | 1.018 | 1.021 |
| Edge density | 0.003 | 0.221 | 0.085 | 0.073 |
| Black clip % | 0.10 | 52.03 | 12.4 | 6.09 |
| White clip % | 0.00 | 6.83 | 0.72 | 0.13 |
| Lum std (noise) | 16.8 | 89.3 | 50.2 | 46.6 |
| MTF50 (cyc/px) | 0.001 | 0.001 | 0.001 | 0.001 |

### 3.2 Notable Findings

1. **R-G varies wildly** (-18.8 to +11.3) — suggests different scenes/lighting, not config effect
2. **Some images have negative R-G** (-18.8 to -0.8) — unusual for this sensor; may indicate different AWB or processing
3. **5 images have impossible ISO** (15094-25500) — likely from a different capture mode
4. **Black clip ranges 0.1-52.03%** — extreme variation suggests different scenes
5. **Edge density ranges 0.003-0.221** — some images have high edge density (0.17-0.22) which is better than prior data

### 3.3 High-Edge-Density Images (Best Detail)

| Image | Edge Density | R-G | Black Clip | Notes |
|-------|-------------|-----|------------|-------|
| 20261019_172207_lmc_8.4.jpg | 0.221 | -5.5 | 0.64% | Best edge density |
| 20261019_172202_lmc_8.4.jpg | 0.212 | -6.6 | 0.45% | Second best |
| 20261019_172124_lmc_8.4.jpg | 0.173 | -0.8 | 6.24% | High edges, moderate clip |
| 20261019_172126_lmc_8.4.jpg | 0.174 | -1.3 | 6.09% | High edges, moderate clip |
| 20261019_172231_lmc_8.4.jpg | 0.176 | -16.9 | 0.52% | High edges, very cool WB |

### 3.4 Low-Edge-Density Images (Low Detail)

| Image | Edge Density | R-G | Black Clip | Notes |
|-------|-------------|-----|------------|-------|
| 20261019_172306_lmc_8.4.jpg | 0.003 | 1.5 | 50.9% | Very dark, 51% black clip |
| 20261019_172405_lmc_8.4.jpg | 0.004 | -1.2 | 23.14% | Very dark |
| 20261019_172334_lmc_8.4.jpg | 0.019 | 0.8 | 52.03% | Very dark, 52% black clip |
| 20261019_172422_lmc_8.4.jpg | 0.008 | 1.5 | 9.29% | Dark |

## 4. Discrepancies & Issues

### 4.1 Image Count Mismatch
- **Expected:** 24 images (8 scenes × 3 captures)
- **Actual:** 33 images pulled
- **Extra:** 9 images (likely test shots or additional scenes)

### 4.2 Software Tag Variation
- 20 images: `HDR+ 1.0.414775603zdy` (normal)
- 13 images: `HDR+ 1.0.414775603ndy` (unusual)
- **Question:** Were these captured with different settings or processing modes?

### 4.3 Impossible ISO Values
5 images have ISO values of 15,094-25,500. These are not physically possible for the IMX682 sensor. These images also have `ndy` software suffix and very negative EV (-5.2 to -6.0).

### 4.4 Extreme Scene Variation
R-G ranges from -18.8 to +11.3, suggesting these are from very different scenes/lighting conditions, not matched A/B test pairs.

## 5. Validation Status

| Check | Status |
|-------|--------|
| File count | ⚠️ 33 (expected 24) |
| EXIF metadata | ⚠️ Present but anomalous (ndy suffix, impossible ISO) |
| File integrity | ✅ All 33 readable |
| Image dimensions | ✅ All 4624×3472 |
| Lens | ✅ All 5.43mm (rear IMX682) |
| Config active | ✅ `default .xml` (baseline) — NOT changed |
| Phone originals | ✅ Preserved (not deleted) |

## 6. Issues to Resolve

1. **Clarify capture intent:** Were 24 or 33 images captured? Which are A/B test pairs?
2. **Explain ISO anomalies:** 5 images with ISO 15K-25K — different mode or error?
3. **Explain "ndy" suffix:** 13 images with unusual software tag
4. **Scene identification:** Which images correspond to which of the 8 test scenes?
5. **Missing optimized captures:** No optimized config images exist yet (authorization required)

## 7. Next Steps

1. **User clarification needed:** Which of the 33 images are valid baseline A/B captures?
2. **If 24 are valid:** Identify which 9 are extra/test shots
3. **If mixed configs:** Determine which images were captured with which config
4. **Once clarified:** Run A/B analysis with matched pairs
5. **Request authorization** for optimized config import

**Do not claim A/B test results until capture conditions are clarified.**
**Config state:** Baseline `default .xml` remains active. `LXX521_LMC84_Optimized_Corrected.xml` staged but NOT imported.
