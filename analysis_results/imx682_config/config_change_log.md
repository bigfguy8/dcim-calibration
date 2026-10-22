# Config Change Log — LXX521_LMC84_Optimized.xml

## Device & App Info
- **Device:** LAVA LXX521 (Lava Play Ultra), Android 15, SDK 35
- **Sensor:** Sony IMX682, rear 5.43mm f/1.89, front 3.59mm, UW 1.98mm
- **Camera App:** LMC 8.4 Iris R18F1 (com.samsung.android.server.iris), v8.4.300.414775575.18
- **Config Schema:** `<map>` with `lib_*`/`pref_*` string keys, 2640 keys
- **Base Config:** `original_V2_Release_Day.xml` (genuine device baseline, 143,969 bytes)

## Calibration Data Sources

| Source | Images | Key Findings |
|--------|--------|--------------|
| Root-level target photos (121034/39/43) | 3 | EV ~8.0, ISO ~520, R-G +3.3 to +6.8, R/B 1.078-1.096, black clip 1.89-3.21%, white clip 0%, edge density 6.05-6.36% |
| recapture_v12/Camera batch | 37 | EV range 4.9-8.9, ISO 101-4909, best MTF50 0.1438 cyc/px at EV 6.8, checkerboard 16/37 images |
| Stock camera (LavaPlayUltra_IMX682_Pro) | ~6 | Warm cast R-G +8.1 to +12.2 (sensor-level, worse than LMC) |
| LMC V2 Release captures | ~12 | Black clip 1.4-2.2%, white clip 0.45-6.3%, edge density 3.9-12.7% |

## Changes from Baseline (original_V2_Release_Day.xml)

| Key | Baseline | Optimized | Evidence | Rationale |
|-----|----------|-----------|----------|-----------|
| cw_rg_key | 0.5925 | 0.4500 | R-G +3.3 to +6.8 warm cast across all photos | Reduce red gain on rear camera to compensate sensor-level warm bias. Suffixed variants cw_rg_key_2-5 already at 0.4200 in baseline. |
| lib_sharpnessb_key | 1 | 2 | Best MTF50 0.1438 cyc/px at EV 6.8; edge density 3.9-12.7% | Moderate sharpening increase for detail retention without halo artifacts. |
| lib_sharpgain_key | 1 | 2 | Same as above | Gain on sharpening to complement sharpnessb increase. |
| lib_sharpmini_key | 1 | 2 | Same as above | Micro-sharpening for fine detail preservation. |

## Settings Retained at Baseline (No Evidence for Change)

| Key | Value | Reason |
|-----|-------|--------|
| cw_rg_key_2 through cw_rg_key_5 | 0.4200 | Already reduced in baseline; no evidence to change |
| cw_rg_key_front | 0.5925 | No front-camera warm cast data available |
| lib_denoise_key | 1 | ISO up to 4909 covered by noise modeler; black clip 1.89-3.21% within target |
| lib_lumadenoise_key | 1 | Same as above |
| lib_lumanoise_key | 1 | Same as above |
| lib_denoisesmoothing_key | 1 | Same as above |
| pref_iso_noise_key | 2 | Noise modeler covers ISO range 101-4909 |
| pref_camera_hdr_plus_key | enhanced | Confirmed working; HDR+ active, black clip 1.4-2.2% |
| pref_qjpg_key | 97 | High JPEG quality; no evidence for change |
| pref_awb_key | 1 | Daylight preset; outdoor EV range 4.9-8.9 |

## Unsupported Measurements

- **Absolute color accuracy (CIEDE2000):** No ColorChecker reference values available
- **RAW sensor response:** All data from JPEG captures with ISP processing
- **Intrinsic lens parameters:** No physical checkerboard calibration possible (monitor-displayed charts only)
- **Front camera AWB:** No front-camera warm cast measurements available

## Remaining Uncertainties

1. Warm cast R-G reduction from +3.3 to +6.8 toward target <4.0 may not be fully achievable via XML alone (sensor-level MT6878 ISP characteristic)
2. cw_rg_key_2-5 at 0.4200 may already over-correct for some cameras/modes
3. No real-device A/B testing performed yet — all changes are evidence-based estimates
4. Config not yet imported or tested on device
