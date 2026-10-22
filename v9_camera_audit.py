#!/usr/bin/env python3
"""Reproducible Termux audit of recent images in Android DCIM/Camera.

This script reads image files only. It does not alter images or camera XML.
Pixel statistics are descriptive encoded-JPEG proxies, not measurements of
sensor dynamic range, true sensor noise, color accuracy, or MTF50.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import numpy as np
    from PIL import Image, ExifTags, ImageFile
except ImportError as exc:
    print("Missing dependency:", exc, file=sys.stderr)
    print("In Termux, install with: pkg install python python-numpy python-pillow", file=sys.stderr)
    sys.exit(2)

# Don't silently accept truncated JPEGs: decoding failures should be reported.
ImageFile.LOAD_TRUNCATED_IMAGES = False

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".heic", ".heif"}
EXIF_LABELS = getattr(ExifTags, "TAGS", {})


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", "replace").strip("\x00 ")
        except Exception:
            return repr(value)
    if isinstance(value, (list, tuple)):
        return ";".join(safe_text(v) for v in value)
    return str(value)


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            den = float(value.denominator)
            return float(value.numerator) / den if den else None
        if isinstance(value, (tuple, list)) and len(value) == 2:
            den = float(value[1])
            return float(value[0]) / den if den else None
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError, OverflowError):
        return None


def collect_exif(image: Image.Image) -> Dict[str, Any]:
    """Collect top-level and EXIF IFD entries supported by Pillow."""
    found: Dict[str, Any] = {}
    try:
        exif = image.getexif()
    except Exception:
        return found
    if not exif:
        return found

    for tag_id, value in exif.items():
        label = EXIF_LABELS.get(tag_id, f"Tag_{tag_id}")
        if tag_id in (34665, 34853, 40965):
            # IFD pointers are read below when Pillow supports get_ifd.
            continue
        found[str(label)] = value

    if hasattr(exif, "get_ifd"):
        for ifd_id in (34665, 40965):
            try:
                entries = exif.get_ifd(ifd_id)
            except Exception:
                continue
            if isinstance(entries, dict):
                for tag_id, value in entries.items():
                    label = EXIF_LABELS.get(tag_id, f"Tag_{tag_id}")
                    found[str(label)] = value
    return found


def value_for(exif: Dict[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        if name in exif and exif[name] not in (None, ""):
            return exif[name]
    return ""


def to_iso_value(value: Any) -> str:
    if value in (None, ""):
        return ""
    return safe_text(value)


def exposure_seconds(value: Any) -> Optional[float]:
    return as_float(value)


def list_images(folder: Path, recursive: bool, since_dt: Optional[datetime], limit: int) -> Tuple[List[Path], List[str]]:
    warnings: List[str] = []
    if not folder.exists():
        return [], [f"Input directory does not exist: {folder}"]
    if not folder.is_dir():
        return [], [f"Input path is not a directory: {folder}"]
    try:
        iterator = folder.rglob("*") if recursive else folder.iterdir()
        paths: List[Path] = []
        for path in iterator:
            try:
                if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                    if since_dt is not None and mtime < since_dt:
                        continue
                    paths.append(path)
            except (PermissionError, OSError) as exc:
                warnings.append(f"Cannot inspect {path}: {exc}")
        paths.sort(key=lambda p: (p.stat().st_mtime if p.exists() else 0), reverse=True)
        if limit > 0:
            paths = paths[:limit]
        return paths, warnings
    except (PermissionError, OSError) as exc:
        return [], warnings + [f"Unable to list input directory: {exc}"]


def pct(mask: np.ndarray) -> float:
    return float(np.count_nonzero(mask) * 100.0 / mask.size) if mask.size else 0.0


def analyze_image(path: Path, profile_label: str, profile_source: str) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "file_name": path.name,
        "file_path": str(path),
        "profile_label": profile_label,
        "profile_attribution": profile_source,
        "file_size_bytes": "",
        "file_modified_local": "",
        "sha256": "",
        "duplicate_group": "",
        "decode_status": "FAIL",
        "error": "",
        "width_px": "",
        "height_px": "",
        "format": "",
        "mode": "",
        "exif_datetime_original": "",
        "exif_make": "",
        "exif_model": "",
        "exif_software": "",
        "exposure_time_raw": "",
        "exposure_time_s": "",
        "iso_raw": "",
        "f_number": "",
        "focal_length_mm": "",
        "exposure_compensation_ev": "",
        "metering_mode": "",
        "flash": "",
        "white_balance": "",
        "exposure_program": "",
        "light_source": "",
        "jpeg_quality_metadata": "",
        "mean_encoded_luma_proxy": "",
        "median_encoded_luma_proxy": "",
        "std_encoded_luma_proxy": "",
        "luma_p01": "",
        "luma_p05": "",
        "luma_p95": "",
        "luma_p99": "",
        "near_black_luma_lt_0_02_pct": "",
        "near_white_luma_gt_0_98_pct": "",
        "pixels_any_channel_exact_0_pct": "",
        "pixels_any_channel_exact_255_pct": "",
        "mean_saturation_proxy": "",
        "median_saturation_proxy": "",
        "metrics_note": "Encoded RGB/JPEG proxies; not sensor-level or calibrated measurements.",
    }
    try:
        st = path.stat()
        base["file_size_bytes"] = st.st_size
        base["file_modified_local"] = datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
        base["sha256"] = sha256_file(path)

        with Image.open(path) as im:
            im.load()
            base["width_px"], base["height_px"] = im.size
            base["format"] = im.format or ""
            base["mode"] = im.mode or ""
            exif = collect_exif(im)

            base["exif_datetime_original"] = safe_text(value_for(exif, ("DateTimeOriginal", "DateTimeDigitized", "DateTime")))
            base["exif_make"] = safe_text(value_for(exif, ("Make",)))
            base["exif_model"] = safe_text(value_for(exif, ("Model",)))
            base["exif_software"] = safe_text(value_for(exif, ("Software",)))

            exp = value_for(exif, ("ExposureTime",))
            exp_sec = exposure_seconds(exp)
            base["exposure_time_raw"] = safe_text(exp)
            base["exposure_time_s"] = round(exp_sec, 8) if exp_sec is not None else ""
            base["iso_raw"] = to_iso_value(value_for(exif, ("PhotographicSensitivity", "ISOSpeedRatings", "ISO", "StandardOutputSensitivity")))
            fn = as_float(value_for(exif, ("FNumber",)))
            focal = as_float(value_for(exif, ("FocalLength",)))
            ev = as_float(value_for(exif, ("ExposureCompensation",)))
            base["f_number"] = round(fn, 4) if fn is not None else ""
            base["focal_length_mm"] = round(focal, 4) if focal is not None else ""
            base["exposure_compensation_ev"] = round(ev, 4) if ev is not None else ""
            base["metering_mode"] = safe_text(value_for(exif, ("MeteringMode",)))
            base["flash"] = safe_text(value_for(exif, ("Flash",)))
            base["white_balance"] = safe_text(value_for(exif, ("WhiteBalance",)))
            base["exposure_program"] = safe_text(value_for(exif, ("ExposureProgram",)))
            base["light_source"] = safe_text(value_for(exif, ("LightSource",)))
            base["jpeg_quality_metadata"] = safe_text(value_for(exif, ("Compression", "JPEGQuality")))

            # Convert to encoded sRGB-like channel values [0,1]. These metrics
            # describe rendered image pixels, not linear scene radiance.
            rgb = np.asarray(im.convert("RGB"), dtype=np.uint8)
            x = rgb.astype(np.float32) / 255.0
            r, g, b = x[..., 0], x[..., 1], x[..., 2]
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            mx = np.max(x, axis=2)
            mn = np.min(x, axis=2)
            sat = np.zeros_like(mx, dtype=np.float32)
            nonzero = mx > 0
            sat[nonzero] = (mx[nonzero] - mn[nonzero]) / mx[nonzero]

            qs = np.percentile(luma, [1, 5, 50, 95, 99])
            base["mean_encoded_luma_proxy"] = round(float(np.mean(luma)), 6)
            base["median_encoded_luma_proxy"] = round(float(np.median(luma)), 6)
            base["std_encoded_luma_proxy"] = round(float(np.std(luma)), 6)
            for key, val in zip(("luma_p01", "luma_p05", "luma_p95", "luma_p99"), (qs[0], qs[1], qs[3], qs[4])):
                base[key] = round(float(val), 6)
            base["near_black_luma_lt_0_02_pct"] = round(pct(luma < 0.02), 5)
            base["near_white_luma_gt_0_98_pct"] = round(pct(luma > 0.98), 5)
            base["pixels_any_channel_exact_0_pct"] = round(pct(np.any(rgb == 0, axis=2)), 5)
            base["pixels_any_channel_exact_255_pct"] = round(pct(np.any(rgb == 255, axis=2)), 5)
            base["mean_saturation_proxy"] = round(float(np.mean(sat)), 6)
            base["median_saturation_proxy"] = round(float(np.median(sat)), 6)
            base["decode_status"] = "PASS"
    except Exception as exc:
        base["error"] = f"{type(exc).__name__}: {exc}"
    return base


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def parse_local_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("--since format must be YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")


def sha_for_outputs(directory: Path, dest: Path) -> None:
    lines: List[str] = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path != dest:
            try:
                lines.append(f"{sha256_file(path)}  {path.relative_to(directory)}")
            except OSError as exc:
                lines.append(f"ERROR  {path.relative_to(directory)}  {exc}")
    dest.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only audit of recent images in Android DCIM/Camera; writes reports under ~/dcim_calibration/analysis_results/"
    )
    parser.add_argument("--input-dir", default="/storage/emulated/0/DCIM/Camera", help="Camera folder path")
    parser.add_argument("--project-dir", default="~/dcim_calibration", help="Project directory")
    parser.add_argument("--profile", default="V9_ConservativeBalanced", help="User-supplied profile label to annotate this batch")
    parser.add_argument("--limit", type=int, default=30, help="Analyze latest N files by modification time; use 0 for all matching images (default: 30)")
    parser.add_argument("--since", default=None, help='Only include files modified on/after local time, e.g. "2026-10-21 11:00:00" or "2026-10-21"')
    parser.add_argument("--recursive", action="store_true", help="Search subdirectories too (default: only Camera folder itself)")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser()
    project_dir = Path(args.project_dir).expanduser()
    since_dt = parse_local_datetime(args.since)
    if args.limit < 0:
        parser.error("--limit must be >= 0 (use 0 for all matching images)")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = project_dir / "analysis_results"
    output_dir = output_base / f"v9_camera_audit_{stamp}"
    suffix = 1
    while output_dir.exists():
        output_dir = output_base / f"v9_camera_audit_{stamp}_{suffix:02d}"
        suffix += 1
    try:
        output_dir.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        print(f"ERROR: Cannot create output directory {output_dir}: {exc}", file=sys.stderr)
        print("Check project path and Termux storage permissions.", file=sys.stderr)
        return 2

    log_path = output_dir / "execution_log.txt"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("v9_camera_audit")
    logger.info("Starting read-only V9 camera audit")
    logger.info("Input directory: %s", input_dir)
    logger.info("Project directory: %s", project_dir)
    logger.info("Output directory: %s", output_dir)
    logger.info("Profile label: %s (user-declared; not verified from EXIF)", args.profile)
    logger.info("Pillow version: %s; NumPy version: %s; Python: %s", Image.__version__, np.__version__, sys.version.split()[0])

    images, scan_warnings = list_images(input_dir, args.recursive, since_dt, args.limit)
    for warning in scan_warnings:
        logger.warning(warning)

    if not images:
        message = (
            f"No supported image files found in {input_dir}. If Android shared storage is not accessible, run "
            "termux-setup-storage, grant permission, reopen Termux, and retry."
        )
        logger.error(message)
        (output_dir / "README_bn.md").write_text(
            "# V9 Camera Audit — কোনো ছবি পাওয়া যায়নি\n\n"
            + message
            + "\n\nএই রান-এর লগ: `execution_log.txt`\n",
            encoding="utf-8",
        )
        sha_for_outputs(output_dir, output_dir / "output_sha256_manifest.txt")
        print(f"\nOutput directory: {output_dir}")
        return 2

    logger.info("Image files selected: %d", len(images))
    logger.info("File selection uses filesystem modification time, not guaranteed EXIF capture time.")

    profile_source = "USER-DECLARED LABEL; not independently verified by EXIF/runtime evidence"
    rows: List[Dict[str, Any]] = []
    input_hash_lines: List[str] = []
    hash_groups: Dict[str, List[str]] = defaultdict(list)
    for index, path in enumerate(images, 1):
        logger.info("[%d/%d] Analyzing %s", index, len(images), path.name)
        row = analyze_image(path, args.profile, profile_source)
        rows.append(row)
        if row.get("sha256"):
            hash_groups[row["sha256"]].append(str(path))
            input_hash_lines.append(f"{row['sha256']}  {path}")
        if row["decode_status"] != "PASS":
            logger.error("Could not decode %s: %s", path, row.get("error", "unknown error"))

    # Label exact duplicates by hash, without deleting anything.
    duplicate_groups = 0
    for digest, paths in hash_groups.items():
        if len(paths) > 1:
            duplicate_groups += 1
            label = f"DUPLICATE_GROUP_{digest[:12]}"
            for row in rows:
                if row.get("sha256") == digest:
                    row["duplicate_group"] = label

    metrics_fields = list(rows[0].keys()) if rows else []
    metrics_path = output_dir / "image_metrics.csv"
    write_csv(metrics_path, rows, metrics_fields)

    manifest_fields = [
        "file_name", "file_path", "profile_label", "profile_attribution", "file_modified_local",
        "exif_datetime_original", "sha256", "width_px", "height_px", "file_size_bytes",
        "exif_make", "exif_model", "exif_software", "exposure_time_raw", "exposure_time_s",
        "iso_raw", "f_number", "focal_length_mm", "exposure_compensation_ev", "metering_mode",
        "flash", "white_balance", "decode_status", "error"
    ]
    write_csv(output_dir / "capture_manifest.csv", rows, manifest_fields)
    (output_dir / "input_sha256_manifest.txt").write_text("\n".join(input_hash_lines) + ("\n" if input_hash_lines else ""), encoding="utf-8")

    good = [row for row in rows if row.get("decode_status") == "PASS"]
    failures = [row for row in rows if row.get("decode_status") != "PASS"]
    metric_fields = ("mean_encoded_luma_proxy", "median_encoded_luma_proxy", "std_encoded_luma_proxy",
                     "near_black_luma_lt_0_02_pct", "near_white_luma_gt_0_98_pct", "mean_saturation_proxy")
    summary: Dict[str, Any] = {
        "audit_name": "LXX521 IMX682 V9 Camera Audit",
        "created_local": datetime.now().isoformat(timespec="seconds"),
        "input_directory": str(input_dir),
        "project_directory": str(project_dir),
        "output_directory": str(output_dir),
        "selection_rule": {
            "recursive": bool(args.recursive),
            "limit": args.limit,
            "since_local": args.since or None,
            "time_filter_basis": "filesystem modification time; not guaranteed EXIF capture time",
        },
        "profile_label": args.profile,
        "profile_attribution_status": profile_source,
        "files_selected": len(images),
        "images_decoded_successfully": len(good),
        "images_failed": len(failures),
        "exact_duplicate_hash_groups": duplicate_groups,
        "dependencies": {"python": sys.version.split()[0], "pillow": Image.__version__, "numpy": np.__version__},
        "aggregate_metrics_for_descriptive_use_only": {},
        "limitations": [
            "EXIF does not prove that an XML profile was loaded or applied by LMC.",
            "The profile label is supplied by the user and is not automatically verified.",
            "Pixel statistics are calculated from rendered encoded RGB pixels.",
            "These metrics do not establish true sensor dynamic range, sensor noise, color accuracy, or MTF50.",
            "Scene matching, lighting, framing, and capture order must be verified separately.",
            "A file modification timestamp may differ from the actual capture time."
        ],
    }
    if good:
        for field in metric_fields:
            vals = []
            for row in good:
                try:
                    vals.append(float(row[field]))
                except (TypeError, ValueError, KeyError):
                    pass
            if vals:
                summary["aggregate_metrics_for_descriptive_use_only"][field] = {
                    "n": len(vals),
                    "mean": round(float(np.mean(vals)), 6),
                    "median": round(float(np.median(vals)), 6),
                    "sample_stddev": round(float(np.std(vals, ddof=1)), 6) if len(vals) > 1 else None,
                }
    summary["failed_files"] = [{"file_path": row["file_path"], "error": row["error"]} for row in failures]
    (output_dir / "audit_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    report_lines = [
        "# LXX521 / IMX682 — V9 Camera Audit",
        "",
        f"- তৈরি: {summary['created_local']}",
        f"- Input folder: `{input_dir}`",
        f"- Profile label: **{args.profile}** (ব্যবহারকারীর দেওয়া label; EXIF থেকে যাচাইকৃত নয়)",
        f"- নির্বাচিত ছবি: {len(images)}",
        f"- সফলভাবে decode: {len(good)}",
        f"- decode ব্যর্থ: {len(failures)}",
        f"- exact duplicate SHA-256 group: {duplicate_groups}",
        "",
        "## এই রান-এর ফাইল",
        "- `image_metrics.csv` — প্রতি ছবির metadata ও pixel statistics",
        "- `capture_manifest.csv` — capture/EXIF manifest",
        "- `input_sha256_manifest.txt` — input hash তালিকা",
        "- `audit_summary.json` — machine-readable summary",
        "- `execution_log.txt` — execution log",
        "- `output_sha256_manifest.txt` — generated outputs-এর hash (manifest নিজেকে বাদ দিয়ে)",
        "",
        "## পরিমাপের ব্যাখ্যা",
        "Mean/median/std encoded-luma proxy এবং near-black/near-white শতাংশ JPEG-এ দৃশ্যমান pixel distribution বর্ণনা করে। এগুলো সরাসরি sensor dynamic range বা shadow recovery প্রমাণ করে না। Saturation proxy-ও color accuracy নয়।",
        "",
        "## যাচাইয়ের সীমাবদ্ধতা",
        "EXIF থেকে XML profile LMC-তে প্রয়োগ হয়েছে কি না নিশ্চিত করা যায় না। Profile label command line থেকে দেওয়া হয়। আলো, framing, exposure, HDR state ও capture order না মিললে profile-এর causal effect দাবি করা যাবে না। এই স্ক্রিপ্ট sensor noise, true dynamic range, color accuracy বা MTF50 পরিমাপের দাবি করে না।",
        "",
        "## পরবর্তী পদক্ষেপ",
        "1. `capture_manifest.csv`-এ timestamp, exposure time, ISO ও resolution পরীক্ষা করুন।",
        "2. একই scene-এর ProBalanced এবং FullAllRounder/V9 ছবিগুলো আলাদা batch label দিয়ে চালান।",
        "3. ChatGPT-তে `image_metrics.csv`, `capture_manifest.csv`, `audit_summary.json` ও `README_bn.md` একসঙ্গে দিন; scene pairing এবং limitations-সহ interpretation চাইুন।",
        "",
    ]
    (output_dir / "README_bn.md").write_text("\n".join(report_lines), encoding="utf-8")

    logger.info("Audit complete. Success=%d Failure=%d Duplicate groups=%d", len(good), len(failures), duplicate_groups)
    logger.info("Writing output SHA-256 manifest")
    sha_for_outputs(output_dir, output_dir / "output_sha256_manifest.txt")
    print("\n=== AUDIT COMPLETE ===")
    print(f"Images selected: {len(images)}")
    print(f"Images decoded:  {len(good)}")
    print(f"Images failed:   {len(failures)}")
    print(f"Duplicate groups:{duplicate_groups}")
    print(f"Reports folder:  {output_dir}")
    print("Profile label is user-declared; this report does not verify XML runtime application.")
    return 0 if good else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled by user.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(1)
