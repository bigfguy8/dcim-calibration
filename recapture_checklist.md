# IMX682 Calibration — Complete Re-Capture Checklist
**Device:** LAVA LXX521 (IMX682, Android 15) | **App:** LMC8.4 R18F1 Iris

---

## Phase 1: Prepare Environment

### 1.1 Print the Calibration Chart
- [ ] Print `D:\LXX521-GCam\calibration_chart_IMX682.png` on **matte paper** (not glossy)
- [ ] Print at 300 DPI → size ~16.7 × 21.7 cm
- [ ] Tape flat to a wall/board — no curls, wrinkles, or bubbles

### 1.2 Lighting Setup
- [ ] Even, diffuse lighting on the chart (no shadows, no glare)
- [ ] Avoid direct sunlight or harsh overhead lights
- [ ] If using monitor fallback: native resolution, 100% scaling, no blue-light filter, fixed brightness

### 1.3 Phone Mounting
- [ ] Phone on tripod or stable stand
- [ ] Lens **parallel to chart plane** (perpendicular, no angle)
- [ ] Grid lines ON in camera app (helps keep straight)
- [ ] Fill frame with chart, small margins around edges
- [ ] No phone case shadow on lens

---

## Phase 2: LMC8.4 Settings

Open LMC8.4 app and verify:
- [ ] **HDR:** OFF (for consistent, repeatable results)
- [ ] **AI scene detection:** OFF
- [ ] **Beauty/filter:** OFF
- [ ] **Grid:** ON
- [ ] **RAW/DNG:** ON if available (check settings)

### Exposure Compensation Values to Capture
| Shot | EV Comp | Purpose |
|------|---------|---------|
| 1 | -2 EV | Shadow detail, noise floor |
| 2 | -1 EV | Dark mid-tones |
| 3 | 0 EV | Normal reference |
| 4 | +1 EV | Bright mid-tones |
| 5 | +2 EV | Highlight clipping |

---

## Phase 3: Capture Sequence (in order)

### Shot Group A — Center, Perpendicular (5 shots, exposure bracket)
For each EV setting:
1. Frame chart centered, perpendicular
2. Tap-to-focus on chart center
3. Hold steady (tripod)
4. Tap shutter
5. Note the EV used

**EV sequence: -2, -1, 0, +1, +2**

### Shot Group B — Angled Views (3 shots, 0 EV)
- [ ] 0 EV, camera 15° rotated LEFT
- [ ] 0 EV, camera straight-on
- [ ] 0 EV, camera 15° rotated RIGHT

### Shot Group C — Corner Views (4 shots, 0 EV)
Move chart so each corner is near frame center:
- [ ] Top-left corner centered
- [ ] Top-right corner centered
- [ ] Bottom-left corner centered
- [ ] Bottom-right corner centered

### Shot Group D — White Balance (1 shot, 0 EV)
- [ ] Fill frame with neutral gray card or white paper
- [ ] Same lighting as chart shots

**Total: 13 photos**

---

## Phase 4: Pull Photos via ADB

Run this after all captures:

```powershell
# Create new batch folder
mkdir "C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\recapture_v2"

# Pull all new photos from phone
C:\Users\l\android-sdk\platform-tools\adb.exe pull "/storage/emulated/0/DCIM/Camera/" "C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\recapture_v2\"

# Optional: delete from phone to avoid duplicates next time
# C:\Users\l\android-sdk\platform-tools\adb.exe shell rm "/storage/emulated/0/DCIM/Camera/*.jpg"
```

---

## Phase 5: Run Analysis

```powershell
python "C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\unified_analysis.py" --batch-dir "C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\recapture_v2"
```

Outputs:
- `analysis/summary_report.md` — Full report
- `analysis/summary.csv` — Machine-readable metrics
- `analysis/histogram_comparison.png` — Exposure comparison
- `analysis/sharpness_comparison.png` — MTF/contrast comparison
- `analysis/analysis_results.json` — Complete data

---

## Phase 6: Expected Improvements (vs current)

| Metric | Current | Target After Fix |
|--------|---------|-----------------|
| MTF50 | 0.0063 cyc/px | >0.02 cyc/px |
| Checkerboard alternation | 0.42–0.47 | >0.70 |
| Black clipping (stock) | 9.44% | <2% |
| Exposure bracket | No (EV 7.2–8.1 only) | Yes (-2 to +2 EV) |

---

## Quick ADB Reference

```powershell
# Launch camera
adb shell am start -a android.media.action.IMAGE_CAPTURE

# Force-stop camera if stuck
adb shell am force-stop com.android.camera

# Pull all photos
adb pull "/storage/emulated/0/DCIM/Camera/" "C:\captures\"

# Check phone storage
adb shell df /storage/emulated/0/

# List all photos on phone
adb shell ls "/storage/emulated/0/DCIM/Camera/"
```

---

## When You're Done

Once you've captured the 13+ photos and pulled them to `recapture_v2/`, run the analysis and share the results. I'll help interpret:
- MTF50 improvement (focus fix verification)
- Checkerboard alternation ratio (lighting fix verification)
- Exposure bracket dynamic range
- Distortion coefficients (from multi-angle shots)
