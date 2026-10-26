# MGC VERSION COMPATIBILITY MATRIX — LAVA LXX521 (Android 15)

Run 20261026_190044. Static evidence only: APK badging (aapt), dex string-pool
comparison, MGC on-device camera-enumeration logs, crash-log captures.
No camera session launched by this run; no photo captured.

## 1. Locally available MGC versions

| Version | APK (SHA-256) | Package | versionCode / Name | min/target SDK | Native config available? |
|---|---|---|---|---|---|
| 9.4.103 (V41) | `MGC_9.4.103_V41_MGC.apk` `3985244c1edc…` (326,061,819 B) | `com.android.MGC_9_4_103` (CONFIRMED in crash logs + aapt) | 67635286 / `9.4.103.650360311.25` | min 30 / target 34 (a:14) | YES — `/sdcard/Download/MGC_CONFIG/9.4.103/mgc.xml`, SHA `911b27d9…` |
| 9.8.102 (V0) | `MGC_9.8.102_V0_MGC.apk` `b15dc5532474…` (323,938,309 B) | `com.android.MGC_9_8_102` (CONFIRMED in crash logs + aapt) | 68281438 / `9.8.102.738511538.14` | min 30 / target 35 (a:15 "Baklava") | NO — schema UNKNOWN locally |
| 9.8.102 duplicate | `MGC_9.8.102_V0_MGC (1).apk` | same | byte-identical (same SHA as above, CONFIRMED in run-174142 inventory) | — | (duplicate, not a distinct build) |
| 9.7.047 | APK NOT locally available | (only crash-log dir `MGC_CRASH_LOG/9.7.047/` exists) | unknown | unknown | NO |

Android 15 compatibility: 9.4.103 (target 34) and 9.8.102 (target 35) both
CONFIRMED installable/launchable on this Android 15 device (both launched and
logged camera enumeration on-device).

## 2. Camera routing (MGC's own on-device test harness, CONFIRMED in logs)

MGC enumerates all 3 camera IDs and classifies lenses (tags `E/FOUND_LENSES`,
`E/TOGGLE_DISTRIBUTION_*`), identical in 9.4.103 (16-21-09 capture) and
9.8.102 (17-16-50 and 19-00-07 captures):

| Item | Value | Status |
|---|---|---|
| `FOUND_LENSES` | `[0 1 2]` | CONFIRMED both versions |
| Rear (back) distribution | `[2 0]` (0 = primary) | CONFIRMED |
| Front distribution | `[1]` | CONFIRMED |
| Rear primary sensor | pixel array 4625×3473, active 4624×3472, physical 4.624×3.472 mm (IMX682-class) | CONFIRMED (9.8.102 log `FIX_SENSOR_INFO_*`) |
| Front sensor | pixel array 4033×3025, active 4032×3024, physical 4.032×3.024 mm | CONFIRMED (9.8.102 log 19-00-07) |
| Native config front routing `active_cam_id_front_key=1` / `active_cam_id_back_key=0` | matches harness | CONFIRMED |

## 3. Config-schema verification (dex string-pool, this run)

Method: `strings -n 4` on all classes*.dex of each APK; match against the
181 unique key names of the verified 9.4.103 native `mgc.xml`.
Raw pools + key list preserved in `evidence/` (pool_94103.txt, pool_98102.txt, keys.txt).

| Metric | 9.4.103 | 9.8.102 |
|---|---|---|
| Literal keys in dex pool | 64 / 181 | 63 / 181 |
| Dynamic-family keys (per-camera suffix `_0/_1/_2`; base name present in pool) | 79 / 181 | 79 / 181 |
| Keys verifiable in pool (literal + family) | 143 / 181 | 142 / 181 |
| Remaining 38/39 keys | absent as literals; provenance = MGC's own serializer output (genuine schema), likely runtime-construction | same |
| Delta vs 9.4.103 pool | — | `pref_has_checked_dual_ev_shadow` and `pref_mode_vesperad_option` NOT in 9.8.102 pool (present in 9.4.103); `hdr_net_key` IN 9.8.102 pool, absent in 9.4.103 |

Family bases CONFIRMED in both pools: `gawb_user_bg_*`, `gawb_user_rg_*`,
`gawb_user_ratio_*`, `c_shad_map_center/edge_key_N`, `device_hdrplus_key_N`,
`jpg_scaling_key_N` (via `device_hdrplus_key` etc.).
`fix_saturation_key_N`, `peaking_key_N`, `jpg_scaling_enable_key_N`,
`lUpRi/lUpTi`, `pref_camera_dirty_lens_history_key0`, `hdr_net_key` bases
NOT found as exact literals (LIKELY concatenation-built; UNKNOWN).

Conclusion:
- 9.4.103 native schema: **CONFIRMED** (its own serialized output + 143/181 pool-verified).
- 9.8.102 schema: **UNKNOWN** — no native 9.8.102 config exists locally; key-set is LIKELY near-identical (142/181 pool-verified, 2 night/edu keys absent, 1 key gained). **No 9.8.102-specific config profile was produced** (rule: do not fabricate a profile for an unverified schema).

## 4. Settings inventory (native 9.4.103 schema, all present in verified config)

| Domain | Keys (camera-indexed where applicable) | Native values | Status |
|---|---|---|---|
| Camera routing | `active_cam_id_back_key=0`, `active_cam_id_front_key=1` | correct for LXX521 | CONFIRMED vs harness |
| HDR+ | `pref_camera_hdr_plus_key=on`, `pref_camera_hdrplus_option_available_key=1`, `pref_camera_hdrplus_flashmode_thermally_disabled_key=0`, `device_hdrplus_key_N=blueline`, `hdr_net_key=1` | enabled | CONFIRMED present; runtime effect NOT TESTED |
| Night Sight | `pref_camera_back_flashmode_key=ns`, `pref_camera_front_flashmode_key=ns`, `auto_ns_key=1`, `pref_mode_vesper_level=0`, `pref_mode_vesperad_option=0`, `pref_has_checked_dual_ev_shadow=0` | NS-permitting flashmodes, auto-NS on, vesper (NS-mode) level 0 | CONFIRMED keys; semantics of `ns`/`vesper_level` value space UNKNOWN (not documented locally) |
| AWB | `gawb_user_bg_*` (16 chars × 2) + `gawb_user_rg_*` (16 × 2) + `gawb_user_ratio_key_N`, `pref_camera_gawb_b_photo=0`, `pref_camera_enable_iris=0` | MGC's own live values | CONFIRMED present; calibrated-quality effect UNKNOWN |
| Colour/shadow | `fix_saturation_key_N=1`, `c_shad_map_center_key_N=0.625`, `c_shad_map_edge_key_N=0.625` | MGC's own values | CONFIRMED present |
| Noise/quality | `pref_storage_saver=1`, `jpg_scaling_key_N=100`, `jpg_scaling_enable_key_N=0`, `pref_camera_resolution=medium` (previous: full) | MGC's own values | CONFIRMED present |
| Sharpening/peaking | `peaking_key_N=1` | on | CONFIRMED present; semantics UNKNOWN |
| Video | `pref_video_resolution=RES_1080P`, `pref_video_hevc_setting_key=1`, `pref_video_fps_cm/p2018/4k_key=FPS_30`, `pref_video_fps_previous=FPS_AUTO` | 1080p + HEVC | CONFIRMED present |
| AF | `pref_af_mode_front=0`, `pref_af_mode_back=0`, `pref_camera_cd_indicator_enabled_key=1` | MGC's own values | CONFIRMED present |
| Exposure-ISO confinement (crash site) | **NO key exists in this schema** (0 of 181 keys matched iso/exposure/confine/range/clamp pattern) | — | CONFIRMED gap; crash unfixable via config |

## 5. Candidates produced

| Candidate | Version | Character | Runtime |
|---|---|---|---|
| `MGC_9_4_103_AllInOne.xml` | 9.4.103 | byte-identical copy of verified native `mgc.xml` (0 keys changed — no measurement justifies a change; all quality domains already at MGC's own live state) | NOT TESTED |
| `MGC_9_4_103_SpecialNight.xml` | 9.4.103 | byte-identical to AllInOne. Night domain is already in MGC's night-enabled state (`ns` flashmodes, `auto_ns_key=1`). No evidence-based night delta exists; changing `pref_mode_vesper_level`/flashmode values would invent undocumented values → prohibited | NOT TESTED |
| (none) | 9.8.102 | schema UNKNOWN → no profile fabricated | — |
| (none) | 9.7.047 | APK not available locally | — |

## 6. Best-supported version (evidence-based ranking)

1. **MGC 9.8.102 (V0)** — LIKELY best for this Android 15 device: targetSdk 35
   (device-native), launched repeatedly on-device, lens enumeration + sensor
   metadata probes work (front ID 1 confirmed), the fatal
   `Range.getUpper`/`loadConfinesExposureISO` NPE was **NOT observed in any
   9.8.102 capture**, whereas it is CONFIRMED fatal in 9.4.103 and
   9.7.047-generation. A separate, non-fatal-looking `mts-launcher` NPE
   (`leu.e()`) occurred once (17:16:46 capture) and the app relaunched and
   continued enumerating cameras. Front-camera *activation* survival on
   9.8.102 remains **NOT TESTED** (enumeration/characteristics probing only).
2. **MGC 9.4.103 (V41)** — currently installed; CONFIRMED fatal front-camera
   activation crash on first activation (survivable on relaunch, per
   16:21 capture where front streamed at 4624×3472 after restart).
