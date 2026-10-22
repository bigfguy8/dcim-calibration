from pathlib import Path
from datetime import datetime
import hashlib
import xml.etree.ElementTree as ET
import sys

ROOT = Path.home() / "dcim_calibration"
SOURCE = ROOT / "profiles" / "LXX521_IMX682_LMC84_AllRounder.xml"
DEST_DIR = Path.home() / "storage" / "shared" / "LMC8.4"

BASE_NAME = "LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED.xml"
STATUS_LABEL = "BASELINE_COPY_UNTUNED_NOT_DEVICE_VALIDATED"

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def fail(message):
    print(f"ERROR: {message}")
    raise SystemExit(1)

print("=== DCIM CALIBRATION: V10 → LMC8.4 ===")

if not SOURCE.is_file() or SOURCE.stat().st_size == 0:
    fail(f"Source profile missing or empty: {SOURCE}")

source_data = SOURCE.read_bytes()

try:
    root = ET.fromstring(source_data)
except ET.ParseError as exc:
    fail(f"Invalid source XML: {exc}")

if root.tag != "map":
    fail(f"Unexpected XML root: <{root.tag}>")

entries = root.findall("string")
keys = [entry.get("name") for entry in entries]

if any(not key for key in keys):
    fail("A direct string entry has no name")

if len(keys) != len(set(keys)):
    fail("Duplicate direct string keys found")

source_hash = sha256(source_data)

try:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    probe = DEST_DIR / ".dcim_write_test"
    probe.write_text("test", encoding="utf-8")
    probe.unlink()
except OSError as exc:
    fail(f"Cannot write to LMC8.4 folder: {exc}")

candidate = DEST_DIR / BASE_NAME
stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
suffix = 0

while True:
    status_path = candidate.with_suffix(".status.md")

    if candidate.exists():
        if candidate.is_file():
            try:
                existing_hash = sha256(candidate.read_bytes())
                ET.parse(candidate)
            except (OSError, ET.ParseError):
                existing_hash = ""

            if existing_hash == source_hash:
                if not status_path.exists():
                    # Same XML exists; create the missing status report.
                    break

                try:
                    old_status = status_path.read_text(encoding="utf-8")
                except OSError:
                    old_status = ""

                if (
                    f"Source SHA-256: `{source_hash}`" in old_status
                    and f"Config SHA-256: `{source_hash}`" in old_status
                    and STATUS_LABEL in old_status
                ):
                    print("Existing V10 config is already up to date.")
                    print(f"CONFIG={candidate}")
                    print(f"STATUS_FILE={status_path}")
                    print(f"SHA256={source_hash}")
                    print("XML_PARSE=PASS")
                    print(f"STATUS={STATUS_LABEL}")
                    sys.exit(0)

    elif not status_path.exists():
        break

    suffix += 1
    extra = f"_{suffix}" if suffix > 1 else ""
    candidate = DEST_DIR / (
        f"LXX521_IMX682_LMC84_V10_Baseline_UNVALIDATED_"
        f"{stamp}{extra}.xml"
    )

# Never overwrite an existing config.
if not candidate.exists():
    try:
        with candidate.open("xb") as f:
            f.write(source_data)
    except OSError as exc:
        fail(f"Could not create config: {exc}")

try:
    output_data = candidate.read_bytes()
    ET.parse(candidate)
except (OSError, ET.ParseError) as exc:
    fail(f"Output validation failed: {exc}")

output_hash = sha256(output_data)

if output_hash != source_hash:
    fail("Source/output checksum mismatch")

created = datetime.now().astimezone().isoformat(timespec="seconds")

status_text = f"""# LXX521 / Sony IMX682 — V10 Config Status

- Status: `{STATUS_LABEL}`
- Created: `{created}`
- Source: `{SOURCE}`
- Config: `{candidate}`
- Source SHA-256: `{source_hash}`
- Config SHA-256: `{output_hash}`
- XML parsing: PASS
- XML root: `<{root.tag}>`
- Direct string entries: {len(entries)}
- Duplicate direct string keys: 0
- Tuning changes: none; exact source copy.
- Device validation: NOT PERFORMED.

This file is a baseline candidate, not a tuned or
device-validated calibration profile.
"""

if not status_path.exists():
    try:
        with status_path.open("x", encoding="utf-8") as f:
            f.write(status_text)
    except OSError as exc:
        fail(f"Config saved, but status report could not be written: {exc}")

# Final verification
if sha256(SOURCE.read_bytes()) != sha256(candidate.read_bytes()):
    fail("Final source/config verification failed")

print("\n=== V10 CONFIG SAVED ===")
print(f"CONFIG={candidate}")
print(f"STATUS_FILE={status_path}")
print(f"SOURCE_SHA256={source_hash}")
print(f"CONFIG_SHA256={output_hash}")
print(f"XML_PARSE=PASS; STRING_ENTRIES={len(entries)}")
print("TUNING_CHANGES=0")
print(f"STATUS={STATUS_LABEL}")
