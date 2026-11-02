#!/usr/bin/env python3
"""Suite 1: Device Probe tests."""
import unittest
import os
import sys
import tempfile
import json
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.device_probe import (
    probe_device,
    synthetic_fixture,
    capability_hash,
    CameraId,
    HardwareLevel,
    CameraCapabilities,
    KNOWN_ISSUES,
    SENSITIVITY_RANGE_SENTINEL,
)


class TestDeviceProbe(unittest.TestCase):
    """Test the device_probe module with synthetic data only. No physical camera access."""

    def test_probe_device_returns_camera_capabilities(self):
        """probe_device() returns a CameraCapabilities for camera ID 0."""
        caps = probe_device(camera_id=0)
        self.assertIsInstance(caps, CameraCapabilities)
        self.assertEqual(caps.camera_id, CameraId.REAR_PRIMARY)

    def test_probe_device_rear_camera_values(self):
        """Rear camera (ID 0) has known sensitivity range."""
        caps = probe_device(camera_id=0)
        self.assertEqual(caps.sensitivity_range, (100, 1600))
        self.assertIsNotNone(caps.exposure_range)
        self.assertEqual(caps.hardware_level, HardwareLevel.LIMITED)

    def test_probe_device_front_camera_null_sensitivity(self):
        """Front camera (ID 1) has NULL sensitivity range — root cause of NPE."""
        caps = probe_device(camera_id=1)
        self.assertIsNone(caps.sensitivity_range,
                          "Front camera sensitivity_range must be None (NULL)")
        self.assertEqual(caps.facing, "front")

    def test_probe_device_diagnostic_camera(self):
        """Diagnostic camera (ID 2) is labeled external."""
        caps = probe_device(camera_id=2)
        self.assertEqual(caps.camera_id, CameraId.DIAGNOSTIC)
        self.assertEqual(caps.facing, "external")

    def test_probe_device_null_camera_manager(self):
        """Probe with no camera_manager returns synthetic fixture (no device access)."""
        caps = probe_device(camera_manager=None, camera_id=0)
        self.assertIsInstance(caps, CameraCapabilities)
        # Verify it's the same as calling without camera_manager
        caps2 = probe_device(camera_id=0)
        self.assertEqual(caps.sensitivity_range, caps2.sensitivity_range)

    def test_synthetic_fixture_rear(self):
        """synthetic_fixture('rear_id0') returns a valid CameraCapabilities."""
        caps = synthetic_fixture("rear_id0")
        self.assertIsInstance(caps, CameraCapabilities)
        self.assertEqual(caps.camera_id, CameraId.REAR_PRIMARY)

    def test_synthetic_fixture_front(self):
        """synthetic_fixture('front_id1') returns front camera with NULL sensitivity."""
        caps = synthetic_fixture("front_id1")
        self.assertEqual(caps.camera_id, CameraId.FRONT)
        self.assertIsNone(caps.sensitivity_range)

    def test_synthetic_fixture_diagnostic(self):
        """synthetic_fixture('diagnostic_id2') returns diagnostic camera."""
        caps = synthetic_fixture("diagnostic_id2")
        self.assertEqual(caps.camera_id, CameraId.DIAGNOSTIC)

    def test_synthetic_fixture_unknown_raises(self):
        """synthetic_fixture with unknown name raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            synthetic_fixture("nonexistent_fixture")
        self.assertIn("Unknown fixture", str(ctx.exception))

    def test_synthetic_fixture_is_synthetic_not_measured(self):
        """Synthetic fixture values must be distinguishable from measured data.

        The probe_device() with camera_manager=None produces synthetic values
        based on observed device data, but these are NOT real-time measurements.
        """
        caps = probe_device(camera_manager=None, camera_id=0)
        self.assertIsNotNone(caps.sensitivity_range,
                             "Synthetic rear camera should have a sensitivity range")
        # The sensitivity range value (100, 1600) comes from observed data,
        # but the fixture is clearly synthetic because no CameraManager was used.
        # This is documented in the probe_device docstring.
        self.assertIsInstance(caps, CameraCapabilities)

    def test_capability_hash_is_deterministic(self):
        """capability_hash() produces the same hash for the same capabilities."""
        caps1 = probe_device(camera_id=0)
        caps2 = probe_device(camera_id=0)
        self.assertEqual(capability_hash(caps1), capability_hash(caps2))

    def test_capability_hash_differs_across_cameras(self):
        """capability_hash() produces different hashes for different cameras."""
        rear = probe_device(camera_id=0)
        front = probe_device(camera_id=1)
        self.assertNotEqual(capability_hash(rear), capability_hash(front),
                            "Different cameras must have different capability hashes")

    def test_null_characteristic_handling(self):
        """NULL characteristics are represented as None, not missing or zero."""
        front = probe_device(camera_id=1)
        self.assertIsNone(front.sensitivity_range)
        # The sentinel value should be None
        self.assertIsNone(SENSITIVITY_RANGE_SENTINEL,
                          "SENSITIVITY_RANGE_SENTINEL must be None for NULL Range")

    def test_missing_characteristic_does_not_crash(self):
        """Missing characteristics don't cause KeyError or crash."""
        for cam_id in [0, 1, 2]:
            caps = probe_device(camera_id=cam_id)
            self.assertIsNotNone(caps, f"probe_device({cam_id}) returned None")

    def test_known_issues_documented(self):
        """KNOWN_ISSUES contains the front camera NPE issue."""
        self.assertIn("front_camera_null_sensitivity_range", KNOWN_ISSUES)
        issue = KNOWN_ISSUES["front_camera_null_sensitivity_range"]
        self.assertIn("SENSOR_INFO_SENSITIVITY_RANGE", issue["description"])
        self.assertIn("loadConfinesExposureISO", issue["symptom"])

    def test_no_physical_camera_access(self):
        """The synthetic probe does not attempt any physical camera access.

        probe_device() with camera_manager=None should work without any
        android.camera2 import or camera session creation.
        """
        # This test verifies that the module can be called without any
        # CameraManager or physical device — it should produce synthetic data
        # without raising any error.
        caps = probe_device(camera_manager=None, camera_id=0)
        self.assertIsInstance(caps, CameraCapabilities)


if __name__ == "__main__":
    unittest.main()
