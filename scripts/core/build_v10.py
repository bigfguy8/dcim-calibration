"""V10 baseline config builder.

Copies the texture-first source profile to the MGC storage directory as an
untuned, device-unvalidated baseline,
writing a matching .status.md report. Never overwrites an existing config.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from .logging import get_logger
from .paths import DEFAULT_MASTER, LMC_STORAGE_DIR
from .safety import check_deploy_target

logger = get_logger()

BASE_NAME = "LXX521_V10_Baseline_UNVALIDATED.xml"
STATUS_LABEL = "BASELINE_COPY_UNTUNED_NOT_DEVICE_VALIDATED"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(message: str) -> None:
    logger.error(message)
    raise SystemExit(1)


def build_v10_baseline(
    source: Path | str = DEFAULT_MASTER,
    dest_dir: Path | str | None = LMC_STORAGE_DIR,
) -> None:
    """Build the V10 baseline config in ``dest_dir``."""
    source = Path(source)
    if dest_dir is None:
        fail("No deploy directory configured; set CALIB_LMC_DIR")
    dest_dir = check_deploy_target(dest_dir)
    base_name = BASE_NAME

    if not source.is_file() or source.stat().st_size == 0:
        fail(f"Source profile missing or empty: {source}")

    source_data = source.read_bytes()
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

    source_hash = sha256_bytes(source_data)

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        probe = dest_dir / ".dcim_write_test"
        probe.write_text("test", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        fail(f"Cannot write to deploy folder {dest_dir}: {exc}")

    candidate = dest_dir / base_name
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    suffix = 0

    while True:
        status_path = candidate.with_suffix(".status.md")
        if candidate.exists():
            if candidate.is_file():
                try:
                    existing_hash = sha256_bytes(candidate.read_bytes())
                    ET.parse(candidate)
                except (OSError, ET.ParseError):
                    existing_hash = ""
                if existing_hash == source_hash:
                    if not status_path.exists():
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
                        logger.info("Existing V10 config is already up to date.")
                        logger.info("CONFIG=%s", candidate)
                        logger.info("STATUS_FILE=%s", status_path)
                        logger.info("SHA256=%s", source_hash)
                        logger.info("XML_PARSE=PASS")
                        logger.info("STATUS=%s", STATUS_LABEL)
                        return
        elif not status_path.exists():
            break
        suffix += 1
        extra = f"_{suffix}" if suffix > 1 else ""
        candidate = dest_dir / (
            f"LXX521_V10_Baseline_UNVALIDATED_{stamp}{extra}.xml"
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

    output_hash = sha256_bytes(output_data)
    if output_hash != source_hash:
        fail("Source/output checksum mismatch")

    created = datetime.now().astimezone().isoformat(timespec="seconds")
    status_text = f"""# LXX521 / Sony IMX682 — V10 Config Status

- Status: `{STATUS_LABEL}`
- Created: `{created}`
- Source: `{source}`
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

    status_path = candidate.with_suffix(".status.md")
    if not status_path.exists():
        try:
            with status_path.open("x", encoding="utf-8") as f:
                f.write(status_text)
        except OSError as exc:
            fail(f"Config saved, but status report could not be written: {exc}")

    if sha256_bytes(source.read_bytes()) != sha256_bytes(candidate.read_bytes()):
        fail("Final source/config verification failed")

    logger.info("=== V10 CONFIG SAVED ===")
    logger.info("CONFIG=%s", candidate)
    logger.info("STATUS_FILE=%s", status_path)
    logger.info("SOURCE_SHA256=%s", source_hash)
    logger.info("CONFIG_SHA256=%s", output_hash)
    logger.info("XML_PARSE=PASS; STRING_ENTRIES=%d", len(entries))
    logger.info("TUNING_CHANGES=0")
    logger.info("STATUS=%s", STATUS_LABEL)


__all__ = ["build_v10_baseline"]
