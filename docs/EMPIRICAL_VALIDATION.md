# MGC 8.9 LXX521 Empirical Validation Workflow

This guide covers physical capture and analysis workflow for calibration validation on Lava Play Ultra 5G (LXX521 / IMX682).

---

## Capture Setup

### Required Charts & Targets

| Capture | Purpose | Setup |
|---------|---------|-------|
| ISO 12233 chart | MTF50 spatial resolution | Print ISO 12233 chart at ≥ A2 size, mount flat, good diffuse lighting |
| Gray card / ColorChecker | Color accuracy (deltaE00) | Use X-Rite ColorChecker or equivalent gray card under same lighting as chart |
| Flat field | Shading/vignetting | Shoot uniform gray or white target at same distance as chart |
| 4K video clip | Video mode MTF + noise | Record 10-30s of chart or scene with each profile |

### Lighting Requirements

| Profile | Light level | Color temp | Notes |
|---------|------------|------------|-------|
| TEX (day) | ≥ 500 lux | 5500K (D65) | Diffuse, even — no hot spots |
| NIGHT | ~10-50 lux | Warm (~3200K) | Low noise — use tripod if < 30 lux |

---

## Capture Workflow

### Step 1 — Deploy Mandated Profiles

```bash
# Deploy TEX + NIGHT to /sdcard/lmc8.4/
cd /data/data/com.termux/files/home/dcim-calibration-github
./scripts/deploy_profiles.sh --dest /sdcard/lmc8.4 --prune --local --force-source-overlap
```

### Step 2 — Switch to Profile Under Test

1. Open MGC 8.9
2. Settings → Select profile: **TEX** or **NIGHT**
3. Return to camera

### Step 3 — Photograph ISO 12233 Chart

```bash
# After capture, pull from device
adb pull /sdcard/DCIM/Camera/*IMG*.jpg ./captures/ISO12233/
```

- Camera distance: chart fills ≥ 60% of frame height
- Ensure edge patches are clearly visible (not clipped)
- Use timer or remote trigger to avoid shake
- Take 3 shots per profile, pick sharpest

### Step 4 — Photograph Gray Card

```bash
adb pull /sdcard/DCIM/Camera/*IMG*.jpg ./captures/graycard/
```

- Fill frame with gray card
- Neutral gray patch (e.g., 18% gray) for exposure
- No harsh shadows on card

### Step 5 — Photograph Flat Field

```bash
adb pull /sdcard/DCIM/Camera/*IMG*.jpg ./captures/flatfield/
```

- Uniform white or gray wall
- Same distance as chart
- Check for shading/vignetting in analysis output

### Step 6 — Record 4K Video

```bash
# Record 10-30s video of chart
adb pull /sdcard/DCIM/Camera/*VID*.mp4 ./captures/4k_video/
```

- 4K 30fps with each profile (TEX, NIGHT)
- Extract a sharp frame for MTF analysis:
```bash
ffmpeg -i VIDEO_FILE -vf "select=eq(n\,30)" -vframes 1 frame_tex.png
```

---

## Analysis Commands

All scripts are pure-Python (no OpenCV, no rawpy). Requires only Pillow and tifffile.

### Full analysis on a capture

```bash
# MTF50 + noise + exposure from a single image
python3 scripts/analyze.py captures/ISO12233/img_tex_001.jpg \
    --profile TEX --camera LXX521 --session 001 \
    --mtf-method iso12233 \
    --output analysis/TEX_mtf50_001.json \
    --pretty
```

### Batch analyze DCIM captures

```bash
# Auto-detect latest DCIM images and extract metrics
python3 scripts/analyze_photos.py \
    --camera-dir /sdcard/DCIM/Camera \
    --limit 20 \
    --output analysis/dcim_batch.json
```

### Gray card color accuracy (deltaE00)

```bash
# Identify a neutral gray patch ROI and measure CIEDE2000 error
# Use GIMP or ImageMagick to find pixel coordinates first
python3 scripts/analyze.py captures/graycard/gray_card.jpg \
    --gray-patch X,Y,W,H \
    --profile TEX --camera LXX521 \
    --output analysis/TEX_graycard.json
```

### Compare two profiles side by side

```bash
# Markdown comparison
python3 scripts/compare.py analysis/TEX_mtf50.json analysis/NIGHT_mtf50.json --out md

# JSON comparison
python3 scripts/compare.py analysis/TEX_mtf50.json analysis/NIGHT_mtf50.json --out json
```

### DNG ingest (for RAW captures)

```bash
# Convert DNG to intermediate TIFF
python3 scripts/dng.py capture.DNG --output capture.tiff

# Then analyze the TIFF
python3 scripts/analyze.py capture.tiff --profile TEX
```

### MTF50 only (fast)

```bash
# One-shot slanted-edge MTF50
python3 scripts/mtf.py captures/ISO12233/chart_shot.png
```

---

## Gate Thresholds (from configs/gates.json)

### Day (TEX)

| Metric | Min | Max | Unit |
|--------|-----|-----|------|
| MTF50 center | 0.30 | — | cycles/px |
| MTF50 edge | 0.22 | — | cycles/px |
| Mean luma | 100 | 140 | DN |
| Highlight clipping | — | 1.0 | % |
| Noise green ISO100 | — | 1.5 | DN |
| Noise green ISO3200 | — | 12.0 | DN |
| Gray patch deltaE00 | — | 5.0 | dE00 |

### Night (NIGHT)

| Metric | Min | Max | Unit |
|--------|-----|-----|------|
| MTF50 center | 0.18 | — | cycles/px |
| MTF50 edge | — | — | cycles/px |
| Mean luma | — | — | DN |

> Exact night thresholds: check `configs/gates.json`

---

## Full Pipeline (deploy + analyze)

```bash
# Single command: deploy mandated profiles then analyze latest DCIM captures
CALIB_LMC_DIR=/sdcard/lmc8.4 \
DCIM_PATH=/sdcard/DCIM/Camera \
./scripts/run_deploy_and_analyze.sh
```

Output: `analysis/data/dcim_camera_analysis/calibration_metrics.json`

---

## Directory Structure

```
dcim-calibration-github/
├── captures/
│   ├── ISO12233/          # ISO 12233 chart photos
│   ├── graycard/          # Gray card / ColorChecker photos
│   ├── flatfield/         # Flat field / shading captures
│   └── 4k_video/          # 4K video clips and extracted frames
├── analysis/
│   ├── TEX_mtf50_001.json
│   ├── NIGHT_mtf50_001.json
│   └── dcim_batch.json
├── scripts/
│   ├── analyze.py          # MTF50 + noise + exposure (single image)
│   ├── analyze_photos.py   # Batch DCIM analysis
│   ├── compare.py          # Side-by-side JSON comparison
│   ├── dng.py             # DNG → TIFF via tifffile
│   ├── mtf.py             # ISO12233 slanted-edge MTF50
│   └── run_deploy_and_analyze.sh
└── configs/
    ├── gates.json          # Pass/fail thresholds
    └── xml/                # Active profiles
```

---

## Front Camera Validation

After physical captures, test front camera separately:

1. Open MGC 8.9 → switch to **front camera**
2. Photograph ISO 12233 chart from appropriate distance (selfie distance ~30-40cm)
3. Photograph gray card at selfie distance
4. Record front video
5. Analyze same as rear camera, but use `--camera LXX521_FRONT` label

```bash
python3 scripts/analyze.py captures/ISO12233/selfie_chart.jpg \
    --profile TEX --camera LXX521_FRONT --session selfie_001 \
    --output analysis/front_tex_mtf50.json
```

---

## Quick Test Sequence

```bash
# 1. Deploy
./scripts/deploy_profiles.sh --dest /sdcard/lmc8.4 --prune --local --force-source-overlap

# 2. Capture (manual on device)

# 3. Pull
adb pull /sdcard/DCIM/Camera/*.jpg ./captures/ISO12233/

# 4. Analyze
python3 scripts/analyze.py captures/ISO12233/shot.jpg \
    --profile TEX --camera LXX521 \
    --mtf-method iso12233 \
    --output analysis/TEX_capture.json --pretty

# 5. Compare with gate thresholds
python3 scripts/validate_profile.py analysis/TEX_capture.json
```
