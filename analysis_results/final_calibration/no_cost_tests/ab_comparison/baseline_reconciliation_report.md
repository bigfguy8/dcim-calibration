# Baseline Reconciliation Report — IMX682 A/B Test

**Date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF), Android 15, SDK 35
**Camera App:** LMC 8.4 Iris R18F1 v8.4.300.414775575.18
**Sensor:** Sony IMX682, rear 5.43mm f/1.89
**Active Config:** `default .xml` (baseline) — NOT changed

## 1. File Inventory

| Property | Value |
|----------|-------|
| Total files pulled | 33 |
| Expected (8 scenes × 3) | 24 |
| Extra files | 9 |
| Unique SHA-256 hashes | 33 (no duplicates) |
| All readable | ✅ Yes |
| All dimensions | 4624×3468 (portrait, rear IMX682) |
| All lens | 5.43mm f/1.89 |
| All software | HDR+ 1.0.414775603 (zdy or ndy suffix) |
| All CustomRendered | 1 (custom processing) |

## 2. EXIF Metadata Summary

### 2.1 Software Tag Analysis

| Software Tag | Count | ISO Range | EV Range | Notes |
|-------------|-------|-----------|----------|-------|
| `HDR+ 1.0.414775603zdy` | 19 | 399-1552 | -0.78 to 3.33 | Normal HDR+ processing |
| `HDR+ 1.0.414775603ndy` | 14 | 442-25500 | -5.99 to 2.65 | Unusual suffix — possible night/long-exposure mode |

**Investigation of "ndy" suffix:**
- All 14 "ndy" images have CustomRendered=1 (custom processing)
- 5 of 14 have impossible ISO values (15,094-25,500) and very negative EV (-5.2 to -6.0)
- These 5 have exposure times of 0.25s (1/4s) — long exposure
- BrightnessValue ranges -9.08 to -5.0 (very dark scenes)
- Likely captured in a **night mode or long-exposure capture mode** within LMC
- The "ndy" suffix may indicate a different HDR+ processing variant (night HDR+)

**Conclusion:** The "ndy" suffix is a genuine EXIF value from LMC's HDR+ pipeline, indicating a different processing mode (likely night/long-exposure). These are NOT parsing errors. The high ISO values are composite ISO reported by the HDR+ pipeline for multi-frame captures.

### 2.2 ISO Analysis

| ISO Range | Count | Images | Assessment |
|-----------|-------|--------|------------|
| 399-900 | 12 | Normal captures | Valid for comparison |
| 901-1552 | 16 | Normal captures | Valid for comparison |
| 15,094-25,500 | 5 | Night/long-exposure captures | **Exclude from primary A/B** (different capture mode) |

**The 5 high-ISO images (17:23:06-17:24:22) are night-mode captures** with 0.25s exposure, very dark scenes (BrightnessValue -9.08 to -5.0), and impossible real ISO values. These represent a different capture mode and should not be compared with standard captures.

### 2.3 Exposure Analysis

| Time Group | Count | EV Range | ISO Range | Software | Assessment |
|------------|-------|----------|-----------|----------|------------|
| 17:20:24-17:20:44 | 4 | 0.549-1.837 | 442-1453 | Mixed | Standard captures |
| 17:21:01-17:21:37 | 8 | -0.783 to 3.327 | 498-1929 | Mixed | Standard captures |
| 17:22:02-17:22:34 | 8 | 0.103-1.648 | 638-1552 | Mixed | Standard captures |
| 17:23:06-17:24:22 | 5 | -5.994 to -5.238 | 15094-25500 | All ndy | **Night mode — exclude from primary** |
| 17:24:51-17:25:14 | 8 | 1.335-3.060 | 399-793 | Mixed | Standard captures |

## 3. Scene Grouping (Uncertain Assignments)

Based on timestamps, EXIF, and visual content (from contact sheet), the 33 images are tentatively grouped into time-based batches. **Scene assignments are uncertain** — visual content analysis would be needed for confirmation.

### Likely Scene Groups (by time proximity)

| Group | Time Range | Images | Count | Likely Scene |
|-------|------------|--------|-------|--------------|
| A | 17:20:24-17:20:44 | 4 | 4 | Unknown (possibly Scene 1-2) |
| B | 17:21:01-17:21:37 | 8 | 8 | Unknown (possibly Scene 3-4) |
| C | 17:22:02-17:22:34 | 8 | 8 | Unknown (possibly Scene 5-6) |
| D | 17:23:06-17:24:22 | 5 | 5 | Night mode (likely Scene 7) |
| E | 17:24:51-17:25:14 | 8 | 8 | Unknown (possibly Scene 8) |

**Note:** These groupings are based on time proximity only. Visual content analysis would be needed to confirm which images belong to which of the 8 planned scenes. Some groups have more than 3 images, suggesting additional test shots or burst captures.

### Images per Group

**Group A (17:20:24-17:20:44) — 4 images:**
1. 20261019_172024_lmc_8.4.jpg (ISO=442, EV=1.178, R-G=-10.9)
2. 20261019_172034_lmc_8.4.jpg (ISO=560, EV=1.837, R-G=-5.5)
3. 20261019_172038_lmc_8.4.jpg (ISO=1367, EV=0.549, R-G=-7.8)
4. 20261019_172044_lmc_8.4.jpg (ISO=1453, EV=0.783, R-G=-1.9)

**Group B (17:21:01-17:21:37) — 8 images:**
5. 20261019_172101_lmc_8.4.jpg (ISO=1929, EV=0.052, R-G=-18.8)
6. 20261019_172103_lmc_8.4.jpg (ISO=610, EV=0.865, R-G=-17.3)
7. 20261019_172106_lmc_8.4.jpg (ISO=618, EV=0.846, R-G=-17.9)
8. 20261019_172116_lmc_8.4.jpg (ISO=498, EV=3.327, R-G=1.7)
9. 20261019_172124_lmc_8.4.jpg (ISO=461, EV=2.855, R-G=-0.8)
10. 20261019_172126_lmc_8.4.jpg (ISO=472, EV=2.821, R-G=-1.3)
11. 20261019_172134_lmc_8.4.jpg (ISO=1434, EV=-0.783, R-G=6.2)
12. 20261019_172137_lmc_8.4.jpg (ISO=1217, EV=-0.662, R-G=4.8)

**Group C (17:22:02-17:22:34) — 8 images:**
13. 20261019_172202_lmc_8.4.jpg (ISO=1072, EV=0.9, R-G=-6.6)
14. 20261019_172207_lmc_8.4.jpg (ISO=638, EV=1.648, R-G=-5.5)
15. 20261019_172224_lmc_8.4.jpg (ISO=1053, EV=0.925, R-G=-15.5)
16. 20261019_172225_lmc_8.4.jpg (ISO=1008, EV=0.989, R-G=-15.4)
17. 20261019_172225_lmc_8.4__1_.jpg (ISO=901, EV=1.15, R-G=-17.9)
18. 20261019_172226_lmc_8.4.jpg (ISO=899, EV=1.154, R-G=-17.7)
19. 20261019_172231_lmc_8.4.jpg (ISO=824, EV=0.279, R-G=-16.9)
20. 20261019_172234_lmc_8.4.jpg (ISO=1552, EV=0.103, R-G=-15.6)

**Group D (17:23:06-17:24:22) — 5 images (NIGHT MODE):**
21. 20261019_172306_lmc_8.4.jpg (ISO=24219, EV=-5.92, R-G=1.5)
22. 20261019_172334_lmc_8.4.jpg (ISO=15094, EV=-5.238, R-G=0.8)
23. 20261019_172342_lmc_8.4.jpg (ISO=25500, EV=-5.994, R-G=0.9)
24. 20261019_172405_lmc_8.4.jpg (ISO=25500, EV=-5.994, R-G=-1.2)
25. 20261019_172422_lmc_8.4.jpg (ISO=23349, EV=-5.867, R-G=1.5)

**Group E (17:24:51-17:25:14) — 8 images:**
26. 20261019_172451_lmc_8.4.jpg (ISO=612, EV=3.029, R-G=8.7)
27. 20261019_172452_lmc_8.4.jpg (ISO=617, EV=3.018, R-G=10.9)
28. 20261019_172453_lmc_8.4.jpg (ISO=599, EV=3.06, R-G=11.3)
29. 20261019_172454_lmc_8.4.jpg (ISO=606, EV=3.043, R-G=10.8)
30. 20261019_172512_lmc_8.4.jpg (ISO=792, EV=1.336, R-G=-8.0)
31. 20261019_172513_lmc_8.4.jpg (ISO=793, EV=1.335, R-G=-8.5)
32. 20261019_172514_lmc_8.4.jpg (ISO=792, EV=1.336, R-G=-9.8)
33. 20261019_172514_lmc_8.4__1_.jpg (ISO=399, EV=2.647, R-G=-12.1)

## 4. Quality Assessment

### 4.1 Suitable for Baseline Comparison (28 images)

| Group | Count | Assessment |
|-------|-------|------------|
| A | 4 | Standard captures, valid for comparison |
| B | 8 | Standard captures, valid for comparison |
| C | 8 | Standard captures, valid for comparison |
| E | 8 | Standard captures, valid for comparison |

**Total suitable: 28 images**

### 4.2 Excluded from Primary Comparison (5 images)

| Group | Count | Reason |
|-------|-------|--------|
| D (night mode) | 5 | Impossible ISO (15K-25K), very negative EV (-5.2 to -6.0), 0.25s exposure, night/long-exposure mode |

**Retained in audit but excluded from A/B comparison.**

### 4.3 Image Quality Flags

| Flag | Count | Images |
|------|-------|--------|
| High edge density (>0.15) | 6 | 172124, 172126, 172202, 172207, 172231, 172234 |
| Very dark (black clip >20%) | 6 | 172306, 172334, 172342, 172405, 172422, 172044 |
| Very warm (R-G >+8) | 4 | 172451, 172452, 172453, 172454 |
| Very cool (R-G <-10) | 5 | 172101, 172103, 172106, 172224, 172225, 172225__1_, 172226, 172231, 172234, 172514__1_ |
| Low edge density (<0.05) | 7 | 172116, 172306, 172334, 172342, 172405, 172422, 172514__1_ |

## 5. Recommendations

### 5.1 For A/B Baseline Comparison
- **Use 28 standard captures** (Groups A, B, C, E)
- **Exclude 5 night-mode captures** (Group D) from primary comparison
- **Group by time proximity** for scene identification
- **Use median (not mean)** for robustness against outliers

### 5.2 Scene Identification Needed
The 28 standard captures need to be grouped into 8 scenes (3 each = 24) with 4 extra. Visual inspection of contact sheet is needed to identify which images belong to which scene.

### 5.3 Config State
- **Active:** `default .xml` (baseline) — NOT changed
- **Staged:** `LXX521_LMC84_Optimized_Corrected.xml` — NOT imported
- **No config switch performed**

### 5.4 Next Steps
1. **Visual inspection** of contact sheet to identify 8 scenes
2. **Group 24 images** into 8 scenes (3 each)
3. **Mark 4 extra** images as test shots
4. **Run baseline analysis** on 24 qualified images
5. **Request authorization** for optimized config import
6. **Capture 24 optimized images** (same scenes)
7. **Run A/B comparison**

## 6. Files Generated

| File | Purpose |
|------|---------|
| `baseline_inventory.json` | Full EXIF + metadata for 33 images |
| `baseline_contact_sheet.png` | Visual contact sheet |
| `baseline_inventory_text.png` | Text inventory |
| `baseline_reconciliation_report.md` | This report |
| `ab_baseline_analysis.md` | Earlier analysis (superseded) |

## 7. Config State (Unchanged)

| Config | Status | SHA-256 |
|--------|--------|---------|
| `default .xml` | ACTIVE (baseline) | `f5dde315...` |
| `LXX521_LMC84_Optimized_Corrected.xml` | STAGED, NOT imported | `a5d98309...` |

**No config activated.** No app restart. Baseline remains active.
**Authorization required** before importing optimized config.
