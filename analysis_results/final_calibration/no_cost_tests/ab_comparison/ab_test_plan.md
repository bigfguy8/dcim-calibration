# IMX682 A/B Configuration Test Plan — LMC 8.4

**Date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15, SDK 35
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Sensor:** Sony IMX682, rear 5.43mm f/1.89

## 1. Configs Under Test

| Config | File | SHA-256 | Active? |
|--------|------|---------|---------|
| Baseline (Control) | `default .xml` (on device) | `f5dde315...` | ✅ YES (currently active) |
| Optimized (Treatment) | `LXX521_LMC84_Optimized_Corrected.xml` (on device) | `a5d98309...` | ❌ NO (staged, not imported) |

### 4 Changes in Optimized
| Key | Baseline | Optimized | Expected Effect |
|-----|----------|-----------|-----------------|
| cw_rg_key | 0.5925 | 0.4500 | Reduce warm cast (R-G) |
| lib_sharpnessb_key | 0 | 2 | Moderate sharpening |
| lib_sharpgain_key | 0 | 2 | Sharpening gain |
| lib_sharpmini_key | 0 | 2 | Micro-sharpening |

## 2. Test Scenes (Natural, No Charts)

| # | Scene Type | Description | Why Selected |
|---|-----------|-------------|--------------|
| 1 | Fine texture (fabric/leaves) | Close-up of textured surface | Tests sharpening, detail retention, halos |
| 2 | Foliage (outdoor) | Tree leaves against sky | Tests green color, edge sharpness, WB |
| 3 | Text (sign/book) | Printed text at readable distance | Tests sharpening, contrast, halos |
| 4 | Indoor mixed lighting | Room with window + artificial light | Tests WB, HDR, dynamic range |
| 5 | Neutral objects | Gray/white surfaces (wall, paper) | Tests warm cast, color consistency |
| 6 | Bright highlights | Window/sky in frame | Tests highlight retention, clipping |
| 7 | Low light | Dim indoor scene (EV < 3) | Tests noise, NR, shadow detail |
| 8 | Skin tone (if available) | Portrait in consistent light | Tests color accuracy, skin rendering |

## 3. Capture Protocol

### Per Scene
1. **Verify active config** in LMC Settings → Config
2. **Set up scene** (consistent framing, lighting, focus)
3. **Capture 3 images** with baseline config
4. **Record metadata** (EV, ISO, shutter, aperture, distance, lighting)
5. **Switch to optimized config** (after authorization)
6. **Capture 3 images** with optimized config (same scene)
7. **Record metadata**

### Consistency Requirements
- Same phone position (tripod or stable handhold)
- Same focus point (tap to focus on same object)
- Same lighting (avoid changing conditions between configs)
- Same framing (use grid overlay if available)
- Same time of day (for outdoor scenes)
- Wait 2-3 seconds between captures for stabilization

### Metadata Recording Template

| Field | Baseline | Optimized |
|-------|----------|-----------|
| Scene # | | |
| Chart/Scene name | | |
| Image filename | | |
| ISO | | |
| Shutter (s) | | |
| Aperture | | |
| EV | | |
| Focal length | | |
| Distance (cm) | | |
| Lighting (lux/K) | | |
| Notes | | |

## 4. Comparison Metrics

### Quantitative (from unified_analysis.py)
| Metric | What It Measures | Baseline Target | Optimized Target |
|--------|-----------------|-----------------|------------------|
| R-G (warm cast) | White balance | +5.7 mean | <4.0 (target) |
| R/B ratio | Color neutrality | 1.041 mean | Closer to 1.0 |
| Black clip % | Shadow detail | 10.64% mean | ≤ baseline |
| White clip % | Highlight retention | 5.36% mean | ≤ baseline |
| Edge density | Sharpness/detail | 0.0296 mean | ≥ baseline |
| Lum std (noise) | Noise level | varies | ≤ baseline |
| MTF50 | Relative sharpness | 0.001 (floor) | Not actionable |

### Qualitative (Visual Assessment)
| Aspect | What to Check |
|--------|---------------|
| Sharpening halos | White/black fringes around edges |
| Noise texture | Grain in flat areas (sky, walls) |
| Color naturalness | Skin tones, foliage, sky color |
| Detail retention | Fine texture preservation without artifacts |
| Exposure balance | Highlight/shadow balance |
| Overall impression | Which looks better? |

## 5. Analysis Protocol

### Per Scene Pair
1. Pull both baseline and optimized images via ADB
2. Run `unified_analysis.py` on each set
3. Compare metrics side-by-side
4. Visual inspection for artifacts
5. Record which config wins per metric

### Statistical Comparison
- Use median (not mean) for robustness against outliers
- Report min/max range for uncertainty
- Flag scenes where results are inconsistent (scene-dependent)
- Require consistent improvement across ≥3 scenes for recommendation

### Decision Criteria
| Outcome | Recommendation |
|---------|---------------|
| Optimized wins on ≥5 of 8 metrics across ≥3 scenes | Recommend optimized config |
| Mixed results (some better, some worse) | Recommend selective changes only |
| Optimized worse on ≥3 metrics | Recommend rollback to baseline |
| No consistent difference | Keep baseline (no benefit) |

## 6. Authorization Required

**Before importing optimized config:**
1. Baseline captures must be complete and saved
2. User must explicitly authorize config switch
3. Active config must be verified before each capture

**Config switch procedure:**
1. LMC → Settings → Config → Import → select `LXX521_LMC84_Optimized_Corrected.xml`
2. Verify active config in Settings
3. Capture optimized images
4. (Optional) Switch back to baseline after testing

## 7. Files to Save

| File | Purpose |
|------|---------|
| `ab_comparison/baseline/` | Baseline capture images |
| `ab_comparison/optimized/` | Optimized capture images |
| `ab_comparison/ab_metrics.csv` | Side-by-side metrics |
| `ab_comparison/ab_report.md` | Comparison report |
| `ab_comparison/plots/` | Comparison plots |
| `ab_comparison/image_pairs/` | Side-by-side image pairs |

## 8. Important Constraints

- **Do NOT switch configs without authorization**
- **Do NOT claim improved optical sharpness** — MTF50 is floor-level
- **Do NOT claim sensor-level correction** — warm cast is sensor characteristic
- **Do NOT use monitor captures** for A/B comparison (moiré confounds)
- **Report only repeatable improvements** — single-image differences are noise
- **If optimized is worse, recommend rollback** to baseline

## 9. Current Status

| Item | Status |
|------|--------|
| ADB connected | ✅ 0123456789ABCDEF |
| Baseline active | ✅ `default .xml` |
| Optimized on device | ✅ Pushed, NOT imported |
| Baseline captures | ❌ Not started |
| Optimized captures | ❌ Not started |
| Analysis | ❌ Not started |

**Authorization required** before importing optimized config or switching active settings.
