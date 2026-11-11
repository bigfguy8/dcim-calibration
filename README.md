# MGC 8.9 (BSG) Camera Calibration & Tuning Pipeline

Automated optical calibration, testing, and configuration management for the **Lava Play Ultra 5G (Model: LXX521, Sensor: Sony IMX682)** running **MGC 8.9 (BSG)**.

---

## Architecture & Specifications

* **Base App:** MGC 8.9 (BSG)
* **Target Device:** Lava Play Ultra 5G (`LXX521` / Sony `IMX682`)
* **Configuration Directory:** set via `CALIB_LMC_DIR` (no default; the
  deploy scripts refuse to run until it is provided)
* **Active Profiles:** 
  * `LXX521_TEX.xml` (V4.1 Texture-First Production Profile)
  * `LXX521_AI.xml` (Balanced Computational Variant)

---

## Pipeline Modules

1. **`capture.sh`** — Executes automated test chart capture sequences via `adb` into structured session directories (`/sdcard/DCIM/calib/<session_id>/`), with local-import fallback when ADB is unavailable.
2. **`pull.sh`** — Synchronizes captured RAW (`.dng`) and JPEG (`.jpg`) assets from device storage to the local workspace with SHA-256 integrity verification.
3. **`analyze.py`** — Computes slanted-edge MTF50 sharpness metrics, per-channel MAD-based noise distributions ($\sigma$), exposure statistics, and optional gray-patch CIEDE2000 neutrality using NumPy (with OpenCV when available).
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
| **Gray-Patch Neutrality ($\Delta E_{00}$)** | $\le 5$ |

Night captures (`LXX521_NIGHT.xml`) are judged against relaxed gates by
`report.py`: MTF50 center $\ge 0.18$, edge $\ge 0.12$ cy/px, mean luma
$70 - 120$ DN, highlight clipping $< 2\%$, and green sigma
$\le 15$ DN @ ISO 3200. Profiles whose name contains `NIGHT` opt in
automatically; the set is published as `night_gates` in the JSON report. The
gray-patch $\Delta E_{00} \le 5$ gate applies to every profile.

---

## Quick Start

```bash
# 1. Capture (device mode; falls back to local import when adb is absent)
./scripts/capture.sh --session 20261111_190000

# 2. Pull + verify integrity (SHA-256 manifest, DNG/JPG pairing optional)
./scripts/pull.sh 20261111_190000 --require-raw

# 3. Measure MTF50, per-channel sigma, exposure and gray-patch neutrality
python3 scripts/analyze.py analysis_results/20261111_190000/device --recursive \
    --gray-patch 1180,820,420,420

# 4. Aggregate to Markdown + JSON
python3 scripts/report.py analysis_results/20261111_190000/device/analysis.json

# 5. Enforce the two-profile mandate on the MGC storage path
CALIB_LMC_DIR=/path/to/mgc/config ./scripts/deploy_profiles.sh --prune
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

`configs/xml/LXX521_AI.xml` is generated from `LXX521_TEX.xml`; the delta set
and rationale are documented in `configs/xml/LXX521_AI.status.md` and enforced
by:

```bash
python3 scripts/make_ai_profile.py --check
```

`deploy_profiles.sh --prune` archives any other `*.xml` in the destination
under `archive/<timestamp>/` before deploying the two active profiles, so the
destination always contains exactly `LXX521_TEX.xml` and `LXX521_AI.xml`.
There is no hardcoded destination: pass `--dest DIR` or set `CALIB_LMC_DIR`.
The optional `LXX521_NIGHT.xml` remains in `configs/xml/` for night sessions
and is archived by `--prune` when it is not part of the active pair.

### Tests

```bash
python3 -m unittest discover -s scripts/tests -v
```

The suite validates MTF50 against an analytic Gaussian PSF, noise-sigma
recovery, exposure statistics, report grouping, and profile reproducibility.

---

## LXX521 Candidate Triage

Seventeen LXX521 LMC84 XML profile variants are registered as **read-only inputs**
under `configs/candidates/LXX521/` and triaged against the canonical baseline
`configs/xml/LXX521_TEX.xml`.

### Invariant (read-only)

Candidates are **inputs, not deploy targets**. The active deployed pair remains
`LXX521_TEX.xml` + `LXX521_AI.xml`; `deploy_profiles.sh` deploys only that pair.
`/sdcard/lmc8.4` is **READ-ONLY** in this feature: the `device_live` source is
verify-only and is never written to or deployed from. No push to `main`; all work
lands on a feature branch only.

### Sources registry (`configs/sources.json`)

Three sources are registered:

| name | path | kind | role | read_only |
|---|---|---|---|---|
| `repo_canonical` | `configs/xml` | lmc84 | canonical | no |
| `repo_candidates` | `configs/candidates/LXX521` | lmc84 | candidate | no |
| `device_live` | `/sdcard/lmc8.4` | lmc84 | live | yes |

`manifest_sha256` algorithm: build the canonical JSON blob
`{"files":[{"name":<basename>,"sha256":<hex>,"bytes":<int>}, ...]}` with file
entries sorted by name, object keys sorted, UTF-8 encoding, no whitespace, then
SHA-256 that blob. `verify` recomputes it and exits `0` on match, `1` on drift.

Commands (`scripts/sources.py`):

```bash
# list all sources with file/byte counts
python3 scripts/sources.py list

# verify every source manifest (exit 0 = all match, 1 = drift)
python3 scripts/sources.py verify

# verify a single source
python3 scripts/sources.py verify --name repo_candidates

# register a new source (writes only to configs/)
python3 scripts/sources.py add --name foo --path /some/dir --kind lmc84 --role candidate

# remove a source (live sources require --yes)
python3 scripts/sources.py remove --name foo --yes
```

### Triage CLI (`scripts/triage_profiles.py`)

```bash
python3 scripts/triage_profiles.py \
    --candidates configs/candidates/LXX521 \
    --reference configs/xml/LXX521_TEX.xml \
    --out reports \
    --format md
```

Writes `reports/lxx521_triage.md` (human; `generated_at` in header only) and
`reports/lxx521_triage.json` (machine; **no timestamps**, deterministic ordering).

For each candidate it reports sha256, byte size, key count, the delta vs the
reference (added / removed / changed keys), a family assignment, and validation
status via `validate_source` (kind `lmc84`).

### Family taxonomy (deterministic, first match wins)

| family | rule |
|---|---|
| `baseline` | no added or changed keys |
| `night` | name contains `NIGHT`, or `lib_denoise_key>1` AND `pref_frames_hdr_key>4` |
| `balanced` | name contains `BALANCED` |
| `dslr` | name matches `/DSLR(64|MAX)?/` |
| `sharpness_probe` | name contains `SHARPNESS_PROBE`, or only `lib_sharpnessb_key` changed |
| `allinone` | name contains `ALLINONE` |
| `hr` | name contains `_HR` |
| `aesthetic` | name in `{IPHONE, PIXEL, PORTRAIT}` |
| `experiment` | fallback |

### Duplicate detection

Candidates are grouped by exact sha256 and by delta signature
(frozenset of `{"key","old","new"}` change triples). Groups with `>1` member are
reported as duplicates.

### `keys_unknown.txt` workflow

When validating a **candidate** source, unknown keys are downgraded to warnings
and appended to `configs/keys_unknown.txt` (sorted, deduped). Review that file to
decide whether to promote unknown keys into `configs/keys.txt`.

### Deploy / source overlap guard

Before `deploy_profiles.sh --prune` archives anything into the destination, it
calls `scripts/sources.py verify-overlap --path <dest>`. If the destination is a
registered `live` source path (e.g. `/sdcard/lmc8.4`), the prune is refused with
exit code `2` unless `--force-source-overlap` is supplied. Dry-run behavior is
unchanged.


