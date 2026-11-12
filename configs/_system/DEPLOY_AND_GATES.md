# MGC 8.9 (BSG) — LXX521 / IMX682 — System Documentation
Reconciled to the TEX + AI active-profile mandate (commit 3b513dd / PR #1).
Generated 2026-11-12. Source of truth: scripts/deploy_profiles.sh, configs/gates.json.

## Active deploy pair (enforced by deploy_profiles.sh)

| Profile | Role | SHA-256 | Keys | Deltas vs TEX |
|---|---|---|---|---|
| LXX521_TEX.xml | V4.1 Texture-First Production (baseline) | f84a96a0c1324f808edf6cf2e0d880dc64f7e7ea7e72faf4745a0e195678a1a0 | 2641 | 0 |
| LXX521_AI.xml | Balanced Computational Variant | 2948747ed52c81a17f3d0df9261157dddd812a64d8edb0295628448e3348f204 | 2641 | 43 |

Deploy contract:
- No implicit destination: `--dest DIR` or `CALIB_LMC_DIR` required (DCIM_LMC_DIR fallback).
- Missing destination exits 2.
- `--dry-run` exits 0, creates nothing.
- `--prune` archives non-mandated XMLs to `<dest>/archive/<ts>/` (never deletes).
- `/sdcard/lmc8.4` is registered as a `role=live` source in configs/sources.json — pruning it requires `--force-source-overlap`.
- No hardcoded `/sdcard/lmc8.4` remains in scripts/ or packages/.

## Optional (non-active) profiles

| Profile | SHA-256 | Status |
|---|---|---|
| LXX521_NIGHT.xml | 75a7621578f6e644291ea04b33e27322a418716de10cbb529cf5b9a730a7eaee | Optional night/handheld session. Transport copy at /sdcard/Download/LXX521_NIGHT.xml. Not active; archived by --prune if present in dest. |
| LXX521_ALLINONE.xml | 7f6a93ad... | Archived candidate (historical). |
| LXX521_NIGHT_CRISP.xml | 00df6df3... | Transport copy in /sdcard/Download/. |

## Quality gates (configs/gates.json, day / night)

| Metric | Day (TEX/AI) | Night (*NIGHT*) |
|---|---|---|
| MTF50 center | >= 0.30 cy/px | >= 0.18 cy/px |
| MTF50 edge | >= 0.22 cy/px | >= 0.12 cy/px |
| Mean luma | 100 - 140 DN | 70 - 120 DN |
| Highlight clipping | < 1.0 % | < 2.0 % |
| Green noise @ ISO 100 | <= 1.5 DN | <= 2.5 DN |
| Green noise @ ISO 3200 | <= 12 DN | <= 15 DN |
| Gray-patch deltaE00 | <= 5.0 | <= 5.0 |

Night gates auto-select when profile name contains "night".

## Measurement status (56 DCIM/Camera JPEGs, 2026-11-12)

Overall: FAIL. 38 groups, 62 failures.
- MTF50: data available for 1/38 groups (natural scenes lack ISO 12233 slanted edges).
- Noise sigma: 31 group failures (scene texture inflates MAD estimate).
- Mean luma: 19 group failures (auto-exposure varies).
- Highlight clipping: 11 group failures (blue-channel clip dominant).

MTF50, flat-field noise, deltaE00 and 4K video gates remain DATA PENDING pending
slanted-edge chart, flat field, gray card / ColorChecker, and 4K captures.
