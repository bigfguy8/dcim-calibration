#!/usr/bin/env python3
"""Tests for scripts/compare.py (deterministic side-by-side comparison)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import compare  # noqa: E402


def _fixture(path: Path, groups: list[dict]) -> None:
    records = []
    for g in groups:
        for _ in range(g["n"]):
            records.append(
                {
                    "file": f"{g['profile']}_{g['iso']}.jpg",
                    "profile": g["profile"],
                    "camera": g["camera"],
                    "iso": g["iso"],
                    "status": "ok",
                    "mtf50_center": g["mtf50_center"],
                    "mtf50_edge": g["mtf50_edge"],
                    "noise_sigma": {"g": g["noise_green"]},
                    "mean_luma": g["mean_luma"],
                    "highlight_clipping_pct": g["highlight"],
                    "gray_patch": {"delta_e00": g["delta_e"]},
                }
            )
    path.write_text(json.dumps({"records": records}))


class CompareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="comptest_"))

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, *paths: Path, out: str = "md") -> tuple[int, str]:
        import io

        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = compare.main([str(p) for p in paths] + ["--out", out])
        return code, buf.getvalue()

    def test_deterministic_markdown_two_fixtures(self):
        a = self.tmp / "a.json"
        b = self.tmp / "b.json"
        _fixture(
            a,
            [
                {
                    "profile": "LXX521_TEX.xml",
                    "camera": "back_main",
                    "iso": 100,
                    "n": 2,
                    "mtf50_center": 0.34,
                    "mtf50_edge": 0.25,
                    "noise_green": 1.1,
                    "mean_luma": 120.0,
                    "highlight": 0.1,
                    "delta_e": 2.0,
                }
            ],
        )
        _fixture(
            b,
            [
                {
                    "profile": "LXX521_TEX.xml",
                    "camera": "back_main",
                    "iso": 100,
                    "n": 2,
                    "mtf50_center": 0.30,
                    "mtf50_edge": 0.22,
                    "noise_green": 1.5,
                    "mean_luma": 110.0,
                    "highlight": 0.5,
                    "delta_e": 3.0,
                }
            ],
        )
        md_a = self._run(a, b)[1]
        md_b = self._run(a, b)[1]
        self.assertEqual(md_a, md_b, "compare markdown must be deterministic")
        self.assertIn("LXX521_TEX.xml/back_main/ISO 100", md_a)
        self.assertIn("MTF50 center (cy/px)", md_a)
        self.assertIn("0.3400", md_a)
        self.assertIn("0.3000", md_a)
        # delta b - a for mtf50_center = 0.30 - 0.34 = -0.04
        self.assertIn("-0.0400", md_a)

    def test_json_output_structure(self):
        a = self.tmp / "a.json"
        b = self.tmp / "b.json"
        _fixture(
            a,
            [
                {
                    "profile": "LXX521_TEX.xml",
                    "camera": "back_main",
                    "iso": 100,
                    "n": 1,
                    "mtf50_center": 0.34,
                    "mtf50_edge": 0.25,
                    "noise_green": 1.1,
                    "mean_luma": 120.0,
                    "highlight": 0.1,
                    "delta_e": 2.0,
                }
            ],
        )
        _fixture(
            b,
            [
                {
                    "profile": "LXX521_TEX.xml",
                    "camera": "back_main",
                    "iso": 100,
                    "n": 1,
                    "mtf50_center": 0.20,
                    "mtf50_edge": 0.15,
                    "noise_green": 2.0,
                    "mean_luma": 90.0,
                    "highlight": 2.0,
                    "delta_e": 6.0,
                }
            ],
        )
        import io

        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            compare.main([str(a), str(b), "--out", "json"])
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(len(payload["inputs"]), 2)
        self.assertEqual(len(payload["rows"]), 6)  # 1 group x 6 metrics
        row = payload["rows"][0]
        self.assertEqual(row["metric"], "mtf50_center")
        self.assertEqual(row["cells"][0]["value"], 0.34)
        self.assertEqual(row["cells"][1]["value"], 0.20)
        self.assertEqual(row["delta"], -0.14)
        self.assertEqual(row["cells"][0]["verdict"], "pass")
        self.assertEqual(row["cells"][1]["verdict"], "fail")


if __name__ == "__main__":
    unittest.main(verbosity=2)
