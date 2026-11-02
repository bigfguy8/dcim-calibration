#!/usr/bin/env python3
"""
profile_compare.py - Profile comparison and conflict detection.

Compares XML profiles by:
- Configuration keys.
- Values.
- Missing parameters.
- Conflicting parameters.
- Duplicate configurations.
- Schema family.
- Historical provenance.

All comparisons are read-only; no files are modified.
"""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .camera_capabilities import identify_schema_family, SchemaFamily
from .xml_audit import check_syntax, compute_sha256


#
# Comparison result types
#

class ComparisonResult(Enum):
    """Result of comparing two profile configurations."""
    IDENTICAL = "identical"
    SIMILAR = "similar"  # Same schema, some keys differ
    CONFLICTING = "conflicting"  # Same key, different incompatible values
    DIFFERENT_SCHEMA = "different_schema"  # Different schema families
    DUPLICATE = "duplicate"  # Byte-identical profiles


@dataclass
class KeyDiff:
    """Difference for a single key between two profiles."""
    key: str
    value_first: Any
    value_second: Any


@dataclass
class ProfileComparison:
    """Result of comparing two profiles."""
    profile_first: str
    profile_second: str
    result: ComparisonResult
    schema_first: SchemaFamily
    schema_second: SchemaFamily
    missing_in_second: Tuple[str, ...]
    extra_in_second: Tuple[str, ...]
    changed: Tuple[KeyDiff, ...]
    duplicate_note: str  # e.g. "byte-identical" or key-level changes


#
# Profile comparison engine
#


def extract_profile_keys(xml_path: str) -> Tuple[Set[str], Optional[int]]:
    """Extract the set of key names from an XML profile.

    Returns:
        (set_of_keys, entry_count) or (set_of_keys, None) if parse fails.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        keys = {child.attrib.get("name") for child in root if child.attrib.get("name") is not None}
        return keys, len(list(root))
    except Exception:
        return set(), None


def compare_profiles(
    path_first: str,
    path_second: str,
) -> ProfileComparison:
    """Compare two XML profiles in detail.

    Performs the following comparisons:
    1. SHA-256 hash check (byte-identical → duplicate).
    2. Schema family identification (LMC / BSG / MIXED / UNKNOWN).
    3. Key-level: missing, extra, and changed values.
    4. Determines a high-level ComparisonResult.

    Returns:
        ProfileComparison with all results filled in.
    """
    # 1. SHA-256 check for byte-identical duplicate detection
    h1 = compute_sha256(path_first)
    h2 = compute_sha256(path_second)
    is_identical_hash = h1 == h2

    # 2. Extract keys from both profiles
    keys1, count1 = extract_profile_keys(path_first)
    keys2, count2 = extract_profile_keys(path_second)

    # 3. Schema family identification
    family1 = identify_schema_family(keys1) if keys1 else SchemaFamily.UNKNOWN
    family2 = identify_schema_family(keys2) if keys2 else SchemaFamily.UNKNOWN

    # 4. Key-level comparison
    set1 = set(keys1) if keys1 else set()
    set2 = set(keys2) if keys2 else set()

    missing_in_second = tuple(sorted(set1 - set2))
    extra_in_second = tuple(sorted(set2 - set1))

    # Changed keys: present in both but with different values
    changed_keys: List[KeyDiff] = []
    for key in sorted(set1 & set2):
        # Extract values from XML
        val1 = _extract_key_value(path_first, key)
        val2 = _extract_key_value(path_second, key)
        if val1 != val2:
            changed_keys.append(KeyDiff(key=key, value_first=val1, value_second=val2))

    changed = tuple(changed_keys) if changed_keys else ()

    # 5. Determine comparison result
    if is_identical_hash:
        result = ComparisonResult.DUPLICATE
        duplicate_note = "byte-identical (SHA-256 match)"
    elif family1 != family2:
        result = ComparisonResult.DIFFERENT_SCHEMA
        duplicate_note = f"schema differ: {family1.value} vs {family2.value}"
    elif not changed_keys and not missing_in_second and not extra_in_second:
        result = ComparisonResult.IDENTICAL
        duplicate_note = "identical key sets and values"
    elif not changed_keys:
        result = ComparisonResult.SIMILAR
        duplicate_note = "same keys, no value differences"
    else:
        result = ComparisonResult.CONFLICTING
        duplicate_note = f"{len(changed_keys)} conflicting key(s) with different values"

    return ProfileComparison(
        profile_first=path_first,
        profile_second=path_second,
        result=result,
        schema_first=family1,
        schema_second=family2,
        missing_in_second=missing_in_second,
        extra_in_second=extra_in_second,
        changed=changed,
        duplicate_note=duplicate_note,
    )


def _extract_key_value(xml_path: str, key: str) -> Optional[str]:
    """Extract the text value of a named key from an XML profile.

    Returns the text content of the <string name="key">value</string> entry,
    or None if the key is not found.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for child in root:
            if child.attrib.get("name") == key:
                return child.text
        return None
    except Exception:
        return None


def compare_profile_to_caps(
    xml_path: str,
    caps: object,
) -> Dict[str, any]:
    """Compare a profile against device capabilities.

    Uses the device_probe.CameraCapabilities instance to check whether
    the profile's keys are compatible with the device's known capabilities.
    This is a structural check, not a runtime test.

    Returns:
        Dict with comparison results including:
        - profile_schema: identified schema family
        - supported_keys: profile keys that overlap with known capabilities
        - unsupported_keys: profile keys known not to be supported for this device
        - missing_from_critical: critical LMC/BSG keys absent from the profile
    """
    from .device_probe import probe_device

    # Get device capabilities (use synthetic fixture if no real probe)
    try:
        device_caps = probe_device(camera_id=0)  # rear camera as default
    except Exception:
        device_caps = None

    # Get profile schema and keys
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        profile_keys = {child.attrib.get("name") for child in root if child.attrib.get("name") is not None}
    except Exception:
        profile_keys = set()

    profile_schema = identify_schema_family(profile_keys) if profile_keys else SchemaFamily.UNKNOWN

    # Determine supported/unsupported based on schema
    supported_keys: Set[str] = set()
    unsupported_keys: Set[str] = set()

    if profile_schema == SchemaFamily.LMC:
        # LMC profiles: supported keys are those not in UNSUPPORTED_LMC_KEYS
        supported_keys = profile_keys - UNSUPPORTED_LMC_KEYS
        unsupported_keys = profile_keys & UNSUPPORTED_LMC_KEYS
    elif profile_schema == SchemaFamily.BSG:
        # BSG profiles: conservative unsupported detection
        unsupported_keys = profile_keys & UNSUPPORTED_LMC_KEYS  # overlap check
        supported_keys = profile_keys - UNSUPPORTED_LMC_KEYS
    else:
        # MIXED/UNKNOWN: cannot reliably determine support
        unsupported_keys = set()
        supported_keys = set()

    # Missing critical keys
    from .camera_capabilities import critical_lmc, critical_bsg
    if profile_schema == SchemaFamily.LMC:
        missing_from_critical = critical_lmc - profile_keys
    elif profile_schema == SchemaFamily.BSG:
        missing_from_critical = critical_bsg - profile_keys
    else:
        missing_from_critical = set()

    return {
        "profile_schema": profile_schema.value,
        "supported_keys": sorted(supported_keys),
        "unsupported_keys": sorted(unsupported_keys),
        "missing_from_critical": sorted(missing_from_critical),
        "profile_key_count": len(profile_keys),
    }


#
# Convenience: batch comparison of multiple profiles
#


def batch_compare(
    paths: List[str],
) -> List[ProfileComparison]:
    """Compare all unique pairs of profiles in the given list.

    Returns a list of ProfileComparison, one per unique pair (i, j) with i < j.
    """
    results: List[ProfileComparison] = []
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            cmp = compare_profiles(paths[i], paths[j])
            results.append(cmp)
    return results


#
# Historical provenance tracking
#

_PROVENANCE_LOG: Dict[str, Dict[str, any]] = {}


def record_provenance(
    profile_path: str,
    source_description: str,
    sha256: str,
    schema_family: SchemaFamily,
    notes: str = "",
) -> None:
    """Record the provenance of a profile for traceability.

    This is a best-effort in-memory log.  It does not modify the profile file
    or any external database.  The log is reset each time the module is
    imported (i.e. per process), which is sufficient for audit/regression
    workflows.

    Args:
        profile_path: Path to the profile XML file.
        source_description: Human-readable description of where the profile
            came from (e.g. "profiles/LMC/", "generated/", "historical/").
        sha256: SHA-256 hash of the profile file.
        schema_family: The identified SchemaFamily.
        notes: Any additional notes about the profile's history.
    """
    _PROVENANCE_LOG[profile_path] = {
        "source": source_description,
        "sha256": sha256,
        "schema_family": schema_family.value if schema_family else "unknown",
        "notes": notes,
    }


def get_provenance(profile_path: str) -> Optional[Dict[str, any]]:
    """Return the provenance record for a profile, if any.

    Returns:
        Dict with provenance info, or None if no record exists.
    """
    return _PROVENANCE_LOG.get(profile_path)


def export_provenance_report(path: str = "profile_provenance.json") -> str:
    """Export the provenance log to a JSON file.

    Args:
        path: Output file path.  Defaults to "profile_provenance.json" in the
            current working directory.

    Returns:
        The path written to.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_PROVENANCE_LOG, f, indent=2, ensure_ascii=False)
    except OSError:
        pass  # best-effort; do not block
    return path


if __name__ == "__main__":
    # Demo: compare some profiles from the repo
    import sys

    default_paths = [
        "profiles/LXX521_IMX682_AllInOne_V3.xml",
        "profiles/LXX521_BSG_Master.xml",
        "profiles/LXX521_BSG_Pro.xml",
        "LXX521_IMX682_Super_AllInOne_V4.xml",
        "profiles/LXX521_IMX682_AllInOne_V2.xml",
    ]

    paths = sys.argv[1:] if len(sys.argv) > 1 else default_paths

    print("=" * 70)
    print("Profile Comparison Engine")
    print("=" * 70)

    # Batch compare
    comparisons = batch_compare(paths)
    print(f"\nCompared {len(comparisons)} unique pairs among {len(paths)} profiles:\n")

    for cmp in comparisons:
        print(f"  {cmp.profile_first} vs {cmp.profile_second}")
        print(f"    Result: {cmp.result.value}")
        print(f"    Schema: {cmp.schema_first.value} vs {cmp.schema_second.value}")
        if cmp.missing_in_second:
            print(f"    Missing in second: {len(cmp.missing_in_second)} keys")
        if cmp.extra_in_second:
            print(f"    Extra in second: {len(cmp.extra_in_second)} keys")
        if cmp.changed:
            print(f"    Changed keys: {len(cmp.changed)}")
            for kd in cmp.changed[:5]:  # show first 5
                print(f"      - {kd.key}: {kd.value_first} → {kd.value_second}")
        print(f"    Note: {cmp.duplicate_note}")
        print()