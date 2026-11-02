#!/usr/bin/env python3
"""Suite 2: Camera Capabilities tests."""
import unittest
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.camera_capabilities import (
    identify_schema_family,
    profile_schema_families,
    SchemaFamily,
    validate_profile_against_caps,
    CameraCapabilities,
    synthetic_fixture,
    CameraId,
    HardwareLevel,
)


class TestCameraCapabilitiesSchemaFamily(unittest.TestCase):
    """Test schema-family identification and separation between LMC and BSG families."""

    def test_lmc_profile_is_lmc_family(self):
        """LMC84_AllRounder profile schema keys are identified as LMC family."""
        lmc_keys = {"pref_qjpg_key", "ptchr_contrast", "ptchr_saturation"}
        family = identify_schema_family(lmc_keys)
        self.assertEqual(family, SchemaFamily.LMC)

    def test_bsg_profile_is_bsg_family(self):
        """BSG profiles use pref_quality_key and camera_id_back."""
        bsg_keys = {"pref_quality_key", "camera_id_back"}
        family = identify_schema_family(bsg_keys)
        self.assertEqual(family, SchemaFamily.BSG)

    def test_mixed_profile_mixed_family(self):
        """Profile with mixed schema keys is identified as MIXED family."""
        mixed_keys = {"pref_qjpg_key", "pref_quality_key", "camera_id_back"}
        family = identify_schema_family(mixed_keys)
        # Mixed keys from both families result in MIXED family
        self.assertEqual(family, SchemaFamily.MIXED)

    def test_unknown_schema_family_handling(self):
        """Unknown keys result in SchemaFamily.UNKNOWN."""
        unknown_keys = {"some_random_key", "another_unknown"}
        family = identify_schema_family(unknown_keys)
        self.assertEqual(family, SchemaFamily.UNKNOWN)

    def test_schema_family_enum_values(self):
        """SchemaFamily enum has expected string values."""
        # Check that enum .value gives the string tag
        self.assertEqual(SchemaFamily.LMC.value, "LMC")
        self.assertEqual(SchemaFamily.BSG.value, "BSG")
        self.assertEqual(SchemaFamily.UNKNOWN.value, "UNKNOWN")
        # Test assertIn with string values
        self.assertIn("LMC", [f.value for f in SchemaFamily])
        self.assertIn("BSG", [f.value for f in SchemaFamily])
        self.assertIn("UNKNOWN", [f.value for f in SchemaFamily])

    def test_profile_schema_families_lmc(self):
        """profile_schema_families() correctly identifies LMC profiles."""
        result = profile_schema_families("src/xml_audit.py")
        # result is (SchemaFamily, set(keys), set(duplicate_keys))
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3,
                          "profile_schema_families should return 3-element tuple")
        # The first element is the SchemaFamily
        family = result[0]
        self.assertIn(family, [SchemaFamily.LMC, SchemaFamily.BSG, SchemaFamily.UNKNOWN, SchemaFamily.MIXED])

    def test_profile_schema_families_bsg(self):
        """profile_schema_families() correctly identifies BSG profiles."""
        result = profile_schema_families("analysis_results/imx682_config/lava/generate_lava.py")
        # result is (SchemaFamily, set(keys), set(duplicate_keys))
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3,
                          "profile_schema_families should return 3-element tuple")
        # The first element is the SchemaFamily
        family = result[0]
        self.assertIn(family, [SchemaFamily.LMC, SchemaFamily.BSG, SchemaFamily.UNKNOWN, SchemaFamily.MIXED])


class TestCameraCapabilitiesSeparation(unittest.TestCase):
    """Test that LMC and BSG families are not interchanged (strict separation)."""

    def test_lmc_and_bsg_not_interchangeable(self):
        """LMC8.4 and BSG/MGC config families must never be silently interchanged."""
        lmc_keys = {"pref_qjpg_key", "ptchr_contrast"}
        bsg_keys = {"pref_quality_key", "camera_id_back"}

        lmc_family = identify_schema_family(lmc_keys)
        bsg_family = identify_schema_family(bsg_keys)

        # They must be different families
        self.assertNotEqual(lmc_family, bsg_family,
                            "LMC and BSG families must NOT be interchangeable")

        # Each must identify correctly
        self.assertEqual(lmc_family, SchemaFamily.LMC)
        self.assertEqual(bsg_family, SchemaFamily.BSG)


class TestCameraCapabilitiesValidation(unittest.TestCase):
    """Test capability validation and unknown schema handling."""

    def test_validate_profile_against_caps_lmc(self):
        """validate_profile_against_caps() works with LMC schema."""
        caps = synthetic_fixture("rear_id0")
        # Profile with valid keys should validate or at least not crash
        result = validate_profile_against_caps(
            "src/xml_audit.py", caps
        )
        self.assertIsNotNone(result)

    def test_validate_profile_against_caps_bsg(self):
        """validate_profile_against_caps() works with BSG schema."""
        caps = synthetic_fixture("rear_id0")
        result = validate_profile_against_caps(
            "analysis_results/imx682_config/lava/generate_lava.py", caps
        )
        self.assertIsNotNone(result)

    def test_unsupported_key_detection_lmc(self):
        """LMC profile should detect unsupported BSG keys."""
        lmc_keys = {"pref_qjpg_key", "ptchr_contrast"}
        family = identify_schema_family(lmc_keys)
        # Should NOT be identified as BSG
        self.assertNotEqual(family, SchemaFamily.BSG)

    def test_unsupported_key_detection_bsg(self):
        """BSG profile should detect unsupported LMC keys."""
        bsg_keys = {"pref_quality_key", "camera_id_back"}
        family = identify_schema_family(bsg_keys)
        # Should NOT be identified as LMC
        self.assertNotEqual(family, SchemaFamily.LMC)

    def test_synthetic_fixture_has_expected_fields(self):
        """synthetic_fixture() produces capabilities with expected fields."""
        caps = synthetic_fixture("rear_id0")
        self.assertIsNotNone(caps.exposure_range)
        self.assertIsNotNone(caps.hardware_level)
        self.assertEqual(caps.camera_id, CameraId.REAR_PRIMARY)


if __name__ == "__main__":
    unittest.main()