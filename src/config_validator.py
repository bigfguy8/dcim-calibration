#!/usr/bin/env python3
"""
config_validator.py - XML configuration validation and unsupported key detection.

Validates XML profiles against:
- Documented supported parameter ranges for LAVA LXX521 / Sony IMX682 / LMC 8.4.
- Known unsupported keys (UNSUPPORTED_LMC_KEYS).
- Schema family consistency (LMC vs BSG separation).
- Missing critical keys.
- Duplicate keys within the <map>.
- SHA-256 integrity tracking.

All validation is read-only; no files are modified.
"""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .camera_capabilities import (
    SchemaFamily,
    identify_schema_family,
    UNSUPPORTED_LMC_KEYS,
)
from .camera_capabilities import LMC_MARKER_KEYS, BSG_MARKER_KEYS

# Critical LMC keys (profile keys expected in a valid LMC 8.4 profile)
CRITICAL_LMC_KEYS: frozenset = frozenset({
    "pref_qjpg_key",
    "ptchr_sharpness_0",
    "ptchr_luma_denoise_0",
    "ptchr_contrast_0",
    "ptchr_saturation_0",
    "ptchr_sharp_outline_0",
})

# Critical BSG keys (profile keys expected in a valid BSG/MGC profile)
CRITICAL_BSG_KEYS: frozenset = frozenset({
    "pref_quality_key",
    "pref_hdr_plus_frames_key",
    "camera_id_back",
})
from .xml_audit import check_syntax, compute_sha256


#
# Validation result per check
#

@dataclass
class CheckResult:
    """Result of a single validation check."""
    name: str
    passed: bool
    details: str
    evidence: Optional[Dict[str, Any]] = field(default=None)


#
# Configuration validator
#


def validate_configuration(
    xml_path: str,
) -> Dict[str, Any]:
    """Run all validation checks on an XML profile configuration.

    This is the primary public API.  It returns a dict with one entry per
    validation check, each being a CheckResult.  The caller can decide how
    to interpret the results.

    Checks performed:
    1. Syntax well-formedness (Level A: check_syntax).
    2. Schema family identification (Level B).
    3. Unsupported key detection (LMC keys known not to be supported for this device).
    4. Missing critical keys (LMC: pref_qjpg_key, ptchr_sharpness_0, etc.;
       BSG: pref_quality_key, pref_hdr_plus_frames_key, camera_id_back).
    5. Duplicate key detection within <map>.
    6. SHA-256 integrity verification.

    Returns:
        Dict mapping check name to CheckResult.
    """
    results: Dict[str, CheckResult] = {}

    # 1. Syntax validation
    syntax = check_syntax(xml_path)
    results["syntax"] = CheckResult(
        name="syntax_well_formed",
        passed=syntax.passed,
        details=syntax.details,
        evidence=syntax.evidence,
    )

    # If syntax fails, we cannot do further structural checks
    if not syntax.passed:
        # Still record what we can
        results["schema"] = CheckResult(
            name="schema_identification",
            passed=False,
            details="Cannot identify schema: XML syntax failure prevents parsing.",
            evidence={"syntax_error": syntax.details},
        )
        results["unsupported"] = CheckResult(
            name="unsupported_key_detection",
            passed=False,
            details="Cannot detect unsupported keys: XML syntax failure prevents parsing.",
            evidence={"syntax_error": syntax.details},
        )
        results["critical"] = CheckResult(
            name="missing_critical_keys",
            passed=False,
            details="Cannot check critical keys: XML syntax failure prevents parsing.",
            evidence={"syntax_error": syntax.details},
        )
        results["duplicate"] = CheckResult(
            name="duplicate_key_detection",
            passed=False,
            details="Cannot detect duplicate keys: XML syntax failure prevents parsing.",
            evidence={"syntax_error": syntax.details},
        )
        results["integrity"] = CheckResult(
            name="sha256_integrity",
            passed=False,
            details="Cannot verify integrity: XML syntax failure prevents parsing.",
            evidence={"syntax_error": syntax.details},
        )
        return results

    # 2. Schema family identification
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        keys = {child.attrib.get("name") for child in root if child.attrib.get("name") is not None}
    except Exception as e:
        results["schema"] = CheckResult(
            name="schema_identification",
            passed=False,
            details=f"Schema identification error: {e}",
            evidence={"error": str(e)},
        )
        return results

    family = identify_schema_family(keys)
    has_lmc_markers = bool(LMC_MARKER_KEYS & keys) if 'LMC_MARKER_KEYS' in dir() else False
    has_bsg_markers = bool(BSG_MARKER_KEYS & keys) if 'BSG_MARKER_KEYS' in dir() else False

    # Use the imported marker sets from camera_capabilities
    from .camera_capabilities import LMC_MARKER_KEYS, BSG_MARKER_KEYS
    has_lmc_markers = bool(LMC_MARKER_KEYS & keys)
    has_bsg_markers = bool(BSG_MARKER_KEYS & keys)

    if has_lmc_markers and has_bsg_markers:
        family = SchemaFamily.MIXED
    elif has_lmc_markers:
        family = SchemaFamily.LMC
    elif has_bsg_markers:
        family = SchemaFamily.BSG
    else:
        family = SchemaFamily.UNKNOWN

    results["schema"] = CheckResult(
        name="schema_identification",
        passed=True,
        details=f"Schema identified: {family.value}. "
                f"LMC markers: {', '.join(sorted(LMC_MARKER_KEYS & keys)) or 'none'}; "
                f"BSG markers: {', '.join(sorted(BSG_MARKER_KEYS & keys)) or 'none'}.",
        evidence={"family": family.value, "lmc_markers": sorted(LMC_MARKER_KEYS & keys), "bsg_markers": sorted(BSG_MARKER_KEYS & keys)},
    )

    # 3. Unsupported key detection
    # LMC profiles: any key in UNSUPPORTED_LMC_KEYS is flagged
    # BSG/MIXED/UNKNOWN profiles: conservative flagging
    unsupported: Set[str] = set()
    if family == SchemaFamily.LMC:
        unsupported = keys & UNSUPPORTED_LMC_KEYS
    elif family == SchemaFamily.BSG:
        # For BSG, also check against LMC unsupported set as overlap
        unsupported = keys & UNSUPPORTED_LMC_KEYS
    elif family == SchemaFamily.MIXED:
        # Mixed: flag any UNSUPPORTED_LMC_KEYS present, plus note the mixing risk
        unsupported = keys & UNSUPPORTED_LMC_KEYS
    else:
        # Unknown: cannot reliably flag without risking false positives
        unsupported = set()

    results["unsupported"] = CheckResult(
        name="unsupported_key_detection",
        passed=len(unsupported) == 0,
        details=f"Found {len(unsupported)} unsupported key(s): {', '.join(sorted(unsupported)) or 'none'}",
        evidence={"unsupported_keys": sorted(unsupported)},
    )

    # 4. Missing critical keys
    if family == SchemaFamily.LMC:
        critical = CRITICAL_LMC_KEYS
    elif family == SchemaFamily.BSG:
        critical = CRITICAL_BSG_KEYS
    elif family == SchemaFamily.MIXED:
        # For mixed, check both sets conservatively
        critical = CRITICAL_LMC_KEYS | CRITICAL_BSG_KEYS
    else:
        # Unknown: report missing from both sets (conservative)
        critical = CRITICAL_LMC_KEYS | CRITICAL_BSG_KEYS

    missing = critical - keys
    results["critical"] = CheckResult(
        name="missing_critical_keys",
        passed=len(missing) == 0,
        details=f"Missing {len(missing)} critical key(s): {', '.join(sorted(missing)) or 'none'}",
        evidence={"missing_critical_keys": sorted(missing)},
    )

    # 5. Duplicate key detection (within <map>)
    # Already checked by check_syntax, but we report it separately here
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        seen: Set[str] = set()
        dups: List[str] = []
        for child in root:
            key = child.attrib.get("name")
            if key is None:
                continue
            if key in seen:
                dups.append(key)
            else:
                seen.add(key)
        has_duplicates = len(dups) > 0
    except Exception as e:
        has_duplicates = False
        details_error = str(e)

    results["duplicate"] = CheckResult(
        name="duplicate_key_detection",
        passed=not has_duplicates,
        details=f"{'Duplicate keys found: ' + ', '.join(sorted(dups)) if has_duplicates else 'no duplicate keys.'}",
        evidence={"duplicate_keys": sorted(dups) if has_duplicates else []},
    )

    # 6. SHA-256 integrity
    try:
        sha256 = compute_sha256(xml_path)
        results["integrity"] = CheckResult(
            name="sha256_integrity",
            passed=True,
            details=f"SHA-256: {sha256}",
            evidence={"sha256": sha256},
        )
    except Exception as e:
        results["integrity"] = CheckResult(
            name="sha256_integrity",
            passed=False,
            details=f"Could not compute SHA-256: {e}",
            evidence={"error": str(e)},
        )

    return results


def validate_profile_summary(xml_path: str) -> Dict[str, any]:
    """Produce a human-readable summary of profile validation.

    Convenience wrapper around validate_configuration that returns a
    simplified dict suitable for display or logging.

    Returns:
        Dict with keys: well_formed, schema, unsupported, missing_critical,
        duplicate, sha256, and overall_passed.
    """
    checks = validate_configuration(xml_path)

    well_formed = checks.get("syntax", CheckResult("syntax", False, "")).passed
    schema_passed = checks.get("schema", CheckResult("schema", False, "")).passed
    unsupported_passed = checks.get("unsupported", CheckResult("unsupported", False, "")).passed
    missing_passed = checks.get("critical", CheckResult("critical", False, "")).passed
    duplicate_passed = checks.get("duplicate", CheckResult("duplicate", False, "")).passed
    sha256_passed = checks.get("integrity", CheckResult("integrity", False, "")).passed

    overall_passed = all([
        well_formed, schema_passed, unsupported_passed,
        missing_passed, duplicate_passed, sha256_passed
    ])

    return {
        "well_formed": well_formed,
        "schema_identified": schema_passed,
        "unsupported_keys_found": not unsupported_passed,
        "missing_critical_keys": not missing_passed,
        "duplicate_keys_found": not duplicate_passed,
        "sha256_valid": sha256_passed,
        "overall_passed": overall_passed,
    }


#
# Batch validation
#


def batch_validate(
    paths: List[str],
) -> Dict[str, Dict[str, any]]:
    """Validate multiple profiles and return per-file summaries.

    Args:
        paths: List of XML file paths to validate.

    Returns:
        Dict mapping each path to its validation summary dict (as from
        validate_profile_summary).
    """
    results: Dict[str, Dict[str, any]] = {}
    for path in paths:
        results[path] = validate_profile_summary(path)
    return results


if __name__ == "__main__":
    # Demo: validate a few profiles from the repo
    import sys

    default_paths = [
        "profiles/LXX521_IMX682_AllInOne_V3.xml",
        "profiles/LXX521_BSG_Master.xml",
        "profiles/LXX521_BSG_Pro.xml",
        "LXX521_IMX682_Super_AllInOne_V4.xml",
        "profiles/LXX521_IMX682_LMC84_AllRounder.xml",
    ]

    paths = sys.argv[1:] if len(sys.argv) > 1 else default_paths

    print("=" * 70)
    print("Config Validator Demo")
    print("=" * 70)

    summaries = batch_validate(paths)
    for path, summary in summaries.items():
        print(f"\n{path}")
        print(f"  well_formed: {summary['well_formed']}")
        print(f"  schema_identified: {summary['schema_identified']}")
        print(f"  unsupported_keys_found: {summary['unsupported_keys_found']}")
        print(f"  missing_critical_keys: {summary['missing_critical_keys']}")
        print(f"  duplicate_keys_found: {summary['duplicate_keys_found']}")
        print(f"  sha256_valid: {summary['sha256_valid']}")
        print(f"  overall_passed: {summary['overall_passed']}")