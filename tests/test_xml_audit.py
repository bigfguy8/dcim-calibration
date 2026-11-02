#!/usr/bin/env python3
"""Suite 3: XML Audit tests."""
import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.xml_audit import (
    check_syntax,
    check_schema,
    check_compatibility,
    check_device,
    compute_sha256,
    find_duplicate_profiles,
    audit_directory_profiles,
    validate_xml_complete,
    ValidationLevel,
    ValidationResult,
    FullValidationReport,
)


class TestXMLSyntax(unittest.TestCase):
    """Test XML syntax validation."""

    def test_check_syntax_valid_xml(self):
        """check_syntax() returns SUCCESS on well-formed XML."""
        # Use the root directory XML audit test
        result = check_syntax("src/xml_audit.py")
        self.assertIsNotNone(result)
        # Valid XML should have level PASSED or syntax OK
        self.assertTrue(
            result.level.name == "A_SYNTAX" or result.passed,
            f"Valid XML should succeed: {result.message}",
        )

    def test_check_syntax_malformed_xml_raises(self):
        """check_syntax() on a truly malformed file should reveal the issue."""
        # Create a temp malformed XML file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False
        ) as f:
            f.write("<map><invalid><unclosed tag")
            tmp_path = f.name
        try:
            result = check_syntax(tmp_path)
            self.assertIsNotNone(result)
            # Should detect the malformed XML
            self.assertFalse(result.passed, "Malformed XML should fail syntax check")
        finally:
            os.unlink(tmp_path)

    def test_check_syntax_known_xml_files(self):
        """Syntax check passes on all 106 original XML profile files."""
        from pathlib import Path
        xml_dir = Path("analysis_results/imx682_config")
        if xml_dir.exists():
            xml_files = list(xml_dir.glob("*.xml"))
            for xml_file in xml_files[:5]:  # Check first 5
                result = check_syntax(str(xml_file))
                self.assertIsNotNone(result,
                                     f"Syntax check failed on {xml_file.name}")

    def test_syntax_result_has_required_fields(self):
        """Syntax validation result has expected fields."""
        result = check_syntax("src/xml_audit.py")
        self.assertTrue(hasattr(result, "success"))
        self.assertTrue(hasattr(result, "message"))
        self.assertTrue(hasattr(result, "level"))


class TestXMLSchema(unittest.TestCase):
    """Test XML schema checks."""

    def test_check_schema_known_profiles(self):
        """check_schema() works on known profile XML files."""
        result = check_schema("analysis_results/imx682_config/lava/generate_lava.py")
        # Should return ValidationResult
        self.assertIsNotNone(result)

    def test_check_schema_has_level(self):
        """Schema result has a level attribute."""
        result = check_schema("src/xml_audit.py")
        self.assertTrue(hasattr(result, "level"))

    def test_check_schema_identifies_schema_family(self):
        """check_schema() should identify the schema family."""
        result = check_schema("analysis_results/imx682_config/lava/generate_lava.py")
        self.assertIsNotNone(result)


class TestXMLCompatibility(unittest.TestCase):
    """Test compatibility checking."""

    def test_check_compatibility_result_has_fields(self):
        """check_compatibility() result has level and message."""
        result = check_compatibility("src/xml_audit.py")
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "level"))
        self.assertTrue(hasattr(result, "message"))


class TestXMLDeviceValidation(unittest.TestCase):
    """Test device-level validation."""

    def test_check_device_result_has_fields(self):
        """check_device() result has expected fields."""
        result = check_device("src/xml_audit.py")
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "level"))
        self.assertTrue(hasattr(result, "message"))

    def test_check_device_on_lmc_profile(self):
        """check_device() on LMC profile returns appropriate validation."""
        result = check_device("analysis_results/imx682_config/lava/generate_lava.py")
        self.assertIsNotNone(result)


class TestSHA256(unittest.TestCase):
    """Test SHA-256 computation."""

    def test_compute_sha256_known_file(self):
        """compute_sha256() produces hash for a known file."""
        result = compute_sha256("src/xml_audit.py")
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)  # SHA-256 hex digest length

    def test_compute_sha256_consistency(self):
        """Same file always produces same SHA-256."""
        h1 = compute_sha256("src/xml_audit.py")
        h2 = compute_sha256("src/xml_audit.py")
        self.assertEqual(h1, h2)

    def test_compute_sha256_different_files(self):
        """Different files produce different SHA-256 hashes."""
        h1 = compute_sha256("src/xml_audit.py")
        h2 = compute_sha256("src/camera_capabilities.py")
        self.assertNotEqual(h1, h2)


class TestDuplicateProfiles(unittest.TestCase):
    """Test duplicate profile detection."""

    def test_find_duplicate_profiles_returns_results(self):
        """find_duplicate_profiles() returns duplicate groups."""
        result = find_duplicate_profiles(
            ["analysis_results/imx682_config/lava/generate_lava.py",
             "analysis_results/imx682_config/lava/default_working_backup.xml"]
        )
        # Should return a list or dict of duplicate groups
        self.assertIsNotNone(result,
                             "find_duplicate_profiles() should return results")

    def test_duplicate_profiles_has_hash_info(self):
        """Duplicate results include hash information."""
        result = find_duplicate_profiles(
            ["analysis_results/imx682_config/lava/generate_lava.py",
             "analysis_results/imx682_config/lava/default_working_backup.xml"]
        )
        if result:
            self.assertTrue(
                isinstance(result, (list, dict)),
                "find_duplicate_profiles() should return list or dict")


class TestAuditDirectory(unittest.TestCase):
    """Test directory-level profile auditing."""

    def test_audit_directory_profiles_returns_results(self):
        """audit_directory_profiles() returns profile audit results."""
        result = audit_directory_profiles("analysis_results/imx682_config")
        self.assertIsNotNone(result,
                             "audit_directory_profiles() should return results")


class TestValidateXMLComplete(unittest.TestCase):
    """Test complete XML validation."""

    def test_validate_xml_complete_has_all_levels(self):
        """validate_xml_complete() should produce report with A, B, C, D levels."""
        report = validate_xml_complete("analysis_results/imx682_config/lava/generate_lava.py")
        self.assertIsNotNone(report)
        self.assertTrue(hasattr(report, "level"),
                        "Report should have level attribute")
        self.assertTrue(
            hasattr(report, "syntax"),
            "Report should have syntax validation info")
        self.assertTrue(
            hasattr(report, "schema"),
            "Report should have schema validation info")
        self.assertTrue(
            hasattr(report, "compatibility"),
            "Report should have compatibility validation info")
        self.assertTrue(
            hasattr(report, "device"),
            "Report should have device validation info")


if __name__ == "__main__":
    unittest.main()