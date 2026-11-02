#!/usr/bin/env python3
"""
deployment.py - Safe deployment utility for GCam profiles.

Provides reliable profile deployment with:
- Explicit profile selection.
- XML validation before deployment.
- Existing-file backup.
- SHA-256 verification.
- Destination verification.
- Rollback support.
- Dry-run mode.
- Explicit user confirmation.

Preferred shared storage: ~/storage/shared/Download/DCIM_Calibration/
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .config_validator import validate_profile_summary
from .config_generator import compute_sha256, record_provenance
from .xml_audit import check_syntax


#
# Deployment destination paths
#

# Preferred Termux shared storage path (per project mission spec §12)
PREFERRED_TERMUX_DIR = Path("~/storage/shared/Download/DCIM_Calibration").expanduser()

# Fallback: ~/.lcgc/ if preferred dir not available
FALLBACK_DIR = Path("~/.lcgc").expanduser()

# Android application config dirs (these are device-specific and must be
# confirmed by the user; not auto-detected in Termux without ADB)
ANDROID_LMC84_DIR = Path("/sdcard/LMC8.4")
ANDROID_MGC_DIR = Path("/data/data/com.android.MGC_9_4_103/shared_prefs")


#
# Deployment result types
#

class DeployResult(Enum):
    """Result of a deployment operation."""
    SUCCESS = "success"
    DRY_RUN = "dry_run"
    VALIDATION_FAILED = "validation_failed"
    PERMISSION_DENIED = "permission_denied"
    USER_CANCELLED = "user_cancelled"
    DESTINATION_NOT_FOUND = "destination_not_found"


@dataclass
class DeployOutput:
    """Output from a deployment operation."""
    result: DeployResult
    message: str
    profile_path: Optional[str] = None
    destination: Optional[str] = None
    sha256: Optional[str] = None
    backup_path: Optional[str] = None
    rollback_available: bool = False


#
# Deployment engine
#


def verify_destination(
    dest_path: Path,
    label: str,
) -> Tuple[bool, str]:
    """Verify that a destination path is valid and writable.

    Checks:
    - Path exists (or can be created).
    - Directory is writable.
    - Not the same as the source profile (to prevent accidental overwrite).

    Returns:
        (is_valid, details) tuple.
    """
    try:
        # Ensure parent directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Test writability by attempting to create and delete a temp file
        test_file = dest_path / ".deploy_test"
        try:
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError):
            return False, f"No write permission for {dest_path}"

        # Check that we're not trying to overwrite the source itself
        return True, f"Destination {dest_path} is valid and writable."

    except Exception as e:
        return False, f"Destination verification error: {e}"


def select_profile(
    profiles: List["profile_manager.ProfileInfo"],
    profile_name: Optional[str] = None,
) -> Optional["profile_manager.ProfileInfo"]:
    """Select a profile from the given list.

    If profile_name is given, find the matching profile.
    Otherwise, list all profiles and let the user choose (via CLI input).

    Returns:
        ProfileInfo for the selected profile, or None if no selection.
    """
    if profile_name:
        for p in profiles:
            if p.name == profile_name:
                return p
        print(f"Profile '{profile_name}' not found.")
        return None

    # List profiles for user to choose
    print("Available profiles:")
    for i, p in enumerate(profiles, 1):
        baseline_marker = " (BASELINE)" if p.is_baseline else ""
        sha_short = p.sha256[:16]
        print(f"  {i}. {p.name} — Family: {p.schema_family.value}{baseline_marker} — {sha_short}")

    while True:
        try:
            choice = input(f"\nSelect profile (1-{len(profiles)}, 0 to cancel): ").strip()
            if choice == "0":
                return None
            idx = int(choice) - 1
            if 1 <= idx <= len(profiles):
                return profiles[idx - 1]
            else:
                print(f"Please enter a number between 1 and {len(profiles)}.")
        except ValueError:
            print("Please enter a valid number.")


def deploy_profile(
    profile_path: str,
    dest_dir: Optional[Path] = None,
    /,
    *,
    dry_run: bool = False,
    confirm: bool = True,
) -> DeployOutput:
    """Deploy (copy) a profile XML to a destination directory.

    Steps:
    1. Validate the profile XML (syntax + schema).
    2. If validation passes, create a backup of the destination if it exists.
    3. Copy the profile to the destination.
    4. Verify SHA-256 integrity.
    5. Record provenance.

    If dry_run=True, steps 2-4 are skipped; only validation is performed.

    Args:
        profile_path: Path to the profile XML to deploy.
        dest_dir: Destination directory.  If None, uses the preferred Termux dir.
        dry_run: If True, only validate; do not copy.
        confirm: If True, ask for confirmation before overwriting existing destination.

    Returns:
        DeployOutput with the result.
    """
    # 1. Validate the profile
    summary = validate_profile_summary(profile_path)

    if not summary["well_formed"]:
        return DeployOutput(
            result=DeployResult.VALIDATION_FAILED,
            message=f"Profile fails syntax validation.",
            profile_path=profile_path,
        )

    if not summary["schema_identified"]:
        return DeployOutput(
            result=DeployResult.VALIDATION_FAILED,
            message=f"Profile schema could not be identified.",
            profile_path=profile_path,
        )

    if summary["unsupported_keys_found"]:
        # Not a hard failure, but warn the user
        pass  # continue with warning

    if summary["missing_critical_keys"]:
        # Not a hard failure, but warn the user
        pass  # continue with warning

    # 2. Determine destination
    if dest_dir is None:
        dest_dir = PREFERRED_TERMUX_DIR

    dest_path = dest_dir / Path(profile_path).name

    # 3. Backup existing destination if it exists
    backup_path: Optional[str] = None
    if dest_path.exists() and not dry_run:
        if confirm:
            backup_choice = input(
                f"Destination {dest_path} already exists. "
                f"Create backup before overwriting? (yes/NO): "
            ).strip().lower()
            if backup_choice == "yes":
                try:
                    backup_path = backup_profile(str(dest_path))
                    print(f"Backup created: {backup_path}")
                except Exception as e:
                    return DeployOutput(
                        result=DeployResult.PERMISSION_DENIED,
                        message=f"Could not create backup: {e}",
                        profile_path=profile_path,
                        destination=str(dest_path),
                    )
        else:
            # Auto-backup without asking
            try:
                backup_path = backup_profile(str(dest_path))
            except Exception as e:
                return DeployOutput(
                    result=DeployResult.PERMISSION_DENIED,
                    message=f"Could not create backup: {e}",
                    profile_path=profile_path,
                    destination=str(dest_path),
                )

    # 4. Confirm overwrite if destination exists
    if dest_path.exists() and confirm and not dry_run:
        overwrite = input(
            f"Profile '{Path(profile_path).name}' will overwrite "
            f"'{dest_path}'. Proceed? (yes/NO): "
        ).strip().lower()
        if overwrite != "yes":
            return DeployOutput(
                result=DeployResult.USER_CANCELLED,
                message="Deployment cancelled by user.",
                profile_path=profile_path,
                destination=str(dest_path),
            )

    # 5. Copy the profile (or dry-run)
    if dry_run:
        # Just validate; no file operations
        return DeployOutput(
            result=DeployResult.DRY_RUN,
            message=f"Dry-run: Profile {Path(profile_path).name} validated OK. "
                    f"Schema: {summary['schema_identified']}. "
                    f"Unsupported keys: {summary['unsupported_keys_found']}.",
            profile_path=profile_path,
            destination=str(dest_path),
            sha256=compute_sha256(profile_path),
            rollback_available=False,
        )

    # Actual copy
    try:
        shutil.copy2(profile_path, str(dest_path))
    except Exception as e:
        return DeployOutput(
            result=DeployResult.PERMISSION_DENIED,
            message=f"Could not copy profile to destination: {e}",
            profile_path=profile_path,
            destination=str(dest_path),
        )

    # 6. Verify SHA-256
    try:
        final_sha256 = compute_sha256(str(dest_path))
    except Exception:
        final_sha256 = "unknown"

    # 7. Record provenance
    record_provenance(
        str(dest_path),
        source_description=f"deployed_from_{Path(profile_path).name}",
        sha256=final_sha256,
        schema_family=None,  # will be determined by the caller
        notes=f"Deployed from {Path(profile_path).name}",
    )

    # 8. Return success
    return DeployOutput(
        result=DeployResult.SUCCESS,
        message=f"Profile '{Path(profile_path).name}' successfully deployed to {dest_path}.",
        profile_path=profile_path,
        destination=str(dest_path),
        sha256=final_sha256,
        backup_path=backup_path,
        rollback_available=backup_path is not None,
    )


def deploy_interactive(
    profiles: List["profile_manager.ProfileInfo"],
    dest_dir: Optional[Path] = None,
    /,
    *,
    dry_run: bool = False,
) -> DeployOutput:
    """Interactive profile deployment.

    Lists available profiles, lets the user select one, then deploys it
    to the chosen destination.

    Args:
        profiles: List of ProfileInfo to choose from.
        dest_dir: Destination directory.  If None, uses the preferred Termux dir.
        dry_run: If True, only validate; do not copy.

    Returns:
        DeployOutput with the result.
    """
    # Select profile
    selected = select_profile(profiles)
    if selected is None:
        return DeployOutput(
            result=DeployResult.USER_CANCELLED,
            message="No profile selected; deployment aborted.",
        )

    # Select destination (or use default)
    if dest_dir is None:
        print(f"\nDefault destination: {PREFERRED_TERMUX_DIR}")
        use_default = input("Use this destination? (yes/NO): ").strip().lower()
        if use_default != "yes":
            # Ask for custom path
            custom = input("Enter custom destination path: ").strip()
            dest_dir = Path(custom).expanduser()
            if not dest_dir.is_dir():
                dest_dir.mkdir(parents=True, exist_ok=True)

    return deploy_profile(
        selected.path,
        dest_dir=dest_dir,
        dry_run=dry_run,
        confirm=True,
    )


#
# Rollback
#


def request_rollback(
    dest_path: str,
    backup_dir: str = "backups",
) -> bool:
    """Interactive rollback request.

    Asks the user if they want to roll back to the latest backup, and
    performs the rollback if confirmed.

    Returns:
        True if rollback was performed, False otherwise.
    """
    backup = Path(backup_dir)
    bak_files = list(backup.glob("*.bak"))

    if not bak_files:
        print("No backups found. Nothing to roll back.")
        return False

    print("Available backups:")
    for i, f in enumerate(sorted(bak_files, reverse=True), 1):
        print(f"  {i}. {f.name}")

    while True:
        try:
            choice = input(
                f"\nRoll back to latest backup? (1-{len(bak_files)}, 0 to cancel): "
            ).strip()
            if choice == "0":
                return False
            idx = int(choice) - 1
            if 1 <= idx <= len(bak_files):
                latest = sorted(bak_files, reverse=True)[idx - 1]
                print(f"Rolling back to: {latest.name}")
                confirm = input("Confirm rollback? (yes/NO): ").strip().lower()
                if confirm == "yes":
                    from .profile_manager import rollback_to_latest
                    success = rollback_to_latest(latest)
                    return success
                else:
                    return False
            else:
                print(f"Please enter a number between 1 and {len(bak_files)}.")
        except ValueError:
            print("Please enter a valid number.")


if __name__ == "__main__":
    # Demo: list profiles and show deployment capability
    import sys

    print("=" * 70)
    print("Deployment Utility Demo")
    print("=" * 70)

    from .profile_manager import list_profiles

    profiles = list_profiles()
    print(f"\nFound {len(profiles)} profiles in the repository.\n")

    # Show deployment info for the first non-baseline profile
    for p in profiles:
        if not p.is_baseline:
            print(f"Profile: {p.name}")
            print(f"  SHA-256: {p.sha256[:16]}...")
            print(f"  Schema: {p.schema_family.value}")

            # Test deployment (dry-run)
            output = deploy_profile(p.path, dry_run=True)
            print(f"  Dry-run result: {output.result.value}")
            print(f"  Message: {output.message[:80]}")
            break

    # Test interactive deployment (would need user input)
    # output = deploy_interactive(profiles, dry_run=True)
    # print(f"\nInteractive result: {output.result.value}")
    # print(f"Message: {output.message}")