#!/usr/bin/env python3
"""Pull new baseline A/B test photos from device"""
import subprocess, os

ADB = r"C:\Users\l\android-sdk\platform-tools\adb.exe"
DEST = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\no_cost_tests\ab_comparison\baseline"

# List all jpg files on device
result = subprocess.run([ADB, "shell", "find /sdcard/DCIM/ -type f -name '*.jpg'"], capture_output=True, text=True)
all_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]

# Already pulled files (monitor captures)
already_pulled = set()
for d in [r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\monitor_calibration\captures",
          r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\monitor_calibration\captures2"]:
    if os.path.exists(d):
        for f in os.listdir(d):
            already_pulled.add(f)

# Also check local dcim_calibration root
dcim_root = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration"
for f in os.listdir(dcim_root):
    if f.lower().endswith('.jpg'):
        already_pulled.add(f)

# Identify new files
new_files = []
for f in all_files:
    name = os.path.basename(f)
    safe_name = name.replace('(', '_').replace(')', '_').replace(' ', '_')
    if name not in already_pulled and safe_name not in already_pulled:
        new_files.append(f)

print(f"Total on device: {len(all_files)}")
print(f"Already pulled: {len(already_pulled)}")
print(f"New files: {len(new_files)}")

for f in new_files:
    name = os.path.basename(f)
    safe_name = name.replace('(', '_').replace(')', '_').replace(' ', '_')
    dest_path = os.path.join(DEST, safe_name)
    print(f"Pulling: {name} -> {safe_name}")
    r = subprocess.run([ADB, "pull", f, dest_path], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr}")
    else:
        print(f"  OK")

print("\nDone pulling " + str(len(new_files)) + " files")
print("Baseline dir count: " + str(len(os.listdir(DEST))))
