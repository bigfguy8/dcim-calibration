# Measurement-to-Setting Justification Table — LXX521_LMC84_Optimized.xml

| Measurement | Value | Source | Setting | Old | New | Justification |
|-------------|-------|--------|---------|-----|-----|---------------|
| R-G warm cast | +3.3 to +6.8 | Target 3 photos (121034/39/43) | cw_rg_key | 0.5925 | 0.4500 | Reduce red gain on rear camera; baseline 0.5925 too warm. Suffixed cw_rg_key_2-5 already at 0.4200. 0.4500 is compromise to avoid over-correction. |
| R/B ratio | 1.078-1.096 | Target 3 photos | cw_rg_key | 0.5925 | 0.4500 | Consistent with warm cast; lower RG ratio needed on rear camera. |
| Black clip % | 1.89-3.21% | Target 3 photos + V2 Release device test | lib_denoise_key | 1 | 1 (keep) | Within target (<3%). NR +1 already conservative; no change needed. |
| White clip % | 0.45-6.3% | V2 Release device test | pref_camera_hdr_plus_key | enhanced | enhanced (keep) | HDR+ active and functioning; no highlight blowout at typical exposures. |
| Edge density | 3.9-12.7% | V2 Release device test | lib_sharpnessb_key | 1 | 2 | Moderate increase to improve edge density toward >10% target without halo artifacts. |
| MTF50 (best) | 0.1438 cyc/px | recapture_v12 EV 6.8 checkerboard | lib_sharpnessb_key | 1 | 2 | Best measured sharpness; moderate boost sufficient. |
| MTF50 (floor) | 0.0063 cyc/px | Target 3 photos (natural scenes) | — | — | — | Natural scenes lack slanted edges; not actionable via XML. |
| ISO range | 101-4909 | 37-image batch | lib_denoise_key | 1 | 1 (keep) | Noise modeler covers full ISO range; NR +1 sufficient. |
| EV range | 4.9-8.9 | 37-image batch | pref_camera_hdr_plus_key | enhanced | enhanced (keep) | HDR+ handles wide EV range; confirmed working. |
| Stock warm cast | +8.1 to +12.2 R-G | Stock camera photos | cw_rg_key | 0.5925 | 0.4500 | LMC already better than stock; further reduction limited by sensor but 0.4500 helps. |
| LMC V2 black clip | 1.4-2.2% | Device test | lib_denoise_key | 1 | 1 (keep) | Within target; maintain current NR. |
| Software | HDR+ 1.0.414775603zdy | EXIF | pref_camera_hdr_plus_key | enhanced | enhanced (keep) | Confirms HDR+ pipeline active and functioning. |
| JPEG quality | 97 | Baseline | pref_qjpg_key | 97 | 97 (keep) | High quality; no change needed. |
| Checkerboard alternation | 0.40-0.46 | 16 images | — | — | — | Confirms monitor-displayed chart; MTF includes display artifacts. |

## Settings NOT Changed (No Supporting Data)

| Setting | Baseline Value | Reason |
|---------|---------------|--------|
| cw_rg_key_2 through cw_rg_key_5 | 0.4200 | Already reduced in baseline; no per-camera warm cast data to justify change |
| cw_rg_key_front | 0.5925 | No front-camera warm cast measurements available |
| lib_denoise_key through _5 | 1 / 0 | Baseline noise modeler covers ISO range; black clip within target |
| lib_saturation2_key | 0 | No color saturation measurement available |
| lib_contrast_key | 1 | No strong evidence either way; slight boost retained |
| pref_awb_key | 1 | Daylight preset matches outdoor EV range; no AWB preset test data |
