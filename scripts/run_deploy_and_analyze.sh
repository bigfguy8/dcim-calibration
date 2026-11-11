#!/usr/bin/env bash
#
# run_deploy_and_analyze.sh — Deploy the mandated MGC 8.9 profiles and analyze
# device captures.
#
# Steps:
#   1. Run deploy_profiles.sh to deploy exactly LXX521_TEX.xml and LXX521_NIGHT.xml
#      to the directory in CALIB_LMC_DIR (any other *.xml is archived).
#   2. Run analyze_photos.py to extract image resolution and color channel
#      metrics from the latest captures in /sdcard/DCIM/Camera/.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

LMC_DIR="${CALIB_LMC_DIR:-${DCIM_LMC_DIR:-}}"
DCIM_DIR="${DCIM_PATH:-/sdcard/DCIM/Camera}"

if [[ -z "${LMC_DIR}" ]]; then
    echo "[-] set CALIB_LMC_DIR to the MGC profile directory" >&2
    exit 2
fi

echo "============================================================"
echo "MGC 8.9 Profile Deploy & Analyze"
echo "============================================================"
echo ""

# ------------------------------------------------------------------
# Step 1: Deploy the two mandated profiles
# ------------------------------------------------------------------
echo "[1/2] Deploying LXX521_TEX.xml and LXX521_NIGHT.xml..."
bash "${SCRIPT_DIR}/deploy_profiles.sh" --prune

for profile in LXX521_TEX.xml LXX521_NIGHT.xml; do
    if [[ ! -f "${LMC_DIR}/${profile}" ]]; then
        echo "  ✗ ERROR: ${profile} missing from ${LMC_DIR}/" >&2
        exit 1
    fi
    echo "  ✓ ${profile}"
done

# ------------------------------------------------------------------
# Step 2: Analyze DCIM captures
# ------------------------------------------------------------------
echo ""
echo "[2/2] Analyzing DCIM captures for image metrics..."
python "${SCRIPT_DIR}/analyze_photos.py" \
    --camera-dir "${DCIM_DIR}" \
    --output "${REPO_DIR}/analysis/data/dcim_camera_analysis/calibration_metrics.json"

echo ""
echo "============================================================"
echo "Deploy & Analyze complete."
echo "  Profiles:  ${LMC_DIR}/LXX521_TEX.xml, ${LMC_DIR}/LXX521_NIGHT.xml"
echo "  Metrics:   ${REPO_DIR}/analysis/data/dcim_camera_analysis/calibration_metrics.json"
echo "============================================================"
