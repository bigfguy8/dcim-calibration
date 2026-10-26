# MGC Build Compatibility Report — 9.4.103 (current) vs 9.8.102 V0 (candidate)

Method: static comparison of the two **local** APKs (dex bytecode + native libs +
manifests) plus the **runtime** logcat each build produced on this device.
No install was performed by this project; no large download was made (both APKs
were already present locally).

## 1. Release / source notes
- Candidate `MGC 9.8.102 V0` was already downloaded locally
  (`MGC_9.8.102_V0_MGC.apk`, SHA-256 `b15dc553…`). The exact upstream release
  page (`celsoazevedo.com/…/dl404/`) was **not** fetched/verified here; the
  classification below rests on the local artifact, which is authoritative for
  what is actually installed. (Fetching the release page is optional and out of
  the safe-local scope.)
- Package `com.android.MGC_9_8_102` is **distinct** from
  `com.android.MGC_9_4_103`, so the two coexist safely (verified by
  `pm list packages`). No uninstall of the current build is required.

## 2. Classification of the candidate
Required rubric: A = plausible fix, B = same apparent defect, C = inconclusive,
D = cannot inspect.

**Overall classification: B — the candidate contains the same apparent defect
(the unguarded `Range.getUpper()`), and additionally fails earlier with a
different NPE. It is NOT a confirmed fix for the front-camera crash.**

Sub-finding detail:
- **Inspectability (not D):** both APKs are local and fully inspectable.
- **Crash-method bytecode (B):** `com.a.loadConfinesExposureISO()V` exists in
  **both** builds with an **identical** guard structure — 3 `Range.getUpper()`,
  2 `Range.getLower()`, 3 `check-cast`, 1 `if-nez`, 0 `if-eqz`/`instance-of`.
  No null-check was added in 9.8.102. A `check-cast` does not null-check, so the
  latent NPE remains. → same apparent defect.
- **Runtime (B, with a twist):** on-device, 9.8.102 crashes *before* reaching the
  front-camera confinement path — NPE on `leu.e()` (interface) in the
  `mts-launcher` thread plus `Cannot start the Google Camera App on an unsupported
  device`. So it does not "fix" the front camera; it introduces a different,
  earlier failure on this device.
- **Native/ABI (neutral):** arm64-v8a in both; 9.8.102 adds ARCore +
  segmentation libs, drops halide/rampatcher. No ABI-level null-guard implication.

## 3. Why "newer version" ≠ "fix" (explicit non-claim)
A higher version number (9.8.102 > 9.4.103) does **not** by itself prove the
front-camera crash is fixed. The bytecode shows the specific unguarded
`Range.getUpper()` call survives in 9.8.102, and the runtime log shows 9.8.102
fails in a *different* way. Therefore **no build promotion is recommended on the
basis of version alone.**

## 4. Evidence table
| Evidence | 9.4.103 | 9.8.102 | Class |
|---|---|---|---|
| `com.a.loadConfinesExposureISO` present | yes | yes | B (same defect) |
| New null-guard added to that method | — | no (counts identical) | B |
| `Range.getUpper()` NPE reproduced in log | yes | no (in ~2-min window) | NOT a fix-proof |
| Other earlier failure | — | NPE `leu.e()` + "unsupported device" | B / new issue |
| ABI | arm64-v8a | arm64-v8a | neutral |
| Safe coexistence (distinct pkg) | yes | yes | CONFIRMED |

## 5. Residual UNKNOWN / NOT TESTED
- UNKNOWN: whether a *later* 9.8.x/9.9 build adds the null-guard (not locally
  available; not fetched).
- NOT TESTED: runtime front-camera preview under 9.8.102; whether the
  "unsupported device" block is device-specific or config-dependent.
- NOT TESTED: importing any config into 9.8.102 (version stamp is
  9.4.103-era, see Device & APK Audit §4).

## 6. Bottom line
- The 9.8.102 V0 candidate is **inspected** (not D).
- Its crash-handling implementation for `loadConfinesExposureISO` **does not
  differ** in a way that adds null protection (B).
- It is therefore **not** a defensible resolution of the front-camera crash.
- The correct path to a working front camera is a build in which
  `loadConfinesExposureISO` null-guards the `Range` (or the front sensor exposes
  a valid sensitivity range); that must come from the BSG vendor or a patched
  APK. No such patched APK is currently in evidence.
