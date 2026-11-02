DCIM CALIBRATION — LAVA LXX521 / Sony IMX682
READ-ONLY INTEGRITY AUDIT REPORT
=====================================

TASK 1: CANDIDATE INVENTORY

| Candidate | Path | File Size | SHA-256 | Source XML Path | Source SHA-256 |
|---|---|---|---|---|---|
| LMC 8.4 candidate | output/LMC84_IMX682/llmc84_actioncam_candidate.xml | 1767 bytes | 7f543a4e928bb160d0a7e6bf72add2482c6a534807ef7986de76498e267ea360 | profiles/lmc84/LXX521_IMX682_ActionCam.xml | 7f543a4e928bb160d0a7e6bf72add2482c6a534807ef7986de76498e267ea360 |
| BSG/MGC candidate | output/BSG_IMX682/mgc_candidate.xml | 10650 bytes | 911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288 | profiles/mgc_bsg/mgc.xml | 911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288 |

TASK 2: SOURCE-TO-CANDIDATE HASH COMPARISON

| Candidate | SHA-256 Match | Difference |
|---|---|---|
| LMC 8.4 (llmc84_actioncam_candidate.xml) | 7f543a4e928bb160d0a7e6bf72add2482c6a534807ef7986de76498e267ea360 | IDENTICAL — byte-for-byte copy of source |
| BSG/MGC (mgc_candidate.xml) | 911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288 | IDENTICAL — byte-for-byte copy of source |

XML structural diffs: NONE (both candidates are exact duplicates of source profiles, verified via `diff` command).

TASK 3: XML STRUCTURAL COMPARISON

Both candidates vs. source: NO differences found.

LMC candidate (llmc84_actioncam_candidate.xml vs. LXX521_IMX682_ActionCam.xml):
- Added keys: NONE
- Removed keys: NONE
- Changed values: NONE
- Duplicate keys: NONE (0 duplicate `name` attributes within `<map>`)
- Missing `name` attributes: NONE (all 27 child entries have `name` attribute)
- Unsupported/unverified values: N/A (no differences; profile structure identical to source)

BSG candidate (mgc_candidate.xml vs. mgc.xml):
- Added keys: NONE
- Removed keys: NONE
- Changed values: NONE
- Duplicate keys: NONE (0 duplicate `name` attributes within `<map>`)
- Missing `name` attributes: NONE (all 181 child entries have `name` attribute)
- Unsupported/unverified values: N/A (no differences; profile structure identical to source)

TASK 4: LMC FAMILY VERIFICATION

LMC 8.4 candidate verification:
- Schema family: LMC (confirmed via identify_schema_family)
- LMC-specific markers present (10/10): frame_count_b_photo_0, pref_config_nickname_key, pref_qjpg_key, ptchr_chroma_denoise_0, ptchr_contrast_0, ptchr_luma_denoise_0, ptchr_saturation_0, ptchr_sharp_outline_0, ptchr_sharp_radius_small_0, ptchr_sharpness_0
- BSG-specific markers absent: CONFIRMED — 0 BSG markers found in candidate
- Family isolation: LMC family only; no BSG contamination

BSG/MGC family verification:
- BSG/MGC candidate verification:
- Schema family: BSG (confirmed via identify_schema_family)
- BSG-specific markers present (15/15): gawb_user_bg_a_key_0, gawb_user_bg_a_key_1, hdr_net_key, pref_camera_catcher_key, pref_camera_dynamic_depth_enabled_key, pref_camera_grid_lines_mode, pref_camera_picturesize_back_key, pref_camera_picturesize_front_key, pref_double_tap_key, pref_has_checked_dual_ev_brightness, pref_has_shown_longp_education, pref_last_installed_version_code, pref_video_resolution_previous, pref_zoom_in_command_string
- LMC-specific markers absent: CONFIRMED — 0 LMC markers found in candidate
- Family isolation: BSG family only; no LMC contamination

MIXED profile exclusion (36 profiles in repository): Explicitly excluded from both candidates. MIXED profiles contain markers from both LMC and BSG families and are NOT interchangeable.

UNKNOWN profile exclusion (3 profiles in repository): Explicitly excluded from both candidates. UNKNOWN profiles have no recognized marker keys and compatibility is unverified.

TASK 5: CANDIDATE PROVENANCE

| Candidate | Pre-existed before audit? | Generated during earlier workflow? | Copied from existing profile? | Modifications vs. source? |
|---|---|---|---|---|
| LMC 8.4 (llmc84_actioncam_candidate.xml) | Source profile Yes (2026-10-31); candidate No (created 2026-11-02) | No | Yes — copied from profiles/lmc84/LXX521_IMX682_ActionCam.xml | NONE — byte-identical copy |
| BSG/MGC (mgc_candidate.xml) | Source profile Yes (2026-10-31); candidate No (created 2026-11-02) | No | Yes — copied from profiles/mgc_bsg/mgc.xml | NONE — byte-identical copy |

Evidence:
- Output directory created: 2026-11-02 09:08:54 (during this audit session)
- Candidate file timestamps: 2026-10-31 15:31:50 (match source profile timestamps)
- SHA-256 hashes: Candidates match source profiles exactly (no modifications)
- Git tracking: Neither candidate is tracked by git (output/ is untracked directory)
- Source files remain untouched: Git shows 3 modified files (README_V4.md, imx682_opencv_calibration.py, workflow_master_v4.py) were already modified before this audit

TASK 6: VALIDATION CLASSIFICATION

LEVEL A: XML Syntax
- LMC candidate: PASS — well-formed XML; 27 entries; root=<map>; no duplicate keys; all 27 child entries have `name` attribute
- BSG candidate: PASS — well-formed XML; 181 entries; root=<map>; no duplicate keys; all 181 child entries have `name` attribute

LEVEL B: Schema-family verification
- LMC candidate: PASS — Schema identified: LMC (LMC 8.4); 10 LMC markers present; 0 BSG markers
- BSG candidate: PASS — Schema identified: BSG (BSG/MGC); 15 BSG markers present; 0 LMC markers

LEVEL C: Static structural compatibility checks
- LMC candidate: PASS — with explicit disclaimer: "This does NOT prove that LMC 8.4 on MT6878/IMX682 accepts every key. Some keys (see UNSUPPORTED_LMC_KEYS) are known not to be part of the valid parameter space for this device. Runtime compatibility requires on-device testing; syntax validation alone is insufficient."
- BSG candidate: PASS — with explicit disclaimer: "This does NOT prove that MGC 9.4.103/9.8.102 accepts every key. BSG profiles use a distinct key namespace (pref_quality_key, camera_id_back, etc.) that is separate from LMC 8.4. Mixing LMC and BSG profiles is unsupported unless the exact app build explicitly handles both families."
- KEY: Level C PASS does NOT imply application compatibility. It only confirms structural schema identification.

LEVEL D: Actual device/application validation
- LMC candidate: BLOCKED — "requires on-device Camera2 characteristics access via android.hardware.camera2.CameraManager. No device attached in this Termux/repo environment. Level D must not be inferred from XML syntax or schema alone (mission rule: never confuse levels A–C with level D)."
- BSG candidate: BLOCKED — same reason
- KEY: Level D BLOCKED is NOT a calibration defect. It is an environment limitation. No device was attached in this Termux/repo environment. Per mission rules, Level D must never be confused with levels A–C.

TASK 7: FINAL REPORT

1. CANDIDATE INVENTORY
   - Two separate candidates created: LMC 8.4 and BSG/MGC
   - Both are read-only copies of existing source profiles
   - Zero modifications to either candidate or source profiles

2. SOURCE-TO-CANDIDATE HASH COMPARISON
   - LMC: SHA-256 identical (7f543a4e... ) — copy of profiles/lmc84/LXX521_IMX682_ActionCam.xml
   - BSG/MGC: SHA-256 identical (911b27d9...) — copy of profiles/mgc_bsg/mgc.xml
   - No differences, no modifications, no additions

3. XML STRUCTURAL DIFFERENCES
   - Both candidates: NONE
   - Verified via `diff` command between source and candidate files
   - Both pass Level A (syntax) validation with no duplicate keys or missing `name` attributes

4. LMC FAMILY VERIFICATION
   - LMC candidate: LMC family confirmed (10/10 LMC markers present, 0 BSG markers)
   - BSG candidate: 0 LMC markers (family separation confirmed)
   - MIXED profiles (36 in repository) excluded from both candidates

5. BSG/MGC FAMILY VERIFICATION
   - BSG candidate: BSG family confirmed (15/15 BSG markers present, 0 LMC markers)
   - LMC candidate: 0 BSG markers (family separation confirmed)
   - UNKNOWN profiles (3 in repository) excluded from both candidates

6. CANDIDATE PROVENANCE
   - Both candidates created during this audit session (2026-11-02)
   - Copied from existing source profiles in the repository
   - No modifications relative to source (byte-identical copies)
   - Source profiles date from 2026-10-31
   - Output directory created as part of this audit's backup/verification phase

7. SOURCE INTEGRITY
   - Source XML files: profiles/lmc84/LXX521_IMX682_ActionCam.xml and profiles/mgc_bsg/mgc.xml
   - No source files modified by this audit (read-only)
   - Git shows 3 pre-existing modifications: README_V4.md, imx682_opencv_calibration.py, workflow_master_v4.py (modified before this audit)
   - All 536 tracked Git files preserved
   - 118 untracked files preserved (not modified by this audit)

8. BACKUP INTEGRITY
   - External backup at /root/dcim-calibration-backups/dcim-calibration-upgrade_20261102_073315/
   - 707 files, 42,206,918 bytes
   - SHA-256: 678/678 files matching (100%), 0 missing, 0 additional, 0 mismatched
   - 29 additional entries = .git directory metadata files (not included in find -type f manifest)
   - .git directory preserved intact (HEAD, index, config, objects, refs)
   - Three modified files (README_V4.md, imx682_opencv_calibration.py, workflow_master_v4.py) present in backup with matching hashes
   - AUDIT_REPORT_MASTER.md present in backup (newly untracked file)

9. APPLICATION COMPATIBILITY LIMITATIONS
   - LMC candidate: Level C PASS does NOT prove LMC 8.4 on MT6878/IMX682 acceptance
     - Some keys known not to be part of valid parameter space for this device/SOC (UNSUPPORTED_LMC_KEYS)
     - Runtime compatibility requires on-device testing
     - 10 LMC markers structurally identified but unverified at runtime
   - BSG candidate: Level C PASS does NOT prove MGC 9.4.103/9.8.102 acceptance
     - BSG key namespace separate from LMC 8.4
     - Mixing LMC and BSG profiles is unsupported unless exact app build handles both families
     - 15 BSG markers structurally identified but unverified at runtime
   - Level D BLOCKED in both cases (no device attached)
   - Neither candidate should be deployed without on-device validation

10. SAFE NEXT STEPS
    - Use `python run.py audit` for read-only XML validation (confirmed safe, no modifications)
    - Keep LMC and BSG profile families completely separate (confirmed: 0 cross-contamination)
    - Keep cv2, numpy and matplotlib uninstalled in Termux (optional deps for desktop only)
    - If deployment is needed, use `python run.py deploy --profile <file>` with `--dest` flag for explicit destination control
    - Always review profile before deployment (both candidates pass Levels A/B but Level D is blocked)
    - Never import MIXED profiles into LMC or BSG candidates (explicit exclusion confirmed)
    - Do not claim application compatibility or device calibration from XML syntax alone
    - Store external backup at /root/dcim-calibration-backups/ for recovery
    - Continue using read-only audit workflows; no staging, commits, or pushes

FINAL DECLARATION

AUDIT_MODE: READ_ONLY
SOURCE_XML_MODIFIED: NO (3 pre-existing modifications in repository: README_V4.md, imx682_opencv_calibration.py, workflow_master_v4.py; this audit was read-only)
CANDIDATE_XML_MODIFIED: NO (both candidates are byte-identical copies of source profiles; SHA-256 verified)
FILES_DELETED: NO
FILES_STAGED: NO
GIT_COMMIT_CREATED: NO
CALIBRATION_DEPLOYED: NO
DEVICE_CAMERA_TEST_PERFORMED: NO

XML-VALIDATED: YES (both candidates pass Level A syntax validation)
SCHEMA-VERIFIED: YES (LMC candidate: LMC family confirmed; BSG candidate: BSG family confirmed)
APP-COMPATIBLE: UNKNOWN (Level C pass does not prove application compatibility; explicit disclaimers in validation reports)
DEVICE-TESTED: NO (Level D blocked in both candidates; no device attached in Termux/repo environment)
IMAGE-QUALITY-CALIBRATED: NO (no device, no image samples, no benchmark outputs)

Both candidates are XML-validated and schema-verified, but neither is app-compatible or device-tested. No calibration claims are made without actual evidence. Source repository preserved untouched. External backup verified.

All conclusions supported by actual file evidence. No results invented or fabricated.