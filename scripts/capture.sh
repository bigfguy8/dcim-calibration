#!/usr/bin/env bash
# capture.sh - automated test-chart capture for MGC 8.9 (BSG) on LXX521 / IMX682.
#
# Device mode (default when `adb` is available and a device is authorised):
#   Creates /sdcard/DCIM/calib/<session_id>/, launches MGC, fires the shutter
#   for every slot x frame, and writes session.json + capture.log next to the
#   frames.
#
# Local / adb-optional mode (--local, or automatically when adb is missing):
#   Imports frames from --source (or $CALIB_LOCAL_SOURCE) into
#   analysis_results/<session_id>/incoming/ so analyze.py and report.py can run
#   on a host without ADB.
#
# ISO is recorded from EXIF after capture. MGC exposes no shell API for ISO
# selection, so an optional --iso-command template can drive the UI between
# steps (e.g. 'input tap 540 2100'); otherwise set ISO manually per step.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION_ID="${CALIB_SESSION_ID:-$(date +%Y%m%d_%H%M%S)}"
ISO_LIST="${CALIB_ISO_LIST:-100 400 800 1600 3200}"
SLOTS="${CALIB_SLOTS:-center edge}"
FRAMES="${CALIB_FRAMES:-3}"
PROFILE="${CALIB_PROFILE:-TEX}"
CAMERA="${CALIB_CAMERA:-back_main}"
DEVICE_ROOT="${CALIB_DEVICE_ROOT:-/sdcard/DCIM/calib}"
LOCAL_ROOT="${CALIB_LOCAL_ROOT:-${REPO_ROOT}/analysis_results}"
MGC_PACKAGE="${MGC_PACKAGE:-com.agc.gcam89}"
MGC_ACTIVITY="${MGC_ACTIVITY:-com.google.android.apps.camera.gcam.CameraActivity}"
SHUTTER_KEY="${MGC_SHUTTER_KEY:-27}"
ISO_COMMAND="${CALIB_ISO_COMMAND:-}"
ADB="${ADB:-adb}"

MODE="auto"
SOURCE=""
AUTO=0
SKIP_LAUNCH=0
DO_RAW=1

usage() {
    cat <<'USAGE'
Usage: scripts/capture.sh [options]

  --session ID        session id (default: timestamp)
  --iso "LIST"        space-separated ISO ladder (default: 100 400 800 1600 3200)
  --slots "LIST"      framing targets (default: center edge)
  --frames N          frames per slot/ISO step (default: 3)
  --profile NAME      profile label written to session.json (default: TEX)
  --camera NAME       camera label (default: back_main)
  --local             force local import mode
  --device            force device mode (fails if adb is unavailable)
  --source DIR        local import source (local mode)
  --no-raw            record that RAW capture is disabled
  --no-launch         do not launch MGC
  --auto              no interactive "frame the chart" prompts

Environment: ADB, MGC_PACKAGE, MGC_ACTIVITY, MGC_SHUTTER_KEY,
             CALIB_DEVICE_ROOT, CALIB_LOCAL_ROOT, CALIB_LOCAL_SOURCE,
             CALIB_ISO_COMMAND
USAGE
}

die() { echo "[-] $*" >&2; exit 1; }
log() { echo "[*] $*"; }
warn() { echo "[!] $*" >&2; }

while [ "$#" -gt 0 ]; do
    case "$1" in
        --session) SESSION_ID="$2"; shift 2 ;;
        --iso) ISO_LIST="$2"; shift 2 ;;
        --slots) SLOTS="$2"; shift 2 ;;
        --frames) FRAMES="$2"; shift 2 ;;
        --profile) PROFILE="$2"; shift 2 ;;
        --camera) CAMERA="$2"; shift 2 ;;
        --local) MODE="local"; shift ;;
        --device) MODE="device"; shift ;;
        --source) SOURCE="$2"; shift 2 ;;
        --no-raw) DO_RAW=0; shift ;;
        --no-launch) SKIP_LAUNCH=1; shift ;;
        --auto) AUTO=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) die "unknown argument: $1" ;;
    esac
done

[ -n "${SOURCE}" ] || SOURCE="${CALIB_LOCAL_SOURCE:-}"

adb_ready() {
    command -v "${ADB}" >/dev/null 2>&1 || return 1
    "${ADB}" get-state 2>/dev/null | grep -q '^device$'
}

if [ "$MODE" = "auto" ]; then
    if adb_ready; then
        MODE="device"
    else
        MODE="local"
    fi
fi

write_session_json() {
    local destination="$1"
    local payload="$2"
    if [ "${payload}" = "device" ]; then
        printf '%s\n' "${SESSION_JSON}" | "${ADB}" shell "cat > '${destination}/session.json'"
    else
        mkdir -p "${destination}"
        printf '%s\n' "${SESSION_JSON}" > "${destination}/session.json"
    fi
}

build_session_json() {
    SESSION_JSON="$(python3 - "$SESSION_ID" "$PROFILE" "$CAMERA" "$MODE" \
        "$ISO_LIST" "$SLOTS" "$FRAMES" "$DO_RAW" "$MGC_PACKAGE" <<'PY'
import json, sys
session, profile, camera, mode, iso, slots, frames, raw, package = sys.argv[1:]
print(json.dumps({
    "schema_version": 1,
    "session_id": session,
    "profile": profile,
    "camera": camera,
    "mode": mode,
    "application": {"package": package, "version": "MGC 8.9 (BSG)"},
    "device": {"model": "LXX521", "sensor": "Sony IMX682"},
    "intended_iso": [int(x) for x in iso.split()],
    "slots": slots.split(),
    "frames_per_step": int(frames),
    "raw_enabled": raw == "1",
}, indent=2))
PY
)"
}

prompt_slot() {
    local slot="$1" iso="$2"
    [ "$AUTO" -eq 1 ] && return 0
    if [ -t 0 ]; then
        printf '[?] Frame the chart for slot=%s iso=%s, then press Enter ' "$slot" "$iso"
        read -r _ || true
    fi
}

apply_iso() {
    local iso="$1"
    [ -n "${ISO_COMMAND}" ] || return 0
    local cmd="${ISO_COMMAND//\{iso\}/${iso}}"
    log "ISO hook: ${cmd}"
    "${ADB}" shell "${cmd}" >/dev/null || warn "ISO hook failed for ${iso}"
    sleep 1
}

# --------------------------------------------------------------------------- #
# Device mode
# --------------------------------------------------------------------------- #
run_device() {
    log "mode=device session=${SESSION_ID}"
    local target="${DEVICE_ROOT}/${SESSION_ID}"
    local before after
    build_session_json

    "${ADB}" shell "mkdir -p '${target}'" || die "cannot create ${target} on device"
    write_session_json "${target}" device
    log "session directory: ${target}"

    if [ "$SKIP_LAUNCH" -eq 0 ]; then
        log "launching ${MGC_PACKAGE}"
        "${ADB}" shell "am start -n '${MGC_PACKAGE}/${MGC_ACTIVITY}'" >/dev/null 2>&1 \
            || "${ADB}" shell "monkey -p '${MGC_PACKAGE}' -c android.intent.category.LAUNCHER 1" >/dev/null 2>&1 \
            || warn "could not launch ${MGC_PACKAGE}; continuing"
        sleep 4
    fi

    local total=0
    for iso in ${ISO_LIST}; do
        apply_iso "${iso}"
        for slot in ${SLOTS}; do
            prompt_slot "${slot}" "${iso}"
            before="$("${ADB}" shell "ls -1 '${target}' 2>/dev/null | wc -l" | tr -d '\r ')"
            for frame in $(seq 1 "${FRAMES}"); do
                log "capture slot=${slot} iso=${iso} frame=${frame}/${FRAMES}"
                "${ADB}" shell "input keyevent ${SHUTTER_KEY}" >/dev/null 2>&1 \
                    || warn "shutter keyevent ${SHUTTER_KEY} failed"
                sleep 2
            done
            sleep 3
            after="$("${ADB}" shell "ls -1 '${target}' 2>/dev/null | wc -l" | tr -d '\r ')"
            if [ "${after:-0}" -le "${before:-0}" ]; then
                warn "no new files detected for slot=${slot} iso=${iso}; check shutter key / MGC save path"
            else
                total=$((total + after - before))
            fi
        done
    done

    log "captured ${total} new file(s) into ${target}"
    [ "${total}" -gt 0 ] || die "capture produced no files"
    log "next: ./scripts/pull.sh ${SESSION_ID}"
}

# --------------------------------------------------------------------------- #
# Local / adb-optional mode
# --------------------------------------------------------------------------- #
run_local() {
    log "mode=local session=${SESSION_ID}"
    local destination="${LOCAL_ROOT}/${SESSION_ID}/incoming"
    build_session_json
    mkdir -p "${destination}"
    write_session_json "${LOCAL_ROOT}/${SESSION_ID}" local
    log "session directory: ${LOCAL_ROOT}/${SESSION_ID}"

    [ -n "${SOURCE}" ] || die "local mode needs --source DIR (or CALIB_LOCAL_SOURCE); adb is unavailable"
    [ -d "${SOURCE}" ] || die "source directory not found: ${SOURCE}"

    local copied=0
    while IFS= read -r -d '' file; do
        cp -p "${file}" "${destination}/" || warn "failed to copy ${file}"
        copied=$((copied + 1))
    done < <(find "${SOURCE}" -maxdepth 2 -type f \
        \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.dng' -o -iname '*.png' \) -print0)

    [ "${copied}" -gt 0 ] || die "no JPEG/DNG assets found in ${SOURCE}"
    log "imported ${copied} file(s) into ${destination}"
    log "next: ./scripts/pull.sh ${SESSION_ID} --from '${LOCAL_ROOT}/${SESSION_ID}'"
}

case "$MODE" in
    device) adb_ready || die "device mode requested but adb/device is unavailable"; run_device ;;
    local) run_local ;;
    *) die "invalid mode: ${MODE}" ;;
esac
