#!/usr/bin/env python3
# Guided, one-batch-at-a-time image-quality test controller for Termux.
# Does not modify XML profiles or original images.
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HOME = Path.home()
PROJECT = HOME / "dcim_calibration"
AUDIT_SCRIPT = PROJECT / "v9_camera_audit.py"
CAMERA_DIR = Path("/storage/emulated/0/DCIM/Camera")
RESULTS_DIR = PROJECT / "analysis_results"
SESSION_DIR = RESULTS_DIR / "guided_ab_session"
STATE_FILE = SESSION_DIR / "session_state.json"
BATCHES_CSV = SESSION_DIR / "batch_log.csv"

PROFILES = [
    ("V9_ConservativeBalanced", "V9 — LXX521_IMX682_V9_ConservativeBalanced.xml"),
    ("V8_ProBalanced", "V8 ProBalanced — LXX521_IMX682_V8_ProBalanced.xml"),
    ("V8_FullAllRounder_Q100", "V8 FullAllRounder Q100 — LXX521_IMX682_V8_FullAllRounder_Q100.xml"),
]
SCENES = [
    ("bright_window", "SCENE 1 — Bright window + dark interior", 5,
     "ফোন স্থির রাখুন। একই framing-এ উজ্জ্বল জানালা ও অন্ধকার ঘর দুটোই রাখুন।"),
    ("fine_detail", "SCENE 2 — Fine detail / texture", 5,
     "বইয়ের লেখা, কাপড় বা সূক্ষ্ম texture-সহ স্থির দৃশ্য নিন। একই দূরত্ব ও framing রাখুন।"),
    ("low_light", "SCENE 3 — Low-light static scene", 10,
     "কম আলোয় স্থির দৃশ্য নিন। ফোন ও দৃশ্য স্থির রাখুন; আলো/zoom/lens বদলাবেন না।"),
]
# Balanced, rotating order to reduce time/order confounding.
ORDER = [
    ("bright_window", "V9_ConservativeBalanced"),
    ("bright_window", "V8_ProBalanced"),
    ("bright_window", "V8_FullAllRounder_Q100"),
    ("fine_detail", "V8_ProBalanced"),
    ("fine_detail", "V8_FullAllRounder_Q100"),
    ("fine_detail", "V9_ConservativeBalanced"),
    ("low_light", "V8_FullAllRounder_Q100"),
    ("low_light", "V9_ConservativeBalanced"),
    ("low_light", "V8_ProBalanced"),
]
SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}

def now_local():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def snapshot():
    result = {}
    if not CAMERA_DIR.is_dir():
        raise RuntimeError(f"Camera folder not found: {CAMERA_DIR}")
    for p in CAMERA_DIR.iterdir():
        if p.is_file() and p.suffix.lower() in SUPPORTED:
            try:
                st = p.stat()
                result[str(p)] = {
                    "size": st.st_size,
                    "mtime_ns": st.st_mtime_ns,
                    "sha256": sha256_file(p),
                }
            except OSError:
                continue
    return result

def load_state():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        return {"next_batch_index": 0, "created_local": now_local(), "completed": []}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"State file is unreadable: {STATE_FILE} ({e})")

def save_state(state):
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_FILE)

def append_batch_row(row):
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    exists = BATCHES_CSV.exists()
    with BATCHES_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "batch_index", "scene_id", "scene_label", "profile_label", "expected_count",
            "start_local", "end_local", "new_files_count", "audit_status", "report_dir",
            "new_file_names", "notes"
        ])
        if not exists:
            writer.writeheader()
        writer.writerow(row)

def read_capture_manifest(report_dir: Path):
    manifest = report_dir / "capture_manifest.csv"
    if not manifest.exists():
        return []
    with manifest.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def main():
    ap = argparse.ArgumentParser(
        description="Interactive Termux A/B test: one profile/scene batch per run; preserves originals/XML."
    )
    ap.add_argument("--reset", action="store_true", help="Start a new guided session (does not delete prior reports).")
    ap.add_argument("--status", action="store_true", help="Show current session progress only.")
    args = ap.parse_args()

    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    if args.reset:
        if STATE_FILE.exists():
            backup = STATE_FILE.with_name(f"session_state_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            backup.write_bytes(STATE_FILE.read_bytes())
        state = {"next_batch_index": 0, "created_local": now_local(), "completed": []}
        save_state(state)
        print("New guided session initialized. Previous reports and images were not deleted.")
        print("Run `python guided_v9_ab_test.py` again when you are ready to begin Batch 1.")
        return

    if not AUDIT_SCRIPT.is_file():
        sys.exit(f"ERROR: Existing audit script not found: {AUDIT_SCRIPT}")
    if not CAMERA_DIR.is_dir():
        sys.exit(f"ERROR: Camera folder not found: {CAMERA_DIR}")
    if args.status:
        state = load_state()
        print(f"Session: {SESSION_DIR}")
        print(f"Completed batches: {len(state.get('completed', []))}/{len(ORDER)}")
        idx = state.get("next_batch_index", 0)
        if idx < len(ORDER):
            print(f"Next batch: {idx + 1}/{len(ORDER)} — {ORDER[idx][0]} / {ORDER[idx][1]}")
        else:
            print("All planned batches marked complete.")
        return

    state = load_state()
    idx = int(state.get("next_batch_index", 0))
    if idx >= len(ORDER):
        print("All 9 planned batches are marked complete.")
        print(f"Batch log: {BATCHES_CSV}")
        print(f"Session folder: {SESSION_DIR}")
        print("Review all manifests before drawing a profile-quality conclusion.")
        return

    scene_id, profile_label = ORDER[idx]
    scene = next(s for s in SCENES if s[0] == scene_id)
    _, scene_title, expected_count, scene_note = scene
    profile_title = next(p[1] for p in PROFILES if p[0] == profile_label)

    print("=" * 68)
    print(f"GUIDED CAMERA TEST — Batch {idx + 1}/{len(ORDER)}")
    print(f"Scene: {scene_title}")
    print(f"Profile: {profile_title}")
    print(f"Required new photos: {expected_count}")
    print(f"Camera folder: {CAMERA_DIR}")
    print("=" * 68)
    print("\nBefore continuing:")
    print("1. Open LMC 8.4 yourself; this script cannot operate the camera UI.")
    print("2. Select/load the exact profile named above and verify it in the app.")
    print("3. Set the scene as described below and keep lens/zoom/framing fixed.")
    print(f"Scene instruction: {scene_note}")
    print("4. Do not take unrelated photos or copy files into DCIM/Camera during this batch.")
    input("\nWhen the correct profile and scene are ready, press ENTER to snapshot the folder... ")

    before = snapshot()
    start_dt = datetime.now().astimezone()
    start_arg = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nBatch start recorded: {start_dt.isoformat(timespec='seconds')}")
    print(f"Now take exactly {expected_count} photo(s).")
    input(f"After all {expected_count} photos are saved, return to Termux and press ENTER... ")
    end_dt = datetime.now().astimezone()
    after = snapshot()

    changed = []
    for name, info in after.items():
        old = before.get(name)
        if old is None or old["sha256"] != info["sha256"] or old["size"] != info["size"]:
            changed.append((Path(name), info))
    changed.sort(key=lambda pair: pair[1]["mtime_ns"])

    batch_id = f"batch_{idx+1:02d}_{scene_id}_{profile_label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    batch_dir = SESSION_DIR / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    new_manifest = batch_dir / "observed_new_files.csv"
    with new_manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file_name", "file_path", "size_bytes", "mtime_ns", "sha256"])
        for p, info in changed:
            w.writerow([p.name, str(p), info["size"], info["mtime_ns"], info["sha256"]])

    print(f"\nNew/changed image files detected: {len(changed)}")
    for p, _ in changed:
        print(f"  - {p.name}")

    if len(changed) != expected_count:
        msg = (
            f"INVALID BATCH: expected {expected_count} new/changed files, detected {len(changed)}. "
            "The session did NOT advance. Do not delete anything; check the camera folder and rerun "
            "this same step after resolving the issue. If the intended images already exist, use a fresh "
            "batch with exactly the required new captures."
        )
        (batch_dir / "BATCH_STATUS.txt").write_text(msg + "\n", encoding="utf-8")
        append_batch_row({
            "batch_index": idx + 1, "scene_id": scene_id, "scene_label": scene_title,
            "profile_label": profile_label, "expected_count": expected_count,
            "start_local": start_dt.isoformat(timespec="seconds"), "end_local": end_dt.isoformat(timespec="seconds"),
            "new_files_count": len(changed), "audit_status": "INVALID_FILE_COUNT",
            "report_dir": str(batch_dir), "new_file_names": ";".join(p.name for p, _ in changed),
            "notes": "Session not advanced; inspect file selection."
        })
        print("\n" + msg)
        print(f"Observed file manifest: {new_manifest}")
        return

    # The existing audit script selects by mtime, so use the batch start time and exact expected count.
    cmd = [
        sys.executable, str(AUDIT_SCRIPT),
        "--profile", profile_label,
        "--since", start_arg,
        "--limit", str(expected_count),
    ]
    print("\nRunning existing read-only audit script:")
    print(" ".join(repr(x) for x in cmd))
    proc = subprocess.run(cmd, cwd=str(PROJECT))
    if proc.returncode != 0:
        print(f"\nAudit script returned exit code {proc.returncode}. Session NOT advanced.")
        append_batch_row({
            "batch_index": idx + 1, "scene_id": scene_id, "scene_label": scene_title,
            "profile_label": profile_label, "expected_count": expected_count,
            "start_local": start_dt.isoformat(timespec="seconds"), "end_local": end_dt.isoformat(timespec="seconds"),
            "new_files_count": len(changed), "audit_status": f"AUDIT_EXIT_{proc.returncode}",
            "report_dir": str(batch_dir), "new_file_names": ";".join(p.name for p, _ in changed),
            "notes": "Session not advanced."
        })
        return

    # Find the most recently created report directory and verify the audited SHA set against this batch.
    report_dirs = sorted(
        [p for p in RESULTS_DIR.glob("v9_camera_audit_*") if p.is_dir()],
        key=lambda p: p.stat().st_mtime_ns,
        reverse=True,
    )
    report_dir = report_dirs[0] if report_dirs else None
    expected_hashes = {info["sha256"] for _, info in changed}
    audited_rows = read_capture_manifest(report_dir) if report_dir else []
    audited_hashes = {r.get("sha256", "").strip() for r in audited_rows if r.get("sha256")}
    hashes_match = (expected_hashes == audited_hashes and len(audited_rows) == expected_count)
    status = "PASS_BATCH_HASH_MATCH" if hashes_match else "REVIEW_AUDIT_SELECTION"
    (batch_dir / "BATCH_STATUS.txt").write_text(
        f"Status: {status}\n"
        f"Expected image count: {expected_count}\n"
        f"Detected new/changed count: {len(changed)}\n"
        f"Audit report: {report_dir if report_dir else 'NOT FOUND'}\n"
        f"SHA-256 set match: {hashes_match}\n"
        "Profile attribution remains user-declared; this script does not prove runtime XML application.\n",
        encoding="utf-8",
    )
    append_batch_row({
        "batch_index": idx + 1, "scene_id": scene_id, "scene_label": scene_title,
        "profile_label": profile_label, "expected_count": expected_count,
        "start_local": start_dt.isoformat(timespec="seconds"), "end_local": end_dt.isoformat(timespec="seconds"),
        "new_files_count": len(changed), "audit_status": status,
        "report_dir": str(report_dir) if report_dir else str(batch_dir),
        "new_file_names": ";".join(p.name for p, _ in changed),
        "notes": "Profile label is manual; runtime application not independently verified."
    })
    if not hashes_match:
        print("\nWARNING: Audit-selected image hashes do not exactly match this batch.")
        print("This batch is saved for review, but the session will NOT advance.")
        print(f"Inspect: {batch_dir / 'BATCH_STATUS.txt'}")
        return

    state.setdefault("completed", []).append({
        "batch_index": idx + 1, "scene_id": scene_id, "profile_label": profile_label,
        "report_dir": str(report_dir), "batch_dir": str(batch_dir), "completed_local": now_local()
    })
    state["next_batch_index"] = idx + 1
    save_state(state)
    print("\nBATCH PASS: New file count and audited SHA-256 set match.")
    print("Original images and XML profiles were not modified by this controller.")
    print(f"Batch evidence: {batch_dir}")
    print(f"Audit report: {report_dir}")
    if idx + 1 < len(ORDER):
        ns, np = ORDER[idx + 1]
        nscene = next(s for s in SCENES if s[0] == ns)
        nprofile = next(p for p in PROFILES if p[0] == np)
        print(f"\nNEXT STEP: Run the same script again. It will guide Batch {idx+2}/{len(ORDER)}:")
        print(f"  Scene: {nscene[1]}")
        print(f"  Profile: {nprofile[1]}")
        print("Do not switch scene/profile until the next run instructs you.")
    else:
        print("\nALL PLANNED BATCHES COMPLETE.")
        print(f"Session folder: {SESSION_DIR}")
        print(f"Batch log: {BATCHES_CSV}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. No XML or original image was intentionally modified.")
        sys.exit(130)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
