# Sony IMX682 Calibration — Full Audit Report (Kilo + Calibration Folders)

**Audit date:** 2026-10-19 15:00
**Calibration folder:** `C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\`
**Kilo folder:** `C:\Users\l\.config\kilo\` (config) + `C:\Users\l\.local\share\kilo\` (data/sessions)

## 1. Kilo Folder Audit

**Kilo is the CLI tool itself** — no camera-analysis code exists in the Kilo project folder. The Kilo directories contain:
- `C:\Users\l\.config\kilo\kilo.jsonc` (198 bytes) — Kilo configuration
- `C:\Users\l\.local\share\kilo\kilo.db` (109.8 MB) — session database
- `C:\Users\l\.local\share\kilo\log\` — execution logs (opencode.log 1.5 MB, session logs)
- `C:\Users\l\.local\share\kilo\storage\` — session diffs and share metadata
- `C:\Users\l\.local\share\kilo\tool-output\` — tool execution outputs

**Conclusion:** No camera-analysis workflow exists in Kilo. All calibration work is in `dcim_calibration/`. No integration changes needed — the unified_analysis.py pipeline is standalone and does not depend on Kilo internals.

## 2. Calibration Folder Inventory

**Total images:** 87 (86 JPG + 1 PNG)
**Total scripts:** 2 (unified_analysis.py, calibration_analysis_step1.py)
**Total analysis runs:** 2 (recapture_v12/Camera 37 images; target_1210 3 images)

### Directory structure:
```
dcim_calibration/
├── unified_analysis.py          (719 lines, PIL+numpy, optional matplotlib)
├── calibration_analysis_step1.py
├── capture_session_v2.md
├── analysis_results/
│   ├── IMX682_audit_report.md   (previous audit)
│   ├── IMX682_full_audit_report.md (this report)
│   ├── color_results.json       (color analysis data)
│   ├── calibration_verification.json
│   └── target_1210/
│       └── analysis/
│           ├── analysis_results.json (3 images)
│           ├── summary.csv
│           ├── summary_report.md
│           └── analysis.log
├── recapture_v12/
│   ├── analysis/analysis.log    (failed — images in Camera/ subfolder)
│   └── Camera/
│       ├── analysis/            (37-image batch results)
│       │   ├── analysis_results.json
│       │   ├── summary.csv
│       │   ├── summary_report.md
│       │   ├── analysis.log
│       │   └── annotated/      (annotated images)
│       └── *.jpg                (37 images)
├── _  20261019_121034_lmc_8.4.jpg  (7.7 MB, target 1)
├── _  20261019_121039_lmc_8.4.jpg  (7.8 MB, target 2)
├── _  20261019_121043_lmc_8.4.jpg  (7.6 MB, target 3)
└── (20+ more root-level images from various capture sessions)
```

## 3. Latest Photos (by modification time)

| Rank | File | Modified | Size | Location |
|------|------|----------|------|----------|
| 1 | recapture_v12/Camera/IMG_20261019_142639_1.jpg | 14:41:38 | 6.2 MB | V2 Release + stock batch |
| 2 | recapture_v12/Camera/IMG_20261019_142650_1.jpg | 14:41:38 | 5.2 MB | V2 Release + stock batch |
| 3-37 | recapture_v12/Camera/*.jpg | 14:41:35-38 | 2-8 MB | 37 images total |
| 38 | _  20261019_121034_lmc_8.4.jpg | 12:11:48 | 7.7 MB | Target photo 1 (natural scene) |
| 39 | _  20261019_121039_lmc_8.4.jpg | 12:11:48 | 7.8 MB | Target photo 2 (natural scene) |
| 40 | _  20261019_121043_lmc_8.4.jpg | 12:11:48 | 7.6 MB | Target photo 3 (natural scene) |

**Newest batch:** recapture_v12/Camera/ (37 images, pulled from device at 14:41, analyzed at 14:50)
**Oldest relevant:** root-level images from 12:11 (earlier capture sessions)

## 4. Image Classification

| Category | Count | Examples | Analysis Status |
|----------|-------|----------|-----------------|
| Natural scenes (no checkerboard) | ~50 | 121034, 121039, 121043, 133141, 133147, 133152 | Analyzed (MTF floor, no calibration possible) |
| Checkerboard targets | ~16 | 134401, 134408, 134414, 134420, 134433, 142620, 142622, 142632, 142635, 142649 | Analyzed (alternation 0.40-0.46) |
| Stock camera (LavaPlayUltra) | ~6 | 020261019_133814, 133816, 133819, 133821 | Analyzed (warm cast +6.3 to +9.4) |
| LMC 8.4 captures | ~12 | 020261019_133843, 133846, 140214, 141010, 141014 | Analyzed (V2 Release test) |
| Night/low-light | ~5 | 020261018_225339, 020261019_003658, 003712 | Not analyzed in detail |
| Quarantined donor | 1 | 020261019_103901 | Not useful (deleted from device) |

## 5. Calibration Analysis Summary

### Target 3 Photos (121034/121039/121043) — Natural Scenes
- All 3468×4624, EV ~8.0, ISO ~520, 1/50s, f/1.89, 5.43mm FL
- HDR+ 1.0.414775603zdy processing confirmed
- Warm cast: R-G +3.3 to +6.8, R/B 1.078-1.096
- Black clip: 1.89-3.21%, White clip: 0%
- Edge density: 6.05-6.36%
- MTF50: 0.0063 cyc/px (floor — no slanted edges in scene)
- **No checkerboard detected** — cannot perform MTF/distortion calibration

### 37-Image Batch (recapture_v12/Camera) — Mixed
- EV range: 4.9 to 8.9 (exposure bracket)
- Best MTF50: 0.1438 cyc/px at EV 6.8 (checkerboard target)
- Checkerboard detected in 16/37 images (6×8 and 6×12 patterns, alternation 0.40-0.46)
- LMC V2 Release: black clip 1.4-2.2%, white clip 0.45-6.3%, edge density 3.9-12.7%
- Stock camera: warm cast R-G +8.1 to +12.2 (sensor-level, not LMC-specific)

### Color Analysis
- No ColorChecker reference values available — CIEDE2000 cannot be computed
- R/B ratio and R-G are relative metrics only
- Warm cast is sensor-level (MT6878 ISP), not correctable via LMC XML keys alone

## 6. Code Reused and Changes Made

- **Reused:** `unified_analysis.py` (719 lines) — EXIF, RGB/luma, edge density, clipping, MTF50, checkerboard, histograms, CSV/JSON/markdown reports
- **Reused:** `calibration_analysis_step1.py` — older step-1 script (bugs fixed: histogram ravel, edge-mask shape)
- **Created:** `analysis_results/target_1210/` — isolated analysis of 3 target photos
- **Created:** `analysis_results/IMX682_audit_report.md` — previous audit
- **Created:** `analysis_results/IMX682_full_audit_report.md` — this comprehensive audit
- **No modifications** to Kilo internals, no competing implementations created

## 7. Errors and Limitations

1. **cv2, matplotlib, scipy, exifread not installed** — analysis uses PIL + numpy only. MTF uses simplified ESF method.
2. **recapture_v12/analysis/analysis.log shows failure** — images were in `Camera/` subfolder, not root. Fixed by pointing `--batch-dir` at the subfolder.
3. **No checkerboard in target 3 photos** — natural scene captures, not calibration targets. MTF50 is floor value.
4. **No ColorChecker reference data** — cannot compute CIEDE2000. R/B ratio is relative only.
5. **3 JPEGs alone cannot establish complete IMX682 calibration** — need RAW, controlled lighting, verified reference targets.
6. **Kilo folder has no camera-analysis code** — no integration needed or possible.

## 8. Remaining Tasks

1. Capture ISO 12233 slanted-edge chart + ColorChecker targets with LMC V2 Release config
2. Test v2.1 Auto AWB (pref_awb_key=0) and Daylight AWB (pref_awb_key=4) to reduce R-G warm cast
3. If XML tuning insufficient, install BSG GCam 9.2.113+ with AWB correction (requires user authorization)
4. Install cv2 + matplotlib for improved analysis (optional)
5. Pull latest V2 Release photos from device for formal analysis
6. Update capture_session_v2.md with latest findings
7. Do not claim complete IMX682 calibration until controlled chart captures are analyzed
