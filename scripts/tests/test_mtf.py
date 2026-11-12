#!/usr/bin/env python3
"""Tests for scripts/mtf.py (ISO 12233 slanted-edge MTF50).

Pure NumPy; synthetic slanted edges only -- no device captures needed.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import mtf  # noqa: E402


def _gaussian_kernel(sigma: float) -> np.ndarray:
    radius = max(1, int(math.ceil(3.0 * sigma)))
    x = np.arange(-radius, radius + 1, dtype=np.float64)
    kernel = np.exp(-(x**2) / (2.0 * sigma**2))
    return (kernel / kernel.sum()).astype(np.float64)


def slanted_edge_image(
    height: int = 240,
    width: int = 320,
    *,
    center: float = 160.0,
    slope: float = 0.05,
    sigma_px: float = 1.0,
    supersample: int = 6,
    low: float = 0.15,
    high: float = 0.85,
) -> np.ndarray:
    """Render a supersampled, Gaussian-blurred slanted edge (float 0..1)."""
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
    return blurred.reshape(height, supersample, width, supersample).mean(
        axis=(1, 3)
    )


def gaussian_mtf50(sigma_px: float) -> float:
    """Analytic MTF50 of a Gaussian PSF (cycles/pixel)."""
    return math.sqrt(math.log(2.0) / (2.0 * math.pi**2)) / sigma_px


class SlantedEdgeMTFTests(unittest.TestCase):
    def test_sigma_one_in_ballpark(self):
        image = slanted_edge_image(sigma_px=1.0)
        result = mtf.slanted_edge_mtf50(image)
        self.assertIsNotNone(result["mtf50"])
        expected = gaussian_mtf50(1.0)
        # The aligned slanted-edge measurement runs somewhat hot vs. the
        # analytic Gaussian value; assert the same order of magnitude.
        self.assertGreater(result["mtf50"], expected * 0.3)
        self.assertLess(result["mtf50"], expected * 2.5)
        self.assertIsNotNone(result["angle_deg"])
        self.assertIsNotNone(result["contrast"])

    def test_sharper_edge_orders_higher(self):
        soft = slanted_edge_image(sigma_px=1.4)
        crisp = slanted_edge_image(sigma_px=0.7)
        soft_mtf = mtf.slanted_edge_mtf50(soft)["mtf50"]
        crisp_mtf = mtf.slanted_edge_mtf50(crisp)["mtf50"]
        self.assertIsNotNone(soft_mtf)
        self.assertIsNotNone(crisp_mtf)
        self.assertGreater(crisp_mtf, soft_mtf)

    def test_flat_region_is_rejected(self):
        flat = np.full((120, 120), 0.5, dtype=np.float64)
        result = mtf.slanted_edge_mtf50(flat)
        self.assertIsNone(result["mtf50"])
        self.assertIsNone(result["contrast"])
        self.assertIsNone(result["overshoot"])

    def test_gradient_noise_is_rejected(self):
        rng = np.random.default_rng(0)
        noise = rng.random((120, 120)).astype(np.float64)
        result = mtf.slanted_edge_mtf50(noise)
        self.assertIsNone(result["mtf50"])

    def test_returns_expected_keys(self):
        image = slanted_edge_image(sigma_px=1.0)
        result = mtf.slanted_edge_mtf50(image)
        self.assertEqual(
            set(result), {"mtf50", "angle_deg", "contrast", "overshoot"}
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
