# IMX682 Calibration Session — Equipment Audit & Readiness

**Session date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15, SDK 35
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18

## 1. Device Verification

| Check | Result |
|-------|--------|
| ADB connected | ✅ 0123456789ABCDEF (authorized) |
| Back camera active array | 4624×3472 (IMX682, rear) |
| Front camera | 4208×3120 |
| UW camera | 2592×1944 |
| Active config | `default .xml` (baseline, SHA-256 `f5dde315...`) |
| Optimized config | `LXX521_LMC84_Optimized_Corrected.xml` (pushed, NOT imported) |
| HDR+ software | `HDR+ 1.0.414775603zdy` confirmed in EXIF |

## 2. Physical Chart Availability

| Chart Type | Available? | Source | Notes |
|------------|------------|--------|-------|
| Checkerboard | ❌ No physical chart | `calibration_chart_IMX682.png` (5000×6500px) available for printing | Needs matte print, known square size |
| ISO 12233 Slanted-Edge | ❌ No physical chart | Not found on system | Needs acquisition |
| Siemens Star | ❌ No physical chart | Not found on system | Needs acquisition |
| 24-patch ColorChecker | ❌ No physical chart | Not found on system | Needs acquisition (X-Rite or equivalent) |
| 18% Gray Card | ❌ No physical chart | Not found on system | Needs acquisition |
| White Reference | ❌ No physical chart | Not found on system | Needs acquisition |

**Conclusion:** No physical calibration charts are available. Only a digital calibration chart PNG exists (`calibration_chart_IMX682.png`, 5000×6500px RGB).

## 3. Equipment Acquisition Checklist

Before executing capture phases, acquire:

| Item | Specification | Purpose | Priority |
|------|---------------|---------|----------|
| Checkerboard print | 8×6 or 9×6 squares, matte paper, known square size (mm) | Intrinsics, distortion | Critical |
| ISO 12233 slanted-edge chart | 5° slanted edges, high contrast | MTF50, sharpness | Critical |
| Siemens star | Multiple resolution patterns | Resolution limit | High |
| 24-patch ColorChecker | X-Rite ColorChecker Passport or equivalent, verified sRGB/XYZ values | Color accuracy, CIEDE2000 | Critical |
| 18% gray card | Lambertian, neutral reflectance | WB calibration, exposure | Critical |
| White reference card | 90%+ reflectance, neutral | White point, clipping | High |
| Matte mounting board | Rigid, flat, non-reflective | Chart mounting | Medium |
| Tripod | Stable, phone mount | Consistent framing | Medium |
| D65/6500K light source | Even, color-accurate illumination | Controlled lighting | High |

## 4. Digital Chart Available

| File | Path | Size | Format | Notes |
|------|------|------|--------|-------|
| calibration_chart_IMX682.png | `C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\calibration_chart_IMX682.png` | 5000×6500 | RGB PNG | Suitable for printing as checkerboard reference |

**Warning:** This is a digital image. Printing it does not guarantee dimensionally accurate squares unless printed at verified scale. Square dimensions must be measured after printing.

## 5. Session Readiness

| Item | Status |
|------|--------|
| ADB connectivity | ✅ Verified |
| Device authorized | ✅ Yes |
| Baseline config active | ✅ `default .xml` |
| Optimized config on device | ✅ Pushed, not imported |
| Pull directory ready | ✅ `analysis_results/final_calibration/` |
| Analysis scripts | ✅ `analyze_dcim.py`, `analyze_opencv.py` available |
| Physical charts | ❌ Not available |

## 6. Next Steps (When Charts Acquired)

1. Print `calibration_chart_IMX682.png` at verified scale; measure square dimensions
2. Acquire ISO 12233 chart, Siemens star, ColorChecker, gray card
3. Execute Phase 1 (checkerboard, baseline config)
4. Execute Phase 2 (sharpness/MTF, baseline config)
5. Execute Phase 3 (color, baseline config)
6. Execute Phase 4 (exposure bracket, baseline config)
7. Execute Phase 5 (noise, baseline config)
8. Execute Phase 6 (HDR, baseline config)
9. Pull all baseline images via ADB
10. **Request authorization** before importing `LXX521_LMC84_Optimized_Corrected.xml`
11. Repeat phases with optimized config for A/B comparison
12. Analyze and report

## 7. Current Config State (DO NOT CHANGE)

- **Active:** `default .xml` (baseline) — 141,566 bytes, SHA-256 `f5dde315...`
- **Staged:** `LXX521_LMC84_Optimized_Corrected.xml` — 143,961 bytes, SHA-256 `a5d98309...` — NOT imported
- **No app restart performed**
- **No settings changed**

**Authorization required** before importing optimized config or changing active settings.
