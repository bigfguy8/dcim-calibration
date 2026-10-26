# MGC FRONT-CAMERA CRASH ANALYSIS v2 — LAVA LXX521

Run 20261026_190044. Consolidates run-163754 analysis with new 9.8.102
evidence. All findings below cite local captures; nothing here claims runtime
front-camera operation.

## 1. The crash: `Range.getUpper()` NPE in `loadConfinesExposureISO`

Fatal exception (CONFIRMED, multiple independent captures):

```
java.lang.NullPointerException: Attempt to invoke virtual method
  'java.lang.Comparable android.util.Range.getUpper()' on a null object reference
  at com.a.loadConfinesExposureISO(a.java:716)        [MGC 9.4.103]
  at com.a.loadConfinesExposureISO(a.java:654)        [MGC 9.7.047-generation]
```

| Capture (file) | Process | Observed |
|---|---|---|
| `9.4.103/…16-16-12.log` | `com.android.MGC_9_4_103` PID 11912, main, 16:15:59 | Fatal 11 s after launch; app relaunched 16:16:12, rear streaming survived |
| `9.4.103/…16-21-09.log` | same, ActiveCamera + CallbackHndlr, 16:21:08 | Fatal on camera activation; relaunch PID 21117 survived 90 s with **front** stream at 4624×3472 |
| `9.4.103/…17-00-45.log` | same app | same signature present (grep hit) |
| `9.7.047/…16-02-33.log` | `com.ss.android.ugc.aweme` (TikTok) PID 3399 | **Unrelated app, identical null-Range signature** → device-side gap in the front camera's sensitivity Range as consumed by camera-app code |

Mechanism (CONFIRMED by config-format inspection + dex string pool):
- MGC's "confinement" feature loads a per-camera exposure/ISO `Range` and
  dereferences it in `loadConfinesExposureISO`.
- The Range is sourced from camera characteristics / runtime metadata — the
  dex pool contains `SENSOR_INFO_SENSITIVITY_RANGE` and
  `StaticMetadata_iso_range_set` (both versions) — NOT from the config file.
- The 181-key native schema contains **zero** confinement/ISO-range keys
  (pattern `iso|expos|range|confin|clamp|limit` → 0 hits): the crash cannot
  be mitigated through any MGC config file. It is an MGC-build defect
  (missing null guard) interacting with this device's front-camera
  characteristics.

Fix path (out of scope for config work): a patched MGC build with a null
guard/explicit default Range, or a firmware/HAL update reporting the front
sensitivity Range.

## 2. 9.8.102: new findings (this run)

- Captures examined: `…17-16-50.log` (79,583 lines, since **overwritten on
  device by newer 9.8.102 captures** — key excerpts preserved below),
  `…18-58-57.log` (also rotated away), `…19-00-07.log` (backed up at
  `backup/LAVA_…_19-00-07.log`, SHA `d6ce8934…`).
- `17-16-50`: one FATAL on thread `mts-launcher` in PID 29915 at 17:16:46:
  `NPE: invoke interface method 'int leu.e()'` → `hoh.ma03b…` (obfuscated,
  background service thread). **Not** the Range.getUpper signature. After the
  crash the app relaunched (PID 30913, 17:16:50) and re-ran full lens
  enumeration: `FOUND_LENSES [0 1 2]`, `TOGGLE_DISTRIBUTION_FRONT_LENSES [1]`.
- `19-00-07`: app running normally (PID 10554); characteristics probed for
  both rear (4625×3473) and front (4033×3025); **no fatal, no Range NPE**.
- `loadConfinesExposureISO` is present as a method string in BOTH dex pools
  (9.4.103 and 9.8.102) — the code path exists in both; what changed is
  evidently its null-handling on this device.

Status of the crash on 9.8.102: **NOT OBSERVED in any available 9.8.102
capture (LIKELY mitigated/fixed in this build); front-camera activation
survival on 9.8.102 = NOT TESTED** (only enumeration/characteristics
probing appears in the logs — no active front session logged).

## 3. Log-rotation hazard (CONFIRMED this run)

MGC 9.8.102 actively rewrites `/sdcard/Download/MGC_CRASH_LOG/9.8.102/`
captures while installed: the 17:16:50 (79,583-line) and 18:58:57 captures
disappeared between 19:00:30 and 19:00:44, replaced by 19:00:07, then
19:00-xx captures. Timestamped copies under `MGC_AllInOne_Output/*/backup/`
are the durable record; treat `/sdcard` copies as ephemeral.

## 4. Impact on configuration work

- The crash is NOT expressible in the 181-key native schema (no confinement
  key) → no config edit in any version can fix it (CONFIRMED gap).
- Version choice, not config content, is the crash lever: stay on / move to
  a build that null-guards `loadConfinesExposureISO`. Evidence currently
  favours 9.8.102 (crash not observed), subject to an explicit front-camera
  activation test by the user (prohibited for this assistant to launch).
