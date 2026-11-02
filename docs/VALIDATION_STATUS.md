# Validation Status — LAVA LXX521 / Sony IMX682

**Document:** Four validation levels as defined in mission §8.  Strictly separated.
**Last updated:** 2026-10-31

## 1. Validation Levels (as defined in mission §8)

Four distinct validation levels must be strictly separated. This document records the status of each level for the repository.

### Level A: XML Syntax Validation

**Check:** XML well-formedness, root element `<map>`, all entries have `name` attribute, no duplicate `name` attributes within `<map>`.

| Status | VERIFIED |
|---|---|
| Evidence | All 106 XML files parsed successfully with `xml.etree.ElementTree`. Zero parse failures. Root element is `<map>` in every file. Zero intra-file duplicate keys found. |
| Applicable files | All XML profiles in `profiles/`, top-level `LXX521_*.xml`, and `analysis_results/imx682_config/**/*.xml` |
| Notes | Syntax validation proves only that the XML is structurally valid. It does NOT prove that the camera app recognizes each setting. |

### Level B: Configuration Schema Validation

**Check:** Identification of schema family (LMC vs BSG vs MIXED / UNKNOWN) by marker keys. Distinguishes Level A from B: syntax valid ≠ schema valid.

| Status | OBSERVED |
|---|---|
| Evidence | Schema families identified by key-content markers:
- LMC-style: `pref_qjpg_key`, `frame_count_b_photo_0`, `ptchr_sharpness_0` (48 profiles)
- BSG/MGC-style: `pref_quality_key`, `pref_hdr_plus_frames_key`, `camera_id_back` (2 profiles)
- Mixed: profiles containing markers from both families (6 profiles)
- Unknown: profiles with neither marker set (3 profiles) |
| Applicable files | All XML profiles |
| Notes | Level B identifies the key-family schema; it does NOT prove that the camera app accepts every key. |

### Level C: Camera Application Compatibility

**Check:** Deterministic compatibility statements based on the identified schema family. Never confuses Level C with Level A (syntax) or Level B (schema).

| Status | NOT TESTED IN REPO |
|---|---|
| Evidence | Compatibility statements can be emitted for each schema family (see PROFILE_COMPATIBILITY.md), but these do not prove runtime behavior. No on-device camera testing was performed (per safety scope). |
| Applicable files | All XML profiles |
| Notes | **Never claim device compatibility from XML syntax alone.** This is a mission rule (#7). |

### Level D: Actual Device Validation

**Check:** On-device Camera2 characteristics access via `android.hardware.camera2.CameraManager`. Requires actual device attached running target camera app.

| Status | BLOCKED |
|---|---|
| Evidence | No device attached in this Termux/repo environment. Level D cannot be performed and is reported as BLOCKED, not FAIL. The validation operation itself cannot be completed, not that the profile is invalid. |
| Applicable files | N/A (requires device) |
| Notes | **Mission rules explicitly state:**
- "Never confuse these four validation levels."
- "Never claim device compatibility from XML syntax alone."
- "Do not launch a camera test session."
- "Do not modify firmware, NVRAM, NVDATA, or secure storage." |

The result is BLOCKED, not FAIL — the validation operation itself cannot be completed in this environment.

## 2. Profile Validation Summary

| Profile | Level A (syntax) | Level B (schema) | Level C (compat) | Level D (device) | Overall |
|---|---|---|---|---|---|
| `profiles/LXX521_IMX682_AllInOne_V3.xml` | ✅ PASS | ✅ LMC identified | ✅ Statement emitted | ❌ BLOCKED | — |
| `LXX521_BSG_Master.xml` | ✅ PASS | ⚠️ MIXED identified | ✅ Statement emitted (MIXED risk) | ❌ BLOCKED | — |
| `LXX521_IMX682_Super_AllInOne_V4.xml` | ✅ PASS | ✅ LMC identified | ✅ Statement emitted | ❌ BLOCKED | — |
| `profiles/LXX521_BSG_Pro.xml` | ✅ PASS | ⚠️ MIXED identified | ✅ Statement emitted (MIXED risk) | ❌ BLOCKED | — |
| `profiles/LXX521_IMX682_LMC84_AllRounder.xml` | ✅ PASS | ✅ LMC identified | ✅ Statement emitted | ❌ BLOCKED | — |
| `LXX521_FrontCam_Only_Sanitized.xml` | ✅ PASS | ✅ LMC identified | ✅ Statement emitted | ❌ BLOCKED | — |

**Overall:** All profiles pass Level A (syntax). Level D is BLOCKED for all profiles (no device). Levels B and C produce deterministic reports but do not validate runtime behavior.

## 3. Validation Status Matrix

| Validation Aspect | Status | Confidence |
|---|---|---|
| XML well-formedness | VERIFIED | 100% |
| Root element `<map>` | VERIFIED | 100% |
| Intra-file duplicate keys | VERIFIED | 100% |
| Schema family identification | OBSERVED | 95% (based on key markers) |
| Unsupported key detection | OBSERVED | 90% (based on known key set) |
| Missing critical keys | OBSERVED | 85% |
| Camera app compatibility | NOT TESTED | 0% (no device) |
| Actual device validation | BLOCKED | 0% (no device) |
| Front camera NPE resolution | NOT TESTED | 0% (code-level only) |

## 4. Known Issue Validation

### 4.1 Front Camera NullPointerException

| Check | Result | Evidence |
|---|---|---|
| Code-level NPE in `loadConfinesExposureISO()` | CONFIRMED | Bytecode analysis: `Range.getUpper()` called on null `Range` object, no null guard |
| Config-level fix possible | ❌ NO | `SENSOR_INFO_SENSITIVITY_RANGE` is NULL for front camera; no XML parameter can supply a valid Range |
| Build-level fix required | ✅ YES | Vendor/BSG must add null guard in `loadConfinesExposureISO()` |
| Tested on device | ❌ NO | Per safety scope: no runtime camera session performed |

### 4.2 Hidden Camera ID 2

| Check | Result | Evidence |
|---|---|---|
| Accessible via CameraCharacteristics | ✅ YES | Logcat evidence: `FOUND_LENSES [0 1 2]` |
| Present in `getCameraIdList()` | ❌ NO | Not present; diagnostic target only |

## 5. Summary

- **All profiles pass Level A** (XML syntax validation).
- **Level D is BLOCKED** for all profiles (no device attached). This is correct and expected per mission rules.
- **Levels B and C** produce deterministic reports but do not validate runtime behavior.
- **Front camera NPE** is a code-level issue; no XML profile can fix it. Vendor/BSG code change required.
- **No device validation** has been performed (per safety scope). Claims of device compatibility from XML syntax alone are explicitly prohibited by mission rules.

---

**VALIDATION STATUS.md complete. No existing files were modified during this audit.**