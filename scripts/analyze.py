#!/usr/bin/env python3
"""Slanted-edge optical analysis for the MGC 8.9 (BSG) LXX521 / IMX682 pipeline.

For every captured frame this module reports:

* **MTF50** in cycles/pixel, measured with an ISO 12233-style slanted-edge
  transform (edge-angle estimation -> oversampled ESF -> LSF -> FFT).  Edges
  are classified as ``center`` or ``edge`` from their image position so that
  the two quality gates in the specification can be evaluated independently.
* **Per-channel noise sigma** (R/G/B + luma) in 8-bit DN, via a robust MAD
  estimate of the high-pass residual.  Scene texture is rejected by the
  median, so chart edges do not inflate the result.
* **Exposure statistics**: mean luma, highlight/shadow clipping and the
  5/50/95 luma percentiles.

OpenCV is used when importable, but is *not* required: loading and all
measurements fall back to NumPy/Pillow so the pipeline runs on a stock
Termux install.  DNG decoding uses ``rawpy`` when available; otherwise the
file is reported with ``status="skipped_no_raw_decoder"`` and its metadata
is still extracted through ``exiftool`` when present.

CLI
---
    python3 scripts/analyze.py <file-or-directory> [-o out.json]
                                [--recursive] [--profile TEX] [--camera back]
                                [--no-mtf]

When the target is a directory and ``-o`` is omitted the JSON is written to
``<directory>/analysis.json``; a single file prints to stdout.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

try:  # optional acceleration / extra formats
    import cv2  # type: ignore

    _HAS_CV2 = True
except Exception:  # pragma: no cover - depends on host packages
    cv2 = None  # type: ignore
    _HAS_CV2 = False

try:
    from PIL import Image  # type: ignore

    _HAS_PIL = True
except Exception:  # pragma: no cover
    Image = None  # type: ignore
    _HAS_PIL = False

try:
    import rawpy  # type: ignore

    _HAS_RAWPY = True
except Exception:  # pragma: no cover
    rawpy = None  # type: ignore
    _HAS_RAWPY = False


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}
RAW_EXTS = {".dng", ".cr2", ".nef", ".arw", ".raf", ".orf", ".rw2"}

#: MTF50 gate targets from the specification (cycles/pixel).
MTF50_GATE_CENTER = 0.30
MTF50_GATE_EDGE = 0.22

#: Pixel bin width (px) used to oversample the edge spread function.
_ESF_BIN_PX = 0.25
#: Half-width (px) of the search band around a detected edge.
_EDGE_BAND_HALF = 24


@dataclass
class LoadedImage:
    gray: np.ndarray  # float32, HxW, normalised to 0..1
    rgb: np.ndarray | None  # float32, HxWx3, normalised to 0..1
    bit_depth: int
    width: int
    height: int
    note: str = ""


# --------------------------------------------------------------------------- #
# Image loading
# --------------------------------------------------------------------------- #
def _luma(rgb: np.ndarray) -> np.ndarray:
    """Rec.709 luma for an HxWx3 float array."""
    return (
        0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    ).astype(np.float32)


def _normalise(arr: np.ndarray, bit_depth: int) -> np.ndarray:
    scale = float((1 << bit_depth) - 1)
    return np.clip(arr.astype(np.float32) / scale, 0.0, 1.0)


def _load_with_cv2(path: Path) -> LoadedImage | None:
    if not _HAS_CV2:
        return None
    raw = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if raw is None:
        return None
    if raw.ndim == 2:
        bit = 16 if raw.dtype == np.uint16 else 8
        gray = _normalise(raw, bit)
        return LoadedImage(gray, None, bit, raw.shape[1], raw.shape[0], "cv2")
    bit = 16 if raw.dtype == np.uint16 else 8
    rgb = _normalise(raw[..., :3][..., ::-1], bit)  # BGR -> RGB
    return LoadedImage(_luma(rgb), rgb, bit, raw.shape[1], raw.shape[0], "cv2")


def _load_with_pil(path: Path) -> LoadedImage | None:
    if not _HAS_PIL:
        return None
    with Image.open(path) as im:  # type: ignore[union-attr]
        im.load()
        arr = np.asarray(im)
    if arr.ndim == 2:
        bit = 16 if arr.dtype == np.uint16 else 8
        gray = _normalise(arr, bit)
        return LoadedImage(gray, None, bit, arr.shape[1], arr.shape[0], "pillow")
    if arr.ndim == 3 and arr.shape[2] >= 3:
        bit = 16 if arr.dtype == np.uint16 else 8
        rgb = _normalise(arr[..., :3], bit)
        return LoadedImage(_luma(rgb), rgb, bit, arr.shape[1], arr.shape[0], "pillow")
    return None


def _load_raw_with_rawpy(path: Path) -> LoadedImage | None:
    if not _HAS_RAWPY:
        return None
    with rawpy.imread(str(path)) as raw:  # type: ignore[union-attr]
        rgb16 = raw.postprocess(use_camera_wb=True, output_bps=16, no_auto_bright=True)
    rgb = _normalise(rgb16, 16)
    return LoadedImage(_luma(rgb), rgb, 16, rgb.shape[1], rgb.shape[0], "rawpy")


def load_image(path: Path) -> LoadedImage:
    """Decode an image into normalised grayscale/RGB with a bit-depth tag."""
    ext = path.suffix.lower()
    loaded: LoadedImage | None = None
    if ext in RAW_EXTS:
        loaded = _load_raw_with_rawpy(path)
    else:
        loaded = _load_with_cv2(path) or _load_with_pil(path)
    if loaded is None:
        if ext in RAW_EXTS:
            raise UnsupportedImage(
                "no RAW decoder available (install rawpy or convert to 16-bit TIFF)"
            )
        raise UnsupportedImage("no decoder available (install python-pillow or opencv)")
    return loaded


class UnsupportedImage(Exception):
    """Raised when a file cannot be decoded on this host."""


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #
_EXIF_ISO = 34855
_EXIF_EXPOSURE = 33434
_EXIF_FNUMBER = 33437
_EXIF_MODEL = 272
_EXIF_MAKE = 271
_EXIF_SOFTWARE = 305
_EXIF_DATETIME = 36867
_EXIF_FOCAL = 37386


def _tag(exif: Any, tag: int) -> Any:
    try:
        value = exif.get(tag)
    except Exception:
        return None
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace").strip("\x00 ")
    if isinstance(value, (tuple, list)) and len(value) == 1:
        return value[0]
    return value


def _exif_from_pil(path: Path) -> dict[str, Any]:
    if not _HAS_PIL:
        return {}
    try:
        with Image.open(path) as im:  # type: ignore[union-attr]
            exif = im.getexif()
            nested: Any = {}
            try:
                nested = exif.get_ifd(0x8769)
            except Exception:
                pass
    except Exception:
        return {}

    def pick(tag: int) -> Any:
        value = _tag(exif, tag)
        return value if value is not None else _tag(nested, tag)

    out: dict[str, Any] = {
        "iso": pick(_EXIF_ISO),
        "exposure_time_s": pick(_EXIF_EXPOSURE),
        "f_number": pick(_EXIF_FNUMBER),
        "focal_length_mm": pick(_EXIF_FOCAL),
        "camera_model": pick(_EXIF_MODEL),
        "camera_make": pick(_EXIF_MAKE),
        "software": pick(_EXIF_SOFTWARE),
        "captured_at": pick(_EXIF_DATETIME),
    }
    return {k: v for k, v in out.items() if v is not None}


def _exif_from_exiftool(path: Path) -> dict[str, Any]:
    tool = shutil.which("exiftool")
    if not tool:
        return {}
    try:
        proc = subprocess.run(
            [tool, "-json", "-n", "-ISO", "-ExposureTime", "-FNumber",
             "-FocalLength", "-Model", "-Make", "-Software", "-DateTimeOriginal",
             str(path)],
            capture_output=True, text=True, timeout=20, check=False,
        )
        payload = json.loads(proc.stdout or "[]")
    except Exception:
        return {}
    if not payload:
        return {}
    raw = payload[0]
    return {
        "iso": raw.get("ISO"),
        "exposure_time_s": raw.get("ExposureTime"),
        "f_number": raw.get("FNumber"),
        "focal_length_mm": raw.get("FocalLength"),
        "camera_model": raw.get("Model"),
        "camera_make": raw.get("Make"),
        "software": raw.get("Software"),
        "captured_at": raw.get("DateTimeOriginal"),
    }


def read_metadata(path: Path) -> dict[str, Any]:
    meta = _exif_from_pil(path)
    if not meta:
        meta = _exif_from_exiftool(path)
    if meta:
        return {k: v for k, v in meta.items() if v is not None}
    if path.suffix.lower() in RAW_EXTS:
        return _exif_from_exiftool(path)
    return {}


# --------------------------------------------------------------------------- #
# Signal helpers
# --------------------------------------------------------------------------- #
def _box_blur_1d(values: np.ndarray, width: int, axis: int = -1) -> np.ndarray:
    """Edge-padded moving average along ``axis`` (no SciPy required)."""
    if width <= 1:
        return values
    width = int(width) | 1
    pad = width // 2
    moved = np.moveaxis(np.asarray(values, dtype=np.float32), axis, -1)
    padded = np.pad(moved, ((0, 0), (pad, pad)), mode="edge")
    cumulative = np.cumsum(padded, axis=-1, dtype=np.float64)
    cumulative = np.concatenate(
        [np.zeros(cumulative.shape[:-1] + (1,)), cumulative], axis=-1
    )
    smoothed = (cumulative[..., width:] - cumulative[..., :-width]) / width
    return np.moveaxis(smoothed.astype(np.float32), -1, axis)


def _savitzky_golay_5(values: np.ndarray) -> np.ndarray:
    """5-point quadratic Savitzky-Golay smoothing (edge padded)."""
    kernel = np.array([-3.0, 12.0, 17.0, 12.0, -3.0], dtype=np.float32) / 35.0
    padded = np.pad(np.asarray(values, dtype=np.float32), 2, mode="edge")
    return np.convolve(padded, kernel, mode="valid").astype(np.float32)


def _top_peaks(profile: np.ndarray, count: int, min_distance: int) -> list[int]:
    """Indices of the strongest local maxima separated by ``min_distance``."""
    profile = np.asarray(profile, dtype=np.float64)
    if profile.size == 0:
        return []
    order = np.argsort(profile)[::-1]
    chosen: list[int] = []
    for index in order:
        index = int(index)
        if profile[index] <= 0:
            break
        if all(abs(index - other) >= min_distance for other in chosen):
            chosen.append(index)
        if len(chosen) >= count:
            break
    return chosen


def _robust_line_fit(xs: np.ndarray, ys: np.ndarray) -> tuple[float, float, float, int]:
    """Least-squares line with one MAD-based outlier rejection pass."""
    design = np.vstack([ys, np.ones_like(ys)]).T
    coeff, *_ = np.linalg.lstsq(design, xs, rcond=None)
    residual = xs - design @ coeff
    centred = residual - np.median(residual)
    mad = float(np.median(np.abs(centred)))
    if mad > 0:
        keep = np.abs(centred) <= 3.5 * 1.4826 * mad
    else:
        keep = np.ones_like(residual, dtype=bool)
    if keep.sum() >= 8:
        coeff, *_ = np.linalg.lstsq(design[keep], xs[keep], rcond=None)
        residual = xs[keep] - design[keep] @ coeff
    total = float(np.sum((xs - xs.mean()) ** 2)) + 1e-12
    r2 = 1.0 - float(np.sum(residual ** 2)) / total
    return float(coeff[0]), float(coeff[1]), r2, int(keep.sum())


# --------------------------------------------------------------------------- #
# MTF50
# --------------------------------------------------------------------------- #
def _esf_mtf50(distances: np.ndarray, values: np.ndarray) -> tuple[float, float]:
    """MTF50 (cycles/px) and DC contrast from an oversampled edge profile."""
    low, high = np.percentile(distances, [0.5, 99.5])
    low = max(float(low), -8.0)
    high = min(float(high), 8.0)
    if high - low < 2.0:
        return float("nan"), 0.0

    bin_edges = np.arange(low, high + _ESF_BIN_PX, _ESF_BIN_PX)
    n_bins = len(bin_edges) - 1
    if n_bins < 16:
        return float("nan"), 0.0

    index = np.digitize(distances, bin_edges) - 1
    valid = (index >= 0) & (index < n_bins)
    if valid.sum() < 100:
        return float("nan"), 0.0

    sums = np.bincount(index[valid], weights=values[valid], minlength=n_bins)[:n_bins]
    counts = np.bincount(index[valid], minlength=n_bins)[:n_bins]
    populated = counts >= 5
    if populated.sum() < 0.6 * n_bins:
        return float("nan"), 0.0

    esf = np.full(n_bins, np.nan, dtype=np.float32)
    esf[populated] = (sums[populated] / counts[populated]).astype(np.float32)
    centres = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    good = np.flatnonzero(populated)
    esf = np.interp(centres, centres[good], esf[good]).astype(np.float32)

    esf = _savitzky_golay_5(esf)
    lsf = np.gradient(esf)
    window = np.hanning(n_bins).astype(np.float32)

    spectrum = np.abs(np.fft.rfft(lsf * window))
    if spectrum[0] <= 0:
        return float("nan"), 0.0
    mtf = spectrum / spectrum[0]
    frequencies = np.fft.rfftfreq(n_bins, d=_ESF_BIN_PX)

    limit = frequencies <= 0.5
    frequencies = frequencies[limit]
    mtf = mtf[limit]

    below = np.flatnonzero(mtf < 0.5)
    if below.size == 0:
        return 0.5, float(esf[-1] - esf[0])
    i = int(below[0])
    if i == 0:
        return 0.0, float(esf[-1] - esf[0])
    f0, f1 = frequencies[i - 1], frequencies[i]
    m0, m1 = mtf[i - 1], mtf[i]
    if m0 == m1:
        return float(f0), float(esf[-1] - esf[0])
    crossing = f0 + (0.5 - m0) * (f1 - f0) / (m1 - m0)
    return float(crossing), float(esf[-1] - esf[0])


def _measure_vertical_edge(
    gray: np.ndarray, x0: int, half_band: int = _EDGE_BAND_HALF
) -> dict[str, Any] | None:
    """Measure a near-vertical slanted edge centred on column ``x0``."""
    height, width = gray.shape
    left = max(0, x0 - half_band)
    right = min(width, x0 + half_band)
    if right - left < 16:
        return None
    band = gray[:, left:right]
    band_w = band.shape[1]

    # Estimate the edge position on every (sub-sampled) row.
    step = max(1, height // 768)
    rows = np.arange(0, height, step)
    band = band[rows]
    smoothed = _box_blur_1d(_box_blur_1d(band, 5, axis=1), 5, axis=1)
    gradient = np.abs(np.diff(smoothed, axis=1))
    weights = gradient.sum(axis=1)
    threshold = float(np.median(weights)) * 0.3 + 1e-12
    centroids = (gradient * np.arange(gradient.shape[1])).sum(axis=1) / (weights + 1e-12)

    usable = (weights > threshold) & (centroids > 0.2 * band_w) & (centroids < 0.8 * band_w)
    if usable.sum() < 24:
        return None
    ys = rows[usable].astype(np.float64)
    xs = centroids[usable].astype(np.float64)
    slope, intercept, r2, samples = _robust_line_fit(xs, ys)
    if not math.isfinite(slope) or abs(slope) > 2.5 or r2 < 0.5:
        return None

    # Signed perpendicular distance from the fitted edge line (band-local x).
    pixel_x = np.arange(band_w, dtype=np.float32)[None, :]
    pixel_y = rows.astype(np.float32)[:, None]
    distances = (pixel_x - (slope * pixel_y + intercept)) / math.sqrt(1.0 + slope * slope)
    values = band.astype(np.float32)

    mtf50, contrast = _esf_mtf50(distances.ravel(), values.ravel())
    if not math.isfinite(mtf50) or contrast < 0.10:
        return None

    centre_x = float(intercept + slope * (height / 2.0)) + left
    region = "center" if 0.30 * width <= centre_x <= 0.70 * width else "edge"
    return {
        "mtf50_cpp": round(mtf50, 4),
        "region": region,
        "edge_x": round(centre_x, 1),
        "slope": round(slope, 4),
        "angle_deg": round(math.degrees(math.atan(slope)), 2),
        "contrast": round(float(contrast), 4),
        "fit_r2": round(r2, 3),
        "samples": samples,
    }


def measure_mtf50(gray: np.ndarray) -> dict[str, Any]:
    """Detect the strongest slanted edges and return per-region MTF50.

    Returns ``mtf50_center`` / ``mtf50_edge`` (None when no usable edge is
    found in that region) plus a ``candidates`` list for traceability.
    """
    height, width = gray.shape
    if height < 64 or width < 64:
        return {"mtf50_center": None, "mtf50_edge": None, "candidates": []}

    response_x = np.abs(np.diff(gray, axis=1)).sum(axis=0)
    response_y = np.abs(np.diff(gray, axis=0)).sum(axis=1)

    transpose = float(response_y.max()) > float(response_x.max()) * 1.2
    working = gray.T if transpose else gray
    profile = response_y if transpose else response_x
    profile = _box_blur_1d(profile[None, :], 5, axis=1)[0]

    peaks = _top_peaks(profile, count=12, min_distance=max(32, working.shape[1] // 24))
    candidates: list[dict[str, Any]] = []
    for peak in peaks:
        result = _measure_vertical_edge(working, peak)
        if result is None:
            continue
        if transpose:
            # Region classification stays valid after transposition because
            # both dimensions are normalised independently by position; keep
            # the measured values but mark the orientation.
            result["orientation"] = "horizontal"
        else:
            result["orientation"] = "vertical"
        candidates.append(result)

    center = [c for c in candidates if c["region"] == "center"]
    edge = [c for c in candidates if c["region"] == "edge"]
    best_center = max(center, key=lambda c: c["contrast"] * c["fit_r2"], default=None)
    best_edge = max(edge, key=lambda c: c["contrast"] * c["fit_r2"], default=None)

    return {
        "mtf50_center": best_center["mtf50_cpp"] if best_center else None,
        "mtf50_edge": best_edge["mtf50_cpp"] if best_edge else None,
        "center_edge": best_center,
        "peripheral_edge": best_edge,
        "candidates": candidates,
    }


# --------------------------------------------------------------------------- #
# Noise & exposure
# --------------------------------------------------------------------------- #
def _channel_noise(channel: np.ndarray) -> float:
    """Robust sigma in 8-bit DN for a normalised (0..1) channel."""
    if channel.size < 1024:
        return float("nan")
    stride = max(1, int(round(math.sqrt(channel.size / 250_000.0))))
    sample = channel[::stride, ::stride].astype(np.float32)
    residual = sample - _box_blur_1d(_box_blur_1d(sample, 5, axis=0), 5, axis=1)
    centred = residual - np.median(residual)
    sigma = 1.4826 * float(np.median(np.abs(centred)))
    # Undo the variance reduction of the 5x5 box used to build the residual.
    sigma /= math.sqrt(1.0 - 1.0 / 25.0)
    return sigma * 255.0


def measure_noise(rgb: np.ndarray | None, gray: np.ndarray) -> dict[str, float]:
    if rgb is None:
        sigma = _channel_noise(gray)
        return {"r": sigma, "g": sigma, "b": sigma, "luma": sigma}
    return {
        "r": _channel_noise(rgb[..., 0]),
        "g": _channel_noise(rgb[..., 1]),
        "b": _channel_noise(rgb[..., 2]),
        "luma": _channel_noise(gray),
    }


def measure_exposure(rgb: np.ndarray | None, gray: np.ndarray) -> dict[str, float]:
    luma = gray * 255.0
    if rgb is None:
        peak = luma
        floor = luma
    else:
        peak = rgb.max(axis=2) * 255.0
        floor = rgb.min(axis=2) * 255.0
    return {
        "mean_luma": float(luma.mean()),
        "luma_p05": float(np.percentile(luma, 5)),
        "luma_p50": float(np.percentile(luma, 50)),
        "luma_p95": float(np.percentile(luma, 95)),
        "highlight_clipping_pct": float((peak >= 254.0).mean() * 100.0),
        "shadow_clipping_pct": float((floor <= 1.0).mean() * 100.0),
    }


# --------------------------------------------------------------------------- #
# Record assembly
# --------------------------------------------------------------------------- #
_SESSION_RE = re.compile(r"(\d{8}[_-]\d{6})")
_ISO_RE = re.compile(r"iso[\s_-]*(\d+)", re.IGNORECASE)
_PROFILE_RE = re.compile(r"(LXX521[_-](TEX|AI))", re.IGNORECASE)
_CAMERA_RE = re.compile(r"(front|back|rear|main|tele|wide|macro)", re.IGNORECASE)


def _infer_session(path: Path, override: str | None) -> str:
    if override:
        return override
    for parent in path.parents:
        match = _SESSION_RE.search(parent.name)
        if match:
            return match.group(1)
    return "unknown"


def _infer_profile(path: Path, override: str | None) -> str:
    if override:
        return override
    match = _PROFILE_RE.search(str(path))
    if match:
        return match.group(2).upper()
    for parent in path.parents:
        sidecar = parent / "session.json"
        if sidecar.is_file():
            try:
                payload = json.loads(sidecar.read_text())
                if payload.get("profile"):
                    return str(payload["profile"]).upper()
            except Exception:
                pass
    if re.search(r"\bAI\b", str(path)):
        return "AI"
    if re.search(r"\bTEX\b", str(path)):
        return "TEX"
    return "unknown"


def _infer_camera(path: Path, metadata: dict[str, Any], override: str | None) -> str:
    if override:
        return override
    match = _CAMERA_RE.search(path.name)
    if match:
        token = match.group(1).lower()
        return "back_main" if token in {"back", "rear", "main"} else token
    model = str(metadata.get("camera_model") or "")
    if "front" in model.lower():
        return "front"
    return "back_main"


def _infer_iso(path: Path, metadata: dict[str, Any]) -> int | None:
    value = metadata.get("iso")
    try:
        if value is not None:
            return int(float(value))
    except (TypeError, ValueError):
        pass
    match = _ISO_RE.search(path.name)
    return int(match.group(1)) if match else None


def _json_safe(value: Any) -> Any:
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    # PIL returns EXIF rationals as IFDRational, which json cannot encode.
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        try:
            return float(value.numerator) / float(value.denominator)
        except (TypeError, ValueError, ZeroDivisionError):
            return None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def analyse_file(
    path: Path,
    *,
    profile: str | None = None,
    camera: str | None = None,
    session: str | None = None,
    compute_mtf: bool = True,
) -> dict[str, Any]:
    metadata = read_metadata(path)
    record: dict[str, Any] = {
        "file": path.name,
        "path": str(path),
        "session": _infer_session(path, session),
        "profile": _infer_profile(path, profile),
        "camera": _infer_camera(path, metadata, camera),
        "iso": _infer_iso(path, metadata),
        "captured_at": metadata.get("captured_at"),
        "exposure_time_s": metadata.get("exposure_time_s"),
        "f_number": metadata.get("f_number"),
        "focal_length_mm": metadata.get("focal_length_mm"),
        "software": metadata.get("software"),
    }

    try:
        image = load_image(path)
    except UnsupportedImage as exc:
        record.update(
            {
                "status": "skipped_no_raw_decoder"
                if path.suffix.lower() in RAW_EXTS
                else "skipped_undecodable",
                "reason": str(exc),
                "mtf50_center": None,
                "mtf50_edge": None,
                "mtf50_cpp": None,
                "mtf50_region": None,
                "noise_sigma": None,
                "mean_luma": None,
                "highlight_clipping_pct": None,
                "shadow_clipping_pct": None,
            }
        )
        return _json_safe(record)

    record.update(
        {
            "width": image.width,
            "height": image.height,
            "bit_depth": image.bit_depth,
            "decoder": image.note,
            "status": "ok",
        }
    )
    record.update(measure_exposure(image.rgb, image.gray))
    record["noise_sigma"] = measure_noise(image.rgb, image.gray)
    record["noise_sigma_green"] = record["noise_sigma"]["g"]

    if compute_mtf:
        mtf = measure_mtf50(image.gray)
        record["mtf50_center"] = mtf["mtf50_center"]
        record["mtf50_edge"] = mtf["mtf50_edge"]
        record["mtf50_cpp"] = mtf["mtf50_center"] or mtf["mtf50_edge"]
        record["mtf50_region"] = (
            "center" if mtf["mtf50_center"] is not None else
            "edge" if mtf["mtf50_edge"] is not None else None
        )
        record["mtf_candidates"] = mtf["candidates"]
    else:
        record["mtf50_center"] = None
        record["mtf50_edge"] = None
        record["mtf50_cpp"] = None
        record["mtf50_region"] = None

    return _json_safe(record)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def iter_images(target: Path, recursive: bool) -> Iterable[Path]:
    extensions = IMAGE_EXTS | RAW_EXTS
    if target.is_file():
        yield target
        return
    pattern = "**/*" if recursive else "*"
    for path in sorted(target.glob(pattern)):
        if path.is_file() and path.suffix.lower() in extensions:
            yield path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slanted-edge MTF50, per-channel noise and exposure analysis."
    )
    parser.add_argument("target", type=Path, help="image file or directory")
    parser.add_argument("-o", "--output", type=Path, help="output JSON path")
    parser.add_argument("--recursive", action="store_true", help="walk sub-directories")
    parser.add_argument("--profile", help="override profile label (TEX/AI)")
    parser.add_argument("--camera", help="override camera label")
    parser.add_argument("--session", help="override session id")
    parser.add_argument(
        "--no-mtf", action="store_true", help="skip MTF50 (faster batch runs)"
    )
    parser.add_argument("--pretty", action="store_true", help="indent JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target: Path = args.target
    if not target.exists():
        print(f"[-] target not found: {target}", file=sys.stderr)
        return 2

    images = list(iter_images(target, args.recursive))
    if not images:
        print(f"[-] no images found under: {target}", file=sys.stderr)
        return 2

    records = [
        analyse_file(
            path,
            profile=args.profile,
            camera=args.camera,
            session=args.session,
            compute_mtf=not args.no_mtf,
        )
        for path in images
    ]

    payload = {
        "schema_version": 1,
        "analyzer": "analyze.py",
        "target": str(target),
        "image_count": len(records),
        "records": records,
    }
    text = json.dumps(_json_safe(payload), indent=2 if args.pretty else None)

    output = args.output
    if output is None and target.is_dir():
        output = target / "analysis.json"
    if output is None:
        print(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n")
        print(f"[*] analysed {len(records)} image(s) -> {output}")

    failures = [r for r in records if r.get("status") != "ok"]
    if failures:
        print(
            f"[!] {len(failures)} file(s) could not be fully analysed; see status fields",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
