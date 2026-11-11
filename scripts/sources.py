#!/usr/bin/env python3
"""sources.py - manage the LMC84 sources registry (configs/sources.json).

Subcommands:
  list                          print a table of all registered sources
  verify [--name NAME]          recompute manifest_sha256; exit 0 on match, 1 on drift
  add --name NAME --path PATH [--kind lmc84] [--role canonical|candidate|live]
  remove --name NAME [--yes]    remove a registered source
  verify-overlap --path PATH    print whether PATH overlaps a registered `live` source
                                (exit 2 if it overlaps and --force-source-overlap is absent)

manifest_sha256 algorithm (documented in README):
    canonical JSON blob {"files":[{"name":<basename>,"sha256":<hex>,"bytes":<int>}, ...]}
    with file entries sorted by name, object keys sorted, UTF-8, no whitespace;
    SHA-256 of that blob.

All writes go only to configs/. Never write to a registered source path.
"""
import argparse
import hashlib
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(REPO_ROOT, "configs")
REGISTRY_PATH = os.environ.get("LMC84_SOURCES_REGISTRY",
                               os.path.join(CONFIG_DIR, "sources.json"))


def _load_registry():
    with open(REGISTRY_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def _save_registry(registry):
    with open(REGISTRY_PATH, "w", encoding="utf-8") as handle:
        json.dump(registry, handle, indent=2, sort_keys=False)
        handle.write("\n")


def _manifest_files(path):
    """Return sorted file list [{name,sha256,bytes}] for *.xml under `path` (read-only)."""
    files = []
    for name in sorted(os.listdir(path)):
        if not name.endswith(".xml"):
            continue
        full = os.path.join(path, name)
        if not os.path.isfile(full):
            continue
        with open(full, "rb") as handle:
            data = handle.read()
        files.append({
            "name": name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        })
    files.sort(key=lambda x: x["name"])
    return files


def _manifest_sha256(path):
    files = _manifest_files(path)
    blob = json.dumps({"files": files}, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    return files, hashlib.sha256(blob).hexdigest()


def _entry_path(registry, name):
    for entry in registry.get("sources", []):
        if entry.get("name") == name:
            return entry
    return None


def _resolve_path(path):
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _is_live(entry):
    return entry.get("role") == "live"


def overlaps_deploy_dest(path):
    """Return True if `path` equals a registered `live` source path (read-only check)."""
    registry = _load_registry()
    target = os.path.abspath(path)
    for entry in registry.get("sources", []):
        if _is_live(entry):
            entry_path = os.path.abspath(_resolve_path(entry["path"]))
            if os.path.normcase(target) == os.path.normcase(entry_path):
                return True
    return False


def cmd_list(_args):
    registry = _load_registry()
    print(f"{'name':<18} {'role':<10} {'kind':<10} {'path':<32} {'files':>6} {'bytes':>10}  read_only")
    print("-" * 95)
    for entry in registry.get("sources", []):
        path = _resolve_path(entry["path"])
        try:
            files, _ = _manifest_sha256(path)
            total_bytes = sum(f["bytes"] for f in files)
            nfiles = len(files)
        except FileNotFoundError:
            nfiles, total_bytes = -1, -1
        print(f"{entry.get('name',''):<18} {entry.get('role',''):<10} "
              f"{entry.get('kind',''):<10} {entry.get('path',''):<32} "
              f"{nfiles:>6} {total_bytes:>10}  {entry.get('read_only', False)}")
    return 0


def cmd_verify(args):
    registry = _load_registry()
    targets = [args.name] if args.name else [e["name"] for e in registry.get("sources", [])]
    overall_ok = True
    for name in targets:
        entry = _entry_path(registry, name)
        if not entry:
            print(f"[!] no such source: {name}", file=sys.stderr)
            overall_ok = False
            continue
        path = _resolve_path(entry["path"])
        try:
            files, computed = _manifest_sha256(path)
        except FileNotFoundError:
            print(f"[!] {name}: source path missing: {path}", file=sys.stderr)
            overall_ok = False
            continue
        recorded = entry.get("manifest_sha256", "")
        status = "PASS" if computed == recorded else "DRIFT"
        if computed != recorded:
            overall_ok = False
        print(f"[{status}] {name}: recorded={recorded[:12]}... computed={computed[:12]}... "
              f"files={len(files)} path={entry.get('path')}")
    return 0 if overall_ok else 1


def cmd_add(args):
    registry = _load_registry()
    if _entry_path(registry, args.name):
        print(f"[!] source already exists: {args.name}", file=sys.stderr)
        return 1
    path = _resolve_path(args.path)
    if not os.path.isdir(path):
        print(f"[!] source path is not a directory: {path}", file=sys.stderr)
        return 1
    files, manifest = _manifest_sha256(path)
    entry = {
        "name": args.name,
        "path": args.path,
        "kind": args.kind,
        "role": args.role,
        "manifest_sha256": manifest,
    }
    if args.role == "live":
        entry["read_only"] = True
    entry["added_at"] = _utc_now()
    entry["notes"] = args.notes or ""
    registry.setdefault("sources", []).append(entry)
    _save_registry(registry)
    print(f"[+] added source {args.name} ({args.role}) with {len(files)} files, manifest={manifest[:12]}...")
    return 0


def cmd_remove(args):
    registry = _load_registry()
    entry = _entry_path(registry, args.name)
    if not entry:
        print(f"[!] no such source: {args.name}", file=sys.stderr)
        return 1
    if entry.get("role") == "live" and not args.yes:
        print(f"[!] refusing to remove live source {args.name} without --yes", file=sys.stderr)
        return 1
    registry["sources"] = [e for e in registry.get("sources", []) if e.get("name") != args.name]
    _save_registry(registry)
    print(f"[-] removed source {args.name}")
    return 0


def _utc_now():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def cmd_verify_overlap(args):
    path = args.path
    overlap = overlaps_deploy_dest(path)
    if overlap:
        if args.force_source_overlap:
            print(f"[!] WARNING: destination overlaps registered live source: {path}",
                  file=sys.stderr)
            return 0
        print(f"[!] destination overlaps a registered live source: {path}", file=sys.stderr)
        print("    Refusing: pass --force-source-overlap to override.", file=sys.stderr)
        return 2
    print(f"[OK] no overlap with registered live sources: {path}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="LMC84 sources registry manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list registered sources")
    p_list.set_defaults(func=cmd_list)

    p_verify = sub.add_parser("verify", help="recompute manifest_sha256; exit 0 match / 1 drift")
    p_verify.add_argument("--name", help="source name to verify (default: all)")
    p_verify.set_defaults(func=cmd_verify)

    p_add = sub.add_parser("add", help="register a new source")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--path", required=True)
    p_add.add_argument("--kind", default="lmc84")
    p_add.add_argument("--role", default="candidate",
                       choices=["canonical", "candidate", "live"])
    p_add.add_argument("--notes", default="")
    p_add.set_defaults(func=cmd_add)

    p_remove = sub.add_parser("remove", help="remove a registered source")
    p_remove.add_argument("--name", required=True)
    p_remove.add_argument("--yes", action="store_true")
    p_remove.set_defaults(func=cmd_remove)

    p_overlap = sub.add_parser("verify-overlap",
                              help="check whether a path overlaps a registered live source")
    p_overlap.add_argument("--path", required=True)
    p_overlap.add_argument("--force-source-overlap", action="store_true")
    p_overlap.set_defaults(func=cmd_verify_overlap)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
