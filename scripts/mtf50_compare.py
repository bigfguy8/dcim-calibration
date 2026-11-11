#!/usr/bin/env python3
"""
mtf50_compare.py — Slanted-edge MTF50 comparison between two camera configs.

Estimates MTF50 (spatial frequency where Modulation Transfer Function drops
to 50%) using the ISO 12233 slanted-edge method on natural scene edges:

1. Register frame B to frame A (phase correlation on translation)
2. Detect strong edges (Sobel magnitude threshold)
3. For each edge pixel, extract intensity profile perpendicular to edge
4. Bin profiles into Edge Spread Function (ESF)
5. Differentiate ESF → Line Spread Function (LSF)
6. Windowed FFT of LSF → MTF
7. Find frequency where MTF = 0.5 → MTF50 (cycles/pixel)

Outputs structured JSON to analysis/reports/.

Usage
-----
    python3 scripts/mtf50_compare.py V3.jpg DSLR64.jpg --out report.json
    python3 scripts/mtf50_compare.py --latest 2 --dir /sdcard/DCIM/Camera
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
BLOCK = 32
EDGE_SOBEL_THRESH = 60.0
PROFILE_HALF_WIDTH = 6
ESF_BINS = 64


def load_gray(path: Path) -> "tuple[np.ndarray, np.ndarray]":
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f"cannot decode {path}")
    return img, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)


def register(ref_gray: np.ndarray, mov_gray: np.ndarray) -> "tuple[np.ndarray, float]":
    """Phase-correlation translation warp (mov -> ref)."""
    h, w = ref_gray.shape
    scale = 4
    size = (max(16, w // scale), max(16, h // scale))
    ref = cv2.GaussianBlur(
        cv2.resize(ref_gray, size, interpolation=cv2.INTER_AREA), (5, 5), 0
    ).astype(np.float32)
    mov = cv2.GaussianBlur(
        cv2.resize(mov_gray, size, interpolation=cv2.INTER_AREA), (5, 5), 0
    ).astype(np.float32)
    ref -= ref.mean()
    mov -= mov.mean()
    window = cv2.createHanningWindow(size, cv2.CV_32F)
    (dx, dy), response = cv2.phaseCorrelate(ref, mov, window)
    warp = np.array([[1.0, 0.0, -dx * scale], [0.0, 1.0, -dy * scale]],
                    dtype=np.float32)
    return warp, float(response)


def edge_profiles(gray: np.ndarray,
                  valid: "np.ndarray | None" = None) -> "tuple[np.ndarray, np.ndarray]":
    """Return (esf_x, esf_y) binned edge-spread-function samples."""
    h, w = gray.shape
    sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(sobelx * sobelx + sobely * sobely)

    # Collect profiles from strong edge pixels
    profiles: list[np.ndarray] = []
    for y in range(PROFILE_HALF_WIDTH + 2, h - PROFILE_HALF_WIDTH - 2):
        for x in range(PROFILE_HALF_WIDTH + 2, w - PROFILE_HALF_WIDTH - 2):
            if valid is not None and not valid[y, x]:
                continue
            if mag[y, x] < EDGE_SOBEL_THRESH:
                continue
            # Edge normal direction (gradient direction)
            gx = sobelx[y, x]
            gy = sobely[y, x]
            norm = np.hypot(gx, gy)
            if norm < 1.0:
                continue
            ux = gx / norm
            uy = gy / norm
            # Sample perpendicular to edge (along normal)
            offsets = np.arange(-PROFILE_HALF_WIDTH, PROFILE_HALF_WIDTH + 1)
            xs = np.clip(x + offsets * ux, 0, w - 1).astype(int)
            ys = np.clip(y + offsets * uy, 0, h - 1).astype(int)
            profile = gray[ys, xs]
            profiles.append(profile)

    if not profiles:
        return np.array([]), np.array([])

    profiles = np.array(profiles, dtype=np.float32)
    # Normalize each profile to [0, 1] by local min/max
    pmin = profiles.min(axis=1, keepdims=True)
    pmax = profiles.max(axis=1, keepdims=True)
    rng = np.where(pmax - pmin > 1e-3, pmax - pmin, 1.0)
    profiles = (profiles - pmin) / rng

    # Bin by position across the edge
    esf_x = np.arange(-PROFILE_HALF_WIDTH, PROFILE_HALF_WIDTH + 1, dtype=np.float32)
    esf_y = profiles.mean(axis=0)
    return esf_x, esf_y


def esf_to_mtf(esf_x: np.ndarray, esf_y: np.ndarray) -> "tuple[np.ndarray, np.ndarray]":
    """Differentiate ESF → LSF → windowed FFT → MTF."""
    if len(esf_x) < 8:
        return np.array([]), np.array([])

    # Sort by x
    order = np.argsort(esf_x)
    xs = esf_x[order]
    ys = esf_y[order]

    # Line spread function = derivative of ESF
    lsf = np.gradient(ys, xs)

    # Center LSF
    lsf = lsf - lsf.mean()

    # Hann window
    window = np.hanning(len(lsf))
    lsf_w = lsf * window

    # FFT
    n = len(lsf_w)
    mtf_complex = np.fft.rfft(lsf_w)
    mtf = np.abs(mtf_complex)
    mtf = mtf / mtf[0]  # Normalize MTF(0) = 1

    # Frequency axis (cycles/pixel)
    freqs = np.fft.rfftfreq(n, d=(xs[1] - xs[0]) if len(xs) > 1 else 1.0)
    return freqs, mtf


def mtf50(freqs: np.ndarray, mtf: np.ndarray) -> float:
    """Return frequency where MTF crosses 0.5, or 0 if never."""
    if len(mtf) == 0:
        return 0.0
    below = np.where(mtf <= 0.5)[0]
    if len(below) == 0:
        return float(freqs[-1]) if len(freqs) > 0 else 0.0
    i = below[0]
    if i == 0:
        return 0.0
    # Linear interpolation between MTF[i-1] > 0.5 and MTF[i] <= 0.5
    f0, f1 = freqs[i - 1], freqs[i]
    m0, m1 = mtf[i - 1], mtf[i]
    if m0 == m1:
        return float(f1)
    t = (0.5 - m0) / (m1 - m0)
    return float(f0 + t * (f1 - f0))


def exposure(path: Path) -> dict:
    try:
        from PIL import Image, ExifTags
        exif = Image.open(path).getexif()
        ifd = exif.get_ifd(0x8769)
        TAGS = {v: k for k, v in ExifTags.TAGS.items()}
        iso = ifd.get(TAGS.get("ISOSpeedRatings"), exif.get(TAGS.get("ISOSpeedRatings")))
        exp = ifd.get(TAGS.get("ExposureTime"), exif.get(TAGS.get("ExposureTime")))
        bright = ifd.get(TAGS.get("BrightnessValue"), exif.get(TAGS.get("BrightnessValue")))
        return {"iso": int(iso) if iso else None,
                "exposure_s": round(exp / 1, 5) if isinstance(exp, (int, float)) else None,
                "brightness": round(float(bright), 2) if bright else None}
    except Exception:
        return {"iso": None, "exposure_s": None, "brightness": None}


def compare(path_a: Path, path_b: Path, out_json: Path | None = None) -> dict:
    img_a, gray_a = load_gray(path_a)
    img_b, gray_b = load_gray(path_b)

    if gray_a.shape != gray_b.shape:
        raise RuntimeError(
            f"different resolutions: {gray_a.shape} vs {gray_b.shape}"
        )

    h, w = gray_a.shape
    warp, response = register(gray_a, gray_b)
    off_y, off_x = int(round(-warp[1, 2])), int(round(-warp[0, 2]))

    # Build valid overlap mask by sampling at offset positions
    pairs = []
    for y in range(0, h - BLOCK, BLOCK):
        for x in range(0, w - BLOCK, BLOCK):
            by, bx = y + off_y, x + off_x
            if 0 <= by <= h - BLOCK and 0 <= bx <= w - BLOCK:
                pairs.append((y, x, by, bx))
    overlap_pct = len(pairs) / max(1, (h // BLOCK) * (w // BLOCK)) * 100

    # Edge profiles on native pixels (no resampling)
    flat_a = [(y, x) for y, x, _, _ in pairs][:4000]
    flat_b = [(by, bx) for _, _, by, bx in pairs][:4000]

    # Use full frames for edge detection (edges are translation-invariant)
    _, esf_y_a = edge_profiles(gray_a)
    _, esf_y_b = edge_profiles(gray_b)

    freqs_a, mtf_a = esf_to_mtf(np.arange(-PROFILE_HALF_WIDTH,
                                          PROFILE_HALF_WIDTH + 1,
                                          dtype=np.float32), esf_y_a)
    freqs_b, mtf_b = esf_to_mtf(np.arange(-PROFILE_HALF_WIDTH,
                                          PROFILE_HALF_WIDTH + 1,
                                          dtype=np.float32), esf_y_b)

    mtf50_a = mtf50(freqs_a, mtf_a)
    mtf50_b = mtf50(freqs_b, mtf_b)

    # Noise: flat-block sigma on matched flat blocks
    def flat_noise(gray, coords):
        sig = []
        for y, x in coords[:3000]:
            b = gray[y:y + BLOCK, x:x + BLOCK].astype(np.float64)
            if float(b.std()) < 6.0:
                lap = cv2.Laplacian(b, cv2.CV_64F)
                sig.append(float(lap.std() / np.sqrt(6.0)))
        return float(np.median(sig)) if sig else None

    noise_a = flat_noise(gray_a, flat_a)
    noise_b = flat_noise(gray_b, flat_b)

    result = {
        "compared_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "a": {"file": path_a.name, **exposure(path_a),
              "mtf50": round(mtf50_a, 4),
              "noise_sigma": round(noise_a, 4) if noise_a else None,
              "overlap_pct": round(overlap_pct, 1),
              "phase_response": round(response, 4)},
        "b": {"file": path_b.name, **exposure(path_b),
              "mtf50": round(mtf50_b, 4),
              "noise_sigma": round(noise_b, 4) if noise_b else None,
              "overlap_pct": round(overlap_pct, 1),
              "phase_response": round(response, 4)},
        "delta": {
            "mtf50_pct": round((mtf50_b - mtf50_a) / mtf50_a * 100, 1) if mtf50_a else None,
            "noise_pct": round((noise_b - noise_a) / noise_a * 100, 1)
            if noise_a and noise_b else None,
        },
    }
    result["winner"] = "b" if mtf50_b > mtf50_a else ("a" if mtf50_a > mtf50_b else "tie")

    if out_json:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    return result


def print_report(result: dict) -> None:
    a, b, d = result["a"], result["b"], result["delta"]
    print(f"A: {a['file']}  ISO={a['iso']}  MTF50={a['mtf50']:.4f} cyc/px  "
          f"noise_sigma={a['noise_sigma']}")
    print(f"B: {b['file']}  ISO={b['iso']}  MTF50={b['mtf50']:.4f} cyc/px  "
          f"noise_sigma={b['noise_sigma']}")
    print(f"Registration: overlap={a['overlap_pct']}%  phase_response={a['phase_response']}")
    print(f"Delta: MTF50 {d['mtf50_pct']:+.1f}%  Noise {d['noise_pct']:+.1f}%")
    print(f"Winner: {result['winner']} (higher MTF50 = sharper)")


def main() -> int:
    parser = argparse.ArgumentParser(description="MTF50 side-by-side comparison")
    parser.add_argument("a", nargs="?", type=Path, help="reference image (A)")
    parser.add_argument("b", nargs="?", type=Path, help="comparison image (B)")
    parser.add_argument("--latest", type=int, default=0,
                        help="compare the N newest images in --dir")
    parser.add_argument("--dir", type=Path, default=Path("/sdcard/DCIM/Camera"))
    parser.add_argument("--out", type=Path, default=None,
                        help="output JSON path")
    args = parser.parse_args()

    try:
        if args.latest:
            files = sorted(
                (p for p in args.dir.iterdir()
                 if p.is_file() and p.suffix.lower() in IMAGE_EXTS),
                key=lambda p: p.stat().st_mtime,
            )[-args.latest:]
            if len(files) < 2:
                print(f"need 2 photos in {args.dir}, found {len(files)}",
                      file=sys.stderr)
                return 2
            path_a, path_b = files[-2], files[-1]
        elif args.a and args.b:
            path_a, path_b = args.a, args.b
        else:
            parser.error("give two images or --latest N")

        result = compare(path_a, path_b, args.out)
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print_report(result)
    if args.out:
        print(f"json: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
