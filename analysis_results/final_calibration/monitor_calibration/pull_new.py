#!/usr/bin/env python3
"""Pull all new DCIM photos from device"""
import subprocess, os

ADB = r"C:\Users\l\android-sdk\platform-tools\adb.exe"
DEST = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration\analysis_results\final_calibration\monitor_calibration\captures2"

# List all jpg files on device
result = subprocess.run([ADB, "shell", "find /sdcard/DCIM/ -type f -name '*.jpg'"], capture_output=True, text=True)
files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]

# Skip already-pulled files (the original 5)
already_pulled = {
    "/sdcard/DCIM/Camera/20261019_170217_lmc_8.4.jpg",
    "/sdcard/DCIM/Camera/20261019_170227_lmc_8.4.jpg",
    "/sdcard/DCIM/Camera/20261019_170236_lmc_8.4.jpg",
    "/sdcard/DCIM/Camera/20261019_170241_lmc_8.4.jpg",
    "/sdcard/DCIM/Camera/20261019_170249_lmc_8.4.jpg",
}

new_files = [f for f in files if f not in already_pulled]
print(f"Total files: {len(files)}")
print(f"Already pulled: {len(already_pulled)}")
print(f"New files: {len(new_files)}")

for f in new_files:
    name = os.path.basename(f)
    # Sanitize filename for Windows (replace invalid chars)
    safe_name = name.replace('(', '_').replace(')', '_').replace(' ', '_')
    dest_path = os.path.join(DEST, safe_name)
    print(f"Pulling: {name} -> {safe_name}")
    r = subprocess.run([ADB, "pull", f, dest_path], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr}")
    else:
        print(f"  OK")
print("\nDone pulling " + str(len(new_files)) + " files")
