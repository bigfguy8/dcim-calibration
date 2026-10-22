# A/B Test Report — IMX682 Config Variants

## Status: TEST PLAN READY — AWAITING CAPTURE

### Device & App Verification
- **Device:** LAVA LXX521 (Lava Play Ultra), Android 15, SDK 35
- **Camera App:** LMC 8.4 Iris R18F1, v8.4.300.414775575.18
- **Config compatibility:** VERIFIED — all 4 XMLs are 2640-key `<map>` schema matching device baseline
- **Original backup hash:** D592BED3FE5C7F79CB0109F3EA27335BC8AB6E011D7E224C9D518E9AEFC08102 (unchanged)

### Test Plan

#### Scenes Required (consistent across all 4 configs)
1. **Indoor neutral gray card** — AWB warm cast measurement (R-G, R/B ratio)
2. **Outdoor daylight** — HDR, dynamic range, color accuracy
3. **Low light (EV < 6)** — noise, NR artifacts, shadow detail
4. **Textured detail (fabric/leaves)** — sharpness, edge density, halos
5. **Backlit portrait** — skin tone, highlight retention

#### Procedure
1. Push config to `/sdcard/LMC8.4/` via ADB
2. Open LMC → Settings → Load config → select XML
3. Capture 3 photos per scene (9 total per config, 36 total)
4. Pull photos to `device_tests/<config_name>/`
5. Run `unified_analysis.py` on each batch
6. Compare metrics across configs

#### Configs to Test
| Config | File | Key Differences |
|--------|------|-----------------|
| Original (baseline) | original_V2_Release_Day.xml | cw_rg=0.4200, sharp=+2, NR=+1, HDR=enhanced |
| Balanced | balanced.xml | Same as original (V2 Release) |
| Detail | detail.xml | sharp=+3, NR=0 |
| Low Light | lowlight.xml | NR=+2, sharp=0 |

### Missing for Execution
- User authorization to push configs to device
- User to capture test photos in consistent conditions
- Physical capture session (cannot be automated remotely)

### A/B Comparison Template (to be filled after capture)
| Metric | Original | Balanced | Detail | Low Light | Winner |
|--------|----------|----------|--------|-----------|--------|
| R-G warm cast | — | — | — | — | — |
| Black clip % | — | — | — | — | — |
| White clip % | — | — | — | — | — |
| Edge density | — | — | — | — | — |
| MTF50 cyc/px | — | — | — | — | — |
| Lum noise (std) | — | — | — | — | — |
| R/B ratio | — | — | — | — | — |
