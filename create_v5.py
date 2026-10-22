from pathlib import Path
import xml.etree.ElementTree as ET
import shutil

base = Path.home() / "dcim_calibration"
source = base / "profiles/LXX521_IMX682_Super_AllInOne_V4.xml"
name = "LXX521_IMX682_Super_AllInOne_V5_BalancedLowLight.xml"
output = base / "profiles" / name
destination = Path("/sdcard/LMC8.4") / name

if not source.is_file():
    raise SystemExit(f"Missing source profile: {source}")

if output.exists() or destination.exists():
    raise SystemExit("V5 already exists; nothing overwritten. Inspect or rename it first.")

text = source.read_text(encoding="utf-8")
changes = {
    "LXX521_IMX682_Super_AllInOne_V4": "LXX521_IMX682_Super_AllInOne_V5_BalancedLowLight",
    '<string name="ptchr_sharpness_0">1.18</string>':
        '<string name="ptchr_sharpness_0">1.10</string>',
    '<string name="ptchr_contrast_0">1.03</string>':
        '<string name="ptchr_contrast_0">1.00</string>',
    '<string name="ptchr_saturation_0">1.01</string>':
        '<string name="ptchr_saturation_0">0.97</string>',
    '<string name="ptchr_luma_denoise_0">1.00</string>':
        '<string name="ptchr_luma_denoise_0">1.05</string>',
    '<string name="ptchr_chroma_denoise_0">1.18</string>':
        '<string name="ptchr_chroma_denoise_0">1.22</string>',
}
for old, new in changes.items():
    if old not in text:
        raise SystemExit(f"Expected V4 setting not found; aborting: {old}")
    text = text.replace(old, new, 1)

output.write_text(text, encoding="utf-8")
root = ET.parse(output).getroot()
keys = [e.attrib.get("name") for e in root.findall("string")]
duplicates = sorted(k for k in set(keys) if k and keys.count(k) > 1)

if root.tag != "map" or duplicates:
    output.unlink(missing_ok=True)
    raise SystemExit(f"Validation failed: root={root.tag}, duplicates={duplicates}")

destination.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(output, destination)

if output.read_bytes() != destination.read_bytes():
    raise SystemExit("Copy verification failed; keep using V4.")

print("V5 created and copied; not activated.")
print("Entries:", len(keys))
print("Source:", output)
print("Destination:", destination)
print("Copy verification: PASS")
