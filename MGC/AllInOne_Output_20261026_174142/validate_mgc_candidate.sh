#!/data/data/com.termux/files/usr/bin/bash
# MGC AllInOne candidate — reproducible static validation (no camera runtime, no install)
# Re-runnable. Prints PASS/FAIL per check and exits non-zero on any FAIL.
set -u
HOME_="$HOME"
NATIVE="$HOME_/storage/shared/Download/MGC_CONFIG/9.4.103/mgc.xml"
HERE="$(cd "$(dirname "$0")" && pwd)"
CAND="$HERE/LXX521_MGC_AllInOne_CANDIDATE.xml"
NATIVE_SHA="911b27d929072bac13a86e354e20e27960ca2aabc7ddf2fbbcf4e63a3ec8c288"
FAILS=0
ok(){ echo "PASS  $1"; }
no(){ echo "FAIL  $1"; FAILS=$((FAILS+1)); }

# 1. Candidate exists
[ -f "$CAND" ] && ok "candidate file exists" || no "candidate file missing"

# 2. Candidate is byte-identical to the verified native source (unchanged restore)
if [ -f "$NATIVE" ]; then
  if cmp -s "$NATIVE" "$CAND"; then ok "candidate byte-identical to native source"; else no "candidate DIFFERS from native source"; fi
  native_sha=$(sha256sum "$NATIVE" | awk '{print $1}')
  [ "$native_sha" = "$NATIVE_SHA" ] && ok "native source SHA-256 matches expected" || no "native source SHA-256 CHANGED (expected $NATIVE_SHA, got $native_sha)"
else
  no "native source not found at $NATIVE"
fi

# 3. Candidate SHA-256 (record + must equal native for unchanged restore)
cand_sha=$(sha256sum "$CAND" | awk '{print $1}')
echo "INFO  candidate SHA-256 = $cand_sha"
[ "$cand_sha" = "$NATIVE_SHA" ] && ok "candidate SHA-256 equals native (unchanged)" || no "candidate SHA-256 differs from native"

# 4. XML well-formedness + structure + no duplicate keys
python3 - "$CAND" <<'PY' && ok "XML well-formed, root=<map>, 181 entries, 0 duplicate keys" \
   || no "XML structure check failed"
import sys, xml.etree.ElementTree as ET
from collections import Counter
r = ET.parse(sys.argv[1]).getroot()
assert r.tag == 'map', f"root is {r.tag}"
kids = list(r)
names = [c.get('name') for c in kids]
c = Counter(k.tag for k in kids)
assert len(names) == 181, f"expected 181 entries, got {len(names)}"
assert c == Counter({'string':175,'long':2,'int':2,'boolean':2}), f"type mix {dict(c)}"
assert len(names) == len(set(names)), "duplicate keys present"
PY

# 5. No exposure/iso/sensitivity/confinement keys (confirms crash not addressable via config)
if grep -qiE "exposure|iso|sensitive|sensitivity|confin|ae_" "$CAND"; then
  no "exposure/iso/sensitivity keys unexpectedly present"
else
  ok "no exposure/iso/sensitivity/confinement keys (crash is code-level, not config-level)"
fi

# 6. Front/rear routing keys intact
grep -q 'name="active_cam_id_front_key">1' "$CAND" && ok "front routing key = 1" || no "front routing key changed"
grep -q 'name="active_cam_id_back_key">0' "$CAND" && ok "rear routing key = 0" || no "rear routing key changed"

# 7. Rear-camera & HDR settings preserved (spot-check a few known native values)
for kv in 'name="pref_camera_hdr_plus_key">on' 'name="pref_video_resolution">RES_1080P' 'name="fix_saturation_key_0">1'; do
  grep -q "$kv" "$CAND" && ok "preserved: $kv" || no "missing/changed: $kv"
done

echo
echo "=== VALIDATION RESULT: $FAILS failure(s) ==="
exit $FAILS
