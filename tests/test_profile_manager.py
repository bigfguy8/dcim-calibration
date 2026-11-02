#!/usr/bin/env python3
"""Suite 7: Profile Manager tests."""
import unittest
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.profile_manager import (
    classify_family,
    profile_info_from_path,
    backup_profile,
    rollback_to_latest,
    ProfileFamily,
    ProvenanceRecord,
    ProfileInfo,
)


class TestProfileManagerFamilyClassification(unittest.TestCase):
    """Test profile-family classification."""

    def test_classify_family_lmc(self):
        """classify_family() identifies LMC family profiles."""
        lmc_keys = {"pref_qjpg_key", "ptchr_contrast", "ptchr_saturation"}
        family = classify_family(lmc_keys)
        self.assertEqual(family, ProfileFamily.LMC)

    def test_classify_family_bsg(self):
        """classify_family() identifies BSG family profiles."""
        bsg_keys = {"pref_quality_key", "camera_id_back"}
        family = classify_family(bsg_keys)
        self.assertEqual(family, ProfileFamily.BSG)

    def test_classify_family_mixed(self):
        """classify_family() identifies MIXED family profiles."""
        mixed_keys = {"pref_qjpg_key", "pref_quality_key"}
        family = classify_family(mixed_keys)
        self.assertEqual(family, ProfileFamily.MIXED)

    def test_classify_family_experimental(self):
        """classify_family() returns EXPERIMENTAL for unknown keys."""
        unknown_keys = {"random_key1", "random_key2"}
        family = classify_family(unknown_keys)
        self.assertEqual(family, ProfileFamily.EXPERIMENTAL)


class TestProfileManagerProfileInfo(unittest.TestCase):
    """Test profile info extraction."""

    def test_profile_info_from_path_returns_info(self):
        """profile_info_from_path() extracts profile metadata."""
        info = profile_info_from_path(
            "analysis_results/imx682_config/lava/generate_lava.py"
        )
        self.assertIsNotNone(info)

    def test_profile_info_has_required_fields(self):
        """ProfileInfo has expected fields."""
        info = profile_info_from_path(
            "analysis_results/imx682_config/lava/generate_lava.py"
        )
        self.assertTrue(hasattr(info, "family") or
                        hasattr(info, "path") or
                        hasattr(info, "name"),
                        "ProfileInfo must have essential fields")

    def test_profile_info_name(self):
        """ProfileInfo contains the profile name."""
        info = profile_info_from_path(
            "analysis_results/imx682_config/lava/generate_lava.py"
        )
        self.assertIsNotNone(getattr(info, "name", None),
                             "ProfileInfo should have name")


class TestProfileManagerBackupRollback(unittest.TestCase):
    """Test backup and rollback functionality."""

    def test_backup_profile_creates_copy(self):
        """backup_profile() creates a backup copy."""
        test_dir = tempfile.mkdtemp()
        try:
            # Create a test profile
            profile_path = os.path.join(test_dir, "test_profile.xml")
            with open(profile_path, "w") as f:
                f.write("<map><test_key>test_value</test_key></map>")
            
            backup_path = backup_profile(profile_path, test_dir)
            self.assertTrue(os.path.exists(backup_path),
                            "backup_profile should create a backup file")
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_backup_profile_preserves_content(self):
        """Backup copy is byte-identical to original."""
        test_dir = tempfile.mkdtemp()
        try:
            profile_path = os.path.join(test_dir, "original.xml")
            with open(profile_path, "w") as f:
                f.write("<map><original>content</original></map>")
            
            backup_path = backup_profile(profile_path, test_dir)
            with open(profile_path) as f:
                original = f.read()
            with open(backup_path) as f:
                backup = f.read()
            self.assertEqual(original, backup,
                             "Backup must be byte-identical to original")
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()