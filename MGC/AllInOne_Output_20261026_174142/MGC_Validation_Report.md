# MGC Validation Report — LXX521 (static only; NO camera runtime)

Method: `validate_mgc_candidate.sh` (reproducible) + targeted byte-level checks.
All results below are static. Nothing here proves the app accepts the config at
runtime, and nothing proves the crash is fixed.

## 1. Static checks (all PASS)
| Check | Result | Class |
|---|---|---|
| Candidate file exists | PASS | CONFIRMED |
| Candidate byte-identical to native source (`cmp`) | PASS | CONFIRMED |
| Native source SHA-256 matches expected `911b27…` | PASS | CONFIRMED |
| Candidate SHA-256 equals native (unchanged) | PASS (`911b27…`) | CONFIRMED |
| XML well-formed; root `<map>` | PASS | CONFIRMED |
| Entry count = 181 (175 string / 2 long / 2 int / 2 boolean) | PASS | CONFIRMED |
| Duplicate-key detection | 0 duplicates | CONFIRMED |
| Unknown-key analysis | 0 unknown keys (all are known MGC-native keys of this build) | CONFIRMED |
| No exposure/iso/sensitivity/confinement keys (crash not config-addressable) | PASS | CONFIRMED |
| Front routing key = 1, rear routing key = 0 | PASS | CONFIRMED |
| Spot-checks of preserved rear/HDR values (`hdr_plus_key=on`, `video_resolution=RES_1080P`, `fix_saturation_key_0=1`) | PASS | CONFIRMED |

## 2. Accepted-value validation (where supported)
- Values are strings holding 0/1 flags, floats (gawb/c_shad coefficients),
  resolution enums (`RES_1080P`, `full`, `medium`), FPS enums (`FPS_30`,
  `FPS_AUTO`), flash modes (`ns`), and empty strings. All are internally
  consistent with the 9.4.103 native export.
- **Limitation:** full enum validation (e.g. that `pref_camera_resolution`
  accepts only a known set in 9.4.103) was not possible without the app's
  preference schema; the values are taken verbatim from the app's own native
  export, so they are accepted-by-construction. NOT independently re-validated.

## 3. Source-vs-candidate diff
- `diff native candidate` → **empty** (byte-identical). 0 changed keys,
  0 added, 0 removed.

## 4. Backup integrity
- Native source backed up to `…/20261026_174142/backup/mgc_native_source.xml`.
- Backup SHA-256 equals the native source SHA-256 (`911b27…`). CONFIRMED.
- Prior candidates/reports in `20261026_163754` and `20261026_170524` were
  **not** overwritten (new dir `20261026_174142` used).

## 5. Build-script / validator syntax
- `bash -n validate_mgc_candidate.sh` → clean. CONFIRMED.
- `python3 -m py_compile` on the embedded XML check → clean.
- The validation script is self-contained and re-runnable (exit 0 on all-PASS).

## 6. Relevant bytecode comparison (from crash analysis)
- `com.a.loadConfinesExposureISO()V`: 3 `Range.getUpper()`, 2 `getLower()`,
  3 `check-cast`, 1 `if-nez` in **both** 9.4.103 and 9.8.102. No new null-guard
  in the candidate build. CONFIRMED (static).

## 7. Explicit non-claims (required)
- A **valid/parsing** XML does **not** mean the app accepts the configuration.
- **No** camera runtime test was performed.
- **No** configuration import/deploy was performed.
- The front-camera crash is **NOT** shown to be resolved by any artifact here.
- "Successful parsing" ≠ "MGC accepted the candidate" (NOT TESTED at runtime).

## 8. What remains untested (NOT TESTED)
- MGC accepting the candidate on import.
- Front camera preview/capture behaviour under 9.4.103 or 9.8.102.
- Whether a later BSG build null-guards `loadConfinesExposureISO`.
- Runtime camera metadata (`SENSOR_INFO_SENSITIVITY_RANGE` value).
