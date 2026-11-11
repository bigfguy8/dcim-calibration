#!/usr/bin/env python3
"""tests for the deploy/source overlap guard in scripts/sources.py."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
from scripts import sources  # noqa: E402


class OverlapGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lxc_overlap_")
        self.reg = os.path.join(self.tmp, "sources.json")
        os.environ["LMC84_SOURCES_REGISTRY"] = self.reg
        sources.REGISTRY_PATH = self.reg
        self.live_dir = os.path.join(self.tmp, "live_dest")
        os.makedirs(self.live_dir)
        registry = {
            "sources": [
                {
                    "name": "device_live",
                    "path": self.live_dir,
                    "kind": "lmc84",
                    "role": "live",
                    "read_only": True,
                    "manifest_sha256": "x",
                }
            ]
        }
        with open(self.reg, "w", encoding="utf-8") as handle:
            json.dump(registry, handle)
        self.other_dir = os.path.join(self.tmp, "other")
        os.makedirs(self.other_dir)

    def _run_overlap(self, argv):
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            code = sources.main(argv)
        return code, buf_out.getvalue(), buf_err.getvalue()

    def test_overlaps_deploy_dest_true_for_live(self):
        self.assertTrue(sources.overlaps_deploy_dest(self.live_dir))

    def test_overlaps_deploy_dest_false_for_other(self):
        self.assertFalse(sources.overlaps_deploy_dest(self.other_dir))

    def test_verify_overlap_into_live_exits_2(self):
        code, _out, err = self._run_overlap(["verify-overlap", "--path", self.live_dir])
        self.assertEqual(code, 2)
        self.assertIn("overlaps a registered live source", err)

    def test_verify_overlap_into_live_with_force_exits_0_warns(self):
        code, _out, err = self._run_overlap(["verify-overlap", "--path", self.live_dir,
                                             "--force-source-overlap"])
        self.assertEqual(code, 0, err)
        self.assertIn("WARNING", err)
        self.assertIn(self.live_dir, err)

    def test_verify_overlap_into_other_is_ok(self):
        code, out, _err = self._run_overlap(["verify-overlap", "--path", self.other_dir])
        self.assertEqual(code, 0, out)
        self.assertIn("[OK]", out)


if __name__ == "__main__":
    unittest.main()
