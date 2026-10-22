# IMX682 Calibration — Capture Session Setup
**Device:** LAVA LXX521 (IMX682, Android 15) | **App:** LMC8.4 R18F1 Iris
**Chart:** Monitor-based calibration chart (1920×1440)

---

## Quick Summary of What We've Learned

| Finding | Value |
|---------|-------|
| Best MTF50 | 0.1438 cyc/px (345 LWPH) at EV ~6.8 |
| Sharpness sweet spot | EV 6.8–7.4 |
| Best black clipping | LMC8.4: 2–3% vs Stock: 7–9% |
| Checkerboard detected | 4/5 photos in bracket, alternation ~0.40–0.42 (needs >0.70) |
| Chart working on monitor | ✅ Yes, checkerboards detected |

---

## Step 1: Prepare the Monitor Chart

### Display Settings
1. Open `D:\LXX521-GCam\calibration_chart_IMX682_monitor.png`
2. Set monitor to **native resolution** (1920×1440 or closest)
3. Display **full-screen** (F11 in most viewers)
4. Set scaling to **100%** (no zoom)
5. Disable blue-light filter, night mode, HDR, auto-brightness
6. Set monitor brightness to **70–80%** (fixed, not auto)
7. **Dim room lights** — reduce glare on screen

### Verify Chart is Visible
- You should see: ColorChecker patches, grayscale ramp, Siemens star, line-pair bars, slanted-edge target, checkerboard, crosshairs
- Chart should fill most of the screen with small margins

---

## Step 2: Phone Mounting

### Position
- [ ] Phone on **tripod or stable stand** (no handheld)
- [ ] Lens **perpendicular to monitor** (parallel to screen plane)
- [ ] Frame fills with chart, small margins (~5%) around edges
- [ ] Use grid lines in camera app to keep straight
- [ ] No phone case shadow on lens
- [ ] No reflections/glare on monitor visible in frame

---

## Step 3: LMC8.4 Settings

Open LMC8.4 app and verify:
- [ ] **HDR:** OFF
- [ ] **AI scene detection:** OFF
- [ ] **Beauty/filter modes:** OFF
- [ ] **Grid:** ON
- [ ] **RAW/DNG:** ON if available

---

## Step 4: Capture Sequence (13 Photos Total)

### Group A — Exposure Bracket (5 shots, center, perpendicular)
Use exposure compensation in LMC8.4:

| Shot | EV Comp | Purpose |
|------|---------|---------|
| 1 | -2 EV | Shadow detail, noise floor |
| 2 | -1 EV | Dark mid-tones |
| 3 | 0 EV | Normal reference |
| 4 | +1 EV | Bright mid-tones |
| 5 | +2 EV | Highlight clipping |

**For each shot:**
1. Frame chart centered, perpendicular
2. **Tap-to-focus on chart center** (critical!)
3. Hold steady (tripod)
4. Tap shutter
5. Move to next EV

### Group B — Angled Views (3 shots, 0 EV)
- [ ] Camera rotated ~15° LEFT (0 EV)
- [ ] Camera straight-on (0 EV) — repeat of Group A center shot
- [ ] Camera rotated ~15° RIGHT (0 EV)

### Group C — Corner Views (4 shots, 0 EV)
Move chart so each corner is near frame center:
- [ ] Top-left corner centered
- [ ] Top-right corner centered
- [ ] Bottom-left corner centered
- [ ] Bottom-right corner centered

### Group D — White Balance (1 shot, 0 EV)
- [ ] Fill frame with neutral gray card or white paper
- [ ] Same lighting as chart shots

**Total: 13 photos**

---

## Step 5: Pull Photos via ADB

Run this **after all captures**:

```powershell
# Create new batch folder
mkdir "C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\session_v2"

# Pull all new photos from phone
C:\Users\l\android-sdk\platform-tools\adb.exe pull "/storage/emulated/0/DCIM/Camera/" "C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\session_v2\"

# Optional: delete from phone to avoid duplicates next time
# C:\Users\l\android-sdk\platform-tools\adb.exe shell rm "/storage/emulated/0/DCIM/Camera/*.jpg"
```

---

## Step 6: Analyze

```powershell
python "C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\unified_analysis.py" --batch-dir "C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\session_v2"
```

Outputs:
- `analysis/summary_report.md` — Full report
- `analysis/summary.csv` — Machine-readable metrics
- `analysis/histogram_comparison.png` — Exposure comparison
- `analysis/sharpness_comparison.png` — MTF/contrast comparison
- `analysis/analysis_results.json` — Complete data

---

## Step 7: What to Look For in Results

### Success Criteria
| Metric | Target | Current Best |
|--------|--------|--------------|
| Checkerboard detected | All photos | 4/5 |
| Alternation ratio | >0.70 | ~0.40–0.42 |
| MTF50 | >0.1 cyc/px | 0.1438 (345 LWPH) |
| Black clipping | <5% | 2–11% |
| Exposure bracket | 5+ distinct EV | ✅ Done |

### If Results Are Poor
- **Checkerboard not detected:** Move closer/further, adjust focus, improve lighting
- **MTF50 = 0:** Image is out of focus — tap-to-focus again
- **Heavy clipping:** Adjust exposure compensation
- **Moiré patterns:** Increase distance from monitor, or use printed chart instead

---

## ADB Quick Reference

```powershell
# Launch camera app
adb shell am start -a android.media.action.IMAGE_CAPTURE

# Force-stop camera if stuck
adb shell am force-stop com.android.camera

# Pull all photos
adb pull "/storage/emulated/0/DCIM/Camera/" "C:\captures\"

# Delete all photos from phone (careful!)
adb shell rm "/storage/emulated/0/DCIM/Camera/*.jpg"

# Check phone storage
adb shell df /storage/emulated/0/

# List all photos
adb shell ls "/storage/emulated/0/DCIM/Camera/"
```

---

## When You're Done

Once you've captured the 13+ photos and pulled them to `session_v2/`, run the analysis command above and share the output. I'll help you interpret:
- MTF50 improvement vs previous sessions
- Checkerboard alternation ratio
- Exposure bracket dynamic range
- Best exposure setting for your IMX682 sensor

**Good luck with the capture session!**
