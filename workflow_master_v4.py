#!/usr/bin/env python3
"""Safe XML profile picker/deployer for the DCIM Calibration V4 pack."""
from __future__ import annotations
import argparse
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROFILE_DIRS = [BASE_DIR / "profiles", BASE_DIR / "analysis_results" / "imx682_config"]

# Preferred Termux shared storage path (per project mission §12)
TERMUX_DEFAULT_DIR = Path.home() / "storage/shared/Download/DCIM_Calibration"

# Fallback: ~/.lcgc/ if preferred dir not available
FALLBACK_DIR = Path("~/.lcgc").expanduser()

# Android application config dirs (these are device-specific and must be
# confirmed by the user; not auto-detected in Termux without ADB)
ANDROID_LMC84_DIR = Path("/sdcard/LMC8.4")
ANDROID_MGC_DIR = Path("/data/data/com.android.MGC_9_4_103/shared_prefs")

# Backup directory relative to project root
BACKUP_DIR = BASE_DIR / "backups"


def parse_cli_args() -> argparse.Namespace:
    """Parse command-line arguments for the deployer."""
    parser = argparse.ArgumentParser(
        description="Safe XML profile picker/deployer for DCIM Calibration V4 pack."
    )
    parser.add_argument(
        "--dest",
        default=None,
        help=(
            "Destination directory for profile deployment. "
            "If not provided, uses Termux-preferred path "
            "$HOME/storage/shared/Download/DCIM_Calibration, "
            "or falls back to ~/.lcgc, or the Android /sdcard/LMC8.4 path."
        ),
    )
    parser.add_argument(
        "--list-dest",
        action="store_true",
        help="Show the resolved destination path and exit.",
    )
    return parser.parse_args()

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

def resolve_destination(dest_arg: any) -> Path:
    """Resolve the deployment destination directory.

    Priority order:
    1. --dest CLI argument if provided and valid
    2. Termux-preferred: $HOME/storage/shared/Download/DCIM_Calibration
    3. Fallback: ~/.lcgc/
    4. Android /sdcard/LMC8.4 (last resort)

    Returns the resolved Path object.
    """
    # 1. CLI --dest argument
    if dest_arg is not None:
        p = Path(dest_arg).expanduser().resolve()
        if p.is_dir() or p.parent.is_dir():
            return p.resolve()
        # If directory doesn't exist yet, still return it (will be created on deploy)

    # 2. Termux-preferred path
    termux_path = TERMUX_DEFAULT_DIR.expanduser().resolve()
    if termux_path.is_dir():
        return termux_path

    # 3. Fallback
    fallback_path = FALLBACK_DIR.resolve()
    if fallback_path.is_dir():
        return fallback_path

    # 4. Android fallback (may not exist in Termux environment)
    android_path = ANDROID_LMC84_DIR
    return android_path


def deploy(path: Path, dest_dir: Optional[Path] = None):
    ok, message = validate_xml(path)
    if not ok:
        print(f"[ERROR] {message}")
        return False
    print(f"[CHECK] {path.name}: {message}")
    print(f"[NOTE] XML syntax does not prove compatibility with your exact LMC/BSG build.")

    # Resolve destination directory
    if dest_dir is None:
        dest_dir = resolve_destination(None)

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"[ERROR] Could not create destination directory: {exc}")
        return False

    dest = dest_dir / path.name
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        if dest.exists():
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
    args = parse_cli_args()

    # Show destination info
    dest_dir = resolve_destination(args.dest)
    if args.list_dest:
        print(f"Resolved destination: {dest_dir}")
        sys.exit(0)

    banner("DCIM Calibration V4 — Safe Profile Manager")
    print(f"Destination: {dest_dir}")
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
        confirm = input(f"Copy to {dest_dir}? Type YES to continue: ").strip()
        if confirm != "YES":
            print("Cancelled; no files copied.")
            return
        deploy(selected, dest_dir=dest_dir)
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
if __name__ == "__main__":
    main()
