# IMX682 Calibration Chart Inspection & Print Readiness

**Date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15, SDK 35
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18

## 1. Digital Chart Inspection

### calibration_chart_IMX682.png

| Property | Value |
|----------|-------|
| Path | `C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\calibration_chart_IMX682.png` |
| Size | 5000×6500 px |
| Mode | RGB |
| File size | 250,162 bytes |
| Unique colors | 274 |
| Mean RGB | [218, 217, 216] |
| Min/Max | 0 / 255 |

### Content Analysis

**Checkerboard detection:** NONE found
- Tested patterns: (9×6), (7×5), (8×6), (6×8), (9×7), (7×9), (10×7), (7×10), (11×8), (8×11), (13×9), (9×13), (15×10), (10×15), (20×14), (14×20) — all negative
- Also tested with Otsu thresholding — all negative

**Color content:** Grayscale steps detected (0, 30, 85, 120, 160, 255) plus color patches ([78,121,167], [76,173,198], [100,181,105], [98,122,157])

**Image structure:** Gradient/complex pattern — top-right is mostly white (255), left side varies. Not a uniform checkerboard grid.

**Slanted-edge detection:** Not tested (no checkerboard framework to anchor)

### Print Readiness Assessment

| Criterion | Status | Notes |
|-----------|--------|-------|
| Resolution sufficient | ✅ | 5000×6500 px at 300 DPI = 16.7×21.7 inches |
| Checkerboard detectable | ❌ | No standard checkerboard pattern found |
| Known square dimensions | ❌ | Cannot verify without detectable grid |
| Color reference values | ❌ | No verified sRGB/XYZ reference data |
| Grayscale step values | ⚠️ | Detected (0, 30, 85, 120, 160, 255) but not verified as calibration targets |

**Conclusion:** `calibration_chart_IMX682.png` is **NOT suitable** as a precision calibration reference. It lacks:
- Detectable checkerboard geometry
- Known physical square dimensions
- Verified color reference values
- Slanted-edge targets for MTF analysis

Printing it would produce an uncalibrated pattern with unknown geometry — using it would introduce measurement errors.

### Monitor Version

| Property | Value |
|----------|-------|
| Path | `C:\Users\l\AppData\Local\Temp\opencode\lxx521_docs\calibration_chart_IMX682_monitor.png` |
| Size | 1920×1440 px |
| Mode | RGB |

**Note:** Monitor-displayed charts are explicitly excluded from precision calibration per the master prompt (monitor pixel structure, moiré, and unverified color output).

## 2. Missing Physical Equipment — Acquisition List

| # | Item | Specification | Purpose | Priority | Est. Source |
|---|------|---------------|---------|----------|-------------|
| 1 | Checkerboard | 8×6 or 9×6 squares, matte paper/card, known square size (e.g., 20mm) | Camera intrinsics, distortion | Critical | Print + measure, or purchase calibration board |
| 2 | ISO 12233 Slanted-Edge Chart | 5° slanted edges, multiple edges, high contrast | MTF50, sharpness | Critical | Print or purchase |
| 3 | Siemens Star | Multiple resolution patterns, high contrast | Resolution limit, aliasing | High | Print or purchase |
| 4 | 24-patch ColorChecker | X-Rite ColorChecker Passport or equivalent, verified sRGB/XYZ values | Color accuracy, CIEDE2000, WB | Critical | Purchase (X-Rite, Datacolor, etc.) |
| 5 | 18% Gray Card | Lambertian, neutral reflectance, known reflectance | White balance, exposure | Critical | Purchase (photo supply) |
| 6 | White Reference Card | 90%+ reflectance, neutral | White point, clipping detection | High | Purchase (photo supply) |
| 7 | Matte Mounting Board | Rigid, flat, non-reflective, A3 or larger | Chart mounting | Medium | Art supply store |
| 8 | Tripod with Phone Mount | Stable, adjustable height | Consistent framing | Medium | Photo supply |
| 9 | D65/6500K Light Source | Even, color-accurate, no glare | Controlled lighting | High | Photo supply |

## 3. Print-Ready Preparation (If Printing Digital Chart)

If the user chooses to print `calibration_chart_IMX682.png` despite its limitations:

| Step | Action | Verification |
|------|--------|--------------|
| 1 | Print at 300 DPI (16.7×21.7 inches) | Measure printed dimensions with ruler |
| 2 | Measure individual square/patch dimensions | Use digital calipers, record in mm |
| 3 | Verify patch positions and spacing | Measure multiple patches |
| 4 | Document measured geometry | Record all measurements in capture log |
| 5 | Use only for rough reference, not precision | Do not claim calibration accuracy |

**Warning:** Without verified square dimensions and reference values, printed charts cannot support:
- Camera matrix/distortion coefficient computation
- MTF50 measurement
- CIEDE2000 color accuracy
- Any precision calibration claim

## 4. Current Device State

| Property | Value |
|----------|-------|
| ADB connected | ✅ 0123456789ABCDEF |
| Back camera (IMX682) | 4624×3472 active array |
| Front camera | 4208×3120 |
| UW camera | 2592×1944 |
| Active config | `default .xml` (baseline) |
| Optimized config | `LXX521_LMC84_Optimized_Corrected.xml` — pushed, NOT imported |
| HDR+ software | `HDR+ 1.0.414775603zdy` confirmed |

**No config changes made.** Baseline remains active. No photos captured in this session.

## 5. Next Steps (When Charts Acquired)

1. Print `calibration_chart_IMX682.png` at 300 DPI; measure printed square dimensions with calipers
2. Acquire ISO 12233 chart, Siemens star, ColorChecker, gray card, white reference
3. Execute capture phases (baseline first, then request authorization for optimized A/B)
4. Pull images via ADB read-only
5. Analyze valid targets only

**Do not claim physical calibration accuracy until printed dimensions and reference values are verified.**
