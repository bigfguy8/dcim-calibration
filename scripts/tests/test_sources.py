#!/usr/bin/env python3
"""tests for scripts/sources.py (sources registry).

Uses a fixture registry under $TMPDIR via the LMC84_SOURCES_REGISTRY
environment variable so the real configs/sources.json is never touched.
"""
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


class SourcesRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lxc_sources_")
        self.reg = os.path.join(self.tmp, "sources.json")
        os.environ["LMC84_SOURCES_REGISTRY"] = self.reg
        sources.REGISTRY_PATH = self.reg
        with open(self.reg, "w", encoding="utf-8") as handle:
            json.dump({"sources": []}, handle)
        self.srcdir = os.path.join(self.tmp, "src")
        os.makedirs(self.srcdir)
        with open(os.path.join(self.srcdir, "a.xml"), "wb") as handle:
            handle.write(b'<map><string name="k1">1</string></map>')
        with open(os.path.join(self.srcdir, "b.xml"), "wb") as handle:
            handle.write(b'<map><string name="k2">2</string></map>')

    def _run(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sources.main(argv)
        return code, buf.getvalue()

    def test_add_list_verify_remove_round_trip(self):
        code, out = self._run(["add", "--name", "fix", "--path", self.srcdir,
                               "--kind", "lmc84", "--role", "candidate"])
        self.assertEqual(code, 0, out)
        code, out = self._run(["list"])
        self.assertEqual(code, 0, out)
        self.assertIn("fix", out)
        code, out = self._run(["verify", "--name", "fix"])
        self.assertEqual(code, 0, out)
        self.assertIn("[PASS]", out)
        code, out = self._run(["remove", "--name", "fix", "--yes"])
        self.assertEqual(code, 0, out)
        registry = json.load(open(self.reg, encoding="utf-8"))
        self.assertEqual([e["name"] for e in registry["sources"]], [])

    def test_verify_detects_drift(self):
        self._run(["add", "--name", "fix", "--path", self.srcdir,
                   "--kind", "lmc84", "--role", "candidate"])
        # Mutate one source file -> manifest must drift.
        with open(os.path.join(self.srcdir, "a.xml"), "wb") as handle:
            handle.write(b'<map><string name="k1">999</string></map>')
        code, out = self._run(["verify", "--name", "fix"])
        self.assertEqual(code, 1, out)
        self.assertIn("[DRIFT]", out)

    def test_verify_missing_source(self):
        code, _ = self._run(["verify", "--name", "does_not_exist"])
        self.assertEqual(code, 1)

    def test_remove_live_requires_yes(self):
        self._run(["add", "--name", "live", "--path", self.srcdir,
                   "--kind", "lmc84", "--role", "live"])
        code, _ = self._run(["remove", "--name", "live"])
        self.assertEqual(code, 1)
        code, _ = self._run(["remove", "--name", "live", "--yes"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
