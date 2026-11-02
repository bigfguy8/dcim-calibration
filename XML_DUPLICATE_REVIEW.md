# R4 DUPLICATE-REMOVAL PROPOSAL: XML Profile Duplicate Review

## 1. Scope

Identify duplicate XML profiles (byte-identical, different paths) in the repository
and produce authoritative-copy recommendations. This proposal does NOT delete or
move any files — it generates a review report for explicit approval before any
action.

## 2. Duplicate groups identified (from live repository audit)

The full repository audit (587 files) found 30 duplicate hash groups. Of these:

### 2.1 Profile/config duplicate groups (16 groups)

These involve actual camera profile XML files or configuration baselines.

| SHA-256 (first 16 hex) | File count | Files | Profile purpose | Recommendation |
|---|---|---|---|---|
| `0d8385f495ed7455` | 4 | `profiles/LXX521_BSG_Master.xml`<br>`profiles/LXX521_BSG_Pro.xml`<br>`backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_BSG_Master.xml`<br>`backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_BSG_Pro.xml` | BSG master/pro — 12-key MIXED profiles; byte-identical despite different names | Keep `profiles/LXX521_BSG_Master.xml` as authoritative; mark `Pro` as duplicate or document purpose difference (none found — content identical) |
| `07141128e51bb4a0` | 2 | `backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_IMX682_UltimateMaster.xml`<br>`profiles/LXX521_IMX682_UltimateMaster.xml` | Ultimate master profile | Remove backup copy; keep profiles/ version as authoritative |
| `085323aff48fe602` | 2 | `backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_IMX682_HDR_Video_Test.xml`<br>`profiles/LXX521_IMX682_HDR_Video_Test.xml` | HDR video test profile | Remove backup copy; keep profiles/ version as authoritative |
| `0d8385f495ed7455` | 4 | (see above) | BSG profiles | (see above) |
| `15eec8037b7cd173` | 2 | `LXX521_IMX682_Super_AllInOne_V4.xml` (root level)<br>`profiles/LXX521_IMX682_Super_AllInOne_V4.xml` | Super AllInOne V4 — 26-key LMC profile | Remove root-level copy; keep `profiles/` version as authoritative (already identified in DUPLICATE_CONFLICT_REPORT.md) |
| `2118c905a247a553` | 2 | `analysis_results/imx682_config/balanced.xml`<br>`analysis_results/imx682_config/original_V2_Release_Day.xml` | V2 release day profile (balanced = original) | Keep `original_V2_Release_Day.xml` as reference; `balanced.xml` is duplicate |
| `241008d54a501064` | 2 | `analysis_results/imx682_config/video/Lava_Videography.xml`<br>`analysis_results/imx682_config/video_master_v2/LXX521_IMX682_Video_Master_V2.xml` | Video master profile | Keep `video_master_v2/` version as it has more specific path; remove `video/` duplicate |
| `642fd418d7c8ecd3` | 2 | `backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_IMX682_AllInOne_V2.xml`<br>`profiles/LXX521_IMX682_AllInOne_V2.xml` | AllInOne V2 profile | Remove backup copy; keep profiles/ version as authoritative |
| `8be6d35dcd137074` | 2 | `backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_IMX682_AllInOne_V3.xml`<br>`profiles/LXX521_IMX682_AllInOne_V3.xml` | AllInOne V3 baseline template | Remove backup copy; keep profiles/ version as authoritative |
| `8ea2da084e666440` | 2 | `analysis_results/imx682_config/lowlight_v3/LXX521_IMX682_LowLight_Shot_V3.xml`<br>`analysis_results/imx682_config/lowlight_v4/LXX521_IMX682_LowLight_Shot_V4.xml` | Low-light profiles — V3 and V4 are byte-identical | Keep `lowlight_v3/` version as (slightly) more specific; document that V4 is identical duplicate |
| `911b27d929072bac` | 12 | MGC/ family: 12 files across MGC/ sub-directories | MGC 9.4.103 candidates (AllInOne, SpecialNight, BEST, native config, backups) | Keep one authoritative copy (recommend `MGC/shared_MGC_CONFIG_9_4_103/mgc.xml` as live config); remove 11 duplicates. Document which variant each represents. |
| `93f45f81ba13ef04` | 2 | `analysis_results/dcim_master/camera_delete_manifest_20261021_131814.txt`<br>`analysis_results/dcim_master/camera_delete_manifest_20261021_131836.txt` | Camera delete manifests | Keep newer manifest (timestamp 131836 > 131814); remove older |
| `b59f8744122b776b` | 2 | `backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_IMX682_NightPro.xml`<br>`profiles/LXX521_IMX682_NightPro.xml` | Night profile | Remove backup copy; keep profiles/ version as authoritative |
| `b80d5fb382386177` | 5 | `V10_Backups/V9_Backup_b80d5fb38238.xml`<br>`V10_Master_Output/run_20261021_124656/V10_Final_Release/V10_Final.xml`<br>`V10_Master_Output/run_20261021_124656/V10_Final_Release/V9_Backup.xml`<br>`backups/LXX521_IMX682_V9_ConservativeBalanced_20261021_114246.xml`<br>`profiles/LXX521_IMX682_V9_ConservativeBalanced.xml` | V9 ConservativeBalanced profile — 5 copies across V10 backup dirs and profiles/ | Keep `profiles/LXX521_IMX682_V9_ConservativeBalanced.xml` as authoritative; remove 4 backup duplicates. The V10_Final.xml copy is a separate release build artifact. |
| `c7ebaa726920a3ed` | 4 | `analysis_results/imx682_config/hdr_master/LXX521_IMX682_HDR_Master.xml`<br>`analysis_results/imx682_config/hdr_video/Lava_HDR_Video.xml`<br>`analysis_results/imx682_config/superportrait_hdr/LXX521_IMX682_SuperPortrait_HDR.xml`<br>`analysis_results/imx682_config/video_master/LXX521_IMX682_Video_Master_V1.xml` | Generator output files (HDR master, HDR video, SuperPortrait HDR, Video master V1) | These are generator output duplicates. Keep the earliest/timestamped version; remove others. Document as generator artifacts, not user profiles. |
| `f4ffd9e0af157feb` | 2 | `backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_MasterPortrait_Pro.xml`<br>`profiles/LXX521_MasterPortrait_Pro.xml` | MasterPortrait Pro profile (14-key LMC) | Remove backup copy; keep profiles/ version as authoritative |
| `f5dde315f71bb4c2` | 22 | 22 files scattered across `analysis_results/imx682_config/*/default_working_backup.xml` and `profiles/LXX521_IMX682_LMC84_AllRounder.xml` / `profiles/LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml` | LMC84 AllRounder baseline (2641 keys) — 22 copies total: 2 in profiles/, 22 in analysis_results/ default_working_backup locations | Keep `profiles/LXX521_IMX682_LMC84_AllRounder.xml` as the **authoritative baseline** (hash `f5dde315f71bb4c28f72ea0b2a5cd3b5385f2e4aeb12b7463416174acb1b5f49`). Remove or `.gitignore` the 21 duplicate copies in `analysis_results/imx682_config/*/`. The V10 baseline copy (`profiles/LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml`) is byte-identical and documented as an unchanged copy — keep as reference. |

### 2.2 Audit-log/CSV duplicate groups (14 groups)

These are analysis/run artifacts (CSVs, markdown logs, SHA256SUMS files) that are
legitimately duplicated across audit run timestamps. They are NOT profile
configuration duplicates.

| SHA-256 | File count | Files | Type |
|---|---|---|---|
| `030aeeb5c21c847d` | 4 | 4 `runtime_verification_matrix.csv` copies | Audit run output |
| `050614008f0c002c` | 4 | 4 `V8_AB_TEST_PLAN.md` copies | AB test plan |
| `2525ce763136e404` | 4 | 4 `xml_key_differences.csv` copies | Comparison output |
| `331530fe4a25db04` | 4 | 4 `input_inventory.csv` copies | Input inventory |
| `48189e042485d980` | 4 | 4 `V10_candidate/NEXT_STEPS.txt` copies | Next steps |
| `4d6714504cc5f531` | 4 | 4 `capture_protocol_bn.md` copies | Capture protocol |
| `53f06b65280ec3a5` | 4 | 4 `statistical_summary.csv` copies | Statistical summary |
| `85a1e70aacbd49bd` | 4 | 4 `matched_pair_manifest.csv` copies | Manifest |
| `a75af2746f560c53` | 4 | 4 `relevant_settings.csv` copies | Settings |
| `b390a25303bd1d77` | 4 | 4 `xml_comparison_notes.md` copies | Comparison notes |
| `c7ebaa726920a3ed` | 4 | (also in profile groups — generator outputs) | (see above) |
| `e9e6a146255e8451` | 2 | 2 `SHA256SUMS.txt` copies | SHA-256SUMS |
| `f99ad11dc76bd1dd` | 4 | 4 `capture_manifest_template.csv` copies | Manifest template |

These 14 groups are NOT included in the removal proposal below, as they are audit
artifacts, not profile configurations.

## 3. Redundant copies summary

| Category | Duplicate groups | Total file instances | Unique profiles | Redundant copies |
|---|---|---|---|---|
| Profile/config duplicates | 16 | 121 | 30 (one per group) | 91 |
| Audit-log/CSV artifacts | 14 | N/A (not profiles) | N/A | N/A |

## 4. Authoritative-copy recommendations

### 4.1 Keep as authoritative (do not remove)

1. `profiles/LXX521_IMX682_LMC84_AllRounder.xml` — LMC 8.4 baseline (2641 keys), hash `f5dde315f71bb4c28f72ea0b2a5cd3b5385f2e4aeb12b7463416174acb1b5f49`
2. `profiles/LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml` — V10 baseline, byte-identical to AllRounder, documented unchanged copy
3. `profiles/LXX521_IMX682_AllInOne_V3.xml` — Small LMC baseline template (26 keys)
4. `profiles/LXX521_BSG_Master.xml` — BSG master profile (12-key MIXED), authoritative for BSG family
5. `profiles/LXX521_IMX682_AllInOne_V2.xml` — AllInOne V2, unique content
6. `profiles/LXX521_IMX682_AllInOne_V3.xml` — AllInOne V3, unique content
7. `profiles/LXX521_IMX682_NightPro.xml` — Night profile, unique content
8. `profiles/LXX521_IMX682_Super_AllInOne_V4.xml` — Super AllInOne V4, keep profiles/ version (remove root-level duplicate)
9. `MGC/shared_MGC_CONFIG_9_4_103/mgc.xml` — MGC live native config (SHA-256 `911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288`)

### 4.2 Remove (delete or .gitignore)

1. 21 of 22 `default_working_backup.xml` copies in `analysis_results/imx682_config/*/` (keep one reference if needed)
2. Root-level `LXX521_IMX682_Super_AllInOne_V4.xml` (keep `profiles/` version)
3. 14 of 15 `default_working_backup.xml` copies referenced in DUPLICATE_CONFLICT_REPORT.md (keep one)
4. `V10_Backups/V9_Backup_b80d5fb38238.xml` (keep `profiles/LXX521_IMX682_V9_ConservativeBalanced.xml`)
5. Root-level `LXX521_BSG_Pro.xml` (keep `profiles/LXX521_BSG_Master.xml`; document that Pro is duplicate)
6. 3 of 4 backup copies in `backups/duplicate_xml_quarantine_20261021_011812/root/` for BSG Master/Pro/HDR_Video_Test/UltimateMaster/MasterPortrait_Pro/AllInOne_V2/AllInOne_V3/NightPro
7. 11 of 12 MGC/ family duplicate files (keep one authoritative copy per purpose)
8. `analysis_results/imx682_config/balanced.xml` (keep `original_V2_Release_Day.xml` as reference)
9. `analysis_results/imx682_config/lowlight_v4/LXX521_IMX682_LowLight_Shot_V4.xml` (keep `lowlight_v3/` version; V4 is byte-identical duplicate)
10. `analysis_results/imx682_config/video/Lava_Videography.xml` (keep `video_master_v2/` version)
11. `analysis_results/dcim_master/camera_delete_manifest_20261021_131814.txt` (keep newer 131836 version)

### 4.3 Relocate (move to sub-directories per R3 plan)

1. `profiles/LXX521_BSG_Master.xml` → `profiles/mgc_bsg/`
2. `profiles/LXX521_BSG_Pro.xml` → `profiles/mgc_bsg/`
3. `profiles/LXX521_IMX682_HDR_Video_Test.xml` → `profiles/mgc_bsg/`
4. `LXX521_FrontCam_Only_Sanitized.xml` → `profiles/frontcam/`
5. `LXX521_FrontCam_Sanitized_V2.xml` → `profiles/frontcam/`
6. `LXX521_FrontCam_Sanitized_V3.xml` → `profiles/frontcam/`

## 5. Backup and rollback plan

### Before any removal

1. **Create full backup**: Use the existing backup mechanism — `tar czf /tmp/opencode/backup/dcim-calibration-upgrade_backup_$(date +%Y%m%d%H%M%S).tgz --exclude='.git' .` (the backup already created at `/tmp/opencode/backup/`)
2. **Record SHA-256 hashes**: Document the SHA-256 of every file slated for removal before deletion
3. **Store hash manifest**: Save to `/tmp/opencode/backup/duplicate_removal_hashes_$(date +%Y%m%d%H%M%S).txt`

### Rollback procedure

1. **If removal causes issues**: Restore from the backup archive
   ```sh
   tar xzf /tmp/opencode/backup/dcim-calibration-upgrade_backup_*.tgz
   ```
2. **Individual file restoration**: Copy from the backup directory
   ```sh
   cp backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_BSG_Master.xml profiles/
   ```
3. **Verification**: Run `python run.py audit` after restoration to confirm all profiles validate

### Per-file backup before removal

For each file slated for removal, create a backup:
```sh
cp SOURCE_PATH backups/duplicate_removal_$(basename SOURCE_PATH).bak_$(date +%Y%m%d%H%M%S)
```

## 6. Approval required

This proposal does NOT delete or move any files. It presents a review report for
explicit approval before any action is taken.

**Required approvals:**

1. **Schema family separation (R3 migration plan)** — Approve the directory
   restructuring plan (STAGE3_MIGRATION_PLAN.md) before moving any profiles.

2. **Duplicate removal (R4)** — Approve the authoritative-copy recommendations
   above before deleting or `.gitignore`-ing any files.

3. **Combined R3 + R4** — If both are approved, the combined operation should:
   a. First execute R3 (profile directory restructuring)
   b. Then execute R4 (duplicate removal on the restructured set)
   c. Update all script references (PROFILE_DIRS, glob patterns, etc.)
   d. Run the full test suite (`python run.py audit`, `python run.py compare`, etc.)
   e. Verify no broken references remain

---
**R4 duplicate-removal proposal complete. No files have been deleted or moved.**
 awaiting explicit approval before execution.