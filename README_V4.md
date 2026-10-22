# DCIM Calibration V4 — Lava LXX521 / IMX682

## What is included
- `profiles/LXX521_IMX682_Super_AllInOne_V4.xml`: new balanced candidate using the supplied AllInOne_V3-style keys.
- `profiles/`: supplied candidate XML profiles for side-by-side testing.
- `source_profiles/`: copies of the supplied source XMLs and `workflow_master.py`.
- `workflow_master_v4.py`: safer profile picker, XML parser, backup, and deployment helper.
- `manifest.json`: XML parse results, duplicate-key checks, hashes, and limitations.

## Important compatibility note
The uploaded files contain two apparent config families:
- LMC-style keys such as `pref_qjpg_key`, `frame_count_b_photo_0`, and `ptchr_sharpness_0`.
- BSG-style keys such as `pref_quality_key`, `pref_hdr_plus_frames_key`, and `camera_id_back`.

These are not interchangeable unless your exact camera app supports both. The new V4 profile follows the LMC-style `AllInOne_V3` structure. XML parsing only proves syntax, not that the app recognizes each setting.

## Safe use
1. Keep your current working config and do not delete originals.
2. Copy the V4 XML into the target app's supported config folder.
3. Load it through the app's own import mechanism; for LMC 8.4 this is commonly done by double-tapping near the shutter, but confirm against your specific build.
4. Test daylight detail, skin tones, indoor noise, night scenes, moving subjects, and video separately.
5. If you see crashes, black video, strong halos, color shifts, or worse noise, restore the previous profile.

## Termux
Run:
```sh
python workflow_master_v4.py
```
The script searches this pack's `profiles/` and the legacy `analysis_results/imx682_config/` directory. It validates XML before copying and makes a backup of an existing destination file. Default destination is `/sdcard/LMC8.4/`; edit `SDCARD_LMC_DIR` in the script if your exact app uses another folder.

## Limits
No image samples or benchmark outputs were included in this upload, so the V4 values are a reasoned starting point, not a verified quality improvement. No sensor calibration, firmware, protected partition, or device-level data is changed.
