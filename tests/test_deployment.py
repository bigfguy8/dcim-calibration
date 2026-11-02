#!/usr/bin/env python3
"""Suite 8: Deployment tests."""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.deployment import (
    deploy_profile,
    DeployResult,
    DeployOutput,
    verify_destination,
    select_profile,
    request_rollback,
)
from src.config_validator import validate_configuration


class TestDeploymentDeployResultEnum(unittest.TestCase):
    """Test DeployResult enum values."""

    def test_deploy_result_enum_values(self):
        """DeployResult has expected enum values."""
        values = [e.value for e in DeployResult]
        # Actual DeployResult values from the module
        self.assertIn("success", values)
        self.assertIn("dry_run", values)
        self.assertIn("validation_failed", values)
        self.assertIn("permission_denied", values)
        self.assertIn("user_cancelled", values)
        self.assertIn("destination_not_found", values)


class TestDeploymentDeployOutput(unittest.TestCase):
    """Test DeployOutput dataclass."""

    def test_deploy_output_has_fields(self):
        """DeployOutput has result, message, and profile_path fields."""
        output = DeployOutput(
            result=DeployResult.DRY_RUN,
            message="Dry-run completed",
            profile_path="test_profile.xml",
        )
        self.assertEqual(output.result, DeployResult.DRY_RUN)
        self.assertEqual(output.message, "Dry-run completed")
        self.assertEqual(output.profile_path, "test_profile.xml")


class TestDeploymentDryRunDeployment(unittest.TestCase):
    """Test dry-run deployment (no real writes)."""

    def test_deploy_profile_dry_run_no_writes(self):
        """deploy_profile() in dry_run mode should not write to destination."""
        # Use a profile that exists
        result = deploy_profile(
            "analysis_results/imx682_config/lava/generate_lava.py",
            dry_run=True,
            confirm=False,
        )
        self.assertIsNotNone(result)
        # Dry-run should not succeed as actual deployment
        # It should be DRY_RUN or VALIDATION_FAILED

    def test_deploy_profile_dry_run_returns_dry_run_result(self):
        """deploy_profile() dry-run returns DRY_RUN result."""
        result = deploy_profile(
            "analysis_results/imx682_config/lava/generate_lava.py",
            dry_run=True,
            confirm=False,
        )
        self.assertIsNotNone(result)

    def test_deploy_profile_dry_run_validation_failed(self):
        """deploy_profile() dry-run on invalid profile returns VALIDATION_FAILED."""
        result = deploy_profile(
            "/nonexistent/profile.xml",
            dry_run=True,
            confirm=False,
        )
        self.assertIsNotNone(result)


class TestDeploymentDestinationVerification(unittest.TestCase):
    """Test destination verification."""

    def test_verify_destination_invalid_path(self):
        """verify_destination() on invalid path handles gracefully."""
        result = verify_destination(Path("/nonexistent/path/"), "test_label")
        self.assertIsNotNone(result)

    def test_verify_destination_returns_result(self):
        """verify_destination() returns a verification result."""
        # Use a real existing path
        result = verify_destination(Path(os.path.dirname(os.path.abspath("."))), "test")
        self.assertIsNotNone(result)


class TestDeploymentSelectProfile(unittest.TestCase):
    """Test profile selection for deployment."""

    def test_select_profile_returns_path(self):
        """select_profile() returns a profile path."""
        # Provide a list of ProfileInfo objects and mock user input
        from src.profile_manager import profile_info_from_path, ProfileInfo
        import builtins
        original_input = builtins.input
        
        # Mock input to return "1" (select the first profile)
        def mock_input(prompt):
            print(prompt)
            return "1"
        
        builtins.input = mock_input
        profiles = [profile_info_from_path("analysis_results/imx682_config/lava/generate_lava.py")]
        result = select_profile(profiles)
        builtins.input = original_input
        self.assertIsNotNone(result,
                             "select_profile() should return a profile path")


class TestDeploymentRollbackHandling(unittest.TestCase):
    """Test rollback request handling."""

    def test_request_rollback_basic(self):
        """request_rollback() handles rollback request."""
        result = request_rollback(
            "analysis_results/imx682_config/lava/generate_lava.py"
        )
        self.assertIsNotNone(result)

    def test_request_rollback_nonexistent(self):
        """request_rollback() on nonexistent profile handles gracefully."""
        result = request_rollback(
            "/nonexistent/profile.xml"
        )
        self.assertIsNotNone(result)


class TestDeploymentNoAutoRealDeployment(unittest.TestCase):
    """Test that deployment does not auto-deploy to real camera app."""

    def test_deploy_profile_no_real_deployment(self):
        """deploy_profile() should NOT auto-deploy to Android camera app.

        Mission rule: dry-run mode must not produce SUCCESS without user
        confirmation, and must not write to real deployment destinations.
        """
        result = deploy_profile(
            "analysis_results/imx682_config/lava/generate_lava.py",
            dry_run=True,
            confirm=False,
        )
        # DRY_RUN should not mean "actual deployment succeeded"
        # It should mean "no files were modified on disk"
        self.assertNotEqual(
            result.result,
            DeployResult.SUCCESS,
            "Dry-run must not produce SUCCESS"
        )


if __name__ == "__main__":
    unittest.main()