# MGC Front-Camera Crash Analysis — LAVA LXX521

## 1. The exception (CONFIRMED, from local logcat)
```
java.lang.NullPointerException:
  Attempt to invoke virtual method
  'java.lang.Comparable android.util.Range.getUpper()'
  on a null object reference
    at com.a.loadConfinesExposureISO(a.java:716)   # 9.4.103
    at qbh.SetVALUES(...)
    at ndv.<init>(...)
    ...
```
- Observed on threads `main`, `ActiveCamera`, and `CallbackHndlr` (9.4.103 logs
  `16-16-12` and `16-21-09`). The method dereferences `Range.getUpper()` on a
  **null** `android.util.Range` while loading exposure/ISO confining bounds.
- Root-cause class: the front camera's sensitivity/exposure-ISO confinement
  `Range` is **null** at activation time (no valid
  `SENSOR_INFO_SENSITIVITY_RANGE`/confinement value is available for the front
  lens on this device), and `loadConfinesExposureISO()` performs the virtual call
  without a null guard.

## 2. Per-build crash signatures (CONFIRMED patterns)
| Build | Exception | Method / line | Thread | Class |
|---|---|---|---|---|
| 9.4.103 | NPE `Range.getUpper()` | `com.a.loadConfinesExposureISO(a.java:716)` | main / ActiveCamera / CallbackHndlr | CONFIRMED crash |
| 9.7.047 | NPE `Range.getUpper()` | `com.a.loadConfinesExposureISO(a.java:654)` | main | CONFIRMED (same defect, different line ⇒ code moved) |
| 9.8.102 | NPE `interface leu.e()` on null | `hoh.ma03b067...` | mts-launcher | CONFIRMED *different, earlier* failure |

Note: the 9.7.047 log's foreground process was `com.ss.android.ugc.aweme`; the
MGC crash signature (`com.a.loadConfinesExposureISO → Range.getUpper()`) is the
decisive part and matches the 9.4.x pattern. The differing line numbers
(716 vs 654) confirm the method body changed between generations but the defect
(class `com.a`, unguarded `Range.getUpper`) persisted.

## 3. Static bytecode comparison of the crashing method (CONFIRMED)
Using `apkanalyzer dex code --class com.a --method loadConfinesExposureISO()V`:

| Metric | 9.4.103 | 9.8.102 |
|---|---|---|
| `Range.getUpper()` calls | 3 | 3 |
| `Range.getLower()` calls | 2 | 2 |
| `check-cast v1, Landroid/util/Range;` | 3 | 3 |
| `if-nez` null guards in method | 1 | 1 |
| `if-eqz` / `instance-of` | 0 / 0 | 0 / 0 |

**Interpretation:** 9.8.102 did **NOT** add a null-check around the
`Range.getUpper()` dereferences; the guard count is identical to 9.4.103.
A plain `check-cast` does **not** null-check (a null passes the cast), so the
unguarded `invoke-virtual {v1} Range.getUpper()` on a possibly-null `v1`
remains a latent NPE in both builds. → The candidate is **not** a
null-handling fix (see Build Compatibility Report, classification B).

## 4. Why the config cannot fix it (CONFIRMED)
- The native MGC configuration (181 entries) contains **no** key matching
  `exposure|iso|sensitive|sensitivity|confin|ae_`.
- Therefore no supported configuration control influences the
  `loadConfinesExposureISO` code path. The crash is **code-level**, not
  configuration-level. (Rule: config must not be used to bypass an internal
  Java exception unless a supported control demonstrably affects that path —
  none exists here.)

## 5. Runtime evidence for 9.8.102 (CONFIRMED observations, NOT a fix)
- 9.8.102 fails **earlier** with a different NPE (`leu.e()` on the
  `mts-launcher` thread) and logs `Cannot start the Google Camera App on an
  unsupported device`.
- Within the captured ~2-minute window it enumerated lenses (`[0 1 2]`),
  configured the front RAW sensor (4624×3472) and YUV (1440×1080 / 4096×3072)
  pipelines, and exited **without** reproducing the `Range.getUpper()` NPE —
  but it also never demonstrated a stable front-camera preview (see §6).
- Conclusion: absence of the specific NPE in a short window is **not** proof
  the front camera works; the build instead hits a different failure.

## 6. Explicit untested items (NOT TESTED)
- Whether 9.4.103 or 9.8.102 ever shows a working **front-camera preview**
  (no runtime capture performed, per safety scope).
- Whether the 9.8.102 "unsupported device" path is a hard block or recoverable.
- The exact `SENSOR_INFO_SENSITIVITY_RANGE` value the front sensor reports
  (metadata not readable without root / `dumpsys`).
- Whether importing the unchanged candidate config changes crash behaviour
  (no config import/deploy was performed).

## 7. Defensible resolution path (recommended next steps, out of scope here)
1. Confirm with the BSG vendor whether a 9.8.x / later build adds a null-guard
   to `loadConfinesExposureISO` (current 9.8.102 V0 does **not**, per §3).
2. If a guard is added in a newer build, that is the code-level fix; until then
   the front camera remains unreliable on this device.
3. The unchanged candidate config (Phase F) is a safe baseline restore only —
   it does **not** resolve the crash.
