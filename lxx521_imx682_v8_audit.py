#!/usr/bin/env python3
"""
LXX521 / Sony IMX682 / LMC 8.4 V8 safe XML auditor.
Read-only by default. Never installs or activates a profile.
Python 3 standard library only.
"""
import argparse, hashlib, json, os, re, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

KNOWN = {
    "original_v2_release_day": {
        "sha256": "2118c905a247a5534dadfb82530638659e7d39c54ea3cf8dd622baf145bebc9a",
        "keys": 2633,
    },
    "default_working_backup": {
        "sha256": "f5dde315f71bb4c28f72ea0b2a5cd3b5385f2e4aeb12b7463416174acb1b5f49",
        "keys": 2641,
    },
}
EXPECTED = [
    "analysis_results/imx682_config/original_V2_Release_Day.xml",
    "analysis_results/imx682_config/allrounder/default_working_backup.xml",
    "analysis_results/imx682_config/LXX521_LMC84_Optimized_Corrected.xml",
    "analysis_results/imx682_config/lowlight_v5/LXX521_IMX682_LowLight_Shot_V5.xml",
    "analysis_results/final_calibration/final_report/IMX682_FINAL_REPORT.md",
    "analysis_results/IMX682_full_audit_report.md",
    "analysis_results/imx682_config/IMX682_full_calibration_report.md",
    "analysis_results/imx682_config/no_cost_tests/ab_comparison/baseline_reconciliation_report.md",
    "analysis_results/imx682_config/no_cost_tests/ab_comparison/ab_report.md",
    "analysis_results/imx682_config/device_tests/ab_test_report.md",
]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_xml(path):
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        return {"path": str(path), "error": f"XML_PARSE_ERROR: {e}"}
    entries, duplicates = {}, []
    child_tags = {}
    for child in list(root):
        child_tags[child.tag] = child_tags.get(child.tag, 0) + 1
        key = child.attrib.get("name")
        if key is None:
            continue
        # Preserve actual representation; don't silently normalize attribute/text schemas.
        value = ("attribute:value=" + child.attrib["value"]) if "value" in child.attrib else ("text:" + (child.text or ""))
        if key in entries:
            duplicates.append(key)
        entries[key] = {"value": value, "tag": child.tag, "attrib": dict(child.attrib)}
    schema = "value-attribute" if any("value" in c.attrib for c in list(root)) else (
        "text-content" if any(c.attrib.get("name") is not None for c in list(root)) else "unknown"
    )
    return {
        "path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256(path),
        "root_tag": root.tag, "direct_children": len(list(root)),
        "named_entries": sum(1 for c in list(root) if "name" in c.attrib),
        "unique_keys": len(entries), "duplicate_keys": sorted(set(duplicates)),
        "schema": schema, "child_tags": child_tags, "entries": entries,
        "parse_ok": True,
    }

def markdown_escape(s):
    return str(s).replace("|", r"\|").replace("\n", " ")

def compare(a, b):
    ka, kb = set(a["entries"]), set(b["entries"])
    changed = []
    for k in sorted(ka & kb):
        if a["entries"][k]["value"] != b["entries"][k]["value"]:
            changed.append((k, a["entries"][k]["value"], b["entries"][k]["value"]))
    return {"missing_in_second": sorted(ka-kb), "extra_in_second": sorted(kb-ka), "changed": changed}

def main():
    ap = argparse.ArgumentParser(description="Safe LXX521 IMX682 LMC XML audit; no device writes.")
    ap.add_argument("--root", default="~/dcim_calibration", help="Project root (default: ~/dcim_calibration)")
    ap.add_argument("--create-candidate-from", help="Optional full XML path relative to root or absolute. Creates an unchanged experimental copy only if known baseline hash/schema checks pass.")
    args = ap.parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: project root not found: {root}", file=sys.stderr); return 2
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = root / "analysis_results" / f"v8_audit_{stamp}"
    # No project writes until root is confirmed; report output is new and timestamped.
    outdir.mkdir(parents=True, exist_ok=False)
    report = {
        "generated_local": datetime.now().astimezone().isoformat(),
        "project_root": str(root), "mode": "audit-only" if not args.create_candidate_from else "audit-plus-explicit-candidate",
        "files": [], "comparisons": [], "warnings": [], "candidate": None
    }
    print(f"Project: {root}\nAudit output: {outdir}\nScanning XML and reports...")
    xmls = sorted(root.rglob("*.xml"))
    # Avoid rescanning previous audit outputs and giant unrelated hidden trees.
    xmls = [x for x in xmls if "v8_audit_" not in str(x) and ".git" not in x.parts]
    parsed = {}
    for path in xmls:
        try:
            r = parse_xml(path)
            parsed[str(path)] = r
            rel = str(path.relative_to(root))
            summary = {k: v for k, v in r.items() if k != "entries"}
            summary["relative_path"] = rel
            report["files"].append(summary)
        except Exception as e:
            report["warnings"].append(f"Failed to inspect {path}: {e}")
    print(f"XML files scanned: {len(xmls)}")
    for rel in EXPECTED:
        f = root / rel
        if not f.exists():
            report["warnings"].append(f"Expected reference missing: {rel}")
    # Known hash verification for two specifically identified files, regardless of filenames elsewhere.
    for path_s, r in parsed.items():
        if not r.get("parse_ok"): continue
        name = Path(path_s).name.lower()
        key = None
        if name == "original_v2_release_day.xml": key = "original_v2_release_day"
        elif name == "default_working_backup.xml": key = "default_working_backup"
        if key:
            expected = KNOWN[key]
            r["known_reference_check"] = {
                "expected_sha256": expected["sha256"], "hash_matches": r["sha256"] == expected["sha256"],
                "expected_unique_keys": expected["keys"], "key_count_matches": r["unique_keys"] == expected["keys"]
            }
            if r["sha256"] != expected["sha256"]:
                report["warnings"].append(f"{name}: SHA-256 differs from supplied historical reference; don't assume same revision.")
            if r["unique_keys"] != expected["keys"]:
                report["warnings"].append(f"{name}: key count differs from supplied historical reference.")
    # Pairwise compare relevant full configs by name and large XMLs.
    fulls = [r for r in parsed.values() if r.get("parse_ok") and r["unique_keys"] >= 1000]
    for i in range(len(fulls)):
        for j in range(i+1, len(fulls)):
            a, b = fulls[i], fulls[j]
            c = compare(a, b)
            report["comparisons"].append({
                "first": str(Path(a["path"]).relative_to(root)),
                "second": str(Path(b["path"]).relative_to(root)),
                "first_keys": a["unique_keys"], "second_keys": b["unique_keys"],
                "first_schema": a["schema"], "second_schema": b["schema"],
                "missing_in_second": c["missing_in_second"],
                "extra_in_second": c["extra_in_second"],
                "changed_count": len(c["changed"]),
                "changed_values": [{"key": k, "first": av, "second": bv} for k,av,bv in c["changed"][:300]],
                "changed_values_truncated": len(c["changed"]) > 300
            })
    # Report text inventory (content isn't presumed true; merely list file metadata).
    report_files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".txt", ".csv"} and "v8_audit_" not in str(path) and ".git" not in path.parts:
            try:
                report_files.append({"path": str(path.relative_to(root)), "size_bytes": path.stat().st_size, "sha256": sha256(path)})
            except OSError: pass
    report["reports_and_data_inventory"] = report_files
    # Candidate is opt-in and only permitted from a file matching a known verified 2640-key backup hash.
    if args.create_candidate_from:
        source = Path(args.create_candidate_from).expanduser()
        if not source.is_absolute(): source = (root / source).resolve()
        source = source.resolve()
        sr = parsed.get(str(source))
        if sr is None:
            try: sr = parse_xml(source)
            except Exception: sr = None
        if not sr or not sr.get("parse_ok"):
            report["candidate"] = {"created": False, "reason": "Source XML could not be parsed."}
        elif sr["sha256"] != KNOWN["default_working_backup"]["sha256"] or sr["unique_keys"] != KNOWN["default_working_backup"]["keys"] or sr["schema"] != "text-content":
            report["candidate"] = {
                "created": False,
                "reason": "Safety gate blocked candidate: source must match the known 2641-key default_working_backup SHA-256 and text-content schema.",
                "source": str(source), "sha256": sr["sha256"], "keys": sr["unique_keys"], "schema": sr["schema"]
            }
        else:
            target = outdir / "LXX521_IMX682_V8_EvidenceBased_AllInOne.xml"
            if target.exists():
                report["candidate"] = {"created": False, "reason": "Target already exists; refusing overwrite."}
            else:
                # Copy exact bytes: no tuning claims and no schema conversion.
                tmp = outdir / (target.name + ".tmp")
                shutil.copyfile(source, tmp)
                with open(tmp, "rb") as f: os.fsync(f.fileno())
                check = parse_xml(tmp)
                if not check.get("parse_ok") or check["sha256"] != sr["sha256"] or check["unique_keys"] != KNOWN["default_working_backup"]["keys"] or check["schema"] != "text-content":
                    tmp.unlink(missing_ok=True)
                    report["candidate"] = {"created": False, "reason": "Post-copy validation failed; temporary file removed."}
                else:
                    os.replace(tmp, target)
                    report["candidate"] = {
                        "created": True, "path": str(target.relative_to(root)), "sha256": check["sha256"],
                        "size_bytes": check["size_bytes"], "unique_keys": check["unique_keys"],
                        "changes": [], "note": "Exact unchanged copy of verified historical baseline; experimental baseline candidate, not an optimized/tuned V8. Do not import until device compatibility and A/B testing are approved."
                    }
    # Create human-readable audit report.
    md = [
        "# LXX521 IMX682 LMC 8.4 — V8 Audit Report", "",
        f"- Generated: {report['generated_local']}",
        f"- Project root: `{root}`",
        f"- XML files scanned: {len(xmls)}",
        "- Device deployment/import: **NOT performed**",
        "- Existing source files modified: **No** (only new timestamped report directory/candidate, if explicitly requested)",
        "", "## XML inventory", "",
        "| File | Bytes | SHA-256 | Root | Schema | Unique keys | Duplicates |",
        "|---|---:|---|---|---|---:|---|",
    ]
    for r in report["files"]:
        md.append("| " + " | ".join(map(markdown_escape, [
            r.get("relative_path", r.get("path")), r.get("size_bytes", "?"), r.get("sha256", "ERROR"),
            r.get("root_tag", "?"), r.get("schema", "?"), r.get("unique_keys", "?"),
            ", ".join(r.get("duplicate_keys", [])) or "none"
        ])) + " |")
    md += ["", "## Full-config comparisons", ""]
    for c in report["comparisons"]:
        md += [
            f"### `{c['first']}` vs `{c['second']}`",
            f"- Keys: {c['first_keys']} vs {c['second_keys']}; schemas: `{c['first_schema']}` vs `{c['second_schema']}`",
            f"- Missing in second: {len(c['missing_in_second'])}; extra in second: {len(c['extra_in_second'])}; changed shared values: {c['changed_count']}",
        ]
        if c["missing_in_second"]: md.append("- Missing keys: " + ", ".join(f"`{x}`" for x in c["missing_in_second"][:100]))
        if c["extra_in_second"]: md.append("- Extra keys: " + ", ".join(f"`{x}`" for x in c["extra_in_second"][:100]))
        if c["changed_values"]:
            md += ["", "| Key | First value | Second value |", "|---|---|---|"]
            for v in c["changed_values"][:80]:
                md.append("| " + " | ".join(markdown_escape(v[k]) for k in ("key", "first", "second")) + " |")
        md.append("")
    md += ["## Warnings", ""]
    md += ["- " + w for w in report["warnings"]] or ["- No inventory warnings."]
    md += ["", "## Candidate status", "", "```json",
           json.dumps(report["candidate"], indent=2, ensure_ascii=False) if report["candidate"] else "No candidate requested; audit-only mode.",
           "```", "", "## Interpretation", "",
           "- Hash/key-count agreement proves file identity against the supplied historical reference, not that it is the currently active phone config.",
           "- XML structure alone does not establish image quality. No A/B performance claim is made.",
           "- Small text-content profiles must not be merged into full value-attribute configs.",
           "- Do not import or activate any candidate until its LMC import format and device behavior are verified.", ""]
    (outdir / "V8_AUDIT_REPORT.md").write_text("\n".join(md), encoding="utf-8")
    (outdir / "V8_VALIDATION.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    # Safe minimal test plan
    plan = """# V8 A/B Test Plan (not executed)

1. Back up the currently active LMC config and record its exact path and SHA-256.
2. Confirm the app's actual import format; do not assume a full config is accepted as a small profile.
3. Keep baseline and candidate separate. Do not overwrite the active file.
4. Use the same Lava LXX521, rear IMX682 camera, LMC 8.4 Iris R18F1 version, lens, resolution, mode, framing, focus, and lighting.
5. Capture at least 3 baseline and 3 candidate images per scene: neutral gray/white target under controlled indoor light; daylight with highlights and shadows; textured fabric/leaves/text; indoor low light; night mode tested separately.
6. Keep original files and EXIF. Pair captures by scene and mode. Do not mix night/long-exposure images with standard-photo results.
7. Compare white balance/color cast, clipping, luminance/chroma noise, texture, halos, and consistency. Avoid claims of true MTF/distortion/color calibration without appropriate targets and controlled setup.
8. If candidate is worse or unstable, restore the backed-up baseline and verify its hash. Do not alter protected device partitions.
9. This plan is not evidence that a test has run or passed.
"""
    (outdir / "V8_AB_TEST_PLAN.md").write_text(plan, encoding="utf-8")
    print(f"\nDONE. Audit report: {outdir / 'V8_AUDIT_REPORT.md'}")
    print(f"Machine-readable report: {outdir / 'V8_VALIDATION.json'}")
    print(f"A/B plan: {outdir / 'V8_AB_TEST_PLAN.md'}")
    if report["candidate"]:
        print("Candidate:", report["candidate"])
    print("No phone config was imported or activated.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
