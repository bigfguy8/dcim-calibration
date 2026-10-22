# IMX682 A/B Test — Baseline Capture Session

**Session date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15, SDK 35
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Active Config:** `default .xml` (baseline) — verified on device
**Staged Config:** `LXX521_LMC84_Optimized_Corrected.xml` — NOT imported

## Pre-Capture Verification

| Check | Status |
|-------|--------|
| ADB connected | ✅ 0123456789ABCDEF (authorized) |
| Baseline config on device | ✅ `default .xml` (141,566 bytes) |
| Optimized config on device | ✅ `LXX521_LMC84_Optimized_Corrected.xml` (143,961 bytes) |
| Baseline config local hash | ✅ `f5dde315...` (matches device) |
| Optimized config local hash | ✅ `a5d98309...` (matches device) |
| ab_analyze.py | ✅ 10,735 bytes |
| ab_report.md | ✅ 5,617 bytes |
| ab_test_plan.md | ✅ 6,473 bytes |
| Current DCIM photos | 32 (all monitor captures) |

## Capture Protocol

### 8 Test Scenes (3 photos each = 24 total)

| # | Scene | Description | Key Metrics to Compare |
|---|-------|-------------|----------------------|
| 1 | Fine texture | Fabric, leaves, or textured surface | Edge density, halos, detail |
| 2 | Foliage | Tree leaves against sky | Green color, edge sharpness, WB |
| 3 | Text | Printed text at readable distance | Sharpening, contrast, halos |
| 4 | Indoor mixed light | Room with window + artificial | WB, HDR, dynamic range |
| 5 | Neutral surfaces | Gray/white wall or paper | Warm cast, color consistency |
| 6 | Bright highlights | Window/sky in frame | Highlight retention, clipping |
| 7 | Low light | Dim indoor (EV < 3) | Noise, NR, shadow detail |
| 8 | Skin tone (optional) | Portrait in consistent light | Color accuracy, skin rendering |

### Per-Scene Capture Procedure

1. **Verify active config:** LMC → Settings → Config → should show `default .xml`
2. **Set up scene:** Consistent framing, lighting, focus, distance
3. **Capture 3 images** with baseline config
4. **Record metadata:** EV, ISO, shutter, aperture, distance, lighting
5. **Note any issues:** Moiré, glare, reflections, focus problems

### Consistency Requirements
- Same phone position (tripod or stable handhold)
- Same focus point (tap to focus on same object)
- Same lighting (avoid changing conditions)
- Same framing (use grid overlay if available)
- Same time of day (outdoor scenes)
- Wait 2-3 seconds between captures

### Capture Log Template

| Scene # | Scene Name | Image Filename | ISO | Shutter | Aperture | EV | Distance (cm) | Lighting | Notes |
|---------|-----------|----------------|-----|---------|----------|-----|---------------|----------|-------|
| 1 | Fine texture | | | | | | | | |
| 1 | Fine texture | | | | | | | | |
| 1 | Fine texture | | | | | | | | |
| 2 | Foliage | | | | | | | | |
| ... | ... | | | | | | | | |

## Post-Capture Steps

1. **Pull photos via ADB** to `ab_comparison/baseline/`
2. **Verify file count** (should be 24)
3. **Verify EXIF metadata** (ISO, EV, software tag)
4. **Run baseline quality checks** (clipping, warm cast, edge density)
5. **Save baseline metrics** to `ab_comparison/baseline_results.json`
6. **Stop and request authorization** before importing optimized config

## Important Notes

- **Do NOT import optimized config** during baseline session
- **Do NOT change active config** without authorization
- **Do NOT delete phone originals** — pull copies only
- **Record all metadata** — distance, brightness, exposure
- **Check for moiré** on each capture
- **All measurements are comparative** — not absolute calibration

## Next Steps

1. **Execute baseline capture** (24 photos across 8 scenes)
2. **Pull images via ADB** to `ab_comparison/baseline/`
3. **Run `ab_analyze.py`** for baseline metrics
4. **Request authorization** to import optimized config
5. **Execute optimized capture** (same 24 scenes)
6. **Run comparison analysis**
7. **Generate final recommendation**

**Authorization required** before importing optimized config or switching active settings.

**I cannot capture photos remotely.** Please execute the baseline capture session and confirm when complete. I'll then pull images via ADB and analyze them.
