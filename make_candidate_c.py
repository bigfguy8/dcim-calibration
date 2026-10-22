import xml.etree.ElementTree as ET
from pathlib import Path
import hashlib
import shutil

base = Path(
    "analysis_results/imx682_config/"
    "allrounder/default_working_backup.xml"
)

out = Path(
    "analysis_results/v8_audit_20261020_211620/"
    "LXX521_IMX682_V8_Candidate_C_BalancedDetail.xml"
)

download = Path.home() / "storage/shared/Download"
download.mkdir(parents=True, exist_ok=True)

if not base.is_file():
    raise SystemExit(f"Baseline not found: {base}")

tree = ET.parse(base)
root = tree.getroot()

if root.tag != "map":
    raise SystemExit(f"Unexpected XML root: {root.tag}")

entries = {}
for e in root.iter("string"):
    name = e.get("name")
    if name:
        if name in entries:
            raise SystemExit(f"Duplicate key: {name}")
        entries[name] = e

# Conservative experiment: main-camera processing keys only.
# Do not change other lens IDs, sensor calibration, or resolution.
changes = {
    "lib_sharpgain_key": "1",
    "lib_sharpmini_key": "1",
    "lib_sharpnessb_key": "1",
    "lib_denoise_key": "1",
    "lib_lumadenoise_key": "1",
    "lib_lumanoise_key": "1",
}

missing = [k for k in changes if k not in entries]
if missing:
    raise SystemExit(f"Required keys absent; no file written: {missing}")

before = {k: entries[k].text for k in changes}

for key, value in changes.items():
    entries[key].text = value

out.parent.mkdir(parents=True, exist_ok=True)
tree.write(out, encoding="utf-8", xml_declaration=True)

# Reopen and validate the generated XML.
check = ET.parse(out).getroot()
check_entries = {
    e.get("name"): e.text
    for e in check.iter("string")
    if e.get("name")
}

if len(check_entries) != len(entries):
    out.unlink(missing_ok=True)
    raise SystemExit("Validation failed: key count changed")

for key, value in changes.items():
    if check_entries.get(key) != value:
        out.unlink(missing_ok=True)
        raise SystemExit(f"Validation failed: {key}")

target = download / out.name
shutil.copy2(out, target)

digest = hashlib.sha256(target.read_bytes()).hexdigest()

print("Candidate C created and validated.")
print(f"Keys preserved: {len(check_entries)}")
print("Changed values:")
for key, value in changes.items():
    print(f"  {key}: {before[key]!r} -> {value!r}")
print(f"File: {target}")
print(f"SHA256: {digest}")
