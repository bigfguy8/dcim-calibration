#!/usr/bin/env python3
"""Pure-Python DNG/raw ingest for the MGC 8.9 (BSG) pipeline.

DNG is a TIFF-based container, so it is read with ``tifffile`` (pure Python;
no native build, no ``rawpy``).  Only a *bilinear* demosaic is implemented --
sufficient to feed the existing NumPy/Pillow analyzers.  Vendor colour science,
tone curves and noise reduction are intentionally *not* reproduced.

Data model
----------
:func:`load_dng` returns a :class:`DngImage`::

    DngImage(cfa, black, white, wb, pattern, bit_depth, width, height)

* ``cfa``   -- raw CFA plane (HxW), black level not yet subtracted
* ``black`` -- black level (float, raw units)
* ``white`` -- white / saturation level (float, raw units)
* ``wb``    -- AsShotNeutral-based gains ``(r, g, b)`` or ``None``
* ``pattern``-- CFA layout string, e.g. ``"RGGB"``
* ``bit_depth``-- bits per sample

:func:`to_linear_rgb` black-subtracts, applies white balance and bilinear
demosaics to a float32 HxWx3 image normalised to 0..1.  :func:`to_uint8`
converts to 0..255 uint8 for legacy analyzers.

CLI
---
    python3 scripts/dng.py <file.dng>
    # prints a one-line summary of the decoded DNG
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

try:  # tifffile is pure Python; no native build required
    import tifffile  # type: ignore

    _HAS_TIFFFILE = True
except Exception:  # pragma: no cover - depends on host packages
    tifffile = None  # type: ignore
    _HAS_TIFFFILE = False

# DNG TIFF tag ids.
_TAG_BLACK_LEVEL = 33722   # BlackLevel
_TAG_WHITE_LEVEL = 33723   # WhiteLevel
_TAG_AS_SHOT_NEUTRAL = 37121  # AsShotNeutral
_TAG_CFA_PATTERN = 33421   # CFAPattern
_TAG_CFA_PLANE_COLOR = 33422  # CFAPlaneColor

_COLOR_BY_INDEX = {0: "R", 1: "G", 2: "B"}
_DEFAULT_PATTERN = "RGGB"


@dataclass
class DngImage:
    """Decoded DNG raw data."""

    path: Path
    cfa: np.ndarray              # HxW, black NOT subtracted
    black: float                 # black level (raw units)
    white: float                 # white/saturation level (raw units)
    wb: tuple[float, float, float] | None  # AsShotNeutral gains (r, g, b)
    pattern: str                 # e.g. "RGGB", "BGGR"
    bit_depth: int
    width: int
    height: int


def _tag_value(page: Any, code: int) -> Any:
    """Return the value of a TIFF tag by id, or None if absent."""
    try:
        tag = page.tags.get(code)
    except Exception:
        return None
    if tag is None:
        return None
    try:
        return tag.value
    except Exception:
        return None


def _as_floats(value: Any) -> list[float]:
    if value is None:
        return []
    if isinstance(value, (bytes, bytearray)):
        for dt in (np.uint16, np.uint32, np.uint8):
            try:
                return [float(v) for v in np.frombuffer(bytes(value), dtype=dt)]
            except ValueError:
                continue
        return [float(v) for v in bytes(value)]
    if isinstance(value, (list, tuple, np.ndarray)):
        return [float(v) for v in np.ravel(value)]
    return [float(value)]


def _cfa_pattern_string(page: Any) -> str:
    """Best-effort CFA layout string (e.g. ``RGGB``)."""
    cfapattern = _tag_value(page, _TAG_CFA_PATTERN)
    planecolor = _tag_value(page, _TAG_CFA_PLANE_COLOR)
    if cfapattern is None or planecolor is None:
        return _DEFAULT_PATTERN
    try:
        pc = [int(v) for v in np.ravel(planecolor)]
        cp = np.asarray(cfapattern)
        if cp.ndim == 1 and cp.size == 4:
            cp = cp.reshape(2, 2)
        colors = [_COLOR_BY_INDEX.get(int(pc[i]), "?") for i in np.ravel(cp)]
        return "".join(colors)
    except Exception:
        return _DEFAULT_PATTERN


def load_dng(path: Path | str) -> DngImage:
    """Read a DNG file into a :class:`DngImage`."""
    if not _HAS_TIFFFILE:
        raise ImportError("tifffile is required to read DNG; pip install tifffile")
    p = Path(path)
    with tifffile.TiffFile(p) as tf:
        if len(tf.pages) != 1:
            raise ValueError(f"expected a single-page DNG, got {len(tf.pages)} pages")
        page = tf.pages[0]
        cfa = page.asarray()
        if cfa.ndim != 2:
            raise ValueError(f"DNG CFA plane must be 2D, got shape {cfa.shape}")
        height, width = cfa.shape

        bit_depth = int(page.bitspersample) if page.bitspersample else (
            16 if cfa.dtype == np.uint16 else 8
        )

        black_f = _as_floats(_tag_value(page, _TAG_BLACK_LEVEL))
        black = black_f[0] if black_f else 0.0

        white_f = _as_floats(_tag_value(page, _TAG_WHITE_LEVEL))
        white = float(white_f[0]) if white_f else float((1 << bit_depth) - 1)

        wb: tuple[float, float, float] | None = None
        neutral = _as_floats(_tag_value(page, _TAG_AS_SHOT_NEUTRAL))
        if len(neutral) == 3 and all(v > 0 for v in neutral):
            gains = [1.0 / v for v in neutral]
            gains = [g / gains[1] for g in gains]  # normalise green to 1
            wb = (gains[0], gains[1], gains[2])

        pattern = _cfa_pattern_string(page)

    return DngImage(
        path=p,
        cfa=cfa,
        black=black,
        white=white,
        wb=wb,
        pattern=pattern,
        bit_depth=bit_depth,
        width=width,
        height=height,
    )


def _color_grid(pattern: str, height: int, width: int) -> np.ndarray:
    """HxW array of colour labels ('R'/'G'/'B') for the CFA layout."""
    if len(pattern) != 4:
        pattern = _DEFAULT_PATTERN
    grid = np.empty((height, width), dtype="<U1")
    for i, ch in enumerate(pattern):
        yy, xx = divmod(i, 2)
        grid[yy % 2::2, xx % 2::2] = ch
    return grid


def _sum3x3(arr: np.ndarray) -> np.ndarray:
    """3x3 neighbourhood sum with edge replication."""
    padded = np.pad(arr, 1, mode="edge")
    out = np.zeros_like(arr, dtype=np.float64)
    for dy in range(3):
        for dx in range(3):
            out += padded[dy : dy + arr.shape[0], dx : dx + arr.shape[1]]
    return out


def _interp_channel(values: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Bilinear interpolation of one colour plane onto the full grid."""
    v = np.where(mask, values.astype(np.float64), 0.0)
    m = mask.astype(np.float64)
    vs = _sum3x3(v)
    ms = _sum3x3(m)
    out = np.full_like(vs, 0.5, dtype=np.float64)
    np.divide(vs, ms, out=out, where=ms > 0)
    return out


def to_linear_rgb(dng: DngImage) -> np.ndarray:
    """Black-subtract, white-balance and bilinear-demosaic to float32 HxWx3 in 0..1."""
    cfa = dng.cfa.astype(np.float64) - float(dng.black)
    np.clip(cfa, 0.0, None, out=cfa)
    scale = max(float(dng.white), 1.0)
    linear = cfa / scale

    grid = _color_grid(dng.pattern, dng.height, dng.width)
    rgb = np.empty((dng.height, dng.width, 3), dtype=np.float64)
    chan_index = {"R": 0, "G": 1, "B": 2}
    for ch, idx in chan_index.items():
        mask = grid == ch
        rgb[..., idx] = _interp_channel(linear, mask)

    if dng.wb is not None:
        rgb = rgb * np.array(dng.wb, dtype=np.float64).reshape(1, 1, 3)
    np.clip(rgb, 0.0, 1.0, out=rgb)
    return rgb.astype(np.float32)


def to_uint8(rgb: np.ndarray) -> np.ndarray:
    """Convert a 0..1 float HxWx3 image to 0..255 uint8."""
    return np.clip(np.round(rgb * 255.0), 0, 255).astype(np.uint8)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("usage: python3 scripts/dng.py <file.dng>", file=sys.stderr)
        return 2
    image = load_dng(args[0])
    print(
        f"{image.path.name}: {image.width}x{image.height} "
        f"bit={image.bit_depth} pattern={image.pattern} "
        f"black={image.black} white={image.white} wb={image.wb}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
