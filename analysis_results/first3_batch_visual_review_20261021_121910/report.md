# First 3 Batch — Exploratory Image Review

- Generated: 2026-10-21T12:19:24.207871+05:30
- Source: `/storage/emulated/0/DCIM/Camera`
- Images successfully analyzed: 15 / 15 expected
- Missing files: 0
- Analysis errors: 0

## Important interpretation limits
- Profile labels are taken from the test plan/user declaration; the JPEGs do not independently prove which XML was applied.
- Pixel metrics describe encoded JPEG output only. They do not prove sensor noise, true dynamic range, color accuracy, or MTF50.
- This is an exploratory comparison. Exposure, HDR processing, focus, white balance, framing, and changing light may confound results.
- Batch 4 is intentionally excluded because it was invalid (6 new files detected instead of 5). No files are deleted or changed.

## Per-profile quick summary

| Batch | Profile label | Images analyzed | Mean luma avg | Near-black % avg | Near-white % avg | Sharpness proxy avg |
|---|---|---:|---:|---:|---:|---:|
| 01 | `V9_ConservativeBalanced` | 5/5 | 110.036 | 8.964 | 6.099 | 843.208 |
| 02 | `V8_ProBalanced` | 5/5 | 100.748 | 13.360 | 7.479 | 718.143 |
| 03 | `V8_FullAllRounder_Q100` | 5/5 | 98.408 | 16.084 | 4.326 | 728.731 |

## Output files
- `image_metrics.csv`: per-image metrics and SHA-256.
- `contact_sheet.jpg`: visual overview only; not a full-resolution sharpness assessment.
- `file_manifest.json`: expected file list and per-file analysis status/hash.
