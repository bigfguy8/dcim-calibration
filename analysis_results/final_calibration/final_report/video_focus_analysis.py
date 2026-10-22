#!/usr/bin/env python3
"""Video focus analysis for IMX682 captures"""
import os, json, cv2, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\final_report\new_captures"
BASE2 = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\final_report\new_captures2"
OUT = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\final_report\video_analysis"
os.makedirs(OUT, exist_ok=True)

videos = [
    os.path.join(BASE, "20261019_175043_lmc_8.4.mp4"),
    os.path.join(BASE, "20261019_175111_lmc_8.4.mp4"),
    os.path.join(BASE2, "VID_20261019_175334.mp4"),
]

def analyze_video(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Sample every Nth frame
    sample_interval = max(1, total_frames // 30)

    frame_sharpness = []
    frame_brightness = []
    frame_contrast = []
    frame_numbers = []

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_interval == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Sharpness via Laplacian variance
            lap = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = float(np.var(lap))
            # Brightness
            brightness = float(np.mean(gray))
            # Contrast
            contrast = float(np.std(gray))

            frame_sharpness.append(sharpness)
            frame_brightness.append(brightness)
            frame_contrast.append(contrast)
            frame_numbers.append(frame_idx)

        frame_idx += 1

    cap.release()

    return {
        "filename": os.path.basename(path),
        "width": w,
        "height": h,
        "fps": round(fps, 2),
        "total_frames": total_frames,
        "duration_s": round(total_frames / fps, 2),
        "sampled_frames": len(frame_numbers),
        "sharpness": {
            "mean": float(np.mean(frame_sharpness)),
            "min": float(np.min(frame_sharpness)),
            "max": float(np.max(frame_sharpness)),
            "std": float(np.std(frame_sharpness)),
            "cv": float(np.std(frame_sharpness) / np.mean(frame_sharpness)) if np.mean(frame_sharpness) > 0 else 0,
        },
        "brightness": {
            "mean": float(np.mean(frame_brightness)),
            "min": float(np.min(frame_brightness)),
            "max": float(np.max(frame_brightness)),
            "std": float(np.std(frame_brightness)),
        },
        "contrast": {
            "mean": float(np.mean(frame_contrast)),
            "min": float(np.min(frame_contrast)),
            "max": float(np.max(frame_contrast)),
            "std": float(np.std(frame_contrast)),
        },
        "frame_numbers": frame_numbers,
        "sharpness_series": frame_sharpness,
        "brightness_series": frame_brightness,
        "contrast_series": frame_contrast,
    }

# Analyze all videos
results = []
for v in videos:
    if os.path.exists(v):
        print(f"Analyzing: {os.path.basename(v)}")
        r = analyze_video(v)
        if r:
            results.append(r)
            print(f"  {r['width']}x{r['height']} @ {r['fps']}fps, {r['duration_s']}s")
            print(f"  Sharpness: mean={r['sharpness']['mean']:.1f}, min={r['sharpness']['min']:.1f}, max={r['sharpness']['max']:.1f}, CV={r['sharpness']['cv']:.3f}")
            print(f"  Brightness: mean={r['brightness']['mean']:.1f}, std={r['brightness']['std']:.1f}")
            print(f"  Contrast: mean={r['contrast']['mean']:.1f}, std={r['contrast']['std']:.1f}")
    else:
        print(f"  NOT FOUND: {v}")

# Save results
json_path = os.path.join(OUT, "video_analysis.json")
with open(json_path, 'w') as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved: {json_path}")

# Generate plots
for r in results:
    fig, axes = plt.subplots(3, 1, figsize=(12, 8))

    axes[0].plot(r['frame_numbers'], r['sharpness_series'], 'b-', linewidth=1)
    axes[0].set_title(r['filename'] + ' - Sharpness (Laplacian Var)')
    axes[0].set_ylabel('Sharpness')
    axes[0].axhline(y=r['sharpness']['mean'], color='r', linestyle='--', alpha=0.5, label='Mean')
    axes[0].legend()

    axes[1].plot(r['frame_numbers'], r['brightness_series'], 'g-', linewidth=1)
    axes[1].set_title('Brightness')
    axes[1].set_ylabel('Mean Luminance')
    axes[1].axhline(y=r['brightness']['mean'], color='r', linestyle='--', alpha=0.5, label='Mean')
    axes[1].legend()

    axes[2].plot(r['frame_numbers'], r['contrast_series'], 'm-', linewidth=1)
    axes[2].set_title('Contrast')
    axes[2].set_ylabel('Std Luminance')
    axes[2].set_xlabel('Frame Number')
    axes[2].axhline(y=r['contrast']['mean'], color='r', linestyle='--', alpha=0.5, label='Mean')
    axes[2].legend()

    plt.tight_layout()
    plot_path = os.path.join(OUT, r['filename'].replace('.mp4', '_analysis.png'))
    plt.savefig(plot_path, dpi=100)
    plt.close()
    print(f"Saved plot: {plot_path}")

# Focus issue assessment
print("\n=== FOCUS ISSUE ASSESSMENT ===")
for r in results:
    sharp_cv = r['sharpness']['cv']
    sharp_min = r['sharpness']['min']
    sharp_mean = r['sharpness']['mean']
    print(f"\n{r['filename']}:")
    print(f"  Resolution: {r['width']}x{r['height']}")
    print(f"  Sharpness CV: {sharp_cv:.3f} (lower = more consistent)")
    print(f"  Sharpness min/mean: {sharp_min:.1f}/{sharp_mean:.1f} ({sharp_min/sharp_mean*100:.1f}% of mean)")
    print(f"  Brightness std: {r['brightness']['std']:.1f}")
    print(f"  Contrast std: {r['contrast']['std']:.1f}")

    # Focus assessment
    if sharp_cv > 0.3:
        print(f"  ⚠️ HIGH sharpness variation (CV={sharp_cv:.3f}) - possible focus hunting")
    elif sharp_cv > 0.15:
        print(f"  ⚠️ MODERATE sharpness variation (CV={sharp_cv:.3f}) - some focus inconsistency")
    else:
        print(f"  ✅ LOW sharpness variation (CV={sharp_cv:.3f}) - consistent focus")

    if sharp_min < sharp_mean * 0.5:
        print(f"  ⚠️ Sharpness drops below 50% of mean - significant soft frames")

    if r['brightness']['std'] > 20:
        print(f"  ⚠️ High brightness variation (std={r['brightness']['std']:.1f}) - exposure instability")

# Recommendations
print("\n=== FOCUS FIX RECOMMENDATIONS ===")
print("1. Use tap-to-focus on subject before recording")
print("2. Lock focus (AF lock) if available in LMC settings")
print("3. Avoid rapid panning or subject movement")
print("4. Use higher shutter speed for moving subjects")
print("5. Check if video mode uses different focus algorithm than photo mode")
print("6. Consider manual focus if LMC supports it")
print("7. Ensure adequate lighting for reliable AF")
print("8. Clean lens before recording")
print("\nNote: These are general recommendations. Actual focus performance")
print("depends on LMC's video AF implementation and scene conditions.")
print("No focus-related XML keys were found in the LMC 8.4 config format.")
