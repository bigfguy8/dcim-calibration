#!/usr/bin/env python3
"""Safe XML profile picker/deployer for the DCIM Calibration V4 pack."""
from __future__ import annotations
import shutil
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROFILE_DIRS = [BASE_DIR / "profiles", BASE_DIR / "analysis_results" / "imx682_config"]
SDCARD_LMC_DIR = Path("/sdcard/LMC8.4")
BACKUP_DIR = BASE_DIR / "backups"

def banner(title: str) -> None:
    print("\n" + "=" * 68 + f"\n  {title}\n" + "=" * 68)

def collect_profiles():
    found = {}
    for folder in PROFILE_DIRS:
        if folder.is_dir():
            for path in folder.glob("*.xml"):
                found.setdefault(path.name, path)
    return sorted(found.values(), key=lambda p: p.name.lower())

def validate_xml(path: Path):
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        return False, f"XML parse failed: {exc}"
    if root.tag != "map":
        return False, f"Unexpected root <{root.tag}>; expected <map> for this pack's profiles."
    seen, duplicates = set(), set()
    for node in root:
        key = node.attrib.get("name")
        if not key:
            return False, f"<{node.tag}> entry is missing its name attribute."
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    if duplicates:
        return False, "Duplicate keys: " + ", ".join(sorted(duplicates))
    return True, f"XML syntax OK; {len(list(root))} entries"

def deploy(path: Path):
    ok, message = validate_xml(path)
    if not ok:
        print(f"[ERROR] {message}")
        return False
    print(f"[CHECK] {path.name}: {message}")
    print(f"[NOTE] XML syntax does not prove compatibility with your exact LMC/BSG build.")
    dest_dir = SDCARD_LMC_DIR
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / path.name
        if dest.exists():
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = BACKUP_DIR / f"{dest.name}.{stamp}.bak"
            shutil.copy2(dest, backup)
            print(f"[BACKUP] Existing destination saved to: {backup}")
        shutil.copy2(path, dest)
        print(f"[OK] Copied to: {dest}")
        print("[NEXT] Import the XML from inside the camera app. Keep the previous config for rollback.")
        return True
    except OSError as exc:
        print(f"[ERROR] Copy failed: {exc}")
        print("On Android/Termux, run `termux-setup-storage` and check that /sdcard is accessible.")
        return False

def main():
    banner("DCIM Calibration V4 — Safe Profile Manager")
    print("Destination:", SDCARD_LMC_DIR)
    profiles = collect_profiles()
    if not profiles:
        print("[ERROR] No XML files found in profiles/ or analysis_results/imx682_config/.")
        sys.exit(1)
    for i, path in enumerate(profiles, 1):
        ok, msg = validate_xml(path)
        print(f"[{i:2}] {'OK' if ok else 'INVALID'}  {path.name} — {msg}")
    print("[0] Exit")
    try:
        raw = input("\nSelect profile to copy (0 cancels): ").strip()
        if not raw.isdigit():
            print("Please enter a listed number.")
            sys.exit(2)
        choice = int(raw)
        if choice == 0:
            return
        if not 1 <= choice <= len(profiles):
            print("Selection out of range.")
            sys.exit(2)
        selected = profiles[choice - 1]
        print(f"\nSelected: {selected.name}")
        confirm = input(f"Copy to {SDCARD_LMC_DIR}? Type YES to continue: ").strip()
        if confirm != "YES":
            print("Cancelled; no files copied.")
            return
        deploy(selected)
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
if __name__ == "__main__":
    main()
