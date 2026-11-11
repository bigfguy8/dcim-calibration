#!/usr/bin/env python3
"""Reproducibility check for the active AI profile."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]


class AIProfileTests(unittest.TestCase):
    def test_ai_profile_is_reproducible(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "make_ai_profile.py"), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
