#!/usr/bin/env python3
"""validate_profile.py - validate LMC84 camera profile XML files.

Public API:
    validate_profile(path) -> {"pass": bool, "errors": [...], "warnings": [...]}
    validate_source(name_or_path, registry=None, kind_override=None) -> {
        "pass": bool, "errors": [...], "warnings": [...], "unknown_keys": [...]}

A profile XML is expected to have a <map> root containing <string name="..">..</string> entries.

Checks:
  * unknown key          -> ERROR   (WARNING for candidate/lmc84 sources)
  * wrong type           -> ERROR   (non-numeric where schema says number)
  * out of range         -> ERROR   (vs configs/keys_schema.json min/max)
  * missing required key -> ERROR   (required = key present in LXX521_TEX.xml)

For candidate sources (kind "lmc84", role "candidate") unknown keys are
downgraded to WARNINGS and appended to configs/keys_unknown.txt (sorted, deduped).
"""
import json
import os
import re
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(REPO_ROOT, "configs")
KEYS_PATH = os.path.join(CONFIG_DIR, "keys.txt")
SCHEMA_PATH = os.path.join(CONFIG_DIR, "keys_schema.json")
TEX_PATH = os.path.join(CONFIG_DIR, "xml", "LXX521_TEX.xml")
UNKNOWN_PATH = os.path.join(CONFIG_DIR, "keys_unknown.txt")

_STRING_RE = re.compile(r'<string\s+name="([^"]+)"\s*>(.*?)</string>', re.S)


def _load_keys():
    with open(KEYS_PATH, encoding="utf-8") as handle:
        return {line.strip() for line in handle if line.strip()}


def _load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def _load_tex_keys():
    """Required keys = every key present in the canonical TEX baseline."""
    root = ET.parse(TEX_PATH).getroot()
    return {el.get("name") for el in root.findall("string") if el.get("name")}


def parse_profile(path):
    """Parse a profile XML into {key: value}. Raises on malformed XML."""
    root = ET.parse(path).getroot()
    if root.tag != "map":
        raise ValueError(f"root is <{root.tag}>, expected <map>")
    kv = {}
    for el in root.findall("string"):
        name = el.get("name")
        if name:
            kv[name] = el.text
    return kv


def _is_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _check(path, keys, schema, tex_keys, unknown_is_error=True):
    """Core check. Returns (errors, warnings, unknown_keys)."""
    errors = []
    warnings = []
    unknown_keys = []
    try:
        kv = parse_profile(path)
    except Exception as exc:
        return [f"parse error: {exc}"], [], []

    # Unknown keys
    for name in kv:
        if name not in keys:
            unknown_keys.append(name)
            if unknown_is_error:
                errors.append(f"unknown key: {name}")
            else:
                warnings.append(f"unknown key (candidate): {name}")

    # Missing required keys (required == present in TEX baseline)
    for name in sorted(tex_keys):
        if name not in kv:
            errors.append(f"missing required key: {name}")

    # Type / range checks
    for name, value in kv.items():
        spec = schema.get(name)
        if not spec:
            continue
        if spec.get("type") == "number":
            if not _is_number(value):
                errors.append(f"wrong type for {name}: expected number, got {value!r}")
                continue
            num = float(value)
            mn = spec.get("min")
            mx = spec.get("max")
            if mn is not None and num < mn:
                errors.append(f"out of range {name}: {num} < {mn}")
            if mx is not None and num > mx:
                errors.append(f"out of range {name}: {num} > {mx}")

    return errors, warnings, unknown_keys


def validate_profile(path):
    """Validate a single profile file against the canonical schema (strict)."""
    keys = _load_keys()
    schema = _load_schema()
    tex_keys = _load_tex_keys()
    errors, warnings, _unknown = _check(path, keys, schema, tex_keys, unknown_is_error=True)
    return {"pass": len(errors) == 0, "errors": errors, "warnings": warnings}


def _append_unknown_keys(unknown_keys):
    """Append unknown keys to configs/keys_unknown.txt, sorted and deduped."""
    existing = set()
    if os.path.isfile(UNKNOWN_PATH):
        with open(UNKNOWN_PATH, encoding="utf-8") as handle:
            existing = {line.strip() for line in handle if line.strip()}
    existing.update(unknown_keys)
    with open(UNKNOWN_PATH, "w", encoding="utf-8") as handle:
        for name in sorted(existing):
            handle.write(name + "\n")


def _resolve(name_or_path, registry, kind_override):
    """Resolve a source name or path to (path, kind, role)."""
    # Direct filesystem path
    if name_or_path and (os.path.isabs(name_or_path) or os.path.exists(name_or_path)):
        path = name_or_path if os.path.isabs(name_or_path) else os.path.join(REPO_ROOT, name_or_path)
        kind = kind_override or "lmc84"
        role = "candidate" if "/candidates/" in path.replace("\\", "/") else "canonical"
        return path, kind, role

    if registry is None:
        registry_path = os.path.join(CONFIG_DIR, "sources.json")
        with open(registry_path, encoding="utf-8") as handle:
            registry = json.load(handle)

    for entry in registry.get("sources", []):
        if entry.get("name") == name_or_path:
            path = entry["path"]
            if not os.path.isabs(path):
                path = os.path.join(REPO_ROOT, path)
            kind = kind_override or entry.get("kind", "lmc84")
            role = entry.get("role", "candidate")
            return path, kind, role

    raise ValueError(f"unknown source: {name_or_path}")


def _is_candidate_source(kind, role):
    return kind == "lmc84" and role == "candidate"


def validate_source(name_or_path, registry=None, kind_override=None):
    """Validate a registered source or direct path.

    For candidate sources (kind=lmc84, role=candidate) unknown keys are
    WARNINGS (not ERRORS) and are appended to configs/keys_unknown.txt.
    """
    path, kind, role = _resolve(name_or_path, registry, kind_override)
    keys = _load_keys()
    schema = _load_schema()
    tex_keys = _load_tex_keys()
    candidate = _is_candidate_source(kind, role)
    errors, warnings, unknown_keys = _check(path, keys, schema, tex_keys, unknown_is_error=not candidate)

    if candidate and unknown_keys:
        _append_unknown_keys(unknown_keys)

    return {
        "pass": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "unknown_keys": sorted(unknown_keys),
    }
