# TERMUX USAGE GUIDE — LAVA LXX521 / IMX682 DCIM Calibration

## Quick start

```sh
# 1. Install Termux and required packages
pkg install python git

# 2. Clone the repository
git clone https://github.com/bigfguy8/dcim-calibration.git ~/dcim-calibration-upgrade
cd ~/dcim-calibration-upgrade

# 3. Run the installer (creates directories, sets up paths)
bash TERMUX_INSTALL.sh

# 4. Run the calibration workflow
bash TERMUX_RUN.sh
```

## Core commands

### Run audit

```sh
# Audit all XML profiles in the repository
python run.py audit

# Or audit a single profile
python run.py audit --profile profiles/LXX521_IMX682_AllInOne_V3.xml
```

### Validate XML profile

```sh
python run.py validate --profile profiles/LXX521_IMX682_AllInOne_V3.xml
```

### Compare two profiles

```sh
python run.py compare --profile1 profiles/LXX521_IMX682_AllInOne_V3.xml --profile2 profiles/LXX521_IMX682_Super_AllInOne_V4.xml
```

### Dry-run deployment (no files written to device)

```sh
python run.py deploy --profile profiles/LXX521_IMX682_AllInOne_V3.xml
```

**Important**: The deploy command validates the profile and reports the result without
writing any files to the device. No configuration is automatically deployed to the
Android camera application.

### Show destination path

```sh
python run.py --list-dest
# Or with custom destination
python run.py --dest ~/storage/shared/Download/DCIM_Calibration --list-dest
```

## Directory structure after R3 restructuring (planned)

After the profile directory reorganization (R3 migration plan), the `profiles/`
directory will contain three sub-directories:

```
profiles/
├── lmc84/     # LMC 8.4 key family profiles (pref_qjpg_key, ptchr_*)
├── mgc_bsg/   # BSG/MGC-key and MIXED profiles (pref_quality_key, camera_id_back)
└── frontcam/  # Front camera–only profiles (NULL sensitivity range)
```

## Termux path management

The deployment scripts use the following path priority:

1. **`--dest` CLI argument** (highest priority): `python run.py deploy --dest /path/to/folder`
2. **Termux-preferred**: `$HOME/storage/shared/Download/DCIM_Calibration`
   - Set up storage: `termux-setup-storage`
   - Path: `~/storage/shared/Download/DCIM_Calibration/`
3. **Fallback**: `$HOME/.lcgc/` (if preferred dir not available)
4. **Android `/sdcard/LMC8.4/`** (last resort, may not exist in Termux)

### Ensure Termux shared storage is available

```sh
termux-setup-storage
# This creates ~/storage/shared/Download/ and related directories
```

### If `--dest` is not provided

The scripts will automatically use the Termux-preferred path if `termux-setup-storage`
has been run. If that path is unavailable, they fall back to `~/.lcgc/`, and then
to the Android `/sdcard/LMC8.4/` path.

## CLI cheat sheet

| Command | Effect |
|---|---|
| `python run.py audit` | Read-only XML syntax and schema audit |
| `python run.py validate --profile <file>` | Validate single profile structure |
| `python run.py compare --profile1 <f1> --profile2 <f2>` | Compare two profiles (read-only) |
| `python run.py deploy --profile <file>` | Dry-run deployment validation (no writes) |
| `python run.py --list-dest` | Show resolved destination path |
| `python run.py help` | Show help output |

## Known limitations (Termux)

- No on-device camera testing possible in this environment (Level D BLOCKED)
- Front camera NPE is a code-level bug; no XML profile can fix it
- Optional deps (opencv-python, numpy, matplotlib, Pillow) are NOT installed by default
  and not needed for stdlib-based scripts
- The `source_profiles/` directory referenced in some documentation does not exist
- Duplicate profile copies exist across the repository (16+ copies of baselines)
- Actual device validation requires a physical LAVA LXX521 device

## Commands referenced from this guide

- `TERMUX_INSTALL.sh` — 6-step installation script
- `TERMUX_RUN.sh` — CLI dispatch script
- `run.py` — Python CLI entry point
- `workflow_master_v4.py` — Safe profile picker/deployer
- `src/xml_audit.py` — Four-level XML validation (A–D)
- `src/config_validator.py` — XML structure validation
- `src/profile_manager.py` — Profile management with provenance
- `src/deployment.py` — Safe deployment with backup and rollback
- `requirements.txt` — Optional dependencies documentation