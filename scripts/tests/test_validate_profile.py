#!/usr/bin/env python3
"""tests for scripts/validate_profile.py.

Fixtures live under $TMPDIR; module path constants are monkeypatched so the
real configs/ keys/schema/TEX are never touched.
"""
import json
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
import scripts.validate_profile as vp  # noqa: E402


def _write_map(path, pairs):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("<map>\n")
        for key, value in pairs:
            handle.write(f'  <string name="{key}">{value}</string>\n')
        handle.write("</map>\n")


class ValidateProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lxc_validate_")
        self.keys_path = os.path.join(self.tmp, "keys.txt")
        self.schema_path = os.path.join(self.tmp, "keys_schema.json")
        self.tex_path = os.path.join(self.tmp, "LXX521_TEX.xml")
        self.unknown_path = os.path.join(self.tmp, "keys_unknown.txt")
        # canonical baseline: required keys a (number 0-10), b (string), c (number)
        _write_map(self.tex_path, [("a", "1"), ("b", "two"), ("c", "5")])
        with open(self.keys_path, "w", encoding="utf-8") as handle:
            handle.write("a\nb\nc\n")
        schema = {
            "a": {"type": "number", "min": 0, "max": 10},
            "b": {"type": "string"},
            "c": {"type": "number", "min": 0, "max": 100},
        }
        with open(self.schema_path, "w", encoding="utf-8") as handle:
            json.dump(schema, handle)
        vp.KEYS_PATH = self.keys_path
        vp.SCHEMA_PATH = self.schema_path
        vp.TEX_PATH = self.tex_path
        vp.UNKNOWN_PATH = self.unknown_path

    def _reset_unknown(self):
        if os.path.exists(self.unknown_path):
            os.remove(self.unknown_path)

    def test_valid_tex_passes(self):
        result = vp.validate_profile(self.tex_path)
        self.assertTrue(result["pass"])
        self.assertEqual(result["errors"], [])

    def test_unknown_key_profile_mode_is_error(self):
        path = os.path.join(self.tmp, "prof.xml")
        _write_map(path, [("a", "1"), ("b", "two"), ("c", "5"), ("zzz", "9")])
        result = vp.validate_profile(path)
        self.assertFalse(result["pass"])
        self.assertTrue(any("unknown key: zzz" in e for e in result["errors"]))

    def test_unknown_key_source_mode_is_warning(self):
        os.makedirs(os.path.join(self.tmp, "candidates"), exist_ok=True)
        path = os.path.join(self.tmp, "candidates", "variant.xml")
        _write_map(path, [("a", "1"), ("b", "two"), ("c", "5"), ("zzz", "9")])
        self._reset_unknown()
        result = vp.validate_source(path, kind_override="lmc84")
        self.assertTrue(result["pass"])  # unknown -> warning, not error
        self.assertTrue(any("unknown key" in w for w in result["warnings"]))
        self.assertIn("zzz", result["unknown_keys"])
        self.assertTrue(os.path.exists(self.unknown_path))
        with open(self.unknown_path, encoding="utf-8") as handle:
            self.assertIn("zzz", handle.read())

    def test_wrong_type_is_error(self):
        path = os.path.join(self.tmp, "prof.xml")
        _write_map(path, [("a", "not_a_number"), ("b", "two"), ("c", "5")])
        result = vp.validate_profile(path)
        self.assertFalse(result["pass"])
        self.assertTrue(any("wrong type for a" in e for e in result["errors"]))

    def test_out_of_range_is_error(self):
        path = os.path.join(self.tmp, "prof.xml")
        _write_map(path, [("a", "99"), ("b", "two"), ("c", "5")])
        result = vp.validate_profile(path)
        self.assertFalse(result["pass"])
        self.assertTrue(any("out of range a" in e for e in result["errors"]))

    def test_missing_required_is_error(self):
        path = os.path.join(self.tmp, "prof.xml")
        _write_map(path, [("a", "1"), ("b", "two")])  # missing required c
        result = vp.validate_profile(path)
        self.assertFalse(result["pass"])
        self.assertTrue(any("missing required key: c" in e for e in result["errors"]))

    def test_unknown_appended_to_keys_unknown_deduped(self):
        os.makedirs(os.path.join(self.tmp, "candidates"), exist_ok=True)
        base = os.path.join(self.tmp, "candidates")
        _write_map(os.path.join(base, "v1.xml"), [("a", "1"), ("b", "two"), ("c", "5"), ("zzz", "9")])
        _write_map(os.path.join(base, "v2.xml"), [("a", "1"), ("b", "two"), ("c", "5"), ("zzz", "8")])
        vp.validate_source(os.path.join(base, "v1.xml"), kind_override="lmc84")
        vp.validate_source(os.path.join(base, "v2.xml"), kind_override="lmc84")
        with open(self.unknown_path, encoding="utf-8") as handle:
            lines = [line.strip() for line in handle if line.strip()]
        self.assertEqual(lines, ["zzz"])  # sorted, deduped


if __name__ == "__main__":
    unittest.main()
