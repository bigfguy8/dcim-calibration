#!/usr/bin/env python3
"""DCIM Calibration / LXX521 IMX682 — portable Termux master workflow.
Python standard library only. No photo capture, no camera session, no source edits.
Default: audit/build an unchanged candidate package, camera inventory only, no Telegram send.
Destructive cleanup and Telegram publication require explicit CLI flags and credentials.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, os, re, shutil, statistics, sys, time, zipfile
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
import urllib.error, urllib.request
import xml.etree.ElementTree as ET

APP_VERSION = "1.0.0"
PROJECT_OWNER = "@bigfguy8"
TARGET_CAMERA = Path("/sdcard/DCIM/Camera")
ALLOWED_CAMERA_RESOLVED = {Path("/sdcard/DCIM/Camera"), Path("/storage/emulated/0/DCIM/Camera")}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".avif", ".gif", ".bmp", ".tif", ".tiff", ".dng", ".raw", ".cr2", ".cr3", ".nef", ".arw", ".rw2", ".orf", ".raf"}
RELEVANT_EXTS = {".xml", ".py", ".csv", ".md", ".json", ".zip", ".txt", ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".avif"}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "site-packages", "storage", "Camera", "DCIM"}


def now_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def format_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}h {minutes:02d}m {secs:02d}s"


class SourceRef:
    def __init__(self, display: str, name: str, reader, size: int, modified: str | None, from_zip: bool = False):
        self.display, self.name, self._reader = display, name, reader
        self.size, self.modified, self.from_zip = size, modified, from_zip
    def read_bytes(self) -> bytes:
        return self._reader()
    def digest(self) -> str:
        return sha256_bytes(self.read_bytes())


def read_ref(path: Path) -> SourceRef:
    st = path.stat()
    return SourceRef(str(path.resolve()), path.name, path.read_bytes, st.st_size,
                     datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="seconds"), False)


def zip_refs(zip_path: Path):
    refs = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                # Reject weird paths for inventory/candidate use; never extract archive paths.
                pp = PurePosixPath(info.filename)
                if pp.is_absolute() or ".." in pp.parts:
                    continue
                suffix = pp.suffix.lower()
                if suffix not in RELEVANT_EXTS:
                    continue
                entry = info.filename
                def loader(zpath=zip_path, zentry=entry):
                    with zipfile.ZipFile(zpath, "r") as za:
                        return za.read(zentry)
                modified = None
                try:
                    modified = datetime(*info.date_time).astimezone().isoformat(timespec="seconds")
                except Exception:
                    pass
                refs.append(SourceRef(f"{zip_path.resolve()}!/{entry}", pp.name, loader, info.file_size, modified, True))
    except (OSError, zipfile.BadZipFile) as e:
        return [], str(e)
    return refs, None


def safe_project_files(root: Path):
    found = []
    if not root.is_dir():
        return found
    for current, dirs, filenames in os.walk(root, topdown=True, followlinks=False):
        here = Path(current)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not (here / d).is_symlink()]
        # Avoid generated outputs/backups and recursively scanning Android paths.
        dirs[:] = [d for d in dirs if not d.startswith("V10_Master_Output") and d not in {"backups", "release_backups"}]
        for filename in filenames:
            p = here / filename
            if p.is_symlink() or p.suffix.lower() not in RELEVANT_EXTS:
                continue
            try:
                found.append(read_ref(p))
            except OSError:
                pass
    return found


def discover_zip(args_zip: str | None, root: Path) -> Path | None:
    candidates = []
    if args_zip:
        candidates.append(Path(args_zip).expanduser())
    candidates += [
        root / "DCIM_Calibration_Source.zip",
        Path.home() / "storage/shared/Download/DCIM_Calibration_Source.zip",
        Path.home() / "storage/shared/Downloads/DCIM_Calibration_Source.zip",
        Path("/sdcard/Download/DCIM_Calibration_Source.zip"),
        Path("/sdcard/Downloads/DCIM_Calibration_Source.zip"),
        Path("/mnt/data/DCIM_Calibration_Source.zip"),
    ]
    seen = set()
    for p in candidates:
        try:
            rp = p.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if rp in seen:
            continue
        seen.add(rp)
        if rp.is_file() and zipfile.is_zipfile(rp):
            return rp
    return None


def parse_xml_bytes(data: bytes):
    result = {"parse_ok": False, "error": None, "root_tag": None, "child_count": 0,
              "named_entries": 0, "unique_keys": 0, "duplicate_keys": [], "schema_family": "unknown"}
    try:
        root = ET.fromstring(data)
    except (ET.ParseError, ValueError, UnicodeError) as e:
        result["error"] = str(e)
        return result
    names, duplicates, tags = set(), set(), set()
    children = list(root)
    for child in children:
        tags.add(child.tag)
        key = child.attrib.get("name")
        if key is not None:
            if key in names:
                duplicates.add(key)
            names.add(key)
    result.update(parse_ok=True, root_tag=root.tag, child_count=len(children), named_entries=sum(1 for c in children if "name" in c.attrib),
                  unique_keys=len(names), duplicate_keys=sorted(duplicates), child_tags=sorted(tags))
    if root.tag == "map" and any(c.tag == "string" and c.attrib.get("name") == "pref_qjpg_key" for c in children):
        result["schema_family"] = "LMC-style shared-preferences map (probable; app support not proven)"
    elif root.tag == "map":
        result["schema_family"] = "Android shared-preferences map (parameter family unconfirmed)"
    else:
        result["schema_family"] = f"XML root: {root.tag} (application schema unavailable)"
    return result


def is_v9_baseline(ref: SourceRef) -> bool:
    norm = re.sub(r"[^a-z0-9]+", "", ref.name.lower())
    return ("v9" in norm and "conservativebalanced" in norm) or ("conservativebalancedv9" in norm)


def is_lmc_candidate(ref: SourceRef) -> bool:
    n = ref.name.lower()
    return n in {"lxx521_imx682_lmc84_allrounder.xml", "lxx521_imx682_allrounder_naturalbalanced.xml"} or ("lmc84" in n and "allrounder" in n)


def pick_source(refs: list[SourceRef], predicate):
    choices = [r for r in refs if r.name.lower().endswith(".xml") and predicate(r)]
    if not choices:
        return None, []
    by_hash = {}
    for ref in choices:
        try: by_hash.setdefault(ref.digest(), []).append(ref)
        except Exception: pass
    if len(by_hash) > 1:
        return None, choices
    # Prefer local file to archive entry, then known most-recent modification.
    choices.sort(key=lambda r: (r.from_zip, r.modified or "", r.display))
    return choices[-1], choices


def camera_signature(path: Path) -> bool:
    try:
        with path.open("rb") as f: h = f.read(32)
    except OSError:
        return False
    if h.startswith(b"\xff\xd8\xff") or h.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if h.startswith((b"GIF87a", b"GIF89a", b"BM", b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")):
        return True
    if len(h) >= 12 and h[:4] == b"RIFF" and h[8:12] == b"WEBP":
        return True
    if len(h) >= 12 and h[4:8] == b"ftyp" and h[8:12] in {b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1", b"avif", b"avis"}:
        return True
    return False


def camera_is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS or camera_signature(path)


def camera_inventory(do_delete: bool = False, pre_report_path: Path | None = None):
    report = {"requested_path": str(TARGET_CAMERA), "exists": False, "resolved_path": None,
              "mode": "DELETE" if do_delete else "INVENTORY_ONLY", "image_count_before": 0,
              "image_bytes_before": 0, "non_image_or_preserved_count": 0, "nested_directory_count": 0,
              "images": [], "preserved": [], "errors": [], "deleted": [], "delete_errors": [],
              "remaining_image_count_after": None}
    if not TARGET_CAMERA.exists() or not TARGET_CAMERA.is_dir() or TARGET_CAMERA.is_symlink():
        report["error"] = "Exact /sdcard/DCIM/Camera target is missing, not a directory, or is itself a symlink. No deletion performed."
        return report
    try:
        resolved = TARGET_CAMERA.resolve(strict=True)
    except OSError as e:
        report["error"] = f"Target resolution failed: {e}"
        return report
    if resolved not in ALLOWED_CAMERA_RESOLVED or resolved.name != "Camera" or resolved.parent.name != "DCIM":
        report["error"] = f"Canonical path outside allowed Camera directory: {resolved}. No deletion performed."
        return report
    report.update(exists=True, resolved_path=str(resolved))
    images, preserved, dirs, errors = [], [], [], []
    for current, dirnames, filenames in os.walk(TARGET_CAMERA, topdown=True, followlinks=False):
        rp = Path(current)
        safe_dirs = []
        for dn in dirnames:
            dp = rp / dn
            if dp.is_symlink(): preserved.append({"path": str(dp), "reason": "symlink directory preserved"})
            else: dirs.append(str(dp)); safe_dirs.append(dn)
        dirnames[:] = safe_dirs
        for name in filenames:
            fp = rp / name
            try:
                if fp.is_symlink() or not fp.is_file():
                    preserved.append({"path": str(fp), "reason": "symlink/non-regular file preserved"}); continue
                item = {"path": str(fp), "size_bytes": fp.stat().st_size}
                if camera_is_image(fp): images.append(item)
                else: preserved.append({**item, "reason": "not identified as image"})
            except OSError as e: errors.append({"path": str(fp), "error": str(e)})
    report.update(image_count_before=len(images), image_bytes_before=sum(i["size_bytes"] for i in images),
                  non_image_or_preserved_count=len(preserved), nested_directory_count=len(dirs), images=images,
                  preserved=preserved, errors=errors)
    # Persist the full pre-deletion inventory before any unlink operation begins.
    if pre_report_path is not None:
        write_json(pre_report_path, report)
    if do_delete:
        for item in images:
            fp = Path(item["path"])
            try:
                if fp.is_symlink() or not fp.is_file():
                    report["delete_errors"].append({"path": str(fp), "error": "changed to symlink/non-file; skipped"}); continue
                parent = fp.parent.resolve(strict=True)
                if parent != resolved and resolved not in parent.parents:
                    report["delete_errors"].append({"path": str(fp), "error": "resolved parent escaped target; skipped"}); continue
                if not camera_is_image(fp):
                    report["delete_errors"].append({"path": str(fp), "error": "no longer identified as image; skipped"}); continue
                fp.unlink()
                report["deleted"].append(str(fp))
            except OSError as e: report["delete_errors"].append({"path": str(fp), "error": str(e)})
        remaining = []
        for current, dirnames, filenames in os.walk(TARGET_CAMERA, topdown=True, followlinks=False):
            rp = Path(current); dirnames[:] = [d for d in dirnames if not (rp / d).is_symlink()]
            for name in filenames:
                fp = rp / name
                if not fp.is_symlink() and fp.is_file() and camera_is_image(fp): remaining.append(str(fp))
        report["remaining_image_count_after"] = len(remaining)
        report["remaining_images_after"] = remaining
    return report


def discover_analysis_data(refs: list[SourceRef]):
    metric = [r for r in refs if r.name.lower() == "image_metrics.csv"]
    reports = [r for r in refs if r.name.lower() == "report.md"]
    sheets = [r for r in refs if r.name.lower() == "contact_sheet.jpg"]
    manifests = [r for r in refs if r.name.lower() == "file_manifest.json"]
    result = {"original_artifacts_found": {"image_metrics.csv": bool(metric), "report.md": bool(reports), "contact_sheet.jpg": bool(sheets), "file_manifest.json": bool(manifests)},
              "csv_audits": [], "notes": []}
    for ref in metric:
        try:
            text = ref.read_bytes().decode("utf-8-sig", "replace")
            rows = list(csv.DictReader(io.StringIO(text)))
            headers = list(rows[0].keys()) if rows else []
            duplicates = len(rows) - len({tuple((row.get(h) or "") for h in headers) for row in rows})
            missing_cells = sum(1 for row in rows for h in headers if not (row.get(h) or "").strip())
            lower = [h.lower() for h in headers]
            profile_cols = [headers[i] for i, h in enumerate(lower) if "profile" in h or "config" in h]
            scene_cols = [headers[i] for i, h in enumerate(lower) if "scene" in h or "image" in h or "file" in h]
            numeric_cols = []
            for h in headers:
                vals = []
                for row in rows:
                    try: vals.append(float(row[h]))
                    except (ValueError, TypeError, KeyError): pass
                if vals and len(vals) >= max(1, int(len(rows) * 0.6)):
                    numeric_cols.append({"column": h, "numeric_values": len(vals), "mean": round(statistics.mean(vals), 6), "median": round(statistics.median(vals), 6)})
            result["csv_audits"].append({"source": ref.display, "rows": len(rows), "columns": headers,
                "duplicate_rows": duplicates, "missing_cells": missing_cells, "possible_profile_columns": profile_cols,
                "possible_scene_or_file_columns": scene_cols, "numeric_summary": numeric_cols})
        except Exception as e: result["notes"].append(f"Could not audit {ref.display}: {e}")
    if not metric: result["notes"].append("Original image_metrics.csv not located. Historical values remain unverified.")
    if not sheets: result["notes"].append("contact_sheet.jpg not located; scene/framing mismatch cannot be re-reviewed.")
    result["notes"].append("Different scenes or framing are not a controlled comparison; JPEG proxies do not establish sensor noise, dynamic range, color accuracy, or MTF50.")
    return result


def load_time_log(path: Path):
    if not path.exists(): return {"schema_version": 1, "sessions": [], "manual_minutes": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("sessions", []), list): raise ValueError("unexpected schema")
        data.setdefault("manual_minutes", 0)
        return data
    except Exception as e:
        raise RuntimeError(f"Existing time log could not be read safely and will not be overwritten: {path} ({e})")


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def make_openapi(out_path: Path):
    content = '''openapi: 3.1.0
info:
  title: DCIM Calibration Project Status API
  version: 1.0.0
  description: Read-only project status and logged effort for LXX521 / IMX682. Does not capture photos, delete files, edit XML, or publish to Telegram.
servers:
  - url: https://YOUR_PUBLIC_HTTPS_DOMAIN
    description: Replace with a trusted HTTPS endpoint or secured HTTPS tunnel.
security:
  - bearerAuth: []
paths:
  /health:
    get:
      operationId: getServiceHealth
      summary: Check that the local project API is running
      security: []
      responses:
        '200':
          description: Service status
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: {type: string}
                  service: {type: string}
  /project/status:
    get:
      operationId: getProjectStatus
      summary: Read the latest V10 audit and release state
      responses:
        '200':
          description: Latest project state
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: {type: string}
                  project_root: {type: string}
                  baseline_found: {type: boolean}
                  source_profile: {type: string}
                  xml_parse_ok: {type: boolean}
                  runtime_compatibility: {type: string}
                  image_quality_claim: {type: string}
                  package_integrity: {type: string}
                  generated_at: {type: string}
  /project/time:
    get:
      operationId: getProjectLoggedTime
      summary: Read measured/logged project time, not unrecorded historical effort
      responses:
        '200':
          description: Logged project time
          content:
            application/json:
              schema:
                type: object
                properties:
                  total_logged_seconds: {type: integer}
                  total_logged: {type: string}
                  historical_unlogged_time_known: {type: boolean}
                  note: {type: string}
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: API key
'''
    out_path.write_text(content, encoding="utf-8")


def make_plugin_readme(path: Path):
    path.write_text(f'''# DCIM Calibration ChatGPT Action scaffold\n\nThis folder is a **connector scaffold**, not an installed ChatGPT plugin. The OpenAPI schema exposes read-only project status and logged effort.\n\n## Setup\n1. Run `python V10_Termux_Master.py --root ~/dcim_calibration --serve-api` in Termux after setting a long random `V10_API_KEY`. The service listens only on `127.0.0.1` by default.\n2. ChatGPT cannot reach a phone's `127.0.0.1` directly. For an Action, deploy/proxy it behind a trusted public HTTPS endpoint or an authenticated HTTPS tunnel; do not expose an unauthenticated server.\n3. Replace `https://YOUR_PUBLIC_HTTPS_DOMAIN` in `V10_ChatGPT_Action_OpenAPI.yaml` with that real HTTPS base URL.\n4. In the ChatGPT plugin/action setup available to your account, create an API action, paste/import the OpenAPI schema, and configure Bearer API-key authentication with the same `V10_API_KEY`. Test `/health`, `/project/status`, and `/project/time`.\n5. This scaffold intentionally has no remote delete, XML-write, camera-control, or Telegram-publish endpoint.\n\nThe current ChatGPT integration model and UI vary by account. OpenAI documents Actions as OpenAPI-defined API integrations; this scaffold cannot install itself into ChatGPT.\n''', encoding="utf-8")


def api_server(root: Path, port: int):
    secret = os.environ.get("V10_API_KEY", "")
    if len(secret) < 24:
        raise SystemExit("Refusing to start API: set V10_API_KEY to a strong random value (at least 24 characters).")
    def latest_run():
        base = root / "V10_Master_Output"
        if not base.is_dir(): return None
        folders = sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name)
        return folders[-1] if folders else None
    class Handler(BaseHTTPRequestHandler):
        server_version = "DCIMCalibrationReadOnly/1.0"
        def log_message(self, *_args): return  # Do not log credentials/request headers.
        def send_json(self, status, data):
            raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(raw)
        def do_GET(self):
            route = urlparse(self.path).path
            if route == "/health":
                return self.send_json(200, {"status": "ok", "service": "dcim-calibration-read-only"})
            if self.headers.get("Authorization", "") != f"Bearer {secret}":
                return self.send_json(401, {"error": "unauthorized"})
            run = latest_run()
            if route == "/project/status":
                if run is None: return self.send_json(200, {"status": "no-audit-run", "project_root": str(root)})
                state_path = run / "project_status.json"
                try: state = json.loads(state_path.read_text(encoding="utf-8"))
                except Exception: state = {"status": "status-report-unavailable", "project_root": str(root)}
                return self.send_json(200, state)
            if route == "/project/time":
                tl = root / "V10_project_time_log.json"
                try:
                    data = json.loads(tl.read_text(encoding="utf-8")) if tl.exists() else {"sessions": [], "manual_minutes": 0}
                    sec = int(data.get("manual_minutes", 0) * 60 + sum(float(s.get("duration_seconds", 0)) for s in data.get("sessions", [])))
                except Exception: sec = 0
                return self.send_json(200, {"total_logged_seconds": sec, "total_logged": format_duration(sec),
                    "historical_unlogged_time_known": False, "note": "Only explicit logged sessions/manual entries are counted. Historical unlogged effort cannot be inferred from file timestamps."})
            return self.send_json(404, {"error": "not found"})
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Read-only API listening on http://127.0.0.1:{port}; no external bind. Press Ctrl+C to stop.")
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nAPI stopped.")
    finally: server.server_close()


def telegram_request(token: str, method: str, fields: dict, file_field: tuple[str, Path] | None = None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    boundary = "----V10Boundary7MA4YWxkTrZu0gW"
    body = bytearray()
    def field(name, value):
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
    for k, v in fields.items(): field(k, v)
    if file_field:
        name, path = file_field
        data = path.read_bytes()
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{path.name}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode())
        body.extend(data); body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(url, data=bytes(body), headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp: result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Deliberately suppress URL/error bodies that might echo credentials.
        raise RuntimeError(f"Telegram API returned HTTP {e.code} for {method}; credentials omitted from report")
    except Exception as e:
        raise RuntimeError(f"Telegram request failed for {method}: {type(e).__name__}; credentials omitted from report")
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API returned ok=false for {method}; details omitted to avoid credential leakage")
    return result.get("result", {})


def send_telegram(release: Path, zip_path: Path, validation_path: Path, post_text: str, dest: str):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token: raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    if not dest: raise RuntimeError("TELEGRAM_CHAT_ID not set")
    uploaded = []
    for file_path in (release / "V10_Final.xml", zip_path, validation_path):
        if not file_path.is_file(): raise RuntimeError(f"Required attachment missing: {file_path.name}")
        result = telegram_request(token, "sendDocument", {"chat_id": dest, "caption": file_path.name}, ("document", file_path))
        uploaded.append({"file": file_path.name, "message_id": result.get("message_id")})
    result = telegram_request(token, "sendMessage", {"chat_id": dest, "text": post_text, "disable_web_page_preview": "true"})
    message_id = result.get("message_id")
    post_url = None
    if dest.startswith("@") and message_id:
        post_url = f"https://t.me/{dest[1:]}/{message_id}"
    return {"upload_status": "success", "uploaded": uploaded, "post_status": "success", "message_id": message_id, "post_url": post_url}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default="~/dcim_calibration", help="project root (default: ~/dcim_calibration)")
    parser.add_argument("--source-zip", help="source ZIP path; auto-discovered if omitted")
    parser.add_argument("--skip-camera", action="store_true", help="skip inventory of exact /sdcard/DCIM/Camera path")
    parser.add_argument("--delete-camera-images", action="store_true", help="explicitly delete identified image files ONLY inside /sdcard/DCIM/Camera after inventory; irreversible")
    parser.add_argument("--publish", action="store_true", help="upload XML, ZIP, validation report and publish accurate status to TELEGRAM_CHAT_ID using TELEGRAM_BOT_TOKEN")
    parser.add_argument("--chat-id", default=os.environ.get("TELEGRAM_CHAT_ID", ""), help="Telegram destination chat/channel id; otherwise use TELEGRAM_CHAT_ID env var")
    parser.add_argument("--log-minutes", type=int, default=0, help="append an explicitly supplied additional project-work duration (minutes); only use if you can substantiate it")
    parser.add_argument("--serve-api", action="store_true", help="after audit, start local read-only API for ChatGPT Action scaffold")
    parser.add_argument("--api-port", type=int, default=8765)
    args = parser.parse_args()

    start_mono = time.monotonic()
    start_iso = now_local()
    root = Path(args.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    output_base = root / "V10_Master_Output"
    output_base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_base / f"run_{stamp}"
    if run_dir.exists(): raise SystemExit(f"Refusing to overwrite existing run directory: {run_dir}")
    release = run_dir / "V10_Final_Release"
    release.mkdir(parents=True)

    source_zip = discover_zip(args.source_zip, root)
    local_refs = safe_project_files(root)
    all_refs = list(local_refs)
    zip_errors = []
    if source_zip:
        arch_refs, err = zip_refs(source_zip)
        all_refs.extend(arch_refs)
        if err: zip_errors.append(err)

    # Inventory records prove existence before use; archive files are never extracted or executed.
    inventory = []
    seen = set()
    for ref in all_refs:
        key = ref.display
        if key in seen: continue
        seen.add(key)
        item = {"filename": ref.name, "absolute_or_archive_path": ref.display, "size_bytes": ref.size,
                "sha256": None, "modified": ref.modified, "file_type": Path(ref.name).suffix.lower() or "unknown",
                "validation": "not applicable"}
        try:
            data = ref.read_bytes(); item["sha256"] = sha256_bytes(data)
            suffix = Path(ref.name).suffix.lower()
            if suffix == ".xml":
                xv = parse_xml_bytes(data)
                item["validation"] = "XML_PARSE_PASS" if xv["parse_ok"] else "XML_PARSE_FAIL"
                item["xml"] = {k: v for k, v in xv.items() if k != "child_tags"}
                known_hashes = {
                    "2118c905a247a5534dadfb82530638659e7d39c54ea3cf8dd622baf145bebc9a": "historical reference: original_v2_release_day.xml (2633 keys)",
                    "f5dde315f71bb4c28f72ea0b2a5cd3b5385f2e4aeb12b7463416174acb1b5f49": "historical reference: default_working_backup.xml (2641 keys)",
                }
                item["known_historical_hash_match"] = known_hashes.get(item["sha256"])
            elif suffix == ".py":
                try:
                    compile(data.decode("utf-8-sig"), ref.name, "exec")
                    item["validation"] = "PYTHON_SYNTAX_PASS"
                except Exception as e: item["validation"] = f"PYTHON_SYNTAX_FAIL: {type(e).__name__}: {e}"
        except Exception as e:
            item["validation"] = f"READ_ERROR: {type(e).__name__}: {e}"
        inventory.append(item)

    v9, v9_choices = pick_source(all_refs, is_v9_baseline)
    v9_ambiguous = v9 is None and len({r.digest() for r in v9_choices}) > 1 if v9_choices else False
    candidate, cand_choices = (None, [])
    candidate_ambiguous = False
    if v9 is None and not v9_ambiguous:
        # Prefer the explicitly LMC 8.4-named all-rounder; only use secondary candidates if absent.
        preferred_names = ["lxx521_imx682_lmc84_allrounder.xml", "lxx521_imx682_allrounder_naturalbalanced.xml"]
        for preferred_name in preferred_names:
            exact = [r for r in all_refs if r.name.lower() == preferred_name]
            if exact:
                candidate, cand_choices = pick_source(exact, lambda _r: True)
                candidate_ambiguous = candidate is None and len({r.digest() for r in cand_choices}) > 1
                break
        if candidate is None and not candidate_ambiguous and not cand_choices:
            fallbacks = [r for r in all_refs if r.name.lower() in {"lxx521_imx682_allinone_v3.xml", "lxx521_imx682_allinone_master.xml"}]
            if fallbacks:
                candidate, cand_choices = pick_source(fallbacks, lambda _r: True)
                candidate_ambiguous = candidate is None and len({r.digest() for r in cand_choices}) > 1
    chosen = v9 or candidate
    baseline_found = v9 is not None
    output_xml = release / "V10_Final.xml"
    source_profile = None
    xml_validation = {"parse_ok": False, "error": "No valid source XML candidate found"}
    backup_path = None
    if chosen is not None:
        raw = chosen.read_bytes()
        xml_validation = parse_xml_bytes(raw)
        if xml_validation["parse_ok"]:
            output_xml.write_bytes(raw)  # exact byte-copy; no values are invented/modified
            source_profile = {"source": chosen.display, "filename": chosen.name, "sha256": sha256_bytes(raw), "size_bytes": len(raw), "is_v9_baseline": baseline_found}
            if baseline_found:
                backup_root = root / "V10_Backups"
                backup_root.mkdir(parents=True, exist_ok=True)
                backup_path = backup_root / f"V9_Backup_{sha256_bytes(raw)[:12]}.xml"
                if not backup_path.exists(): backup_path.write_bytes(raw)
                # Verify independent backup before including it in the release.
                if sha256_file(backup_path) == sha256_bytes(raw): shutil.copy2(backup_path, release / "V9_Backup.xml")
                else: raise RuntimeError("V9 backup hash verification failed; refusing to continue")
        else:
            source_profile = {"source": chosen.display, "filename": chosen.name, "sha256": sha256_bytes(raw), "size_bytes": len(raw), "is_v9_baseline": baseline_found}
    else:
        output_xml.write_text("<!-- BLOCKED: no identifiable, parseable source profile. Do not import this file. -->\n", encoding="utf-8")

    duplicate_count = len(xml_validation.get("duplicate_keys", [])) if xml_validation.get("parse_ok") else None
    if v9_ambiguous:
        status = "BLOCKED_AMBIGUOUS_V9_BASELINE"
    elif candidate_ambiguous and not baseline_found:
        status = "BLOCKED_AMBIGUOUS_SOURCE_PROFILE"
    elif chosen is None or not xml_validation.get("parse_ok"):
        status = "BLOCKED_NO_VALID_XML_SOURCE"
    elif baseline_found and duplicate_count:
        status = "BLOCKED_V9_DUPLICATE_KEYS"
    elif baseline_found:
        status = "AUDITED_REVISION_NO_SETTINGS_CHANGED"
    else:
        status = "DRAFT_CANDIDATE_NOT_V9_DERIVED"

    metrics = discover_analysis_data(all_refs)
    camera_report = {"mode": "SKIPPED"} if args.skip_camera else camera_inventory(args.delete_camera_images, run_dir / "Camera_Cleanup_Inventory.json")
    write_json(run_dir / "Camera_Cleanup_Inventory.json", camera_report)
    # Copy project inventory reports into the release; original source files remain untouched.
    write_json(release / "V10_File_Inventory.json", {"generated_at": now_local(), "project_root": str(root), "source_zip": str(source_zip) if source_zip else None,
              "source_files": inventory, "archive_warnings": zip_errors})
    with (release / "V10_Source_Manifest.txt").open("w", encoding="utf-8") as f:
        f.write(f"Generated: {now_local()}\nProject root: {root}\nSource ZIP: {source_zip or 'not found'}\n\n")
        for item in sorted(inventory, key=lambda x: x["absolute_or_archive_path"]):
            f.write(f"{item.get('sha256') or 'NO_HASH'}  {item['absolute_or_archive_path']}  ({item['size_bytes']} bytes; {item['validation']})\n")

    changelog_lines = ["# V10 Change Log", "", f"Generated: {now_local()}", f"Status: **{status}**", "",
      "- The source profile was copied byte-for-byte; no XML parameters were changed or invented.",
      "- No image capture or camera test session was performed.",
      "- The candidate is an audited configuration revision only; image-quality superiority is not established."]
    if baseline_found:
        changelog_lines += [f"- Starting baseline: `{chosen.name}` (exact V9 ConservativeBalanced filename match).", f"- Independent V9 backup: `{backup_path}` (SHA-256 verified).", "- No setting change was justified by the supplied evidence; V10 preserves the baseline bytes."]
    elif chosen:
        changelog_lines += [f"- Exact V9 ConservativeBalanced profile was not found. Draft source copied: `{chosen.name}`.", "- This draft is **not derived from V9** and does not include `V9_Backup.xml`; do not treat it as an approved final release or replace a working profile."]
        if source_profile["sha256"] == "f5dde315f71bb4c28f72ea0b2a5cd3b5385f2e4aeb12b7463416174acb1b5f49":
            changelog_lines.append("- The candidate SHA-256 exactly matches the historical `default_working_backup.xml` hash embedded in the supplied V8 audit script (2641 keys). This establishes identity with that historical working-backup reference, **not** that it was the V9 ConservativeBalanced profile.")
    else: changelog_lines += ["- No valid XML source profile was found. `V10_Final.xml` contains only a BLOCKED marker and is not importable."]
    if v9_ambiguous: changelog_lines.append("- Multiple different files matched the V9 baseline name; baseline selection was blocked as ambiguous.")
    if candidate_ambiguous: changelog_lines.append("- Multiple different source files with the same candidate filename had different hashes; candidate selection was blocked as ambiguous.")
    (release / "V10_ChangeLog.md").write_text("\n".join(changelog_lines) + "\n", encoding="utf-8")

    validation_lines = ["# V10 Validation Report", "", f"Generated: {now_local()}", f"Release state: **{status}**", "",
      f"- XML syntax: {'PASS' if xml_validation.get('parse_ok') else 'FAIL'}.",
      f"- XML root: `{xml_validation.get('root_tag')}`; direct children: {xml_validation.get('child_count')}; unique named keys: {xml_validation.get('unique_keys')}.",
      f"- Repeated named keys: {len(xml_validation.get('duplicate_keys', [])) if xml_validation.get('parse_ok') else 'not applicable'}.",
      f"- Schema family: {xml_validation.get('schema_family', 'unknown')}.",
      "- Structural validity against an authoritative LMC 8.4 schema: NOT VERIFIED (no schema supplied).",
      "- Documented parameter support/ranges: NOT VERIFIED.",
      "- LXX521 device / LMC 8.4 runtime compatibility: NOT TESTED.",
      "- Image-quality improvement over V9: NOT ESTABLISHED.",
      "- New photos captured: NO.", "- Camera test session started: NO.", ""]
    if xml_validation.get("error"): validation_lines.append(f"XML error: {xml_validation['error']}")
    if xml_validation.get("duplicate_keys"): validation_lines.append("Repeated keys: " + ", ".join(xml_validation["duplicate_keys"][:80]))
    if not baseline_found: validation_lines.append("WARNING: V9 ConservativeBalanced was not identified. The XML file is a draft from an existing profile, not a V9-derived release.")
    (release / "V10_Validation_Report.md").write_text("\n".join(validation_lines) + "\n", encoding="utf-8")

    metrics_lines = ["# V10 Metrics Audit", "", f"Generated: {now_local()}", "", "## Source evidence", ""]
    for name, found in metrics["original_artifacts_found"].items(): metrics_lines.append(f"- `{name}`: {'FOUND' if found else 'NOT FOUND'}")
    for ca in metrics["csv_audits"]:
        metrics_lines += ["", f"## CSV: `{ca['source']}`", f"- Rows: {ca['rows']}; duplicate rows: {ca['duplicate_rows']}; empty cells: {ca['missing_cells']}.", f"- Candidate profile columns: {ca['possible_profile_columns']}; scene/file columns: {ca['possible_scene_or_file_columns']}.", "- Numeric column means/medians are recorded in the inventory analysis only; interpretation depends on verified column semantics."]
    metrics_lines += ["", "## Limitations", ""] + [f"- {n}" for n in metrics["notes"]]
    (release / "V10_Metrics_Audit.md").write_text("\n".join(metrics_lines) + "\n", encoding="utf-8")

    # Project time is based only on measured script runs plus explicitly supplied --log-minutes.
    timer_path = root / "V10_project_time_log.json"
    timer = load_time_log(timer_path)
    if args.log_minutes < 0: raise SystemExit("--log-minutes cannot be negative")
    if args.log_minutes:
        timer["manual_minutes"] = int(timer.get("manual_minutes", 0)) + args.log_minutes
        timer.setdefault("manual_entries", []).append({"at": now_local(), "minutes": args.log_minutes, "note": "Explicit user-supplied time; not independently verified"})
    elapsed = time.monotonic() - start_mono
    timer.setdefault("sessions", []).append({"started_at": start_iso, "ended_at": now_local(), "duration_seconds": round(elapsed, 2), "mode": "audit/build"})
    timer["last_updated"] = now_local()
    write_json(timer_path, timer)
    total_seconds = int(timer.get("manual_minutes", 0) * 60 + sum(float(s.get("duration_seconds", 0)) for s in timer.get("sessions", [])))
    time_report = {"total_logged_seconds": total_seconds, "total_logged": format_duration(total_seconds),
                   "run_seconds": round(elapsed, 2), "manual_minutes": int(timer.get("manual_minutes", 0)),
                   "historical_unlogged_time_known": False,
                   "note": "This is only measured script runtime plus manually supplied/logged sessions. File dates cannot reveal prior hands-on work hours."}
    write_json(release / "V10_Project_Time.json", time_report)

    # ChatGPT Action scaffold included with every run.
    action_dir = run_dir / "ChatGPT_Action"
    action_dir.mkdir()
    make_openapi(action_dir / "V10_ChatGPT_Action_OpenAPI.yaml")
    make_plugin_readme(action_dir / "V10_ChatGPT_Plugin_Setup.md")

    # status endpoint payload is intentionally read-only and does not expose secrets.
    project_status = {"status": status, "project_root": str(root), "baseline_found": baseline_found,
       "source_profile": source_profile["filename"] if source_profile else None,
       "xml_parse_ok": bool(xml_validation.get("parse_ok")),
       "runtime_compatibility": "not verified", "image_quality_claim": "not established",
       "package_integrity": "pending", "generated_at": now_local(), "project_time_logged": time_report["total_logged"]}
    write_json(run_dir / "project_status.json", project_status)

    # Hash all intended release files except the checksum file itself.
    with (release / "SHA256SUMS.txt").open("w", encoding="utf-8") as f:
        for item in sorted(release.iterdir()):
            if item.is_file() and item.name != "SHA256SUMS.txt": f.write(f"{sha256_file(item)}  {item.name}\n")
    zip_path = run_dir / "V10_Final_Package.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in sorted(release.iterdir()):
            if item.is_file(): zf.write(item, arcname=f"V10_Final_Release/{item.name}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        bad_member = zf.testzip()
        zip_names = zf.namelist()
    package_ok = bad_member is None and "V10_Final_Release/V10_Final.xml" in zip_names
    if package_ok:
        with zipfile.ZipFile(zip_path) as zf:
            manifest_data = zf.read("V10_Final_Release/SHA256SUMS.txt").decode("utf-8", "replace")
            for line in manifest_data.splitlines():
                if not line.strip(): continue
                digest, name = line.split("  ", 1)
                data = zf.read(f"V10_Final_Release/{name}")
                if sha256_bytes(data) != digest:
                    package_ok = False; break
    project_status["package_integrity"] = "PASS" if package_ok else "FAIL"
    project_status["package_sha256"] = sha256_file(zip_path) if zip_path.exists() else None
    write_json(run_dir / "project_status.json", project_status)
    # Save an external checksum file for the ZIP itself.
    (run_dir / "V10_Package_SHA256.txt").write_text(f"{sha256_file(zip_path)}  {zip_path.name}\n", encoding="utf-8")

    # Refresh the current session duration at the release-ready point, then rebuild hashes/package
    # so the reported project time corresponds to the full audit/build workflow before any Telegram network operation.
    elapsed_final = time.monotonic() - start_mono
    timer["sessions"][-1]["ended_at"] = now_local()
    timer["sessions"][-1]["duration_seconds"] = round(elapsed_final, 2)
    timer["last_updated"] = now_local()
    write_json(timer_path, timer)
    total_seconds = int(timer.get("manual_minutes", 0) * 60 + sum(float(s.get("duration_seconds", 0)) for s in timer.get("sessions", [])))
    time_report = {"total_logged_seconds": total_seconds, "total_logged": format_duration(total_seconds),
                   "run_seconds": round(elapsed_final, 2), "manual_minutes": int(timer.get("manual_minutes", 0)),
                   "historical_unlogged_time_known": False,
                   "note": "Includes measured audit/build workflow time up to release readiness plus explicitly supplied/logged sessions. It excludes any later Telegram network time; unrecorded historical hands-on work cannot be inferred from file timestamps."}
    write_json(release / "V10_Project_Time.json", time_report)
    with (release / "SHA256SUMS.txt").open("w", encoding="utf-8") as f:
        for item in sorted(release.iterdir()):
            if item.is_file() and item.name != "SHA256SUMS.txt": f.write(f"{sha256_file(item)}  {item.name}\n")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in sorted(release.iterdir()):
            if item.is_file(): zf.write(item, arcname=f"V10_Final_Release/{item.name}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        bad_member = zf.testzip()
        zip_names = zf.namelist()
    package_ok = bad_member is None and "V10_Final_Release/V10_Final.xml" in zip_names
    if package_ok:
        with zipfile.ZipFile(zip_path) as zf:
            manifest_data = zf.read("V10_Final_Release/SHA256SUMS.txt").decode("utf-8", "replace")
            for line in manifest_data.splitlines():
                if not line.strip(): continue
                digest, name = line.split("  ", 1)
                if sha256_bytes(zf.read(f"V10_Final_Release/{name}")) != digest:
                    package_ok = False; break
    project_status["package_integrity"] = "PASS" if package_ok else "FAIL"
    project_status["package_sha256"] = sha256_file(zip_path) if zip_path.exists() else None
    project_status["project_time_logged"] = time_report["total_logged"]
    write_json(run_dir / "project_status.json", project_status)
    (run_dir / "V10_Package_SHA256.txt").write_text(f"{sha256_file(zip_path)}  {zip_path.name}\n", encoding="utf-8")

    # Truthful Telegram post; measured total is included, unknown prior work is not invented.
    if status == "AUDITED_REVISION_NO_SETTINGS_CHANGED":
        release_sentence = "V10 is an audited unchanged revision of the identified V9 baseline; no setting changes were justified."
    elif source_profile:
        release_sentence = f"An unchanged draft candidate was copied from {source_profile['filename']}; a verified V9 baseline was not found, so this is NOT an approved V9-derived final release."
    else:
        release_sentence = "The V10 configuration is blocked because no valid source XML was found."
    post = (f"V10 CAMERA CONFIG AUDIT | {PROJECT_OWNER}\n\n{release_sentence}\n\n"
            f"✓ XML syntax: {'PASS' if xml_validation.get('parse_ok') else 'FAIL'}\n"
            f"✓ Package integrity: {'PASS' if package_ok else 'FAIL'}\n"
            f"✓ Original source files preserved; no new photos captured\n"
            f"✓ Runtime compatibility and image-quality superiority: NOT VERIFIED\n"
            f"Project time: total historical hands-on hours were not previously logged; this run's measured audit/build time: {time_report['run_seconds']:.2f}s. Cumulative logged time: {time_report['total_logged']}.\n\n"
            f"Attachments: V10_Final.xml, V10_Final_Package.zip, V10_Validation_Report.md.\n"
            f"Status: {status}")
    (run_dir / "Telegram_Post_Draft.md").write_text(post + "\n", encoding="utf-8")

    # Camera deletion happens only after full inventory report exists, exact target checks pass.
    if args.delete_camera_images:
        # Safety: require target was inventoryable and every path remained inside exact target.
        if not camera_report.get("exists") or "error" in camera_report:
            print("CAMERA CLEANUP NOT PERFORMED: target validation failed; see Camera_Cleanup_Inventory.json")
        else:
            print(f"CAMERA CLEANUP: deleted={len(camera_report.get('deleted', []))}; remaining={camera_report.get('remaining_image_count_after')}; errors={len(camera_report.get('delete_errors', []))}")

    publish_result = {"requested": bool(args.publish), "status": "not requested"}
    if args.publish:
        try:
            if not xml_validation.get("parse_ok"): raise RuntimeError("XML syntax check failed; publication blocked")
            if not package_ok: raise RuntimeError("Package integrity check failed; publication blocked")
            publish_result = send_telegram(release, zip_path, release / "V10_Validation_Report.md", post, args.chat_id)
            publish_result["status"] = "success"
        except Exception as e:
            publish_result = {"requested": True, "status": "failed or blocked", "reason": str(e)}
        write_json(run_dir / "Telegram_Publication_Result.json", publish_result)
    else:
        write_json(run_dir / "Telegram_Publication_Result.json", publish_result)

    # Re-finalize checksums/report after status result is generated; it is kept outside release package.
    print("\n=== DCIM Calibration Master Result ===")
    print(f"Project root: {root}")
    print(f"Source ZIP: {source_zip if source_zip else 'not found'}")
    print(f"V9 baseline found: {baseline_found}")
    print(f"Source profile: {source_profile['filename'] if source_profile else 'none'}")
    print(f"Release status: {status}")
    print(f"XML parse: {'PASS' if xml_validation.get('parse_ok') else 'FAIL'}")
    print(f"ZIP integrity + embedded SHA-256: {'PASS' if package_ok else 'FAIL'}")
    print(f"Logged project effort: {time_report['total_logged']} (prior unlogged work unknown)")
    print(f"Release folder: {release}")
    print(f"Release ZIP: {zip_path}")
    print(f"Telegram post draft: {run_dir / 'Telegram_Post_Draft.md'}")
    print(f"Camera inventory: {run_dir / 'Camera_Cleanup_Inventory.json'}")
    print(f"Telegram: {publish_result.get('status')}")
    print("No photos captured; no camera test session started.")

    if args.serve_api:
        api_server(root, args.api_port)
    return 0 if package_ok and xml_validation.get("parse_ok") else 2

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Interrupted. No photos were captured.", file=sys.stderr)
        sys.exit(130)
