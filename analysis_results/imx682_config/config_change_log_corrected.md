# Config Change Log — LXX521_LMC84_Optimized_Corrected.xml

## Device & App Info
- **Device:** LAVA LXX521 (Lava Play Ultra), Android 15, SDK 35
- **Sensor:** Sony IMX682, rear 5.43mm f/1.89, front 3.59mm, UW 1.98mm
- **Camera App:** LMC 8.4 Iris R18F1 (com.samsung.android.server.iris), v8.4.300.414775575.18
- **Config Schema:** `<map>` with `lib_*`/`pref_*` string keys, 2640 keys
- **Working Baseline:** Desktop `default .xml` (matches device `/sdcard/LMC8.4/default .xml`)

## Calibration Data Sources

| Source | Images | Key Findings |
|--------|--------|--------------|
| Target photos (121034/39/43) | 3 | EV ~8.0, ISO ~520, R-G +3.3 to +6.8, R/B 1.078-1.096, black clip 1.89-3.21% |
| recapture_v12/Camera batch | 37 | EV range 4.9-8.9, ISO 101-4909, best MTF50 0.1438 cyc/px at EV 6.8 |
| Stock camera (LavaPlayUltra_IMX682_Pro) | ~6 | Warm cast R-G +8.1 to +12.2 (sensor-level, worse than LMC) |
| LMC V2 Release captures | ~12 | Black clip 1.4-2.2%, white clip 0.45-6.3%, edge density 3.9-12.7% |

## Changes from Desktop Working Baseline (`default .xml`)

| Key | Baseline | Corrected | Evidence | Rationale |
|-----|----------|-----------|----------|-----------|
| cw_rg_key | 0.5925 | 0.4500 | R-G +3.3 to +6.8 warm cast across all photos | Reduce red gain on rear camera to compensate sensor-level warm bias. |
| lib_sharpnessb_key | 0 | 2 | Best MTF50 0.1438 cyc/px at EV 6.8; edge density 3.9-12.7% | Moderate sharpening increase for detail retention without halo artifacts. |
| lib_sharpgain_key | 0 | 2 | Same as above | Gain on sharpening to complement sharpnessb increase. |
| lib_sharpmini_key | 0 | 2 | Same as above | Micro-sharpening for fine detail preservation. |

## Settings Retained at Desktop Baseline (No Evidence for Change)

All other 2636 keys are identical to the Desktop `default .xml` (the working device config), including:
- `cw_rg_key_2` through `cw_rg_key_5` = 0.5925 (no per-camera data to justify change)
- `pref_camera_hdr_plus_key` = `auto` (device's current working setting)
- `pref_qjpg_key` = 97 (device's current working setting)
- `lib_denoise_key` = 0 (device's current working setting)
- `pref_awb_key` = 0 (device's current working setting)
- `lib_contrast_1_key` = 0, `lib_contrast_2_key` = 0

## Previous Error (Fixed)

The earlier `LXX521_LMC84_Optimized.xml` was based on `original_V2_Release_Day.xml` (SHA-256 `d592bed3...`) which differed from the device's working `default .xml` (SHA-256 `f5dde315...`). This caused 29 unintended value differences including `pref_qjpg_key: 97→100`, `pref_color_key: 0→-4`, `pref_camera_hdr_plus_key: auto→enhanced`, etc. The corrected config uses the Desktop `default .xml` as the true working baseline and modifies only the 4 verified tuning keys.

## Unsupported Measurements

- **Absolute color accuracy (CIEDE2000):** No ColorChecker reference values available
- **RAW sensor response:** All data from JPEG captures with ISP processing
- **Intrinsic lens parameters:** No physical checkerboard calibration possible (monitor-displayed charts only)

## Remaining Uncertainties

1. Warm cast reduction from R-G +3.3 to +6.8 toward target <4.0 may not be fully achievable via XML alone (sensor-level MT6878 ISP characteristic)
2. Config not yet imported or tested on device — all changes are evidence-based estimates
3. No real-device A/B testing performed yet
