#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only static audit for DCIM Calibration projects on Termux/Android."""

import argparse
import ast
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0"
SOURCE_EXTS = {
    ".py", ".pyw", ".xml", ".md", ".markdown", ".sh", ".bash",
    ".json", ".csv", ".ini", ".cfg", ".toml", ".yaml", ".yml",
    ".txt", ".log", ".properties",
}
MEDIA_EXTS = {
    ".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp",
    ".tif", ".tiff", ".bmp", ".dng", ".raw",
    ".mp4", ".mov", ".mkv", ".avi", ".webm",
}
SKIP_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv",
    "__pycache__", ".pytest_cache", ".mypy_cache",
}
INTERESTING_CALLS = {
    "calibrateCamera", "calibrateCameraExtended",
    "findChessboardCorners", "findChessboardCornersSB",
    "cornerSubPix", "projectPoints", "imread", "imwrite",
    "imreadmulti", "glob", "walk", "rglob", "savefig",
    "VideoCapture", "solvePnP", "stereoCalibrate",
    "findContours", "cvtColor",
}


def relative_path(path, root):
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def walk_files(root, report_dir):
    """Walk without following symlinked directories or scanning report output."""
    report_dir = report_dir.resolve()

    for current, dirs, filenames in os.walk(root, followlinks=False):
        base = Path(current)
        kept = []

        for dirname in dirs:
            candidate = base / dirname
            try:
                resolved = candidate.resolve()
                if dirname in SKIP_DIRS or candidate.is_symlink():
                    continue
                if resolved == report_dir or report_dir in resolved.parents:
                    continue
                kept.append(dirname)
            except OSError:
                continue

        dirs[:] = kept

        for filename in filenames:
            candidate = base / filename
            try:
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                resolved = candidate.resolve()
                if resolved == report_dir or report_dir in resolved.parents:
                    continue
                yield candidate
            except OSError:
                continue


def audit_python(path, root):
    result = {
        "path": relative_path(path, root),
        "lines": None,
        "syntax": "ERROR",
        "functions": [],
        "classes": [],
        "imports": [],
        "calls": [],
        "main_guard": False,
        "issues": [],
    }

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        result["lines"] = len(source.splitlines())
        tree = ast.parse(source, filename=str(path))
        result["syntax"] = "PASS"
    except SyntaxError as exc:
        result["syntax"] = "FAIL"
        result["issues"].append(
            f"SyntaxError at line {exc.lineno}: {exc.msg}"
        )
        return result
    except Exception as exc:
        result["issues"].append(
            f"{type(exc).__name__}: {exc}"
        )
        return result

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result["functions"].append({
                "name": node.name,
                "line": node.lineno,
            })
        elif isinstance(node, ast.ClassDef):
            result["classes"].append({
                "name": node.name,
                "line": node.lineno,
            })
        elif isinstance(node, ast.Import):
            for alias in node.names:
                result["imports"].append({
                    "module": alias.name,
                    "line": node.lineno,
                })
        elif isinstance(node, ast.ImportFrom):
            result["imports"].append({
                "module": "." * node.level + (node.module or ""),
                "line": node.lineno,
            })

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            try:
                test = ast.unparse(node.test).replace(" ", "")
                if test == "__name__=='__main__'":
                    result["main_guard"] = True
            except Exception:
                pass

        if isinstance(node, ast.Call):
            func = node.func
            name = (
                func.attr if isinstance(func, ast.Attribute)
                else func.id if isinstance(func, ast.Name)
                else ""
            )
            if name in INTERESTING_CALLS:
                result["calls"].append({
                    "name": ast.unparse(func),
                    "line": node.lineno,
                })

    result["functions"].sort(key=lambda x: x["line"])
    result["imports"].sort(key=lambda x: x["line"])
    result["calls"].sort(key=lambda x: x["line"])
    return result


def audit_xml(path, root):
    result = {
        "path": relative_path(path, root),
        "status": "PASS",
        "root": None,
        "elements": 0,
        "attributes": 0,
        "issues": [],
    }

    try:
        element = ET.parse(path).getroot()
        result["root"] = element.tag
        result["elements"] = sum(1 for _ in element.iter())
        result["attributes"] = sum(
            len(item.attrib) for item in element.iter()
        )
    except Exception as exc:
        result["status"] = "FAIL"
        result["issues"].append(
            f"{type(exc).__name__}: {exc}"
        )

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Read-only DCIM calibration source audit"
    )
    parser.add_argument(
        "project", nargs="?", default=".",
        help="Project directory; defaults to current directory",
    )
    parser.add_argument(
        "--report-dir", default="audit_report",
        help="Report directory; defaults to PROJECT/audit_report",
    )
    parser.add_argument(
        "--no-hashes", action="store_true",
        help="Skip SHA-256 hashing and duplicate detection",
    )
    args = parser.parse_args()

    root = Path(args.project).expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: project directory not found: {root}", file=sys.stderr)
        return 2

    report_dir = Path(args.report_dir).expanduser()
    if not report_dir.is_absolute():
        report_dir = root / report_dir
    report_dir = report_dir.resolve()

    files = sorted(
        walk_files(root, report_dir),
        key=lambda item: relative_path(item, root).lower(),
    )

    extension_counts = Counter()
    top_counts = Counter()
    hash_groups = defaultdict(list)
    entries = []
    python_results = []
    xml_results = []
    json_results = []
    markdown_files = []
    unreadable = []
    total_bytes = 0

    for path in files:
        rel = relative_path(path, root)
        extension = path.suffix.lower()

        try:
            size = path.stat().st_size
        except OSError as exc:
            unreadable.append({"path": rel, "error": str(exc)})
            continue

        total_bytes += size
        extension_counts[extension or "(none)"] += 1
        parts = Path(rel).parts
        top = parts[0] if len(parts) > 1 else "(root)"
        top_counts[top] += 1

        entry = {
            "path": rel,
            "extension": extension,
            "bytes": size,
            "sha256": None,
        }

        if not args.no_hashes:
            try:
                entry["sha256"] = sha256_file(path)
                hash_groups[entry["sha256"]].append(rel)
            except OSError as exc:
                unreadable.append({"path": rel, "error": str(exc)})

        entries.append(entry)

        if extension == ".py":
            python_results.append(audit_python(path, root))
        elif extension == ".xml":
            xml_results.append(audit_xml(path, root))
        elif extension == ".json":
            try:
                json.loads(path.read_text(
                    encoding="utf-8", errors="replace"
                ))
                status, issue = "PASS", ""
            except Exception as exc:
                status, issue = "FAIL", f"{type(exc).__name__}: {exc}"

            json_results.append({
                "path": rel,
                "status": status,
                "issue": issue,
            })
        elif extension in {".md", ".markdown"}:
            markdown_files.append(rel)

    duplicates = [
        {
            "sha256": digest,
            "files": sorted(paths),
            "count": len(paths),
        }
        for digest, paths in hash_groups.items()
        if len(paths) > 1
    ]
    duplicates.sort(
        key=lambda item: (-item["count"], item["files"][0].lower())
    )

    python_stems = {Path(item["path"]).stem for item in python_results}
    dependencies = []

    for item in python_results:
        local_imports = []
        other_imports = []

        for imported in item["imports"]:
            module = imported["module"].lstrip(".")
            first = module.split(".")[0] if module else ""
            target = (
                local_imports
                if first in python_stems
                else other_imports
            )
            target.append(imported)

        dependencies.append({
            "script": item["path"],
            "local_imports": local_imports,
            "other_imports": other_imports,
        })

    profile_candidates = [
        item["path"] for item in xml_results
        if any(token in item["path"].lower() for token in (
            "profile", "imx682", "lxx521", "camera",
            "config", "lowlight", "hdr", "video",
        ))
    ]

    python_failures = [
        item for item in python_results
        if item["syntax"] != "PASS"
    ]
    xml_failures = [
        item for item in xml_results
        if item["status"] != "PASS"
    ]
    json_failures = [
        item for item in json_results
        if item["status"] != "PASS"
    ]

    report = {
        "metadata": {
            "tool_version": VERSION,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "project_root": str(root),
            "report_dir": str(report_dir),
            "source_modified": False,
            "project_scripts_executed": False,
            "hashes_enabled": not args.no_hashes,
        },
        "summary": {
            "file_count": len(entries),
            "total_bytes": total_bytes,
            "extensions": dict(extension_counts.most_common()),
            "top_level_paths": dict(top_counts.most_common()),
            "python_count": len(python_results),
            "xml_count": len(xml_results),
            "json_count": len(json_results),
            "markdown_count": len(markdown_files),
            "profile_candidate_count": len(profile_candidates),
            "duplicate_sha256_groups": len(duplicates),
            "python_syntax_failures": len(python_failures),
            "xml_parse_failures": len(xml_failures),
            "json_parse_failures": len(json_failures),
            "unreadable_files": len(unreadable),
        },
        "files": entries,
        "duplicates": duplicates,
        "python": python_results,
        "xml": xml_results,
        "json": json_results,
        "markdown_files": markdown_files,
        "profile_candidates": profile_candidates,
        "dependency_map": dependencies,
        "unreadable_files": unreadable,
        "limitations": [
            "Static audit only; project scripts are not executed or imported.",
            "Python syntax PASS does not prove runtime correctness or calibration accuracy.",
            "XML parsing checks well-formedness, not LMC schema or device compatibility.",
            "Identical hashes do not identify the authoritative profile.",
            "Dependency and profile identification are heuristic; dynamic imports may be missed.",
            "No calibration measurements or image-quality results are generated.",
        ],
    }

    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "audit_report.json"
    markdown_path = report_dir / "audit_report.md"

    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "# DCIM Calibration — Final Static Audit",
        "",
        f"- Project: `{root}`",
        f"- Audit time (UTC): `{report['metadata']['created_utc']}`",
        "- Mode: **read-only static audit**",
        "- Project scripts executed: **No**",
        "- Source files modified: **No**",
        "",
        "## 1. Summary",
        "",
        "| Check | Result |",
        "|---|---:|",
        f"| Files inventoried | {len(entries)} |",
        f"| Python scripts | {len(python_results)} |",
        f"| XML files | {len(xml_results)} |",
        f"| JSON files | {len(json_results)} |",
        f"| Markdown files | {len(markdown_files)} |",
        f"| Candidate profile XMLs | {len(profile_candidates)} |",
        f"| Duplicate SHA-256 groups | {len(duplicates)} |",
        f"| Python syntax failures | {len(python_failures)} |",
        f"| XML parse failures | {len(xml_failures)} |",
        f"| JSON parse failures | {len(json_failures)} |",
        f"| Unreadable files | {len(unreadable)} |",
        "",
        "## 2. File counts by extension",
        "",
        "| Extension | Count |",
        "|---|---:|",
    ]

    for extension, count in extension_counts.most_common():
        lines.append(f"| `{extension}` | {count} |")

    lines += [
        "",
        "## 3. Python syntax and entry points",
        "",
        "| Script | Lines | Syntax | Main guard | Functions |",
        "|---|---:|---|---|---|",
    ]

    for item in python_results:
        functions = ", ".join(
            f"{func['name']} (L{func['line']})"
            for func in item["functions"]
        ) or "—"
        lines.append(
            f"| `{item['path']}` | {item['lines'] or '—'} "
            f"| {item['syntax']} "
            f"| {'Yes' if item['main_guard'] else 'No/unclear'} "
            f"| {functions} |"
        )

    if python_failures:
        lines += ["", "### Python syntax failures", ""]
        for item in python_failures:
            lines.append(
                f"- `{item['path']}`: {'; '.join(item['issues'])}"
            )

    lines += ["", "### Dependency map (heuristic)", ""]

    for item in dependencies:
        local = ", ".join(
            imported["module"] for imported in item["local_imports"]
        ) or "none detected"
        other = ", ".join(
            imported["module"] for imported in item["other_imports"]
        ) or "none detected"
        lines.append(
            f"- **`{item['script']}`** — local-looking imports: {local}; "
            f"other imports: {other}"
        )

    lines += ["", "### Camera/image processing calls", ""]
    found_calls = False

    for item in python_results:
        if item["calls"]:
            found_calls = True
            lines.append(f"- **`{item['path']}`**")
            for call in item["calls"]:
                lines.append(
                    f"  - Line {call['line']}: `{call['name']}`"
                )

    if not found_calls:
        lines.append("No recognized calls found.")

    lines += [
        "",
        "## 4. XML/profile inventory",
        "",
        "| XML path | Status | Root tag | Elements | Attributes |",
        "|---|---|---|---:|---:|",
    ]

    for item in xml_results:
        lines.append(
            f"| `{item['path']}` | {item['status']} "
            f"| `{item['root'] or '—'}` | {item['elements']} "
            f"| {item['attributes']} |"
        )

    if xml_failures:
        lines += ["", "### XML parsing failures", ""]
        for item in xml_failures:
            lines.append(
                f"- `{item['path']}`: {'; '.join(item['issues'])}"
            )

    lines += [
        "",
        "### Candidate profile XMLs",
        "",
        "This is a filename/path heuristic, not proof of active LMC use.",
        "",
    ]
    lines.extend(f"- `{path}`" for path in profile_candidates)

    lines += ["", "## 5. Byte-identical duplicates (SHA-256)", ""]

    if duplicates:
        for item in duplicates:
            lines.append(
                f"- **{item['count']} files** — SHA-256 `{item['sha256']}`"
            )
            lines.extend(f"  - `{path}`" for path in item["files"])
    else:
        lines.append("No duplicate groups found, or hashing was disabled.")

    lines += ["", "## 6. JSON validation", ""]
    for item in json_results:
        suffix = f" — {item['issue']}" if item["issue"] else ""
        lines.append(f"- `{item['path']}`: {item['status']}{suffix}")

    lines += [
        "",
        "## 7. Top-level directory counts",
        "",
        "| Path | Files |",
        "|---|---:|",
    ]
    for name, count in top_counts.most_common():
        lines.append(f"| `{name}` | {count} |")

    lines += [
        "",
        "## 8. Limitations and cautions",
        "",
    ]
    lines.extend(f"- {note}" for note in report["limitations"])

    lines += [
        "",
        "## 9. Recommended validation plan",
        "",
        "1. Back up the project before any future changes.",
        "2. Confirm the active LMC 8.4 import directory and profile selection on-device.",
        "3. Review syntax/XML/JSON failures and duplicate groups manually; do not delete duplicates solely by hash.",
        "4. Document every generator's inputs, outputs, overwrite behavior, and dependencies.",
        "5. Test generators on a copied fixture before importing profiles.",
        "6. Use documented captures with known chart geometry and controlled conditions.",
        "7. Validate checkerboard geometry, reprojection RMS, and image-quality metrics independently.",
        "8. Compare one candidate profile at a time against a preserved baseline.",
        "",
        "## 10. Reports",
        "",
        "- `audit_report.md` — readable report",
        "- `audit_report.json` — detailed inventory and findings",
        "",
    ]

    markdown_path.write_text("\n".join(lines), encoding="utf-8")

    print("DCIM Calibration audit complete")
    print(f"Project: {root}")
    print(
        f"Files: {len(entries)} | Python: {len(python_results)} | "
        f"XML: {len(xml_results)} | JSON: {len(json_results)} | "
        f"Markdown: {len(markdown_files)}"
    )
    print(f"Duplicate SHA-256 groups: {len(duplicates)}")
    print(
        f"Python syntax failures: {len(python_failures)} | "
        f"XML failures: {len(xml_failures)} | "
        f"JSON failures: {len(json_failures)}"
    )
    print("Reports:")
    print(f"  {markdown_path}")
    print(f"  {json_path}")
    print("Safety: project scripts were not executed; source files were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
