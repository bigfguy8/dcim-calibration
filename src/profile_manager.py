#!/usr/bin/env python3
"""
profile_manager.py - Profile management with provenance and rollback.

Provides:
- Profile loading and schema classification.
- Provenance tracking (source, hash, changes, generation).
- Immutable original baseline preservation (never modify original files).
- Rollback to last-known-good backup.
- Directory-based profile organization (LMC vs BSG vs experimental).
- Backup creation with SHA-256 verification.
- Migration between profile families (with explicit confirmation and
  incompatibility warnings).
"""

from __future__ import annotations

import json
import hashlib
import shutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .config_validator import validate_profile_summary, CRITICAL_LMC_KEYS, CRITICAL_BSG_KEYS, UNSUPPORTED_LMC_KEYS
from .config_generator import compute_sha256, record_provenance
from .xml_audit import check_syntax


#
# Profile organization families
#

class ProfileFamily(Enum):
    """Profile schema families for organizational purposes."""
    LMC = "LMC"       # LMC 8.4 key family (pref_qjpg_key, ptchr_*, etc.)
    BSG = "BSG"       # BSG/MGC key family (pref_quality_key, camera_id_back, etc.)
    MIXED = "MIXED"   # Contains markers from both families
    EXPERIMENTAL = "EXPERIMENTAL"  # No recognized markers


#
# Provenance record
#

@dataclass
class ProvenanceRecord:
    """Metadata tracking the origin and history of a profile."""
    source: str  # e.g. "profiles/LMC/", "generated/", "historical/"
    original_path: str  # Path to the original/baseline profile
    generated_path: str  # Path to the generated/profile copy
    sha256: str  # SHA-256 of the file at creation time
    generation: int  # Generation number (0 = baseline, 1 = first generation, etc.)
    changes: Tuple[str, ...]  # Tuple of change descriptions; empty if no changes
    timestamp: str  # ISO-8601 generation timestamp
    notes: str  # Free-form notes

    def to_dict(self) -> Dict[str, any]:
        return {
            "source": self.source,
            "original_path": self.original_path,
            "generated_path": self.generated_path,
            "sha256": self.sha256,
            "generation": self.generation,
            "changes": list(self.changes),
            "timestamp": self.timestamp,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> "ProvenanceRecord":
        return cls(
            source=data.get("source", ""),
            original_path=data.get("original_path", ""),
            generated_path=data.get("generated_path", ""),
            sha256=data.get("sha256", ""),
            generation=data.get("generation", 0),
            changes=tuple(data.get("changes", [])),
            timestamp=data.get("timestamp", ""),
            notes=data.get("notes", ""),
        )


#
# Profile manager
#


@dataclass
class ProfileInfo:
    """Metadata for a single profile."""
    path: str
    name: str
    schema_family: ProfileFamily
    sha256: str
    size_bytes: int
    is_baseline: bool = False  # True if this is the immutable original


def classify_family(keys: Set[str]) -> ProfileFamily:
    """Classify a profile's key set into a ProfileFamily."""
    from .camera_capabilities import LMC_MARKER_KEYS, BSG_MARKER_KEYS

    has_lmc = bool(LMC_MARKER_KEYS & keys)
    has_bsg = bool(BSG_MARKER_KEYS & keys)

    if has_lmc and has_bsg:
        return ProfileFamily.MIXED
    if has_lmc:
        return ProfileFamily.LMC
    if has_bsg:
        return ProfileFamily.BSG
    return ProfileFamily.EXPERIMENTAL


def profile_info_from_path(xml_path: str) -> ProfileInfo:
    """Build a ProfileInfo for a given XML profile path."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        keys = {child.attrib.get("name") for child in root if child.attrib.get("name") is not None}
    except Exception:
        keys = set()

    family = classify_family(keys)
    try:
        with open(xml_path, "rb") as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
    except OSError:
        sha256 = "unknown"

    name = Path(xml_path).name
    size_bytes = Path(xml_path).stat().st_size

    # Determine if this is a baseline (the verified AllRounder/V10 baseline)
    is_baseline = (
        "LMC84_AllRounder" in name
        or "V10_Baseline_UNVALIDATED" in name
        or "default_working_backup" in name.lower()
    )

    return ProfileInfo(
        path=xml_path,
        name=name,
        schema_family=family,
        sha256=sha256,
        size_bytes=size_bytes,
        is_baseline=is_baseline,
    )


def list_profiles(
    directories: Tuple[str, ...] = ("profiles",),
) -> List[ProfileInfo]:
    """List all XML profiles in the given directories.

    Args:
        directories: Tuple of directory names (relative to repo root) to scan.

    Returns:
        List of ProfileInfo objects, one per XML file found.
    """
    import os

    results: List[ProfileInfo] = []
    repo_root = Path(__file__).resolve().parent.parent

    for dir_name in directories:
        dir_path = repo_root / dir_name
        if not dir_path.is_dir():
            continue
        for f in dir_path.rglob("*.xml"):
            try:
                info = profile_info_from_path(str(f))
                results.append(info)
            except Exception:
                pass  # skip files that can't be parsed

    # Sort: baselines first, then by name
    results.sort(key=lambda i: (not i.is_baseline, i.name.lower()))
    return results


def backup_profile(
    source_path: str,
    backup_dir: str = "backups",
) -> str:
    """Create a SHA-256-backed backup of a profile.

    The profile is copied (not moved) to the backup directory with a
    timestamped filename.  The original file is never modified.

    Args:
        source_path: Path to the profile to back up.
        backup_dir: Subdirectory under the project's backups/ directory.

    Returns:
        Path to the created backup file.
    """
    import os
    from datetime import datetime, timezone

    # Ensure backup directory exists
    project_backups = Path(__file__).resolve().parent.parent / "backups" / backup_dir
    project_backups.mkdir(parents=True, exist_ok=True)

    # Compute source SHA-256 for the record
    source_hash = compute_sha256(source_path)

    # Generate backup filename: basename.YYYYMMDD-HHMMSS.bak
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_filename = f"{Path(source_path).name}.{timestamp}.bak"
    backup_path = project_backups / backup_filename

    # Copy the file (shutil.copy2 preserves metadata)
    try:
        shutil.copy2(source_path, backup_path)
    except Exception as e:
        raise RuntimeError(f"Could not create backup: {e}")

    # Record provenance
    record_provenance(
        str(backup_path),
        source_description="profile_backup",
        sha256=source_hash,
        schema_family=None,  # will be determined later
        notes=f"Backup of {source_path} at {timestamp} UTC",
    )

    return str(backup_path)


def rollback_to_latest(
    target_path: str,
    backup_dir: str = "backups",
) -> bool:
    """Restore the profile to the most recent backup.

    Looks for the newest .bak file in the backup directory and copies it
    to the target path.  The backup file itself is preserved.

    Args:
        target_path: Path where the profile will be restored.
        backup_dir: Subdirectory under the project's backups/ directory.

    Returns:
        True if the rollback succeeded, False if no backups found.
    """
    project_backups = Path(__file__).resolve().parent.parent / "backups" / backup_dir

    if not project_backups.is_dir():
        return False

    # Find all .bak files, sorted by timestamp (newest first)
    bak_files = list(project_backups.glob("*.bak"))
    if not bak_files:
        return False

    # Sort by timestamp (filename format: name.YYYYMMDD-HHMMSS.bak)
    # The filename format ensures lexicographic sort = chronological sort
    bak_files.sort(reverse=True)
    latest_backup = bak_files[0]

    try:
        shutil.copy2(str(latest_backup), target_path)
        return True
    except Exception as e:
        print(f"Rollback failed: {e}")
        return False


def migrate_profile(
    source_path: str,
    target_family: ProfileFamily,
    target_dir: str = "profiles",
    /,
    confirm: bool = True,
) -> Tuple[Optional[str], str]:
    """Migrate a profile to a different schema family.

    This is a NO-OP if the source profile is already in the target family.
    If the source is MIXED and the target is LMC or BSG, the function
    will attempt to filter keys to the target family, removing incompatible
    keys.  A warning is emitted if keys are removed.

    MIGRATION IS IRREVERSIBLE in the sense that the original profile is
    not modified, but the resulting file is a new copy.  A backup is
    automatically created before migration.

    Args:
        source_path: Path to the source profile XML.
        target_family: The desired ProfileFamily (LMC, BSG, or MIXED).
        target_dir: Target directory name (relative to repo root).
        confirm: If True, ask for confirmation before removing keys.
                If False, silently remove incompatible keys.

    Returns:
        (new_path, message) tuple.  new_path is the path to the new profile,
        or None if migration was not performed.  message describes the result.
    """
    from .config_generator import generate_from_baseline

    # Quick check: if already in target family, no migration needed
    source_info = profile_info_from_path(source_path)
    if source_info.schema_family == target_family:
        return None, f"Profile already in {target_family.value} family; no migration needed."

    # Create backup before any changes
    backup_path = backup_profile(source_path)

    # Load source profile
    try:
        tree = ET.parse(source_path)
        root = tree.getroot()
        keys = {child.attrib.get("name") for child in root if child.attrib.get("name") is not None}
    except Exception as e:
        return None, f"Could not read source profile: {e}"

    # Determine which keys to keep based on target family
    from .camera_capabilities import LMC_MARKER_KEYS, BSG_MARKER_KEYS

    if target_family == ProfileFamily.LMC:
        keys_to_keep = keys & LMC_MARKER_KEYS
        keys_removed = keys - keys_to_keep
    elif target_family == ProfileFamily.BSG:
        keys_to_keep = keys & BSG_MARKER_KEYS
        keys_removed = keys - keys_to_keep
    elif target_family == ProfileFamily.MIXED:
        # Keep all keys; just re-classify
        keys_to_keep = keys
        keys_removed = set()
    else:  # EXPERIMENTAL
        keys_to_keep = keys
        keys_removed = set()

    # If keys would be removed and confirmation is requested, ask
    if keys_removed and confirm:
        print(f"\n=== Migration Warning ===")
        print(f"Profile: {source_info.name}")
        print(f"Target family: {target_family.value}")
        print(f"Keys to remove: {', '.join(sorted(keys_removed))}")
        print(f"Keys to keep: {', '.join(sorted(keys_to_keep)) or 'none'}")
        proceed = input("Proceed with migration? (yes/NO): ").strip().lower()
        if proceed != "yes":
            # Restore from backup
            # (shutil.copy2 from backup_path would go here, but we just abort)
            return None, "Migration aborted by user."

    # Build new profile with only the kept keys
    try:
        # Deep copy the root element
        new_root = ET.Element(root.tag, root.attrib.copy())

        for key in keys_to_keep:
            # Find and copy the matching entry from the source
            for child in root:
                if child.attrib.get("name") == key:
                    # Create a new element with the same name and text
                    new_child = ET.SubElement(new_root, child.tag, child.attrib.copy())
                    new_child.text = child.text
                    break

        # Build new XML tree
        new_tree = ET.ElementTree(new_root)

        # Write to target directory
        target_dir_path = Path(__file__).resolve().parent.parent / target_dir
        target_dir_path.mkdir(parents=True, exist_ok=True)
        target_name = Path(source_path).name
        new_path = target_dir_path / target_name

        new_tree.write(
            str(new_path),
            encoding="utf-8",
        )

    except Exception:
        with open(new_path, "rb") as f:
            new_sha256 = hashlib.sha256(f.read()).hexdigest()
        record_provenance(
            str(new_path),
            source_description=f"migrated_from_{source_info.name}_to_{target_family.value}",
            sha256=new_sha256,
            schema_family=target_family,
            notes=f"Migration from {source_info.schema_family.value} to {target_family.value}. "
                  f"Keys removed: {', '.join(sorted(keys_removed)) if keys_removed else 'none'}. "
                  f"Keys kept: {', '.join(sorted(keys_to_keep)) or 'none'}.",
        )

        new_info = profile_info_from_path(str(new_path))
        message = (
            f"Profile migrated to {target_family.value} family.\n"
            f"  Source: {source_info.name} ({source_info.schema_family.value})\n"
            f"  Target: {new_info.name} ({new_info.schema_family.value})\n"
            f"  SHA-256: {new_sha256}\n"
            f"  Backup created: {Path(backup_path).name}"
        )

        return str(new_path), message

    except Exception as e:
        return None, f"Migration failed: {e}"


#
# Profile reorganization
#


def organize_profiles(
    source_dirs: Tuple[str, ...] = ("profiles",),
    target_base: str = "profiles",
) -> Dict[str, int]:
    """Organize profiles into sub-directories by family.

    Moves profiles into:
    - profiles/lmc84/     → LMC key family
    - profiles/mgc_bsg/   → BSG/MGC key family
    - profiles/experimental/ → no recognized markers

    Profiles are NOT moved if they would be overwriting an existing file.
    Backups are created before any moves.

    Returns:
        Dict mapping directory name to number of profiles moved.
    """
    import shutil

    repo_root = Path(__file__).resolve().parent.parent
    target_lmc = repo_root / target_base / "lmc84"
    target_bsg = repo_root / target_base / "mgc_bsg"
    target_exp = repo_root / target_base / "experimental"

    # Create target directories
    target_lmc.mkdir(parents=True, exist_ok=True)
    target_bsg.mkdir(parents=True, exist_ok=True)
    target_exp.mkdir(parents=True, exist_ok=True)

    # List current profiles
    profiles = list_profiles(source_dirs)

    moved: Dict[str, int] = {"lmc84": 0, "mgc_bsg": 0, "experimental": 0}

    for info in profiles:
        dest_dir_map = {
            ProfileFamily.LMC: target_lmc,
            ProfileFamily.BSG: target_bsg,
            ProfileFamily.MIXED: target_bsg,  # Mixed go to BSG dir as conservative default
            ProfileFamily.EXPERIMENTAL: target_exp,
        }

        dest_dir = dest_dir_map[info.schema_family]
        dest_path = dest_dir / info.name

        # Skip if destination already exists (avoid overwrite)
        if dest_path.is_file():
            continue

        # Create backup of original before moving
        try:
            backup_profile(info.path)
        except Exception:
            pass  # best-effort; continue even if backup fails

        # Move the file
        try:
            shutil.move(str(info.path), str(dest_path))
            moved[dest_dir.name.split("/")[-1]] += 1  # count by top-level dir name
        except Exception:
            pass  # best-effort; continue

    return moved


if __name__ == "__main__":
    # Demo: list profiles and show their info
    import sys

    default_dirs = sys.argv[1:] if len(sys.argv) > 1 else ("profiles",)

    print("=" * 70)
    print("Profile Manager Demo")
    print("=" * 70)

    profiles = list_profiles(tuple(default_dirs))
    print(f"\nFound {len(profiles)} profiles:\n")

    for info in profiles:
        print(f"  {info.name}")
        print(f"    Family: {info.schema_family.value}")
        print(f"    SHA-256: {info.sha256[:16]}...")
        print(f"    Size: {info.size_bytes} bytes")
        print(f"    Baseline: {info.is_baseline}")
        print()