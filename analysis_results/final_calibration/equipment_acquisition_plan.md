# IMX682 Calibration Equipment Acquisition Plan — Minimum Cost

**Date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Baseline Config:** `default .xml` (active, SHA-256 `f5dde315...`)
**Staged Config:** `LXX521_LMC84_Optimized_Corrected.xml` (pushed, NOT imported)

## 1. Existing Inventory — Nothing Found

| Item | Found? | Source | Notes |
|------|--------|--------|-------|
| Physical checkerboard | ❌ No | — | Only Java Checker Framework libraries found (unrelated) |
| ISO 12233 chart | ❌ No | — | |
| Siemens star | ❌ No | — | |
| ColorChecker | ❌ No | — | |
| 18% gray card | ❌ No | — | |
| White reference card | ❌ No | — | |
| Tripod | ❌ No | — | |
| D65 lighting | ❌ No | — | |

**Digital chart:** `calibration_chart_IMX682.png` (5000×6500px) — NOT suitable for precision calibration (no detectable checkerboard, unverified geometry).

## 2. Minimum-Cost Acquisition Plan

### Tier 1: DIY Print-at-Home (Lowest Cost, Verify After Printing)

| # | Item | DIY Approach | Est. Cost | Where | Notes |
|---|------|--------------|-----------|-------|-------|
| 1 | Checkerboard | Print on matte cardstock, measure squares with calipers | $5-15 | Home printer + cardstock | Must measure actual printed square size; do not assume |
| 2 | ISO 12233 slanted-edge | Print on matte paper | $5-10 | Home printer | Download ISO 12233:2017 chart from public sources |
| 3 | Siemens star | Print on matte paper | $5-10 | Home printer | Download public domain Siemens star |
| 4 | 18% gray card | Print on matte paper | $5-10 | Home printer | 18% gray = RGB(117,117,117) in sRGB |
| 5 | White reference | Print on matte paper | $5-10 | Home printer | White = RGB(255,255,255) |

**DIY subtotal: ~$25-55** (plus calipers ~$15-25 if not owned)

### Tier 2: Purchased Reference-Grade (Recommended for Accuracy)

| # | Item | Recommended Product | Est. Cost | Where | Reference Data |
|---|------|---------------------|-----------|-------|----------------|
| 1 | Checkerboard | OpenCV calibration board (9×6 or 10×7), printed | $10-30 | Amazon/eBay | Measure squares with calipers |
| 2 | ISO 12233 Chart | Transparent/Reflective resolution target | $25-60 | Amazon, eBay, photography stores | Manufacturer specs |
| 3 | Siemens Star | Resolution test target | $15-30 | Amazon, photography stores | Line pairs per mm |
| 4 | ColorChecker | X-Rite ColorChecker Passport Photo 2 | $90-110 | B&H, Amazon, Adorama | X-Rite publishes sRGB/XYZ values |
| 5 | 18% Gray Card | Kodak Gray Card or equivalent | $10-20 | Photography stores | 18% reflectance |
| 6 | White Reference | White balance card (90%+) | $10-20 | Photography stores | 90%+ reflectance |
| 7 | Digital Calipers | For measuring printed squares | $15-25 | Hardware store | ±0.01mm precision |
| 8 | Tripod | Any stable phone tripod | $15-30 | Amazon, electronics stores | |
| 9 | Light Source | D65 bulb or daylight | $10-25 | Hardware store | 6500K color temp |

**Purchased subtotal: ~$195-280** (with ColorChecker) or ~$95-170 (without ColorChecker)

### Tier 3: Absolute Minimum (DIY Only, Accept Limitations)

| # | Item | Est. Cost | Accuracy Limitation |
|---|------|-----------|---------------------|
| 1 | Printed checkerboard + calipers | $20-40 | Square size measurement error ±0.1mm |
| 2 | Printed ISO 12233 | $5-10 | Printer scaling may distort edges |
| 3 | Printed gray/white cards | $10-20 | Reflectance not verified |
| 4 | No ColorChecker | $0 | CIEDE2000 not possible |
| 5 | No tripod | $0 | Handheld variation |
| 6 | No D65 light | $0 | Indoor lighting varies |

**DIY minimum subtotal: ~$35-70**

**Trade-off:** Without a verified ColorChecker, absolute color accuracy (CIEDE2000) cannot be computed. Without calipers, printed square sizes cannot be verified. Without a tripod, framing consistency suffers.

## 3. Recommended Minimum Purchase List

| Priority | Item | Product Example | Est. Cost | Why Needed |
|----------|------|-----------------|-----------|------------|
| 1 | Checkerboard print + matte cardstock | Home print on cardstock | $10-20 | Intrinsics, distortion |
| 2 | ISO 12233 chart print | Home print | $5-10 | MTF50 |
| 3 | 18% gray card | Kodak or generic | $10-20 | White balance |
| 4 | White reference card | Generic white card | $10-15 | Clipping, white point |
| 5 | Digital calipers | Any ±0.01mm | $15-25 | Measure printed squares |
| 6 | Tripod | Basic phone tripod | $15-25 | Framing consistency |

**Recommended minimum: ~$65-95**

## 4. Printing Specifications (If DIY)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Printer resolution | 300 DPI minimum | Higher = better edge definition |
| Paper | Matte cardstock, 200-300 gsm | Avoid glossy (reflections) |
| Color mode | sRGB | Standard color space |
| Scaling | 100% (no fit-to-page) | Verify with ruler after printing |
| Chart files | Download from public sources | ISO 12233, Siemens star available online |

## 5. Verification Steps After Acquisition

| Step | Action | Tool | Record |
|------|--------|------|--------|
| 1 | Measure printed checkerboard squares | Digital calipers | Square size in mm (±0.01mm) |
| 2 | Verify chart geometry | Measure multiple squares | Consistency across board |
| 3 | Verify ColorChecker reference values | Manufacturer data sheet | sRGB/XYZ per patch |
| 4 | Verify gray card reflectance | Manufacturer spec | 18% ±2% |
| 5 | Verify white card reflectance | Manufacturer spec | 90%+ |
| 6 | Document lighting conditions | Light meter or app | Color temperature (K) |
| 7 | Record camera-framing distance | Tape measure | Distance to chart in cm |

## 6. Cost Summary

| Tier | Items | Est. Cost | Capabilities |
|------|-------|-----------|--------------|
| Tier 1 (DIY minimum) | Printed charts + calipers | $35-70 | Intrinsics, MTF50 (approximate), WB (approximate) |
| Tier 2 (Recommended) | + gray card, white card, tripod | $65-95 | All above + WB accuracy, clipping |
| Tier 3 (Full reference) | + ColorChecker + D65 light | $170-280 | Full calibration incl. CIEDE2000 |

## 7. Configuration State (DO NOT CHANGE)

| Config | Path | Status | SHA-256 |
|--------|------|--------|---------|
| Baseline | `/sdcard/LMC8.4/default .xml` | ACTIVE | `f5dde315...` |
| Optimized | `/sdcard/LMC8.4/LXX521_LMC84_Optimized_Corrected.xml` | STAGED, NOT imported | `a5d98309...` |

**No config changes authorized.** Baseline remains active. Optimized config remains on device but not imported.

## 8. Session Readiness

| Item | Status |
|------|--------|
| ADB connectivity | ✅ Verified |
| Device authorized | ✅ Yes |
| Capture directory | ✅ `analysis_results/final_calibration/` |
| Analysis scripts | ✅ Available |
| Physical charts | ❌ Not acquired |
| Printer | ? (verify availability) |
| Calipers | ? (verify ownership) |

## 9. Next Steps

1. **Verify printer and calipers availability** at home
2. **Download ISO 12233 and Siemens star charts** from public sources
3. **Purchase minimum equipment** (gray card, white card, checkerboard print materials)
4. **Print charts at 300 DPI**, measure squares with calipers
5. **Execute baseline capture checklist** with measured charts
6. **Pull images via ADB**, analyze valid targets
7. **Request authorization** for optimized config A/B testing

**Do not claim calibration is complete until valid physical references and capture data are available.**
