#!/usr/bin/env bash
# deploy_profiles.sh - enforce the two-profile mandate on the MGC storage path.
#
# Only LXX521_TEX.xml and LXX521_AI.xml are permitted as active profiles in
# the destination directory. Any other *.xml found there is moved to
# <dest>/archive/<timestamp>/ (never deleted) when --prune is used.
#
# Works over adb (device path) or directly on the filesystem (Termux shared
# storage / local staging directory).
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
XML_DIR="${CALIB_XML_DIR:-${REPO_ROOT}/configs/xml}"
DEST="${CALIB_LMC_DIR:-${DCIM_LMC_DIR:-}}"
ADB="${ADB:-adb}"
PRUNE=0
DRY_RUN=0
FORCE_LOCAL=0
FORCE_SOURCE_OVERLAP=0

ACTIVE=("LXX521_TEX.xml" "LXX521_AI.xml")

usage() {
    cat <<'USAGE'
Usage: scripts/deploy_profiles.sh [options]

  --dest DIR     destination (required; or set CALIB_LMC_DIR)
  --prune        archive any non-mandated *.xml in DEST before deploying
  --local        force direct filesystem access (no adb)
  --dry-run      print the plan, change nothing
  --force-source-overlap allow pruning into a registered `live` source path

Environment: ADB, CALIB_XML_DIR, CALIB_LMC_DIR / DCIM_LMC_DIR
USAGE
}

die() { echo "[-] $*" >&2; exit 2; }
log() { echo "[*] $*"; }
warn() { echo "[!] $*" >&2; }

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dest) DEST="$2"; shift 2 ;;
        --prune) PRUNE=1; shift ;;
        --local) FORCE_LOCAL=1; shift ;;
        --dry-run) DRY_RUN=1; shift ;;
        --force-source-overlap) FORCE_SOURCE_OVERLAP=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) die "unknown option: $1" ;;
    esac
done

case "${DEST}" in
    /|/sdcard|/storage|/data|/system|/vendor|/mnt) die "refusing unsafe destination: ${DEST}" ;;
esac
[ -n "${DEST}" ] || die "no destination: pass --dest or set CALIB_LMC_DIR"

# --------------------------------------------------------------------------- #
# Transport selection
# --------------------------------------------------------------------------- #
USE_ADB=0
if [ "${FORCE_LOCAL}" -eq 0 ] && [ "${DEST#/sdcard}" != "${DEST}" ]; then
    if command -v "${ADB}" >/dev/null 2>&1 && "${ADB}" get-state 2>/dev/null | grep -q '^device$'; then
        USE_ADB=1
    fi
fi

dest_mkdir() {
    if [ "${USE_ADB}" -eq 1 ]; then "${ADB}" shell "mkdir -p '$1'" >/dev/null
    else mkdir -p "$1"; fi
}
dest_ls_xml() {
    if [ "${USE_ADB}" -eq 1 ]; then "${ADB}" shell "ls -1 '$1'/*.xml 2>/dev/null"
    else find "$1" -maxdepth 1 -type f -name '*.xml' -print 2>/dev/null; fi
}
dest_copy() {
    if [ "${USE_ADB}" -eq 1 ]; then "${ADB}" push "$1" "$2/" >/dev/null
    else cp -p "$1" "$2/"; fi
}
dest_move() {
    if [ "${USE_ADB}" -eq 1 ]; then "${ADB}" shell "mv '$1' '$2/'" >/dev/null
    else mv "$1" "$2/"; fi
}

transport="filesystem"
[ "${USE_ADB}" -eq 1 ] && transport="adb"
log "destination: ${DEST} (${transport})"

# --------------------------------------------------------------------------- #
# Validate sources
# --------------------------------------------------------------------------- #
for name in "${ACTIVE[@]}"; do
    profile="${XML_DIR}/${name}"
    [ -f "${profile}" ] || die "missing active profile: ${profile}"
    python3 - "${profile}" <<'PY' || die "invalid profile: ${profile}"
import sys, xml.etree.ElementTree as ET
path = sys.argv[1]
root = ET.parse(path).getroot()
assert root.tag == "map", f"root is <{root.tag}>, expected <map>"
assert len(root) >= 100, f"only {len(root)} keys"
PY
done
log "validated ${#ACTIVE[@]} active profile(s)"
[ "${DRY_RUN}" -eq 1 ] && log "dry-run: no changes will be written"

# --------------------------------------------------------------------------- #
# Deploy
# --------------------------------------------------------------------------- #
if [ "${DRY_RUN}" -eq 0 ]; then
    dest_mkdir "${DEST}" || die "cannot create ${DEST}"
fi

stamp="$(date +%Y%m%d_%H%M%S)"
archive="${DEST}/archive/${stamp}"
pruned=()

if [ "${PRUNE}" -eq 1 ]; then
    # Overlap guard: refuse to prune into a registered `live` source path
    # unless --force-source-overlap is given.
    # Read-only; skipped in dry-run so dry-run behavior is unchanged.
    if [ "${DRY_RUN}" -eq 0 ]; then
        OVERLAP_ARGS=(--path "${DEST}")
        [ "${FORCE_SOURCE_OVERLAP}" -eq 1 ] && OVERLAP_ARGS+=(--force-source-overlap)
        python3 "${REPO_ROOT}/scripts/sources.py" verify-overlap "${OVERLAP_ARGS[@]}" \
            || die "destination overlaps a registered live source; pass --force-source-overlap to override"
    fi
    while IFS= read -r remote; do
        [ -n "${remote}" ] || continue
        base="$(basename "${remote}")"
        skip=0
        for name in "${ACTIVE[@]}"; do
            [ "${base}" = "${name}" ] && skip=1
        done
        [ "${skip}" -eq 1 ] && continue
        log "prune -> archive/${stamp}/${base}"
        pruned+=("${base}")
        if [ "${DRY_RUN}" -eq 0 ]; then
            dest_mkdir "${archive}" || die "cannot create archive ${archive}"
            dest_move "${remote}" "${archive}" || warn "failed to archive ${base}"
        fi
    done < <(dest_ls_xml "${DEST}" | tr -d '\r')
fi

deployed=()
for name in "${ACTIVE[@]}"; do
    log "deploy ${name}"
    deployed+=("${name}")
    [ "${DRY_RUN}" -eq 1 ] && continue
    dest_copy "${XML_DIR}/${name}" "${DEST}" || die "failed to deploy ${name}"
done

# --------------------------------------------------------------------------- #
# Manifest
# --------------------------------------------------------------------------- #
if [ "${DRY_RUN}" -eq 0 ]; then
    python3 - "${DEST}/deploy_manifest.json" "${DEST}" "${transport}" \
        "${deployed[@]}" -- "${pruned[@]}" <<'PY'
import hashlib, json, os, sys
from datetime import datetime, timezone
out, dest, transport = sys.argv[1:4]
rest = sys.argv[4:]
split = rest.index("--") if "--" in rest else len(rest)
deployed = rest[:split]
pruned = rest[split + 1:] if split < len(rest) else []

def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

files = []
for name in deployed:
    path = os.path.join(dest, name)
    files.append({"name": name, "bytes": os.path.getsize(path), "sha256": sha(path)})

json.dump({
    "schema_version": 1,
    "deployed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "destination": dest,
    "transport": transport,
    "active_profiles": files,
    "archived": pruned,
}, open(out, "w"), indent=2)
PY
fi

log "deployed: ${deployed[*]}"
if [ "${#pruned[@]}" -gt 0 ]; then log "archived: ${pruned[*]}"; fi
if [ "${DRY_RUN}" -eq 0 ]; then log "manifest: ${DEST}/deploy_manifest.json"; fi

exit 0
