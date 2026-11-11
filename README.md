# MGC 8.9 (BSG) Camera Calibration & Tuning Pipeline

Automated optical calibration, testing, and configuration management for the **Lava Play Ultra 5G (Model: LXX521, Sensor: Sony IMX682)** running **MGC 8.9 (BSG)**.

---

## Architecture & Specifications

* **Base App:** MGC 8.9 (BSG)
* **Target Device:** Lava Play Ultra 5G (`LXX521` / Sony `IMX682`)
* **Configuration Directory:** `/sdcard/lmc8.4/` (MGC compatibility path)
* **Active Profiles:** 
  * `LXX521_TEX.xml` (V4.1 Texture-First Production Profile)
  * `LXX521_NIGHT.xml` (Handheld City / Nightscape Profile)

---

## Pipeline Modules

1. **`capture.sh`** — Executes automated test chart capture sequences via `adb` into structured session directories (`/sdcard/DCIM/calib/<session_id>/`), with local-import fallback when ADB is unavailable.
2. **`pull.sh`** — Synchronizes captured RAW (`.dng`) and JPEG (`.jpg`) assets from device storage to the local workspace with SHA-256 integrity verification.
3. **`analyze.py`** — Computes slanted-edge MTF50 sharpness metrics, per-channel noise distributions ($\sigma$), and exposure statistics using NumPy (with OpenCV when available).
4. **`report.py`** — Aggregates metrics by profile, camera, and ISO to generate structured Markdown + JSON audit reports against the quality gates.

---

## Quality Gates & Benchmarks

| Metric | Target (TEX Profile) |
| :--- | :--- |
| **MTF50 Center** | $\ge 0.30\text{ cy/px}$ |
| **MTF50 Edge** | $\ge 0.22\text{ cy/px}$ |
| **Noise ($\sigma$) @ ISO 100** | $\le 1.5\text{ DN}$ |
| **Noise ($\sigma$) @ ISO 3200** | $\le 12\text{ DN}$ |
| **Mean Luma** | $100 - 140$ |
| **Highlight Clipping** | $< 1\%$ |

Night captures (`LXX521_NIGHT.xml`) are judged against relaxed gates by
`report.py`: MTF50 center $\ge 0.18$, edge $\ge 0.12$ cy/px, mean luma
$70 - 120$ DN, highlight clipping $< 2\%$, and green sigma
$\le 15$ DN @ ISO 3200. Profiles whose name contains `NIGHT` opt in
automatically; the set is published as `night_gates` in the JSON report.

---

## Quick Start

```bash
# 1. Capture (device mode; falls back to local import when adb is absent)
./scripts/capture.sh --session 20261111_190000

# 2. Pull + verify integrity (SHA-256 manifest, DNG/JPG pairing optional)
./scripts/pull.sh 20261111_190000 --require-raw

# 3. Measure MTF50, per-channel sigma and exposure
python3 scripts/analyze.py analysis_results/20261111_190000/device --recursive

# 4. Aggregate to Markdown + JSON
python3 scripts/report.py analysis_results/20261111_190000/device/analysis.json

# 5. Enforce the two-profile mandate on the MGC storage path
./scripts/deploy_profiles.sh --prune
```

### ADB-optional operation

`capture.sh` and `pull.sh` detect `adb` automatically. Without a device they
operate on a local staging directory:

```bash
CALIB_LOCAL_ROOT=analysis_results \
./scripts/capture.sh --local --source /path/to/frames --session 20261111_190000
./scripts/pull.sh 20261111_190000 --from analysis_results/20261111_190000
```

`analyze.py` uses OpenCV when importable but falls back to Pillow + NumPy. DNG
decoding requires `rawpy`; without it DNG files are listed with
`status="skipped_no_raw_decoder"` and their EXIF metadata is still collected
through `exiftool`.

### Quality-gate exit codes

`report.py` writes `calibration_report.md` and `calibration_report.json`; pass
`--fail-on-gate` to exit non-zero when any profile/camera/ISO group misses a
gate, so CI can block regressions.

### Profile management

`configs/xml/LXX521_NIGHT.xml` is generated from `LXX521_TEX.xml`; the delta set
and rationale are documented in `configs/xml/LXX521_NIGHT.status.md` and enforced
by:

```bash
python3 scripts/make_night_profile.py --check
```

`deploy_profiles.sh --prune` archives any other `*.xml` in `/sdcard/lmc8.4/`
under `archive/<timestamp>/` before deploying the two active profiles, so the
destination always contains exactly `LXX521_TEX.xml` and `LXX521_NIGHT.xml`.

### Tests

```bash
python3 -m unittest discover -s scripts/tests -v
```

The suite validates MTF50 against an analytic Gaussian PSF, noise-sigma
recovery, exposure statistics, report grouping, and profile reproducibility.

