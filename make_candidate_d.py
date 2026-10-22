from pathlib import Path
import xml.etree.ElementTree as ET
import hashlib
import sys

src = Path(
    "analysis_results/imx682_config/"
    "allrounder/default_working_backup.xml"
)
out = Path(
    "analysis_results/v8_audit_20261020_211620/"
    "LXX521_IMX682_V8_Candidate_D_DetailTest.xml"
)

if not src.is_file():
    sys.exit(f"ERROR: Baseline not found: {src}")

# Preserve the original file and all XML entries.
tree = ET.parse(src)
root = tree.getroot()

if root.tag != "map":
    sys.exit(f"ERROR: Unexpected XML root: {root.tag}")

changes = {
    "lib_sharpgain_key": "1",
    "lib_sharpmini_key": "1",
    "lib_sharpnessb_key": "1",
}

elements = {}
for elem in root.iter("string"):
    name = elem.get("name")
    if name in changes:
        elements.setdefault(name, []).append(elem)

for key in changes:
    found = elements.get(key, [])
    if len(found) != 1:
        sys.exit(
            f"STOP: {key} occurs {len(found)} times; "
            "no output written. Inspect the baseline first."
        )

out.parent.mkdir(parents=True, exist_ok=True)

for key, value in changes.items():
    elements[key][0].text = value

tree.write(out, encoding="utf-8", xml_declaration=True)

# Reopen and verify the generated XML.
check = ET.parse(out).getroot()
verified = {
    e.get("name"): e.text
    for e in check.iter("string")
    if e.get("name") in changes
}
if verified != changes:
    out.unlink(missing_ok=True)
    sys.exit(f"ERROR: Verification failed: {verified}")

print("Candidate D created:", out)
print("Changes:", verified)
print("SHA256:", hashlib.sha256(out.read_bytes()).hexdigest())
print("XML validation: PASS")
print("Baseline modified: NO")
