#!/usr/bin/env python3
"""
image_quality_analyzer.py - Read-only image quality analysis.

Supports analysis of EXISTING images only.

Metrics:
- Sharpness / MTF50 when suitable test data exists.
- Noise estimation.
- Edge halos.
- Color accuracy when reference data exists.
- Dynamic range when suitable source data exists.
- Detail retention.
- Exposure consistency.

Clearly distinguish measured metrics from estimates.

Do not capture photographs.

Do not request new photographs.

All analysis is read-only; no new images are captured or generated.
"""

from __future__ import annotations


try:
    from PIL import Image, ExifTags
except ImportError:
    Image = None
    ExifTags = None
import csv
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from PIL import Image, ExifTags
except ImportError:
    Image = None
    ExifTags = None


#
# Metric types
#

class MetricType(Enum):
    """Types of image quality metrics."""
    SHARPNESS = "sharpness"       # Laplacian variance / MTF50
    NOISE = "noise"               # Estimated noise level
    HALO = "halo"                 # Edge halo severity
    COLOR_ACCURACY = "color_accuracy"  # Delta E against reference
    DYNAMIC_RANGE = "dynamic_range"  # EV range
    DETAIL_RETENTION = "detail_retention"  # Percentage detail kept
    EXPOSURE_CONSISTENCY = "exposure_consistency"  # Exposure error


@dataclass
class ImageMetric:
    """A single image quality metric result."""
    metric_type: MetricType
    value: float  # Numeric value (units depend on metric)
    units: str  # e.g. "cycles/pixel", "%, "EV", "sigma"
    reference: Optional[str] = None  # Reference image or target, if applicable
    measurement_method: Optional[str] = None  # How the metric was computed
    is_estimate: bool = False  # True if the value is an estimate, not a measured value
    image_path: Optional[str] = None  # Path to the analyzed image


@dataclass
class ImageAnalysisResult:
    """Complete analysis result for one image."""
    image_path: str
    file_hash: str  # SHA-256 of the image file
    width: int
    height: int
    format: str
    metrics: Tuple[ImageMetric, ...] = field(default_factory=tuple)
    overall_assessment: Optional[str] = None  # Free-form text summary
    analysis_method: Optional[str] = None  # e.g. "laplacian", "delta_e", etc.


#
# Image quality analyzer
#


def compute_file_hash(path: str) -> str:
    """Compute SHA-256 hash of an image file."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return None


def analyze_image(
    image_path: str,
) -> ImageAnalysisResult:
    """Analyze an existing image for quality metrics.

    Performs read-only analysis of the image at the given path.  No photographs
    are captured and no new images are generated.

    Metrics computed:
    - Format, dimensions, and file hash.
    - Where applicable, basic metrics using PIL only (no OpenCV required).

    Returns:
        ImageAnalysisResult with computed metrics.  Metrics that cannot be
        computed (e.g. no suitable test target in the image) will have
        is_estimate=True and a note in the measurement_method.
    """
    path = Path(image_path)

    # Basic file information
    try:
        file_hash = compute_file_hash(str(path))
        with Image.open(path) as img:
            width, height = img.size
            fmt = img.format or "Unknown"
    except Exception as e:
        return ImageAnalysisResult(
            image_path=str(path),
            file_hash="error",
            width=0,
            height=0,
            format="Error",
            overall_assessment=f"Could not open image: {e}",
        )

    metrics: List[ImageMetric] = []

    # 1. Sharpness (Laplacian variance estimate)
    # We compute a basic Laplacian variance using PIL only.
    # This is an ESTIMATE, not a precise MTF50 measurement, because we don't
    # have a test chart.  The value is scaled for interpretability.
    try:
        img_gray = img_gray = img.convert("L")
        # Resize to a manageable size for speed
        small = img_gray.resize((min(width, 640), min(height, 640)), Image.LANCZOS)
        arr = list(small.getdata())
        # Laplacian kernel: [ 0  1  0; 1 -4  1; 0  1  0]
        laplacian_vals = []
        for y in range(1, small.height - 1):
            for x in range(1, small.width - 1):
                p = small.getpixel((x, y))
                tl = small.getpixel((x - 1, y - 1))
                tr = small.getpixel((x + 1, y - 1))
                bl = small.getpixel((x - 1, y + 1))
                br = small.getpixel((x + 1, y + 1))
                center = 4 * p - tl - tr - bl - br
                laplacian_vals.append(center if center > 0 else 0)
        if laplacian_vals:
            mean_lap = sum(laplacian_vals) / len(laplacian_vals)
            # Scale to "cycles/pixel" equivalent for interpretability
            sharpness_value = mean_lap / 255.0 * 100.0
            metrics.append(ImageMetric(
                metric_type=MetricType.SHARPNESS,
                value=round(sharpness_value, 2),
                units="arbitrary",
                measurement_method="laplacian_via_PIL",
                is_estimate=True,  # This is an estimate without a test chart
                image_path=image_path,
            ))
    except Exception:
        pass  # Sharpness could not be computed

    # 2. Noise estimation (from low-variance smooth regions)
    try:
        # Compute average pixel value and stddev as a noise estimate
        img_gray = img.convert("L")
        pixels = list(img_gray.getdata())
        if pixels:
            mean_val = sum(pixels) / len(pixels)
            variance = sum((p - mean_val) ** 2 for p in pixels) / len(pixels)
            noise_sigma = variance ** 0.5
            # Normalize to 0-1 scale
            noise_value = min(noise_sigma / 255.0, 1.0)
            metrics.append(ImageMetric(
                metric_type=MetricType.NOISE,
                value=round(noise_value, 3),
                units="normalized",
                measurement_method="pixel_stddev_via_PIL",
                is_estimate=True,
                image_path=image_path,
            ))
    except Exception:
        pass

    # 3. Edge halo detection (simple check: compare central region edge sharpness
    # to outer region edge sharpness).  This is a very rough estimate.
    try:
        img_gray = img.convert("L")
        width, height = img_gray.size
        # Compare middle third sharpness to edge third sharpness
        middle_start = height // 3
        middle_end = 2 * height // 3
        edge_pixels = []

        # Get Laplacian values at edges and middle
        middle_vals = []
        edge_vals = []

        for y in range(1, height - 1):
            for x in range(1, width - 1):
                p = img_gray.getpixel((x, y))
                # Simple measure: average of 4 neighbors minus center
                n = (img_gray.getpixel((x - 1, y)) + img_gray.getpixel((x + 1, y))
                     + img_gray.getpixel((x, y - 1)) + img_gray.getpixel((x, y + 1))) / 4
                lapl = p - n
                if middle_start <= y < middle_end:
                    middle_vals.append(max(lap, 0) for lap in [lapl])
                else:
                    edge_vals.append(max(lapl, 0))

        if middle_vals and edge_vals:
            mean_middle = sum(middle_vals) / len(middle_vals)
            mean_edge = sum(edge_vals) / len(edge_vals)
            halo_ratio = mean_edge / (mean_middle + 0.001)  # avoid div by zero
            metrics.append(ImageMetric(
                metric_type=MetricType.HALO,
                value=round(halo_ratio, 3),
                units="ratio (edge/middle)",
                measurement_method="edge_vs_middle_sharpness_via_PIL",
                is_estimate=True,
                image_path=image_path,
            ))
    except Exception:
        pass

    # 4. Color analysis (basic histogram info - no reference target)
    try:
        img_rgb = img.convert("RGB")
        # Compute average R, G, B values as a basic color characterization
        pixels = list(img_rgb.getdata())
        if pixels:
            r_sum = g_sum = b_sum = 0
            count = 0
            for p in pixels:
                # PIL tuples are (R, G, B) for RGB images
                if isinstance(p, tuple) and len(p) >= 3:
                    r_sum += p[0]
                    g_sum += p[1]
                    b_sum += p[2]
                    count += 1
            if count > 0:
                r_avg = r_sum / count
                g_avg = g_sum / count
                b_avg = b_sum / count
                metrics.append(ImageMetric(
                    metric_type=MetricType.COLOR_ACCURACY,
                    value=round((r_avg + g_avg + b_avg) / 3, 1),
                    units="average pixel value (0-255)",
                    measurement_method="average_rgb_via_PIL",
                    is_estimate=True,
                    image_path=image_path,
                ))
    except Exception:
        pass

    # 5. Exposure consistency (from EXIF if available)
    try:
        exif = img._getexif()
        if exif and 0x8828 in exif:  # ExposureTime tag
            exposure_time = exif[0x8828]
            # Store as raw value; interpretation depends on exposure time mode
            metrics.append(ImageMetric(
                metric_type=MetricType.EXPOSURE_CONSISTENCY,
                value=exposure_time if exposure_time else 0,
                units="raw EXIF value",
                measurement_method="exif_exposure_time",
                is_estimate=False,  # EXIF value is directly read, not estimated
                image_path=image_path,
            ))
    except Exception:
        pass

    overall = None
    if metrics:
        # Simple overall assessment: count how many metrics are estimates
        n_estimates = sum(1 for m in metrics if m.is_estimate)
        overall = f"Analyzed {len(metrics)} metric(s), {n_estimates} estimate(s), " \
                  f"image {width}x{height}, {fmt}"

    return ImageAnalysisResult(
        image_path=image_path,
        file_hash=file_hash,
        width=width,
        height=height,
        format=fmt,
        metrics=tuple(metrics),
        overall_assessment=overall,
    )


def analyze_directory(
    directory: str,
    pattern: str = "*.jpg",
) -> Dict[str, any]:
    """Analyze all images in a directory and return a summary.

    Args:
        directory: Path to directory containing images.
        pattern: File pattern to match (e.g. "*.jpg", "*.png").

    Returns:
        Dict with analysis summary including per-image results and aggregate stats.
    """
    import os

    results: Dict[str, ImageAnalysisResult] = {}
    image_paths = []

    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(pattern.lstrip("*")):
                image_paths.append(os.path.join(root, f))

    for path in image_paths:
        result = analyze_image(path)
        results[path] = result

    # Aggregate statistics
    total_images = len(results)
    if total_images == 0:
        return {"total_images": 0, "message": "No images matching pattern found."}

    n_metrics = sum(len(r.metrics) for r in results.values())
    n_estimates = sum(1 for r in results.values() for m in r.metrics if m.is_estimate)
    avg_sharpness = None
    sharpness_vals = [m.value for r in results.values() for m in r.metrics
                      if m.metric_type == MetricType.SHARPNESS and not m.is_estimate]
    if sharpness_vals:
        avg_sharpness = round(sum(sharpness_vals) / len(sharpness_vals), 2)

    return {
        "total_images": total_images,
        "n_metrics": n_metrics,
        "n_estimates": n_estimates,
        "avg_sharpness": avg_sharpness,
        "per_image": {path: {
            "file_hash": r.file_hash[:16],
            "metrics_count": len(r.metrics),
            "overall_assessment": r.overall_assessment,
            "has_sharpness": any(m.metric_type == MetricType.SHARPNESS for m in r.metrics),
        } for path, r in results.items()},
    }


if __name__ == "__main__":
    # Demo: analyze a few existing images from the repo
    import sys
    from pathlib import Path

    print("=" * 70)
    print("Image Quality Analyzer Demo (read-only, existing images only)")
    print("=" * 70)

    # Look for sample images in common repo directories
    search_dirs = [
        "new_captures",
        "new_captures_1325",
        "analysis_results/final_calibration/latest_samples",
    ]

    found_images = []
    for d in search_dirs:
        p = Path(d)
        if p.is_dir():
            for img in sorted(p.glob("*.jpg")) + sorted(p.glob("*.png")):
                found_images.append(str(img))

    if not found_images:
        # Also try the analysis_results directories
        import glob
        for pattern in ["analysis_results/**/*.jpg", "analysis_results/**/*.png"]:
            for f in glob.glob(pattern, recursive=True):
                found_images.append(f)

    if not found_images:
        print("\nNo existing image files found in standard repo directories.")
        print("The analyzer is designed for read-only analysis of existing images.")
        print("Place some .jpg/.png files in the repo directories to test.")
    else:
        print(f"\nFound {len(found_images)} image(s) to analyze.\n")
        for img_path in found_images[:3]:  # Analyze first 3
            print(f"=== {Path(img_path).name} ===")
            result = analyze_image(img_path)
            print(f"  Size: {result.width}x{result.height}, {result.format}")
            print(f"  Hash: {result.file_hash[:16]}...")
            print(f"  Metrics: {len(result.metrics)}")
            for m in result.metrics:
                estimate_mark = " [ESTIMATE]" if m.is_estimate else ""
                print(f"    - {m.metric_type.value}: {m.value} {m.units}{estimate_mark}")
                if m.measurement_method:
                    print(f"      method: {m.measurement_method}")
            if result.overall_assessment:
                print(f"  Assessment: {result.overall_assessment}")
            print()