#!/usr/bin/env python3
"""tests for scripts/triage_profiles.py."""
import json
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
from scripts import triage_profiles  # noqa: E402


def _write_map(path, pairs):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("<map>\n")
        for key, value in pairs:
            handle.write(f'  <string name="{key}">{value}</string>\n')
        handle.write("</map>\n")


class DeltaAndFamilyTests(unittest.TestCase):
    def test_delta_exact(self):
        ref = {"a": "1", "b": "2", "c": "3"}
        cand = {"a": "1", "b": "20", "c": "3", "d": "4", "e": "5"}
        delta = triage_profiles._delta(ref, cand)
        self.assertEqual(delta["added"], ["d", "e"])
        self.assertEqual(delta["removed"], [])
        self.assertEqual(delta["changed"],
                         [{"key": "b", "old": "2", "new": "20"}])

    def test_family_night_by_name(self):
        delta = {"added": [], "changed": [{"key": "x", "old": "1", "new": "2"}]}
        self.assertEqual(triage_profiles._family("LXX521_NIGHT.xml", delta), "night")
        self.assertEqual(triage_profiles._family("night_variant.xml", delta), "night")

    def test_family_sharpness_probe_by_name(self):
        delta = {"added": [], "changed": [{"key": "x", "old": "1", "new": "2"}]}
        self.assertEqual(triage_profiles._family("X_SHARPNESS_PROBE.xml", delta), "sharpness_probe")

    def test_family_portrait_is_aesthetic(self):
        delta = {"added": [], "changed": [{"key": "x", "old": "1", "new": "2"}]}
        self.assertEqual(triage_profiles._family("LXX521_PORTRAIT.xml", delta), "aesthetic")
        self.assertEqual(triage_profiles._family("LXX521_PIXEL.xml", delta), "aesthetic")
        self.assertEqual(triage_profiles._family("LXX521_IPHONE.xml", delta), "aesthetic")

    def test_family_baseline_when_no_changes(self):
        self.assertEqual(triage_profiles._family("anything.xml",
                                                 {"added": [], "changed": []}), "baseline")

    def test_family_dslr(self):
        delta = {"added": [], "changed": [{"key": "x", "old": "1", "new": "2"}]}
        self.assertEqual(triage_profiles._family("LXX521_DSLR.xml", delta), "dslr")
        self.assertEqual(triage_profiles._family("LXX521_DSLR64.xml", delta), "dslr")
        self.assertEqual(triage_profiles._family("LXX521_DSLRMAX.xml", delta), "dslr")

    def test_delta_signature_grouping(self):
        ref = {"a": "1", "b": "2"}
        d1 = triage_profiles._delta(ref, {"a": "1", "b": "2"})
        d2 = triage_profiles._delta(ref, {"b": "2", "a": "1"})
        self.assertEqual(triage_profiles._delta_signature(d1),
                         triage_profiles._delta_signature(d2))
        d3 = triage_profiles._delta(ref, {"a": "9", "b": "2"})
        self.assertNotEqual(triage_profiles._delta_signature(d1),
                            triage_profiles._delta_signature(d3))


class TriageIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lxc_triage_")
        self.refdir = os.path.join(self.tmp, "ref")
        self.canddir = os.path.join(self.tmp, "cand")
        os.makedirs(self.refdir)
        os.makedirs(self.canddir)
        self.ref = os.path.join(self.refdir, "LXX521_TEX.xml")
        _write_map(self.ref, [("k1", "1"), ("k2", "2"), ("k3", "3")])

    def _write_cand(self, name, pairs):
        path = os.path.join(self.canddir, name)
        _write_map(path, pairs)
        return path

    def test_delta_with_3_changed_1_added(self):
        self._write_cand("variant.xml", [("k1", "1"), ("k2", "20"), ("k3", "30"),
                                         ("k4", "40"), ("k5", "50")])
        report, _, _ = triage_profiles.triage(self.canddir, self.ref, self.tmp)
        entry = report["candidates"][0]
        self.assertEqual(entry["name"], "variant.xml")
        self.assertEqual(entry["delta"]["added"], ["k4", "k5"])
        self.assertEqual(len(entry["delta"]["changed"]), 2)
        self.assertEqual(entry["key_count"], 5)

    def test_duplicate_identical_files_same_signature(self):
        self._write_cand("alpha.xml", [("k1", "1"), ("k2", "2")])
        self._write_cand("beta.xml", [("k1", "1"), ("k2", "2")])
        report, _, _ = triage_profiles.triage(self.canddir, self.ref, self.tmp)
        groups = report["duplicate_groups"]["by_sha256"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(sorted(groups[0]), ["alpha.xml", "beta.xml"])

    def test_missing_reference_exits_2_no_output(self):
        out_dir = os.path.join(self.tmp, "out")
        code = triage_profiles.main(["--candidates", self.canddir,
                                     "--reference", os.path.join(self.tmp, "nope.xml"),
                                     "--out", out_dir])
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(os.path.join(out_dir, "lxx521_triage.json")))
        self.assertFalse(os.path.exists(os.path.join(out_dir, "lxx521_triage.md")))

    def test_json_has_no_timestamps(self):
        self._write_cand("v.xml", [("k1", "1")])
        report, json_path, _ = triage_profiles.triage(self.canddir, self.ref, self.tmp)
        text = json.dumps(report, sort_keys=True)
        self.assertNotIn("generated_at", text)


if __name__ == "__main__":
    unittest.main()
