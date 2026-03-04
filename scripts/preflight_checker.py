#!/usr/bin/env python3
"""
preflight_checker.py

Generates bash script fragments that perform preflight checks on a git repository.
When executed, the generated script prints a formatted status report with
warnings, errors, and recommended next steps.

Usage:
  Integrated: python3 git_ops.py --from-text "preflight check"
  Standalone: python3 preflight_checker.py
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class PreflightChecker:
    """Generates bash script fragments for preflight checks."""

    DEFAULT_CHECKS: Dict[str, bool] = {
        "check_branch": True,
        "check_detached_head": True,
        "check_uncommitted": True,
        "check_untracked": True,
        "check_stashes": True,
        "check_remote_status": True,
        "check_conflicts": True,
        "fetch_before_check": True,
        "show_recommendations": True,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize with optional config from git-ops.yml preflight section.

        Args:
            config: dict of preflight settings, or None for defaults.
        """
        self.checks: Dict[str, bool] = {**self.DEFAULT_CHECKS}
        if config:
            self.checks.update(config)

    def generate_script(self) -> str:
        """
        Generate a complete bash script fragment that performs all enabled
        preflight checks and prints a formatted report.

        Returns:
            Bash script string to be included in the generated script.
        """
        parts = []
        parts.append(self._header())

        if self.checks.get("check_branch", True):
            parts.append(self._check_branch())
        if self.checks.get("check_detached_head", True):
            parts.append(self._check_detached_head())
        if self.checks.get("check_uncommitted", True):
            parts.append(self._check_uncommitted())
        if self.checks.get("check_untracked", True):
            parts.append(self._check_untracked())
        if self.checks.get("check_stashes", True):
            parts.append(self._check_stashes())
        if self.checks.get("check_remote_status", True):
            parts.append(self._check_remote_status())
        if self.checks.get("check_conflicts", True):
            parts.append(self._check_conflicts())

        parts.append(self._summary())

        if self.checks.get("show_recommendations", True):
            parts.append(self._recommendations())

        parts.append(self._footer())
        return "\n".join(parts)

    def _header(self) -> str:
        return r"""# ---- preflight check begin ----
echo ""
echo "========================================"
echo "  PREFLIGHT CHECK RESULTS"
echo "========================================"
echo ""

PREFLIGHT_WARNINGS=0
PREFLIGHT_ERRORS=0
"""

    def _check_branch(self) -> str:
        return r"""# -- Branch Info --
echo "Branch: $BR"
"""

    def _check_detached_head(self) -> str:
        return r"""# -- Detached HEAD Check --
if [ "$BR" = "HEAD" ]; then
  echo "  [!!] Detached HEAD state"
  PREFLIGHT_ERRORS=$((PREFLIGHT_ERRORS + 1))
else
  echo "  [ok] Not in detached HEAD state"
fi
"""

    def _check_uncommitted(self) -> str:
        return r"""# -- Uncommitted Changes --
MODIFIED_COUNT=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
STAGED_COUNT=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
if [ "$STAGED_COUNT" -gt 0 ]; then
  echo "  [i] $STAGED_COUNT staged file(s) ready to commit"
fi
if [ "$MODIFIED_COUNT" -gt 0 ]; then
  echo "  [!] $MODIFIED_COUNT unstaged modified file(s)"
  PREFLIGHT_WARNINGS=$((PREFLIGHT_WARNINGS + 1))
else
  if [ "$STAGED_COUNT" -eq 0 ]; then
    echo "  [ok] Working tree is clean"
  fi
fi
"""

    def _check_untracked(self) -> str:
        return r"""# -- Untracked Files --
UNTRACKED_COUNT=$(git ls-files --others --exclude-standard \
  2>/dev/null | wc -l | tr -d ' ')
if [ "$UNTRACKED_COUNT" -gt 0 ]; then
  echo "  [!] $UNTRACKED_COUNT untracked file(s)"
  PREFLIGHT_WARNINGS=$((PREFLIGHT_WARNINGS + 1))
else
  echo "  [ok] No untracked files"
fi
"""

    def _check_stashes(self) -> str:
        return r"""# -- Stashes --
STASH_COUNT=$(git stash list 2>/dev/null | wc -l | tr -d ' ')
if [ "$STASH_COUNT" -gt 0 ]; then
  echo "  [i] $STASH_COUNT stash(es) saved"
else
  echo "  [ok] No stashes"
fi
"""

    def _check_remote_status(self) -> str:
        fetch_cmd = ""
        if self.checks.get("fetch_before_check", True):
            fetch_cmd = 'git fetch "$REMOTE" --quiet 2>/dev/null || true\n'

        return f"""{fetch_cmd}# -- Remote Status --
if has_upstream; then
  AHEAD=$(git rev-list --count "$REMOTE/$BR..HEAD" 2>/dev/null || echo "0")
  BEHIND=$(git rev-list --count "HEAD..$REMOTE/$BR" 2>/dev/null || echo "0")
  if [ "$AHEAD" -gt 0 ] && [ "$BEHIND" -gt 0 ]; then
    echo "  [!] Branch diverged: $AHEAD ahead, $BEHIND behind $REMOTE/$BR"
    PREFLIGHT_WARNINGS=$((PREFLIGHT_WARNINGS + 1))
  elif [ "$AHEAD" -gt 0 ]; then
    echo "  [i] $AHEAD commit(s) ahead of $REMOTE/$BR (ready to push)"
  elif [ "$BEHIND" -gt 0 ]; then
    echo "  [!] $BEHIND commit(s) behind $REMOTE/$BR (pull recommended)"
    PREFLIGHT_WARNINGS=$((PREFLIGHT_WARNINGS + 1))
  else
    echo "  [ok] Up to date with $REMOTE/$BR"
  fi
else
  echo "  [i] No upstream tracking branch set"
fi
"""

    def _check_conflicts(self) -> str:
        return r"""# -- Merge Conflicts --
CONFLICT_COUNT=$(git ls-files --unmerged 2>/dev/null | wc -l | tr -d ' ')
if [ "$CONFLICT_COUNT" -gt 0 ]; then
  echo "  [!!] Unresolved merge conflicts ($CONFLICT_COUNT entries)"
  PREFLIGHT_ERRORS=$((PREFLIGHT_ERRORS + 1))
else
  echo "  [ok] No merge conflicts"
fi
"""

    def _summary(self) -> str:
        return r"""# -- Summary --
echo ""
echo "----------------------------------------"
if [ "$PREFLIGHT_ERRORS" -gt 0 ]; then
  echo "Result: $PREFLIGHT_ERRORS error(s), $PREFLIGHT_WARNINGS warning(s)"
elif [ "$PREFLIGHT_WARNINGS" -gt 0 ]; then
  echo "Result: $PREFLIGHT_WARNINGS warning(s), no errors"
else
  echo "Result: All checks passed"
fi
"""

    def _recommendations(self) -> str:
        return r"""# -- Recommendations --
echo ""
echo "Recommended next steps:"
STEP=1
if [ "${CONFLICT_COUNT:-0}" -gt 0 ]; then
  echo "  $STEP. Resolve merge conflicts first"
  STEP=$((STEP + 1))
fi
if [ "${MODIFIED_COUNT:-0}" -gt 0 ]; then
  echo "  $STEP. Stage modified files: git add -A"
  STEP=$((STEP + 1))
fi
if [ "${UNTRACKED_COUNT:-0}" -gt 0 ]; then
  echo "  $STEP. Review untracked files: git status"
  STEP=$((STEP + 1))
fi
if [ "${STAGED_COUNT:-0}" -gt 0 ] || [ "${MODIFIED_COUNT:-0}" -gt 0 ]; then
  echo "  $STEP. Commit changes: git commit -m \"...\""
  STEP=$((STEP + 1))
fi
if [ "${BEHIND:-0}" -gt 0 ]; then
  echo "  $STEP. Pull remote changes: git pull --rebase"
  STEP=$((STEP + 1))
fi
if [ "${AHEAD:-0}" -gt 0 ]; then
  echo "  $STEP. Push to remote: git push"
  STEP=$((STEP + 1))
fi
if [ "$STEP" -eq 1 ]; then
  echo "  No action needed. Repository is in good shape."
fi
"""

    def _footer(self) -> str:
        return r"""echo ""
echo "========================================"
# ---- preflight check end ----
"""


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Git-ops preflight checker")
    parser.add_argument("--no-fetch", action="store_true", help="Skip remote fetch")
    parser.add_argument(
        "--no-recommendations", action="store_true", help="Skip recommendations section"
    )
    parser.add_argument("--config", metavar="FILE", help="Path to configuration file")

    args = parser.parse_args()

    # Load config if available
    config: Dict[str, Any] = {}
    try:
        from config_manager import ConfigManager

        cm = ConfigManager(args.config)
        config = cm.get("preflight", {}) or {}
    except ImportError:
        pass

    if args.no_fetch:
        config["fetch_before_check"] = False
        config["check_remote_status"] = False
    if args.no_recommendations:
        config["show_recommendations"] = False

    checker = PreflightChecker(config)
    script = checker.generate_script()

    print("```bash")
    print(script.rstrip())
    print("```")


if __name__ == "__main__":
    main()
