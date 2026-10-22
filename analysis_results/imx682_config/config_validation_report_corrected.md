# Config Validation Report — LXX521_LMC84_Optimized_Corrected.xml

## Validation Status: PASS

### Syntax Validation
- XML is well-formed
- Schema: `<map>` with `<string name="..." value="..."/>` entries (LMC 8.4 compatible)
- Key count: 2640 (identical to Desktop working baseline)
- File size: matches baseline within expected delta for 4 value changes
- SHA-256: `a5d98309bdacad6a1f640fb016d4423036a2b85682545c5002f9b8677d4785cd`
- Desktop baseline SHA-256: `f5dde315f71bb4c28f72ea0b2a5cd3b5385f2e4aeb12b7463416174acb1b5f49`
- Different from baseline: YES (exactly 4 keys changed)

### Schema Compatibility
- Target: LMC 8.4 Iris R18F1 (com.samsung.android.server.iris), v8.4.300.414775575.18
- Config format: `<map>` schema with `lib_*`/`pref_*` keys
- Baseline source: Desktop `default .xml` (matches device `/sdcard/LMC8.4/default .xml`, SHA-256 `f5dde315...`)
- All 2640 keys present and preserved
- No missing keys, no extra keys
- No undocumented or invented keys
- All changed keys exist in baseline with verified data types

### Parameter Range Checks
| Parameter | Old Value | New Value | Valid Range | Status |
|-----------|-----------|-----------|-------------|--------|
| cw_rg_key | 0.5925 | 0.4500 | 0.0-1.0 | PASS |
| lib_sharpnessb_key | 0 | 2 | -10 to +10 | PASS |
| lib_sharpgain_key | 0 | 2 | -10 to +10 | PASS |
| lib_sharpmini_key | 0 | 2 | -10 to +10 | PASS |

### App Version Compatibility
- Config derived from genuine device working baseline (`default .xml`)
- All keys are from the genuine device baseline
- Config is ready for import via LMC Settings → Import config
- Not yet tested on device (import not performed without authorization)

### Caveats
1. Warm cast (+3.3 to +6.8 R-G) is sensor-level — XML tuning may not fully correct it
2. MTF50 measurements are from JPEG captures — include ISP processing and monitor pixel structure
3. No ColorChecker reference values — CIEDE2000 color accuracy not validated
4. Config not yet imported or tested on device — all changes are evidence-based estimates

### Rollback Procedure
1. On device: Settings → LMC → Delete config or re-import baseline
2. Or via ADB: `adb shell rm /sdcard/LMC8.4/LXX521_LMC84_Optimized_Corrected.xml`
3. Re-import baseline: Desktop `default .xml` → `/sdcard/LMC8.4/default .xml`
4. Restart LMC app
5. Verify: check EXIF Software field for `HDR+ 1.0.414775603zdy`

### Deployment Steps (When Authorized)
1. Connect device via ADB
2. Push config: `adb push LXX521_LMC84_Optimized_Corrected.xml /sdcard/LMC8.4/`
3. Open LMC app → Settings → Load config
4. Select `LXX521_LMC84_Optimized_Corrected.xml`
5. Capture test photos in consistent lighting
6. Pull photos and run unified_analysis.py to compare metrics
