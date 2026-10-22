from pathlib import Path
import xml.etree.ElementTree as ET
import hashlib
import shutil

base = Path("analysis_results/imx682_config/allrounder")
source = base / "default_working_backup.xml"
outdir = Path("profiles")
output = outdir / "LXX521_IMX682_AllRounder_NaturalBalanced.xml"

if not source.is_file():
    raise SystemExit(f"STOP: source backup not found: {source}")

if output.exists():
    raise SystemExit(
        f"STOP: output already exists; refusing to overwrite: {output}"
    )

raw = source.read_bytes()
root = ET.fromstring(raw)

# Only tune keys whose exact names already exist.
# Preserve XML structure and original value types.
targets = {
    "pref_quality_key": "100",
    "pref_sharpness_key": "1.0",
    "pref_hdr_plus_frames_key": "9",
    "pref_luma_denoise_key": "1.0",
    "pref_chroma_denoise_key": "1.0",
    "pref_contrast_key": "1.0",
    "pref_shadow_brightness_key": "1.0",
}

nodes = {}
for node in root.iter():
    key = node.attrib.get("name")
    if key:
        nodes.setdefault(key, []).append(node)

duplicates = [k for k, v in nodes.items() if len(v) > 1]
if duplicates:
    raise SystemExit(
        "STOP: duplicate keys in source; no output written:\n"
        + "\n".join(duplicates)
    )

changed = []
skipped = []

for key, desired in targets.items():
    if key not in nodes:
        skipped.append(key)
        continue

    node = nodes[key][0]
    old = node.text or ""

    # Preserve boolean/integer/float/string representation.
    try:
        if old.lower() in ("true", "false"):
            value = desired.lower()
            if value not in ("true", "false"):
                skipped.append(key)
                continue
        elif old.strip().lstrip("-").isdigit():
            value = str(int(float(desired)))
        else:
            float(old)
            value = str(float(desired))
        if old != value:
            node.text = value
            changed.append((key, old, value))
    except (ValueError, TypeError):
        skipped.append(key)

outdir.mkdir(parents=True, exist_ok=True)
ET.indent(root, space=" ")
tree = ET.ElementTree(root)
tree.write(output, encoding="utf-8", xml_declaration=True)

# Verify output before reporting success.
check = ET.parse(output).getroot()
print("STATUS: CREATED AND XML-VALID")
print("SOURCE:", source)
print("OUTPUT:", output)
print("SOURCE SHA256:", hashlib.sha256(raw).hexdigest())
print("OUTPUT SHA256:", hashlib.sha256(output.read_bytes()).hexdigest())
print("ENTRY COUNT:", sum(1 for n in check.iter() if "name" in n.attrib))

print("\nCHANGED KEYS:")
for key, old, new in changed:
    print(f"  {key}: {old!r} -> {new!r}")
if not changed:
    print("  No supported target keys changed.")

print("\nKEYS NOT PRESENT OR NOT SAFELY TUNED:")
for key in skipped:
    print(" ", key)
if not skipped:
    print("  None")

print("\nNOTE: XML validity does not prove LMC compatibility or AF functionality.")
print("Original source and existing profiles were not overwritten.")
