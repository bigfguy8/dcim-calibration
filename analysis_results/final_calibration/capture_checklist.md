# IMX682 Calibration Capture Plan — LMC 8.4 Iris R18F1

**Device:** LAVA LXX521 (Lava Play Ultra), Android 15, SDK 35
**Sensor:** Sony IMX682, rear 5.43mm f/1.89, front 3.59mm, UW 1.98mm
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Working Baseline:** Desktop `default .xml` (SHA-256 `f5dde315...`)
**Optimized Config:** `LXX521_LMC84_Optimized_Corrected.xml` (SHA-256 `a5d98309...`)

## 1. Phone State Verification (Before Capturing)

| Check | Method | Expected |
|-------|--------|----------|
| Active LMC config | LMC app → Settings → Config | Verify which XML is loaded (baseline vs optimized) |
| Camera resolution | LMC app → Settings → Photo resolution | Note max resolution (likely 4624×3468) |
| Active lens | EXIF of test capture | FocalLength = 5.43mm (rear IMX682) |
| HDR+ status | EXIF Software field | `HDR+ 1.0.414775603zdy` |
| AWB preset | EXIF WhiteBalance tag | Check current AWB mode |
| Config import directory | `/sdcard/LMC8.4/` | Verify all XML files present |

## 2. Required Charts & Reference Materials

| Chart Type | Specification | Purpose | Notes |
|------------|---------------|---------|-------|
| Checkerboard | 8×6 or 9×6 squares, known square size (e.g., 20mm), matte print | Camera intrinsics, distortion, perspective | Print on matte paper, mount on flat board |
| ISO 12233 Slanted-Edge | Slanted-edge target (5°), multiple edges | MTF50, sharpness | Print or display at native resolution |
| Siemens Star | Multiple star patterns | Resolution, aliasing | High-contrast target |
| ColorChecker | 24-patch, verified reference values (sRGB or XYZ) | Color accuracy, CIEDE2000, WB | X-Rite ColorChecker Passport or equivalent |
| Neutral Gray | 18% gray card, multiple exposures | White balance calibration, exposure | Lambertian surface |
| White Reference | White card (90%+) | White point, clipping | Lambertian surface |

**Important:** Do NOT use monitor-displayed charts as precision references unless:
- Monitor geometry is verified (no pixel structure aliasing)
- Color output is calibrated (known white point, gamma)
- Chart is photographed perpendicular to screen with no moiré

## 3. Capture Checklist

### Phase 1: Intrinsic Calibration (Checkerboard)
- [ ] Print 8×6 or 9×6 checkerboard on matte paper (known square size in mm)
- [ ] Mount on flat rigid board
- [ ] Capture 15-20 images at varied:
  - Distances: 30cm, 50cm, 80cm, 120cm
  - Angles: 0°, ±15°, ±30° yaw/pitch
  - Positions: center, corners, edges of frame
  - Lighting: even, no glare, no shadows
- [ ] Config: Baseline (`default .xml`) — verify active before capture

### Phase 2: Sharpness / MTF (ISO 12233 + Siemens Star)
- [ ] Print ISO 12233 slanted-edge chart
- [ ] Capture at multiple focus distances (MF if available)
- [ ] Capture Siemens star at center and off-center
- [ ] Lighting: even, no shadows on target
- [ ] Config: Baseline first, then Optimized_Corrected (matched scenes)

### Phase 3: Color Accuracy (ColorChecker + Gray Card)
- [ ] Place 24-patch ColorChecker under D65 (6500K) or daylight
- [ ] Place 18% gray card adjacent
- [ ] Capture multiple exposures (±1 EV around correct)
- [ ] Capture white reference card
- [ ] Config: Baseline first, then Optimized_Corrected

### Phase 4: Exposure & Clipping (EV Bracket)
- [ ] Fixed scene, capture -2, -1, 0, +1, +2 EV
- [ ] Fixed ISO and aperture, vary shutter
- [ ] Config: Baseline first, then Optimized_Corrected

### Phase 5: Noise Analysis (High ISO)
- [ ] Fixed scene, ISO 100, 200, 400, 800, 1600, 3200, 6400
- [ ] Fixed exposure, vary ISO
- [ ] Config: Baseline first, then Optimized_Corrected

### Phase 6: HDR Behavior
- [ ] High-dynamic-range scene (window + interior, or backlit subject)
- [ ] HDR+ on/off comparison
- [ ] Config: Baseline first, then Optimized_Corrected

## 4. Config Comparison Protocol

For each scene:
1. Verify active config in LMC app (check Settings → Config)
2. Capture 3 matched images per config
3. Record: EV, ISO, shutter, aperture, focus distance
4. Pull images via ADB (read-only, do not delete phone originals)
5. Compare metrics: MTF50, edge density, black/white clip, R/B ratio, noise

**Configs to compare:**
- Baseline: Desktop `default .xml` (device's working config)
- Optimized: `LXX521_LMC84_Optimized_Corrected.xml` (4 key changes)

## 5. Analysis Targets (from valid images only)

| Measurement | Required Target | Method |
|-------------|----------------|--------|
| Camera intrinsics (K matrix) | Checkerboard (15+ views) | cv2.calibrateCamera |
| Distortion coefficients (k1,k2,p1,p2,k3) | Checkerboard (15+ views) | cv2.calibrateCamera |
| MTF50 (cyc/px) | ISO 12233 slanted-edge | ESF/LSF analysis |
| Sharpness (LWPH) | Siemens star | Resolution limit |
| Color accuracy (CIEDE2000) | 24-patch ColorChecker | Compare measured vs reference |
| White balance (R-G, R/B) | 18% gray card | RGB mean in neutral region |
| Black clip % | Gray card + shadow region | Pixels ≤ 5 / total |
| White clip % | White card + highlight region | Pixels ≥ 250 / total |
| Noise (luma/chroma std) | Uniform gray patches | Std dev in flat regions |

## 6. Deliverables (analysis_results/final_calibration/)

| File | Purpose |
|------|---------|
| `capture_checklist.md` | This document |
| `capture_inventory.csv` | All captured images with EXIF |
| `intrinsics.json` | Camera matrix + distortion coefficients |
| `mtf50_results.json` | MTF50 per slanted-edge target |
| `color_accuracy.json` | CIEDE2000 per ColorChecker patch |
| `wb_results.json` | R-G, R/B per gray card |
| `exposure_results.json` | Clipping vs EV |
| `noise_results.json` | Noise vs ISO |
| `config_comparison.md` | Baseline vs Optimized A/B results |
| `final_report.md` | Complete calibration summary |
| `annotated/` | Checkerboard/Siemens star annotated images |
| `plots/` | Diagnostic plots |

## 7. Constraints & Limitations

- **No config changes without user authorization** — Baseline remains active unless explicitly authorized
- **No pushing/activating Optimized_Corrected.xml without authorization** — File is on device but not imported
- **No monitor-displayed charts as precision references** — Unless geometry and color output verified
- **No fabrication of results** — Only report what is genuinely measured
- **No claim of complete IMX682 calibration** — Requires RAW captures, controlled lighting, verified references
- **Preserve all phone originals** — Pull via ADB read-only, never delete

## 8. Next Steps (When Authorized)

1. Acquire charts (checkerboard, ISO 12233, ColorChecker, gray card)
2. Verify active config before each capture session
3. Execute capture plan in phases
4. Pull images via ADB to `analysis_results/final_calibration/`
5. Run analysis pipeline on valid targets only
6. Generate config comparison report
7. Report measured results with uncertainty

**Current state:** `LXX521_LMC84_Optimized_Corrected.xml` is on device at `/sdcard/LMC8.4/` but NOT activated. Baseline (`default .xml`) remains active.
