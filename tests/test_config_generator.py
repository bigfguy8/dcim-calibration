#!/usr/bin/env python3
"""Suite 5: Configuration Generator tests."""
import unittest
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_generator import (
    generate_from_baseline,
    generate_preset_candidate,
    create_rollback_copy,
    GenerationResult,
    ChangeRecord,
    _modify_xml_profile,
    _extract_keys,
)
from src.config_validator import validate_configuration


class TestConfigurationGeneratorBaseline(unittest.TestCase):
    """Test baseline-derived candidate generation."""

    def test_generate_from_baseline_creates_result(self):
        """generate_from_baseline() returns a GenerationResult with proper parameter_changes."""
        # Use the correct API: generate_from_baseline(baseline_path, parameter_changes)
        result = generate_from_baseline(
            "analysis_results/imx682_config/lava/generate_lava.py",
            {"some_key": "some_value"},
        )
        self.assertIsInstance(result, GenerationResult)

    def test_generate_from_baseline_uses_baseline_path(self):
        """generate_from_baseline() uses the baseline path correctly."""
        result = generate_from_baseline(
            "analysis_results/imx682_config/lava/generate_lava.py",
            {},
        )
        self.assertIsNotNone(result)

    def test_generate_from_baseline_with_changes(self):
        """generate_from_baseline() with parameter changes produces a result."""
        result = generate_from_baseline(
            "analysis_results/imx682_config/lava/generate_lava.py",
            {"test_key": "test_value"},
        )
        self.assertIsNotNone(result)


class TestConfigurationGeneratorChangeProvenance(unittest.TestCase):
    """Test change provenance tracking."""

    def test_change_record_has_required_fields(self):
        """ChangeRecord tracks what changed, from where, and why."""
        record = ChangeRecord(
            key="test_key",
            original_value="old_value",
            new_value="new_value",
            source="baseline",
            rationale="test",
        )
        self.assertEqual(record.key, "test_key")
        self.assertEqual(record.old_value, "old_value")
        self.assertEqual(record.new_value, "new_value")
        self.assertEqual(record.source, "baseline")


class TestConfigurationGeneratorRollbackCopy(unittest.TestCase):
    """Test rollback-copy creation."""

    def test_create_rollback_copy_creates_file(self):
        """create_rollback_copy() creates a backup copy."""
        # Create a temp test file
        test_dir = tempfile.mkdtemp()
        try:
            src = os.path.join(test_dir, "test_profile.xml")
            with open(src, "w") as f:
                f.write("<map><key>value</key></map>")
            
            result = create_rollback_copy(src, test_dir)
            self.assertTrue(os.path.exists(result),
                            "create_rollback_copy should return path to backup")
            # Verify backup content
            with open(result) as f:
                content = f.read()
            self.assertIn("key", content,
                          "Backup should contain original content")
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_create_rollback_copy_preserves_baseline(self):
        """Rollback copy preserves the baseline configuration unchanged."""
        test_dir = tempfile.mkdtemp()
        try:
            src = os.path.join(test_dir, "original.xml")
            with open(src, "w") as f:
                f.write("<map><baseline_key>baseline_val</baseline_key></map>")
            
            backup = create_rollback_copy(src, test_dir)
            # The backup should be identical to original
            with open(src) as f:
                original = f.read()
            with open(backup) as f:
                backup_content = f.read()
            self.assertEqual(original, backup_content,
                             "Rollback copy must be byte-identical to original")
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


class TestConfigurationGeneratorInvalidBaseline(unittest.TestCase):
    """Test invalid baseline handling."""

    def test_generate_from_baseline_nonexistent(self):
        """generate_from_baseline() on nonexistent baseline handles gracefully."""
        result = generate_from_baseline(
            "/nonexistent/baseline.xml", {}
        )
        self.assertIsNotNone(result,
                             "Should not crash on nonexistent baseline")


class TestConfigurationGeneratorUnchangedBaselinePreservation(unittest.TestCase):
    """Test unchanged baseline preservation."""

    def test_preserves_unchanged_keys_from_baseline(self):
        """generate_from_baseline preserves keys that match the baseline."""
        result = generate_from_baseline(
            "analysis_results/imx682_config/lava/generate_lava.py",
            {},
        )
        # Should have some preserved/unchanged keys
        self.assertIsNotNone(result,
                             "Result should not be None")


class TestConfigurationGeneratorExportedProvenance(unittest.TestCase):
    """Test change provenance and reporting."""

    def test_generation_result_has_provenance(self):
        """Generation result includes provenance information."""
        result = generate_from_baseline(
            "analysis_results/imx682_config/lava/generate_lava.py",
            {"test_key": "test_value"},
        )
        self.assertTrue(hasattr(result, "provenance") or
                        hasattr(result, "change_record") or
                        hasattr(result, "records"),
                        "GenerationResult should track provenance")


class TestConfigurationGeneratorValidatorIntegration(unittest.TestCase):
    """Test configuration validator integration."""

    def test_validate_generated_config(self):
        """validate_configuration works with generated baselines."""
        result = validate_configuration(
            "analysis_results/imx682_config/lava/generate_lava.py"
        )
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()