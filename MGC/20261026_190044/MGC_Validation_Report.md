# MGC ALL-IN-ONE VALIDATION REPORT — run 20261026_190044

Mode: static only. No camera launched, no photo captured, no import, no
deployment, no LMC configuration touched, no uninstall/data-clear.

## 0. Single most important next step

**With MGC 9.8.102 installed (currently active on-device), open the FRONT
camera in MGC and confirm it stays open (the Range.getUpper/
loadConfinesExposureISO fatal has not been observed in any 9.8.102 capture
but front-activation survival is NOT TESTED). Then use MGC's own
"Save config" to export 9.8.102's native `mgc.xml` to
`/sdcard/Download/MGC_CONFIG/9.8.102/`.** Until that export exists, the
9.8.102 schema stays UNKNOWN and no 9.8.102-specific config profile may be
authored (rule: never fabricate a profile for an unverified schema). The
9.4.103 candidates below remain the only schema-CONFIRMED artifacts.

## 1. Checks performed

| # | Check | Result |
|---|---|---|
| 1 | Native source `/sdcard/Download/MGC_CONFIG/9.4.103/mgc.xml` intact, re-hashed at 19:00 | PASS — `911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288` (unchanged since 17:01) |
| 2 | Pre-operation timestamped backup created BEFORE candidate writes | PASS — `backup/mgc_native_9_4_103.xml` (19:00:44) + hash in `backup/SHA256SUMS_backup.txt` |
| 3 | XML well-formedness (source + both candidates, `xml.etree`) | PASS |
| 4 | Root `<map>`, 181 children; 175 string / 2 long / 2 int / 2 boolean; 0 duplicate keys | PASS |
| 5 | Candidate↔source `cmp` (byte identity) + structured diff | PASS — 0 changes in both candidates (deliberate; see §2) |
| 6 | Key-pool cross-check vs dex string pools (this run): 9.4.103 → 64 literal + 79 family = 143/181; 9.8.102 → 63 + 79 = 142/181 | PASS (raw pools in `evidence/`) |
| 7 | 9.8.102 schema delta: `pref_has_checked_dual_ev_shadow`, `pref_mode_vesperad_option` absent from 9.8.102 pool; `hdr_net_key` present | RECORD — 9.8.102 profile therefore NOT produced |
| 8 | Confinement/ISO-range keys in schema | CONFIRMED ABSENT (0/181) → crash unfixable via config |
| 9 | APK inventory + SHA-256 re-verification | PASS — 3 APKs, duplicate `MGC_9.8.102_V0_MGC (1).apk` = identical hash `b15dc553…` |
| 10 | Crash-log preservation | PASS — latest 9.8.102 capture copied at 19:00:44; earlier 9.8.102 captures confirmed rotated/overwritten on-device (ephemeral), key 17:16:50 excerpts preserved in this report set |
| 11 | Front-camera routing keys vs MGC harness (`TOGGLE_DISTRIBUTION_FRONT_LENSES [1]`) | PASS — `active_cam_id_front_key=1` matches |
| 12 | LMC files untouched | PASS — no LMC path written by this run |
| 13 | Candidate import acceptance by MGC | **NOT TESTED** (user action; deliberately not performed) |
| 14 | Runtime front/rear operation under candidates | **NOT TESTED** (no camera session launched) |
| 15 | 9.8.102 crash-absence claim | Evidence-based only: NOT OBSERVED in 3 captures — classified **LIKELY mitigated**, NOT a confirmed fix |

## 2. Why both 9.4.103 candidates are unchanged native copies

- All 181 values are MGC 9.4.103's own live on-device state (its
  "Save config" output). No MGC image-quality measurement for LXX521
  exists in this project, so any value change would be invented (prohibited).
- Night domain is already in MGC's night-enabled state
  (`pref_camera_back_flashmode_key=ns`, `pref_camera_front_flashmode_key=ns`,
  `auto_ns_key=1`); `pref_mode_vesper_level` value space is undocumented
  locally → SpecialNight carries zero deltas and is labeled as such.
- The `loadConfinesExposureISO` NPE is not addressable by any key in this
  schema (check 8); version choice is the only config-side lever.

## 3. Classification summary

- CONFIRMED: hashes/byte-identity, schema structure, key pools, lens
  routing, sensor sizes, crash signatures per version, 9.8.102 log rotation.
- LIKELY: dynamic-suffix key construction; 9.8.102 crash mitigation.
- UNKNOWN: 9.8.102 native schema; semantics of `ns`/`vesper`/`peaking`/
  `device_key=blueline`/`hwlevel_key`/`ptv_ft_key` values.
- NOT TESTED: MGC import acceptance, runtime front/rear operation on either
  version under the candidate files.

## 4. Reproduction

```
cd "$HOME/dcim_calibration/MGC_AllInOne_Output/20261026_190044"
sha256sum -c SHA256SUMS.txt            # (artifact hashes below)
cmp MGC_9_4_103_AllInOne.xml backup/mgc_native_9_4_103.xml
cmp MGC_9_4_103_SpecialNight.xml MGC_9_4_103_AllInOne.xml
python3 -c "import xml.etree.ElementTree as ET;ET.fromstring(open('MGC_9_4_103_AllInOne.xml',encoding='utf-8').read());print('well-formed')"
```
