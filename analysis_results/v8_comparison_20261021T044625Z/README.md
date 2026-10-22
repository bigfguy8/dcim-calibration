# V8 Profile Comparison Audit

- Output: `/data/data/com.termux/files/home/dcim_calibration/analysis_results/v8_comparison_20261021T044625Z`
- Mode: read-only; original files are not modified.
- Decision: **INCONCLUSIVE** until controlled captures and runtime metadata exist.

## Files
- `input_inventory.csv`: discovered target inputs, paths, sizes, timestamps and hashes.
- `xml_key_differences.csv`: parsed XML differences.
- `relevant_settings.csv`: name-based candidate settings; meanings are not presumed.
- `image_metrics.csv`: descriptive JPEG metrics.
- `capture_manifest_template.csv`: blank capture record template.
- `runtime_verification_matrix.csv`: runtime checks currently unverified.
- `matched_pair_manifest.csv`: blank; no pair is assumed valid.
- `statistical_summary.csv`: blank until valid matched repeated captures exist.
- `audit_results.json`: machine-readable summary.
- `execution_log.txt`: diagnostics.

## Metric note
Luma is a weighted proxy computed directly from normalized sRGB-encoded JPEG values,
not linear-light luminance. It must not be interpreted as dynamic range, color accuracy,
sensor noise, or MTF50.

## Re-run
`python /data/data/com.termux/files/home/dcim_calibration/run_v8_comparison.py`
