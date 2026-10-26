# LXX521 | BSG MGC 9.4.103 — AllInOne (Native Restore) Candidate
## Change Report

Date: 2026-10-26
Scope: BSG MGC 9.4.103 only (com.android.MGC_9_4_103, versionCode 67635286).
No other MGC build, LMC profile, install, deploy, camera session, or photo was used.

## Files written (all new; original mgc.xml NOT modified)
| Role | Path | SHA-256 |
|---|---|---|
| NEW labeled candidate | `…/9.4.103/LXX521_MGC94103_AllInOne_NativeRestore_CANDIDATE.xml` | `09c41d212425f3a951b3abaf32004062f561149ee9294ec9af418c4c89e03789` |
| SOURCE BACKUP (copy) | `…/9.4.103/backup/mgc_xml_backup_20261026_195816.xml` | `911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288` |
| ORIGINAL (untouched) | `…/9.4.103/mgc.xml` | `911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288` |

## What the candidate is
- A clearly labeled, standalone MGC-native configuration.
- Entry body = the verified native `mgc.xml` (181 entries: 175 string / 2 long /
  2 int / 2 boolean) carried through **unchanged**.
- A descriptive XML comment header was added (label, provenance, routing, and a
  note that the front-camera crash is not config-resolvable). The header is a
  comment only; it adds **no** keys and changes **no** values.
- Front/rear routing preserved: `active_cam_id_front_key=1`,
  `active_cam_id_back_key=0`. Rear-camera settings unmodified.

## What was intentionally NOT done (per rules)
- No keys, parameter values, or calibration measurements were invented.
- No tuning values were changed (no evidence-backed improvement exists for
  this build; the native config exposes no exposure/ISO/sensitivity/confinement,
  noise, or sharpening keys to tune).
- The front-camera `Range.getUpper()` NPE is **not** claimed fixed; this file is
  a known-good native baseline, not proof the front camera works.

## Change set
| Aspect | Original | Candidate | Evidence |
|---|---|---|---|
| 181 config entries | native values | identical | entry tuples match (0 changed) |
| XML comment header | none | added (label only) | by construction |
| Result | source of truth | labeled candidate | SHA-256 above |

## Validation status (static only)
- [PASS] Candidate is well-formed XML; root `<map>`.
- [PASS] 181 entries, type mix 175/2/2/2, 0 duplicate keys.
- [PASS] Candidate entries identical to native (181/181 tuples match, 0 changed).
- [PASS] Native source SHA-256 unchanged (`911b27…`) before and after writing.
- [PASS] Source backed up to `backup/` (copy, original untouched).
- [PASS] No `--` inside the XML comment body (valid comment).
- [NOT TESTED] Runtime: MGC import acceptance, front-camera preview/capture.
  (No config import/deploy or camera session was performed, per scope.)

## Known limitations
- No evidence-backed tuning improvement was possible, so this is a labeled
  native-settings restore candidate, not a new tuned profile.
- The front-camera crash is a code-level defect in
  `loadConfinesExposureISO`; a valid XML alone does not fix it.
- MGC import acceptance of the comment header is not runtime-verified; if the
  importer rejects the header, the entry body is byte-identical to the native
  `mgc.xml`, which can be re-imported as an equivalent baseline.
