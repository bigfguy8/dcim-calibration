#!/usr/bin/env python3
"""compare_photos.py — objective A/B comparison of two camera configs.

Comparing two profiles by eye is unreliable: exposure, focus and framing all
change between shots.  This script removes those confounders:

1. the second image is registered to the first (ECC, euclidean model);
2. both are measured only on regions that are *matched* in the two frames;
3. flat regions give a noise estimate, textured regions give a detail
   estimate, so a profile that only blurs the frame cannot look like a win.

Reported per image
------------------
* ``noise_flat``   median sigma in matched flat blocks (lower is better)
* ``noise_chroma`` median chroma sigma in the same blocks (lower is better)
* ``detail``       mean gradient energy in matched textured blocks
                   (higher is better)
* ``sharp_lap``    Laplacian variance over the whole frame
* ``score``        detail / noise_flat — a single figure of merit

Usage
-----
    python3 scripts/compare_photos.py A.jpg B.jpg
    python3 scripts/compare_photos.py --latest 2      # two newest in DCIM
    python3 scripts/compare_photos.py A.jpg B.jpg --json out.json --crops DIR

Exit codes: 0 = compared, 1 = error, 2 = not enough photos.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ExifTags

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
BLOCK = 32
FLAT_STD = 6.0
TEXTURE_STD = 24.0
EXIF_TAGS = {v: k for k, v in ExifTags.TAGS.items()}


def exposure(path: Path) -> dict:
    """ISO / shutter / brightness, best effort."""
    try:
        exif = Image.open(path).getexif()
        ifd = exif.get_ifd(0x8769)
    except Exception:  # noqa: BLE001 - EXIF is optional
        return {"iso": None, "exposure_s": None, "brightness": None}

    def get(name: str):
        tag = EXIF_TAGS.get(name)
        if tag is None:
            return None
        return ifd.get(tag, exif.get(tag))

    iso = get("ISOSpeedRatings") or get("PhotographicSensitivity")
    exp = get("ExposureTime")
    bright = get("BrightnessValue")
    out = {"iso": None, "exposure_s": None, "brightness": None}
    try:
        out["iso"] = int(iso) if iso is not None else None
    except (TypeError, ValueError):
        pass
    try:
        if isinstance(exp, tuple) and len(exp) == 2 and exp[1]:
            out["exposure_s"] = round(exp[0] / exp[1], 5)
        elif exp is not None:
            out["exposure_s"] = round(float(exp), 5)
    except (TypeError, ValueError, ZeroDivisionError):
        pass
    try:
        out["brightness"] = round(float(bright), 2) if bright is not None else None
    except (TypeError, ValueError):
        pass
    return out


def load_gray(path: Path) -> "tuple[np.ndarray, np.ndarray]":
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f"cannot decode {path}")
    return img, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def register(ref_gray: np.ndarray, mov_gray: np.ndarray) -> "tuple[np.ndarray, float]":
    """Estimate a translation mapping *mov* onto *ref* (phase correlation).

    Phase correlation on a blurred, downscaled frame is far more robust than
    ECC on 12 MP images, and translation is the only motion that matters when
    both shots are handheld stills of the same scene.
    """
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
    # phaseCorrelate reports how far *mov* is displaced from *ref*; the warp
    # that brings mov back onto ref is the negative of that.
    warp = np.array(
        [[1.0, 0.0, -dx * scale], [0.0, 1.0, -dy * scale]], dtype=np.float32
    )
    return warp, float(response)


def measure(gray: np.ndarray, yuv: np.ndarray,
            coords: "list[tuple[int, int]]", kind: str) -> dict:
    """Noise (flat blocks) or detail (textured blocks) over *coords*."""
    noise, chroma, detail = [], [], []
    for y, x in coords:
        b = gray[y : y + BLOCK, x : x + BLOCK].astype(np.float64)
        if kind == "flat":
            lap = cv2.Laplacian(b, cv2.CV_64F)
            noise.append(lap.std() / np.sqrt(6.0))
            u = yuv[y : y + BLOCK, x : x + BLOCK, 1].astype(np.float64)
            v = yuv[y : y + BLOCK, x : x + BLOCK, 2].astype(np.float64)
            chroma.append(0.5 * (u.std() + v.std()))
        else:
            gx = cv2.Sobel(b, cv2.CV_64F, 1, 0, ksize=3)
            gy = cv2.Sobel(b, cv2.CV_64F, 0, 1, ksize=3)
            detail.append(float(np.mean(np.sqrt(gx * gx + gy * gy))))

    return {
        "blocks": len(coords),
        "noise_flat": round(float(np.median(noise)), 3) if noise else None,
        "noise_chroma": round(float(np.median(chroma)), 2) if chroma else None,
        "detail": round(float(np.median(detail)), 2) if detail else None,
        "sharp_lap": round(float(cv2.Laplacian(gray.astype(np.float64),
                                               cv2.CV_64F).var()), 1),
    }


def pct(new, old) -> str:
    if new is None or old is None or not old:
        return "n/a"
    return f"{(new - old) / old * 100:+.1f}%"


def compare(path_a: Path, path_b: Path, crop_dir: "Path | None") -> dict:
    img_a, gray_a = load_gray(path_a)
    img_b, gray_b = load_gray(path_b)
    if gray_a.shape != gray_b.shape:
        raise RuntimeError(
            f"different resolutions: {gray_a.shape} vs {gray_b.shape}"
        )

    warp, response = register(gray_a, gray_b)
    h, w = gray_a.shape
    # register() returns the warp that brings B onto A; for a pure
    # translation the inverse offset is simply the negative, so B can be
    # sampled at its own native pixels instead of being resampled.
    off_y, off_x = int(round(-warp[1, 2])), int(round(-warp[0, 2]))

    pairs = []
    for y in range(0, h - BLOCK, BLOCK):
        for x in range(0, w - BLOCK, BLOCK):
            by, bx = y + off_y, x + off_x
            if not (0 <= by <= h - BLOCK and 0 <= bx <= w - BLOCK):
                continue
            pairs.append((
                y, x, by, bx,
                float(gray_a[y:y + BLOCK, x:x + BLOCK].std()),
                float(gray_b[by:by + BLOCK, bx:bx + BLOCK].std()),
            ))

    flat_a = [(y, x) for y, x, _, _, sa, sb in pairs
              if sa < FLAT_STD and sb < FLAT_STD][:6000]
    flat_b = [(by, bx) for _, _, by, bx, sa, sb in pairs
              if sa < FLAT_STD and sb < FLAT_STD][:6000]
    tex_a = [(y, x) for y, x, _, _, sa, sb in pairs
             if sa >= TEXTURE_STD and sb >= TEXTURE_STD][:6000]
    tex_b = [(by, bx) for _, _, by, bx, sa, sb in pairs
             if sa >= TEXTURE_STD and sb >= TEXTURE_STD][:6000]
    if not flat_a:
        raise RuntimeError("no matched flat blocks; frames are too different")
    if float(len(pairs)) / max(1, (h // BLOCK) * (w // BLOCK)) < 0.5:
        raise RuntimeError("registered overlap below 50% of the frame")

    yuv_a = cv2.cvtColor(img_a, cv2.COLOR_BGR2YUV)
    yuv_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2YUV)

    def stats(gray, yuv, flat_coords, tex_coords):
        flat = measure(gray, yuv, flat_coords, "flat")
        tex = measure(gray, yuv, tex_coords, "detail")
        return {
            "flat_blocks": flat["blocks"],
            "texture_blocks": tex["blocks"],
            "noise_flat": flat["noise_flat"],
            "noise_chroma": flat["noise_chroma"],
            "detail": tex["detail"],
            "sharp_lap": flat["sharp_lap"],
        }

    stats_a = stats(gray_a, yuv_a, flat_a, tex_a)
    stats_b = stats(gray_b, yuv_b, flat_b, tex_b)

    for s in (stats_a, stats_b):
        s["score"] = (
            round(s["detail"] / s["noise_flat"], 2)
            if s["detail"] and s["noise_flat"] else None
        )

    if crop_dir is not None:
        crop_dir.mkdir(parents=True, exist_ok=True)
        coords = tex_a or flat_a
        if coords:
            cy = max(0, min(int(np.median([c[0] for c in coords])), h - 600))
            cx = max(0, min(int(np.median([c[1] for c in coords])), w - 800))
            by = max(0, min(cy + off_y, h - 600))
            bx = max(0, min(cx + off_x, w - 800))
            cv2.imwrite(str(crop_dir / "crop_A.png"), img_a[cy:cy + 600, cx:cx + 800])
            cv2.imwrite(str(crop_dir / "crop_B.png"), img_b[by:by + 600, bx:bx + 800])

    return {
        "a": {"file": path_a.name, **exposure(path_a), **stats_a},
        "b": {"file": path_b.name, **exposure(path_b), **stats_b},
        "registration": {
            "dx": round(float(warp[0, 2]), 1),
            "dy": round(float(warp[1, 2]), 1),
            "phase_response": round(response, 4),
            "overlap_pct": round(
                len(pairs) / max(1, (h // BLOCK) * (w // BLOCK)) * 100, 1
            ),
        },
        "delta": {
            "noise_flat": pct(stats_b["noise_flat"], stats_a["noise_flat"]),
            "noise_chroma": pct(stats_b["noise_chroma"], stats_a["noise_chroma"]),
            "detail": pct(stats_b["detail"], stats_a["detail"]),
            "sharp_lap": pct(stats_b["sharp_lap"], stats_a["sharp_lap"]),
            "score": pct(stats_b["score"], stats_a["score"]),
        },
    }


def print_report(result: dict) -> None:
    a, b, reg, delta = result["a"], result["b"], result["registration"], result["delta"]
    print(f"A: {a['file']}  ISO={a['iso']} exp={a['exposure_s']}")
    print(f"B: {b['file']}  ISO={b['iso']} exp={b['exposure_s']}")
    print(f"registration: dx={reg['dx']} dy={reg['dy']} overlap={reg['overlap_pct']}%")
    print()
    rows = [
        ("noise_flat", "flat noise sigma", "lower"),
        ("noise_chroma", "chroma noise sigma", "lower"),
        ("detail", "detail (grad energy)", "higher"),
        ("sharp_lap", "Laplacian var (frame)", "higher"),
        ("score", "detail / noise", "higher"),
    ]
    print(f"{'metric':24} {'A':>10} {'B':>10} {'B vs A':>10}")
    print("-" * 57)
    for key, label, _ in rows:
        print(f"{label:24} {str(a[key]):>10} {str(b[key]):>10} {delta[key]:>10}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Objective A/B of two captures")
    parser.add_argument("a", nargs="?", type=Path, help="reference image (A)")
    parser.add_argument("b", nargs="?", type=Path, help="comparison image (B)")
    parser.add_argument("--latest", type=int, default=0,
                        help="compare the N newest images in --dir instead")
    parser.add_argument("--dir", type=Path, default=Path("/sdcard/DCIM/Camera"))
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--crops", type=Path, default=None,
                        help="write aligned 100%% crops to this directory")
    args = parser.parse_args()

    try:
        if args.latest:
            files = sorted(
                (p for p in args.dir.iterdir()
                 if p.is_file() and p.suffix.lower() in IMAGE_EXTS),
                key=lambda p: p.stat().st_mtime,
            )[-args.latest:]
            if len(files) < 2:
                print(f"need 2 photos in {args.dir}, found {len(files)}", file=sys.stderr)
                return 2
            path_a, path_b = files[-2], files[-1]
        elif args.a and args.b:
            path_a, path_b = args.a, args.b
        else:
            parser.error("give two images or --latest N")

        result = compare(path_a, path_b, args.crops)
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    result["compared_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    print_report(result)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"json: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
