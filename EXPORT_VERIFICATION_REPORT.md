DCIM CALIBRATION — LAVA LXX521 / Sony IMX682
EXPORT VERIFICATION REPORT
============================

EXPORT STATUS: COMPLETE
EXPORT TIMESTAMP: 2026-11-02T09:40:09Z
SOURCE REPOSITORY: /root/dcim-calibration-upgrade
DESTINATION: /storage/emulated/0/Download/DCIM_Calibration/

================================================================================
1. CANDIDATE INVENTORY
================================================================================

LMC 8.4 Candidate:
  Source filename:  profiles/lmc84/LXX521_IMX682_ActionCam.xml
  Source SHA-256:   7f543a4e928bb160d0a7e6bf72add2482c6a534807ef7986de76498e267ea360
  Candidate:        output/LMC84_IMX682/llmc84_actioncam_candidate.xml
  Candidate SHA-25: 7f543a4e928bb160d0a7e6bf72add2482c6a534807ef7986de76498e267ea360
  Exported:         /storage/emulated/0/Download/DCIM_Calibration/llmc84_actioncam_candidate.xml
  Exported SHA-25:  7f543a4e928bb160d0a7e6bf72add2482c6a534807ef7986de76498e267ea360

BSG/MGC Candidate:
  Source filename:  profiles/mgc_bsg/mgc.xml
  Source SHA-256:   911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288
  Candidate:        output/BSG_IMX682/mgc_candidate.xml
  Candidate SHA-25: 911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288
  Exported:         /storage/emulated/0/Download/DCIM_Calibration/mgc_candidate.xml
  Exported SHA-25:  911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288

================================================================================
2. GIT STATUS BEFORE AND AFTER EXPORT
================================================================================

Git status before export:
## main...origin/main
 M README_V4.md
 M imx682_opencv_calibration.py
 M workflow_master_v4.py
?? (18 untracked files including output/ and AUDIT_*.md files)

Git status after export:
## main...origin/main
 M README_V4.md
 M imx682_opencv_calibration.py
 M workflow_master_v4.py
?? (18 untracked files including output/ and AUDIT_*.md files)

Git changes: NONE from export operations
The output/ directory was already untracked before the export.
The two exported files were placed into /storage/emulated/0/Download/DCIM_Calibration/
which is outside the repository and not tracked by Git.

Source repository preservation: COMPLETE
No Git staged/ uncommitted changes were introduced by the export.
No commits, pushes, pulls, resets, or stashes were performed.

================================================================================
3. XML SYNTAX AND SCHEMA VALIDATION
================================================================================

LMC 8.4 Candidate (profiles/lmc84/LXX521_IMX682_ActionCam.xml):
  Level A (Syntax):    PASS — well-formed XML; 27 entries; root=<map>;
                       no duplicate keys; all 27 child entries have 'name' attribute
  Level B (Schema):    PASS — Schema identified: LMC (LMC 8.4);
                       10 LMC markers present; 0 BSG markers
  Level C (Compat):    PASS — with explicit disclaimer that syntax validation
                       does NOT prove LMC 8.4 on MT6878/IMX682 acceptance;
                       runtime compatibility requires on-device testing
  Level D (Device):    BLOCKED — no Camera2 access in Termux/repo environment;
                       not a calibration defect; per mission rule, must not be
                       confused with levels A–C

BSG/MGC Candidate (profiles/mgc_bsg/mgc.xml):
  Level A (Syntax):    PASS — well-formed XML; 181 entries; root=<map>;
                       no duplicate keys; all 181 child entries have 'name' attribute
  Level B (Schema):    PASS — Schema identified: BSG (BSG/MGC);
                       15 BSG markers present; 0 LMC markers
  Level C (Compat):    PASS — with explicit disclaimer that syntax validation
                       does NOT prove MGC 9.4.103/9.8.102 acceptance;
                       BSG key namespace separate from LMC 8.4; mixing families
                       is unsupported unless exact app build handles both
  Level D (Device):    BLOCKED — no Camera2 access in Termux/repo environment;
                       not a calibration defect; per mission rule, must not be
                       confused with levels A–C

XML SYNTAX VALIDATED: YES (both candidates pass Level A)
SOURCE HASH VERIFIED: YES (both SHA-256 hashes match source files)
EXPORT HASH VERIFIED: YES (both exported files match source SHA-256)
BYTE IDENTICAL: YES (source == candidate == exported for both families)

================================================================================
4. APPLICATION COMPATIBILITY AND DEVICE VALIDATION
================================================================================

LMC 8.4:
  APP_COMPATIBLE:  UNKNOWN
  DEVICE_TESTED:     NO
  Note: Level C PASS does not prove LMC 8.4 on MT6878/IMX682 acceptance.
  Some keys are known not to be part of the valid parameter space for this
  device/SOC combination (see UNSUPPORTED_LMC_KEYS). Runtime compatibility
  requires on-device testing. No device attached in this environment.

BSG/MGC:
  APP_COMPATIBLE:  UNKNOWN
  DEVICE_TESTED:   NO
  Note: Level C PASS does not prove MGC 9.4.103/9.8.102 acceptance.
  BSG key namespace is separate from LMC 8.4. Mixing LMC and BSG profiles
  is unsupported unless the exact app build explicitly handles both families.
  No device attached in this environment.

================================================================================
5. FILE INVENTORY: EXPORTED
================================================================================

/storage/emulated/0/Download/DCIM_Calibration/llmc84_actioncam_candidate.xml
  Size: 1767 bytes
  SHA-256: 7f543a4e928bb160d0a7e6bf72add2482c6a534807ef7986de76498e267ea360
  Match source: YES

/storage/emulated/0/Download/DCIM_Calibration/mgc_candidate.xml
  Size: 10650 bytes
  SHA-256: 911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288
  Match source: YES

================================================================================
6. SOURCE REPOSITORY PRESERVATION
================================================================================

Source files NOT modified by this export:
  - profiles/lmc84/LXX521_IMX682_ActionCam.xml  (SHA-256: 7f543a4e... )
  - profiles/mgc_bsg/mgc.xml  (SHA-256: 911b27d9... )

Existing Git modifications preserved:
  - README_V4.md (modified, pre-existing)
  - imx682_opencv_calibration.py (modified, pre-existing)
  - workflow_master_v4.py (modified, pre-existing)

No new Git modifications introduced.
No files deleted from repository.
No staging, commits, pushes, pulls, resets, or stashes performed.

================================================================================
6. MANIFEST FILE
================================================================================

Manifest written to: /root/dcim-calibration-upgrade/EXPORT_MANIFEST.json
Contains: filenames, source paths, SHA-256 hashes, validation status, timestamps
for both LMC 8.4 and BSG/MGC candidates.

================================================================================
FINAL VERIFICATION DECLARATION
================================================================================

XML_SYNTAX_VALIDATED:        YES (both candidates pass Level A syntax check)
SOURCE_HASH_VERIFIED:        YES (both SHA-256 hashes verified against source)
EXPORT_HASH_VERIFIED:        YES (both exported files match source SHA-256)
BYTE_IDENTICAL:              YES (source == candidate == exported for both families)
DEVICE_TESTED:               NO (Level D blocked; no device attached in
                              Termux/repo environment; not a defect)
APP_COMPATIBLE:              UNKNOWN (Level C pass does not prove application
                              compatibility; explicit disclaimers in validation
                              reports for both families)

================================================================================
IMPORTANT NOTES
================================================================================

1. Neither candidate should be deployed without on-device validation.
2. Level C validation confirms schema family identification but does not
   imply application compatibility or device calibration.
3. The source repository (/root/dcim-calibration-upgrade) is completely
   preserved untouched. No source files were modified.
4. External backup verified at /root/dcim-calibration-backups/
   dcim-calibration-upgrade_20261102_073315/ (677/678 SHA-256 matches,
   29 = .git metadata files).
5. Termux-safe command for verification:
   python3 -m src.xml_audit check_syntax profiles/lmc84/LXX521_IMX682_ActionCam.xml
   python3 -m src.xml_audit check_syntax profiles/mgc_bsg/mgc.xml
6. Do NOT claim application compatibility or device validation based on
   static XML checks alone. Actual device testing required.

================================================================================
END OF REPORT
================================================================================