#!/usr/bin/env bash
#
# run_deploy_and_analyze.sh — Deploy LMC 8.4 calibration config and analyze DCIM captures
#
# Steps:
#   1. Run generate_best_tuned_config.py to write the updated configuration
+      directly to /sdcard/LMC8.4/LXX521_IMX682.xml
#   2. Run analyze_photos.py to extract image resolution and color channel
+      metrics from the latest captures in /sdcard/DCIM/Camera/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

LMC84_DIR="/sdcard/LMC8.4"
DCIM_DIR="/sdcard/DCIM/Camera"
OUTPUT_XML="LXX521_IMX682.xml"
BASE_CONFIG="configs/xml/LXX521_IMX682_LMC84_AllInOne_Master_PATCHED.xml"

echo "============================================================"
echo "LMC 8.4 Calibration Deploy & Analyze"
echo "============================================================"
echo ""

# ------------------------------------------------------------------
# Step 1: Generate and deploy the updated calibration XML
# ------------------------------------------------------------------
echo "[1/2] Generating best-tuned calibration XML..."
python "${SCRIPT_DIR}/generate_best_tuned_config.py" \
    --base "${BASE_CONFIG}" \
    --output "${OUTPUT_XML}"

# Verify deployment
if [[ -f "${LMC84_DIR}/${OUTPUT_XML}" ]]; then
    echo "  ✓ Deployed to ${LMC84_DIR}/${OUTPUT_XML}"
else
    echo "  ✗ ERROR: Failed to deploy ${OUTPUT_XML} to ${LMC84_DIR}/"
    exit 1
fi

echo ""

# ------------------------------------------------------------------
# Step 2: Analyze DCIM captures
# ------------------------------------------------------------------
echo "[2/2] Analyzing DCIM captures for image metrics..."
python "${SCRIPT_DIR}/analyze_photos.py" \
    --camera-dir "${DCIM_DIR}" \
    --output "${REPO_DIR}/analysis/data/dcim_camera_analysis/calibration_metrics.json"

echo ""
echo "============================================================"
echo "Deploy & Analyze complete."
echo "  Config:    ${LMC84_DIR}/${OUTPUT_XML}"
echo "  Metrics:   ${REPO_DIR}/analysis/data/dcim_camera_analysis/calibration_metrics.json"
echo "============================================================"
