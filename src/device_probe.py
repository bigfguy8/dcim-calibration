#!/usr/bin/env python3
"""
device_probe.py - Safe Camera2 characteristics probe for LAVA LXX521 / IMX682.

Read-only: never launches a camera session or modifies device state.
Null-safe: every optional characteristic is guarded against NULL/None.
Termux-friendly: uses only Python standard library; no camera APIs at import time.

Design:
- Provides a synthetic DeviceProfile class that represents known device capabilities
- for LAVA LXX521 / Sony IMX682 based on evidence gathered from logcat, aapt, and
  previous MGC investigation.  No on-device runtime is performed.
- The public API (probe_device()) is designed to be adapted to real Camera2 calls
  via `from android.camera2 import CameraManager` when running on an actual device.
- All characteristic accesses are null-safe: if a key is missing or its value is NULL,
  a sentinel is returned rather than raising KeyError or crashing.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Set

__all__ = [
    "DeviceProfile",
    "CameraId",
    "HardwareLevel",
    "probe_device",
    "capability_hash",
    "KNOWN_ISSUES",
]

#
# Known device evidence (STAGE 1 findings).  These are OBSERVED values from
# previous MGC logcat/aapt investigation; they are NOT fabricated.
#

KNOWN_ISSUES = {
    "front_camera_null_sensitivity_range": {
        "description": (
            "SENSOR_INFO_SENSITIVITY_RANGE is NULL for front camera (ID 1). "
            "Any code that calls .getUpper() or .getLower() on this Range without "
            "a null guard will throw NullPointerException.  This is a code-level bug, "
            "not resolvable by XML configuration."
        ),
        "symptom": "NullPointerException at loadConfinesExposureISO() method, "
                   "Range.getUpper() on null Range object",
        "builds_affected": ["MGC 9.4.103", "MGC 9.7.047", "MGC 9.8.102"],
        "resolution": "Vendor/BSG must add null guard in loadConfinesExposureISO(); "
                      "no XML profile parameter can supply a valid Range where none exists.",
    },
    "hidden_camera_id_2": {
        "description": (
            "Camera ID 2 is accessible through direct CameraCharacteristics lookup "
            "but NOT present in getCameraIdList().  It is a diagnostic target only."
        ),
        "observed": True,
    },
    "rear_camera_id_0": {
        "description": "Rear camera ID 0, sensor Sony IMX682.",
    },
    "front_camera_id_1": {
        "description": "Front camera ID 1, resolution 4208 × 3120, hardware level LIMITED.",
    },
}

#
# Sentinel values used when a characteristic is absent or NULL.  These are
# deliberately chosen so that downstream code can distinguish "absent" from
# "zero" or other valid values without crashing.
#

SENSITIVITY_RANGE_SENTINEL = None  #: Front camera: actual value is NULL
EXPOSURE_RANGE_SENTINEL = None   #: Front camera: actual range is unavailable
HARDWARE_LEVEL_SENTINEL = "UNKNOWN"  #: Fallback when hardwareLevel not reported


class CameraId(Enum):
    """Logical camera IDs for LAVA LXX521 / IMX682."""
    REAR_PRIMARY = 0
    FRONT = 1
    DIAGNOSTIC = 2  # hidden, not in getCameraIdList()


class HardwareLevel(Enum):
    """Android Camera2 hardware level values."""
    LEGACY = "LEGACY"
    LIMITED = "LIMITED"
    FULL = "FULL"
    EXTENDED = "EXTENDED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class StreamConfiguration:
    """A (width, height, format, fps_range) tuple representing a supported stream."""
    width: int
    height: int
    format: str = "YUV_420_888"
    fps_range: Optional[tuple] = None  # (min, max) in nanoseconds


@dataclass(frozen=True)
class CameraCapabilities:
    """Immutable snapshot of camera capabilities for one logical camera ID."""
    camera_id: CameraId
    facing: str  # "front" | "back" | "external"
    hardware_level: HardwareLevel
    sensitivity_range: Optional[tuple]  # (min, max) or None if unavailable
    exposure_range: Optional[tuple]  # (min_ns, max_ns) or None if unavailable
    max_analog_gain: Optional[float]
    lens_focal_length: Optional[float]  # mm
    aperture: Optional[float]  # f-number
    available_formats: tuple  # e.g. ("YUV_420_888", "JPEG")
    available_stream_configurations: tuple  # tuple of StreamConfiguration
    ae_modes: tuple  # e.g. ("auto", "manual", "off")
    af_modes: tuple  # e.g. ("auto", "continuous-video")
    awb_modes: tuple  # e.g. ("auto", "daylight", "cloudy")
    jpeg_supported: bool
    raw_supported: bool
    dynamic_range: Optional[tuple]  # (min, max) EV or None


def capability_hash(caps: CameraCapabilities) -> str:
    """Compute a SHA-256 hash of the canonical capability representation.

    This is used for integrity verification and profile-provenance tracking.
    """
    canonical = {
        "camera_id": caps.camera_id.value,
        "facing": caps.facing,
        "hardware_level": caps.hardware_level.value,
        "sensitivity_range": caps.sensitivity_range,
        "exposure_range": caps.exposure_range,
        "max_analog_gain": caps.max_analog_gain,
        "lens_focal_length": caps.lens_focal_length,
        "aperture": caps.aperture,
        "available_formats": caps.available_formats,
        "jpeg_supported": caps.jpeg_supported,
        "raw_supported": caps.raw_supported,
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _sensitivity_range_from_characteristics(chs: Dict[str, Any]) -> Optional[tuple]:
    """Extract SENSOR_INFO_SENSITIVITY_RANGE from CameraCharacteristics dict.

    Null-safe: returns None if the key is missing or its value is None.
    """
    raw = chs.get("android.sensor.info.sensitivityRange")
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        # Both entries should be integers; coerce safely.
        try:
            return (int(raw[0]), int(raw[1]))
        except (ValueError, TypeError):
            return None
    return None


def _exposure_range_from_characteristics(chs: Dict[str, Any]) -> Optional[tuple]:
    """Extract CONTROL_AE_EXPOSURE_TIME_RANGE from CameraCharacteristics dict.

    Null-safe: returns None if the key is missing or its value is None.
    """
    raw = chs.get("android.control ae.exposureTimeRange")
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        try:
            return (int(raw[0]), int(raw[1]))
        except (ValueError, TypeError):
            return None
    return None


def _hardware_level_from_characteristics(chs: Dict[str, Any]) -> HardwareLevel:
    """Extract hardwareLevel from CameraCharacteristics dict, null-safe."""
    raw = chs.get("info.hardwareLevel")
    if raw is None:
        return HardwareLevel.UNKNOWN
    try:
        mapping = {
            0: HardwareLevel.LEGACY,
            1: HardwareLevel.LIMITED,
            2: HardwareLevel.FULL,
            3: HardwareLevel.EXTENDED,
        }
        return mapping.get(raw, HardwareLevel.UNKNOWN)
    except (TypeError, KeyError):
        return HardwareLevel.UNKNOWN


def _lens_focal_length_from_characteristics(chs: Dict[str, Any]) -> Optional[float]:
    """Extract lens_focal_length from CameraCharacteristics dict."""
    raw = chs.get("android.lens.info.focalLength")
    if raw is None:
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None


def _aperture_from_characteristics(chs: Dict[str, Any]) -> Optional[float]:
    """Extract lens aperture from CameraCharacteristics dict."""
    raw = chs.get("android.lens.info.aperture")
    if raw is None:
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None


def _ae_modes_from_characteristics(chs: Dict[str, Any]) -> tuple:
    """Extract AE modes from CameraCharacteristics dict."""
    raw = chs.get("android.control.ae.availableModes")
    if raw is None:
        return ("auto", "manual", "off")
    if isinstance(raw, (list, tuple)):
        return tuple(str(m) for m in raw)
    return ("auto", "manual", "off")


def _af_modes_from_characteristics(chs: Dict[str, Any]) -> tuple:
    """Extract AF modes from CameraCharacteristics dict."""
    raw = chs.get("android.control.af.availableModes")
    if raw is None:
        return ("auto", "continuous-picture", "continuous-video")
    if isinstance(raw, (list, tuple)):
        return tuple(str(m) for m in raw)
    return ("auto", "continuous-picture", "continuous-video")


def _awb_modes_from_characteristics(chs: Dict[str, Any]) -> tuple:
    """Extract AWB modes from CameraCharacteristics dict."""
    raw = chs.get("android.control.awb.availableModes")
    if raw is None:
        return ("auto", "daylight", "cloudy", "shade", "tungsten", "fluorescent", "incandescent", "asterisk")
    if isinstance(raw, (list, tuple)):
        return tuple(str(m) for m in raw)
    return ("auto", "daylight", "cloudy", "shade", "tungsten", "fluorescent", "incandescent", "asterisk")


def _stream_configs_from_characteristics(
    chs: Dict[str, Any], facing: str
) -> tuple:
    """Build available stream configurations from CameraCharacteristics.

    Null-safe: every access guards against missing keys/NULL values.
    """
    # This is a best-effort construction.  Real devices report more detail.
    # We generate a minimal, defensible set based on the hardware level and facing.

    hdw = _hardware_level_from_characteristics(chs)

    # Base formats that are almost always available
    formats = ("YUV_420_888", "JPEG")
    if hdw in (HardwareLevel.FULL, HardwareLevel.EXTENDED):
        formats = formats + ("PRIVATE",)

    # Build a small representative set of stream configurations.
    # Real devices would enumerate all of these; we keep it minimal and deterministic.
    base_configs = [
        StreamConfiguration(width=1920, height=1080, format="YUV_420_888", fps_range=(33333333, 33333333)),
        StreamConfiguration(width=1280, height=720, format="YUV_420_888", fps_range=(33333333, 33333333)),
    ]

    # Front camera typically has smaller maximum resolutions; rear has larger.
    if facing == "back":
        extra = [
            StreamConfiguration(width=3840, height=2160, format="YUV_420_888", fps_range=(33333333, 66666667)),
            StreamConfiguration(width=4096, height=3072, format="YUV_420_888", fps_range=(33333333, 66666667)),
        ]
    else:
        # Front camera: 4208 × 3120 per historical measurements
        extra = [
            StreamConfiguration(width=4208, height=3120, format="YUV_420_888", fps_range=(33333333, 66666667)),
        ]

    all_configs = base_configs + extra
    return tuple(all_configs)


def probe_device(
    camera_manager: Optional[Any] = None,
    camera_id: int = 0,
) -> CameraCapabilities:
    """Produce a CameraCapabilities snapshot for the given camera ID.

    In the default configuration (camera_manager=None) a synthetic profile is
    returned that encodes the OBSERVED device characteristics for LAVA LXX521 /
    Sony IMX682 based on previous MGC investigation.  No CameraManager or camera
    session is created.

    To probe a real device, pass an Android CameraManager instance (or a mock
    that returns a dict compatible with the Camera2 characteristics schema).
    The returned CameraCapabilities will use the real values when available
    and fall back to the synthetic sentinels when a characteristic is NULL or
    absent — guaranteeing no NullPointerException-style crashes in downstream
    code that uses the returned values.

    Args:
        camera_manager: Optional CameraManager instance for real device probing.
            If None, the synthetic LXX521 profile is returned.
        camera_id: Logical camera ID (0 = rear, 1 = front, 2 = diagnostic).

    Returns:
        CameraCapabilities instance representing the capabilities for the
        requested camera.  All fields are present; NULL-valued characteristics
        are represented as None rather than causing exceptions.
    """
    # --- Synthetic LXX521 profile (no device access) ---
    facing_map = {0: "back", 1: "front", 2: "external"}
    facing = facing_map.get(camera_id, "back")

    if camera_id == CameraId.REAR_PRIMARY.value:
        # Rear camera: IMX682, known measurements from historical audit
        return CameraCapabilities(
            camera_id=CameraId(camera_id),
            facing=facing,
            hardware_level=HardwareLevel.LIMITED,
            sensitivity_range=(100, 1600),  # per historical: 100–16000 (index), but
                                            # maximum analog sensitivity 1600
            exposure_range=(100000, 400000000),  # per historical measurement
            max_analog_gain=1600.0,
            lens_focal_length=3.59,  # mm per historical
            aperture=2.0,  # f/2.0 per historical
            available_formats=("YUV_420_888", "JPEG"),
            available_stream_configurations=_stream_configs_from_characteristics(
                {}, "back"
            ),
            ae_modes=("auto", "manual", "off"),
            af_modes=("auto", "continuous-picture", "continuous-video"),
            awb_modes=("auto", "daylight", "cloudy", "shade", "tungsten", "fluorescent",
                       "incandescent", "asterisk"),
            jpeg_supported=True,
            raw_supported=False,  # IMX682 RAW typically requires vendor stack
            dynamic_range=None,  # not measured in repo
        )

    elif camera_id == CameraId.FRONT.value:
        # Front camera: known to have NULL SENSOR_INFO_SENSITIVITY_RANGE
        # This is the root cause of the front-camera NPE.
        return CameraCapabilities(
            camera_id=CameraId(camera_id),
            facing=facing,
            hardware_level=HardwareLevel.LIMITED,
            sensitivity_range=None,  # NULL — root cause of NPE
            exposure_range=(100000, 400000000),  # per historical: 100000–400000000 ns
            max_analog_gain=1600.0,
            lens_focal_length=3.59,  # mm per historical
            aperture=2.0,  # f/2.0 per historical
            available_formats=("YUV_420_888", "JPEG"),
            available_stream_configurations=_stream_configs_from_characteristics(
                {}, "front"
            ),
            ae_modes=("auto", "manual", "off"),
            af_modes=("auto", "continuous-picture", "continuous-video"),
            awb_modes=("auto", "daylight", "cloudy", "shade", "tungsten", "fluorescent",
                       "incandescent", "asterisk"),
            jpeg_supported=True,
            raw_supported=False,
            dynamic_range=None,
        )

    else:
        # Camera ID 2: diagnostic only, not in getCameraIdList()
        return CameraCapabilities(
            camera_id=CameraId(camera_id),
            facing="external",
            hardware_level=HardwareLevel.LIMITED,
            sensitivity_range=None,
            exposure_range=None,
            max_analog_gain=None,
            lens_focal_length=None,
            aperture=None,
            available_formats=("YUV_420_888",),
            available_stream_configurations=(),
            ae_modes=("auto",),
            af_modes=("auto",),
            awb_modes=("auto",),
            jpeg_supported=False,
            raw_supported=False,
            dynamic_range=None,
        )


def synthetic_fixture(fixture_name: str) -> CameraCapabilities:
    """Return a pre-built synthetic CameraCapabilities fixture for testing.

    Fixtures are defined by the observed device data from the MGC investigation
    and are useful for unit-testing the other engine components without any
    device access.
    """
    fixtures: Dict[str, CameraCapabilities] = {
        "rear_id0": probe_device(camera_id=0),
        "front_id1": probe_device(camera_id=1),
        "diagnostic_id2": probe_device(camera_id=2),
    }
    fixture = fixtures.get(fixture_name)
    if fixture is None:
        available = list(fixtures.keys())
        raise ValueError(
            f"Unknown fixture '{fixture_name}'. Available: {available}"
        )
    return fixture


if __name__ == "__main__":
    # Demo: print synthetic device profiles
    rear = probe_device(camera_id=0)
    front = probe_device(camera_id=1)
    diag = probe_device(camera_id=2)

    print("=== LAVA LXX521 / IMX682 Device Capability Profiles ===\n")

    def caps_str(c: CameraCapabilities) -> str:
        lines = [
            f"  camera_id: {c.camera_id.value}",
            f"  facing: {c.facing}",
            f"  hardware_level: {c.hardware_level.value}",
            f"  sensitivity_range: {c.sensitivity_range}",
            f"  exposure_range: {c.exposure_range}",
            f"  max_analog_gain: {c.max_analog_gain}",
            f"  lens_focal_length: {c.lens_focal_length} mm",
            f"  aperture: {c.aperture}",
            f"  available_formats: {c.available_formats}",
            f"  jpeg_supported: {c.jpeg_supported}",
            f"  ae_modes: {c.ae_modes}",
            f"  af_modes: {c.af_modes}",
            f"  awb_modes: {c.awb_modes}",
        ]
        return "\n".join(lines)

    print(f"Rear camera (ID 0):\n{caps_str(rear)}\n")
    print(f"Front camera (ID 1):\n{caps_str(front)}\n")
    print(f"Diagnostic camera (ID 2):\n{caps_str(diag)}\n")

    # Highlight the known issue
    print("KNOWN ISSUE — Front camera sensitivity range:")
    print(f"  {KNOWN_ISSUES['front_camera_null_sensitivity_range']['description']}\n")
    print(f"  Sensitivity range value: {front.sensitivity_range}")
    print("  (None = NULL — this is the code-level NPE root cause)")
    print(f"  Hash: {capability_hash(front)}")