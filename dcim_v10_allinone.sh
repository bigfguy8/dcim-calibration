#!/data/data/com.termux/files/usr/bin/bash
# DCIM Calibration — LXX521 / IMX682
# One-file audit + V10 candidate starter + explicitly confirmed image cleanup.
# Default: audit and create an UNMODIFIED baseline candidate. Never deletes files.
set -Eeuo pipefail
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
export DCIM_SCRIPT_DIR="$SCRIPT_DIR"
exec python - "$@" <<'PY'
from __future__ import annotations
import argparse, ast, collections, datetime, hashlib, json, os, re, shutil, sys, tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

VERSION = "2.0.0"
EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache", ".mypy_cache"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif", ".avif", ".heic", ".heif", ".dng", ".cr2", ".cr3", ".nef", ".arw", ".rw2", ".orf", ".pef"}
GENERATED_DIR_MARKERS = {"generated", "charts", "chart", "plots", "plot", "figures", "figure", "thumbnails", "thumbnail", "previews", "preview", "contact_sheet", "contact_sheets", "contact-sheet", "contact-sheets", "visual_review", "visual-review", "rendered", "render", "heatmaps", "heatmap", "montage", "montages", "report_images", "benchmark_output", "dcim_chart_audit"}
GENERATED_NAME_MARKERS = ("contact_sheet", "contact-sheet", "montage", "heatmap", "histogram", "plot_", "chart_", "thumbnail", "preview", "annotated", "overlay", "_diff", "comparison", "visual_review", "visual-review")
PROTECTED_PATH_PARTS = {"source", "sources", "input", "inputs", "dataset", "datasets", "original", "originals", "reference", "references", "baseline", "captured", "captures", "camera_captures", "test_data", "test_images", "raw", "backups", "backup", "archive", "archives"}


def now_stamp(): return datetime.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""): h.update(b)
    return h.hexdigest()
def rel(path: Path, root: Path) -> str:
    try: return str(path.relative_to(root))
    except ValueError: return str(path)
def is_inside(path: Path, root: Path) -> bool:
    try: path.resolve().relative_to(root.resolve()); return True
    except (ValueError, OSError): return False

def walk_files(root: Path):
    for base, dirs, names in os.walk(root, followlinks=False):
        basep = Path(base)
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE_DIRS and not (basep.name == "analysis_results" and d in {"dcim_master", "audit_results"}) and d != "V10_Workbench")
        for name in sorted(names):
            p = basep / name
            if p.is_symlink(): continue
            try:
                if p.is_file(): yield p
            except OSError: continue

def python_audit(p: Path):
    try:
        src = p.read_text(encoding="utf-8-sig", errors="strict")
        tree = ast.parse(src, filename=str(p))
        imports, ops, guards = [], [], False
        operation_names = {"remove", "unlink", "rmtree", "rename", "replace", "move", "write_text", "write_bytes", "write", "copy", "copy2", "copyfile", "mkdir", "rmdir"}
        for n in ast.walk(tree):
            if isinstance(n, ast.Import): imports.extend({"module": a.name.split(".")[0], "line": n.lineno} for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module: imports.append({"module": n.module.split(".")[0], "line": n.lineno})
            elif isinstance(n, ast.If):
                try:
                    s = ast.unparse(n.test)
                    if "__name__" in s and "__main__" in s: guards = True
                except Exception: pass
            elif isinstance(n, ast.Call):
                nm = n.func.id if isinstance(n.func, ast.Name) else n.func.attr if isinstance(n.func, ast.Attribute) else ""
                if nm in operation_names: ops.append({"line": getattr(n, "lineno", None), "operation": nm})
        return {"ok": True, "error": None, "imports": imports, "main_guard": guards, "file_operations_to_review": ops}
    except SyntaxError as e: return {"ok": False, "error": f"SyntaxError line {e.lineno}: {e.msg}", "imports": [], "main_guard": False, "file_operations_to_review": []}
    except Exception as e: return {"ok": False, "error": f"{type(e).__name__}: {e}", "imports": [], "main_guard": False, "file_operations_to_review": []}

def xml_audit(p: Path):
    try:
        root = ET.parse(p).getroot()
        return {"ok": True, "error": None, "root_tag": root.tag.split("}")[-1], "root_attributes": root.attrib, "element_count": sum(1 for _ in root.iter())}
    except Exception as e: return {"ok": False, "error": f"{type(e).__name__}: {e}", "root_tag": None, "root_attributes": {}, "element_count": 0}

def is_generated_image(p: Path, root: Path):
    rel_parts = [part.lower().replace(" ", "_") for part in p.relative_to(root).parts]
    if not rel_parts or p.suffix.lower() not in IMAGE_EXTS: return False
    # Never treat known input/evidence/backups as disposable, even if nested under results.
    if any(part in PROTECTED_PATH_PARTS or part.startswith("backup_") or part.startswith("v10_backups") for part in rel_parts[:-1]): return False
    if not any(part in GENERATED_DIR_MARKERS or any(marker in part for marker in ("visual_review", "contact_sheet", "chart_audit", "generated_images", "benchmark_plot")) for part in rel_parts[:-1]):
        if not any(marker in p.name.lower() for marker in GENERATED_NAME_MARKERS): return False
    # Restrict generated cleanup to project outputs, not arbitrary app/photo folders.
    top = rel_parts[0]
    allowed_top = {"analysis_results", "v10_master_output", "v10_workbench", "outputs", "output", "generated", "charts", "plots", "reports"}
    return top in allowed_top

def candidate_source(root: Path):
    choices = [
        "profiles/LXX521_IMX682_LMC84_AllRounder.xml",
        "profiles/LXX521_IMX682_AllRounder_NaturalBalanced.xml",
        "profiles/LXX521_IMX682_Super_AllInOne_V7_NaturalNight.xml",
        "LXX521_IMX682_AllInOne_Master.xml",
        "profiles/LXX521_IMX682_AllInOne_Master.xml",
    ]
    for item in choices:
        p = root / item
        if p.is_file() and not p.is_symlink():
            try: ET.parse(p); return p
            except Exception: continue
    return None

def write_candidate(root: Path, run_dir: Path):
    src = candidate_source(root)
    if not src: return {"status": "NOT_CREATED", "reason": "No valid baseline XML found among known candidates. Specify/inspect a baseline manually; no profile was invented."}
    candidate_dir = run_dir / "V10_candidate"
    candidate_dir.mkdir(parents=True, exist_ok=False)
    out = candidate_dir / "V10_candidate_baseline_UNVALIDATED.xml"
    src_hash = sha256(src)
    # Copy bytes exactly; no parameter values are changed or fabricated.
    with src.open("rb") as rf, out.open("xb") as wf:
        shutil.copyfileobj(rf, wf); wf.flush(); os.fsync(wf.fileno())
    out_hash = sha256(out)
    if src_hash != out_hash:
        out.unlink(missing_ok=True)
        return {"status": "FAILED", "reason": "Baseline copy hash mismatch; output removed."}
    ET.parse(out)
    manifest = {
        "schema_version": 1,
        "created_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "STARTER_BASELINE_COPY_NOT_TUNED_NOT_DEVICE_VALIDATED",
        "device_target": "LXX521 / Sony IMX682 / LMC 8.4 (compatibility not yet verified)",
        "source_profile": rel(src, root), "source_sha256": src_hash,
        "candidate_profile": str(out), "candidate_sha256": out_hash,
        "parameters_changed": False,
        "note": "V10 work has been initialized from an existing XML baseline. No calibration values were invented or modified. Validate LMC 8.4 compatibility and compare controlled captures before promoting this candidate."
    }
    (candidate_dir / "V10_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (candidate_dir / "NEXT_STEPS.txt").write_text(
        "V10 CANDIDATE — NOT A VERIFIED RELEASE\n\n"
        "1. Preserve this baseline and its SHA-256.\n"
        "2. Review XML keys against the exact LMC 8.4 build.\n"
        "3. Make parameter changes only with a documented hypothesis and change log.\n"
        "4. Capture repeatable baseline/candidate pairs under matched lighting, exposure, lens and focus.\n"
        "5. Evaluate detail, noise, color, exposure and artifacts.\n"
        "6. Roll back if any critical metric regresses.\n\n"
        "This starter contains no tuning changes and proves no image-quality improvement.\n", encoding="utf-8")
    return {"status": "CREATED_BASELINE_COPY_ONLY", **manifest}

def inventory_and_audit(root: Path):
    files = list(walk_files(root))
    by_hash, suffix_counts = collections.defaultdict(list), collections.Counter()
    py_info, xml_info = {}, {}
    image_records, file_records = [], []
    total_bytes = 0
    for p in files:
        try: st = p.stat(); size = st.st_size; digest = sha256(p); total_bytes += size
        except OSError: continue
        rp = rel(p, root); ext = p.suffix.lower() or "[no extension]"
        suffix_counts[ext] += 1
        by_hash[digest].append({"path": rp, "size_bytes": size, "extension": ext})
        file_records.append({"path": rp, "size_bytes": size, "sha256": digest, "extension": ext})
        if ext == ".py": py_info[rp] = python_audit(p)
        elif ext == ".xml": xml_info[rp] = xml_audit(p)
        if ext in IMAGE_EXTS:
            image_records.append({"path": rp, "size_bytes": size, "sha256": digest, "generated_cleanup_candidate": is_generated_image(p, root)})
    duplicates = []
    for digest, group in by_hash.items():
        if len(group) > 1:
            duplicates.append({"sha256": digest, "size_bytes_each": group[0]["size_bytes"], "files": [x["path"] for x in group]})
    xml_dupes = [g for g in duplicates if all(Path(x).suffix.lower() == ".xml" for x in g["files"])]
    doc_exts = {".md", ".txt", ".rst"}
    docs = [p for p in files if p.suffix.lower() in doc_exts]
    module_paths = collections.defaultdict(list)
    for rp in py_info:
        if Path(rp).name != "__init__.py": module_paths[Path(rp).stem].append(rp)
    dep_map, external_counts = {}, collections.Counter()
    standard_common = {"os","sys","re","json","math","time","datetime","pathlib","typing","collections","subprocess","shutil","hashlib","argparse","tempfile","ast","glob","csv","logging","statistics","itertools","functools","threading","urllib","xml","unittest","pytest","PIL","cv2","numpy","matplotlib","requests","sqlite3","platform","copy","io","enum","dataclasses","traceback","textwrap","configparser","zipfile","tarfile","multiprocessing","concurrent","abc","importlib","inspect","contextlib","errno","fnmatch","random","string","struct","base64","binascii","socket","http","email","html","pickle","queue","signal","shlex","smtplib","ssl","tempfile","venv","site","builtins","typing_extensions"}
    for rp, info in py_info.items():
        local = []
        for im in info["imports"]:
            m = im["module"]
            if m in module_paths and m != Path(rp).stem:
                local.extend({"module": m, "path": x, "line": im["line"]} for x in module_paths[m])
            elif m not in standard_common: external_counts[m] += 1
        dep_map[rp] = {"local_dependencies": local, "main_guard": info["main_guard"], "file_operations_to_review": info["file_operations_to_review"]}
    known_names = {p.name for p in files}; doc_refs = []
    for p in docs:
        try: text = p.read_text(encoding="utf-8", errors="replace")
        except OSError: continue
        refs = sorted(set(re.findall(r"[A-Za-z0-9_.-]+\.(?:xml|py)", text, re.I)))
        if refs:
            doc_refs.append({"document": rel(p, root), "referenced_files": refs, "missing_by_basename": [x for x in refs if x not in known_names]})
    candidates = [rp for rp in py_info if re.search(r"(^|/)(main|run|.*workflow.*|.*master.*|.*pipeline.*|lxx521.*audit)\.py$", rp, re.I)]
    return {
        "files": files, "records": file_records,
        "file_count": len(files), "total_bytes": total_bytes, "suffix_counts": dict(sorted(suffix_counts.items())),
        "python": py_info, "xml": xml_info, "duplicates": duplicates, "xml_duplicates": xml_dupes,
        "dependencies": dep_map, "external_import_counts_not_proven_missing": dict(external_counts.most_common()),
        "entry_candidates_not_authoritative": candidates, "docs": docs, "doc_refs": doc_refs, "images": image_records,
        "python_pass": sum(x["ok"] for x in py_info.values()), "python_fail": sum(not x["ok"] for x in py_info.values()),
        "xml_pass": sum(x["ok"] for x in xml_info.values()), "xml_fail": sum(not x["ok"] for x in xml_info.values()),
    }

def write_reports(root: Path, run_dir: Path, data: dict, v10_result: dict, cleanup_preview: list[dict]):
    image_bytes = sum(x["size_bytes"] for x in data["images"])
    generated_images = [x for x in data["images"] if x["generated_cleanup_candidate"]]
    candidate_bytes = sum(x["size_bytes"] for x in generated_images)
    selected_cleanup_bytes = sum(x["size_bytes"] for x in cleanup_preview)
    all_dupes = data["duplicates"]
    summary = {
        "tool": "dcim_v10_allinone.sh", "version": VERSION,
        "created_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "project_root": str(root), "run_dir": str(run_dir),
        "counts": {"files": data["file_count"], "python": len(data["python"]), "xml": len(data["xml"]), "documents": len(data["docs"]), "python_parse_passed": data["python_pass"], "python_parse_failed": data["python_fail"], "xml_parse_passed": data["xml_pass"], "xml_parse_failed": data["xml_fail"], "exact_duplicate_groups_all_files": len(all_dupes), "exact_duplicate_xml_groups": len(data["xml_duplicates"]), "image_files": len(data["images"]), "image_bytes": image_bytes, "generated_image_cleanup_candidates": sum(x["generated_cleanup_candidate"] for x in data["images"]), "selected_cleanup_files": len(cleanup_preview), "selected_cleanup_bytes": sum(x["size_bytes"] for x in cleanup_preview)},
        "file_inventory": data["records"], "suffix_counts": data["suffix_counts"], "workflow_entry_point_candidates_not_authoritative": data["entry_candidates_not_authoritative"],
        "exact_duplicate_groups": all_dupes, "exact_duplicate_xml_groups": data["xml_duplicates"],
        "python_syntax": data["python"], "xml_validation": data["xml"], "dependency_map": data["dependencies"],
        "external_import_counts_not_proven_missing": data["external_import_counts_not_proven_missing"], "documentation_references": data["doc_refs"],
        "image_inventory": data["images"], "v10_candidate_creation": v10_result,
        "cleanup_preview": cleanup_preview,
        "limitations": ["Static audit only; project scripts were not imported or executed.", "XML well-formedness does not prove LMC 8.4/device compatibility.", "V10 file is an exact baseline copy with no parameter changes; not a verified release.", "Generated-image directory/name heuristics are conservative, not proof that every candidate is disposable.", "No SD card path outside --root is scanned or changed."]
    }
    (run_dir / "audit_report.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest_lines = []
    for p in data["files"]:
        try: manifest_lines.append(f"{sha256(p)}  {rel(p, root)}")
        except OSError: pass
    (run_dir / "SHA256SUMS.txt").write_text("\n".join(manifest_lines) + ("\n" if manifest_lines else ""), encoding="utf-8")
    lines = [
        "DCIM CALIBRATION — LXX521 / IMX682", f"Tool: {VERSION}", f"Created: {summary['created_at']}", f"Root: {root}", "",
        "SUMMARY", f"  Files: {data['file_count']}", f"  Python scripts: {len(data['python'])} (syntax passed {data['python_pass']}, failed {data['python_fail']})",
        f"  XML files: {len(data['xml'])} (parsed {data['xml_pass']}, failed {data['xml_fail']})", f"  Documents: {len(data['docs'])}",
        f"  Exact duplicate groups: {len(all_dupes)} (XML-only: {len(data['xml_duplicates'])})", f"  Image files: {len(data['images'])} ({image_bytes / (1024**2):.2f} MiB total)",
        f"  Generated-output image candidates: {len(generated_images)} ({candidate_bytes / (1024**2):.2f} MiB; heuristic, review before deletion)",
        f"  Selected cleanup set for this run: {len(cleanup_preview)} ({selected_cleanup_bytes / (1024**2):.2f} MiB; nothing deleted unless confirmed)", "",
        "V10 CANDIDATE", f"  Status: {v10_result.get('status')}", f"  Source: {v10_result.get('source_profile', v10_result.get('reason', 'not available'))}",
        "  Important: candidate is copied unchanged; no tuning values were invented or changed.", "",
        "WORKFLOW ENTRY-POINT CANDIDATES (not authoritative)", *[f"  - {x}" for x in data["entry_candidates_not_authoritative"]], "",
        "LARGEST IMAGE FILES (top 30; inventory only)"]
    top_images = sorted(data["images"], key=lambda x: x["size_bytes"], reverse=True)[:30]
    lines.extend(f"  {x['size_bytes'] / (1024**2):8.2f} MiB | {'CLEANUP-CANDIDATE' if x['generated_cleanup_candidate'] else 'KEEP/REVIEW'} | {x['path']}" for x in top_images)
    lines += ["", "EXACT DUPLICATE XML GROUPS"]
    for group in data["xml_duplicates"][:60]:
        lines.append(f"  SHA256 {group['sha256']}")
        lines.extend(f"    - {p}" for p in group["files"])
    lines += ["", "SAFETY", "  Default run never deletes files.", "  Cleanup can only target files beneath project root; no full SD card scan.", "  Source images, datasets, reference captures and backups are excluded from generated cleanup.", "  XML parse success does not establish camera compatibility or image-quality improvement."]
    (run_dir / "audit_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

def delete_images(root: Path, targets: list[dict], all_images: bool):
    label = "DELETE ALL IMAGE FILES UNDER PROJECT ROOT" if all_images else "DELETE GENERATED OUTPUT IMAGES"
    expected = "DELETE ALL PROJECT IMAGES" if all_images else "DELETE GENERATED IMAGES"
    print(f"\nDESTRUCTIVE CLEANUP: {label}")
    print(f"Files scheduled: {len(targets)}")
    print(f"Estimated reclaimable space: {sum(x['size_bytes'] for x in targets)/(1024**2):.2f} MiB")
    for item in sorted(targets, key=lambda x: x["size_bytes"], reverse=True)[:80]: print(f"  {item['size_bytes']/(1024**2):8.2f} MiB  {item['path']}")
    if len(targets) > 80: print(f"  ... plus {len(targets)-80} more files (full list in JSON report)")
    if not targets: print("No matching image files found; nothing deleted."); return {"deleted": 0, "bytes_reclaimed_estimate": 0}
    print(f"\nOnly files inside this project root are eligible: {root}")
    try:
        with open("/dev/tty", "r+", encoding="utf-8", errors="replace") as tty:
            tty.write(f"To continue, type exactly: {expected}\n> "); tty.flush()
            typed = tty.readline().strip()
    except OSError:
        print("No interactive terminal available; safe abort. Run this command directly in an interactive Termux session.")
        return {"deleted": 0, "bytes_reclaimed_estimate": 0, "cancelled": True}
    if typed != expected: print("Confirmation did not match; no files deleted."); return {"deleted": 0, "bytes_reclaimed_estimate": 0, "cancelled": True}
    deleted, errors, total = 0, [], 0
    root_real = root.resolve()
    for item in targets:
        p = root / item["path"]
        try:
            if p.is_symlink() or not is_inside(p, root_real) or not p.is_file():
                errors.append({"path": item["path"], "error": "Skipped unsafe path, symlink, or non-file"}); continue
            if sha256(p) != item["sha256"]:
                errors.append({"path": item["path"], "error": "Skipped: file changed after inventory"}); continue
            size = p.stat().st_size
            p.unlink(); deleted += 1; total += size
        except Exception as e: errors.append({"path": item["path"], "error": f"{type(e).__name__}: {e}"})
    return {"deleted": deleted, "bytes_reclaimed_estimate": total, "errors": errors}

def main():
    ap = argparse.ArgumentParser(description="DCIM Calibration audit + V10 baseline starter + safe image cleanup.")
    ap.add_argument("--root", default=os.environ.get("DCIM_SCRIPT_DIR", os.getcwd()), help="Project root; defaults to the folder containing this script")
    ap.add_argument("--no-v10", action="store_true", help="Run audit only; do not create a V10 candidate copy")
    ap.add_argument("--cleanup-generated-images", action="store_true", help="Preview/delete generated-output images under project root")
    ap.add_argument("--delete-all-project-images", action="store_true", help="Dangerous: schedules every supported image file under project root for deletion")
    ap.add_argument("--confirm-cleanup", action="store_true", help="Continue to interactive typed confirmation for image deletion")
    args = ap.parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir(): print(f"ERROR: project root does not exist: {root}", file=sys.stderr); return 2
    if args.cleanup_generated_images and args.delete_all_project_images: print("ERROR: choose only one cleanup mode.", file=sys.stderr); return 2
    if args.confirm_cleanup and not (args.cleanup_generated_images or args.delete_all_project_images): print("ERROR: --confirm-cleanup requires a cleanup mode.", file=sys.stderr); return 2
    if args.confirm_cleanup and not ((root / "analysis_results").is_dir() and ((root / "profiles").is_dir() or (root / "V10_Termux_Master.py").is_file() or (root / "workflow_master.py").is_file())):
        print("ERROR: refusing destructive cleanup because --root does not look like the DCIM project root.", file=sys.stderr); return 2
    stamp = now_stamp()
    run_dir = root / "analysis_results" / "dcim_master" / f"run_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    print("DCIM CALIBRATION — LXX521 / IMX682")
    print(f"All-in-one tool: {VERSION}\nProject root: {root}\nRun directory: {run_dir}")
    print("Scanning project files (read-only; excluding this tool's generated report/workbench)...")
    data = inventory_and_audit(root)
    candidate = {"status": "SKIPPED_BY_USER"} if args.no_v10 else write_candidate(root, run_dir)
    image_targets = []
    if args.delete_all_project_images:
        image_targets = [x for x in data["images"]]
    elif args.cleanup_generated_images:
        image_targets = [x for x in data["images"] if x["generated_cleanup_candidate"]]
    # Produce report before cleanup so preview and initial inventory are preserved.
    write_reports(root, run_dir, data, candidate, image_targets)
    print("\nAUDIT SUMMARY")
    print(f"  Files: {data['file_count']} | Python: {len(data['python'])} ({data['python_pass']} pass / {data['python_fail']} fail)")
    print(f"  XML: {len(data['xml'])} ({data['xml_pass']} pass / {data['xml_fail']} fail) | exact duplicate groups: {len(data['duplicates'])} (XML: {len(data['xml_duplicates'])})")
    print(f"  Images inventoried: {len(data['images'])} | generated cleanup candidates: {sum(x['generated_cleanup_candidate'] for x in data['images'])}")
    print(f"\nV10 starter: {candidate.get('status')}")
    if candidate.get("candidate_profile"): print(f"  Candidate: {candidate['candidate_profile']}\n  Source: {candidate['source_profile']}\n  No tuning values changed.")
    print(f"\nReports:\n  {run_dir / 'audit_report.txt'}\n  {run_dir / 'audit_report.json'}\n  {run_dir / 'SHA256SUMS.txt'}")
    if args.cleanup_generated_images or args.delete_all_project_images:
        if not args.confirm_cleanup:
            total = sum(x["size_bytes"] for x in image_targets)
            print("\nCLEANUP PREVIEW ONLY — nothing was deleted.")
            print(f"  Matched files: {len(image_targets)} | estimated space: {total/(1024**2):.2f} MiB")
            print("  Review the JSON report, then rerun with --confirm-cleanup to delete the listed files.")
        else:
            result = delete_images(root, image_targets, args.delete_all_project_images)
            (run_dir / "cleanup_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(f"\nCleanup result: deleted {result.get('deleted', 0)} files; estimated reclaimed {result.get('bytes_reclaimed_estimate', 0)/(1024**2):.2f} MiB")
            if result.get("errors"): print(f"Skipped/errors: {len(result['errors'])}; see cleanup_result.json")
    print("\nSAFE DEFAULT: source XML values were not tuned, and no files were deleted unless explicitly confirmed.")
    return 0 if not data["python_fail"] and not data["xml_fail"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY
