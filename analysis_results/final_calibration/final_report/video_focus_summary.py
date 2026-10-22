import json
data = json.load(open(r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\final_report\video_analysis\video_analysis.json"))
for r in data:
    sharp_cv = r['sharpness']['cv']
    sharp_min = r['sharpness']['min']
    sharp_mean = r['sharpness']['mean']
    print(r['filename'] + ":")
    print("  Resolution: " + str(r['width']) + "x" + str(r['height']))
    print("  Sharpness CV: " + str(round(sharp_cv, 3)) + " (lower = more consistent)")
    print("  Sharpness min/mean: " + str(round(sharp_min, 1)) + "/" + str(round(sharp_mean, 1)) + " (" + str(round(sharp_min/sharp_mean*100, 1)) + "% of mean)")
    print("  Brightness std: " + str(round(r['brightness']['std'], 1)))
    print("  Contrast std: " + str(round(r['contrast']['std'], 1)))
    if sharp_cv > 0.3:
        print("  HIGH sharpness variation (CV=" + str(round(sharp_cv, 3)) + ") - possible focus hunting")
    elif sharp_cv > 0.15:
        print("  MODERATE sharpness variation (CV=" + str(round(sharp_cv, 3)) + ") - some focus inconsistency")
    else:
        print("  LOW sharpness variation (CV=" + str(round(sharp_cv, 3)) + ") - consistent focus")
    if sharp_min < sharp_mean * 0.5:
        print("  Sharpness drops below 50% of mean - significant soft frames")
    if r['brightness']['std'] > 20:
        print("  High brightness variation (std=" + str(round(r['brightness']['std'], 1)) + ") - exposure instability")
    print()
print("FOCUS FIX RECOMMENDATIONS:")
print("1. Use tap-to-focus on subject before recording")
print("2. Lock focus (AF lock) if available in LMC settings")
print("3. Avoid rapid panning or subject movement")
print("4. Use higher shutter speed for moving subjects")
print("5. Check if video mode uses different focus algorithm than photo mode")
print("6. Consider manual focus if LMC supports it")
print("7. Ensure adequate lighting for reliable AF")
print("8. Clean lens before recording")
print()
print("Note: No focus-related XML keys found in LMC 8.4 config format.")
print("Focus is controlled by camera app, not XML config.")
