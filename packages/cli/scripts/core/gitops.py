"""
Autonomous git operations: stage, commit, push to origin/main over SSH.

Uses plain ``git`` subprocesses (no GitPython) so it runs on stock Python.
When ``GIT_SSH_KEY`` is configured, pushes run with
``GIT_SSH_COMMAND=ssh -i <key> -o IdentitiesOnly=yes
-o StrictHostKeyChecking=accept-new`` so the daemon can authenticate without
interactive prompts.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from .config import DaemonConfig


class GitOps:
    def __init__(self, config: DaemonConfig, log) -> None:
        self.cfg = config
        self.log = log
        self._env = self._build_git_env()

    # ------------------------------------------------------------------ #
    # Environment / transport
    # ------------------------------------------------------------------ #
    def _build_git_env(self) -> dict[str, str]:
        env = dict(os.environ)
        ssh_cmd_parts: list[str] = []
        if self.cfg.git_ssh_key:
            expanded = os.path.expanduser(self.cfg.git_ssh_key)
            ssh_cmd_parts.append(f"ssh -i {expanded}")
            ssh_cmd_parts.append("-o IdentitiesOnly=yes")
            ssh_cmd_parts.append("-o StrictHostKeyChecking=accept-new")
            ssh_cmd_parts.append("-o BatchMode=yes")
        # Respect an operator-supplied GIT_SSH_COMMAND; otherwise synthesize one.
        if env.get("GIT_SSH_COMMAND"):
            ssh_cmd_parts.insert(0, env["GIT_SSH_COMMAND"])
        if ssh_cmd_parts:
            env["GIT_SSH_COMMAND"] = " ".join(ssh_cmd_parts)
        return env

    def _run(
        self, args: list[str], cwd=None, timeout: int = 60
    ) -> tuple[int, str, str]:
        try:
            p = subprocess.run(
                ["git"] + args,
                cwd=str(cwd or self.cfg.base_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self._env,
            )
            return p.returncode, p.stdout.strip(), p.stderr.strip()
        except FileNotFoundError:
            return -1, "", "git not found"
        except subprocess.TimeoutExpired:
            return -1, "", "git command timed out"

    # ------------------------------------------------------------------ #
    # Query helpers
    # ------------------------------------------------------------------ #
    def is_repo(self) -> bool:
        rc, _, _ = self._run(["rev-parse", "--is-inside-work-tree"])
        return rc == 0

    def current_branch(self) -> Optional[str]:
        rc, out, _ = self._run(["rev-parse", "--abbrev-ref", "HEAD"])
        return out if rc == 0 else None

    def remote_url(self) -> Optional[str]:
        rc, out, _ = self._run(["remote", "get-url", self.cfg.git_remote])
        return out if rc == 0 else None

    # ------------------------------------------------------------------ #
    # Commit / push
    # ------------------------------------------------------------------ #
    def commit(self, files: list[str], message: str) -> tuple[bool, str]:
        """Stage and commit *files*. Returns (ok, detail)."""
        if not files:
            return False, "nothing to stage"
        if not self.is_repo():
            self.log.warn("git", "Not inside a git work tree; skipping commit")
            return False, "not a git repo"

        rc, _, err = self._run(["add"] + files)
        if rc != 0:
            self.log.error("git", f"git add failed: {err}")
            return False, f"git add failed: {err}"

        rc, staged, _ = self._run(["diff", "--cached", "--name-only"])
        if not staged:
            self.log.debug("git", "No changes to commit")
            return False, "no changes"

        rc, out, err = self._run(["commit", "-m", message])
        if rc != 0:
            self.log.error("git", f"git commit failed: {err}")
            return False, f"git commit failed: {err}"

        count = len(staged.splitlines())
        self.log.info("git", f"Committed {count} file(s): {message}")
        return True, f"committed {count} file(s)"

    def push(self, branch: Optional[str] = None) -> tuple[bool, str]:
        """Push the current branch to the configured remote/branch."""
        if not self.cfg.git_auto_push:
            return False, "push disabled"
        if not self.is_repo():
            return False, "not a git repo"
        branch = branch or self.cfg.git_branch
        # Push local HEAD to remote branch: HEAD:<remote_branch>
        rc, out, err = self._run(
            ["push", self.cfg.git_remote, f"HEAD:{branch}"], timeout=120
        )
        if rc != 0:
            self.log.error("git", f"git push failed: {err}")
            return False, f"git push failed: {err}"
        self.log.info("git", f"Pushed to {self.cfg.git_remote}/{branch}")
        return True, f"pushed to {self.cfg.git_remote}/{branch}"

    # ------------------------------------------------------------------ #
    # Convenience: commit + push for a successful run
    # ------------------------------------------------------------------ #
    def auto_commit_and_push(
        self,
        changed_files,
        result,
        prefix: str = "daemon(calibration):",
    ) -> dict[str, Any]:
        """
        Stage + commit changed files, then push if enabled and the run
        succeeded. Returns a dict with committed/pushed flags and detail.
        """
        info: dict[str, Any] = {
            "enabled": self.cfg.git_auto_commit,
            "push_enabled": self.cfg.git_auto_push,
            "committed": False,
            "pushed": False,
            "detail": "",
            "remote": self.cfg.git_remote,
            "branch": self.cfg.git_branch,
        }

        if not self.cfg.git_auto_commit:
            info["detail"] = "auto-commit disabled"
            return info

        if not changed_files:
            info["detail"] = "no changed files"
            return info

        # Only commit files that live inside the repo work tree.
        staged: list[str] = []
        for f in changed_files:
            p = f if isinstance(f, str) else str(f)
            try:
                rel = str(Path(p).resolve().relative_to(self.cfg.base_dir.resolve()))
                staged.append(rel)
            except ValueError:
                # File outside the repo (e.g. /sdcard) — stage its repo mirror
                # instead if it was copied into captures/.
                continue

        if not staged:
            info["detail"] = "no repo-relative files to stage"
            return info

        # Build a rich commit message from the run result.
        processed = len(result.processed)
        errors = len(result.errors)
        message = (
            f"{prefix} run {result.run_id}\n\n"
            f"- processed {processed} asset(s)\n"
            f"- errors: {errors}\n"
            f"- report: analysis/reports/{result.run_id}/"
        )

        ok, detail = self.commit(staged, message)
        info["committed"] = ok
        info["detail"] = detail

        if ok and result.success and self.cfg.git_auto_push:
            pok, pdetail = self.push()
            info["pushed"] = pok
            if not pok:
                info["detail"] += f"; push: {pdetail}"
        return info


def discover_ssh_keys() -> list[str]:
    """Return candidate SSH private key paths from common locations."""
    candidates = []
    home = os.path.expanduser("~")
    ssh_dir = os.path.join(home, ".ssh")
    if os.path.isdir(ssh_dir):
        for name in ("id_ed25519", "id_rsa", "id_ecdsa", "identity"):
            p = os.path.join(ssh_dir, name)
            if os.path.isfile(p) and not name.endswith(".pub"):
                candidates.append(p)
    env_key = os.getenv("GIT_SSH_KEY")
    if env_key:
        candidates.insert(0, os.path.expanduser(env_key))
    return candidates
