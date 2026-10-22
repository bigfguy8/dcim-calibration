# Sony IMX682 Camera Calibration — Latest Work Audit Report

**Audit date:** 2026-10-19 14:58
**Working directory:** `C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\`

## 1. Latest Work Discovered (by modification time)

| Time | File | Size | Notes |
|------|------|------|-------|
| 14:57:27 | `analysis_results/target_1210/analysis/analysis_results.json` | 88 KB | **NEWEST** — unified analysis of 3 target photos |
| 14:57:27 | `analysis_results/target_1210/analysis/summary.csv` | 5.2 KB | Metrics CSV for 3 target photos |
| 14:57:27 | `analysis_results/target_1210/analysis/summary_report.md` | 12.8 KB | Report for 3 target photos |
| 14:50:14 | `recapture_v12/Camera/analysis/analysis_results.json` | 88 KB | 37-image batch analysis (V2 Release) |
| 14:50:14 | `recapture_v12/Camera/analysis/summary_report.md` | 12.8 KB | 37-image batch report |
| 14:42:09 | `recapture_v12/analysis/analysis.log` | 165 B | Failed run (images in Camera/ subfolder) |
| 14:41:38 | `recapture_v12/Camera/*.jpg` | 37 files | V2 Release + stock photos pulled from device |
| 12:11:48 | `_  20261019_121034_lmc_8.4.jpg` | 7.7 MB | Target photo 1 (LMC 8.4, EV 8.04) |
| 12:11:48 | `_  20261019_121039_lmc_8.4.jpg` | 7.8 MB | Target photo 2 (LMC 8.4, EV 8.02) |
| 12:11:48 | `_  20261019_121043_lmc_8.4.jpg` | 7.6 MB | Target photo 3 (LMC 8.4, EV 8.06) |

## 2. Tasks Already Completed

- ADB device verified: `0123456789ABCDEF`, authorized, LAVA LXX521, Android 15/SDK 35
- Camera2 capability: FULL hardware level, 3 cameras (ID 0 rear 5.43mm, ID 1 front 3.59mm, ID 2 rear UW 1.98mm), EIS supported, OIS unavailable, RAW/manual present
- Baseline pulled: `/sdcard/LMC8.4/default .xml` (141,566 bytes, 2640 keys)
- `calibration_analysis_step1.py` bugs fixed (histogram ravel, edge-mask shape alignment)
- `unified_analysis.py` pipeline created and run on 21-image and 37-image batches
- V2 Release configs created with 34 calibration overrides, pushed to device, tested
- Stock camera photos captured and analyzed — warm cast confirmed sensor-level (R-G +8.1 to +12.2)
- All configs copied to organized `lxx521_*` subdirectories in `opencode/`
- Non-working configs deleted from device
- Fresh config `LXX521_LMC84_Fresh.xml` created from baseline and pushed to device
- Target 3 photos analyzed with unified_analysis.py (this audit)

## 3. Tasks Newly Completed (this audit)

- Audited entire `dcim_calibration/` folder recursively (37+ images, scripts, logs, reports, JSON)
- Located and validated the 3 target photos: `_  20261019_121034_lmc_8.4.jpg`, `_  20261019_121039_lmc_8.4.jpg`, `_  20261019_121043_lmc_8.4.jpg`
- Ran `unified_analysis.py` on the 3 photos in isolation (new `analysis_results/target_1210/` directory)
- Extracted EXIF, luminance, RGB, edge density, clipping, MTF50, checkerboard metrics for all 3

## 4. Target Photo Analysis Results

| Metric | Photo 1 (121034) | Photo 2 (121039) | Photo 3 (121043) |
|--------|-------------------|-------------------|-------------------|
| Dimensions | 3468×4624 | 3468×4624 | 3468×4624 |
| ISO | 527 | 519 | 534 |
| Exposure | 1/49.96s | 1/49.96s | 1/49.96s |
| EV | 8.041 | 8.019 | 8.060 |
| F# | 1.89 | 1.89 | 1.89 |
| FL | 5.43mm | 5.43mm | 5.43mm |
| Software | HDR+ 1.0.414775603zdy | HDR+ 1.0.414775603zdy | HDR+ 1.0.414775603zdy |
| Lum Mean | 114.5 | 112.4 | 109.0 |
| Lum Std | 80.3 | 79.2 | 82.3 |
| R Mean | 119.6 | 115.8 | 112.8 |
| G Mean | 112.8 | 111.6 | 109.5 |
| B Mean | 110.4 | 107.4 | 102.9 |
| R-G (warm cast) | +6.8 | +4.2 | +3.3 |
| R/B Ratio | 1.083 | 1.078 | 1.096 |
| Edge Density | 6.32% | 6.36% | 6.05% |
| Black Clip | 1.89% | 3.21% | 2.67% |
| White Clip | 0.00% | 0.00% | 0.00% |
| MTF50 (cyc/px) | 0.0063 | 0.0063 | 0.0063 |
| MTF50 (LWPH) | 20.0 | 20.0 | 20.0 |
| Checkerboard | Not detected | Not detected | Not detected |

## 5. Key Findings

1. **All 3 photos are natural/outdoor scenes**, not calibration charts — no checkerboard detected. MTF50 of 0.0063 cyc/px is very low, indicating the scene lacks sharp slanted edges for MTF measurement (not a lens sharpness issue).
2. **Warm color cast persists**: R-G ranges +3.3 to +6.8 across the 3 photos. R/B ratio 1.078-1.096. This is consistent with the sensor-level warm bias identified earlier (stock camera shows R-G +8.1 to +12.2).
3. **Exposure is well-controlled**: EV 8.02-8.06, ISO ~520, 1/50s shutter. Consistent across all 3 frames.
4. **Black clipping is moderate**: 1.89-3.21%, within the <3% target for 2 of 3 photos. White clipping is 0% — no highlight blowout.
5. **Edge density** 6.05-6.36% — below the >10% target, but this reflects scene content (natural foliage/landscape) rather than processing sharpness.
6. **HDR+ processing confirmed**: EXIF Software field shows `HDR+ 1.0.414775603zdy` — LMC's HDR+ pipeline is active.

## 6. Failures and Limitations

- **No checkerboard detected** in any of the 3 photos — cannot perform ISO 12233 slanted-edge MTF or radial distortion analysis. These photos appear to be natural scene captures, not calibration chart captures.
- **MTF50 = 0.0063 cyc/px** is a floor value — the scene lacks suitable slanted edges. This is NOT representative of lens sharpness. Earlier batch (recapture_v12) achieved MTF50 = 0.1438 cyc/px at EV 6.8 with checkerboard targets.
- **No ColorChecker reference values** available — cannot compute CIEDE2000 color accuracy. R/B ratio and R-G are relative metrics only.
- **cv2, matplotlib, scipy, exifread not installed** — analysis relies on PIL + numpy only. MTF uses simplified ESF-based method without proper edge detection refinement.
- **3 JPEGs alone cannot establish complete IMX682 calibration** — need RAW captures, controlled lighting, and verified reference targets.

## 7. Remaining Tasks

1. Capture proper ISO 12233 slanted-edge chart photos and ColorChecker targets for MTF and color accuracy validation
2. Install cv2 + matplotlib for improved edge detection and visualization (optional — pipeline works without them)
3. Test v2.1 Auto AWB (`pref_awb_key=0`) and Daylight AWB (`pref_awb_key=4`) configs against V2 Release to reduce R-G warm cast
4. If XML tuning insufficient, install BSG GCam 9.2.113+ with AWB correction module (requires user authorization)
5. Pull latest V2 Release photos from device and run unified_analysis on them
6. Update `capture_session_v2.md` with latest findings

## 8. Discrepancies Investigated

- **Earlier report (recapture_v12, 37 images)** claimed checkerboard detected in 16 of 37 images with alternation ratios 0.40-0.46. The 3 target photos (121034/121039/121043) show **no checkerboard** — these are natural scene captures taken at 12:10, before the calibration chart captures at 13:38+. This is consistent: the 12:10 photos are exposure-bracket natural scenes, while the 13:38+ photos include checkerboard targets.
- **MTF50 discrepancy**: Earlier batch best was 0.1438 cyc/px (EV 6.8, checkerboard target). Target 3 photos show 0.0063 cyc/px — this is expected since natural scenes lack slanted edges. Not a regression.

## 9. Files Inspected

- `unified_analysis.py` (719 lines) — main pipeline, PIL+numpy, optional matplotlib
- `calibration_analysis_step1.py` — older step-1 script (bugs fixed)
- `capture_session_v2.md` — capture procedure and learned findings
- `recapture_v12/Camera/analysis/summary_report.md` — 37-image batch report
- `recapture_v12/Camera/analysis/summary.csv` — 37-image metrics
- `recapture_v12/Camera/analysis/analysis_results.json` — 37-image detailed results
- `analysis_results/color_results.json` — color analysis data
- `analysis_results/calibration_verification.json` — calibration verification data
- 3 target photos: EXIF, dimensions, histograms, RGB, clipping, MTF, checkerboard

## 10. Recommended Next Steps

1. **Capture calibration chart photos** (ISO 12233 slanted-edge + ColorChecker) with the LMC 8.4 V2 Release config for proper MTF and color accuracy measurement
2. **Test v2.1 AWB variants** on device to reduce R-G warm cast below +4.0
3. **Consider BSG GCam 9.2.113+** if XML-only AWB tuning cannot achieve target — requires user authorization for APK install
4. **Install cv2 + matplotlib** for improved analysis capabilities (optional)
5. **Do not claim complete IMX682 calibration** from these 3 JPEGs — they are natural scene captures, not controlled calibration targets
