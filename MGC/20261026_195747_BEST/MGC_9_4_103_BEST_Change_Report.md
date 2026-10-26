# MGC 9.4.103 "BEST" CONFIG — CHANGE REPORT (run 20261026_195747_BEST)

Base: native `/sdcard/Download/MGC_CONFIG/9.4.103/mgc.xml`
SHA-256 `911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288`
(schema-CONFIRMED: MGC 9.4.103's own serialized output, 181 keys, 143/181
dex-pool-verified; pre-change backup at `backup/mgc_native_9_4_103.xml`).

Artifacts:
- `MGC_9_4_103_BEST_AllInOne.xml` — best all-in-one (photo + video + night + AWB)
- `MGC_9_4_103_BEST_Night.xml` — byte-identical; special-night domain is already
  optimal in the base (see §2), so no additional night delta exists

## 1. Deltas vs native (exactly 1, all other 180 keys preserved verbatim)

| Key | Native | BEST | Evidence class |
|---|---|---|---|
| `pref_camera_resolution` | `medium` | `full` | CONFIRMED — (a) `full` is a valid resolution token in the 9.4.103 dex string pool (alongside `medium`/`small`); (b) MGC's own `pref_camera_resolution_previous=full` in the same file proves MGC previously ran full-resolution capture on this exact device; (c) rear sensor 4625×3473 supports 48MP-class output |

## 2. Night domain — why zero deltas (existing data, all already optimal)

| Key | Value | Meaning (CONFIRMED present; value semantics as emitted by MGC) |
|---|---|---|
| `pref_camera_back_flashmode_key` | `ns` | NS-permitting flash mode (MGC's own live value) |
| `pref_camera_front_flashmode_key` | `ns` | same for front |
| `auto_ns_key` | `1` | automatic Night Sight enabled |
| `pref_camera_hdr_plus_key` | `on` | HDR+ enabled (daytime) |
| `pref_mode_vesper_level` | `0` | vesper (NS-mode) level — value space undocumented locally; NOT changed (inventing a value is prohibited) |

## 3. All other domains — preserved because no existing data supports a change

- AWB (`gawb_user_bg/rg_*`, 34 values + ratio): MGC's own live calibration;
  no superseding measurement exists.
- Colour/shadow: `fix_saturation_key_N=1`, `c_shad_map_*_key_N=0.625` — keep.
- Noise/quality: `jpg_scaling_key_N=100` (max), `pref_storage_saver=1`,
  `pref_video_hevc_setting_key=1`, video `RES_1080P` + `FPS_30` (4K/60fps
  not evidenced for this device) — keep.
- Peaking `peaking_key_N=1`, `pref_camera_cd_indicator_enabled_key=1`,
  `pref_camera_kepler_enabled_key=1`, `pref_camera_pistachio_enabled_key=1` — keep.
- Camera routing: `active_cam_id_back_key=0`, `active_cam_id_front_key=1` —
  matches MGC harness `TOGGLE_DISTRIBUTION_FRONT_LENSES [1]` — keep.

## 4. Crash position (unchanged, re-CONFIRMED)

The `Range.getUpper()`/`loadConfinesExposureISO` NPE on first front-camera
activation is **not addressable by any key in this schema** (0/181
confinement/ISO-range keys). The BEST config does NOT claim to fix the
crash; version choice (9.8.102, where the fatal has not been observed) is
the crash lever. Front/rear runtime behaviour under BEST = NOT TESTED.

## 5. Validation summary

- Well-formed XML: PASS (both artifacts)
- Root `<map>`: PASS; 181 children each; 0 duplicate keys; 175 string /
  2 long / 2 int / 2 boolean
- Diff vs native: exactly 1 line (`pref_camera_resolution`) — verified by
  `diff` at generation time
- No invented keys: PASS (key set identical to native; 1 value edited,
  from MGC's own emitted token set)
- LMC files: untouched
- No camera launched, no import performed
- Next-step unchanged: test 9.8.102 front-camera activation + export its
  native config to build a schema-verified 9.8.102 profile
