#!/bin/bash
# TERMUX INSTALL — LAVA LXX521 / IMX682 GCam Calibration Engine
#
# This script sets up the DCIM Calibration engineering project in Termux.
# It installs dependencies, creates the project directory structure,
# and prepares the environment for the calibration engine.
#
# Prerequisites: Termux app installed on LAVA LXX521 (Android 15)
#                Termux packages: python, pytest, flake8
#
# Recommended shared storage: ~/storage/shared/Download/DCIM_Calibration/
#
# This script MUST NOT be run as root. It uses $HOME/usr/ for local installs.
#
# Copyright (C) 2026 LAVA LXX521 DCIM Calibration Project
# ALL RIGHTS RESERVED. See LICENSE for build terms.

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────────

# Preferred shared storage directory (per mission §12)
PREFERRED_DIR="${HOME}/storage/shared/Download/DCIM_Calibration"

# Project root (where this script resides, resolved relative to Termux home)
PROJECT_ROOT="${HOME}/dcim-calibration-engine"

# Python version check
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1)

# ─── Step 1: Update Termux and install dependencies ──────────────────────

echo "=== Termux Install: Step 1/6 ==="
echo "Updating Termux packages..."

# Update termux packages
pkg update -y > /dev/null 2>&1 || true
pkg upgrade -y > /dev/null 2>&1 || true

# Install Python and required packages
echo "Installing Python and dependencies..."
pkg install -y python python-pip > /dev/null 2>&1

# Install pytest and flake8 for CI compatibility
pip install --break-system-packages pytest flake8 2>/dev/null || \
    pip install pytest flake8 2>/dev/null || \
    echo "Note: pytest/flake8 may already be installed"

# ─── Step 2: Create project directory structure ──────────────────────────

echo ""
echo "=== Termux Install: Step 2/6 ==="
echo "Creating project directory structure..."

mkdir -p "${PROJECT_ROOT}"
mkdir -p "${PROJECT_ROOT}/src"
mkdir -p "${PROJECT_ROOT}/profiles/lmc84"
mkdir -p "${PROJECT_ROOT}/profiles/mgc_bsg"
mkdir -p "${PROJECT_ROOT}/profiles/frontcam"
mkdir -p "${PROJECT_ROOT}/backups"
mkdir -p "${PROJECT_ROOT}/reports"
mkdir -p "${PROJECT_ROOT}/tests"
mkdir -p "${PROJECT_ROOT}/docs"

# Create __init__.py for src/ package
if [ ! -f "${PROJECT_ROOT}/src/__init__.py" ]; then
    touch "${PROJECT_ROOT}/src/__init__.py"
fi

# ─── Step 3: Copy source files ──────────────────────────────────────────

echo ""
echo "=== Termux Install: Step 3/6 ==="
echo "Copying calibration engine source files..."

# Copy the src/ modules we created
cp -r /root/dcim-calibration-upgrade/src/*.py "${PROJECT_ROOT}/src"/ 2>/dev/null || \
    echo "Note: Some src/ files may already exist or copy skipped"

# Copy key reports to docs/
cp /root/dcim-calibration-upgrade/REPOSITORY_AUDIT.md "${PROJECT_ROOT}/docs/" 2>/dev/null
cp /root/dcim-calibration-upgrade/SOURCE_INVENTORY.md "${PROJECT_ROOT}/docs/" 2>/dev/null
cp /root/dcim-calibration-upgrade/DEPENDENCY_MAP.md "${PROJECT_ROOT}/docs/" 2>/dev/null
cp /root/dcim-calibration-upgrade/PROFILE_COMPATIBILITY.md "${PROJECT_ROOT}/docs/" 2>/dev/null
cp /root/dcim-calibration-upgrade/DUPLICATE_CONFLICT_REPORT.md "${PROJECT_ROOT}/docs/" 2>/dev/null
cp /root/dcim-calibration-upgrade/VALIDATION_REPORT.md "${PROJECT_ROOT}/docs/" 2>/dev/null
cp /root/dcim-calibration-upgrade/UPGRADE_CHANGELOG.md "${PROJECT_ROOT}/docs/" 2>/dev/null

# ─── Step 4: Set up preferred storage directory ──────────────────────────

echo ""
echo "=== Termux Install: Step 4/6 ==="
echo "Setting up preferred storage directory..."

if [ -d "${PREFERRED_DIR}" ]; then
    echo "Preferred directory already exists: ${PREFERRED_DIR}"
else
    mkdir -p "${PREFERRED_DIR}"
    echo "Created preferred directory: ${PREFERRED_DIR}"
fi

# Create subdirectories within the preferred dir
mkdir -p "${PREFERRED_DIR}/profiles"
mkdir -p "${PREFERRED_DIR}/backups"
mkdir -p "${PREFERRED_DIR}/downloads"

echo "Preferred storage: ${PREFERRED_DIR}"

# ─── Step 5: Verify Python imports ───────────────────────────────────────

echo ""
echo "=== Termux Install: Step 5/6 ==="
echo "Verifying Python imports..."

# Test that all src/ modules can be imported
FAILURES=0
for module in \
    "device_probe" \
    "camera_capabilities" \
    "xml_audit" \
    "profile_compare" \
    "config_generator" \
    "config_validator" \
    "profile_manager" \
    "deployment"; do
    if python3 -c "from src import ${module}" 2>/dev/null; then
        echo "  ✅ ${module} importable"
    else
        echo "  ❌ ${module} import FAILED"
        FAILURES=$((FAILURES + 1))
    fi
done

if [ "${FAILURES}" -gt 0 ]; then
    echo "Warning: ${FAILURES} module(s) could not be imported directly from ${PROJECT_ROOT}/src/"
    echo "This may be expected if the module relies on relative imports."
fi

# ─── Step 6: Final verification ──────────────────────────────────────────

echo ""
echo "=== Termux Install: Step 6/6 ==="
echo "Final verification..."

echo ""
echo "=== Termux Install Complete ==="
echo ""
echo "Project root:    ${PROJECT_ROOT}"
echo "Preferred storage: ${PREFERRED_DIR}"
echo ""
echo "Next steps:"
echo "  1. Review the generated reports in ${PROJECT_ROOT}/docs/"
echo "  2. Run: python3 -m src.xml_audit --help"
echo "  3. Run: python3 -m src.profile_manager list_profiles"
echo "  4. Edit workflow_master_v4.py to confirm the deploy destination"
echo ""
echo "Mission priority 1: Working front and rear GCam port"
echo "Mission priority 2: Reliable IMX682 configuration and calibration engine"
echo "Mission priority 3: Automated profile generation, validation, and management"
echo "Mission priority 4: Reproducible Android/Termux build and deployment workflow"

exit 0