# REPOSITORY AUDIT REPORT — LAVA LXX521 / Sony IMX682

**Stage:** 1 (read-only audit)
**Date:** 2026-10-31
**Auditor:** Senior Android Computational Photography Engineer

## 1. Repository Snapshot

| Item | Value |
|---|---|
| Repository | `https://github.com/bigfguy8/dcim-calibration.git` |
| Clone | `/root/dcim-calibration-upgrade` |
| HEAD | `82dbae9` — "Add GitHub Actions workflow for Python application" |
| Branch | `main` (single branch, no tags) |
| Total tracked files | 536 (plus 574 total inventory including sub-files) |
| Repository size | 37 MB |
| Python files | 22 (all compile OK with `py_compile`) |
| XML files | ~70+ (top-level + profiles/ + analysis_results/) |
| `README.md` | **Missing** (only `README_V4.md` at root) |
| `requirements.txt` | **Not present** |
| Test files | **None** (CI runs `pytest` but no test directory exists) |

## 2. Directory Structure (actual)

The repository contains the following major components:

- `.github/workflows/python-app.yml` — CI: flake8 + pytest
- `README_V4.md` — Deployment guide (V4 reference)
- `lmc_guidelines.md` — LMC 8.4 in-app settings guide
- `noise_model_guide.md` — Noise model placement guide
- `capture_procedure.md`, `capture_session_v2.md`, `recapture_checklist.md` — Historical capture guides
- `MGC/` — BSG MGC 9.4.103 investigation (separate schema family)
- `V10_Backups/`, `V10_Master_Output/` — V10 release artifacts
- `analysis_results/` — Large; many sub-directories with generated profiles, test results, and reports
- `profiles/` — Authoritative LMC candidate set (19 files)
- Top-level `LXX521_*.xml` profiles (×14 files)
- Python scripts (22 top-level scripts)
- `backups/` — Quarantined duplicates and timestamped backups
- `dcim_master_termux.sh`, `dcim_v10_allinone.sh` — Shell wrappers

## 3. XML Engineering Findings

### 3.1 Well-formedness
All XML files parsed successfully with `xml.etree.ElementTree`. **Zero parse failures.** Every profile has root element `<map>`.

### 3.2 Duplicate key detection
No XML file contains duplicate `name` attributes within its own `<map>` element. **Zero intra-file duplicate keys.**

### 3.3 Schema families (confirmed by key content)

| Family | Marker keys found | Files |
|---|---|---|
| **LMC-style** (LMC 8.4) | `pref_qjpg_key`, `frame_count_b_photo_0`, `ptchr_sharpness_0` | All profiles in `profiles/` (except BSG_* and HDR_Video_Test) |
| **BSG/MGC-style** | `pref_quality_key`, `pref_hdr_plus_frames_key`, `camera_id_back` | `profiles/LXX521_BSG_Master.xml`, `profiles/LXX521_BSG_Pro.xml`, `MGC/` sub-trees, `profiles/LXX521_IMX682_HDR_Video_Test.xml` |
| **Mixed / no-marker** | Neither LMC nor BSG markers found | `LXX521_FrontCam_Sanitized_V2.xml`, `LXX521_FrontCam_Sanitized_V3.xml`, `LXX521_FrontCam_Only_Sanitized.xml` |

### 3.4 Inter-file duplicate and conflict map

| Hash (SHA-256, first 16 hex) | Files | Status |
|---|---|---|
| `0d8385f495ed7455` | `profiles/LXX521_BSG_Master.xml` = `profiles/LXX521_BSG_Pro.xml` = quarantined `backups/…/root/` | **BSG_Pro is byte-identical to BSG_Master** — name differs, content identical |
| `f5dde315f71bb4c2` | `profiles/LXX521_IMX682_LMC84_AllRounder.xml` = `profiles/LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml` = 15 × `analysis_results/imx682_config/*/default_working_backup.xml` | **17 copies of the same 2641-key baseline** |
| `b80d5fb382386177` | `profiles/LXX521_IMX682_V9_ConservativeBalanced.xml` = `V10_Backups/V9_Backup_b80d5fb38238.xml` | V9 backup is a copy of the live V9 profile |
| `2118c905a247a553` | `analysis_results/imx682_config/balanced.xml` = `analysis_results/imx682_config/original_V2_Release_Day.xml` | **V2 original and "balanced" are byte-identical** |
| `c7ebaa726920a3ed` | 4 generated files in `analysis_results/imx682_config/` (HDR_Master, HDR_Video, SuperPortrait_HDR, Video_Master_V1) | **4 distinct generator runs produced identical byte output** |
| `8ea2da084e666440` | `lowlight_v3/LXX521_IMX682_LowLight_Shot_V3.xml` = `lowlight_v4/…_V4.xml` | V3 and V4 lowlight profiles are identical |
| `241008d54a501064` | `video/Lava_Videography.xml` = `video_master_v2/LXX521_IMX682_Video_Master_V2.xml` | Same output in two directories |
| `15eec8037b7cd173` | Top-level `LXX521_IMX682_Super_AllInOne_V4.xml` = `profiles/LXX521_IMX682_Super_AllInOne_V4.xml` | Top-level copy is a duplicate |

### 3.5 AllInOne family value deltas (against AllInOne_V3 baseline)

All six small LMC profiles (11–26 keys each) are derived from the same AllInOne_V3 26-key structure:

| Profile | Keys changed vs V3 |
|---|---|
| `Super_AllInOne_V4` | 5 keys (nickname, chroma_denoise, saturation, sharp_outline, sharpness) |
| `V5_BalancedLowLight` | 7 keys |
| `V6_NaturalDetail` | 7 keys |
| `V6_NightIndoor` | 6 keys |
| `V7_NaturalNight` | 7 keys |

These are **single-digit parameter mutations** of a common template — not independently designed profiles.

### 3.6 Validation levels (strictly separated)

| Level | Status |
|---|---|
| **A. XML syntax** (well-formed, root `<map>`) | VERIFIED — all profiles pass |
| **B. Configuration schema** (LMC vs BSG family) | OBSERVED (by key-content markers) |
| **C. Camera app compatibility** (does LMC 8.4 / MGC accept these keys?) | NOT TESTED in this repo |
| **D. Actual device validation** (image quality improvement) | NOT TESTED — no benchmark image data in repo |

## 4. Python Pipeline Audit

### 4.1 Dependency inventory (stdlib-only scripts)

| Script | stdlib only | External deps | Termux-safe? |
|---|---|---|---|
| `lxx521_imx682_v8_audit.py` | ✅ | none | ✅ |
| `benchmark_dcim.py` | ✅ | numpy (graceful) | ✅ |
| `manage_noise_models.py` | ✅ | none | ✅ |
| `workflow_master_v4.py` | ✅ | none | ✅ |
| `dcim_calibration_audit.py` | ✅ | none | ✅ |
| `v9_camera_audit.py` | ✅ | none | ✅ |
| `run_v8_comparison.py` | ✅ | none | ✅ |
| `guided_v9_ab_test.py` | ✅ | none | ✅ |
| `build_v10_lmc84.py` | ✅ | none | ✅ |
| `imx682_opencv_calibration.py` | ✅ | **cv2, numpy, matplotlib, PIL** | ⚠️ heavy — not Termux-safe as-is |
| `analyze_first3_batches.py` | ✅ | **numpy, PIL** | ⚠️ |
| `run_crisp_pipeline.py` | ✅ | subprocess, shutil | ✅ |
| `patch_dcim.py` | ✅ | none | ✅ |
| `create_v5/v6/v7.py` | ✅ | none | ✅ |
| `make_candidate_c/d.py` | ✅ | none | ✅ |
| `adb_capture_helper.py` | ✅ | none | ✅ |
| `workflow_master.py` | ✅ | none | ✅ |

### 4.2 Key design observations

- **`workflow_master_v4.py`** (authoritative deployer): Default destination is hardcoded to `/sdcard/LMC8.4/` (line 12). The prompt's recommended Termux shared storage path `~/storage/shared/Download/DCIM_Calibration/` is **not used**. The script will fail on a real Termux environment without that path being edited.
- **`imx682_opencv_calibration.py`**: Imports `cv2` and `matplotlib` unconditionally at module top. In Termux these libraries are either unavailable or very slow; there is no try/except guard. The script will `ImportError` immediately on most Termux installs.
- **`lxx521_imx682_v8_audit.py`**: Best-designed script in the repo. Has `KNOWN` hash references, reads from `~/dcim_calibration` (Termux home), uses `expanduser()`, has explicit safety gates for candidate creation. This is the most robust audit tool and the foundation for the new `src/xml_audit.py`.
- **No test directory, no `requirements.txt`, no `src/`, no `run.py`** — the proposed architecture (section 14) does not yet exist.
- **`dcim_master_termux.sh`, `dcim_v10_allinone.sh`, `dcim_v10_allinone_v2_1.sh`** — shell wrappers; content not yet inspected.
- **`prepare_chatgpt_project.sh`** — likely a packaging script; content not yet inspected.

### 4.3 Missing / not yet inspected

- `workflow_master.py` (v1) — historical, superseded by v4
- `run_crisp_pipeline.py` — needs full inspection
- `create_v5.py`, `create_v6.py`, `create_v7.py` — historical generators
- `build_v10_lmc84.py` — needs inspection
- `dcim_calibration_audit.py` — needs inspection
- Shell scripts: `dcim_master_termux.sh`, `dcim_v10_allinone.sh`, `dcim_v10_allinone_v2_1.sh`, `prepare_chatgpt_project.sh`, `MGC/…/validate_mgc_candidate.sh`

## 5. MGC (BSG) Isolation

The `MGC/` directory tree contains:
- BSG MGC 9.4.103 candidate XMLs (native restore, AllInOne, SpecialNight, BEST variants)
- Crash analysis reports (front-camera NPE on `CONTROL_POST_RAW_SENSITIVITY_BOOST_RANGE`)
- Evidence: logcat files, aapt dumpsys output, dex string pools, SHA256SUMS.txt
- **Decision: MGC work is separate from LMC work.** The `profiles/LXX521_BSG_*.xml` files use MGC/BSG key names and must not be mixed with LMC `ptchr_*` / `pref_qjpg_key` profiles.

## 6. Authoritative File Identification (STAGE 2 input)

| File | Role | Authority |
|---|---|---|
| `profiles/LXX521_IMX682_LMC84_AllRounder.xml` | 2641-key LMC baseline | **AUTHORITATIVE BASELINE** (hash `f5dde3…`, referenced by `KNOWN` in audit script and by `V10_Baseline_UNVALIDATED.status.md`) |
| `lxx521_imx682_v8_audit.py` | Best-designed audit tool | **AUTHORITATIVE AUDIT TOOL** (stdlib-only, Termux-ready, hash-verified) |
| `workflow_master_v4.py` | Deployer | Authoritative but needs Termux path fix (`/sdcard/LMC8.4` → `~/storage/shared/Download/DCIM_Calibration/`) |
| `README_V4.md` | Deployment guide | Authoritative reference; notes `source_profiles/` dir that does not exist |
| `profiles/LXX521_IMX682_AllInOne_V3.xml` | Small LMC candidate | Authoritative LMC small-profile family root (26 keys) |
| `MGC/shared_MGC_CONFIG_9_4_103/mgc.xml` | MGC live config | AUTHORITATIVE MGC native config (SHA-256 `911b27…`) |
| `lmc_guidelines.md`, `noise_model_guide.md` | In-app usage | Observed; operational, not validated |
| `create_v5/v6/v7.py`, `make_candidate_c/d.py` | Historical generators | **NOT authoritative** — superseded; output files now live in `profiles/` and `analysis_results/imx682_config/` |
| `workflow_master.py` (v1) | Historical deployer | **Superseded** by v4 |

## 7. Conflict & Duplication Summary (DUPLICATE_CONFLICT_REPORT input)

**Duplicates (identical bytes, different paths):**
1. `LXX521_BSG_Master.xml` ≡ `LXX521_BSG_Pro.xml` — same content, two names, both in `profiles/`
2. `LXX521_IMX682_LMC84_AllRounder.xml` ≡ `LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml` — the V10 file is a documented unchanged copy
3. 15 × `default_working_backup.xml` files in `analysis_results/imx682_config/*/` — all byte-identical to the AllRounder baseline
4. `LXX521_IMX682_Super_AllInOne_V4.xml` exists both at root level and in `profiles/`
5. `V10_Backups/V9_Backup_b80d5fb38238.xml` ≡ `profiles/LXX521_IMX682_V9_ConservativeBalanced.xml`
6. `analysis_results/imx682_config/balanced.xml` ≡ `analysis_results/imx682_config/original_V2_Release_Day.xml`
7. 4 generated files in `analysis_results/imx682_config/` share hash `c7ebaa72…` (HDR_Master, HDR_Video, SuperPortrait_HDR, Video_Master_V1)
8. LowLight V3 ≡ LowLight V4 (byte-identical)
9. `video/Lava_Videography.xml` ≡ `video_master_v2/LXX521_IMX682_Video_Master_V2.xml`

**Conflicts:**
- BSG files in `profiles/` mixed with LMC files — schema families not separated in the `profiles/` directory
- Top-level LMC XMLs duplicate `profiles/` XMLs (Super_AllInOne_V4 appears in both locations)
- `lmc_guidelines.md` references `LXX521_UltimateSpeedCrisp.xml` which does not exist in the repo
- `README_V4.md` references a `source_profiles/` directory that does not exist in the repo

**Missing:**
- No `README.md` at root
- No `requirements.txt`
- No `tests/` directory
- No `src/` module structure
- No `run.py`
- No `docs/` directory
- No `reports/` directory

## 8. Validation Status Table

| Item | Status |
|---|---|
| All XML files well-formed | VERIFIED (all parsed, zero errors) |
| Root element `<map>` in all profiles | VERIFIED |
| Zero intra-file duplicate keys | VERIFIED |
| LMC vs BSG schema families identified | OBSERVED (by key-content markers) |
| LMC app accepts these specific keys | NOT TESTED in this repo |
| MGC 9.4.103 native config hash match | VERIFIED in MGC/ sub-directory (SHA-256 documented) |
| Image quality improvement of any profile | NOT TESTED — no benchmark image data in repo |
| Termux runtime of `workflow_master_v4.py` | NOT TESTED — path hardcode to `/sdcard/LMC8.4/` will fail on Termux without edit |
| `imx682_opencv_calibration.py` on Termux | NOT TESTED — hard `import cv2` / `matplotlib` at top; will `ImportError` on most Termux installs |
| CI `pytest` step | BLOCKED — no test files exist; `pytest` will find nothing and pass vacuously |
| CI `flake8` step | NOT TESTED locally; CI configured for Python 3.10 |

## 9. STAGE 3 — Upgrade Plan (proposed, not yet implemented)

### R1 — Termux-safe deployer path fix
- **File:** `workflow_master_v4.py`, line 12
- **Change:** Replace `Path("/sdcard/LMC8.4")` with a configurable path. Accept an optional `--dest` CLI argument; default to `Path.home() / "storage/shared/Download/DCIM_Calibration"` for Termux. Keep the old `/sdcard/LMC8.4` as a fallback if `~/storage/shared` does not exist.
- **Risk:** Low. Deployment target changes; user must confirm actual app config path on-device.
- **Benefit:** Makes deployer actually work on the target device without manual edit.

### R2 — Guard OpenCV import in `imx682_opencv_calibration.py`
- **File:** `imx682_opencv_calibration.py`
- **Change:** Wrap `import cv2`, `import numpy`, `import matplotlib` in `try/except ImportError`; emit a clear warning and skip the dependent functions.
- **Risk:** Low. No behavior change if libraries are available.
- **Benefit:** Script loads and runs the non-OpenCV portions on Termux.

### R3 — Separate `profiles/` into schema sub-directories
- **Change** (directory moves only, no content changes):
  - `profiles/lmc84/` → all LMC-key profiles
  - `profiles/mgc_bsg/` → `LXX521_BSG_Master.xml`, `LXX521_BSG_Pro.xml`, `LXX521_IMX682_HDR_Video_Test.xml`
  - `profiles/frontcam/` → the 3 front-camera files
- **Risk:** Medium — breaks any existing script that globs `profiles/*.xml` flat. Must update `workflow_master_v4.py` `PROFILE_DIRS` and `collect_profiles()`.
- **Benefit:** Eliminates schema-mixing confusion; makes BSG vs LMC vs front-camera separation explicit.

### R4 — Remove top-level XML duplicates
- **Change:** Move the 14 top-level `LXX521_*.xml` files into `profiles/lmc84/` (or `profiles/` if not separating). The `profiles/LXX521_IMX682_Super_AllInOne_V4.xml` already exists; delete the root-level copy after verifying hash match.
- **Risk:** Low. No unique content lost.
- **Benefit:** Single source of truth; no confusion about which copy is authoritative.

### R5 — Create `src/xml_audit.py` (refactored from `lxx521_imx682_v8_audit.py`)
- Extract the parse, hash, compare, and report functions into a reusable module.
- Add `--check-duplicates` flag that scans all `profiles/**/*.xml` and `analysis_results/**/*.xml` for inter-file byte-identical duplicates and prints a report.
- Add a `KNOWN_BASELINE` dict (from existing `KNOWN` in v8_audit script) for hash verification.
- **Risk:** Low — new file; existing script unchanged.
- **Benefit:** Reusable audit core for regression tests and future profiles.

### R6 — Create `tests/` directory with regression tests
- `test_xml_parse.py` — well-formedness of every XML in `profiles/` and top-level
- `test_duplicate_keys.py` — no intra-file duplicate `name` attributes
- `test_hash_integrity.py` — verify `f5dde3…` baseline hash is stable
- `test_profile_compare.py` — synthetic: compare two small profiles and verify changed-key detection
- `test_workflow_master_v4.py` — mock deploy with `tmp_path` fixture; verify backup created; verify SHA-256 of destination
- `test_invalid_xml.py` — feed malformed XML; verify error is raised not silently passed
- All tests use only `pytest` and stdlib; no network, no camera, no image files required.
- **Risk:** Low.
- **Benefit:** CI `pytest` step will now actually run meaningful checks.

### R7 — Add `requirements.txt`
```
# Termux-safe core
# (all scripts in src/ use stdlib only)
# Optional heavy analysis (desktop only, not needed on device):
# opencv-python
# numpy
# matplotlib
# Pillow
```
- **Risk:** None.
- **Benefit:** Makes dependency intent explicit; CI can optionally install heavy deps.

### R8 — Add `docs/VALIDATION_STATUS.md`
- Records the four validation levels (A/B/C/D) as a living document.
- Marks each profile with its current validation level.

### R9 — Add `run.py`
- Thin CLI: `python run.py audit` → calls `src/xml_audit.py`; `python run.py deploy` → calls deployer; `python run.py compare` → calls comparison tool.
- No dependencies beyond `src/` module.

### R10 — Fix `README_V4.md` inaccuracies
- `source_profiles/` dir does not exist; either remove the reference or create the directory.
- `LXX521_UltimateSpeedCrisp.xml` referenced in `lmc_guidelines.md` does not exist; mark as legacy/removed.

## 10. Risks & Expected Benefits Summary

| Risk | Likelihood | Mitigation |
|---|---|---|
| Moving files into sub-dirs breaks `workflow_master_v4.py` | Medium | Update `PROFILE_DIRS` in same change; run test suite |
| `imx682_opencv_calibration.py` guard hides a real import error | Low | Print warning, not exception; functions still error if called |
| Hash-verified baseline accidentally overwritten | Low | Test suite asserts hash stability; `lxx521_imx682_v8_audit.py` candidate gate already prevents this |
| MGC profiles accidentally mixed into LMC set | Medium | Schema sub-directory separation (R3) makes mixing structurally impossible |
| Termux destination path still wrong even after R1 | Medium | `--dest` override flag; user must confirm on-device before running deploy |

## 11. Evidence Artifacts

- Hash snapshot: generated at audit time (574 files, SHA-256 of every tracked file)
- HEAD snapshot: `82dbae9475be7ba6116d10d921661fc0711ab7cb`
- All XML parse results: zero failures (live in audit)
- KNOWN baseline hash: `f5dde315f71bb4c28f72ea0b2a5cd3b5385f2e4aeb12b7463416174acb1b5f49` (2641 keys)
- MGC native config hash: `911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288`

---

**STAGE 1 complete. Awaiting approval for STAGE 4 before any file modifications.**