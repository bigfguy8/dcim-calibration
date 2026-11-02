# Test Suite Documentation

## Project: dcim-calibration-upgrade

## Overview

This directory contains 9 unittest test suites covering the full calibration engine
for the LAVA LXX521 / Sony IMX682 GCam engineering project. All tests use Python
standard library only (no external dependencies required). Tests are synthetic
only — no physical camera access, no device capture, no real deployment.

## Test Structure

### Suite 1: Device Probe (`test_device_probe.py`)
- Synthetic characteristics parsing
- NULL characteristic handling (front camera sensitivity_range is None)
- Missing/malformed characteristic handling
- Explicit distinction between synthetic and measured data
- No physical camera access

### Suite 2: Camera Capabilities (`test_camera_capabilities.py`)
- Schema-family identification (LMC vs BSG vs UNKNOWN)
- LMC and BSG family separation (strict — never interchangeable)
- Capability validation
- Unknown schema handling
- Unsupported-key reporting

### Suite 3: XML Audit (`test_xml_audit.py`)
- Valid XML syntax detection
- Malformed XML handling
- Root/schema checks
- Duplicate-key detection
- Compatibility and device-validation status handling

### Suite 4: Profile Comparison (`test_profile_compare.py`)
- Identical profile detection
- Changed values detection
- Added and removed keys detection
- Invalid input handling
- Deterministic output verification

### Suite 5: Configuration Generator (`test_config_generator.py`)
- Baseline-derived candidate generation
- Change provenance tracking
- Unchanged baseline preservation
- Rollback-copy creation
- Invalid baseline handling

### Suite 6: Configuration Validator (`test_config_validator.py`)
- Valid and invalid configuration classification
- Unsupported key detection
- Schema-family mismatch reporting
- Correct validation-level classification (A/B/C/D)

### Suite 7: Profile Manager (`test_profile_manager.py`)
- Profile discovery and family classification
- Metadata and provenance tracking
- Backup and rollback operations
- Safe handling of duplicate filenames

### Suite 8: Deployment (`test_deployment.py`)
- Dry-run deployment (no real writes)
- Destination verification
- Backup creation
- SHA-256 verification
- Failed deployment handling
- Rollback request handling
- No automatic real deployment

### Suite 9: Image Quality Analyzer (`test_image_quality_analyzer.py`)
- Synthetic image fixtures only
- File hash calculation
- Valid and invalid image handling
- Missing optional library handling (cv2, numpy, matplotlib)
- No fabricated image-quality measurements
- No camera capture

## Test Execution

All tests use Python `unittest` discovery. Run from the project root:

```bash
cd /root/dcim-calibration-upgrade
python -m unittest discover -s tests -v
```

Or run individual test suites:

```bash
python -m unittest tests.test_device_probe -v
python -m unittest tests.test_camera_capabilities -v
python -m unittest tests.test_xml_audit -v
python -m unittest tests.test_profile_compare -v
python -m unittest tests.test_config_generator -v
python -m unittest tests.test_config_validator -v
python -m unittest tests.test_profile_manager -v
python -m unittest tests.test_deployment -v
python -m unittest tests.test_image_quality_analyzer -v
```

## Test Rules (Strict)

1. Use temporary directories for file operations
2. Never modify original calibration profiles
3. Never use real deployment destinations
4. Never capture photographs or launch camera sessions
5. Never invent camera parameters, test results, or file paths
6. Avoid tests that pass merely because an exception was swallowed
7. Ensure every test can run independently
8. Use deterministic test data
9. Preserve Termux compatibility
10. Do not report tests as passing until the test runner actually executes them and returns exit code 0
11. Do not test physical Camera2 hardware
12. Do not require internet, GitHub, ADB, a PC, or root

## Test Results

Upon first execution, verify all tests pass with exit code 0. If any tests fail,
inspect the exact traceback and exit code before modifying any code. Do not
silently weaken assertions or retry failures by suppressing output.

## References

- `STAGE3_FINAL_ACCEPTANCE_AUDIT.md` — Final acceptance audit document
- `STAGE3_IMPLEMENTATION_REPORT.md` — Implementation history
- `STAGE3_TEST_REPORT.md` — Test report (to be updated after execution)
- `UPGRADE_CHANGELOG.md` — Changelog (to be corrected after R6)
- `VALIDATION_STATUS.md` — Four-level validation status