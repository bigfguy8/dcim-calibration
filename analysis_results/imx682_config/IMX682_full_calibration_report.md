# IMX682 Full Calibration Report — LXX521_LMC84_Optimized.xml

**Date:** 2026-10-19
**Device:** LAVA LXX521 (Lava Play Ultra), Android 15, SDK 35
**Sensor:** Sony IMX682, rear 5.43mm f/1.89, front 3.59mm, UW 1.98mm
**Camera App:** LMC 8.4 Iris R18F1 (com.samsung.android.server.iris), v8.4.300.414775575.18
**Config:** `analysis_results/imx682_config/LXX521_LMC84_Optimized.xml`

## 1. Calibration Data Summary

| Dataset | Count | Key Measurements |
|---------|-------|-----------------|
| Target photos (121034/39/43) | 3 | EV ~8.0, ISO ~520, R-G +3.3 to +6.8, R/B 1.078-1.096, black clip 1.89-3.21% |
| recapture_v12/Camera batch | 37 | EV 4.9-8.9, ISO 101-4909, MTF50 best 0.1438 cyc/px at EV 6.8 |
| Stock camera captures | ~6 | R-G +8.1 to +12.2 (worse than LMC) |
| LMC V2 Release captures | ~12 | Black clip 1.4-2.2%, white clip 0.45-6.3% |

## 2. Configuration Changes (vs Baseline)

| Key | Baseline | Optimized | Evidence Base |
|-----|----------|-----------|---------------|
| cw_rg_key | 0.5925 | **0.4500** | Warm cast R-G +3.3 to +6.8; R/B 1.078-1.096 |
| lib_sharpnessb_key | 1 | **2** | MTF50 0.1438 cyc/px best; edge density 3.9-12.7% |
| lib_sharpgain_key | 1 | **2** | Same as above |
| lib_sharpmini_key | 1 | **2** | Same as above |

All other 2636 keys unchanged from baseline.

## 3. Measurements → Settings

### AWB / Color
- **Warm cast:** R-G +3.3 to +6.8 across all analyzed LMC photos. Stock camera shows +8.1 to +12.2 (worse). cw_rg_key reduced from 0.5925 to 0.4500 on rear camera. Suffixed variants cw_rg_key_2-5 already at 0.4200 in baseline.
- **Limitation:** Warm cast is sensor-level (MT6878 ISP); cannot fully reach R-G <4.0 target via XML alone.
- **Unsupported:** Absolute color accuracy (CIEDE2000) — no ColorChecker reference values available.

### Sharpness / Detail
- **MTF50:** Best 0.1438 cyc/px at EV 6.8 (checkerboard target). Floor 0.0063 cyc/px on natural scenes (no slanted edges).
- **Edge density:** 3.9-12.7% across V2 Release captures.
- **Change:** lib_sharpnessb_key 1→2, lib_sharpgain_key 1→2, lib_sharpmini_key 1→2.
- **Limitation:** MTF includes monitor pixel structure, ISP processing, JPEG compression — cannot isolate optical MTF.

### Noise / Exposure
- **ISO range:** 101-4909 across 37-image batch.
- **Black clip:** 1.89-3.21% (target <3%). Baseline NR +1 sufficient.
- **White clip:** 0.45-6.3% (target <5%). HDR+ enhanced confirmed working.
- **No change:** NR keys retained at baseline values.

### HDR
- **Status:** HDR+ 1.0.414775603zdy confirmed active via EXIF.
- **No change:** pref_camera_hdr_plus_key remains "enhanced".

## 3. Variant Comparison

| Config | cw_rg_key | lib_sharpnessb_key | lib_denoise_key | Best For |
|--------|-----------|-------------------|-----------------|----------|
| Baseline (original_V2_Release_Day) | 0.5925 | 1 | 1 | Reference |
| Balanced | 0.5925 | 1 | 1 | Same as baseline |
| Detail | 0.5925 | 3 | 0 | Maximum detail, higher noise |
| Low-light | 0.5925 | 0 | 2 | Low light, less sharpening |
| **Optimized (NEW)** | **0.4500** | **2** | **1** | Balanced warm cast + detail + NR |

## 4. Unsupported Measurements

| Measurement | Status | Reason |
|-------------|--------|--------|
| Absolute color accuracy (CIEDE2000) | Not available | No ColorChecker reference values |
| RAW sensor response | Not available | All data from JPEG with ISP processing |
| Intrinsic lens parameters | Not possible | Monitor-displayed charts only, no physical checkerboard |
| Front camera AWB | No data | No front-camera warm cast measurements |
| Distortion coefficients | Not possible | Single view, monitor geometry confounds lens distortion |

## 5. Remaining Uncertainties

1. **Warm cast may persist** — R-G target <4.0 may not be achievable via XML alone (sensor-level characteristic)
2. **cw_rg_key_2-5 at 0.4200** may over-correct for some cameras/modes — no per-camera data
3. **Config not yet tested on device** — all changes are evidence-based estimates
4. **No real-device A/B comparison** — needs import and capture testing

## 6. Files in analysis_results/imx682_config/

| File | Purpose |
|------|---------|
| original_V2_Release_Day.xml | Backup of genuine device baseline (143,969 bytes, 2640 keys) |
| balanced.xml | V2 Release baseline copy (identical to original) |
| detail.xml | Detail variant (sharpness +3, NR 0) |
| lowlight.xml | Low light variant (NR +2, sharpness 0) |
| LXX521_LMC84_Optimized.xml | **New optimized config** (cw_rg_key 0.4500, sharpness +2) |
| config_change_log.md | All changes from baseline with justification |
| config_validation_report.md | Syntax, schema, range, compatibility validation |
| measurement_to_setting_table.md | Measurement-to-setting mapping |
| IMX682_full_calibration_report.md | This report |
| device_tests/ab_test_report.md | Test plan (awaiting execution) |
| device_tests/warm_cast_analysis.md | Warm cast hypothesis analysis |
| device_tests/test_image_inventory.csv | Test inventory template |

## 7. Next Steps (When Authorized)

1. Push LXX521_LMC84_Optimized.xml to `/sdcard/LMC8.4/` on device
2. Import via LMC Settings → Load config
3. Capture test photos: indoor gray card, outdoor daylight, low light, textured detail
4. Pull photos and run unified_analysis.py for comparison
5. If warm cast persists, test v2.1 AWB variants or consider BSG GCam

## 8. Rollback

- Delete LXX521_LMC84_Optimized.xml from device
- Or restore original_V2_Release_Day.xml via ADB push
- No existing files modified or deleted
