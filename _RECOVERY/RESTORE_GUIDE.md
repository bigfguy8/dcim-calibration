# Restore Guide

This repository contains a curated copy of DCIM Calibration source,
configuration, documentation and selected text-based results.

## Integrity

Use `_RECOVERY/SHA256SUMS.tsv` to verify file hashes with a Python script.

## Restore safely

1. Clone this private repository on the replacement device.
2. Read `_RECOVERY/BACKUP_SCOPE.md` and review the original project layout.
3. Compare XML profiles before copying them back.
4. Preserve existing working profiles and backups; do not blindly overwrite.
5. Reinstall Python/Termux dependencies separately as needed.

## Important exclusions

Photos, videos, archives, binary files, symlinks, generated build/cache data,
sensitive-looking filenames, and files over 25 MiB are not stored here.
This repo therefore cannot restore the complete multimedia dataset.

No photos were captured and no camera test was run by this workflow.
