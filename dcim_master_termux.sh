#!/data/data/com.termux/files/usr/bin/bash
# DCIM Calibration — LXX521 / IMX682
# Read-only source audit by default. No source/profile is modified or deleted.
set -Eeuo pipefail
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
export DCIM_SCRIPT_DIR="$SCRIPT_DIR"
exec python - "$@" <<'PY'
import argparse, ast, collections, datetime, hashlib, json, os, re, shutil, sys, tempfile, traceback
from pathlib import Path
import xml.etree.ElementTree as ET

VERSION = "1.0.0"
EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path, root):
    try: return str(path.relative_to(root))
    except ValueError: return str(path)


def walk_files(root):
    result = []
    for base, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE_DIRS and not (Path(base).name == "analysis_results" and d.startswith("audit_")))
        for name in sorted(names):
            p = Path(base) / name
            if p.is_file(): result.append(p)
    return sorted(result)


def parse_python(path):
    try:
        text = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(text, filename=str(path))
        imports, local_refs, risky = [], set(), []
        has_main_guard = False
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                imports.extend((a.name.split('.')[0], n.lineno) for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                imports.append((n.module.split('.')[0], n.lineno))
            elif isinstance(n, ast.If):
                # Recognize the usual direct execution guard without importing code.
                try:
                    s = ast.unparse(n.test)
                    if "__name__" in s and "__main__" in s: has_main_guard = True
                except Exception: pass
            elif isinstance(n, ast.Call):
                name = ""
                if isinstance(n.func, ast.Name): name = n.func.id
                elif isinstance(n.func, ast.Attribute): name = n.func.attr
                if name in {"remove", "unlink", "rmtree", "rename", "replace", "move", "write_text", "write_bytes", "write", "copy", "copy2", "copyfile", "move"}:
                    risky.append({"line": getattr(n, "lineno", None), "call": name})
        return {"ok": True, "imports": imports, "has_main_guard": has_main_guard,
                "file_operations_to_review": risky, "error": None}
    except SyntaxError as e:
        return {"ok": False, "imports": [], "has_main_guard": False,
                "file_operations_to_review": [],
                "error": f"SyntaxError line {e.lineno}: {e.msg}"}
    except Exception as e:
        return {"ok": False, "imports": [], "has_main_guard": False,
                "file_operations_to_review": [], "error": f"{type(e).__name__}: {e}"}


def parse_xml(path):
    try:
        root = ET.parse(path).getroot()
        tags = collections.Counter(el.tag.split('}')[-1] for el in root.iter())
        attrs = dict(list(root.attrib.items())[:30])
        return {"ok": True, "root_tag": root.tag.split('}')[-1], "root_attributes": attrs,
                "element_count": sum(tags.values()), "top_tags": tags.most_common(12), "error": None}
    except Exception as e:
        return {"ok": False, "root_tag": None, "root_attributes": {},
                "element_count": 0, "top_tags": [], "error": f"{type(e).__name__}: {e}"}


def purpose_hint(name):
    n = name.lower()
    terms = [("frontcam", "Front-camera profile (filename-based hint)"),
             ("portrait", "Portrait-oriented profile (filename-based hint)"),
             ("night", "Night/low-light profile (filename-based hint)"),
             ("indoor", "Indoor profile (filename-based hint)"),
             ("video", "Video-oriented profile (filename-based hint)"),
             ("hdr", "HDR test/profile (filename-based hint)"),
             ("fastshutter", "Fast-shutter profile (filename-based hint)"),
             ("actioncam", "Action/motion profile (filename-based hint)"),
             ("allrounder", "General-purpose profile (filename-based hint)"),
             ("allinone", "All-in-one profile (filename-based hint)"),
             ("maxquality", "Quality-oriented profile (filename-based hint)"),
             ("bsg", "BSG-named profile; exact purpose needs documentation"),
             ("noise", "Noise-related file/profile (filename-based hint)"),
             ("master", "Master/baseline candidate (filename-based hint)")]
    for term, hint in terms:
        if term in n: return hint
    return "Purpose not inferred; inspect XML and documentation"


def deploy_profile(source, destination, root, confirmed):
    if not confirmed:
        raise RuntimeError("Deployment refused: add --confirm-deploy to explicitly authorize deployment.")
    source = source.resolve(); destination = destination.expanduser().resolve()
    if not source.is_file(): raise RuntimeError(f"Source profile not found: {source}")
    if source.suffix.lower() != ".xml": raise RuntimeError("Only .xml profiles can be deployed by this command.")
    try: ET.parse(source)
    except Exception as e: raise RuntimeError(f"Source XML is invalid; deployment cancelled: {e}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_hash = sha256(source)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = None
    if destination.exists():
        if not destination.is_file(): raise RuntimeError("Destination exists but is not a regular file.")
        backup = destination.with_name(destination.name + f".bak.{stamp}")
        shutil.copy2(destination, backup)
        if sha256(backup) != sha256(destination): raise RuntimeError("Backup hash verification failed; deployment cancelled.")
    temp_name = None
    try:
        fd, temp_name = tempfile.mkstemp(prefix=".dcim_tmp_", suffix=".xml", dir=str(destination.parent))
        with os.fdopen(fd, "wb") as out, open(source, "rb") as inp:
            shutil.copyfileobj(inp, out)
            out.flush(); os.fsync(out.fileno())
        if sha256(Path(temp_name)) != source_hash: raise RuntimeError("Temporary copy hash mismatch.")
        ET.parse(temp_name)
        os.replace(temp_name, destination); temp_name = None
        if sha256(destination) != source_hash:
            if backup and backup.exists(): shutil.copy2(backup, destination)
            raise RuntimeError("Destination hash mismatch; attempted restoration from backup.")
    finally:
        if temp_name and os.path.exists(temp_name): os.unlink(temp_name)
    return {"source": str(source), "destination": str(destination), "sha256": source_hash,
            "backup": str(backup) if backup else None, "status": "DEPLOYED (hash verified)"}


def main():
    ap = argparse.ArgumentParser(description="DCIM Calibration safe Termux master audit (read-only by default).")
    ap.add_argument("--root", default=os.environ.get("DCIM_SCRIPT_DIR", os.getcwd()), help="Project directory; default: directory containing this script")
    ap.add_argument("--out", help="Report output directory; default: ROOT/analysis_results/audit_TIMESTAMP")
    ap.add_argument("--deploy-source", help="Optional XML profile path to deploy (requires --destination and --confirm-deploy)")
    ap.add_argument("--destination", help="Exact destination file for optional XML deployment")
    ap.add_argument("--confirm-deploy", action="store_true", help="Explicitly authorize the optional file deployment")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir(): print(f"ERROR: project root does not exist: {root}", file=sys.stderr); return 2
    if bool(args.deploy_source) != bool(args.destination):
        print("ERROR: --deploy-source and --destination must be used together.", file=sys.stderr); return 2
    if args.confirm_deploy and not args.deploy_source:
        print("ERROR: --confirm-deploy only applies with --deploy-source and --destination.", file=sys.stderr); return 2

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(args.out).expanduser().resolve() if args.out else root / "analysis_results" / f"audit_{stamp}"
    # Avoid scanning reports that this run is writing.
    out.mkdir(parents=True, exist_ok=True)
    files = [p for p in walk_files(root) if out not in p.parents]
    records, hash_groups = [], collections.defaultdict(list)
    py_results, xml_results = {}, {}
    suffix_counts = collections.Counter()
    for p in files:
        rp = rel(p, root); ext = p.suffix.lower() or "[no extension]"
        suffix_counts[ext] += 1
        try: digest = sha256(p); size = p.stat().st_size
        except Exception as e: digest = None; size = None
        records.append({"path": rp, "size_bytes": size, "sha256": digest, "extension": ext})
        if digest: hash_groups[digest].append(rp)
        if ext == ".py": py_results[rp] = parse_python(p)
        elif ext == ".xml": xml_results[rp] = parse_xml(p)

    xml_dupes = [{"sha256": h, "files": names} for h, names in hash_groups.items()
                 if len(names) > 1 and all(Path(x).suffix.lower() == ".xml" for x in names)]
    all_dupes = [{"sha256": h, "files": names} for h, names in hash_groups.items() if len(names) > 1]

    # Map imports to files shipped in this project; do not import/execute project scripts.
    module_to_paths = collections.defaultdict(list)
    for rp in py_results:
        if Path(rp).name != "__init__.py": module_to_paths[Path(rp).stem].append(rp)
    dependency_map, unresolved_external = {}, collections.Counter()
    for rp, info in py_results.items():
        local = []
        for mod, lineno in info["imports"]:
            if mod in module_to_paths and mod != Path(rp).stem:
                local.extend({"module": mod, "file": x, "line": lineno} for x in module_to_paths[mod])
            elif mod not in {"__future__"}:
                unresolved_external[mod] += 1
        dependency_map[rp] = {"local_dependencies": local, "main_guard": info["has_main_guard"],
                              "file_operations_to_review": info["file_operations_to_review"]}

    docs = [p for p in files if p.suffix.lower() in {".md", ".txt", ".rst"}]
    doc_refs = []
    known_names = {p.name for p in files}
    for p in docs:
        try: text = p.read_text(encoding="utf-8", errors="replace")
        except Exception: continue
        refs = sorted(set(re.findall(r"[A-Za-z0-9_.-]+\.(?:xml|py)", text, re.I)))
        missing = [r for r in refs if r not in known_names]
        if refs: doc_refs.append({"document": rel(p, root), "referenced_files": refs, "missing_by_basename": missing})

    entry_candidates = [rp for rp in py_results if re.search(r"(^|/)(main|run|.*workflow.*|.*master.*|.*pipeline.*|lxx521.*audit)\.py$", rp, re.I)]
    xml_profiles = [{"path": rp, "purpose_hint": purpose_hint(Path(rp).name), **info}
                    for rp, info in xml_results.items()]
    deploy_result = None
    if args.deploy_source:
        src = Path(args.deploy_source)
        if not src.is_absolute(): src = root / src
        try:
            deploy_result = deploy_profile(src, Path(args.destination), root, args.confirm_deploy)
        except Exception as e:
            deploy_result = {"status": "FAILED/REFUSED", "error": str(e)}

    summary = {
        "tool": "dcim_master_termux.sh", "version": VERSION,
        "created_local": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "project_root": str(root), "report_dir": str(out),
        "counts": {"all_files": len(records), "python": len(py_results), "xml": len(xml_results),
                   "documents": len(docs), "by_extension": dict(sorted(suffix_counts.items()))},
        "python_syntax": {"passed": sum(1 for x in py_results.values() if x["ok"]),
                           "failed": sum(1 for x in py_results.values() if not x["ok"]),
                           "details": py_results},
        "xml_validation": {"passed": sum(1 for x in xml_results.values() if x["ok"]),
                           "failed": sum(1 for x in xml_results.values() if not x["ok"]),
                           "details": xml_results},
        "exact_duplicate_groups_all_files": all_dupes,
        "exact_duplicate_xml_groups": xml_dupes,
        "script_dependency_map": dependency_map,
        "unresolved_or_external_import_counts_not_proven_missing": dict(unresolved_external.most_common()),
        "workflow_entry_point_candidates_not_authoritative": entry_candidates,
        "xml_profiles_filename_based_purpose_hints": xml_profiles,
        "documentation_file_references": doc_refs,
        "deployment": deploy_result,
        "limitations": ["Static audit only: project scripts were not imported or executed.",
                        "XML well-formedness does not prove compatibility with LMC 8.4 or this device.",
                        "Filename-based profile purpose is only a hint, not verified behaviour.",
                        "No camera image-quality claim is made by this audit.",
                        "External imports may be standard-library or optional dependencies; counts are not proof of missing packages."]
    }

    (out / "audit_report.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (out / "SHA256SUMS.txt").open("w", encoding="utf-8") as f:
        for r in records:
            if r["sha256"]: f.write(f"{r['sha256']}  {r['path']}\n")
    lines = ["DCIM CALIBRATION — LXX521 / IMX682", f"Audit tool: {VERSION}",
             f"Created: {summary['created_local']}", f"Project root: {root}", "",
             "FILE SUMMARY", f"  All files: {len(records)}", f"  Python scripts: {len(py_results)}",
             f"  XML files: {len(xml_results)}", f"  Documentation files: {len(docs)}", "",
             "VALIDATION", f"  Python parse: {summary['python_syntax']['passed']} passed; {summary['python_syntax']['failed']} failed",
             f"  XML parse: {summary['xml_validation']['passed']} passed; {summary['xml_validation']['failed']} failed",
             f"  Exact duplicate XML groups: {len(xml_dupes)}", f"  Exact duplicate groups across all files: {len(all_dupes)}", "",
             "WORKFLOW ENTRY-POINT CANDIDATES (not authoritative)"]
    lines += [f"  - {x}" for x in entry_candidates] or ["  - None detected"]
    lines += ["", "PYTHON SYNTAX ERRORS"]
    errors = [(p, d["error"]) for p, d in py_results.items() if not d["ok"]]
    lines += [f"  - {p}: {e}" for p, e in errors] or ["  None"]
    lines += ["", "XML PARSE ERRORS"]
    errors = [(p, d["error"]) for p, d in xml_results.items() if not d["ok"]]
    lines += [f"  - {p}: {e}" for p, e in errors] or ["  None"]
    lines += ["", "EXACT DUPLICATE XML GROUPS"]
    for group in xml_dupes:
        lines.append(f"  SHA256 {group['sha256']}")
        lines.extend(f"    - {p}" for p in group["files"])
    if not xml_dupes: lines.append("  None")
    lines += ["", "PYTHON FILE OPERATIONS TO REVIEW (static hints; not necessarily unsafe)"]
    any_ops = False
    for p, d in py_results.items():
        for op in d["file_operations_to_review"]:
            any_ops = True; lines.append(f"  - {p}:{op['line']}: {op['call']}()")
    if not any_ops: lines.append("  None detected")
    lines += ["", "PROFILE PURPOSE HINTS (filename only; verify documentation/device compatibility)"]
    lines.extend(f"  - {p}: {purpose_hint(Path(p).name)}" for p in xml_results)
    lines += ["", "LIMITATIONS", "  - This is a static audit; project scripts were not executed.",
              "  - Valid XML is not proof of LMC 8.4/device compatibility.",
              "  - No profile was declared best and no image-quality gain was inferred.",
              "  - Source files were not edited or deleted by the audit.", "", f"Detailed JSON: {out / 'audit_report.json'}",
              f"Hash manifest: {out / 'SHA256SUMS.txt'}"]
    (out / "audit_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:20]))
    print("\nReports saved:")
    print(f"  {out / 'audit_report.txt'}")
    print(f"  {out / 'audit_report.json'}")
    print(f"  {out / 'SHA256SUMS.txt'}")
    print("\nSAFE DEFAULT: no source/profile was modified or deleted.")
    if deploy_result:
        print("DEPLOYMENT:", json.dumps(deploy_result, ensure_ascii=False))
        if deploy_result.get("status") == "FAILED/REFUSED": return 3
    return 1 if summary["python_syntax"]["failed"] or summary["xml_validation"]["failed"] else 0

if __name__ == "__main__":
    try: sys.exit(main())
    except KeyboardInterrupt: print("\nCancelled by user.", file=sys.stderr); sys.exit(130)
    except Exception as e: print(f"FATAL: {type(e).__name__}: {e}", file=sys.stderr); sys.exit(2)
PY
