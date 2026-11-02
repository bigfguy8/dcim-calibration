# DUPLICATE CONFLICT REPORT — LAVA LXX521 / Sony IMX682

**Stage:** 1 (read-only audit)
**Date:** 2026-10-31

## 1. Duplicate Files (byte-identical, different paths)

| SHA-256 (first 16 hex) | File count | Files | Status |
|---|---|---|---|
| `0d8385f495ed7455` | 4 | `profiles/LXX521_BSG_Master.xml`<br>`profiles/LXX521_BSG_Pro.xml`<br>`backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_BSG_Master.xml`<br>`backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_BSG_Pro.xml` | BSG_Master and BSG_Pro are **byte-identical** but have different names. Both quarantined in `backups/duplicate_xml_quarantine_20261021_011812/root/`. |
| `f5dde315f71bb4c2` | 17 | `profiles/LXX521_IMX682_LMC84_AllRounder.xml`<br>`profiles/LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml`<br>15 × `analysis_results/imx682_config/*/default_working_backup.xml` | 17 copies of the **same 2641-key LMC baseline**. The V10 file is a documented unchanged copy (status.md confirms "Tuning changes: none; exact source copy"). |
| `b80d5fb382386177` | 2 | `profiles/LXX521_IMX682_V9_ConservativeBalanced.xml`<br>`V10_Backups/V9_Backup_b80d5fb38238.xml` | V9 backup is a copy of the live V9 profile. |
| `2118c905a247a553` | 2 | `analysis_results/imx682_config/balanced.xml`<br>`analysis_results/imx682_config/original_V2_Release_Day.xml` | V2 original and "balanced" are **byte-identical**. |
| `c7ebaa726920a3ed` | 4 | `analysis_results/imx682_config/hdr_master/LXX521_IMX682_HDR_Master.xml`<br>`analysis_results/imx682_config/hdr_video/Lava_HDR_Video.xml`<br>`analysis_results/imx682_config/superportrait_hdr/LXX521_IMX682_SuperPortrait_HDR.xml`<br>`analysis_results/imx682_config/video_master/LXX521_IMX682_Video_Master_V1.xml` | 4 generator runs produced **identical byte output**. |
| `8ea2da084e666440` | 2 | `analysis_results/imx682_config/lowlight_v3/LXX521_IMX682_LowLight_Shot_V3.xml`<br>`analysis_results/imx682_config/lowlight_v4/LXX521_IMX682_LowLight_Shot_V4.xml` | V3 and V4 lowlight profiles are **byte-identical**. |
| `241008d54a501064` | 2 | `analysis_results/imx682_config/video/Lava_Videography.xml`<br>`analysis_results/imx682_config/video_master_v2/LXX521_IMX682_Video_Master_V2.xml` | Same video profile in two directories. |
| `15eec8037b7cd173` | 2 | `LXX521_IMX682_Super_AllInOne_V4.xml` (root level)<br>`profiles/LXX521_IMX682_Super_AllInOne_V4.xml` | Top-level copy is a **duplicate** of the profiles/ version. |

## 2. Conflict Files (same path type, different content)

| Conflict | Files | Difference |
|---|---|---|
| **BSG key overlap** | `profiles/LXX521_BSG_Master.xml` vs `profiles/LXX521_BSG_Pro.xml` | **Content is identical** despite different names. Both have MIXED schema (some LMC markers + BSG markers). |
| **Top-level vs profiles/** | `LXX521_IMX682_Super_AllInOne_V4.xml` | Root-level copy is identical to `profiles/LXX521_IMX682_Super_AllInOne_V4.xml`. |
| **Schema family mismatch** | Any LMC profile vs any BSG profile | LMC keys (e.g. `pref_qjpg_key`) are ignored by BSG apps; BSG keys (e.g. `pref_quality_key`) are ignored by LMC apps. Mixing causes key conflicts. |

## 3. Redundant/Unnecessary Files

| File | Reason | Recommendation |
|---|---|---|
| 15 × `default_working_backup.xml` in `analysis_results/imx682_config/*/` | All byte-identical to `LMC84_AllRounder.xml` / `V10_Baseline_UNVALIDATED.xml` | Keep one reference; delete duplicates or move to `.gitignore`. |
| `LXX521_IMX682_Super_AllInOne_V4.xml` at repo root | Duplicate of `profiles/LXX521_IMX682_Super_AllInOne_V4.xml` | Remove root-level copy; keep profiles/ version as authoritative. |
| `V10_Backups/V9_Backup_b80d5fb38238.xml` | Duplicate of `profiles/LXX521_IMX682_V9_ConservativeBalanced.xml` | Either keep both (different directories) or remove one. |
| Top-level `LXX521_*.xml` files (14 files) | Many are superseded by `profiles/` versions; some have no corresponding `profiles/` entry | Assess whether top-level copies contain unique content; if not, remove or move to `.gitignore`. |

## 3. Schema Family Conflicts

| Conflict | Description | Risk |
|---|---|---|
| LMC + BSG mixing | Profiles with both LMC and BSG marker keys | App may ignore keys from one family; in some configurations, crash. |
| Super_AllInOne_V4 in both locations | Duplicate file, same content | No additional risk; just confusion about which is authoritative. |
| FrontCam_Sanitized_V2/V3 (UNKNOWN/MIXED) | No LMC/BSG markers detected | Compatibility with any app is unverified; treat as experimental. |

## 4. Recommended Actions

### 4.1 Remove redundant duplicates

1. **Keep** `profiles/LXX521_IMX682_LMC84_AllRounder.xml` as the canonical LMC baseline.
2. **Delete** or `.gitignore` 14 of the 15 `default_working_backup.xml` copies (keep one for reference).
3. **Remove** the root-level `LXX521_IMX682_Super_AllInOne_V4.xml` (keep `profiles/` version).
4. **Decide** on `V10_Backups/V9_Backup_b80d5fb38238.xml` vs `profiles/LXX521_IMX682_V9_ConservativeBalanced.xml` — keep one, remove the other.
5. **Assess** the 14 top-level `LXX521_*.xml` files — if they have no unique content not in `profiles/`, move to `.gitignore`.

### 4.2 Separate schema families

1. **Move** `profiles/LXX521_BSG_Master.xml` and `profiles/LXX521_BSG_Pro.xml` into a `profiles/mgc_bsg/` sub-directory.
2. **Move** the 3 front-camera files into `profiles/frontcam/`.
3. **Update** `workflow_master_v4.py` `PROFILE_DIRS` to point to the new sub-directories.

### 4.3 Document the baseline

1. **Record** `profiles/LXX521_IMX682_LMC84_AllRounder.xml` (hash `f5dde3…`) as the authoritative baseline.
2. **Reference** `profiles/LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml` as the V10 copy (byte-identical, documented).
3. **Update** `V10_Baseline_UNVALIDATED.status.md` to remain the status file for the baseline.

### 4.4 Front camera NPE

1. **Document** that no XML profile can fix the front camera NullPointerException.
2. **Note** that the root cause is a NULL `SENSOR_INFO_SENSITIVITY_RANGE` for the front camera, requiring a vendor/BSG code fix.
3. **Do not** claim that any profile "enables" or "fixes" the front camera.

---

**Duplicate conflict report complete. No existing files were modified during this audit.**

## 5. Reconciliation note (Stage 2 — evidence reconciliation)

The original report identified 8 duplicate hash groups and 107 duplicate file instances.
A full repository audit (STAGE 2 evidence reconciliation) discovered the following
corrected figures:

- **30 duplicate hash groups** (not 8): 13 groups with 2 files, 14 groups with 4 files,
  1 group with 5 files, 1 group with 12 files (MGC/ family), 1 group with 22 files
  (default_working_backup baseline).
- **121 total file instances** across 30 groups (not 107): 26 + 56 + 5 + 12 + 22 = 121.
- **91 redundant copies** (instances − unique groups = 121 − 30).
- **16 profile/config duplicate groups** involve actual camera profile XML files or
  configuration baselines (BSG profiles, AllRounder baseline copies, Super_AllInOne_V4,
  V9 backup, NightPro, MasterPortrait_Pro, default_working_backup, MGC/ family).
- **14 duplicate groups** involve audit-log/CSV artifacts (runtime verification matrices,
  AB_TEST_PLAN markdowns, CSV summaries, SHA256SUMS, etc.) that are legitimately
  duplicated across audit run timestamps and are NOT profile configuration duplicates.

The arithmetic in the original report (18+8+1+1+1 = 29 groups, 107 file instances) was
affected by a counting error — the group counts summed to 29 not 30, and the file
instance calculation was based on the incorrect group counts. The live audit corrected
both the group count (30) and the file instance total (121).

All other findings in the original report (individual hash groups, file lists, conflict
types, recommended actions) remain valid and are cross-referenced in the
STAGE2_EVIDENCE_RECONCILIATION.md and the XML_DUPLICATE_REVIEW.md.