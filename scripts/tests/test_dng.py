#!/usr/bin/env python3
"""Tests for scripts/dng.py (pure-Python DNG ingest via tifffile).

Synthetic DNG-like TIFFs are written to a temp directory -- no device, no
rawpy, no native build required.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import tifffile

SCRIPTS = Path(__file__).resolve().parent.parent
import sys  # noqa: E402

sys.path.insert(0, str(SCRIPTS))

import dng  # noqa: E402

_TAG_BLACK_LEVEL = 33722
_TAG_WHITE_LEVEL = 33723
_TAG_AS_SHOT_NEUTRAL = 37121
_TAG_CFA_PATTERN = 33421
_TAG_CFA_PLANE_COLOR = 33422


def _write_dng(path: Path, cfa: np.ndarray, black, white, neutral, pattern) -> None:
    """Write a minimal DNG-like single-page TIFF with DNG tags."""
    with tifffile.TiffWriter(path) as tw:
        tw.write(
            cfa,
            photometric="minisblack",
            bitspersample=int(cfa.dtype.itemsize * 8),
            extratags=[
                (_TAG_BLACK_LEVEL, "I",
                 len(black) if hasattr(black, "__len__") else 1, black, False),
                (_TAG_WHITE_LEVEL, "I", 2, [white, white], False),
                (_TAG_AS_SHOT_NEUTRAL, "I", 3, neutral, False),
                (_TAG_CFA_PATTERN, "I", 4, pattern, False),
                (_TAG_CFA_PLANE_COLOR, "B", 3, [0, 1, 2], False),
            ],
        )


class DngTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="dngtest_"))

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ramp_cfa(self) -> np.ndarray:
        # Smooth horizontal ramp so the demosaiced R plane is monotonic in x.
        return (
            np.linspace(0, 1000, 64).reshape(1, 64).repeat(64, axis=0)
        ).astype(np.uint16)

    def test_load_dng_round_trip(self):
        cfa = self._ramp_cfa()
        path = self.tmp / "ramp.dng"
        _write_dng(path, cfa, black=128, white=1023, neutral=[1, 2, 4],
                   pattern=[0, 1, 1, 2])

        image = dng.load_dng(path)
        self.assertEqual(image.cfa.shape, (64, 64))
        self.assertEqual(image.bit_depth, 16)
        self.assertEqual(image.width, 64)
        self.assertEqual(image.height, 64)
        self.assertEqual(image.pattern, "RGGB")
        self.assertAlmostEqual(image.black, 128.0)
        self.assertEqual(image.white, 1023.0)
        self.assertIsNotNone(image.wb)
        self.assertAlmostEqual(image.wb[1], 1.0)  # green normalised to 1

    def test_to_linear_rgb_shape_and_range(self):
        cfa = self._ramp_cfa()
        path = self.tmp / "lin.dng"
        _write_dng(path, cfa, black=0, white=1000, neutral=[1, 1, 1],
                   pattern=[0, 1, 1, 2])
        image = dng.load_dng(path)
        rgb = dng.to_linear_rgb(image)
        self.assertEqual(rgb.shape, (64, 64, 3))
        self.assertEqual(rgb.dtype, np.float32)
        self.assertGreaterEqual(rgb.min(), 0.0)
        self.assertLessEqual(rgb.max(), 1.0)

    def test_constant_cfa_yields_constant_rgb(self):
        cfa = np.full((32, 32), 700, dtype=np.uint16)
        path = self.tmp / "const.dng"
        _write_dng(path, cfa, black=0, white=1000, neutral=[1, 1, 1],
                   pattern=[0, 1, 1, 2])
        image = dng.load_dng(path)
        rgb = dng.to_linear_rgb(image)
        self.assertTrue(np.allclose(rgb, rgb[0, 0], atol=1e-3))

    def test_to_uint8_range(self):
        rgb = np.random.rand(8, 8, 3).astype(np.float32)
        u8 = dng.to_uint8(rgb)
        self.assertEqual(u8.dtype, np.uint8)
        self.assertGreaterEqual(u8.min(), 0)
        self.assertLessEqual(u8.max(), 255)


if __name__ == "__main__":
    unittest.main(verbosity=2)
