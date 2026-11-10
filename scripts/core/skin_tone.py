"""Skin-tone profile tuning for LMC 8.4 IMX682 XML profiles.

Refactored from create_skintone_perfect.py. Applies gentle fine-tuning to
color/saturation/sharpness/contrast parameters that influence natural skin
tones, writing a new tuned profile next to the source.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from .logging import get_logger
from .paths import XML_DIR

logger = get_logger()

# Parameter-name keywords that influence skin tone / color / contrast.
_SKIN_KEYWORDS = ("sat", "color", "skin", "sharpness", "contrast")

# Gentle tuned values for natural skin tones.
_TUNED_VALUES = {
    "sat": "0.95",
    "sharpness": "1.02",
}


def _tuned_value(name_attr: str) -> Optional[str]:
    lower = name_attr.lower()
    if any(k in lower for k in _SKIN_KEYWORDS):
        for key, val in _TUNED_VALUES.items():
            if key in lower:
                return val
    return None


def tune_skin_tone(
    source_path: Path | str,
    output_path: Optional[Path | str] = None,
) -> int:
    """Tune skin-influencing parameters in ``source_path``.

    Writes the tuned profile to ``output_path`` (defaults to a
    ``_SkinTone_Perfect`` variant beside the source) and returns the
    number of parameters modified.
    """
    source = Path(source_path)
    if not source.is_file():
        logger.error("Source profile missing: %s", source)
        raise FileNotFoundError(f"Source profile missing: {source}")

    if output_path is None:
        output_path = source.with_name(
            source.stem.replace("_AllRounder", "_SkinTone_Perfect") + ".xml"
        )
    output = Path(output_path)

    tree = ET.parse(source)
    root = tree.getroot()

    modified_count = 0
    for elem in root.iter():
        name_attr = elem.attrib.get("name", "")
        tuned = _tuned_value(name_attr)
        if tuned is not None:
            elem.text = tuned
            modified_count += 1
            logger.debug("Tuned %s -> %s", name_attr, tuned)

    tree.write(output, encoding="utf-8", xml_declaration=True)
    logger.info("Skin-tone config saved: %s", output)
    logger.info("Successfully tuned %d color/saturation parameters.", modified_count)
    return modified_count


__all__ = ["tune_skin_tone"]
