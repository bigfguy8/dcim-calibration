# Config Validation Report — LXX521_LMC84_Optimized.xml

## Validation Status: PASS (with caveats)

### Syntax Validation
- XML is well-formed
- Schema: `<map>` with `<string name="..." value="..."/>` entries (LMC 8.4 compatible)
- Key count: 2640 (identical to baseline)
- File size: 143,969 bytes (identical to baseline)
- SHA-256: `f08ae28f1d86c15a1c85819777b73e4451383696da487448f056eb289ce110bb`
- Baseline SHA-256: `d592bed3fe5c7f79cb0109f3ea27335bc8ab6e011d7e224c9d518e9aefc08102`
- Different from baseline: YES (4 keys changed)

### Schema Compatibility
- Target: LMC 8.4 Iris R18F1 (com.samsung.android.server.iris), v8.4.300.414775575.18
- Config format: `<map>` schema with `lib_*`/`pref_*` keys
- Baseline source: Genuine device baseline exported from `/sdcard/LMC8.4/default .xml`
- All 2640 keys present and preserved
- No undocumented or invented keys
- All changed keys exist in baseline with verified data types

### Parameter Range Checks
| Parameter | Old Value | New Value | Valid Range | Status |
|-----------|-----------|-----------|-------------|--------|
| cw_rg_key | 0.5925 | 0.4500 | 0.0-1.0 | PASS |
| lib_sharpnessb_key | 1 | 2 | -10 to +10 | PASS |
| lib_sharpgain_key | 1 | 2 | -10 to +10 | PASS |
| lib_sharpmini_key | 1 | 2 | -10 to +10 | PASS |

### App Version Compatibility
- Config exported from LMC 8.4 Iris R18F1 on device
- All keys are from the genuine device baseline
- Config is ready for import via LMC Settings → Import config
- Not yet tested on device (import not performed without authorization)

### Caveats
1. Warm cast (+3.3 to +6.8 R-G) is sensor-level — XML tuning may not fully correct it
2. MTF50 measurements are from JPEG captures — include ISP processing and monitor pixel structure
3. No ColorChecker reference values — CIEDE2000 color accuracy not validated
4. Config not yet imported or tested on device — all changes are evidence-based estimates
5. cw_rg_key_2 through cw_rg_key_5 remain at 0.4200 (baseline) — per-camera consistency unknown

### Rollback Procedure
1. On device: Settings → LMC → Delete config or re-import baseline
2. Or via ADB: `adb shell rm /sdcard/LMC8.4/LXX521_LMC84_Optimized.xml`
3. Re-import baseline: `adb push original_V2_Release_Day.xml /sdcard/LMC8.4/`
4. Restart LMC app
5. Verify: check EXIF Software field for `HDR+ 1.0.414775603zdy`

### Deployment Steps (When Authorized)
1. Connect device via ADB
2. Push config: `adb push LXX521_LMC84_Optimized.xml /sdcard/LMC8.4/`
3. Open LMC app → Settings → Load config
4. Select `LXX521_LMC84_Optimized.xml`
5. Capture test photos in consistent lighting
6. Pull photos and run unified_analysis.py to compare metrics
