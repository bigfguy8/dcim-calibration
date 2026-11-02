# DEPENDENCY MAP — LAVA LXX521 / IMX682

**Stage:** 1 (read-only audit)
**Date:** 2026-10-31

## 1. Python Standard Library Usage

All 22 top-level Python scripts use only Python standard library modules, with the following observations:

| Module | stdlib modules used | External deps | Termux-safe? |
|---|---|---|---|
| `lxx521_imx682_v8_audit.py` | `argparse, hashlib, json, os, re, shutil, sys, tempfile, datetime, pathlib, xml.etree.ElementTree` | none | ✅ |
| `workflow_master_v4.py` | `argparse, hashlib, json, os, shutil, sys, pathlib, xml.etree.ElementTree, datetime` | none | ✅ (with path fix) |
| `dcim_calibration_audit.py` | `argparse, hashlib, json, os, re, shutil, sys, tempfile, datetime, pathlib, xml.etree.ElementTree` | none | ✅ |
| `v9_camera_audit.py` | similar stdlib-only | none | ✅ |
| `run_v8_comparison.py` | stdlib-only | none | ✅ |
| `guided_v9_ab_test.py` | stdlib-only | none | ✅ |
| `build_v10_lmc84.py` | stdlib-only | none | ✅ |
| `patch_dcim.py` | `pathlib` | none | ✅ |
| `create_v5/v6/v7.py` | stdlib-only | none | ✅ |
| `make_candidate_c/d.py` | stdlib-only | none | ✅ |
| `adb_capture_helper.py` | stdlib-only | none | ✅ |
| `workflow_master.py` | stdlib-only | none | ✅ |

## 2. Heavier-dependency Scripts (not Termux-safe as-is)

| Script | External dependencies | Termux status |
|---|---|---|
| `imx682_opencv_calibration.py` | `cv2` (OpenCV), `numpy`, `matplotlib`, `Pillow` (PIL) | ⚠️ Will `ImportError` on most Termux installs |
| `analyze_first3_batches.py` | `numpy`, `Pillow` | ⚠️ |
| `run_crisp_pipeline.py` | `subprocess`, `shutil` (stdlib) | ✅ (no heavy deps) |

## 3. Recommended `requirements.txt`

```
# Termux-safe core modules (all scripts in src/ use these only)
# No external dependencies required for stdlib-based scripts.

# Optional heavy analysis — not needed on device, install only for desktop:
# opencv-python
# numpy
# matplotlib
# Pillow
```

**Rationale:** The mission prioritizes Termux compatibility. All new `src/` modules use only stdlib. Heavy libraries (OpenCV, numpy, matplotlib, PIL) are optional desktop-only dependencies.

## 4. CI Workflow Dependencies (from `.github/workflows/python-app.yml`)

| Dependency | Version | Purpose |
|---|---|---|
| `pip` | latest | Python package manager |
| `flake8` | latest | Linting (E9,F63,F7,F82; max-complexity=10; max-line=127) |
| `pytest` | latest | Test execution |

**Note:** The CI workflow checks `if [ -f requirements.txt ]; then pip install -r requirements.txt; fi`. Since no `requirements.txt` exists in the repo, the dependency install step is skipped vacuously.

---

**Dependency map complete. No existing files were modified.**