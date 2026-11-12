#!/usr/bin/env python3
"""ISO 12233 slanted-edge MTF50 (pure NumPy).

Implements the standard slanted-edge pipeline:

    edge detection -> least-squares edge angle -> oversampled ESF ->
    LSF = d(ESF)/dx -> Hamming window -> 4x-oversampled FFT ->
    -3 dB crossing (MTF50)

Returns :math:`\\text{MTF50}` in cycles/pixel together with edge angle,
contrast and overshoot.  Self-contained; no OpenCV/rawpy.  Best used
comparatively (soft vs. crisp) rather than as an absolute lab measurement.

CLI
---
    python3 scripts/mtf.py <image.png>   # prints mtf50 + angle
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image  # type: ignore

#: FFT oversampling factor for the LSF spectrum.
_OVERSAMPLE = 4
#: Fraction of the peak MTF defining the -3 dB point.
_MTF50_FRAC = 0.5


@dataclass
class SlantedEdgeResult:
    mtf50: float | None      # cycles/pixel, None when no usable edge found
    angle_deg: float | None  # edge angle relative to the image x-axis
    contrast: float | None   # (max-min)/(max+min) of the ESF
    overshoot: float | None  # (ESF peak - ESF plateau) / plateau height


def _fit_edge(points_yx: np.ndarray) -> tuple[float, float, float] | None:
    """Fit ``x = a*y + b`` to edge points. Returns (a, b, angle_deg) or None."""
    if points_yx.shape[0] < 10:
        return None
    y = points_yx[:, 0].astype(np.float64)
    x = points_yx[:, 1].astype(np.float64)
    ayy = float(np.mean(y * y)) - float(np.mean(y)) ** 2
    if ayy <= 1e-9:
        return None
    a = (float(np.mean(x * y)) - float(np.mean(x)) * float(np.mean(y))) / ayy
    b = float(np.mean(x)) - a * float(np.mean(y))
    angle_deg = float(np.degrees(np.arctan(a)))
    return a, b, angle_deg


def _edge_points(image: np.ndarray):
    """Return (ys, xs) of the detected slanted edge (x varies per row)."""
    gy, gx = np.gradient(image.astype(np.float64))
    resp_x = float(np.abs(gx).max())
    resp_y = float(np.abs(gy).max())
    working = image
    grad_x = np.abs(gx)
    if resp_y > resp_x * 1.2:
        working = image.T
        grad_x = np.abs(np.gradient(working.astype(np.float64), axis=1))
    row_strength = grad_x.max(axis=1)
    thr = 0.2 * float(row_strength.max()) if row_strength.size else 0.0
    if thr <= 0:
        return None
    valid = row_strength > thr
    ys = np.nonzero(valid)[0]
    xs = np.argmax(grad_x, axis=1)[valid]
    if ys.size < 10:
        return None
    return ys, xs, working


def slanted_edge_mtf50(roi_gray: np.ndarray) -> dict[str, Any]:
    """Compute MTF50 for a slanted edge in ``roi_gray`` (HxW, 0..1).

    Returns dict with keys ``mtf50``, ``angle_deg``, ``contrast``,
    ``overshoot``.  ``mtf50`` is ``None`` when no usable edge is detected.
    """
    image = np.asarray(roi_gray, dtype=np.float64)
    if image.ndim != 2 or image.size == 0:
        return _empty()

    detected = _edge_points(image)
    if detected is None:
        return _empty()
    ys, xs, working = detected

    fit = _fit_edge(np.column_stack([ys, xs]))
    if fit is None:
        return _empty()
    a, b, angle_deg = fit

    h, w = working.shape
    offsets = np.arange(-2.5, 2.5 + 1e-9, 0.125)  # sub-pixel bins (px)
    esf_num = np.zeros_like(offsets, dtype=np.float64)
    esf_den = np.zeros_like(offsets, dtype=np.float64)

    for i, y in enumerate(ys):
        xe = a * y + b
        if xe < 1.0 or xe > w - 2.0:
            continue
        row = working[y, :]
        for k, off in enumerate(offsets):
            xi = xe + off
            xi0 = int(np.floor(xi))
            if xi0 < 0 or xi0 + 1 >= w:
                continue
            f = xi - xi0
            val = row[xi0] * (1.0 - f) + row[xi0 + 1] * f
            esf_num[k] += val
            esf_den[k] += 1.0

    valid = esf_den > 3
    if not np.any(valid):
        return _empty(angle_deg)
    esf = np.divide(
        esf_num, esf_den, out=np.full_like(esf_num, np.nan), where=valid
    )

    first = int(np.argmax(valid))
    last = len(valid) - int(np.argmax(valid[::-1]))
    esf = esf[first:last]
    offsets = offsets[first:last]
    if esf.size < 8:
        return _empty(angle_deg)

    lo = float(np.mean(esf[: max(2, esf.size // 8)]))
    hi = float(np.mean(esf[-max(2, esf.size // 8):]))
    span = hi - lo
    contrast = span / (hi + lo) if (hi + lo) > 0 else 0.0
    peak = float(np.max(esf))
    trough = float(np.min(esf))
    plateau = hi if hi > lo else lo
    overshoot = (peak - plateau) / abs(plateau) if plateau != 0 else 0.0

    lsf = np.gradient(esf, offsets[1] - offsets[0])
    n = lsf.size
    n_fft = n * _OVERSAMPLE
    window = np.hamming(n)
    spectrum = np.abs(np.fft.rfft(lsf * window, n=n_fft))
    if spectrum.size > 0 and spectrum[0] > 0:
        spectrum = spectrum / spectrum[0]
    freqs = np.fft.rfftfreq(n_fft, d=(offsets[1] - offsets[0]))

    mtf50: float | None = None
    if spectrum.size > 1 and spectrum.max() > 0:
        crossings = np.nonzero(spectrum <= _MTF50_FRAC)[0]
        if crossings.size > 0:
            i = int(crossings[0])
            if i > 0 and spectrum[i] != spectrum[i - 1]:
                t = (_MTF50_FRAC - spectrum[i - 1]) / (spectrum[i] - spectrum[i - 1])
                mtf50 = float(freqs[i - 1] + t * (freqs[i] - freqs[i - 1]))
            else:
                mtf50 = float(freqs[i])
    # MTF50 cannot exceed the sampling Nyquist (0.5 cy/px); anything higher is
    # noise, not a resolvable edge.
    if mtf50 is not None and mtf50 > 0.5:
        mtf50 = None

    return {
        "mtf50": mtf50,
        "angle_deg": angle_deg,
        "contrast": float(contrast),
        "overshoot": float(overshoot),
    }


def _empty(angle_deg: float | None = None) -> dict[str, Any]:
    return {"mtf50": None, "angle_deg": angle_deg,
            "contrast": None, "overshoot": None}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("usage: python3 scripts/mtf.py <image.png>", file=sys.stderr)
        return 2
    with Image.open(args[0]) as im:
        gray = np.asarray(im.convert("L"), dtype=np.float64) / 255.0
    result = slanted_edge_mtf50(gray)
    print(
        f"{args[0]}: mtf50={result['mtf50']} angle={result['angle_deg']} "
        f"contrast={result['contrast']} overshoot={result['overshoot']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
