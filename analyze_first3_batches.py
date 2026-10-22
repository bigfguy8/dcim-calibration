#!/usr/bin/env python3
"""Read-only exploratory review of the first three LXX521/IMX682 camera batches.

Reads exact, previously captured JPEGs from /storage/emulated/0/DCIM/Camera.
Does not modify photos or XML profiles. Produces CSV metrics, a contact sheet,
a report, and a small ZIP containing analysis outputs (not originals).
Metrics are encoded-JPEG proxies, not laboratory camera measurements.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageOps, ImageStat
except ImportError as exc:
    print(f"Missing dependency: {exc}. Install with: pip install pillow numpy", file=sys.stderr)
    raise SystemExit(2)

CAMERA_DIR = Path('/storage/emulated/0/DCIM/Camera')
PROJECT_DIR = Path.home() / 'dcim_calibration'
OUT_ROOT = PROJECT_DIR / 'analysis_results'
BATCHES: list[dict[str, Any]] = [
    {
        'batch': '01', 'scene': 'bright_window_dark_interior', 'profile': 'V9_ConservativeBalanced',
        'files': [
            '20261021_120304_lmc_8.4.jpg', '20261021_120320_lmc_8.4.jpg',
            '20261021_120326_lmc_8.4.jpg', '20261021_120330_lmc_8.4.jpg',
            '20261021_120333_lmc_8.4.jpg',
        ],
    },
    {
        'batch': '02', 'scene': 'bright_window_dark_interior', 'profile': 'V8_ProBalanced',
        'files': [
            '020261021_120834_LXX521_IMX682_V8_ProBalanced.jpg',
            '020261021_120843_LXX521_IMX682_V8_ProBalanced.jpg',
            '020261021_120853_LXX521_IMX682_V8_ProBalanced.jpg',
            '020261021_120856_LXX521_IMX682_V8_ProBalanced.jpg',
            '020261021_120901_LXX521_IMX682_V8_ProBalanced.jpg',
        ],
    },
    {
        'batch': '03', 'scene': 'bright_window_dark_interior', 'profile': 'V8_FullAllRounder_Q100',
        'files': [
            '20261021_121019_lmc_8.4.jpg', '20261021_121028_lmc_8.4.jpg',
            '20261021_121034_lmc_8.4.jpg', '20261021_121037_lmc_8.4.jpg',
            '20261021_121040_lmc_8.4.jpg',
        ],
    },
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_exif(image: Image.Image) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        exif = image.getexif()
        # Common EXIF tag IDs: DateTimeOriginal 36867, ExposureTime 33434, FNumber 33437,
        # ISO 34855, FocalLength 37386, WhiteBalance 41987, Flash 37385.
        for tag, label in [(36867, 'exif_datetime_original'), (33434, 'exposure_time'),
                           (33437, 'f_number'), (34855, 'iso'), (37386, 'focal_length'),
                           (41987, 'white_balance'), (37385, 'flash')]:
            value = exif.get(tag)
            if value is not None:
                out[label] = str(value)
    except Exception:
        pass
    return out


def compute_metrics(path: Path, batch: dict[str, Any]) -> dict[str, Any]:
    with Image.open(path) as im0:
        im0.verify()
    with Image.open(path) as im0:
        im = ImageOps.exif_transpose(im0).convert('RGB')
        width, height = im.size
        # Downsample for bounded memory/use on Android. Metrics are approximate encoded-output proxies.
        small = im.copy()
        small.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        a = np.asarray(small, dtype=np.float32)
        r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
        luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
        # Approximate RGB saturation in [0,1].
        hi = np.max(a, axis=2)
        lo = np.min(a, axis=2)
        sat = np.where(hi > 0, (hi - lo) / np.maximum(hi, 1.0), 0.0)
        # Laplacian variance on a grayscale downsample; a rough sharpness/detail proxy only.
        gray_img = small.convert('L')
        gray_img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        gray = np.asarray(gray_img, dtype=np.float32)
        if gray.shape[0] >= 3 and gray.shape[1] >= 3:
            lap = (-4.0 * gray[1:-1, 1:-1] + gray[:-2, 1:-1] + gray[2:, 1:-1]
                   + gray[1:-1, :-2] + gray[1:-1, 2:])
            lap_var = float(np.var(lap))
        else:
            lap_var = float('nan')
        exif = safe_exif(im0)
        return {
            'batch': batch['batch'], 'scene': batch['scene'], 'profile_label_user_declared': batch['profile'],
            'filename': path.name, 'bytes': path.stat().st_size, 'sha256': sha256(path),
            'width': width, 'height': height, 'pixel_count': width * height,
            'mean_luma_0_255': round(float(np.mean(luma)), 3),
            'luma_p10': round(float(np.percentile(luma, 10)), 3),
            'luma_p50': round(float(np.percentile(luma, 50)), 3),
            'luma_p90': round(float(np.percentile(luma, 90)), 3),
            'luma_p99': round(float(np.percentile(luma, 99)), 3),
            'near_black_pct_luma_lt16': round(float(np.mean(luma < 16) * 100), 4),
            'near_white_pct_luma_gt245': round(float(np.mean(luma > 245) * 100), 4),
            'very_bright_pct_luma_gt250': round(float(np.mean(luma > 250) * 100), 4),
            'mean_R': round(float(np.mean(r)), 3), 'mean_G': round(float(np.mean(g)), 3),
            'mean_B': round(float(np.mean(b)), 3), 'mean_saturation_proxy_0_1': round(float(np.mean(sat)), 5),
            'laplacian_variance_proxy': round(lap_var, 3) if math.isfinite(lap_var) else '',
            **exif,
        }


def make_contact_sheet(paths_by_batch: list[tuple[dict[str, Any], list[Path]]], output: Path) -> None:
    cell_w, cell_h = 300, 300
    pad, label_h, head_h = 12, 28, 42
    cols = 5
    rows = len(paths_by_batch)
    sheet = Image.new('RGB', (pad + cols * (cell_w + pad), pad + rows * (cell_h + label_h + head_h + pad)), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    y = pad
    for batch, paths in paths_by_batch:
        draw.text((pad, y), f"Batch {batch['batch']} | {batch['profile']} | {len(paths)} available", fill=(10, 10, 10))
        y += head_h
        for idx in range(cols):
            x = pad + idx * (cell_w + pad)
            if idx < len(paths):
                p = paths[idx]
                try:
                    with Image.open(p) as im0:
                        im = ImageOps.exif_transpose(im0).convert('RGB')
                        im.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
                        card = Image.new('RGB', (cell_w, cell_h), (230, 230, 230))
                        card.paste(im, ((cell_w-im.width)//2, (cell_h-im.height)//2))
                        sheet.paste(card, (x, y))
                    draw.text((x, y + cell_h + 4), f"{idx+1}. {p.name[:32]}", fill=(10, 10, 10))
                except Exception as exc:
                    draw.text((x, y+10), f"ERROR: {type(exc).__name__}", fill=(180, 0, 0))
            else:
                draw.rectangle((x, y, x+cell_w, y+cell_h), fill=(220, 220, 220))
                draw.text((x+10, y+10), 'MISSING', fill=(100, 0, 0))
        y += cell_h + label_h + pad
    sheet.save(output, format='JPEG', quality=88, optimize=True)


def main() -> int:
    if not CAMERA_DIR.is_dir():
        print(f"Camera folder not found: {CAMERA_DIR}", file=sys.stderr)
        return 2
    timestamp = datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')
    out_dir = OUT_ROOT / f'first3_batch_visual_review_{timestamp}'
    out_dir.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, Any]] = []
    paths_by_batch: list[tuple[dict[str, Any], list[Path]]] = []
    missing: list[str] = []
    errors: list[str] = []
    manifest: list[dict[str, Any]] = []

    for batch in BATCHES:
        paths: list[Path] = []
        for filename in batch['files']:
            p = CAMERA_DIR / filename
            if not p.is_file():
                missing.append(filename)
                manifest.append({'batch': batch['batch'], 'profile': batch['profile'], 'filename': filename,
                                 'status': 'MISSING', 'path': str(p)})
                continue
            paths.append(p)
            try:
                row = compute_metrics(p, batch)
                rows.append(row)
                manifest.append({'batch': batch['batch'], 'profile': batch['profile'], 'filename': filename,
                                 'status': 'ANALYZED', 'path': str(p), 'sha256': row['sha256']})
            except Exception as exc:
                errors.append(f'{filename}: {type(exc).__name__}: {exc}')
                manifest.append({'batch': batch['batch'], 'profile': batch['profile'], 'filename': filename,
                                 'status': 'ERROR', 'path': str(p), 'error': f'{type(exc).__name__}: {exc}'})
        paths_by_batch.append((batch, paths))

    # Write CSV with union of present keys.
    csv_path = out_dir / 'image_metrics.csv'
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    (out_dir / 'file_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    sheet_path = out_dir / 'contact_sheet.jpg'
    make_contact_sheet(paths_by_batch, sheet_path)

    report_lines = [
        '# First 3 Batch — Exploratory Image Review', '',
        f'- Generated: {datetime.now().astimezone().isoformat()}',
        f'- Source: `{CAMERA_DIR}`',
        f'- Images successfully analyzed: {len(rows)} / 15 expected',
        f'- Missing files: {len(missing)}', f'- Analysis errors: {len(errors)}', '',
        '## Important interpretation limits',
        '- Profile labels are taken from the test plan/user declaration; the JPEGs do not independently prove which XML was applied.',
        '- Pixel metrics describe encoded JPEG output only. They do not prove sensor noise, true dynamic range, color accuracy, or MTF50.',
        '- This is an exploratory comparison. Exposure, HDR processing, focus, white balance, framing, and changing light may confound results.',
        '- Batch 4 is intentionally excluded because it was invalid (6 new files detected instead of 5). No files are deleted or changed.', '',
        '## Per-profile quick summary', '',
        '| Batch | Profile label | Images analyzed | Mean luma avg | Near-black % avg | Near-white % avg | Sharpness proxy avg |',
        '|---|---|---:|---:|---:|---:|---:|',
    ]
    for batch in BATCHES:
        br = [r for r in rows if r['batch'] == batch['batch']]
        def avg(field: str) -> str:
            nums = [float(r[field]) for r in br if r.get(field) not in ('', None)]
            return f'{sum(nums)/len(nums):.3f}' if nums else 'n/a'
        report_lines.append(f"| {batch['batch']} | `{batch['profile']}` | {len(br)}/5 | {avg('mean_luma_0_255')} | {avg('near_black_pct_luma_lt16')} | {avg('near_white_pct_luma_gt245')} | {avg('laplacian_variance_proxy')} |")
    if missing:
        report_lines += ['', '## Missing files', *[f'- `{x}`' for x in missing]]
    if errors:
        report_lines += ['', '## Analysis errors', *[f'- {x}' for x in errors]]
    report_lines += ['', '## Output files', '- `image_metrics.csv`: per-image metrics and SHA-256.', '- `contact_sheet.jpg`: visual overview only; not a full-resolution sharpness assessment.', '- `file_manifest.json`: expected file list and per-file analysis status/hash.']
    (out_dir / 'report.md').write_text('\n'.join(report_lines) + '\n', encoding='utf-8')

    zip_path = out_dir.with_suffix('.zip')
    import zipfile
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in [csv_path, out_dir / 'file_manifest.json', sheet_path, out_dir / 'report.md']:
            zf.write(p, arcname=p.name)

    print('\n=== FIRST-THREE-BATCH REVIEW COMPLETE ===')
    print(f'Images analyzed: {len(rows)}/15')
    print(f'Missing: {len(missing)} | Errors: {len(errors)}')
    print(f'Report: {out_dir / "report.md"}')
    print(f'Metrics CSV: {csv_path}')
    print(f'Contact sheet: {sheet_path}')
    print(f'Analysis ZIP: {zip_path}')
    if missing:
        print('\nMISSING FILES:')
        for name in missing:
            print(f'  - {name}')
    if errors:
        print('\nERRORS:')
        for e in errors:
            print(f'  - {e}')
    print('\nRead-only: source photos and XML profiles were not modified. Batch 4 was excluded.')
    return 0 if len(rows) == 15 and not missing and not errors else 1

if __name__ == '__main__':
    raise SystemExit(main())
