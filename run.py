#!/usr/bin/env python3
"""run.py — Safe CLI entry point for LAVA LXX521 / IMX682 DCIM Calibration.

Provides read-only and dry-run commands only. Never automatically deploys
configurations to the Android camera application.

Commands:
  python run.py audit           — Run XML syntax and schema validation
  python run.py validate        — Validate XML profile structure
  python run.py compare         — Compare two profiles
  python run.py deploy          — Dry-run deployment (no file writes)
  python run.py help            — Show help output
"""
from __future__ import annotations

import sys
from pathlib import Path

# Project root is the parent of src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add src/ to path so we can import the engine modules
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def cmd_audit(args):
    """Read-only audit command.

    Runs XML syntax and schema validation on all profiles in the repository.
    No files are modified. No device writes are performed.
    """
    from src.xml_audit import validate_xml_complete, audit_directory_profiles, FullValidationReport
    import glob

    # Determine which files to validate
    if args.profile:
        files = [Path(args.profile)]
        file_globs = []
    else:
        # Scan profiles/ and analysis_results/imx682_config/ directories
        files = []
        repo_root = PROJECT_ROOT
        for d in ["profiles", "analysis_results/imx682_config"]:
            p = repo_root / d
            if p.is_dir():
                files.extend(p.rglob("*.xml"))
        # Also include top-level LXX521_*.xml files
        files.extend(repo_root.glob("LXX521_*.xml"))
        files = [f for f in files if f.is_file()]

    if not files:
        print("No XML profiles found for audit.")
        return 0

    print(f"Auditing {len(files)} XML profile(s)...\n")

    errors = 0
    for filepath in sorted(files, key=lambda f: f.name):
        try:
            report = validate_xml_complete(str(filepath))
            print(report.summary())
            if not report.overall_passed:
                errors += 1
        except Exception as e:
            print(f"{filepath.name}: ERROR running validation: {str(e)[:100]}")
            errors += 1

    print()
    if errors == 0:
        print(f"All {len(files)} profiles passed validation (Level A–C).")
    else:
        print(f"{errors} profile(s) had validation failures (Levels A–C).")

    return 0 if errors == 0 else 1


def cmd_validate(args):
    """Validate XML profile structure command.

    Runs configuration validation checks on a specific profile:
    syntax, schema identification, unsupported key detection,
    missing critical keys, duplicate key detection, and SHA-256 integrity.
    """
    from src.config_validator import validate_profile_summary

    profile_path = Path(args.profile)
    if not profile_path.is_file():
        print(f"Error: Profile not found: {args.profile}")
        return 1

    summary = validate_profile_summary(str(profile_path))

    print(f"Profile: {profile_path.name}")
    print(f"  well_formed: {summary['well_formed']}")
    print(f"  schema_identified: {summary['schema_identified']}")
    print(f"  unsupported_keys_found: {summary['unsupported_keys_found']}")
    print(f"  missing_critical_keys: {summary['missing_critical_keys']}")
    print(f"  duplicate_keys_found: {summary['duplicate_keys_found']}")
    print(f"  sha256_valid: {summary['sha256_valid']}")
    print(f"  overall_passed: {summary['overall_passed']}")

    if not summary['overall_passed']:
        print("\nProfile has one or more validation issues.")
        return 1

    print("\nProfile validation passed.")
    return 0


def cmd_compare(args):
    """Compare two profiles command.

    Compares two XML profiles by keys, values, schema family, and
    SHA-256 hash.  All comparisons are read-only.
    """
    from src.profile_compare import compare_profiles

    path1 = Path(args.profile1)
    path2 = Path(args.profile2)

    if not path1.is_file():
        print(f"Error: Profile not found: {args.profile1}")
        return 1
    if not path2.is_file():
        print(f"Error: Profile not found: {args.profile2}")
        return 1

    cmp = compare_profiles(str(path1), str(path2))

    print(f"Comparing {cmp.profile_first} vs {cmp.profile_second}")
    print(f"  Result: {cmp.result.value}")
    print(f"  Schema: {cmp.schema_first.value} vs {cmp.schema_second.value}")
    if cmp.missing_in_second:
        print(f"  Missing in second: {len(cmp.missing_in_second)} keys")
    if cmp.extra_in_second:
        print(f"  Extra in second: {len(cmp.extra_in_second)} keys")
    if cmp.changed:
        print(f"  Changed keys: {len(cmp.changed)}")
        for kd in cmp.changed[:5]:
            print(f"    - {kd.key}: {kd.value_first} → {kd.value_second}")
    print(f"  Note: {cmp.duplicate_note}")

    return 0


def cmd_deploy(args):
    """Dry-run deployment command.

    Validates the profile and reports the result without writing any files.
    No configuration is automatically deployed to the Android camera application.
    """
    from src.deployment import deploy_profile, DeployResult

    profile_path = Path(args.profile)
    if not profile_path.is_file():
        print(f"Error: Profile not found: {args.profile}")
        return 1

    # Dry-run: no file operations, just validation
    output = deploy_profile(str(profile_path), dry_run=True, confirm=False)

    print(f"Profile: {profile_path.name}")
    print(f"  Result: {output.result.value}")
    print(f"  Message: {output.message}")

    if output.result == DeployResult.DRY_RUN:
        print(f"\n( Dry-run completed — no files were modified on disk. )")
        return 0
    elif output.result == DeployResult.VALIDATION_FAILED:
        print("\nProfile failed validation — deployment aborted.")
        return 1
    else:
        # For other results (SUCCESS would mean actual deployment,
        # but dry-run mode should not produce SUCCESS without user confirmation)
        print(f"\nDeployment result: {output.result.value}")
        return 0

    return 0 if output.result.value in ("success", "dry_run") else 1


def cmd_help():
    """Show help output."""
    print(__doc__)
    return 0


#
# Main dispatch
#


def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py <command> [options]")
        print()
        print("Commands:")
        print("  audit       — Read-only XML syntax and schema audit")
        print("  validate    — Validate XML profile structure")
        print("  compare     — Compare two profiles (usage: compare <file1> <file2>)")
        print("  deploy      — Dry-run deployment validation (no writes)")
        print("  help        — Show this help output")
        print()
        print("Run 'python run.py help' for detailed command help.")
        return 1

    command = sys.argv[1].lower()

    # Handle 'help' explicitly before trying subcommand parsing
    if command == "help":
        return cmd_help()

    # Dispatch by command
    if command == "audit":
        from argparse import ArgumentParser
        parser = ArgumentParser(description="Read-only XML audit command")
        parser.add_argument("--profile", help="Single profile to validate (optional; scans all if omitted)")
        args = parser.parse_args(sys.argv[2:])
        return cmd_audit(args)

    if command == "validate":
        from argparse import ArgumentParser
        parser = ArgumentParser(description="Validate XML profile structure")
        parser.add_argument("--profile", required=True, help="Path to the XML profile to validate")
        args = parser.parse_args(sys.argv[2:])
        return cmd_validate(args)

    if command == "compare":
        from argparse import ArgumentParser
        parser = ArgumentParser(description="Compare two profiles")
        parser.add_argument("--profile1", required=True, help="Path to first profile")
        parser.add_argument("--profile2", required=True, help="Path to second profile")
        args = parser.parse_args(sys.argv[2:])
        return cmd_compare(args)

    if command == "deploy":
        from argparse import ArgumentParser
        from src.deployment import DeployResult
        parser = ArgumentParser(description="Dry-run deployment validation (no writes)")
        parser.add_argument("--profile", required=True, help="Path to the XML profile to deploy (dry-run only)")
        args = parser.parse_args(sys.argv[2:])
        return cmd_deploy(args)

    print(f"Unknown command: {command}")
    print("Run 'python run.py help' for available commands.")
    return 1


if __name__ == "__main__":
    sys.exit(main())