from pathlib import Path
import re
import shutil
import time
import xml.etree.ElementTree as ET

base = Path.home() / "dcim_calibration"
src = base / "profiles/LXX521_IMX682_Super_AllInOne_V5_BalancedLowLight.xml"
name = "LXX521_IMX682_Super_AllInOne_V6_NightIndoor"
out = base / "profiles" / f"{name}.xml"
dest_dir = Path("/sdcard/LMC8.4")
dest = dest_dir / out.name
backup_dir = base / "backups"

if not src.is_file():
    raise SystemExit(f"ERROR: V5 source not found: {src}")
if not dest_dir.is_dir():
    raise SystemExit(f"ERROR: Destination not found: {dest_dir}")

text = src.read_text(encoding="utf-8")

# Change only known V5 values; preserve the existing XML schema.
replacements = {
    "LXX521_IMX682_Super_AllInOne_V5_BalancedLowLight": name,
    "ptchr_sharpness_0": None,
    "ptchr_contrast_0": None,
    "ptchr_saturation_0": None,
    "ptchr_luma_denoise_0": None,
    "ptchr_chroma_denoise_0": None,
}

values = {
    "ptchr_sharpness_0": "1.12",
    "ptchr_contrast_0": "1.01",
    "ptchr_saturation_0": "0.99",
    "ptchr_luma_denoise_0": "1.03",
    "ptchr_chroma_denoise_0": "1.20",
}

for key, value in values.items():
    pattern = rf'(<string name="{re.escape(key)}">)[^<]*(</string>)'
    text, count = re.subn(pattern, rf'\g<1>{value}\g<2>', text)
    if count != 1:
        raise SystemExit(f"ERROR: Expected exactly one {key}, found {count}")

text = text.replace(
    "LXX521_IMX682_Super_AllInOne_V5_BalancedLowLight", name
)

root = ET.fromstring(text)
if root.tag != "map":
    raise SystemExit(f"ERROR: Unexpected XML root: {root.tag}")

entries = list(root)
keys = [
    e.attrib.get("name")
    for e in entries
    if e.tag == "string"
]
if len(entries) != 26 or len(keys) != len(set(keys)):
    raise SystemExit(
        f"ERROR: Structure check failed: {len(entries)} entries; "
        "duplicate or missing string keys may exist."
    )

# Confirm all intended values survived parsing.
parsed = {e.attrib.get("name"): e.text for e in entries}
for key, value in values.items():
    if parsed.get(key) != value:
        raise SystemExit(f"ERROR: Value validation failed for {key}")

out.parent.mkdir(parents=True, exist_ok=True)
if out.exists():
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"{out.name}.{int(time.time())}.bak"
    shutil.copy2(out, backup)
    print(f"Existing local V6 backed up: {backup}")

out.write_text(text, encoding="utf-8")

# Re-parse the file actually written.
ET.parse(out)

if dest.exists():
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"{dest.name}.{int(time.time())}.bak"
    shutil.copy2(dest, backup)
    print(f"Existing destination V6 backed up: {backup}")

shutil.copy2(out, dest)
if out.read_bytes() != dest.read_bytes():
    raise SystemExit("ERROR: Destination copy verification failed")

print("V6 created and copied; NOT activated.")
print(f"Entries: {len(entries)}")
print(f"Profile: {out}")
print(f"Destination: {dest}")
print("Copy verification: PASS")
print("Fine tuning:", values)
print("Black levels and frame counts retained from V5.")
