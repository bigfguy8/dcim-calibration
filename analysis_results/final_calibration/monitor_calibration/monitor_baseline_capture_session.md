# Monitor Calibration Baseline Capture Session

**Session date:** 2026-10-19
**Device:** LAVA LXX521 (serial: 0123456789ABCDEF)
**Active config:** `default .xml` (baseline) — NOT changed
**Staged config:** `LXX521_LMC84_Optimized_Corrected.xml` — NOT imported

## Pre-Capture Checklist

- [ ] Acer monitor at native 1920×1080 @ 120Hz
- [ ] HDR disabled on monitor
- [ ] Dynamic contrast disabled
- [ ] Night mode / blue light filter disabled
- [ ] Auto-brightness disabled
- [ ] Brightness set to fixed level (record below)
- [ ] Color temperature set to 6500K (record below)
- [ ] DPI scaling at 100%
- [ ] No taskbar/overlays visible
- [ ] Phone perpendicular to screen, centered
- [ ] Distance measured and recorded
- [ ] Room dimmed (screen as sole light source)
- [ ] LMC active config verified as `default .xml`

## Display Settings (Record Before Capture)

| Setting | Value |
|---------|-------|
| Monitor model | Acer (ACR0FDD) |
| Resolution | 1920×1080 |
| Refresh rate | 120 Hz |
| Brightness | ___ (record) |
| Contrast | ___ (record) |
| Color temperature | ___ (record) |
| HDR | Off |
| Dynamic contrast | Off |
| Night mode | Off |
| Auto-brightness | Off |

## Capture Log Template

| # | Chart File | Image Filename | Distance (cm) | ISO | Shutter (s) | Aperture | EV | Focus | Notes |
|---|-----------|----------------|---------------|-----|-------------|----------|-----|-------|-------|
| 1 | monitor_checkerboard_15x8.png | | | | | | | | |
| 2 | monitor_checkerboard_15x8.png | | | | | | | | |
| 3 | monitor_checkerboard_15x8.png | | | | | | | | |
| 4 | monitor_slanted_edge_5deg.png | | | | | | | | |
| 5 | monitor_slanted_edge_5deg.png | | | | | | | | |
| 6 | monitor_slanted_edge_5deg.png | | | | | | | | |
| 7 | monitor_siemens_star_36.png | | | | | | | | |
| 8 | monitor_siemens_star_36.png | | | | | | | | |
| 9 | monitor_siemens_star_36.png | | | | | | | | |
| 10 | monitor_grayscale_wedge_11.png | | | | | | | | |
| 11 | monitor_grayscale_wedge_11.png | | | | | | | | |
| 12 | monitor_grayscale_wedge_11.png | | | | | | | | |
| 13 | monitor_color_patches_24.png | | | | | | | | |
| 14 | monitor_color_patches_24.png | | | | | | | | |
| 15 | monitor_color_patches_24.png | | | | | | | | |

## Capture Procedure

### Step 1: Verify Active Config
1. Open LMC 8.4 → Settings → Config
2. Confirm `default .xml` is active
3. If not, do NOT proceed — report discrepancy

### Step 2: Display Chart
1. Open chart PNG in full-screen image viewer
2. Verify no taskbar, overlays, or scaling
3. Confirm chart fills entire screen

### Step 3: Position Phone
1. Hold phone perpendicular to screen center
2. Measure distance from phone to screen (cm)
3. Center chart in frame
4. Focus on chart center (AF or MF)

### Step 4: Capture
1. Capture 3 images per chart
2. Wait 2-3 seconds between captures for stabilization
3. Check EXIF for ISO, shutter, aperture, EV

### Step 5: Record
1. Note filename, distance, and any issues
2. Check for moiré, glare, reflections
3. If issues present, reposition and recapture

### Step 6: Repeat for Each Chart
1. Close current chart
2. Open next chart full-screen
3. Repeat steps 3-5

## Post-Capture
1. Pull all new photos via ADB (read-only)
2. Run analysis pipeline on pulled images
3. Document moiré, artifacts, unsuitable captures
4. Save results to `monitor_calibration/captures/`

## Important Notes

- **Do NOT import optimized config** during baseline session
- **Do NOT change active config** without authorization
- **Do NOT delete phone originals** — pull copies only
- **Record all metadata** — distance, brightness, exposure
- **Check for moiré** on each capture — reposition if severe
- **All measurements are comparative** — not absolute calibration

## A/B Testing (After Baseline Complete)

Once baseline captures are safely stored:
1. Request authorization to import `LXX521_LMC84_Optimized_Corrected.xml`
2. Repeat identical capture sequence with optimized config
3. Compare metrics between baseline and optimized
4. Report which config performs better per measurement
