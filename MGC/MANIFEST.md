# MGC 9.4.103 AllInOne — Recovery Addendum (LXX521)

Added: 2026-10-26 (commit "Add MGC 9.4.103 AllInOne deliverables").
This addendum extends the DCIM Calibration recovery snapshot with the BSG MGC
9.4.103 front-camera investigation and the MGC AllInOne candidate work.

## Contents
### MGC/AllInOne_Output_20261026_174142/
Source: `$HOME/dcim_calibration/MGC_AllInOne_Output/20261026_174142/`
- `LXX521_MGC_AllInOne_CANDIDATE.xml` — unchanged native-state restore candidate
  (SHA-256 `911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288`,
  byte-identical to the verified native `mgc.xml`). Labeled: NOT a tuned
  profile, NOT a crash fix.
- `LXX521_MGC_AllInOne_CANDIDATE.LABEL.md` — label manifest for the candidate.
- 7 reports: `MGC_Device_and_APK_Audit.md`, `MGC_Front_Camera_Crash_Analysis.md`,
  `MGC_Build_Compatibility_Report.md`, `MGC_Native_Config_Analysis.md`,
  `MGC_AllInOne_Change_Report.md`, `MGC_Validation_Report.md`,
  `INVENTORY.txt` (Phase-A inventory).
- `SHA256SUMS.txt` — hashes of the deliverable files (as of creation).
- `validate_mgc_candidate.sh` — reproducible static validator (all checks PASS
  at creation; re-runnable).
- `backup/mgc_native_source.xml` — copy of the native config (integrity backup).
- `evidence/` — crash logs (9.4.103 / 9.7.047 / 9.8.102), dex method dumps
  (`94103_method.txt`, `98102_method.txt`, `*_stream.txt`), `mgc_entries.txt`,
  `SOURCE_HASHES.txt`, aapt badging + dumpsys attempt records.

### MGC/20261026_190044/
Source: `$HOME/dcim_calibration/MGC_AllInOne_Output/20261026_190044/`
- `MGC_9_4_103_AllInOne.xml`, `MGC_9_4_103_SpecialNight.xml` — both
  byte-identical to native (`911b27…c288`); 0 deltas.
- `MGC_Front_Camera_Crash_Analysis_v2.md`, `MGC_Validation_Report.md`,
  `MGC_Version_Compatibility_Matrix.md`, `SHA256SUMS.txt`.
- `backup/` — native config copy, `19-00-07` log window (0 FATAL, no MGC
  markers), backup sums.
- `evidence/` — dex string pools (`pool_94103.txt`, `pool_98102.txt`), `keys.txt`.

### MGC/20261026_195747_BEST/
Source: `$HOME/dcim_calibration/MGC_AllInOne_Output/20261026_195747_BEST/`
- `MGC_9_4_103_BEST_AllInOne.xml` and `MGC_9_4_103_BEST_Night.xml` —
  byte-identical to each other (SHA-256 `b3705a…6ae1fc6226`); exactly ONE
  delta vs native over 181 keys: `pref_camera_resolution` `medium` → `full`.
  NOT verified to fix the front-camera crash; no runtime test performed.
- `MGC_9_4_103_BEST_Change_Report.md`, `SHA256SUMS.txt`, `backup/`.

### MGC/shared_MGC_CONFIG_9_4_103/
Source: `$HOME/storage/shared/Download/MGC_CONFIG/9.4.103/` (mirrors the MGC
config folder in Downloads; 8 XMLs total)
- `mgc.xml` — verified native MGC config (SHA-256 `911b27…c288`).
- `LXX521_MGC94103_AllInOne_NativeRestore_CANDIDATE.xml` — labeled standalone
  candidate (native entries + XML comment label header; SHA-256
  `09c41d212425f3a951b3abaf32004062f561149ee9294ec9af418c4c89e03789`).
- `LXX521_MGC94103_AllInOne_CHANGE_REPORT.md` — change report.
- `LXX521_MGC_AllInOne_CANDIDATE_20261026_{170524,174142}.xml` — native-identical.
- `MGC_9_4_103_{AllInOne,SpecialNight}_20261026_190044.xml` — native-identical.
- `MGC_9_4_103_BEST_{AllInOne,Night}_20261026_195747.xml` — BEST copies
  (`pref_camera_resolution` `medium`→`full`); not a crash fix.
- `CONFIG_FILES_INDEX.txt` — inventory of the folder with hashes and labels.
- `backup/mgc_xml_backup_20261026_195816.xml` — pre-modification backup copy.

## Evidence notes (runtime)
- 9.4.103 crash confirmed: NPE `android.util.Range.getUpper()` in
  `com.a.loadConfinesExposureISO` (front camera, logical id 1, sensor 4624x3472).
- 9.8.102 V0: static bytecode shows the SAME unguarded Range.getUpper()
  structure (no new null guard); runtime shows a different earlier failure
  ("unsupported device" notice) and zero `Range.getUpper` NPEs in the
  19:11-19:51 window (log `evidence/9.8.102/…19-11-36.log`, 0 FATAL).
- 9.4.103 `…19-12-03.log` and 9.8.102 `…19-11-36.log` are later capture
  windows with 0 FATAL exceptions; absence of a crash in a window is NOT
  proof the front camera works.
- No camera capture, install, or config import was performed by this project.

## Scope reminder
- This repo stores text/config/report artifacts only (see `_RECOVERY/`);
  it cannot restore the complete original project or media data.
- The front-camera crash remains unresolved at the code level; a valid XML
  alone does not fix it.
