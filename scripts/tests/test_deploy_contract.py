#!/usr/bin/env python3
"""Deploy-contract tests for scripts/deploy_profiles.sh.

Uses tempfile directories only; never touches /sdcard.
A temp LMC84_SOURCES_REGISTRY is used for the source-overlap tests so the
real configs/sources.json is never modified.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
REPO = SCRIPTS.parent
DEPLOY = SCRIPTS / "deploy_profiles.sh"
XML_DIR = REPO / "configs" / "xml"


def _run_deploy(*args: str, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("CALIB_LMC_DIR", None)
    env.pop("DCIM_LMC_DIR", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [str(DEPLOY), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO),
    )


def _dir_hash(root: Path) -> str:
    """SHA-256 over the sorted (relative_path, bytes) of every file under root."""
    digest = hashlib.sha256()
    if root.is_dir():
        for path in sorted(root.rglob("*")):
            if path.is_file():
                digest.update(path.relative_to(root).as_posix().encode())
                digest.update(b"\0")
                digest.update(str(path.stat().st_size).encode())
                digest.update(b"\0")
    return digest.hexdigest()


class DeployContractTests(unittest.TestCase):
    def test_missing_dest_exits_2(self):
        result = _run_deploy("--dry-run", "--local")
        self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
        self.assertIn("no destination", result.stderr)

    def test_dry_run_exits_0_and_creates_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "calib_dryrun"
            result = _run_deploy("--dest", str(dest), "--dry-run", "--local")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertFalse(dest.exists(), "dry-run must not create the dest dir")

    def test_dry_run_leaves_existing_dest_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "calib"
            dest.mkdir()
            (dest / "keep.xml").write_text("stale config")
            before = _dir_hash(dest)
            result = _run_deploy("--dest", str(dest), "--dry-run", "--local")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(_dir_hash(dest), before, "dry-run must not alter dest")

    def test_prune_moves_non_mandated_to_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "calib"
            dest.mkdir()
            stale = dest / "LXX521_STALE.xml"
            stale.write_text("stale config")
            active = dest / "LXX521_TEX.xml"
            active.write_text((XML_DIR / "LXX521_TEX.xml").read_text())

            result = _run_deploy("--dest", str(dest), "--prune", "--local")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            # Stale source gone, archived target present.
            self.assertFalse(stale.exists(), "stale source must be removed")
            archive_files = list(dest.glob("archive/*/LXX521_STALE.xml"))
            self.assertEqual(len(archive_files), 1, archive_files)
            self.assertTrue(archive_files[0].exists())

            # Active TEX preserved, AI deployed, manifest written with matching hashes.
            self.assertTrue((dest / "LXX521_TEX.xml").exists())
            self.assertTrue((dest / "LXX521_AI.xml").exists())
            manifest = json.loads((dest / "deploy_manifest.json").read_text())
            names = {e["name"] for e in manifest["active_profiles"]}
            self.assertEqual(names, {"LXX521_TEX.xml", "LXX521_AI.xml"})
            for entry in manifest["active_profiles"]:
                deployed = dest / entry["name"]
                data = deployed.read_bytes()
                self.assertEqual(entry["bytes"], len(data))
                self.assertEqual(entry["sha256"], hashlib.sha256(data).hexdigest())

    def test_active_array_is_tex_and_ai(self):
        text = DEPLOY.read_text()
        match = re.search(r'^ACTIVE=\((.*)\)$', text, re.MULTILINE)
        self.assertIsNotNone(match, "ACTIVE= line not found")
        self.assertEqual(match.group(1), '"LXX521_TEX.xml" "LXX521_AI.xml"')

    def test_no_hardcoded_sdcard_lmc84(self):
        hits: list[str] = []
        for root_dir in (SCRIPTS, REPO / "packages"):
            if not root_dir.is_dir():
                continue
            for path in root_dir.rglob("*"):
                if path.is_file() and path.suffix in {".sh", ".py"}:
                    if path.name == Path(__file__).name:
                        continue
                    try:
                        content = path.read_text()
                    except (OSError, UnicodeDecodeError):
                        continue
                    if "/sdcard/lmc8.4" in content:
                        hits.append(str(path.relative_to(REPO)))
        self.assertEqual(hits, [], f"hardcoded /sdcard/lmc8.4 found in: {hits}")

    def _temp_registry(self, live_path: Path) -> Path:
        reg = Path(tempfile.mktemp(suffix=".json"))
        reg.write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "name": "temp_live",
                            "path": str(live_path),
                            "kind": "lmc84",
                            "role": "live",
                        }
                    ]
                }
            )
        )
        return reg

    def test_prune_on_live_source_refuses_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "live_source"
            dest.mkdir()
            (dest / "LXX521_STALE.xml").write_text("stale")
            reg = self._temp_registry(dest)
            try:
                result = _run_deploy(
                    "--dest", str(dest), "--prune", "--local",
                    env_extra={"LMC84_SOURCES_REGISTRY": str(reg)},
                )
                self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
                # Nothing archived.
                self.assertFalse(list(dest.glob("archive/*")))
            finally:
                reg.unlink(missing_ok=True)

    def test_prune_on_live_source_allowed_with_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "live_source"
            dest.mkdir()
            stale = dest / "LXX521_STALE.xml"
            stale.write_text("stale")
            reg = self._temp_registry(dest)
            try:
                result = _run_deploy(
                    "--dest", str(dest), "--prune", "--local", "--force-source-overlap",
                    env_extra={"LMC84_SOURCES_REGISTRY": str(reg)},
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertFalse(stale.exists())
                self.assertEqual(len(list(dest.glob("archive/*/LXX521_STALE.xml"))), 1)
            finally:
                reg.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
