"""XML profile helpers for LMC 8.4 calibration.

Refactored from compare_profiles.py and dcim_standalone_pipeline.py.
Parses ``<map>`` XML profiles into key/value dictionaries and compares
two profiles, reporting every differing key.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

from .logging import get_logger

logger = get_logger()


def parse_xml_params(filepath: Path | str) -> Dict[str, str]:
    """Parse a LMC 8.4 ``<map>`` XML profile into a dict of name -> value.

    Returns an empty dict on parse failure (the caller decides how to
    handle missing/invalid profiles).
    """
    path = Path(filepath)
    if not path.is_file():
        logger.error("Profile not found: %s", path)
        return {}
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as exc:
        logger.error("Failed to parse %s: %s", path, exc)
        return {}

    params: Dict[str, str] = {}
    for elem in root.iter():
        name = elem.attrib.get("name")
        if not name:
            continue
        value = elem.attrib.get("value", elem.text)
        if value is None:
            continue
        params[name] = value.strip() if isinstance(value, str) else value
    return params


def compare_profiles(master_path: Path | str, target_path: Path | str) -> int:
    """Compare two profiles and log every differing key.

    Returns the number of differing keys (0 means identical coverage).
    """
    master = parse_xml_params(master_path)
    target = parse_xml_params(target_path)

    if not master:
        logger.error("Master profile is empty or missing: %s", master_path)
        return -1
    if not target:
        logger.error("Target profile is empty or missing: %s", target_path)
        return -1

    logger.info("Comparing target: %s", target_path)
    logger.info("Against master:   %s", master_path)

    all_keys = sorted(set(master.keys()).union(set(target.keys())))
    diff_count = 0
    for key in all_keys:
        m_val = master.get(key, "NOT_PRESENT")
        t_val = target.get(key, "NOT_PRESENT")
        if m_val != t_val:
            logger.info("Param: %s", key)
            logger.info("  Master: %s", m_val)
            logger.info("  Target: %s", t_val)
            diff_count += 1

    logger.info("Total differences found: %d", diff_count)
    return diff_count


__all__ = ["parse_xml_params", "compare_profiles"]
