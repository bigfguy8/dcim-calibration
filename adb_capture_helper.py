#!/usr/bin/env python3
"""
ADB Capture Helper for IMX682 Calibration
Automates pulling photos from phone and organizing them for analysis.
"""
import os
import sys
import shutil
import json
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

# ============================================================
# CONFIGURATION
# ============================================================
ADB_PATH = r"C:\Users\l\android-sdk\platform-tools\adb.exe"
PHONE_DCIM = "/storage/emulated/0/DCIM/Camera/"
BASE_CAPTURE_DIR = r"C:\Users\l\AppData\Local\Temp\opencode\dcim_calibration"

def run_adb(args):
    """Run an adb command and return output."""
    import subprocess
    cmd = [ADB_PATH] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def check_phone():
    """Verify phone is connected via ADB."""
    out, err, rc = run_adb(["devices"])
    if "device" not in out or "List of devices" not in out:
        log("ERROR: No phone connected via ADB")
        return False
    log(f"Phone connected: {out}")
    return True

def create_batch_dir(batch_name=None):
    """Create a new capture batch directory."""
    if batch_name is None:
        batch_name = datetime.now().strftime("batch_%Y%m%d_%H%M%S")
    batch_dir = os.path.join(BASE_CAPTURE_DIR, batch_name)
    os.makedirs(batch_dir, exist_ok=True)
    log(f"Created batch directory: {batch_dir}")
    return batch_dir

def pull_photos(batch_dir):
    """Pull all photos from phone DCIM to batch directory."""
    log(f"Pulling photos from {PHONE_DCIM} to {batch_dir}")
    out, err, rc = run_adb(["pull", PHONE_DCIM, batch_dir])
    log(out)
    if err:
        log(f"Warnings: {err}")

    # List pulled files
    pulled = []
    for f in os.listdir(batch_dir):
        fpath = os.path.join(batch_dir, f)
        if os.path.isfile(fpath) and f.lower().endswith(('.jpg', '.jpeg', '.dng', '.png')):
            size = os.path.getsize(fpath)
            pulled.append({"filename": f, "size_bytes": size, "path": fpath})

    log(f"Pulled {len(pulled)} files")
    return pulled

def delete_phone_photos():
    """Delete all photos from phone DCIM Camera folder."""
    log("Deleting photos from phone DCIM Camera folder")
    out, err, rc = run_adb(["shell", "rm", f"{PHONE_DCIM}*.jpg"])
    log(out)
    if err:
        log(f"Warnings: {err}")

def extract_exif_summary(batch_dir):
    """Extract EXIF summary for all photos in batch."""
    summary = []
    for f in sorted(os.listdir(batch_dir)):
        if not f.lower().endswith(('.jpg', '.jpeg')):
            continue
        fpath = os.path.join(batch_dir, f)
        try:
            img = Image.open(fpath)
            img.load()
            exif_raw = img._getexif() or {}
            exif = {}
            for k, v in exif_raw.items():
                tag = TAGS.get(k, k)
                if isinstance(v, bytes):
                    v = v.decode("latin1", errors="replace")[:100]
                exif[tag] = str(v)[:100]

            summary.append({
                "filename": f,
                "width": img.size[0],
                "height": img.size[1],
                "make": exif.get("Make", ""),
                "model": exif.get("Model", ""),
                "software": exif.get("Software", ""),
                "datetime": exif.get("DateTime", ""),
                "iso": exif.get("ISOSpeedRatings", ""),
                "exposure": exif.get("ExposureTime", ""),
                "f_number": exif.get("FNumber", ""),
                "focal_length": exif.get("FocalLength", ""),
                "white_balance": exif.get("WhiteBalance", ""),
                "flash": exif.get("Flash", ""),
            })
        except Exception as e:
            log(f"  Could not read EXIF from {f}: {e}")

    # Save summary
    summary_path = os.path.join(batch_dir, "exif_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    log(f"Saved EXIF summary: {summary_path}")

    # Print table
    print("\n=== EXIF Summary ===")
    print(f"{'File':<35} {'ISO':<6} {'Exp':<10} {'F#':<5} {'FL':<6} {'Software'}")
    print("-" * 80)
    for s in summary:
        print(f"{s['filename']:<35} {str(s['iso']):<6} {str(s['exposure']):<10} {str(s['f_number']):<5} {str(s['focal_length']):<6} {str(s['software'])[:25]}")

    return summary

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ADB Capture Helper for IMX682 Calibration")
    parser.add_argument("--pull", action="store_true", help="Pull photos from phone")
    parser.add_argument("--delete", action="store_true", help="Delete photos from phone after pull")
    parser.add_argument("--batch", type=str, help="Custom batch name")
    parser.add_argument("--launch-camera", action="store_true", help="Launch camera app on phone")
    parser.add_argument("--exif-only", action="store_true", help="Only extract EXIF from existing batch")
    parser.add_argument("--batch-dir", type=str, help="Existing batch directory for EXIF-only")

    args = parser.parse_args()

    if not check_phone():
        sys.exit(1)

    if args.launch_camera:
        log("Launching camera app on phone...")
        out, err, rc = run_adb(["shell", "am", "start", "-a", "android.media.action.IMAGE_CAPTURE"])
        log(out)
        log("Take photos on the phone, then run this script again with --pull")

    if args.exif_only and args.batch_dir:
        extract_exif_summary(args.batch_dir)
        return

    if args.pull:
        batch_dir = create_batch_dir(args.batch)
        pulled = pull_photos(batch_dir)
        extract_exif_summary(batch_dir)

        if args.delete and pulled:
            confirm = input("\nDelete photos from phone? (y/N): ")
            if confirm.lower() == 'y':
                delete_phone_photos()
                log("Photos deleted from phone")

    if not args.pull and not args.launch_camera and not args.exif_only:
        parser.print_help()

if __name__ == "__main__":
    main()
