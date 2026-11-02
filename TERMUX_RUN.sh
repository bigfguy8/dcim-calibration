#!/bin/bash
# TERMUX RUN — LAVA LXX521 / IMX682 GCam Calibration Engine
#
# This script provides CLI entry points for the DCIM Calibration engine.
# It supports audit, deployment, profile comparison, and test execution.
#
# Usage:
#   python3 src/xml_audit.py --help
#   python3 src/profile_manager list_profiles
#   python3 src/deployment deploy_interactive --dry-run
#   python3 -m pytest tests/
#
# Recommended shared storage: ~/storage/shared/Download/DCIM_Calibration/
#
# This script MUST NOT modify firmware, NVRAM, NVDATA, or secure storage.
# All operations are read-only unless explicitly deploying a profile.
#
# Copyright (C) 2026 LAVA LXX521 DCIM Calibration Project
# ALL RIGHTS RESERVED. See LICENSE for build terms.

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────────

# Project root directory
PROJECT_ROOT="${HOME}/dcim-calibration-engine"

# Preferred shared storage directory (per mission §12)
PREFERRED_DIR="${HOME}/storage/shared/Download/DCIM_Calibration"

# ─── Help / Usage ────────────────────────────────────────────────────────

if [ $# -eq 0 ]; then
    echo "=== TERMUX RUN — LAVA LXX521 / IMX682 ==="
    echo ""
    echo "Usage: python3 <module> [options]"
    echo ""
    echo "Available modules:"
    echo "  src/xml_audit.py        — Four-level XML validation (Levels A-D)"
    echo "  src/profile_manager.py  — List/profiles management"
    echo "  src/deployment.py       — Safe deployment with backup/rollback"
    echo "  src/config_generator.py — Candidate profile generation"
    echo "  src/config_validator.py — XML validation and unsupported key detection"
    echo ""
    echo "Or run the test suite:"
    echo "  python3 -m pytest tests/"
    echo ""
    echo "For Termux-specific operations, see TERMUX_INSTALL.sh"
    echo ""
    exit 1
fi

# ─── Module dispatch ──────────────────────────────────────────────────────

CASE="${1:-}"

case "${CASE}" in
    # ── XML Audit ──────────────────────────────────────────────────────
    xml_audit)
        shift
        python3 "${PROJECT_ROOT}/src/xml_audit.py" "$@"
        ;;

    # ── Profile Manager ────────────────────────────────────────────────
    profile_manager)
        shift
        python3 "${PROJECT_ROOT}/src/profile_manager.py" "$@"
        ;;

    # ── Deployment ─────────────────────────────────────────────────────
    deploy)
        shift
        python3 "${PROJECT_ROOT}/src/deployment.py" "$@"
        ;;

    # ── Config Generator ───────────────────────────────────────────────
    generate)
        shift
        python3 "${PROJECT_ROOT}/src/config_generator.py" "$@"
        ;;

    # ── Config Validator ───────────────────────────────────────────────
    validate)
        shift
        python3 "${PROJECT_ROOT}/src/config_validator.py" "$@"
        ;;

    # ── Test Suite ─────────────────────────────────────────────────────
    test)
        shift
        cd "${PROJECT_ROOT}"
        python3 -m pytest tests/ "$@"
        ;;

    # ── Syntax check ───────────────────────────────────────────────────
    syntax)
        shift
        python3 -c "
from src.xml_audit import check_syntax
import sys
result = check_syntax('${1:-profiles/LXX521_IMX682_AllInOne_V3.xml}')
print(f'Syntax check: {result.passed}')
print(f'Details: {result.details}')
"
        ;;

    # ── Default: show help
    *)
        echo "Unknown command: ${CASE}"
        echo "Run 'TERMUX_RUN.sh' for usage information."
        exit 1
        ;;
esac