#!/usr/bin/env bash
# pull.sh - synchronise a capture session from the device (or a local import)
# and verify asset integrity.
#
# Source:
#   device : /sdcard/DCIM/calib/<session_id>/   (adb pull)
#   local  : --from DIR                        (cp -a, adb not required)
#
# Destination (default): analysis_results/<session_id>/device/
#
# Integrity verification:
#   * every file must be non-empty and readable
#   * SHA-256 manifest written as MANIFEST.sha256
#   * optional DNG/JPG pairing check (--require-raw)
#   * summary written as integrity.json
#
# Exit status: 0 when all checks pass, 1 when any asset fails verification,
# 2 on usage/transport errors.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION_ID=""
SOURCE=""
DEST=""
DEVICE_ROOT="${CALIB_DEVICE_ROOT:-/sdcard/DCIM/calib}"
LOCAL_ROOT="${CALIB_LOCAL_ROOT:-${REPO_ROOT}/analysis_results}"
ADB="${ADB:-adb}"
REQUIRE_RAW=0
VERIFY_ONLY=0

usage() {
    cat <<'USAGE'
Usage: scripts/pull.sh <session_id> [options]

  --from DIR       copy from a local session directory instead of adb
  --dest DIR       destination directory (default: analysis_results/<id>/device)
  --require-raw    fail if a JPEG has no matching DNG
  --verify-only    re-verify an existing MANIFEST.sha256, no copy

Environment: ADB, CALIB_DEVICE_ROOT, CALIB_LOCAL_ROOT
USAGE
}

die() { echo "[-] $*" >&2; exit 2; }
warn() { echo "[!] $*" >&2; }
log() { echo "[*] $*"; }

while [ "$#" -gt 0 ]; do
    case "$1" in
        --from) SOURCE="$2"; shift 2 ;;
        --dest) DEST="$2"; shift 2 ;;
        --require-raw) REQUIRE_RAW=1; shift ;;
        --verify-only) VERIFY_ONLY=1; shift ;;
        -h|--help) usage; exit 0 ;;
        -*) die "unknown option: $1" ;;
        *) [ -z "${SESSION_ID}" ] || die "session id already set"; SESSION_ID="$1"; shift ;;
    esac
done

[ -n "${SESSION_ID}" ] || die "session id is required"
[ -n "${DEST}" ] || DEST="${LOCAL_ROOT}/${SESSION_ID}/device"

hash_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        die "no sha256 tool (sha256sum/shasum) available"
    fi
}

verify_only() {
    local manifest="${DEST}/MANIFEST.sha256"
    [ -f "${manifest}" ] || die "manifest not found: ${manifest}"
    if command -v sha256sum >/dev/null 2>&1; then
        ( cd "${DEST}" && sha256sum -c MANIFEST.sha256 )
    else
        ( cd "${DEST}" && shasum -a 256 -c MANIFEST.sha256 )
    fi || die "integrity verification failed"
    log "manifest verified: ${manifest}"
}

if [ "${VERIFY_ONLY}" -eq 1 ]; then
    verify_only
    exit 0
fi

# --------------------------------------------------------------------------- #
# Acquire assets
# --------------------------------------------------------------------------- #
mkdir -p "${DEST}"

if [ -n "${SOURCE}" ]; then
    [ -d "${SOURCE}" ] || die "source directory not found: ${SOURCE}"
    log "local sync: ${SOURCE} -> ${DEST}"
    # Copy image assets only; prune DEST so a nested destination cannot recurse.
    while IFS= read -r -d '' file; do
        rel="${file#"${SOURCE}/"}"
        mkdir -p "${DEST}/$(dirname "${rel}")"
        cp -p "${file}" "${DEST}/${rel}" || die "failed to copy ${rel}"
    done < <(find "${SOURCE}" -path "${DEST}" -prune -o -type f \
        \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.dng' \
           -o -iname '*.png' -o -iname '*.tif' -o -iname '*.tiff' \) -print0)
else
    command -v "${ADB}" >/dev/null 2>&1 || die "adb not found; use --from DIR for local mode"
    "${ADB}" get-state 2>/dev/null | grep -q '^device$' || die "no authorised adb device"
    remote="${DEVICE_ROOT}/${SESSION_ID}"
    log "adb pull: ${remote}/ -> ${DEST}/"
    "${ADB}" pull "${remote}/." "${DEST}/" || die "adb pull failed for ${remote}"
fi

# --------------------------------------------------------------------------- #
# Verify integrity
# --------------------------------------------------------------------------- #
problems=0
count_jpg=0
count_dng=0
count_other=0
count_image=0
total_bytes=0
manifest_tmp="$(mktemp "${DEST}/.manifest.XXXXXX")"
json_tmp="$(mktemp "${DEST}/.integrity.XXXXXX")"

: > "${manifest_tmp}"

while IFS= read -r -d '' file; do
    rel="${file#"${DEST}/"}"
    case "${rel}" in
        MANIFEST.sha256|integrity.json|session.json|capture.log|.manifest.*|.integrity.*) continue ;;
    esac
    size="$(wc -c < "${file}" | tr -d ' ')"
    if [ "${size:-0}" -le 0 ]; then
        warn "zero-byte asset: ${rel}"
        problems=$((problems + 1))
        continue
    fi
    digest="$(hash_file "${file}")" || { warn "hashing failed: ${rel}"; problems=$((problems + 1)); continue; }
    printf '%s  %s\n' "${digest}" "${rel}" >> "${manifest_tmp}"
    total_bytes=$((total_bytes + size))
    case "${rel,,}" in
        *.jpg|*.jpeg) count_jpg=$((count_jpg + 1)); count_image=$((count_image + 1)) ;;
        *.dng) count_dng=$((count_dng + 1)); count_image=$((count_image + 1)) ;;
        *.png|*.tif|*.tiff|*.webp|*.bmp) count_other=$((count_other + 1)); count_image=$((count_image + 1)) ;;
        *) count_other=$((count_other + 1)) ;;
    esac
done < <(find "${DEST}" -type f -print0 | sort -z)

if [ "${count_image}" -eq 0 ]; then
    warn "no image assets (JPEG/DNG/PNG/TIFF) found in ${DEST}"
    problems=$((problems + 1))
fi

if [ "${REQUIRE_RAW}" -eq 1 ]; then
    while IFS= read -r -d '' jpg; do
        base="${jpg%.*}"
        [ -f "${base}.dng" ] || { warn "missing RAW pair for $(basename "${jpg}")"; problems=$((problems + 1)); }
    done < <(find "${DEST}" -type f \( -iname '*.jpg' -o -iname '*.jpeg' \) -print0)
fi

mv "${manifest_tmp}" "${DEST}/MANIFEST.sha256"
if [ "${problems}" -eq 0 ]; then status="pass"; else status="fail"; fi

python3 - "${DEST}/integrity.json" "${SESSION_ID}" "${SOURCE:-${DEVICE_ROOT}/${SESSION_ID}}" \
    "${DEST}" "${count_jpg}" "${count_dng}" "${count_other}" "${total_bytes}" "${status}" <<'PY'
import json, sys
from datetime import datetime, timezone
out, session, source, dest, jpg, dng, other, total, status = sys.argv[1:]
json.dump({
    "schema_version": 1,
    "session_id": session,
    "source": source,
    "destination": dest,
    "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "counts": {"jpeg": int(jpg), "dng": int(dng), "other": int(other)},
    "total_bytes": int(total),
    "status": status,
    "manifest": "MANIFEST.sha256",
}, open(out, "w"), indent=2)
print()
PY

log "assets: ${count_jpg} JPEG, ${count_dng} DNG, ${count_other} other (${total_bytes} bytes)"
log "manifest: ${DEST}/MANIFEST.sha256"
log "integrity: ${status}"

if [ "${problems}" -ne 0 ]; then
    echo "[-] ${problems} integrity problem(s) detected" >&2
    exit 1
fi
log "next: python3 scripts/analyze.py '${DEST}' --recursive"
