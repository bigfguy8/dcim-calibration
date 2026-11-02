# DCIM Calibration V4 — Lava LXX521 / IMX682

## Project structure

This repository contains camera configuration profiles and a calibration engine
for the LAVA LXX521 device with Sony IMX682 rear sensor, running Android 15 /
SDK 35 with MediaTek MT6878.

### Key directories

- `profiles/` — Authoritative XML candidate profiles (LMC 8.4, BSG MGC, MIXED,
  and UNKNOWN schema families). Organised by family after restructuring.
- `src/` — Python calibration engine modules (9 modules): device_probe,
  camera_capabilities, xml_audit, profile_compare, config_generator,
  config_validator, profile_manager, deployment, image_quality_analyzer.
- `analysis_results/` — Generated profiles, audit reports, and comparison data
  from previous runs.
- `MGC/` — BSG MGC 9.4.103 investigation (separate schema family from LMC).
- `backups/` — Quarantined duplicates and timestamped backups created during
  deployment operations.
- `TERMUX_/` — Termux-specific scripts: TERMUX_INSTALL.sh, TERMUX_RUN.sh.
- `docs/` — Validation and documentation files.
- `V10_Backups/`, `V10_Master_Output/` — V10 release artifacts.
- `workflow_master_v4.py` — Safe profile picker/deployer with Termux-compatible
  path handling and backup/rollback support.

### Schema families

Two distinct key families exist in the repository. These are **NOT interchangeable**:

- **LMC 8.4** (`pref_qjpg_key`, `ptchr_*` markers): Valid for LMC 8.4 on MT6878/IMX682.
- **BSG / MGC** (`pref_quality_key`, `camera_id_back` markers): Valid for MGC 9.4.103/9.8.102.
- **MIXED** profiles contain markers from both families and should not be imported
  into apps that support only one family.
- **UNKNOWN** profiles have no recognized markers; compatibility is unverified.

## Installation in Termux

1. Clone the repository:

   ```sh
   git clone https://github.com/bigfguy8/dcim-calibration.git ~/dcim-calibration-upgrade
   cd ~/dcim-calibration-upgrade
   ```

2. Install Python 3 and required packages (stdlib only; no external deps needed
   for core scripts):

   ```sh
   pkg install python
   # All src/ modules use Python standard library only.
   # Optional: opencv-python, numpy, matplotlib, Pillow for desktop analysis.
   ```

3. Run the Termux installer:

   ```sh
   bash TERMUX_INSTALL.sh
   ```

4. Run the calibration workflow:

   ```sh
   bash TERMUX_RUN.sh
   ```

   Or use the Python CLI:

   ```sh
   python run.py audit
   python run.py validate --profile profiles/LXX521_IMX682_AllInOne_V3.xml
   python run.py compare --profile1 profiles/LXX521_IMX682_AllInOne_V3.xml --profile2 profiles/LXX521_IMX682_Super_AllInOne_V4.xml
   python run.py deploy --profile profiles/LXX521_IMX682_AllInOne_V3.xml
   ```

## Project structure (high level)

```
dcim-calibration-upgrade/
├── .github/           # CI workflows
├── MGC/               # BSG MGC 9.4.103 investigation
├── analysis_results/  # Generated profiles and audit reports
├── backups/           # Timestamped backups from deployments
├── docs/              # Validation and documentation
├── V10_Backups/       # V10 release artifacts
├── V10_Master_Output/ # V10 release outputs
├── TERMUX_INSTALL.sh  # 6-step Termux install script
├── TERMUX_RUN.sh      # CLI dispatch: xml_audit, profile_manager, deploy, etc.
├── workflow_master_v4.py  # Safe profile picker/deployer
├── src/               # 9 calibration engine modules
├── requirements.txt   # Optional deps: opencv-python, numpy, matplotlib, Pillow
├── run.py             # CLI entry point (audit, validate, compare, deploy)
├── LXX521_FrontCam_*.xml  # Front camera sanitized profiles
├── PROFILE_COMPATIBILITY.md
├── REPOSITORY_AUDIT.md
├── SOURCE_INVENTORY.md
├── DEPENDENCY_MAP.md
├── DUPLICATE_CONFLICT_REPORT.md
├── VALIDATION_REPORT.md
├── TEST_REPORT.md
├── STAGE2_EVIDENCE_RECONCILIATION.md
├── UPGRADE_CHANGELOG.md
└── README_V4.md
```

## Dependencies

### Mandatory (all scripts use these)

- Python 3.10+ (stdlib)
- `argparse`, `hashlib`, `json`, `xml.etree.ElementTree`, `pathlib`, `shutil`,
  `sys`, `os`, `datetime`, `tempfile` — all standard library

### Optional (desktop-only, not needed on Termux/device)

- `opencv-python` (`cv2`) — image processing, checkerboard detection
- `numpy` (`np`) — numerical operations, statistics
- `matplotlib` (`plt`) — plotting, MTF50 visualizations
- `Pillow` (`PIL`) — image reading, EXIF, basic analysis

**Termux**: Install nothing from the optional list. All `src/` modules work
out-of-the-box with stdlib only. See `imx682_opencv_calibration.py` for the
optional OpenCV/numpy/matplotlib guard pattern.

## CLI usage

### `python run.py audit`

Run read-only XML syntax and schema validation on all profiles in the repository.
No files are modified. No device writes are performed.

```sh
python run.py audit
# Or: python run.py audit --profile profiles/LXX521_IMX682_AllInOne_V3.xml
```

### `python run.py validate`

Validate XML profile structure (syntax, schema, unsupported keys, critical keys,
duplicates, SHA-256 integrity).

```sh
python run.py validate --profile profiles/LXX521_IMX682_AllInOne_V3.xml
```

### `python run.py compare`

Compare two XML profiles by keys, values, schema family, and SHA-256 hash. All
comparisons are read-only.

```sh
python run.py compare --profile1 profiles/LXX521_IMX682_AllInOne_V3.xml --profile2 profiles/LXX521_IMX682_Super_AllInOne_V4.xml
```

### `python run.py deploy`

Dry-run deployment validation. Validates the profile and reports the result
without writing any files. No configuration is automatically deployed to the
Android camera application.

```sh
python run.py deploy --profile profiles/LXX521_IMX682_AllInOne_V3.xml
```

**Never** run a deployment command without reviewing the profile and confirmation
prompt first. The deploy command requires explicit `YES` confirmation before any
real file copy operation.

## Backup and rollback

- The `workflow_master_v4.py` deployer creates a `.bak` backup before overwriting
  an existing destination file. Backup filename format:
  `{dest_name}.{YYYYMMDD-HHMMSS}.bak`
- The `src/deployment.py` module provides `deploy_profile()` with backup and
  rollback support. Use `deploy_interactive()` for confirmation-guided deployment.
- The `src/profile_manager.py` module provides `backup_profile()` and
  `rollback_to_latest()` for profile-level backup and restoration.
- SHA-256 hash verification is performed on all deployments and backups.

## Validation levels

Four distinct validation levels are strictly separated (per mission §8):

| Level | Check | Status |
|---|---|---|
| **A** | XML syntax validation (well-formedness, root `<map>`, `name` attributes, no duplicate keys) | ✅ VERIFIED — all profiles pass |
| **B** | Configuration schema identification (LMC vs BSG vs MIXED / UNKNOWN) | ✅ OBSERVED — by key-content markers |
| **C** | Camera application compatibility (deterministic statements based on schema family) | ❌ NOT TESTED — no device |
| **D** | Actual device validation (on-device Camera2 characteristics) | ❌ BLOCKED — no device attached |

**Never confuse these four levels.** Level D must not be inferred from XML syntax
alone. See `docs/VALIDATION_STATUS.md` for the full validation status matrix.

## Known limitations

- No on-device camera testing has been performed (per safety scope). Level D is
  BLOCKED, not FAIL.
- The front camera (ID 1) has a NULL `CONTROL_POST_RAW_SENSITIVITY_BOOST_RANGE`
  — this is a code-level NullPointerException in `loadConfinesExposureISO()` that
  no XML profile can fix. Vendor/BSG code change required.
- LMC and BSG schema families are NOT interchangeable. Mixing keys may cause
  the app to ignore keys from one family or, in some configurations, crash.
- No benchmark image samples or quality outputs are included. Profile values are
  a reasoned starting point, not a verified quality improvement.
- The `source_profiles/` directory referenced in some documentation does not
  exist in this repository.
- Duplicate profile copies exist across the repository (16 copies of the
  LMC84_AllRounder baseline). The calibration engine organizes profiles by
  schema family to mitigate confusion.
- Actual device runtime validation requires a physical LAVA LXX521 device attached
  running the target camera app.

## Commands to run tests

```sh
# Python syntax check (all 22 top-level scripts + 9 src/ modules)
python3 -c "import py_compile; [py_compile.compile(f, doraise=True) for f in ['src/*.py', '*.py'])"

# XML well-formedness check
python3 -m src.xml_audit check_syntax profiles/LXX521_IMX682_AllInOne_V3.xml

# Module import verification
python3 -c "from src import device_probe, camera_capabilities, xml_audit, profile_compare, config_generator, config_validator, profile_manager, deployment, image_quality_analyzer"

# Regression tests (run pytest if available)
python3 -m pytest tests/

# Deployment dry-run
python run.py deploy --profile profiles/LXX521_IMX682_AllInOne_V3.xml
```

## Notes

- No internet access required. No GitHub dependency. No ADB dependency. No PC
  dependency. No root requirement.
- Preserve Android/Termux compatibility. Never delete original profiles.
- Never overwrite the only working XML.
- Never fabricate test results or device measurements.
- Never silently suppress errors.
- Never automatically deploy configurations.
- Do not modify firmware, NVRAM, NVDATA, or secure storage.
- Do not launch camera test sessions.