# LXX521_NIGHT.xml - status

Derived from `LXX521_TEX.xml` by `scripts/make_night_profile.py`.
Handheld city / nightscape profile for MGC 8.9 (BSG).

## Deltas

| Key family | TEX | NIGHT | Rationale |
| :--- | :--- | :--- | :--- |
| `pref_camera_hdr_plus_key` | auto | enhanced | force HDR+ enhanced so night frames are always merged |
| `pref_frames_hdr_key` | 0 | 8 | stack 8 frames to cut shot noise without a tripod |
| `pref_noise_model_key` | 1 | 0 | use the tuned denoiser instead of the generic noise model |
| `pref_hdrregion_key` | 5 | 6 | wider HDR region so shadows lift while lights stay controlled |
| `lib_denoise_key` | 0 | 3 | strong luma/chroma denoise at high ISO |
| `lib_denoisesmoothing_key` | 0 | 1 | smooth denoise transitions on flat night sky |
| `lib_lumadenoise_key` | 0 | 3 | luma denoise tuned for ISO 1600-6400 grain |
| `lib_lumanoise_key` | 1 | 3 | raise the luma noise threshold before detail is smoothed |
| `lib_sharpgain_key` | 0 | 1 | minimal post-denoise sharpening gain |
| `lib_sharpmini_key` | 0 | 1 | protect fine highlights (street lamps, neon) from halos |
| `lib_sharpnessb_key` | 0 | 1 | restore only low-level micro-contrast after denoise |
| `lib_sharpnessnoisemodel_key` | 1 | 0 | do not sharpen the estimated noise floor |
| `lib_sharpeningedge_key` | 1 | 0 | disable edge sharpening to avoid amplifying night grain |
| `lib_hdrbrightness_key` | 0 | 1 | lift midtones in the HDR merge for night ambience |
| `lib_darkenlight_key` | 0 | 1 | guard small bright sources against clipping |
| `lib_lightfix_key` | 1 | 0 | disable light-fix so point lights keep their real colour |
| `lib_exposure_key` | 0 | 1 | enable the night exposure bias path |
| `lib_night_mode_gain_key` | 0 | 1 | enable night-mode gain compensation |
| `lib_nightmodeexposition_key` | 0 | 1 | enable night-mode exposure adjustment |
| `pref_gamma_curve_mode_key` | -1 | 0 | use the tone curve that preserves shadow detail at night |

## Preserved

- `cw_rg_key*` = `0.5725` (calibrated IMX682 white balance)
- `lib_saturation_key*` = `0.95` (no colour desaturation)
- `lib_shadow_compensation_key*` = `0.95`
- `lib_preservinghigh_key*` (highlight roll-off) unchanged
- All lens, colour-matrix and tone-preset keys not listed above

## Quality gates (night)

- Mean luma 70-120 DN (night scenes are legitimately darker)
- Highlight clipping < 2% (small bright sources)
- Green sigma <= 15 DN @ ISO 3200
- MTF50 center >= 0.18 cy/px, edge >= 0.12 cy/px (denoise costs acuity)
- No visible colour cast: keep green/magenta balance neutral
