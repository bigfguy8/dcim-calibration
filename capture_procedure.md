# Sony IMX682 Camera Calibration — Capture Procedure
**Device:** LAVA LXX521 (IMX682, Android 15, SDK 35)
**PC:** Windows 10 with ADB at `C:\Users\l\android-sdk\platform-tools\`

---

## Overview

The previous calibration photos were taken of a chart displayed on a monitor. That approach has fundamental limitations:
- Monitor pixel structure limits resolvable detail (MTF)
- Monitor color profile unknown (no absolute color accuracy)
- Single exposure (no dynamic range analysis)
- Cannot separate lens distortion from display geometry

**Goal:** Capture the calibration chart under controlled conditions for quantitative analysis.

---

## Phase 1: Prepare the Calibration Target

### Option A: Print (Recommended for accuracy)

1. Open `D:\LXX521-GCam\calibration_chart_IMX682.png` on your PC
2. Print on matte paper at 300 DPI (chart is 5000×6500 px ≈ 16.7×21.7 cm at 300 DPI)
3. Tape the print flat to a wall or board — no curls, no wrinkles
4. Ensure even, diffuse lighting on the chart (no glare, no shadows)

### Option B: Monitor Display (Fallback)

1. Display `calibration_chart_IMX682.png` full-screen on a high-resolution monitor
2. Set monitor to native resolution, 100% scaling
3. Disable blue-light filters, night mode, HDR
4. Set brightness to a known, fixed level (e.g., 80%)
5. Photograph straight-on, perpendicular to screen

---

## Phase 2: Phone Setup

### Mount the Phone

1. Place phone on a tripod or stable stand
2. Position perpendicular to the chart (camera lens parallel to chart plane)
3. Distance: fill frame with chart, leaving small margins
4. Ensure no phone case shadow on lens

### Disable Image Processing (if possible)

Open the stock camera app (`com.android.camera`) and check for:
- **HDR:** OFF
- **AI scene detection:** OFF
- **Beauty/filter modes:** OFF
- **RAW save:** ON (if supported — MT6878 may support DNG via Camera2 API)
- **Grid/level:** ON (helps keep phone perpendicular)

*Note: Stock Lava camera may not expose these controls. If not available, proceed anyway and note the limitation.*

---

## Phase 3: Capture Sequence

Capture the following shots in order. Use ADB to pull photos after each batch.

### Shot Group 1: Center, Perpendicular (Focus + Sharpness)

| Shot | Exposure Compensation | Purpose |
|------|----------------------|---------|
| C1 | -2 EV (underexposed) | Shadow detail, noise |
| C2 | -1 EV | Mid-tone detail |
| C3 | 0 EV (normal) | Reference |
| C4 | +1 EV | Highlight detail |
| C5 | +2 EV (overexposed) | Clipping behavior |

**ADB to trigger:**
```powershell
C:\Users\l\android-sdk\platform-tools\adb.exe shell am start -a android.media.action.IMAGE_CAPTURE
```
Then tap the shutter manually on the phone. After each batch, pull:
```powershell
C:\Users\l\android-sdk\platform-tools\adb.exe pull "/storage/emulated/0/DCIM/Camera/" "C:\path\to\captures\"
```

### Shot Group 2: Angled 15° (Distortion)

Rotate phone ~15° left and right, repeat C3 (0 EV) for each angle:
- C3-left: 15° rotated left
- C3-right: 15° rotated right

This enables distortion coefficient estimation.

### Shot Group 3: Corners (Field Performance)

Move chart so each corner is near frame center:
- C3-top-left
- C3-top-right
- C3-bottom-left
- C3-bottom-right

### Shot Group 4: White Balance Reference

Capture a neutral gray/white surface under same lighting:
- WB-ref: Fill frame with neutral gray card or white paper

---

## Phase 4: Pull Photos to PC

After each capture batch:

```powershell
# Create capture folder
mkdir "C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\capture_batch_1"

# Pull new photos from phone
C:\Users\l\android-sdk\platform-tools\adb.exe pull "/storage/emulated/0/DCIM/Camera/" "C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\capture_batch_1\"

# Optional: Delete from phone to avoid duplicates
C:\Users\l\android-sdk\platform-tools\adb.exe shell rm "/storage/emulated/0/DCIM/Camera/*.jpg"
```

---

## Phase 5: Analysis

Once you have the new photos, place them in:
```
C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\capture_batch_N\
```

Then re-run the analysis pipeline. I can update the analysis script to:
- Detect exposure brackets automatically
- Compute MTF50 from slanted edges
- Estimate distortion coefficients from checkerboard
- Compute Delta E against ColorChecker reference (if you provide reference values)

---

## Phase 5b: Optional — RAW Capture via Camera2 API

If your stock camera app supports RAW/DNG:
1. Enable RAW save in camera settings
2. Capture DNG + JPEG pairs
3. Analyze DNG files for pure sensor+optics data (no ISP processing)

Check RAW support:
```powershell
C:\Users\l\android-sdk\platform-tools\adb.exe shell dumpsys media.camera | findstr /i "raw\|dng"
```

---

## Files You Already Have

| File | Location | Purpose |
|------|----------|---------|
| Calibration chart | `D:\LXX521-GCam\calibration_chart_IMX682.png` | Print or display this |
| Analysis pipeline | `C:\Users\l\AppData\Local\Temp\opencode\calibration_analysis_step*.py` | Re-run for new photos |
| Previous results | `C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\` | Baseline for comparison |

---

## Quick ADB Reference

```powershell
# Launch camera
adb shell am start -a android.media.action.IMAGE_CAPTURE

# Pull all DCIM photos
adb pull "/storage/emulated/0/DCIM/Camera/" "C:\captures\"

# Delete pulled photos from phone
adb shell rm "/storage/emulated/0/DCIM/Camera/*.jpg"

# Check available storage
adb shell df /storage/emulated/0/

# Force-stop camera app
adb shell am force-stop com.android.camera
```

---

## Next Step

Once you've captured the exposure bracket and angled shots, place them in the capture folder and I'll update the analysis pipeline to process them. The pipeline already supports:
- EXIF metadata extraction
- Luminance/RGB statistics
- Edge density and contrast
- MTF50 via slanted-edge method
- Checkerboard detection (for distortion)
- Relative color analysis

**Just let me know when you have the new photos ready.**
