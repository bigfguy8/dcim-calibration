# SOURCE INVENTORY — LAVA LXX521 / IMX682

**Stage:** 1 (read-only audit)
**Date:** 2026-10-31

## 1. Repository File Inventory

Total files tracked in git: **536** (excluding `.git/` directory)

### 1.1 Top-level files (22 files)

| File | Type | Notes |
|---|---|---|
| `workflow_master.py` | Python script | Historical; superseded by v4 |
| `workflow_master_v4.py` | Python script | Authoritative deployer |
| `run_crisp_pipeline.py` | Python script | Crisp pipeline deployer |
| `imx682_opencv_calibration.py` | Python script | OpenCV-based calibration |
| `benchmark_dcim.py` | Python script | Sharpness benchmark |
| `manage_noise_models.py` | Python script | Noise model manager |
| `lxx521_imx682_v8_audit.py` | Python script | V8 XML auditor |
| `v9_camera_audit.py` | Python script | V9 camera audit |
| `workflow_master.py` | Python script | Historical V1 |
| `dcim_calibration_audit.py` | Python script | Calibration audit |
| `adc_capture_helper.py` | Python script | ADB capture helper |
| `create_v5.py` | Python script | Historical generator |
| `create_v6.py` | Python script | Historical generator |
| `create_v7.py` | Python script | Historical generator |
| `make_candidate_c.py` | Python script | Candidate maker |
| `make_candidate_d.py` | Python script | Candidate maker |
| `build_v10_lmc84.py` | Python script | LMC84 builder |
| `patch_dcim.py` | Python script | DCIM patcher |
| `guided_v9_ab_test.py` | Python script | Guided AB test |
| `run_v8_comparison.py` | Python script | V8 comparison |
| `analyze_first3_batches.py` | Python script | Batch analyzer |
| `MGC/20261026_190044/MGC_Front_Camera_Crash_Analysis_v2.md` | Markdown | Front-camera crash analysis |
| `MGC/20261026_195747_BEST/MGC_9_4_103_BEST_Change_Report.md` | Markdown | BEST change report |
| `README_V4.md` | Markdown | V4 deployment guide |

### 1.2 XML profiles (top-level, 14 files)

| File | Schema family | Keys | Notes |
|---|---|---|---|
| `LXX521_FrontCam_Only_Sanitized.xml` | UNKNOWN/MIXED | 19 | Front camera only |
| `LXX521_FrontCam_Sanitized_V2.xml` | UNKNOWN/MIXED | 11 | V2 sanitized |
| `LXX521_FrontCam_Sanitized_V3.xml` | UNKNOWN/MIXED | 17 | V3 sanitized |
| `LXX521_IMX682_ActionCam.xml` | LMC | 27 | Action mode |
| `LXX521_IMX682_AllInOne_Master.xml` | LMC | 26 | All-in-one master |
| `LXX521_IMX682_FastShutter.xml` | LMC | 24 | Fast shutter |
| `LXX521_IMX682_ISO_Boost.xml` | LMC | 22 | ISO boost |
| `LXX521_IMX682_Master_PhotoVideo.xml` | LMC | 24 | Photo/video master |
| `LXX521_IMX682_MaxQuality.xml` | LMC | 29 | Max quality |
| `LXX521_IMX682_PerfectNight.xml` | LMC | 19 | Perfect night |
| `LXX521_IMX682_Super_AllInOne_V4.xml` | LMC | 26 | Super AllInOne V4 |
| `LXX521_IMX682_TunedPro.xml` | LMC | 24 | Tuned pro |
| `LXX521_MasterPortrait.xml` | LMC | 21 | Master portrait |
| `LXX521_UltraSharp_Detail.xml` | LMC | 21 | Ultra sharp detail |

### 1.3 XML profiles (profiles/ directory, 20 files)

| File | Schema family | Keys | Notes |
|---|---|---|---|
| `LXX521_BSG_Master.xml` | MIXED (BSG+LMC overlap) | 12 | BSG master — byte-identical to BSG_Pro |
| `LXX521_BSG_Pro.xml` | MIXED (BSG+LMC overlap) | 12 | BSG Pro — byte-identical to BSG_Master |
| `LXX521_IMX682_AllInOne_V2.xml` | LMC | 26 | AllInOne V2 |
| `LXX521_IMX682_AllInOne_V3.xml` | LMC | 26 | AllInOne V3 — baseline template |
| `LXX521_IMX682_AllRounder_NaturalBalanced.xml` | LMC | 2641 | Large profile (2641 keys) |
| `LXX521_IMX682_HDR_Video_Test.xml` | UNKNOWN/MIXED | 10 | HDR video test |
| `LXX521_IMX682_LMC84_AllRounder.xml` | LMC | 2641 | LMC84 AllRounder |
| `LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml` | LMC | 2641 | V10 baseline — byte-identical to AllRounder |
| `LXX521_IMX682_NightPro.xml` | LMC | 26 | Night profile |
| `LXX521_IMX682_Super_AllInOne_V4.xml` | LMC | 26 | Super AllInOne V4 |
| `LXX521_IMX682_Super_AllInOne_V5_BalancedLowLight.xml` | LMC | 26 | V5 BalancedLowLight |
| `LXX521_IMX682_Super_AllInOne_V6_NaturalDetail.xml` | LMC | 26 | V6 NaturalDetail |
| `LXX521_IMX682_Super_AllInOne_V6_NightIndoor.xml` | LMC | 26 | V6 NightIndoor |
| `LXX521_IMX682_Super_AllInOne_V7_NaturalNight.xml` | LMC | 25 | V7 NaturalNight |
| `LXX521_IMX682_UltimateMaster.xml` | LMC | 25 | UltimateMaster |
| `LXX521_IMX682_V8_FullAllRounder_Q100.xml` | LMC | 2641 | V8 FullAllRounder Q100 |
| `LXX521_IMX682_V8_ProBalanced.xml` | LMC | 26 | V8 ProBalanced |
| `LXX521_IMX682_V9_ConservativeBalanced.xml` | LMC | 2662 | V9 ConservativeBalanced |
| `LXX521_MasterPortrait_Pro.xml` | LMC | 14 | MasterPortrait Pro |

### 1.4 Historical generator scripts (not authoritative)

| File | Role | Status |
|---|---|---|
| `create_v5.py` | V5 profile generator | Superseded |
| `create_v6.py` | V6 profile generator | Superseded |
| `create_v7.py` | V7 profile generator | Superseded |
| `create_allrounder.py` | AllRounder generator | Superseded |
| `make_candidate_c.py` | Candidate C maker | Superseded |
| `make_candidate_d.py` | Candidate D maker | Superseded |

### 1.5 MGC investigation files (separate schema)

| File | Description |
|---|---|
| `MGC/20261026_190044/` | MGC 9.4.103 crash investigation |
| `MGC/20261026_195747_BEST/` | MGC BEST deliverables |
| `MGC/AllInOne_Output_20261026_174142/` | MGC AllInOne candidate output |
| `MGC/shared_MGC_CONFIG_9_4_103/` | Shared MGC 9.4.103 config |

### 1.6 Documentation files

| File | Description |
|---|---|
| `README_V4.md` | V4 deployment guide |
| `lmc_guidelines.md` | LMC 8.4 operational guidelines |
| `noise_model_guide.md` | Noise model guide |
| `capture_procedure.md` | Capture procedure |
| `capture_session_v2.md` | Capture session v2 |
| `recapture_checklist.md` | Recapture checklist |

## 2. Authoritative File Identification

| File | Role | SHA-256 (first 16 hex) | Authority |
|---|---|---|---|
| `profiles/LXX521_IMX682_LMC84_AllRounder.xml` | 2641-key LMC baseline | `f5dde315` | Referenced by `KNOWN` in audit script and `V10_Baseline_UNVALIDATED.status.md` |
| `lxx521_imx682_v8_audit.py` | Best-designed audit tool | `a768050b` | Stdlib-only, Termux-ready, hash-verified |
| `workflow_master_v4.py` | Deployer | — | Needs Termux path fix |
| `MGC/shared_MGC_CONFIG_9_4_103/mgc.xml` | MGC native config | `911b27` | SHA-256 documented in MGC/ MANIFEST.md |
| `profiles/LXX521_IMX682_AllInOne_V3.xml` | Small LMC candidate (26 keys) | — | Authoritative LMC small-profile root |

## 3. Duplicate Inventory (inter-file byte-identical)

| SHA-256 | File count | Files |
|---|---|---|
| `0d8385f495ed7455` | 4 | `profiles/LXX521_BSG_Master.xml`, `profiles/LXX521_BSG_Pro.xml`, `backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_BSG_Master.xml`, `backups/duplicate_xml_quarantine_20261021_011812/root/LXX521_BSG_Pro.xml` |
| `f5dde315f71bb4c2` | 17 | `profiles/LXX521_IMX682_LMC84_AllRounder.xml`, `profiles/LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml`, 15 × `analysis_results/imx682_config/*/default_working_backup.xml` |
| `b80d5fb382386177` | 2 | `profiles/LXX521_IMX682_V9_ConservativeBalanced.xml`, `V10_Backups/V9_Backup_b80d5fb38238.xml` |
| `2118c905a247a553` | 2 | `analysis_results/imx682_config/balanced.xml`, `analysis_results/imx682_config/original_V2_Release_Day.xml` |
| `c7ebaa726920a3ed` | 4 | `analysis_results/imx682_config/hdr_master/LXX521_IMX682_HDR_Master.xml`, `analysis_results/imx682_config/hdr_video/Lava_HDR_Video.xml`, `analysis_results/imx682_config/superportrait_hdr/LXX521_IMX682_SuperPortrait_HDR.xml`, `analysis_results/imx682_config/video_master/LXX521_IMX682_Video_Master_V1.xml` |
| `8ea2da084e666440` | 2 | `analysis_results/imx682_config/lowlight_v3/LXX521_IMX682_LowLight_Shot_V3.xml`, `analysis_results/imx682_config/lowlight_v4/LXX521_IMX682_LowLight_Shot_V4.xml` |
| `241008d54a501064` | 2 | `analysis_results/imx682_config/video/Lava_Videography.xml`, `analysis_results/imx682_config/video_master_v2/LXX521_IMX682_Video_Master_V2.xml` |
| `15eec8037b7cd173` | 2 | `LXX521_IMX682_Super_AllInOne_V4.xml` (top-level), `profiles/LXX521_IMX682_Super_AllInOne_V4.xml` |

## 4. Profile Schema Summary

| Schema Family | File count | Example |
|---|---|---|
| LMC | 48 | `profiles/LXX521_IMX682_AllInOne_V3.xml` |
| MIXED (LMC+BSG) | 6 | `profiles/LXX521_BSG_Master.xml` |
| BSG | 2 | `profiles/LXX521_BSG_Master.xml`, `profiles/LXX521_BSG_Pro.xml` |
| UNKNOWN/MIXED (no markers) | 3 | `LXX521_FrontCam_Only_Sanitized.xml`, `LXX521_FrontCam_Sanitized_V2.xml`, `LXX521_FrontCam_Sanitized_V3.xml` |

## 5. Known Issues (from MGC investigation)

| Issue | Description | Impact |
|---|---|---|
| Front camera NULL sensitivity range | `SENSOR_INFO_SENSITIVITY_RANGE` is NULL for front camera (ID 1); `loadConfinesExposureISO()` calls `Range.getUpper()` without null guard → NPE | Code-level bug; no XML profile can fix this |
| Hidden camera ID 2 | Accessible via direct CameraCharacteristics lookup but NOT in `getCameraIdList()` | Diagnostic target only |
| 17× baseline copies | `LMC84_AllRounder.xml` has 16 identical copies scattered across generator directories | Version control issue; no functional impact |
| V3 ≡ V4 lowlight | `lowlight_v3/…_V3.xml` and `lowlight_v4/…_V4.xml` are byte-identical | Generator issue; no functional impact if unchanged |

---

**Source inventory complete. No existing files were modified during this audit.**