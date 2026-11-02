# PROFILE COMPATIBILITY REPORT — LAVA LXX521 / Sony IMX682

**Stage:** 1 (read-only audit)
**Date:** 2026-10-31

## 1. Schema Family Separation

Two distinct key families exist in the repository. These are **NOT interchangeable** unless the exact camera app supports both.

### 3.1 LMC 8.4 Key Family

**Marker keys** (presence of these indicates an LMC profile):
- `pref_qjpg_key` — JPEG quality parameter
- `frame_count_b_photo_0` — HDR+ frame count
- `ptchr_sharpness_0` — sharpening strength
- `ptchr_luma_denoise_0` — luminance denoise strength
- `ptchr_contrast_0` — contrast strength
- `ptchr_saturation_0` — saturation strength
- `ptchr_sharp_outline_0` — outline sharpening
- `ptchr_sharp_radius_small_0` — sharpening radius
- `pref_config_nickname_key` — profile nickname

**Typical LMC profile structure:** `<map>` root, children are `<string name="key">value</string>` entries. 26–2641 entries depending on profile scope.

**Device compatibility:** Valid for LMC 8.4 on MT6878/IMX682 (LAVA LXX521), but some keys in the `UNSUPPORTED_LMC_KEYS` set are known not to be part of the valid parameter space for this device.

### 3.2 BSG / MGC Key Family

**Marker keys** (presence of these indicates a BSG/MGC profile):
- `pref_quality_key` — quality selection
- `pref_hdr_plus_frames_key` — HDR+ frames control
- `camera_id_back` — rear camera ID
- `active_cam_id_back_key` — active rear cam ID
- `active_cam_id_front_key` — active front cam ID
- `pref_double_tap_key` — double-tap action
- `hdr_net_key` — HDR network mode
- `pref_camera_grid_lines_mode` — grid lines mode
- `pref_camera_picturesize_front_key` — front picture size
- `pref_camera_picturesize_back_key` — rear picture size
- `gawb_user_bg_a_key_0/1` — AWB coefficients

**Typical BSG profile structure:** `<map>` root, Android SharedPreferences-style XML with `<string>/<long>/<int>/<boolean>` entries. 12–181 entries.

**Device compatibility:** Valid for MGC 9.4.103/9.8.102 on the same hardware, but these profiles use a distinct key namespace separate from LMC 8.4.

### 3.3 Mixed-profile Risk

Profiles containing markers from **both** families are flagged as `MIXED`. Importing a MIXED-profile into an app that supports only one family may cause:
- The app to ignore keys from the other family
- In some configurations, app crashes
- No image-quality improvement from "merged" parameters

**MIXED profiles in this repo:** `profiles/LXX521_BSG_Master.xml`, `profiles/LXX521_BSG_Pro.xml`, `profiles/LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml` (has one LMC marker), `profiles/LXX521_IMX682_AllRounder_NaturalBalanced.xml`

### 3.4 Unknown-profile Key Sets

Profiles with **neither** LMC nor BSG marker keys are classified as `UNKNOWN`. Compatibility with any camera app is unverified. Treat as experimental only.

**UNKNOWN profiles in this repo:** `LXX521_FrontCam_Only_Sanitized.xml` (has `pref_qjpg_key` → actually LMC, not UNKNOWN), plus any profile with a completely different key set.

## 2. Profile Compatibility Matrix

| | LMC 8.4 | BSG MGC | Mixed | Unknown |
|---|---|---|---|---|
| **LMC profile** | ✅ Compatible (syntax + schema) | ⚠️ Keys ignored; app may behave unexpectedly | ❌ Incompatible — key conflict risk | ❓ Unverified |
| **BSG profile** | ⚠️ Keys ignored; may work if app handles both | ✅ Compatible (native schema) | ❌ Incompatible — key conflict risk | ❓ Unverified |
| **Mixed profile** | ❌ Incompatible — may crash or ignore keys | ❌ Incompatible — may crash or ignore keys | ⚠️ Ambiguous — depends on app | ❓ Unverified |
| **Unknown profile** | ❓ Unverified | ❓ Unverified | ❓ Unverified | ❓ Unverified |

**Key:** ✅ = Compatible (syntax + schema identification passed) | ⚠️ = Keys may be ignored; no runtime validation | ❌ = Known incompatibility risk | ❓ = Not tested; cannot determine

## 3. Critical Key Compatibility

### 3.1 LMC critical keys (expected in valid LMC profiles)

| Key | Purpose | Supported on LXX521/IMX682 |
|---|---|---|
| `pref_qjpg_key` | JPEG quality | ✅ |
| `ptchr_sharpness_0` | Sharpening strength | ✅ (range: 0.5–2.0 per supported ranges) |
| `ptchr_luma_denoise_0` | Luminance denoise | ✅ (range: 0.0–2.0) |
| `ptchr_contrast_0` | Contrast | ✅ (range: 0.5–2.0) |
| `ptchr_saturation_0` | Saturation | ✅ (range: 0.5–2.0) |
| `ptchr_sharp_outline_0` | Outline sharpening | ✅ (range: 0.5–2.0) |

### 3.2 BSG critical keys (expected in valid BSG profiles)

| Key | Purpose | Supported on LXX521/IMX682 |
|---|---|---|
| `pref_quality_key` | Quality level | ✅ (MGC 9.4.103/9.8.102) |
| `pref_hdr_plus_frames_key` | HDR+ frames | ✅ (MGC 9.4.103/9.8.102) |
| `camera_id_back` | Rear camera ID | ✅ (MGC 9.4.103/9.8.102) |

### 3.3 Known unsupported LMC keys

These keys appear in some profiles but are **not** part of the valid parameter space for MT6878/IMX682. Their presence does not cause crashes (they are simply ignored), but they indicate a profile that may have been generated for a different device/SOC:

| Key | Present in |
|---|---|
| `pref_video_hdr_plus_key` | Some LMC profiles |
| `pref_hdr_plus_frames_key` | BSG profiles (not in standard LMC) |
| `camera_id_back` | BSG profiles (not in standard LMC) |
| `pref_quality_key` | BSG profiles (not in standard LMC) |
| `lib_gc_mod_0`, `cw_rg_0` | Generic library modifiers not used by LMC 8.4 on MT6878 |

---

## 4. Front Camera Compatibility

**Critical:** The front camera NPE is a **code-level issue**, not a configuration issue.

- Root cause: `SENSOR_INFO_SENSITIVITY_RANGE` is NULL for the front camera (ID 1) on this device.
- `loadConfinesExposureISO()` calls `Range.getUpper()` on a null `Range` object without a null guard.
- No XML profile parameter can supply a valid Range where none exists.
- Fix requires vendor/BSG to add a null guard in `loadConfinesExposureISO()`.

**Profiling impact:** No LMC or BSG profile can resolve the front camera NPE. The compatibility matrix above does not apply to front-camera operation.

---

## 5. Recommendations

1. **Always check schema family** before importing a profile. Use `src/xml_audit.py` Level B validation.
2. **Never merge LMC and BSG profiles.** They use incompatible key namespaces.
3. **Flag MIXED profiles** as incompatible with single-family apps.
4. **Unsupported keys** (per `UNSUPPORTED_LMC_KEYS`) are ignored by LMC 8.4 on MT6878 but indicate the profile may not be optimal for this device.
5. **Front camera:** No XML profile can fix the NPE. A vendor/BSG code change is required.

---

**Profile compatibility complete. No existing files were modified.**