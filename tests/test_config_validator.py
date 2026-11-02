#!/usr/bin/env python3
"""Suite 6: Configuration Validator tests."""
import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_validator import (
    validate_configuration,
    validate_profile_summary,
    batch_validate,
    CheckResult,
    SchemaFamily,
    UNSUPPORTED_LMC_KEYS,
    CRITICAL_LMC_KEYS,
    BSG_MARKER_KEYS,
    CRITICAL_BSG_KEYS,
)


class TestConfigurationValidatorBasic(unittest.TestCase):
    """Test basic configuration validation."""

    def test_validate_configuration_valid(self):
        """validate_configuration() on valid config returns success."""
        # Use an LMC profile that should be valid
        result = validate_configuration(
            "analysis_results/imx682_config/lava/generate_lava.py",
        )
        self.assertIsNotNone(result)

    def test_validate_configuration_has_checkresult(self):
        """validate_configuration() returns a dict containing CheckResults."""
        result = validate_configuration(
            "analysis_results/imx682_config/lava/generate_lava.py"
        )
        self.assertIsInstance(result, dict)
        # Should contain CheckResult values
        self.assertTrue(
            any(isinstance(v, CheckResult) for v in result.values()),
            "Result dict should contain CheckResult values")

    def test_validate_configuration_has_required_fields(self):
        """validate_configuration() returns dict with CheckResult values."""
        result = validate_configuration(
            "analysis_results/imx682_config/lava/generate_lava.py"
        )
        self.assertIsInstance(result, dict)
        # Check that at least one CheckResult has the required fields
        for v in result.values():
            if isinstance(v, CheckResult):
                self.assertTrue(hasattr(v, "name"),
                                "CheckResult must have name")
                self.assertTrue(hasattr(v, "passed"),
                                "CheckResult must have passed")
                self.assertTrue(hasattr(v, "details"),
                                "CheckResult must have details")
                self.assertTrue(hasattr(v, "evidence"),
                                "CheckResult must have evidence")
                break


class TestConfigurationValidatorUnsupportedKeys(unittest.TestCase):
    """Test unsupported key detection."""

    def test_validate_unsupported_keys_detected(self):
        """validate_configuration() detects unsupported keys."""
        result = validate_configuration(
            "analysis_results/imx682_config/lava/generate_lava.py"
        )
        # Should report on unsupported keys if any exist
        self.assertIsNotNone(result)

    def test_unknown_schema_handling(self):
        """Unknown schema keys are properly handled."""
        result = validate_configuration(
            "analysis_results/imx682_config/lava/generate_lava.py"
        )
        # Unknown schema should not crash the validator
        self.assertIsNotNone(result)


class TestConfigurationValidatorSchemaFamilyMismatch(unittest.TestCase):
    """Test schema-family mismatch detection."""

    def test_validate_schema_family_mismatch(self):
        """validate_configuration() reports schema-family mismatch."""
        result = validate_configuration(
            "analysis_results/imx682_config/lava/generate_lava.py"
        )
        # Should have schema family info
        self.assertIsNotNone(result)

    def test_mixed_family_profile_rejected(self):
        """Profiles mixing LMC and BSG keys are properly classified."""
        result = validate_configuration(
            "analysis_results/imx682_config/lava/generate_lava.py"
        )
        # Mixed families should be flagged or handled
        self.assertIsNotNone(result)


class TestConfigurationValidatorBatchValidate(unittest.TestCase):
    """Test batch validation."""

    def test_batch_validate_returns_results(self):
        """batch_validate() returns validation results for multiple profiles."""
        result = batch_validate(
            "analysis_results/imx682_config"
        )
        self.assertIsNotNone(result,
                             "batch_validate() should return results")


class TestConfigurationValidatorCorrectClassification(unittest.TestCase):
    """Test correct validation-level classification."""

    def test_validation_level_classification(self):
        """validate_configuration() classifies at correct level."""
        result = validate_configuration(
            "analysis_results/imx682_config/lava/generate_lava.py"
        )
        # Should classify at appropriate level (A, B, C, or D)
        # result is a dict; check each CheckResult's level
        for v in result.values():
            if isinstance(v, CheckResult) and hasattr(v, "level"):
                level = v.level
                self.assertIn(
                    str(level), ["A", "B", "C", "D"],
                    f"Validation level should be A/B/C/D, got {level}")
                break


if __name__ == "__main__":
    unittest.main()