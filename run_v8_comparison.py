#!/usr/bin/env python
# Read-only V8 profile and JPEG comparison audit.
# Original inputs are never modified.

import os
import sys
import csv
import json
import math
import hashlib
import logging
import platform
import statistics
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.home() / "dcim_calibration"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUT = ROOT / "analysis_results" / f"v8_comparison_{STAMP}"
OUT.mkdir(parents=True, exist_ok=False)

LOG_PATH = OUT / "execution_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8"),
              logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("v8-audit")

PROFILE_NAMES = [
    "LXX521_IMX682_V8_ProBalanced.xml",
    "LXX521_IMX682_V8_FullAllRounder_Q100.xml",
]
IMAGE_NAMES = [
    "20261021_104706_lmc_8.4.jpg",
    "20261021_104551_lmc_8.4.jpg",
    "20261021_104549_lmc_8.4.jpg",
    "20261021_104547_lmc_8.4.jpg",
    "20261021_104544_lmc_8.4.jpg",
    "20261021_104540_lmc_8.4.jpg",
    "020261021_104531_LXX521_IMX682_V8_ProBalanced.jpg",
    "020261021_104528_LXX521_IMX682_V8_ProBalanced.jpg",
    "020261021_104526_LXX521_IMX682_V8_ProBalanced.jpg",
    "020261021_104524_LXX521_IMX682_V8_ProBalanced.jpg",
    "020261021_104516_LXX521_IMX682_V8_ProBalanced.jpg",
    "020261021_104647_LXX521_IMX682_V8_ProBalanced.jpg",
]
IMAGE_PROFILES = {
    "20261021_104706_lmc_8.4.jpg": "FullAllRounder_Q100",
    "20261021_104551_lmc_8.4.jpg": "FullAllRounder_Q100",
    "20261021_104549_lmc_8.4.jpg": "FullAllRounder_Q100",
    "20261021_104547_lmc_8.4.jpg": "FullAllRounder_Q100",
    "20261021_104544_lmc_8.4.jpg": "FullAllRounder_Q100",
    "20261021_104540_lmc_8.4.jpg": "FullAllRounder_Q100",
    "020261021_104531_LXX521_IMX682_V8_ProBalanced.jpg": "ProBalanced",
    "020261021_104528_LXX521_IMX682_V8_ProBalanced.jpg": "ProBalanced",
    "020261021_104526_LXX521_IMX682_V8_ProBalanced.jpg": "ProBalanced",
    "020261021_104524_LXX521_IMX682_V8_ProBalanced.jpg": "ProBalanced",
    "020261021_104516_LXX521_IMX682_V8_ProBalanced.jpg": "ProBalanced",
    "020261021_104647_LXX521_IMX682_V8_ProBalanced.jpg": "ProBalanced",
}

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def locate(name):
    candidates = [
        ROOT / name,
        ROOT / "profiles" / name,
        ROOT / "analysis_results" / name,
        Path("/sdcard/Download") / name,
        Path("/sdcard/DCIM/Camera") / name,
        Path.home() / "storage" / "shared" / "DCIM" / "Camera" / name,
        Path("/sdcard/Pictures") / name,
    ]
    found = []
    for p in candidates:
        try:
            if p.is_file() and p not in found:
                found.append(p)
        except OSError as e:
            log.warning("Path check failed: %s: %s", p, e)
    if found:
        return found
    # Search the project tree for files not at expected locations.
    try:
        for p in ROOT.rglob(name):
            if p.is_file() and OUT not in p.parents and p not in found:
                found.append(p)
    except OSError as e:
        log.warning("Recursive search warning for %s: %s", name, e)
    return found

def xml_entries(path):
    tree = ET.parse(path)
    root = tree.getroot()
    entries = {}
    duplicates = []
    for el in root.iter():
        if el is root:
            continue
        # Preserve full XML path and exact element text/attributes.
        parts = []
        node = el
        while node is not None and node is not root:
            tag = node.tag
            siblings = []
            parent = None
            for candidate in root.iter():
                if node in list(candidate):
                    parent = candidate
                    siblings = [x for x in list(parent) if x.tag == tag]
                    break
            index = siblings.index(node) if node in siblings else 0
            parts.append(f"{tag}[{index}]")
            node = parent
        key = "/" + "/".join(reversed(parts))
        value = {
            "text": (el.text or "").strip(),
            "attributes": dict(sorted(el.attrib.items())),
        }
        if key in entries:
            duplicates.append(key)
        entries[key] = value
    return root.tag, entries, duplicates

def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def optional_versions():
    out = {"python": sys.version, "platform": platform.platform()}
    for module in ("PIL", "numpy", "cv2"):
        try:
            m = __import__(module)
            out[module] = getattr(m, "__version__", "version unavailable")
        except Exception as e:
            out[module] = f"unavailable: {e}"
    return out

def image_metrics(path):
    result = {"path": str(path), "filename": path.name}
    try:
        result["size_bytes"] = path.stat().st_size
        result["sha256"] = sha256(path)
        from PIL import Image, ImageStat
        import numpy as np

        with Image.open(path) as im:
            result["format"] = im.format
            result["mode"] = im.mode
            result["width"], result["height"] = im.size
            rgb = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0

        # sRGB encoded RGB to encoded-space luma proxy; not linear luminance.
        y = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
        mx = rgb.max(axis=2)
        mn = rgb.min(axis=2)
        sat = np.where(mx > 1e-8, (mx - mn) / np.maximum(mx, 1e-8), 0)

        result.update({
            "decode_status": "PASS",
            "mean_luma_srgb_proxy": float(np.mean(y)),
            "median_luma_srgb_proxy": float(np.median(y)),
            "std_luma_srgb_proxy": float(np.std(y)),
            "p01_luma": float(np.percentile(y, 1)),
            "p05_luma": float(np.percentile(y, 5)),
            "p95_luma": float(np.percentile(y, 95)),
            "p99_luma": float(np.percentile(y, 99)),
            "near_black_fraction_lt_0_02": float(np.mean(y < 0.02)),
            "near_white_fraction_gt_0_98": float(np.mean(y > 0.98)),
            "mean_saturation_srgb": float(np.mean(sat)),
            "highlight_fraction_ge_0_98": float(np.mean(y >= 0.98)),
            "metric_note": "JPEG sRGB-encoded luma proxy; descriptive only, not linear luminance, dynamic range, color accuracy, sensor noise, or MTF50."
        })
    except Exception as e:
        result["decode_status"] = "FAIL"
        result["error"] = repr(e)
        log.exception("Image analysis failed: %s", path)
    return result

def main():
    log.info("Project root: %s", ROOT)
    log.info("Output directory: %s", OUT)
    log.info("Read-only audit; no source profiles or images will be changed.")

    inventory = []
    profile_results = {}
    for name in PROFILE_NAMES:
        paths = locate(name)
        if not paths:
            log.error("MISSING PROFILE: %s", name)
            profile_results[name] = {"status": "MISSING", "paths": []}
            continue
        profile_results[name] = {"status": "FOUND", "paths": []}
        for p in paths:
            try:
                record = {
                    "name": name, "path": str(p),
                    "size_bytes": p.stat().st_size,
                    "mtime": datetime.fromtimestamp(
                        p.stat().st_mtime, timezone.utc
                    ).isoformat(),
                    "sha256": sha256(p),
                    "readable": os.access(p, os.R_OK),
                }
                try:
                    root_tag, entries, duplicates = xml_entries(p)
                    record.update({
                        "xml_status": "PASS",
                        "root_tag": root_tag,
                        "key_count": len(entries),
                        "duplicate_paths": duplicates,
                    })
                    profile_results[name]["paths"].append({
                        "path": str(p), "sha256": record["sha256"],
                        "root_tag": root_tag, "key_count": len(entries),
                        "entries": entries, "duplicates": duplicates,
                    })
                except Exception as e:
                    record["xml_status"] = "FAIL"
                    record["xml_error"] = repr(e)
                    log.exception("XML parse failed: %s", p)
                inventory.append(record)
            except OSError as e:
                log.exception("Cannot inspect %s", p)
                inventory.append({"name": name, "path": str(p),
                                  "error": repr(e)})

    diff_rows = []
    relevant_rows = []
    comparison_notes = []
    valid_profiles = []
    for name in PROFILE_NAMES:
        good = [x for x in profile_results[name].get("paths", [])
                if "entries" in x]
        if good:
            # Prefer profiles/ copy when present; retain all copies in inventory.
            chosen = next((x for x in good if "/profiles/" in x["path"]),
                          good[0])
            valid_profiles.append((name, chosen))

    if len(valid_profiles) == 2:
        (name_a, a), (name_b, b) = valid_profiles
        ea, eb = a["entries"], b["entries"]
        for key in sorted(set(ea) | set(eb)):
            va, vb = ea.get(key), eb.get(key)
            if va is None:
                status = "FULLALLROUNDER_ONLY"
            elif vb is None:
                status = "PROBALANCED_ONLY"
            elif va == vb:
                status = "IDENTICAL"
            else:
                status = "DIFFERENT"
            diff_rows.append({
                "xml_path": key, "status": status,
                "ProBalanced_value": json.dumps(va, ensure_ascii=False, sort_keys=True) if va is not None else "",
                "FullAllRounder_Q100_value": json.dumps(vb, ensure_ascii=False, sort_keys=True) if vb is not None else "",
            })
            low = key.lower()
            terms = ("hdr", "exposure", "iso", "frame", "jpeg", "sharp",
                     "denois", "satur", "luma", "chroma", "resolution",
                     "quality", "focus", "noise", "awb", "whitebalance")
            if any(t in low for t in terms):
                relevant_rows.append({
                    "xml_path": key, "status": status,
                    "ProBalanced_value": json.dumps(va, ensure_ascii=False, sort_keys=True) if va is not None else "",
                    "FullAllRounder_Q100_value": json.dumps(vb, ensure_ascii=False, sort_keys=True) if vb is not None else "",
                    "interpretation_status": "NAME-BASED CANDIDATE ONLY; operational meaning/runtime application unverified",
                })
        comparison_notes.append(f"Compared XML files: {a['path']} and {b['path']}")
        comparison_notes.append(f"ProBalanced SHA-256: {a['sha256']}")
        comparison_notes.append(f"FullAllRounder Q100 SHA-256: {b['sha256']}")
        comparison_notes.append("XML presence and parsing do not prove LMC runtime application.")
    else:
        comparison_notes.append("XML comparison incomplete: both valid target XML files were not found and parsed.")

    write_csv(OUT / "input_inventory.csv",
              ["name", "path", "size_bytes", "mtime", "sha256", "readable",
               "xml_status", "root_tag", "key_count", "duplicate_paths",
               "error", "xml_error"], inventory)
    write_csv(OUT / "xml_key_differences.csv",
              ["xml_path", "status", "ProBalanced_value",
               "FullAllRounder_Q100_value"], diff_rows)
    write_csv(OUT / "relevant_settings.csv",
              ["xml_path", "status", "ProBalanced_value",
               "FullAllRounder_Q100_value", "interpretation_status"], relevant_rows)

    image_rows = []
    seen_profile_hashes = set()
    for name in IMAGE_NAMES:
        profile = IMAGE_PROFILES.get(name, "UNKNOWN")
        paths = locate(name)
        if not paths:
            log.warning("MISSING IMAGE: %s", name)
        for p in paths:
            try:
                digest = sha256(p)
            except OSError as e:
                log.warning("Cannot hash image %s: %s", p, e)
                row = image_metrics(p)
                row["profile"] = profile
                row["profile_assignment_basis"] = "user_reported"
                image_rows.append(row)
                continue

            identity = (profile, digest)
            if identity in seen_profile_hashes:
                log.info(
                    "Skipping duplicate content for profile %s: %s",
                    profile, p
                )
                continue

            seen_profile_hashes.add(identity)
            row = image_metrics(p)
            row["profile"] = profile
            row["profile_assignment_basis"] = "user_reported"
            image_rows.append(row)
    write_csv(OUT / "image_metrics.csv", [
        "profile", "profile_assignment_basis",
        "path", "filename", "size_bytes", "sha256", "format", "mode",
        "width", "height", "decode_status", "mean_luma_srgb_proxy",
        "median_luma_srgb_proxy", "std_luma_srgb_proxy", "p01_luma",
        "p05_luma", "p95_luma", "p99_luma",
        "near_black_fraction_lt_0_02", "near_white_fraction_gt_0_98",
        "mean_saturation_srgb", "highlight_fraction_ge_0_98",
        "metric_note", "error"
    ], image_rows)

    # Template only: no unverified capture metadata is fabricated.
    manifest_fields = [
        "scene_id", "capture_id", "profile", "capture_timestamp",
        "source_filename", "device_model", "Android_version", "LMC_version",
        "camera_id", "resolution", "exposure_time", "ISO", "white_balance",
        "focus_state", "HDR_state", "zoom", "flash_state",
        "scene_lighting_notes", "camera_position_notes", "capture_order",
        "retake_or_failure_notes", "metadata_availability", "SHA256"
    ]
    write_csv(OUT / "capture_manifest_template.csv", manifest_fields, [])

    runtime_rows = []
    for parameter in [
        "LMC version", "Android version", "device model",
        "active camera ID", "active profile", "HDR/HDR+ state",
        "exposure time", "ISO", "white balance", "focus state",
        "output resolution", "zoom", "flash state"
    ]:
        runtime_rows.append({
            "parameter": parameter, "configured_or_expected": "",
            "observed_value": "", "evidence_source": "Not available to this script",
            "verification_status": "UNVERIFIABLE",
            "limitation": "Must be recorded on the phone during capture."
        })
    write_csv(OUT / "runtime_verification_matrix.csv", [
        "parameter", "configured_or_expected", "observed_value",
        "evidence_source", "verification_status", "limitation"
    ], runtime_rows)

    write_csv(OUT / "matched_pair_manifest.csv", [
        "scene_id", "ProBalanced_file", "FullAllRounder_Q100_file",
        "pairing_rationale", "pair_status", "notes"
    ], [])
    write_csv(OUT / "statistical_summary.csv", [
        "scene_id", "metric", "profile_A_n", "profile_A_mean",
        "profile_A_sd", "profile_B_n", "profile_B_mean",
        "profile_B_sd", "effect_estimate", "confidence_interval",
        "status", "limitations"
    ], [])

    versions = optional_versions()
    report = {
        "project_root": str(ROOT),
        "output_dir": str(OUT),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "read-only static audit and descriptive JPEG metrics",
        "profiles": {
            k: {kk: vv for kk, vv in v.items() if kk != "paths"}
            for k, v in profile_results.items()
        },
        "image_files_analyzed": len(image_rows),
        "decoded_images": sum(r.get("decode_status") == "PASS" for r in image_rows),
        "xml_differences_rows": len(diff_rows),
        "relevant_setting_rows": len(relevant_rows),
        "software_versions": versions,
        "conclusion": "INCONCLUSIVE",
        "limitations": [
            "This script cannot verify which profile LMC applied at runtime.",
            "Existing images are not assumed to be controlled or matched.",
            "sRGB JPEG metrics are descriptive and are not sensor measurements.",
            "No MTF50, color accuracy, or defensible sensor-noise claim is made.",
            "The script has not been executed on the phone unless the user runs it there."
        ],
        "comparison_notes": comparison_notes,
    }
    (OUT / "audit_results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    readme = f"""# V8 Profile Comparison Audit

- Output: `{OUT}`
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
`python {ROOT / 'run_v8_comparison.py'}`
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    notes = "# XML Comparison Notes\n\n"
    notes += "\n".join(f"- {x}" for x in comparison_notes)
    notes += "\n\nOnly exact parsed paths and values are compared. XML names do not establish semantics.\n"
    notes += "Runtime application remains unverified.\n"
    (OUT / "xml_comparison_notes.md").write_text(notes, encoding="utf-8")

    protocol = """# নিয়ন্ত্রিত V8 Capture Protocol

প্রোফাইল A: LXX521_IMX682_V8_ProBalanced.xml
প্রোফাইল B: LXX521_IMX682_V8_FullAllRounder_Q100.xml

## দৃশ্য
1. দিনের আলো ও সূক্ষ্ম ডিটেইল
2. উজ্জ্বল জানালা ও অন্ধকার ঘর
3. গভীর ছায়া ও shadow texture
4. নিরপেক্ষ রং ও বৈধ color reference
5. slanted-edge target ও fine texture
6. কম আলো

## প্রতি দৃশ্যে
- প্রথম পাঁচ দৃশ্যে প্রতি প্রোফাইলে অন্তত ৫টি capture।
- Low-light দৃশ্যে প্রতি প্রোফাইলে অন্তত ১০টি capture।
- স্থির ফোন/ট্রাইপড, একই lens, distance, framing, lighting ও focus রাখুন।
- সম্ভব হলে order ব্যবহার করুন A,B,B,A,A,B,B,A,A,B; অন্য দৃশ্যে B দিয়ে শুরু করুন।
- প্রতি capture-এর timestamp, profile, resolution, exposure, ISO, WB, HDR state,
  camera ID ও SHA-256 লিখুন; অনুপস্থিত মান ফাঁকা রাখুন।
- ব্যর্থ capture ও retake মুছবেন না; কারণ নথিভুক্ত করুন।
- Burst/HDR stacking/temporal denoising থাকলে frames-কে স্বাধীন sample ধরে নেবেন না।
- একই profile বারবার নির্বাচন করার পর LMC UI-তে active selection যাচাই করুন।
- XML setting উপস্থিত থাকা মানেই runtime-এ প্রয়োগ হওয়া নয়।
"""
    (OUT / "capture_protocol_bn.md").write_text(protocol, encoding="utf-8")

    report_lines = [
        "# V8 Profile Comparison — প্রাথমিক রিপোর্ট",
        "",
        f"- প্রকল্প: `{ROOT}`",
        f"- আউটপুট: `{OUT}`",
        f"- সময় UTC: `{report['timestamp_utc']}`",
        "- সিদ্ধান্ত: **INCONCLUSIVE**",
        "",
        "## যাচাইকৃত সীমা",
        f"- XML difference rows: {len(diff_rows)}",
        f"- JPEG metric rows: {len(image_rows)}",
        f"- Decode PASS: {report['decoded_images']}",
        "",
        "## সতর্কতা",
        "- XML parse PASS হলে শুধু XML গঠন বৈধ বোঝায়; LMC-তে runtime প্রয়োগ প্রমাণ হয় না।",
        "- ভিন্ন framing বা exposure-এর JPEG-কে controlled matched pair ধরা হয়নি।",
        "- JPEG luma/saturation হলো বর্ণনামূলক মেট্রিক; dynamic range, color accuracy বা sensor noise নয়।",
        "- বর্তমান runtime verification এই স্ক্রিপ্ট থেকে সম্ভব হয়নি।",
        "",
        "## পরবর্তী পদক্ষেপ",
        "1. `capture_protocol_bn.md` অনুসারে নিয়ন্ত্রিত capture নিন।",
        "2. `capture_manifest_template.csv` পূরণ করুন; অজানা মান ফাঁকা রাখুন।",
        "3. সব capture একই project-এর অধীনে রাখুন এবং পরবর্তী অডিটে সেগুলো দিন।",
    ]
    (OUT / "final_report_bn.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    # Hash all generated artifacts except the hash manifest itself.
    hash_path = OUT / "output_sha256_manifest.txt"
    files = sorted(p for p in OUT.rglob("*") if p.is_file() and p != hash_path)
    hash_path.write_text(
        "".join(f"{sha256(p)}  {p.relative_to(OUT)}\n" for p in files),
        encoding="utf-8"
    )

    # Verify archive-free artifacts and hashes.
    for p in OUT.iterdir():
        if p.is_file() and p.stat().st_size == 0:
            log.warning("Empty artifact/template: %s", p.name)

    log.info("Audit complete. Output directory: %s", OUT)
    log.info("Decision: INCONCLUSIVE")
    log.info("Profiles found: %s", {
        k: v["status"] for k, v in profile_results.items()
    })
    log.info("Images found/analyzed: %d", len(image_rows))
    log.info("Read original inputs only; output files created in new directory.")
    print("\nOUTPUT_DIR=" + str(OUT))
    return 0 if len(valid_profiles) == 2 else 2

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logging.exception("Fatal audit failure")
        sys.exit(1)
