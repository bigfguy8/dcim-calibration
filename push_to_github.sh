#!/data/data/com.termux/files/usr/bin/bash
# Termux push script for dcim-calibration
# Usage: ./push_to_github.sh [commit message]
#
# Prerequisites (run once in Termux):
#   pkg install openssh git
#   ssh-keygen -t ed25519 -C "your_email@example.com"
#   # Add ~/.ssh/id_ed25519.pub to GitHub SSH keys
#   ssh -T git@github.com   # verify auth
#
set -euo pipefail

REPO_DIR="${DCIM_CALIBRATION_DIR:-$HOME/dcim-calibration}"
COMMIT_MSG="${1:-feat(calibration): sync Termux updates to origin/main}"

cd "$REPO_DIR" || { echo "ERROR: repo not found at $REPO_DIR"; exit 1; }

echo "=== [1/5] Git status ==="
git status --short

echo ""
echo "=== [2/5] Fetching origin ==="
git fetch origin

echo ""
echo "=== [3/5] Checking ahead/behind ==="
git status -sb

echo ""
echo "=== [4/5] Integrating remote changes (rebase) ==="
if git rev-parse --verify origin/main >/dev/null 2>&1; then
    git rebase origin/main || {
        echo ""
        echo "ERROR: Rebase conflicts detected!"
        echo "Resolve conflicts, then run:"
        echo "  git add <resolved-files>"
        echo "  git rebase --continue"
        echo "  $0 \"$COMMIT_MSG\""
        exit 1
    }
fi

echo ""
echo "=== [5/5] Pushing to origin/main ==="
git push origin main

echo ""
echo "=== Done ==="
git log --oneline -3
