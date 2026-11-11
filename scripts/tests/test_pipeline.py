#!/usr/bin/env python3
"""Unit tests for the MGC 8.9 (BSG) calibration pipeline.

Run from the repository root:

    python3 -m unittest discover -s scripts/tests -v
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import analyze  # noqa: E402
import report  # noqa: E402

REPO = SCRIPTS.parent


def _gaussian_kernel(sigma: float) -> np.ndarray:
    radius = max(1, int(math.ceil(3.0 * sigma)))
    x = np.arange(-radius, radius + 1, dtype=np.float64)
    kernel = np.exp(-(x**2) / (2.0 * sigma**2))
    return (kernel / kernel.sum()).astype(np.float32)


def slanted_edge_image(
    height: int = 480,
    width: int = 640,
    *,
    center: int = 320,
    slope: float = 0.05,
    sigma_px: float = 0.7,
    supersample: int = 6,
    low: float = 0.15,
    high: float = 0.85,
    noise_dn: float = 0.0,
    seed: int = 7,
) -> np.ndarray:
    """Render a supersampled blurred slanted edge, returned as uint8 grayscale."""
    big_h, big_w = height * supersample, width * supersample
    ys = (np.arange(big_h, dtype=np.float32)[:, None] + 0.5) / supersample
    xs = (np.arange(big_w, dtype=np.float32)[None, :] + 0.5) / supersample
    edge_x = center + slope * (ys - height / 2.0)
    image = np.where(xs >= edge_x, high, low).astype(np.float32)

    kernel = _gaussian_kernel(sigma_px * supersample)
    radius = len(kernel) // 2
    padded = np.pad(image, ((0, 0), (radius, radius)), mode="edge")
    blurred = np.zeros_like(image)
    for offset, weight in enumerate(kernel):
        blurred += weight * padded[:, offset : offset + big_w]
    padded = np.pad(blurred, ((radius, radius), (0, 0)), mode="edge")
    blurred = np.zeros_like(image)
    for offset, weight in enumerate(kernel):
        blurred += weight * padded[offset : offset + big_h, :]

    down = blurred.reshape(height, supersample, width, supersample).mean(axis=(1, 3))
    rng = np.random.default_rng(seed)
    if noise_dn:
        down = down + rng.normal(0.0, noise_dn / 255.0, down.shape)
    return np.clip(np.round(down * 255.0), 0, 255).astype(np.uint8)


def gaussian_mtf50(sigma_px: float) -> float:
    """Analytic MTF50 of a Gaussian PSF (cycles/pixel)."""
    return math.sqrt(math.log(2.0) / (2.0 * math.pi**2)) / sigma_px


class SlantedEdgeTests(unittest.TestCase):
    def test_mtf50_tracks_analytic_value(self):
        for sigma, tolerance in ((0.7, 0.045), (1.0, 0.04), (1.4, 0.035)):
            image = slanted_edge_image(sigma_px=sigma)
            result = analyze.measure_mtf50(image.astype(np.float32) / 255.0)
            measured = result["mtf50_center"] or result["mtf50_edge"]
            self.assertIsNotNone(measured, f"no edge measured for sigma={sigma}")
            expected = gaussian_mtf50(sigma)
            self.assertAlmostEqual(
                measured,
                expected,
                delta=tolerance,
                msg=f"sigma={sigma}: measured {measured:.3f}, expected {expected:.3f}",
            )

    def test_mtf50_rejects_flat_image(self):
        flat = np.full((240, 320), 128, dtype=np.uint8)
        result = analyze.measure_mtf50(flat.astype(np.float32) / 255.0)
        self.assertIsNone(result["mtf50_center"])
        self.assertIsNone(result["mtf50_edge"])

    def test_sharper_edge_has_higher_mtf50(self):
        soft = slanted_edge_image(sigma_px=1.4)
        crisp = slanted_edge_image(sigma_px=0.7)
        soft_mtf = analyze.measure_mtf50(soft.astype(np.float32) / 255.0)
        crisp_mtf = analyze.measure_mtf50(crisp.astype(np.float32) / 255.0)
        soft_value = soft_mtf["mtf50_center"] or soft_mtf["mtf50_edge"]
        crisp_value = crisp_mtf["mtf50_center"] or crisp_mtf["mtf50_edge"]
        self.assertGreater(crisp_value, soft_value)


class NoiseAndExposureTests(unittest.TestCase):
    def test_noise_sigma_recovers_known_sigma(self):
        rng = np.random.default_rng(3)
        sigma_dn = 2.0
        channel = np.clip(
            0.5 + rng.normal(0.0, sigma_dn / 255.0, (512, 512)), 0.0, 1.0
        ).astype(np.float32)
        measured = analyze._channel_noise(channel)
        self.assertAlmostEqual(measured, sigma_dn, delta=0.35)

    def test_exposure_statistics(self):
        gray = np.full((100, 100), 120 / 255.0, dtype=np.float32)
        rgb = np.repeat(gray[..., None], 3, axis=2)
        rgb[:5, :5, :] = 1.0
        stats = analyze.measure_exposure(rgb, gray)
        self.assertAlmostEqual(stats["mean_luma"], 120.0, delta=0.5)
        self.assertAlmostEqual(stats["highlight_clipping_pct"], 0.25, delta=0.01)
        self.assertEqual(stats["shadow_clipping_pct"], 0.0)


class FilePipelineTests(unittest.TestCase):
    def test_analyse_file_with_pillow(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "20261111_120000"
            session.mkdir()
            path = session / "LXX521_TEX_back_iso400_center.png"
            Image.fromarray(
                slanted_edge_image(height=320, width=420, center=210, noise_dn=1.5)
            ).save(path)
            record = analyze.analyse_file(path)
            self.assertEqual(record["status"], "ok")
            self.assertEqual(record["profile"], "TEX")
            self.assertEqual(record["camera"], "back_main")
            self.assertEqual(record["iso"], 400)
            self.assertEqual(record["session"], "20261111_120000")
            self.assertIsNotNone(record["mtf50_center"])
            self.assertGreater(record["noise_sigma"]["g"], 0.0)

    def test_report_groups_by_profile_camera_iso(self):
        records = [
            {
                "file": "a.jpg", "profile": "TEX", "camera": "back_main", "iso": 100,
                "status": "ok", "mtf50_center": 0.34, "mtf50_edge": 0.25,
                "noise_sigma": {"g": 1.1}, "mean_luma": 120.0,
                "highlight_clipping_pct": 0.1,
            },
            {
                "file": "b.jpg", "profile": "TEX", "camera": "back_main", "iso": 3200,
                "status": "ok", "mtf50_center": 0.20, "mtf50_edge": 0.15,
                "noise_sigma": {"g": 15.0}, "mean_luma": 118.0,
                "highlight_clipping_pct": 0.4,
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "analysis.json"
            source.write_text(json.dumps({"records": records}))
            out = tmp_path / "reports"
            code = report.main([str(source), "-o", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads((out / "calibration_report.json").read_text())
            self.assertEqual(len(payload["summary"]["groups"]), 2)
            self.assertFalse(payload["summary"]["overall_pass"])
            self.assertTrue((out / "calibration_report.md").is_file())
            high_iso = [g for g in payload["summary"]["groups"] if g["iso"] == 3200][0]
            self.assertEqual(high_iso["status"], "fail")
            low_iso = [g for g in payload["summary"]["groups"] if g["iso"] == 100][0]
            self.assertEqual(low_iso["status"], "pass")

    def test_night_profile_uses_night_gates(self):
        record = {
            "profile": "LXX521_NIGHT.xml",
            "camera": "main",
            "iso": 3200,
            "status": "ok",
            "mtf50_center": 0.20,
            "mtf50_edge": 0.14,
            "noise_sigma": {"g": 14.0},
            "mean_luma": 90.0,
            "highlight_clipping_pct": 1.5,
        }
        night = report.build_summary([record])["groups"][0]
        self.assertEqual(night["status"], "pass")
        self.assertEqual(night["gates"]["mtf50_center_min_cpp"], 0.18)

        daylight = report.build_summary([{**record, "profile": "LXX521_TEX.xml"}])[
            "groups"
        ][0]
        self.assertEqual(daylight["status"], "fail")

    def test_night_profile_is_reproducible(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "make_night_profile.py"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
