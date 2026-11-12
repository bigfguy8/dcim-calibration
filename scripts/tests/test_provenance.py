#!/usr/bin/env python3
"""Tests for C2 provenance: analysis.json block + report embedded-gates preference."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import analyze  # noqa: E402
import report  # noqa: E402

REPO = SCRIPTS.parent


def _synthetic_image(path: Path) -> None:
    import numpy as np
    from PIL import Image

    img = np.full((120, 160), 0.5, dtype=np.float32)
    img[40:80, :] = 0.9
    Image.fromarray((img * 255).astype(np.uint8)).save(path)


class ProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="provtest_"))

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_analyze(self, img: Path, out: Path, profile: str | None = None) -> int:
        args = [str(img), "-o", str(out)]
        if profile:
            args += ["--profile", profile]
        return analyze.main(args)

    def test_analyze_writes_provenance_block(self):
        img = self.tmp / "synthetic.png"
        _synthetic_image(img)
        out = self.tmp / "analysis.json"
        code = self._run_analyze(img, out, profile="TEX")
        self.assertEqual(code, 0)
        payload = json.loads(out.read_text())
        prov = payload["provenance"]
        for key in (
            "tool_version",
            "profile_name",
            "profile_sha256",
            "mgc_version",
            "mtf_method",
            "gates_source",
            "analysis_timestamp",
        ):
            self.assertIn(key, prov, f"provenance missing {key}")
        self.assertEqual(prov["mgc_version"], "MGC 8.9 BSG")
        self.assertEqual(prov["profile_name"], "TEX")
        self.assertIsNotNone(prov["profile_sha256"])
        self.assertEqual(len(prov["profile_sha256"]), 64)
        self.assertIn("configs/gates.json", prov["gates_source"])
        self.assertTrue(prov["analysis_timestamp"].endswith("+00:00"))
        self.assertEqual(payload["mtf_method"], "gaussian")

    def test_report_prefers_embedded_gates_source(self):
        # Custom gates: very strict MTF50 center minimum -> TEX group fails.
        custom_gates = self.tmp / "custom_gates.json"
        custom_gates.write_text(
            json.dumps(
                {
                    "day": {
                        "mtf50_center_min_cpp": {
                            "min": 0.99,
                            "max": None,
                            "unit": "cycles/px",
                        },
                        "mtf50_edge_min_cpp": {"min": 0.22, "max": None, "unit": "cycles/px"},
                        "mean_luma_min": {"min": 100.0, "max": None, "unit": "DN"},
                        "mean_luma_max": {"min": None, "max": 140.0, "unit": "DN"},
                        "highlight_clipping_max_pct": {
                            "min": None,
                            "max": 1.0,
                            "unit": "percent",
                        },
                        "noise_green_iso100_max_dn": {
                            "min": None,
                            "max": 1.5,
                            "unit": "DN",
                        },
                        "noise_green_iso3200_max_dn": {
                            "min": None,
                            "max": 12.0,
                            "unit": "DN",
                        },
                        "gray_patch_delta_e00_max": {
                            "min": None,
                            "max": 5.0,
                            "unit": "dE00",
                        },
                    }
                }
            )
        )
        # Analysis JSON whose provenance gates_source points at custom_gates.
        analysis = self.tmp / "analysis.json"
        analysis.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "records": [
                        {
                            "file": "x.jpg",
                            "profile": "LXX521_TEX.xml",
                            "camera": "back_main",
                            "iso": 100,
                            "status": "ok",
                            "mtf50_center": 0.34,
                            "mtf50_edge": 0.25,
                            "noise_sigma": {"g": 1.1},
                            "mean_luma": 120.0,
                            "highlight_clipping_pct": 0.1,
                            "gray_patch": {"delta_e00": 2.0},
                        }
                    ],
                    "provenance": {
                        "gates_source": f"{custom_gates} (sha256 x)",
                    },
                }
            )
        )
        outdir = self.tmp / "out"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = report.main([str(analysis), "-o", str(outdir)])
        self.assertEqual(code, 0)
        report_payload = json.loads((outdir / "calibration_report.json").read_text())
        group = report_payload["summary"]["groups"][0]
        # Embedded strict gate (0.99) makes 0.34 fail.
        self.assertEqual(group["status"], "fail")
        self.assertEqual(group["gates"]["mtf50_center_min_cpp"], 0.99)

    def test_report_explicit_gates_overrides_embedded(self):
        custom_gates = self.tmp / "custom_gates.json"
        custom_gates.write_text(
            json.dumps(
                {
                    "day": {
                        "mtf50_center_min_cpp": {
                            "min": 0.99,
                            "max": None,
                            "unit": "cycles/px",
                        },
                        "mtf50_edge_min_cpp": {"min": 0.22, "max": None, "unit": "cycles/px"},
                        "mean_luma_min": {"min": 100.0, "max": None, "unit": "DN"},
                        "mean_luma_max": {"min": None, "max": 140.0, "unit": "DN"},
                        "highlight_clipping_max_pct": {
                            "min": None,
                            "max": 1.0,
                            "unit": "percent",
                        },
                        "noise_green_iso100_max_dn": {
                            "min": None,
                            "max": 1.5,
                            "unit": "DN",
                        },
                        "noise_green_iso3200_max_dn": {
                            "min": None,
                            "max": 12.0,
                            "unit": "DN",
                        },
                        "gray_patch_delta_e00_max": {
                            "min": None,
                            "max": 5.0,
                            "unit": "dE00",
                        },
                    }
                }
            )
        )
        analysis = self.tmp / "analysis.json"
        analysis.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "records": [
                        {
                            "file": "x.jpg",
                            "profile": "LXX521_TEX.xml",
                            "camera": "back_main",
                            "iso": 100,
                            "status": "ok",
                            "mtf50_center": 0.34,
                            "mtf50_edge": 0.25,
                            "noise_sigma": {"g": 1.1},
                            "mean_luma": 120.0,
                            "highlight_clipping_pct": 0.1,
                            "gray_patch": {"delta_e00": 2.0},
                        }
                    ],
                    "provenance": {
                        "gates_source": f"{custom_gates} (sha256 x)",
                    },
                }
            )
        )
        outdir = self.tmp / "out2"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = report.main(
                [str(analysis), "-o", str(outdir), "--gates", str(REPO / "configs" / "gates.json")]
            )
        self.assertEqual(code, 0)
        report_payload = json.loads((outdir / "calibration_report.json").read_text())
        group = report_payload["summary"]["groups"][0]
        # Explicit default gates (0.30) makes 0.34 pass.
        self.assertEqual(group["status"], "pass")
        self.assertEqual(group["gates"]["mtf50_center_min_cpp"], 0.30)


if __name__ == "__main__":
    unittest.main(verbosity=2)
