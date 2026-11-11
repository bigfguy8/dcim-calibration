# LXX521_AI.xml - status

Derived from `LXX521_TEX.xml` by `scripts/make_ai_profile.py`.
Balanced companion to the V4.1 texture-first production profile.

## Deltas

| Key family | TEX | AI | Rationale |
| :--- | :--- | :--- | :--- |
| `pref_frames_hdr_key` | 0 | 2 | enable multi-frame HDR+ merge |
| `pref_qjpg_key` | 97 | 95 | smaller JPEGs, no visible quality loss |
| `lib_denoise_key` | 0 | 1 | enable luminance/chroma denoise |
| `lib_denoisesmoothing_key` | 0 | 1 | smooth denoise transitions |
| `lib_lumadenoise_key` | 0 | 1 | enable luma denoise at high ISO |
| `lib_sharpgain_key` | 0 | 1.0 | moderate post-denoise sharpening |
| `lib_sharpmini_key` | 0 | 0.5 | protect fine texture from halos |
| `lib_sharpnessb_key` | 0 | 1.1 | restore micro-contrast after denoise |

## Preserved

- `cw_rg_key*` = `0.5725` (calibrated IMX682 white balance)
- All colour, tone-curve, HDR-region and lens keys not listed above

## Quality gates

- MTF50 center >= 0.30 cy/px, edge >= 0.22 cy/px
- Mean luma 100-140 DN, highlight clipping < 1%
- Green sigma <= 1.5 DN @ ISO 100 and <= 12 DN @ ISO 3200
