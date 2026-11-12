#!/usr/bin/env python3
"""triage_profiles.py - triage LXX521 LMC84 candidate XML profiles.

For every candidate XML it computes sha256, byte size, key count, the delta
against a reference profile (added / removed / changed keys), a deterministic
family assignment, and validation status via validate_source (kind=lmc84).
Duplicate candidates are detected both by exact sha256 and by identical delta
signature (frozenset of (key, old, new) triples).

Family heuristic (first matching rule wins, documented here for determinism):
    baseline        if delta.added + delta.changed == 0
    night           if basename contains "NIGHT" (case-insensitive)
                      OR a delta change has key lib_denoise_key  > 1
                      AND a delta change has key pref_frames_hdr_key > 4
    balanced        if basename contains "BALANCED"
    dslr            if basename matches /DSLR(64|MAX)?/
    sharpness_probe if basename contains "SHARPNESS_PROBE"
                      OR the only delta changes touch lib_sharpnessb_key
    allinone        if basename contains "ALLINONE"
    hr              if basename contains "_HR"
    aesthetic       if basename in {IPHONE, PIXEL, PORTRAIT}
    experiment      fallback (everything else)

Outputs (deterministic):
  * reports/lxx521_triage.json  - machine-readable, NO timestamps, stable ordering
  * reports/lxx521_triage.md    - human-readable, generated_at allowed only in header

Safety: never writes to configs/candidates, never writes to /sdcard, never deploys.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from validate_profile import validate_source  # noqa: E402

AESTHETIC_NAMES = {"IPHONE", "PIXEL", "PORTRAIT"}
DSLR_RE = re.compile(r"DSLR(64|MAX)?", re.IGNORECASE)


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _keys(path):
    """Return {key: value} from a profile XML (self-closing tags -> "")."""
    root = ET.parse(path).getroot()
    kv = {}
    for el in root.findall("string"):
        name = el.get("name")
        if name:
            kv[name] = el.text if el.text is not None else ""
    return kv


def _delta(ref_keys, cand_keys):
    added = sorted(k for k in cand_keys if k not in ref_keys)
    removed = sorted(k for k in ref_keys if k not in cand_keys)
    changed = []
    for key in sorted(k for k in ref_keys if k in cand_keys and ref_keys[k] != cand_keys[k]):
        changed.append({"key": key, "old": ref_keys[key], "new": cand_keys[key]})
    return {"added": added, "removed": removed, "changed": changed}


def _family(basename, delta):
    added = delta.get("added", []) or []
    changed = delta.get("changed", []) or []
    lower = basename.lower()
    if not added and not changed:
        return "baseline"
    if "night" in lower:
        return "night"
    denoise = next((c for c in delta["changed"] if c["key"] == "lib_denoise_key"), None)
    frames = next((c for c in delta["changed"] if c["key"] == "pref_frames_hdr_key"), None)
    try:
        denoise_gt1 = denoise is not None and float(denoise["new"]) > 1
    except (TypeError, ValueError):
        denoise_gt1 = False
    try:
        frames_gt4 = frames is not None and float(frames["new"]) > 4
    except (TypeError, ValueError):
        frames_gt4 = False
    if denoise_gt1 and frames_gt4:
        return "night"
    if "balanced" in lower:
        return "balanced"
    if DSLR_RE.search(basename):
        return "dslr"
    sharp_only = (len(delta["changed"]) == 1
                  and delta["changed"][0]["key"] == "lib_sharpnessb_key")
    if "sharpness_probe" in lower or sharp_only:
        return "sharpness_probe"
    if "allinone" in lower:
        return "allinone"
    if "_hr" in lower:
        return "hr"
    upper = basename.upper()
    if any(name in upper for name in AESTHETIC_NAMES):
        return "aesthetic"
    return "experiment"


def _delta_signature(delta):
    """Hashable + JSON-serializable signature of the changed-key triples."""
    return tuple(sorted(
        (c["key"], c["old"], c["new"]) for c in delta["changed"]
    ))


def _group_duplicates(entries):
    """Return (exact_groups, signature_groups) where each group has >= 2 entries."""
    by_sha = {}
    by_sig = {}
    for entry in entries:
        by_sha.setdefault(entry["sha256"], []).append(entry["name"])
        by_sig.setdefault(entry["delta_signature"], []).append(entry["name"])
    exact = [sorted(g) for g in by_sha.values() if len(g) > 1]
    sig = [sorted(g) for g in by_sig.values() if len(g) > 1]
    exact.sort(key=lambda g: g[0])
    sig.sort(key=lambda g: g[0])
    return exact, sig


def triage(candidates_dir, reference_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ref_keys = _keys(reference_path)
    candidate_files = sorted(
        f for f in os.listdir(candidates_dir) if f.endswith(".xml")
    )

    entries = []
    for name in candidate_files:
        path = os.path.join(candidates_dir, name)
        data = open(path, "rb").read()
        cand_keys = _keys(path)
        delta = _delta(ref_keys, cand_keys)
        validation = validate_source(path, kind_override="lmc84")
        entries.append({
            "name": name,
            "path": path,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "key_count": len(cand_keys),
            "delta": delta,
            "delta_signature": _delta_signature(delta),
            "family": _family(name, delta),
            "validation": {
                "pass": validation["pass"],
                "errors": validation["errors"],
                "warnings": validation["warnings"],
            },
        })
    entries.sort(key=lambda e: e["name"])

    exact_groups, sig_groups = _group_duplicates(entries)

    # Aggregates (deterministic, no timestamps)
    family_counts = {}
    validation_summary = {"pass": 0, "warn": 0, "error": 0}
    for entry in entries:
        family_counts[entry["family"]] = family_counts.get(entry["family"], 0) + 1
        v = entry["validation"]
        if v["pass"]:
            validation_summary["pass"] += 1
        if v["warnings"]:
            validation_summary["warn"] += 1
        if v["errors"]:
            validation_summary["error"] += 1

    report = {
        "schema_version": 1,
        "reference": os.path.basename(reference_path),
        "reference_key_count": len(ref_keys),
        "candidate_count": len(entries),
        "families": dict(sorted(family_counts.items())),
        "validation_summary": validation_summary,
        "duplicate_groups": {
            "by_sha256": exact_groups,
            "by_delta_signature": sig_groups,
        },
        "candidates": entries,
    }

    json_path = os.path.join(out_dir, "lxx521_triage.json")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")

    md_path = os.path.join(out_dir, "lxx521_triage.md")
    import datetime
    generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    lines = []
    lines.append("# LXX521 Candidate Triage Report")
    lines.append("")
    lines.append(f"generated_at: {generated_at}")
    lines.append("")
    lines.append(f"Reference: `{os.path.basename(reference_path)}` "
                 f"({report['reference_key_count']} keys)")
    lines.append(f"Candidates: {report['candidate_count']}")
    lines.append("")
    lines.append("## Families")
    for family in sorted(report["families"]):
        lines.append(f"- {family}: {report['families'][family]}")
    lines.append("")
    lines.append("## Validation summary")
    lines.append(f"- pass: {validation_summary['pass']}")
    lines.append(f"- warn: {validation_summary['warn']}")
    lines.append(f"- error: {validation_summary['error']}")
    lines.append("")
    lines.append("## Duplicate groups")
    lines.append(f"- by sha256: {len(exact_groups)}")
    lines.append(f"- by delta signature: {len(sig_groups)}")
    for g in exact_groups:
        lines.append(f"  - exact (sha256): {', '.join(g)}")
    for g in sig_groups:
        lines.append(f"  - delta signature: {', '.join(g)}")
    lines.append("")
    lines.append("## Per-candidate detail")
    for entry in entries:
        lines.append(f"### {entry['name']}")
        lines.append(f"- sha256: {entry['sha256']}")
        lines.append(f"- bytes: {entry['bytes']}")
        lines.append(f"- key_count: {entry['key_count']}")
        lines.append(f"- family: {entry['family']}")
        lines.append(f"- validation: pass={entry['validation']['pass']} "
                     f"errors={len(entry['validation']['errors'])} "
                     f"warnings={len(entry['validation']['warnings'])}")
        d = entry["delta"]
        lines.append(f"- delta: added={len(d['added'])} removed={len(d['removed'])} "
                     f"changed={len(d['changed'])}")
        lines.append("")
    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    return report, json_path, md_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Triage LXX521 candidate profiles")
    parser.add_argument("--candidates", default="configs/candidates/LXX521")
    parser.add_argument("--reference", default="configs/xml/LXX521_TEX.xml")
    parser.add_argument("--out", default="reports")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    args = parser.parse_args(argv)

    candidates_dir = args.candidates if os.path.isabs(args.candidates) \
        else os.path.join(REPO_ROOT, args.candidates)
    reference_path = args.reference if os.path.isabs(args.reference) \
        else os.path.join(REPO_ROOT, args.reference)
    out_dir = args.out if os.path.isabs(args.out) else os.path.join(REPO_ROOT, args.out)

    if not os.path.isdir(candidates_dir):
        print(f"[!] candidates dir not found: {candidates_dir}", file=sys.stderr)
        return 2
    if not os.path.isfile(reference_path):
        print(f"[!] reference not found: {reference_path}", file=sys.stderr)
        return 2

    report, json_path, md_path = triage(candidates_dir, reference_path, out_dir)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        with open(md_path, encoding="utf-8") as handle:
            print(handle.read())
    print(f"[+] wrote {json_path} and {md_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
