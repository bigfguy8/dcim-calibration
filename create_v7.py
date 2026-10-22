import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

base = Path.home() / "dcim_calibration"
src = base / "profiles/LXX521_IMX682_Super_AllInOne_V6_NaturalDetail.xml"
out = base / "profiles/LXX521_IMX682_Super_AllInOne_V7_NaturalNight.xml"
backup_dir = base / "backups"
dest_dir = Path("/sdcard/LMC8.4")
dest = dest_dir / out.name

if not src.is_file():
    raise SystemExit(f"ERROR: Source profile not found: {src}")

tree = ET.parse(src)
root = tree.getroot()

if root.tag != "map":
    raise SystemExit(f"ERROR: Expected <map>, found <{root.tag}>")

entries = {}
for item in root.findall("string"):
    key = item.get("name")
    if not key:
        raise SystemExit("ERROR: String entry missing name")
    if key in entries:
        raise SystemExit(f"ERROR: Duplicate XML key: {key}")
    entries[key] = item

required = {
    "pref_config_nickname_key",
    "ptchr_sharpness_0",
    "ptchr_luma_denoise_0",
}
missing = required - entries.keys()
if missing:
    raise SystemExit(f"ERROR: Required keys missing: {sorted(missing)}")

backup_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(src, backup_dir / f"{src.stem}_{stamp}.xml.bak")

# Keep all other V6 settings unchanged.
entries["pref_config_nickname_key"].text = (
    "LXX521_IMX682_Super_AllInOne_V7_NaturalNight"
)
entries["ptchr_sharpness_0"].text = "1.06"
entries["ptchr_luma_denoise_0"].text = "1.08"

ET.indent(tree, space="  ")
tree.write(out, encoding="utf-8", xml_declaration=True)

# Validate generated XML and key values.
check_tree = ET.parse(out)
check_root = check_tree.getroot()
check = {
    e.get("name"): e.text
    for e in check_root.findall("string")
}
assert check["pref_config_nickname_key"] == (
    "LXX521_IMX682_Super_AllInOne_V7_NaturalNight"
)
assert check["ptchr_sharpness_0"] == "1.06"
assert check["ptchr_luma_denoise_0"] == "1.08"
assert len(check) == len(check_root.findall("string"))

print("V7 created and XML validation passed.")
print("Source V6:", src)
print("Output V7:", out)
print("String entries:", len(check))
print("Sharpness:", check["ptchr_sharpness_0"])
print("Luma denoise:", check["ptchr_luma_denoise_0"])
print("Chroma denoise unchanged:", check["ptchr_chroma_denoise_0"])
print("V6 remains unchanged.")
print()
print("Review V7 before copying it to the phone.")
