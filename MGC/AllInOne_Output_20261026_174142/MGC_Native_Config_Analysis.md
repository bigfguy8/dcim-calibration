# MGC Native Config Analysis — LXX521 / MGC 9.4.103

Authoritative source: `$HOME/storage/shared/Download/MGC_CONFIG/9.4.103/mgc.xml`
SHA-256: `911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288`
(re-verified this run — matches the expected value.)

## 1. Structure (re-verified, not assumed)
- Root element: `<map>` (Android SharedPreferences XML export). ✓
- Total entries: **181**. ✓
- Type breakdown: **175 string, 2 long, 2 int, 2 boolean**. ✓ (matches prior report)
- Duplicate keys: **0**. ✓
- Empty-valued entries: several (e.g. `pref_camera_picturesize_front_key`,
  `pref_camera_picturesize_back_key`, `hex_editor_*`, `galley_key`,
  `lens_bl_key`, `lens_wl_key`, the two `boolean`s `disable_cam_char_fix_keys`
  and `camera.lenstoggles_enable` are empty/blank-valued in the native export).
- Version stamp: `pref_last_installed_version_code=67635286` and
  `pref_check_hal_update_after_gca_version=67635286` → bound to 9.4.103.

## 2. Front / rear routing (CONFIRMED)
- `active_cam_id_front_key = 1`
- `active_cam_id_back_key = 0`
- `hwlevel_key = 0` (stored hardware-level value)
- `pref_af_mode_front = 0`, `pref_af_mode_back = 0`

## 3. Functional key groups (all 181 categorized)
| Group | Representative keys | Count | Class |
|---|---|---|---|
| AWB / colour (per-cam 0/1/2) | `gawb_user_bg_*`, `gawb_user_rg_*`, `gawb_user_ratio_*` | 66 | CONFIRMED present |
| AWB photo flag | `pref_camera_gawb_b_photo=0` | 1 | CONFIRMED |
| Shadow-map / saturation fix | `c_shad_map_edge_key_*`, `c_shad_map_center_key_*`, `fix_saturation_key_*` | 9 | CONFIRMED |
| HDR / HDR+ | `pref_camera_hdr_plus_key=on`, `pref_camera_hdrplus_option_available_key=1`, `hdr_net_key=1`, `pref_camera_hdr_plus_flashmode_thermally_disabled_key=0` | 4 | CONFIRMED |
| Device type | `device_key=blueline`, `device_hdrplus_key_0/1=blueline` | 3 | CONFIRMED |
| Image sizes | `pref_camera_resolution=medium`, `pref_camera_resolution_previous=full`, `jpg_scaling_key_0/1/2=100`, `jpg_scaling_enable_key_0/1/2=0`, `pref_camera_picturesize_front_key` (empty), `pref_camera_picturesize_back_key` (empty) | 9 | CONFIRMED |
| RAW | `pref_camera_raw_output_key=0`, `pref_camera_raw_output_option_available_key=0`, `pref_raw_output_previous=0` | 3 | CONFIRMED |
| Video | `pref_video_resolution=RES_1080P`, `pref_video_resolution_previous=RES_1080P`, `pref_video_fps_*` (FPS_30/FPS_AUTO), `pref_video_hevc_previous=1`, `pref_video_hevc_setting_key=1` | ~9 | CONFIRMED |
| Exposure/ISO/sensitivity confinement | **NONE** | **0** | **CONFIRMED ABSENT** |
| Noise reduction | **NONE** (noise/supershot not exposed as keys in this build) | 0 | CONFIRMED ABSENT |
| Sharpening/detail | **NONE** | 0 | CONFIRMED ABSENT |
| Flash / mode | `pref_camera_back_flashmode_key=ns`, `pref_camera_front_flashmode_key=ns`, `flash_mode_key=0`, `pref_micro_mode=0`, `pref_mode_vesper_level=0`, `pref_mode_vesperad_option=0` | ~7 | CONFIRMED |
| Command / gesture | `pref_shutter_command_string=66`, `pref_switch_camera_command_string=47`, `pref_zoom_in/out_command_string=19/20`, `pref_double_tap_key=zoom`, `pref_volume_key_action=shutter` | ~8 | CONFIRMED |
| Features / toggles | `pref_camera_catcher_key`, `pref_camera_dynamic_depth_enabled_key`, `pref_camera_enable_iris=0`, `pref_camera_kepler_enabled_key=1`, `pref_camera_pistachio_enabled_key=1`, `pref_mars_enabled=0`, `auto_ns_key=1`, `ptv_ft_key=1`, `peaking_key_0/1/2=1` | ~12 | CONFIRMED |
| Storage / UX | `pref_storage_saver=1`, `save_storage_key=0`, `pref_storage_saver_auto_disable=0`, `pref_camera_recordlocation_key=0`, `pref_camera_sounds_key=0`, `pref_camera_single_shot_sound_key=0`, `pref_camera_cd_indicator_enabled_key=1` | ~8 | CONFIRMED |
| Education / tooltips | `pref_double_tap_launch_edu_count`, `perf_has_run_*_education`, `tooltip_*`, `lUpTi`, `lUpRi`, `perf_has_shown_options_bar` | ~10 | CONFIRMED |
| BSG-specific | `disable_cam_char_fix_keys` (bool, empty), `camera.lenstoggles_enable` (bool, empty), `capture_indicator_thumbnail_uri` | 3 | CONFIRMED (port-specific) |
| Hex/debug | `hex_editor_val_key_0`, `hex_editor_addr_key_0`, `hex_editor_libs_key` (all empty) | 3 | CONFIRMED |

## 4. Key findings for the crash
- **Exposure/ISO confinement keys are ABSENT.** The crashing method
  `loadConfinesExposureISO` has no configuration surface in this build — the
  confinement `Range` is derived from camera characteristics at runtime, not
  read from a config key. This is why a config change cannot prevent the NPE.
- **No noise-reduction or sharpening keys** exist in this MGC build, so an
  "all-in-one" candidate cannot tune them (they are not exposed controls here).
  (Do **not** invent such keys — see scope rule.)
- **Image-size keys for front/back are empty** in the native export; the app
  falls back to its defaults. We do **not** invent a value for
  `pref_camera_picturesize_front_key` because the accepted enum for this exact
  build is not established from local evidence (would be fabrication).

## 5. Classification of "the 181 entries cover every supported setting"
- **NOT ASSUMED.** The 181-entry native export is a snapshot of the app's
  SharedPreferences at export time. It is authoritative for what the app had
  stored, but it is **not** a guaranteed exhaustive list of every setting the
  9.4.103 UI can expose. Unsupported/absent groups (noise, sharpening,
  exposure/ISO confinement) are simply not present as keys.
