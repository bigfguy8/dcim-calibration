# MGC Device & APK Audit — LAVA LXX521 (Android 15 / "Baklava")

Scope: static, read-only. No install, no data clear, no camera session, no photo capture.
All values below are recorded from local artifacts (APKs, `aapt`, dex, logcat dumps, vendor files).

## 1. Device
| Item | Value | Class |
|---|---|---|
| Model | LAVA LXX521 | CONFIRMED |
| Android | 15 | CONFIRMED |
| Logical camera IDs | 0, 1, 2 (three) | CONFIRMED |
| Front camera ID | 1 | LIKELY |
| Rear camera IDs | 0 and 2 | LIKELY |
| Vendor camera HAL | NXP Morpho (`/vendor/etc/camera/morpho_*`) | CONFIRMED |
| MGC front sensor active array | 4624×3472 | CONFIRMED |
| MGC front sensor pixel array | 4625×3473 | CONFIRMED |
| MGC front sensor physical size | 4.624 × 3.472 mm | CONFIRMED |
| MGC front RAW sensor output | 4624×3472 | CONFIRMED |
| MGC front YUV outputs | 1440×1080 (preview), 4096×3072 (capture) | CONFIRMED |
| Hardware level / pipeline | Camera2 + CameraPipe (native request processor) | CONFIRMED |
| HDR (HDSR) tuning present | Yes — `morpho_hdsr_tuning_params_0/1.xml`, `*_zoom_0/1.xml` | CONFIRMED |
| Front physical sensor model | UNKNOWN — not inferable from resolution (per scope rules) | UNKNOWN |

Camera-ID / facing evidence (not convention-based):
- `logcat` (9.8.102 run): `FOUND_LENSES [0 1 2]`, `SORTS_LENSES [2 0 1]`,
  `TOGGLE_DISTRIBUTION_BACK_LENSES [2 0]`, `TOGGLE_DISTRIBUTION_FRONT_LENSES [1]`.
- Native MGC config: `active_cam_id_front_key=1`, `active_cam_id_back_key=0`.
- Vendor `morpho_eis_cfg.json` references physical `cameraId: 0` and `cameraId: 3`
  for OIS/EIS (vendor physical numbering, distinct from Android logical IDs).

## 2. Installed packages
| Package | versionName | versionCode | Notes |
|---|---|---|---|
| com.android.MGC_9_4_103 | 9.4.103.650360311.25 | 67635286 | Current build; crashes on front cam |
| com.android.MGC_9_8_102 | 9.8.102.738511538.14 | 68281438 | Candidate, co-installed during crash test |

`pm list packages` confirms BOTH packages present (distinct package names ⇒ safe to coexist).
`pm dump` / `dumpsys package` are **denied** (Termux uid lacks `android.permission.DUMP`,
non-root) — so installed-APK on-disk hashes could not be read directly; metadata was
verified from the downloaded APKs instead (see §3).

## 3. APK build verification (from downloaded APKs)

### 3.1 MGC 9.4.103 V41 (the current build)
| Field | Value |
|---|---|
| File | `$HOME/storage/shared/Download/MGC_9.4.103_V41_MGC.apk` |
| SHA-256 | `3985244c1edc19607132954b6e1c13c3b28c65d41fd1d72d4009c291bb99be69` |
| Package | com.android.MGC_9_4_103 |
| versionName / versionCode | 9.4.103.650360311.25 / 67635286 |
| minSdk / targetSdk | 30 / 34 |
| ABI | arm64-v8a only |
| dex | classes.dex (26,073,768 B), classes2.dex (27,131,252 B) — 2 dex |
| Native libs | 19 .so (incl. `libgcastartup.so` 126,820,376 B) |
| APK size | 326,061,819 B |

### 3.2 MGC 9.8.102 V0 (the candidate)
| Field | Value |
|---|---|
| File | `$HOME/storage/shared/Download/MGC_9.8.102_V0_MGC.apk` |
| SHA-256 | `b15dc553247405079cb3bf7b8a0983f716ccd690af52ca77c60bd316d9b8f8ac` |
| Package | com.android.MGC_9_8_102 |
| versionName / versionCode | 9.8.102.738511538.14 / 68281438 |
| minSdk / targetSdk | 30 / 35 ("Baklava") |
| ABI | arm64-v8a only |
| dex | classes.dex (31,552,380), classes2.dex (25,330,520), classes3.dex (512,324) — 3 dex |
| Native libs | 20 .so |
| APK size | 323,938,309 B |
| Duplicate copy | `MGC_9.8.102_V0_MGC (1).apk` — **identical SHA-256** (same artifact) |

### 3.3 Native-library diff (9.4.103 → 9.8.102)
- **Added in 9.8.102:** `libarcore_sdk_c.so`, `libarcore_sdk_jni.so`, `libsegmentation_predictor_jni.so`
- **Removed in 9.8.102:** `libhalide_hexagon_host.so`, `librampatcher.so`
- ABI unchanged (arm64-v8a only in both). No 32-bit (armeabi-v7a) libraries in either.

## 4. Configuration format & import/export
- Native MGC config is **Android SharedPreferences-style XML**: root `<map>`, children
  `<string>/<long>/<int>/<boolean name="...">value</...>`. 181 entries, 0 duplicates.
- The exported file carries `pref_last_installed_version_code=67635286` and
  `pref_check_hal_update_after_gca_version=67635286`, i.e. it is bound to the
  9.4.103 build (versionCode 67635286). Importing it into 9.8.102 would present a
  9.4.103-era version stamp (not verified at runtime — NOT TESTED).
- Config import/export is via MGC's built-in "import/export configuration" UI; the
  on-device live config lives in the app's private data dir which is **not readable**
  without root (`/data/data/com.android.MGC_9_4_103` → Permission denied).

## 5. Read-only metadata limits (what could NOT be established)
- Live `CameraCharacteristics` (exact `SENSOR_INFO_SENSITIVITY_RANGE` value,
  `hardwareLevel` integer, `LENS_FACING` per ID): **NOT ACCESSIBLE** —
  `dumpsys media.camera` / `cmd media.camera` unavailable (no DUMP permission,
  no root); app private dir unreadable.
- Whether the front camera ever produced a working preview: **NOT TESTED**
  (no runtime camera session performed, per safety scope).
- Front physical sensor model: **UNKNOWN** (resolution 4624×3472 known; model not inferred).
