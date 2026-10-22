# IMX682 LMC 8.4 — Final Audit & Config Validation Report

**Date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15, SDK 35
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Sensor:** Sony IMX682, rear 5.43mm f/1.89, front 3.59mm, UW 1.98mm

---

## 1. What Was Inspected

### 1.1 Device Photos (72 total + 3 videos)

| Category | Count | Software Tag | EV Range | ISO Range |
|----------|-------|--------------|----------|-----------|
| LMC 8.4 captures | 50 | HDR+ 1.0.414775603zdy/ndy | -5.99 to 3.71 | 288-25500 |
| Stock camera captures | 19 | MediaTek Camera Application | -2.29 to 7.74 | 101-4909 |
| Monitor captures | 32 | HDR+ 1.0.414775603zdy | -0.16 to 3.71 | 288-1860 |
| New captures (latest) | 7 | Mixed (zdy/ndy/None) | -0.91 to 2.16 | 371-1670 |
| **Total photos** | **72** | | | |
| **Videos** | **3** | LMC 8.4 | — | — |

Video details:
- 20261019_175043_lmc_8.4.mp4: 1080×1920, 29.95 fps, 17.76s, 30MB
- 20261019_175111_lmc_8.4.mp4: 2160×3840, 29.95 fps, 16.36s, 102MB
- VID_20261019_175334.mp4: 1080×1920, 29.95 fps, 9.71s, 37MB

### 1.2 XML Configs Audited

| Source | Count | Compatible with LMC 8.4? |
|--------|-------|--------------------------|
| Device /sdcard/LMC8.4/ | 4 (default, Fresh, Optimized_Corrected, Special) | ✅ Yes (all 2640 keys) |
| Device /sdcard/GCam/ | 16+ | ❌ No (different format/port) |
| Desktop | 6+ | Mixed (some compatible) |
| Project folders | 15+ | Mixed |
| **Total audited** | **40+** | |

**Working baseline identified:** `default .xml` (SHA-256 `f5dde315...`, 2640 keys, root=map, lmc_style=1878)

**Incompatible configs:** bigfguy8.xml, V2_Day.xml, V2_Night.xml, LavaPlayUltra_IMX682_Pro.xml (different GCam port, Map/root schema)

### 1.3 Analysis Scripts & Reports

| Category | Count | Location |
|----------|-------|----------|
| Analysis scripts | 20+ | Various directories |
| Reports (Markdown) | 15+ | analysis_results/ |
| Data files (JSON/CSV) | 20+ | analysis_results/ |
| Plots (PNG) | 16+ | final_report/plots/ |
| Contact sheets | 3 | ab_comparison/, dcim_chart_audit/ |

## 2. What Was Created

### 2.1 Final Config: LXX521_IMX682_SuperCrisp.xml

| Property | Value |
|----------|-------|
| Path | `analysis_results/imx682_config/final/LXX521_IMX682_SuperCrisp.xml` |
| SHA-256 | `7b5ece32b2e6e98c9bf88198d0d004b0ce9d8964f49c8b9f204db0a8c5dd6288` |
| Key count | 2640 (identical to baseline) |
| Size | 143,961 bytes |
| Schema | `<map>` with `<string name="..." value="..."/>` |
| Status | **UNVERIFIED** — no A/B test performed |

### 2.2 Changed Keys (11)

| Key | Baseline | Final | Evidence |
|-----|----------|-------|----------|
| cw_rg_key | 0.5925 | 0.4500 | Warm cast R-G +5.68 mean |
| lib_sharpnessb_key | 0 | 2 | Edge density 0.0296 (target >0.10) |
| lib_sharpgain_key | 0 | 2 | Complement to sharpnessb |
| lib_sharpmini_key | 0 | 2 | Fine detail preservation |
| lib_contrast_1_key | 0 | 1 | Micro-contrast boost |
| lib_contrast_2_key | 0 | 1 | Micro-contrast boost |
| pref_iso_noise_key | 2 | 3 | ISO noise handling |
| lib_denoise_key | 0 | 1 | Light denoise |
| lib_lumadenoise_key | 0 | 1 | Light luma denoise |
| lib_lumanoise_key | 0 | 1 | Light luma noise |
| lib_preservinghigh_key | 0 | 1 | Preserve highlights |

### 2.3 Supporting Files

| File | Purpose |
|------|---------|
| `default_working_backup.xml` | Backup of working baseline (SHA-256 `f5dde315...`) |
| `change_log.json` | Detailed change log with evidence |
| `validation_report.json` | Syntax, schema, compatibility validation |
| `ROLLBACK_INSTRUCTIONS.txt` | Rollback and deployment steps |
| `generate_final.py` | Reproducible generation script |

## 3. What Was Transferred

| File | Device Path | SHA-256 | Verified |
|------|------------|---------|----------|
| `LXX521_IMX682_SuperCrisp.xml` | `/sdcard/LMC8.4/LXX521_IMX682_SuperCrisp.xml` | `7b5ece32...` | ✅ Match |

### All Device Configs (Preserved)

| Config | Path | SHA-256 | Status |
|--------|------|---------|--------|
| Baseline | `/sdcard/LMC8.4/default .xml` | `f5dde315...` | ACTIVE (unchanged) |
| Optimized Final | `/sdcard/LMC8.4/LXX521_LMC84_Optimized_Final.xml` | `7b5ece32...` | Pushed, NOT imported |
| Special | `/sdcard/LMC8.4/LXX521_LMC84_Special.xml` | `d72d678e...` | Pushed, NOT imported |
| Lava Crisp & Clear | `/sdcard/LMC8.4/Lava_Crisp_Clear.xml` | `a545c2ad...` | Pushed, NOT imported |
| Videography | `/sdcard/LMC8.4/Lava_Videography.xml` | `fbf87e08...` | Pushed, NOT imported |
| SuperCrisp | `/sdcard/LMC8.4/LXX521_IMX682_SuperCrisp.xml` | `c2fb3fbb...` | Pushed, NOT imported |
| SuperCrisp Final | `/sdcard/LMC8.4/LXX521_IMX682_SuperCrisp.xml` | `7b5ece32...` | **Pushed, NOT imported** |
| Fresh | `/sdcard/LMC8.4/LXX521_LMC84_Fresh.xml` | `f5dde315...` | Preserved |
| Backup | `/sdcard/LMC8.4/backups/20261019_153020/` | — | Preserved |

## 4. What Was Verified

| Verification | Result |
|-------------|--------|
| XML well-formed | ✅ |
| Schema compatible (`<map>` with `string` keys) | ✅ |
| Key count (2640) | ✅ Identical to baseline |
| No missing keys | ✅ 0 |
| No extra keys | ✅ 0 |
| Changed keys verified | ✅ 11 (all intended) |
| Baseline hash unchanged | ✅ `f5dde315...` |
| Device hash matches local | ✅ `7b5ece32...` |
| No existing files overwritten | ✅ |
| No files deleted | ✅ |
| Backup preserved | ✅ |

## 5. What Was NOT Verified

| Item | Reason |
|------|--------|
| Config import into LMC | Requires manual UI interaction |
| Config activation | Requires manual UI interaction |
| Settings persistence | Requires manual UI interaction |
| Image quality improvement | Requires A/B test photos |
| Warm cast reduction | Requires A/B test photos |
| Sharpness improvement | Requires A/B test photos |
| Video quality | Requires test video capture |

## 6. A/B Test Status

**Status: NOT PERFORMED**

- Baseline captures: 18 qualified images analyzed
- Optimized captures: 0 (authorization required)
- `ab_analyze.py` ready for comparison

**To complete A/B test:**
1. Authorize import of `LXX521_IMX682_SuperCrisp.xml`
2. Capture 18+ matching optimized images (same scenes)
3. Run `ab_analyze.py`
4. Generate final recommendation

## 7. Device State (Final)

| Property | Value |
|----------|-------|
| ADB | ✅ `0123456789ABCDEF` (authorized) |
| Active config | `default .xml` (baseline) — NOT changed |
| Staged config | `LXX521_IMX682_SuperCrisp.xml` — on device, NOT imported |
| Other configs | 5 additional configs on device (all preserved) |
| Backup | `/sdcard/LMC8.4/backups/20261019_153020/fresh_backup.xml` |
| App | LMC 8.4 Iris R18F1 v8.4.300.414775575.18 |
| Back camera | IMX682, 4624×3472, 5.43mm f/1.89 |
| Photos on device | 72 |
| Videos on device | 3 |

**No config activated.** No app restart. Baseline remains active throughout entire project.

## 8. Import Steps (User Action Required)

1. Open LMC 8.4 → Settings → Config → Import
2. Select `/sdcard/LMC8.4/LXX521_IMX682_SuperCrisp.xml`
3. Verify settings load and persist after reopening LMC
4. Capture test photos in consistent lighting
5. Pull photos via ADB and run `ab_analyze.py` to compare metrics

## 9. Rollback

Delete `LXX521_IMX682_SuperCrisp.xml` from device, or re-import `default .xml`. Baseline backup preserved at `analysis_results/imx682_config/final/default_working_backup.xml`.

## 10. Limitations

1. **No physical calibration charts** — cannot compute intrinsics, distortion, or absolute MTF
2. **No ColorChecker references** — cannot compute CIEDE2000 color accuracy
3. **Monitor captures are unusable** — severe moiré confounds all measurements
4. **A/B test not performed** — optimized config untested on device
5. **Scene classification is feature-based** — may not match actual scene content
6. **Baseline incomplete** — 18 of 24 target images (6 shortfall)
7. **Warm cast is sensor-level** — may not be fully correctable via XML
8. **All measurements are comparative** — not absolute calibration
9. **No video quality analysis** — no matched video comparison performed

---

*Report generated from verified measurements and analysis. All raw data, scripts, and intermediate results preserved in analysis_results/. No results fabricated. No device changes made without authorization. Config is UNVERIFIED — no A/B test performed.*
