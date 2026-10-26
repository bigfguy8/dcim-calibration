# MGC AllInOne Change Report — LXX521

## 1. What was produced
- `LXX521_MGC_AllInOne_CANDIDATE.xml` — an **unchanged native-state restore
  candidate** (byte-identical to the verified native `mgc.xml`).
- `LXX521_MGC_AllInOne_CANDIDATE.LABEL.md` — explicit label: NOT a tuned
  profile, NOT a crash fix.

## 2. Change set: NONE (intentional)
Per the Phase-F rules, a value is only changed when its accepted range and
meaning are supported by actual evidence. After the full native-config audit
(MGC_Native_Config_Analysis.md), **no defensible change exists** that would
(a) improve a setting, or (b) affect the crashing code path. Therefore the
candidate preserves all 181 native entries verbatim and is labeled as an
unchanged restore — per Rule 7 ("If no defensible tuning change is available,
create an unchanged native-state restore candidate and explicitly label it as
such").

| Aspect | Original value | Candidate value | Evidence | Expected behaviour | Risk |
|---|---|---|---|---|---|
| All 181 keys | native values | identical (byte-for-byte) | SHA-256 equals native; `diff` empty | exact current app state restored | none (no change) |

## 3. Explicit non-changes and why
- **Exposure/ISO/sensitivity confinement:** no key exists to change; changing
  config cannot bypass the `Range.getUpper()` NPE (Rule 6). NOT changed.
- **Rear-camera settings:** preserved unmodified (Rule 5).
- **Noise reduction / sharpening / detail:** not exposed as keys in this MGC
  build; **not invented** (Rule 3). Left absent.
- **`pref_camera_picturesize_front_key` / `_back_key`:** empty in native; no
  accepted enum value is established from local evidence, so **not filled**
  (would be fabrication).
- **HDR/HDR+, AWB/colour, video, image sizes, routing:** carried through
  unchanged so rear-camera behaviour is preserved.

## 4. Label integrity
- The candidate is **NOT** labeled a "new tuned profile" or a "crash fix."
- It is explicitly labeled an **unchanged native-state restore** so it can be
  re-imported as a known-good baseline.

## 5. Rollback
- Rollback = re-import the original native `mgc.xml`
  (SHA-256 `911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288`),
  which is byte-identical to the candidate. No destructive step is needed.
- A backup of the native source is stored at
  `…/20261026_174142/backup/mgc_native_source.xml`.

## 6. Relationship to the crash
- This candidate does **not** resolve the front-camera crash. It is a safe
  configuration baseline only. The crash requires a code-level fix in
  `loadConfinesExposureISO` (see Build Compatibility Report), which no available
  build (9.4.103 / 9.8.102 V0) provides.
