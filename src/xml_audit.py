#!/usr/bin/env python3
"""
xml_audit.py - Comprehensive XML validation and duplicate detection.

Provides four levels of validation as defined in the project mission:
  A. XML syntax validation (well-formedness)
  B. Configuration schema validation (LMC vs BSG vs MIXED / UNKNOWN)
  C. Camera application compatibility (does the target app recognize these keys?)
  D. Actual device validation (requires on-device Camera2 characteristics)

Never confused these four levels.  All checks are read-only; no device writes.
"""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .camera_capabilities import (
    SchemaFamily,
    identify_schema_family,
    LMC_MARKER_KEYS,
    BSG_MARKER_KEYS,
    KNOWN_ISSUES,
    UNSUPPORTED_LMC_KEYS,
)


#
# Validation levels (strictly separated, per mission section 8)
#

class ValidationLevel(Enum):
    A_SYNTAX = "A"  # XML well-formedness
    B_SCHEMA = "B"  # Configuration schema (LMC/BSG family)
    C_COMPAT = "C"  # Camera app compatibility (not proved by syntax alone)
    D_DEVICE = "D"  # Actual device validation (requires runtime)


#
# Validation result per level
#

@dataclass
class ValidationResult:
    """Result of a single validation level."""
    level: ValidationLevel
    passed: bool
    details: str
    evidence: Optional[Dict[str, Any]] = field(default=None)

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.level.value}: {self.details}"


@dataclass
class FullValidationReport:
    """Complete validation report across all four levels."""
    xml_path: str
    level_a_syntax: ValidationResult
    level_b_schema: ValidationResult
    level_c_compat: ValidationResult
    level_d_device: ValidationResult
    overall_passed: bool

    def summary(self) -> str:
        lines = [
            f"XML Validation Report: {self.xml_path}",
            "-" * 50,
            f"Level A - Syntax:   {self.level_a_syntax}",
            f"Level B - Schema:   {self.level_b_schema}",
            f"Level C - Compat:   {self.level_c_compat}",
            f"Level D - Device:   {self.level_d_device}",
            "-" * 50,
            f"Overall: {'PASS' if self.overall_passed else 'FAIL'}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, any]:
        return {
            "xml_path": self.xml_path,
            "level_a_syntax": {
                "level": self.level_a_syntax.level.value,
                "passed": self.level_a_syntax.passed,
                "details": self.level_a_syntax.details,
            },
            "level_b_schema": {
                "level": self.level_b_schema.level.value,
                "passed": self.level_b_schema.passed,
                "details": self.level_b_schema.details,
            },
            "level_c_compat": {
                "level": self.level_c_compat.level.value,
                "passed": self.level_c_compat.passed,
                "details": self.level_c_compat.details,
            },
            "level_d_device": {
                "level": self.level_d_device.level.value,
                "passed": self.level_d_device.passed,
                "details": self.level_d_device.details,
            },
            "overall_passed": self.overall_passed,
        }


#
# Level A: XML Syntax Validation
#

def check_syntax(xml_path: str) -> ValidationResult:
    """Level A: XML well-formedness and basic structure.

    Checks:
    - File is parseable by ET (no XML syntax errors).
    - Root element is <map> (expected for this pack's profiles).
    - Every child element has a 'name' attribute (no nameless entries).
    - No duplicate 'name' attributes within the <map>.

    Returns:
        ValidationResult level A.
    """
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        return ValidationResult(
            level=ValidationLevel.A_SYNTAX,
            passed=False,
            details=f"XML parse failed: {e}",
            evidence={"parse_error": str(e)},
        )
    except OSError as e:
        return ValidationResult(
            level=ValidationLevel.A_SYNTAX,
            passed=False,
            details=f"File could not be read: {e}",
            evidence={"os_error": str(e)},
        )

    root = tree.getroot()

    # Root element check
    if root.tag != "map":
        return ValidationResult(
            level=ValidationLevel.A_SYNTAX,
            passed=False,
            details=f"Unexpected root element <{root.tag}>; expected <map> for this pack's profiles.",
            evidence={"root_tag": root.tag},
        )

    # Check all children have 'name' attribute and no duplicates
    seen_keys: Set[str] = set()
    children_missing_name: List[ET.Element] = []
    duplicate_keys: List[str] = []

    for child in list(root):
        if child.attrib.get("name") is None:
            children_missing_name.append(child)
        else:
            key = child.attrib["name"]
            if key in seen_keys:
                duplicate_keys.append(key)
            else:
                seen_keys.add(key)

    # Report missing name attributes first (more fundamental)
    if children_missing_name:
        details = (
            f"<map> has {len(children_missing_name)} child element(s) missing a 'name' attribute. "
            f"First few: {[child.tag for child in children_missing_name[:3]]}"
        )
        return ValidationResult(
            level=ValidationLevel.A_SYNTAX,
            passed=False,
            details=details,
            evidence={"children_missing_name": len(children_missing_name)},
        )

    # Report duplicates
    if duplicate_keys:
        details = f"Duplicate key(s) within <map>: {', '.join(sorted(set(duplicate_keys)))}"
        return ValidationResult(
            level=ValidationLevel.A_SYNTAX,
            passed=False,
            details=details,
            evidence={"duplicate_keys": sorted(set(duplicate_keys))},
        )

    return ValidationResult(
        level=ValidationLevel.A_SYNTAX,
        passed=True,
        details=f"XML syntax OK; {len(list(root))} entries, root=<map>, no duplicate keys, all entries have 'name' attribute.",
        evidence={"entry_count": len(list(root)), "unique_keys": len(seen_keys)},
    )


#
# Helper: extract LMC/BSG marker sets from all keys
#


def _extract_markers(keys: Set[str]) -> Tuple[Set[str], Set[str]]:
    """Extract LMC and BSG marker keys from a set of all keys."""
    lmc_found = LMC_MARKER_KEYS & keys
    bsg_found = BSG_MARKER_KEYS & keys
    return lmc_found, bsg_found


#
# Level B: Configuration Schema Validation
#

def check_schema(xml_path: str) -> ValidationResult:
    """Level B: Configuration schema validation.

    Checks:
    - Identifies the schema family (LMC, BSG, MIXED, UNKNOWN) by marker keys.
    - Profiles are classified into a known family; MIXED/UNKNOWN flags that
      the profile mixes families or uses an unknown key set.
    - Distinguishes A from B: syntax valid ≠ schema valid.

    Returns:
        ValidationResult level B.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        keys = {child.attrib.get("name") for child in root if child.attrib.get("name") is not None}
    except ET.ParseError as e:
        return ValidationResult(
            level=ValidationLevel.B_SCHEMA,
            passed=False,
            details=f"Cannot classify schema: XML parse failed: {e}",
            evidence={"parse_error": str(e)},
        )
    except Exception as e:
        return ValidationResult(
            level=ValidationLevel.B_SCHEMA,
            passed=False,
            details=f"Schema classification error: {e}",
            evidence={"error": str(e)},
        )

    lmc_found, bsg_found = _extract_markers(keys)
    family = identify_schema_family(keys)

    # Determine pass/fail based on whether we can identify a known family
    # A profile that identifies as LMC or BSG passes; MIXED or UNKNOWN
    # flags that the key set is ambiguous or mixed, which is not a hard
    # "fail" but a warning state.
    if family in (SchemaFamily.LMC, SchemaFamily.BSG):
        passed = True
        lmc_str = ", ".join(sorted(lmc_found)) if lmc_found else "none"
        bsg_str = ", ".join(sorted(bsg_found)) if bsg_found else "none"
        details = (
            f"Schema identified: {family.value}. "
            f"LMC markers: {lmc_str}; BSG markers: {bsg_str}."
        )
    elif family == SchemaFamily.MIXED:
        passed = True  # not a failure, just ambiguous
        details = (
            f"Schema MIXED: profile contains markers from both LMC and BSG families. "
            f"These are not interchangeable unless the exact camera app supports both. "
            f"LMC markers: {', '.join(sorted(lmc_found)) or 'none'}; "
            f"BSG markers: {', '.join(sorted(bsg_found)) or 'none'}."
        )
    else:  # UNKNOWN
        passed = False
        details = (
            f"Schema UNKNOWN: no recognized LMC or BSG marker keys found. "
            f"The profile's key set does not match either the LMC 8.4 or BSG MGC "
            f"key-family patterns.  Cannot determine compatibility."
        )

    return ValidationResult(
        level=ValidationLevel.B_SCHEMA,
        passed=passed,
        details=details,
        evidence={
            "family": family.value,
            "lmc_markers": sorted(lmc_found),
            "bsg_markers": sorted(bsg_found),
        },
    )


#
# Level C: Camera Application Compatibility
#

# Mapping from schema family to compatibility statement.
# These are deterministic statements based on the key-family separation
# evidence from STAGE 1; they do NOT prove runtime compatibility.
COMPATIBILITY_STATEMENTS: Dict[SchemaFamily, str] = {
    SchemaFamily.LMC: (
        "XML syntax validation and LMC schema identification passed. "
        "This does NOT prove that LMC 8.4 on MT6878/IMX682 accepts every key. "
        "Some keys (see UNSUPPORTED_LMC_KEYS) are known not to be part of the "
        "valid parameter space for this device.  Runtime compatibility requires "
        "on-device testing; syntax validation alone is insufficient."
    ),
    SchemaFamily.BSG: (
        "XML syntax validation and BSG schema identification passed. "
        "This does NOT prove that MGC 9.4.103/9.8.102 accepts every key. "
        "BSG profiles use a distinct key namespace (pref_quality_key, "
        "camera_id_back, etc.) that is separate from LMC 8.4.  Mixing LMC and "
        "BSG profiles is unsupported unless the exact app build explicitly "
        "handles both families."
    ),
    SchemaFamily.MIXED: (
        "XML syntax passed but schema is MIXED.  This is a critical incompatibility "
        "risk: the profile contains both LMC and BSG marker keys.  LMC and BSG "
        "key families are NOT interchangeable.  Importing a MIXED-profile into "
        "an app that supports only one family may cause the app to ignore keys "
        "from the other family, or in some configurations, crash.  Do not merge "
        "incompatible profiles."
    ),
    SchemaFamily.UNKNOWN: (
        "XML syntax passed but schema is UNKNOWN.  No recognized marker keys "
        "were found.  The profile's key set cannot be classified as LMC or BSG. "
        "Compatibility with any camera app is unverified.  Treat as experimental "
        "only; do not import into a production app without runtime validation."
    ),
}


def check_compatibility(xml_path: str) -> ValidationResult:
    """Level C: Camera application compatibility validation.

    Checks:
    - Schema family is identified (Level B result).
    - Emits the appropriate compatibility statement for the identified family.
    - Flags MIXED and UNKNOWN families as having compatibility uncertainty.
    - Never confuses Level C (application compatibility) with Level A (syntax)
      or Level B (schema identification).

    Returns:
        ValidationResult level C.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        keys = {child.attrib.get("name") for child in root if child.attrib.get("name") is not None}
    except Exception as e:
        return ValidationResult(
            level=ValidationLevel.C_COMPAT,
            passed=False,
            details=f"Cannot assess compatibility: XML parse failed: {e}",
            evidence={"parse_error": str(e)},
        )

    family = identify_schema_family(keys)
    lmc_found, bsg_found = _extract_markers(keys)
    statement = COMPATIBILITY_STATEMENTS.get(family, "Unknown schema family")

    # Level C always "passes" in the sense that we can emit a deterministic
    # compatibility statement.  The value is the statement itself, not a
    # boolean pass/fail.  We set passed=True because the validation operation
    # completed successfully; the meaning of the result is the statement.
    return ValidationResult(
        level=ValidationLevel.C_COMPAT,
        passed=True,
        details=statement,
        evidence={
            "family": family.value,
            "lmc_markers": sorted(lmc_found),
            "bsg_markers": sorted(bsg_found),
        },
    )


#
# Level D: Actual Device Validation
#

def check_device(
    xml_path: str,
    camera_manager: Optional[object] = None,
) -> ValidationResult:
    """Level D: Actual device validation.

    Checks:
    - Requires on-device Camera2 characteristics access via CameraManager.
    - Without a real device and CameraManager instance, this level CANNOT be
      performed and will always report BLOCKED.
    - This level MUST NOT be faked or inferred from XML syntax alone.

    The mission rules (section 8, section 12) explicitly state:
    - "Never confuse these four validation levels."
    - "Never claim device compatibility from XML syntax alone."
    - "Never modify firmware, NVRAM, NVDATA, secure storage, or protected partitions."
    - "Do not launch a camera test session."

    Returns:
        ValidationResult level D with passed=False and details="BLOCKED:
        requires on-device Camera2 characteristics access.  No device attached
        in this environment."
    """
    # In the Termux/repo environment without an actual connected device running
    # the target app, Level D cannot be performed.  We must not fake it.
    # The result is BLOCKED, not FAIL — the validation operation itself
    # cannot be completed, not that the profile is invalid.
    return ValidationResult(
        level=ValidationLevel.D_DEVICE,
        passed=False,
        details="BLOCKED: requires on-device Camera2 characteristics access via "
                "android.hardware.camera2.CameraManager.  No device attached in "
                "this Termux/repo environment.  Level D must not be inferred from "
                "XML syntax or schema alone (mission rule: never confuse levels A–C "
                "with level D).",
        evidence={
            "block_reason": "no_device",
            "requirement": "android.hardware.camera2.CameraManager + device "
                           "running target camera app (LMC 8.4 or MGC 9.4.103)",
        },
    )


#
# Duplicate profile detection (inter-file)
#

def compute_sha256(path: str) -> str:
    """Compute SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_duplicate_profiles(
    paths: List[str],
) -> Dict[str, List[str]]:
    """Find inter-file duplicate profiles based on SHA-256 hash.

    Groups files by identical content (byte-identical SHA-256).

    Returns:
        Dict mapping hash -> list of file paths that share that hash.
        Only groups with 2+ files are included.
    """
    by_hash: Dict[str, List[str]] = {}
    for p in paths:
        try:
            h = compute_sha256(p)
            by_hash.setdefault(h, []).append(p)
        except OSError:
            pass  # skip files we can't read

    # Keep only groups with 2+ files (actual duplicates)
    duplicates = {h: plist for h, plist in by_hash.items() if len(plist) > 1}
    return duplicates


def audit_directory_profiles(
    directory: str,
) -> Dict[str, any]:
    """Audit all XML profiles in a directory for duplicates and schema.

    Returns a summary dict with:
    - total_files: count of XML files found
    - duplicate_groups: dict of hash -> [file paths] for duplicates
    - schema_counts: dict of SchemaFamily -> count of profiles in that family
    - well_formed_count: number of files that pass Level A syntax check
    """
    import os

    # Collect all XML paths
    xml_paths: List[str] = []
    for root_dir, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(".xml"):
                xml_paths.append(os.path.join(root_dir, f))

    total_files = len(xml_paths)

    # Find duplicates
    duplicates = find_duplicate_profiles(xml_paths)

    # Schema family counts
    schema_counts: Dict[SchemaFamily, int] = {}
    for path in xml_paths:
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            keys = {child.attrib.get("name") for child in root if child.attrib.get("name") is not None}
            family = identify_schema_family(keys)
            schema_counts[family] = schema_counts.get(family, 0) + 1
        except Exception:
            schema_counts["UNKNOWN"] = schema_counts.get("UNKNOWN", 0) + 1

    # Well-formed count
    well_formed_count = 0
    for path in xml_paths:
        result = check_syntax(path)
        if result.passed:
            well_formed_count += 1

    return {
        "total_files": total_files,
        "duplicate_groups": {
            h: plist for h, plist in duplicates.items()
        },
        "schema_counts": {k.value: v for k, v in schema_counts.items()},
        "well_formed_count": well_formed_count,
        "well_formed_percent": round(100 * well_formed_count / total_files, 1) if total_files > 0 else 0,
    }


#
# Full validation orchestration
#

def validate_xml_complete(
    xml_path: str,
    camera_manager: Optional[object] = None,
) -> FullValidationReport:
    """Run all four validation levels and produce a FullValidationReport.

    This is the primary public API for end-to-end XML validation.  It respects
    the separation of levels A–D and never confuses them.

    Args:
        xml_path: Path to the XML profile file.
        camera_manager: Optional CameraManager instance for Level D.  If None,
            Level D will be reported as BLOCKED.

    Returns:
        FullValidationReport with all four level results and an overall pass/fail.
    """
    # Level A: Syntax
    level_a = check_syntax(xml_path)

    # Level B: Schema
    level_b = check_schema(xml_path)

    # Level C: Compatibility
    level_c = check_compatibility(xml_path)

    # Level D: Device
    level_d = check_device(xml_path, camera_manager=camera_manager)

    # Overall: passed only if ALL levels pass (Level D blocked = overall not passed)
    overall_passed = all(r.passed for r in [level_a, level_b, level_c]) and level_d.passed

    return FullValidationReport(
        xml_path=xml_path,
        level_a_syntax=level_a,
        level_b_schema=level_b,
        level_c_compat=level_c,
        level_d_device=level_d,
        overall_passed=overall_passed,
    )


if __name__ == "__main__":
    # Demo: validate a few profiles from the repo
    import sys

    test_files = sys.argv[1:] or [
        "profiles/LXX521_IMX682_AllInOne_V3.xml",
        "profiles/LXX521_BSG_Master.xml",
        "profiles/LXX521_BSG_Pro.xml",
        "LXX521_IMX682_Super_AllInOne_V4.xml",
        "LXX521_FrontCam_Only_Sanitized.xml",
    ]

    print("=" * 70)
    print("XML Complete Validation (Levels A-D)")
    print("=" * 70)

    for path in test_files:
        try:
            report = validate_xml_complete(path)
            print(f"\n{path}")
            print(report.summary())
        except Exception as e:
            print(f"\n{path}: ERROR running validation: {str(e)[:100]}")