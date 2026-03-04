#!/usr/bin/env python3
"""
decision_engine.py

Intelligent Decision Engine for git-ops.
Analyzes full repository state and recommends a step-by-step workflow.
Reuses PreflightChecker's bash fragments for state gathering, then adds
its own conditional logic for goal detection, recommendations, and risk assessment.

Usage:
  Integrated: python3 git_ops.py --from-text "what should I do"
  Standalone: python3 decision_engine.py [--goal commit|push|merge|pr]
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class DecisionEngine:
    """Generates bash scripts that analyze repo state and recommend workflows."""

    DEFAULT_CONFIG = {
        "default_target_branch": "main",
        "fetch_before_analyze": True,
        "show_situation": True,
        "show_risks": True,
        "show_next_command": True,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config: Dict[str, Any] = {**self.DEFAULT_CONFIG}
        if config:
            self.config.update(config)

    def generate_script(self, goal: Optional[str] = None) -> str:
        """Main entry point: generate a complete analysis + recommendation script."""
        parts = []
        parts.append(self._header())
        parts.append(self._gather_state())
        parts.append(self._detect_goal(goal))

        if self.config.get("show_situation", True):
            parts.append(self._show_situation())

        parts.append(self._recommend_steps())

        if self.config.get("show_risks", True):
            parts.append(self._show_risks())

        if self.config.get("show_next_command", True):
            parts.append(self._suggest_command())

        parts.append(self._footer())
        return "\n".join(parts)

    def _header(self) -> str:
        return r"""# ---- decision engine begin ----
echo ""
echo "========================================"
echo "  WORKFLOW RECOMMENDATION"
echo "========================================"
echo ""

# Variables used by preflight checker fragments
PREFLIGHT_WARNINGS=0
PREFLIGHT_ERRORS=0
"""

    def _gather_state(self) -> str:
        """Reuse PreflightChecker's _check_* methods to set bash state variables."""
        try:
            from preflight_checker import PreflightChecker

            checker = PreflightChecker(
                {
                    "show_recommendations": False,
                    "fetch_before_check": self.config.get("fetch_before_analyze", True),
                }
            )
            parts = []
            parts.append("# -- Gather repository state --")
            # Reuse individual checks that set $MODIFIED_COUNT, $STAGED_COUNT, etc.
            parts.append(checker._check_uncommitted())
            parts.append(checker._check_untracked())
            parts.append(checker._check_stashes())
            parts.append(checker._check_remote_status())
            parts.append(checker._check_conflicts())
        except ImportError:
            # Fallback: gather state inline if preflight_checker unavailable
            parts = [self._inline_gather_state()]

        # Additional state the decision engine needs
        parts.append(self._check_merge_rebase_state())
        return "\n".join(parts)

    def _inline_gather_state(self) -> str:
        """Fallback state gathering when PreflightChecker is not available."""
        fetch = ""
        if self.config.get("fetch_before_analyze", True):
            fetch = 'git fetch "$REMOTE" --quiet 2>/dev/null || true\n'
        return f"""# -- Gather repository state (inline) --
{fetch}MODIFIED_COUNT=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
STAGED_COUNT=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
UNTRACKED_COUNT=$(git ls-files --others --exclude-standard \
  2>/dev/null | wc -l | tr -d ' ')
STASH_COUNT=$(git stash list 2>/dev/null | wc -l | tr -d ' ')
CONFLICT_COUNT=$(git ls-files --unmerged 2>/dev/null | wc -l | tr -d ' ')
if has_upstream; then
  AHEAD=$(git rev-list --count "$REMOTE/$BR..HEAD" 2>/dev/null || echo "0")
  BEHIND=$(git rev-list --count "HEAD..$REMOTE/$BR" 2>/dev/null || echo "0")
else
  AHEAD=0
  BEHIND=0
fi
"""

    def _check_merge_rebase_state(self) -> str:
        return r"""# -- Merge/Rebase state --
IN_MERGE=0
IN_REBASE=0
if [ -f "$(git rev-parse --git-dir 2>/dev/null)/MERGE_HEAD" ]; then
  IN_MERGE=1
fi
if [ -d "$(git rev-parse --git-dir 2>/dev/null)/rebase-merge" ] || \
   [ -d "$(git rev-parse --git-dir 2>/dev/null)/rebase-apply" ]; then
  IN_REBASE=1
fi
"""

    def _detect_goal(self, goal: Optional[str] = None) -> str:
        goal_init = f'GOAL="{goal}"' if goal else 'GOAL="auto"'
        return f"""{goal_init}

# -- Auto-detect goal --
if [ "$GOAL" = "auto" ]; then
  if [ "$IN_MERGE" -eq 1 ] || [ "$IN_REBASE" -eq 1 ]; then
    GOAL="resolve-conflict"
  elif [ "${{CONFLICT_COUNT:-0}}" -gt 0 ]; then
    GOAL="resolve-conflict"
  elif [ "${{STAGED_COUNT:-0}}" -gt 0 ]; then
    GOAL="commit"
  elif [ "${{MODIFIED_COUNT:-0}}" -gt 0 ] || [ "${{UNTRACKED_COUNT:-0}}" -gt 0 ]; then
    GOAL="stage-and-commit"
  elif [ "${{AHEAD:-0}}" -gt 0 ]; then
    GOAL="push"
  elif [ "${{BEHIND:-0}}" -gt 0 ]; then
    GOAL="pull"
  else
    GOAL="up-to-date"
  fi
fi
echo "Detected goal: $GOAL"
echo ""
"""

    def _show_situation(self) -> str:
        return r"""# -- Current situation --
echo "Current situation:"
if [ "$IN_MERGE" -eq 1 ]; then
  echo "  You are in the middle of a MERGE"
fi
if [ "$IN_REBASE" -eq 1 ]; then
  echo "  You are in the middle of a REBASE"
fi
if [ "${CONFLICT_COUNT:-0}" -gt 0 ]; then
  echo "  [!!] $CONFLICT_COUNT unmerged conflict entries"
fi
if [ "${STAGED_COUNT:-0}" -gt 0 ]; then
  echo "  [i] $STAGED_COUNT file(s) staged for commit"
fi
if [ "${MODIFIED_COUNT:-0}" -gt 0 ]; then
  echo "  [i] $MODIFIED_COUNT file(s) modified (unstaged)"
fi
if [ "${UNTRACKED_COUNT:-0}" -gt 0 ]; then
  echo "  [i] $UNTRACKED_COUNT untracked file(s)"
fi
if [ "${AHEAD:-0}" -gt 0 ]; then
  echo "  [i] $AHEAD commit(s) ahead of remote"
fi
if [ "${BEHIND:-0}" -gt 0 ]; then
  echo "  [i] $BEHIND commit(s) behind remote"
fi
if [ "${STASH_COUNT:-0}" -gt 0 ]; then
  echo "  [i] $STASH_COUNT stash(es) saved"
fi
if [ "$IN_MERGE" -eq 0 ] && [ "$IN_REBASE" -eq 0 ] && \
   [ "${CONFLICT_COUNT:-0}" -eq 0 ] && [ "${STAGED_COUNT:-0}" -eq 0 ] && \
   [ "${MODIFIED_COUNT:-0}" -eq 0 ] && [ "${UNTRACKED_COUNT:-0}" -eq 0 ] && \
   [ "${AHEAD:-0}" -eq 0 ] && [ "${BEHIND:-0}" -eq 0 ]; then
  echo "  Working tree is clean and up to date"
fi
echo ""
"""

    def _recommend_steps(self) -> str:
        return r"""# -- Recommended workflow --
echo "Recommended workflow:"
STEP=1

if [ "$GOAL" = "resolve-conflict" ]; then
  if [ "${CONFLICT_COUNT:-0}" -gt 0 ]; then
    echo "  $STEP. Resolve conflicts in each file:"
    git diff --name-only --diff-filter=U 2>/dev/null | \
      while read -r f; do echo "        $f"; done
    STEP=$((STEP + 1))
  fi
  if [ "$IN_MERGE" -eq 1 ]; then
    echo "  $STEP. git add <resolved-files> && git commit"
    STEP=$((STEP + 1))
    echo "  (or: git merge --abort to cancel)"
  elif [ "$IN_REBASE" -eq 1 ]; then
    echo "  $STEP. git add <resolved-files> && git rebase --continue"
    STEP=$((STEP + 1))
    echo "  (or: git rebase --abort to cancel)"
  fi
fi

if [ "$GOAL" = "stage-and-commit" ]; then
  if [ "${BEHIND:-0}" -gt 0 ]; then
    echo "  $STEP. git pull --rebase  (you are $BEHIND commit(s) behind)"
    STEP=$((STEP + 1))
  fi
  echo "  $STEP. git add -A"
  STEP=$((STEP + 1))
  echo "  $STEP. git commit -m \"...\""
  STEP=$((STEP + 1))
  if has_upstream 2>/dev/null; then
    echo "  $STEP. git push"
    STEP=$((STEP + 1))
  fi
fi

if [ "$GOAL" = "commit" ]; then
  if [ "${BEHIND:-0}" -gt 0 ]; then
    echo "  $STEP. git pull --rebase  (you are $BEHIND commit(s) behind)"
    STEP=$((STEP + 1))
  fi
  if [ "${MODIFIED_COUNT:-0}" -gt 0 ]; then
    echo "  $STEP. Review unstaged changes: git diff"
    STEP=$((STEP + 1))
  fi
  echo "  $STEP. git commit -m \"...\""
  STEP=$((STEP + 1))
  if has_upstream 2>/dev/null; then
    echo "  $STEP. git push"
    STEP=$((STEP + 1))
  fi
fi

if [ "$GOAL" = "push" ]; then
  echo "  $STEP. git push  ($AHEAD commit(s) to push)"
  STEP=$((STEP + 1))
fi

if [ "$GOAL" = "pull" ]; then
  echo "  $STEP. git pull --rebase  ($BEHIND commit(s) to pull)"
  STEP=$((STEP + 1))
fi

if [ "$GOAL" = "up-to-date" ]; then
  echo "  No action needed. Repository is in good shape."
fi

echo ""
"""

    def _show_risks(self) -> str:
        return r"""# -- Risk assessment --
HAS_RISKS=0
if [ "${BEHIND:-0}" -gt 10 ]; then
  if [ "$HAS_RISKS" -eq 0 ]; then echo "Risks:"; HAS_RISKS=1; fi
  echo "  [!] Remote has $BEHIND new commits - rebase may have conflicts"
fi
if [ "${AHEAD:-0}" -gt 20 ]; then
  if [ "$HAS_RISKS" -eq 0 ]; then echo "Risks:"; HAS_RISKS=1; fi
  echo "  [!] You have $AHEAD local commits - consider squashing before push"
fi
if [ "${STASH_COUNT:-0}" -gt 0 ]; then
  if [ "$HAS_RISKS" -eq 0 ]; then echo "Risks:"; HAS_RISKS=1; fi
  echo "  [i] You have $STASH_COUNT stash(es) - don't forget them"
fi
if [ "${MODIFIED_COUNT:-0}" -gt 0 ] && [ "${STAGED_COUNT:-0}" -gt 0 ]; then
  if [ "$HAS_RISKS" -eq 0 ]; then echo "Risks:"; HAS_RISKS=1; fi
  echo "  [i] You have both staged and unstaged changes - review before committing"
fi
if [ "$HAS_RISKS" -gt 0 ]; then
  echo ""
fi
"""

    def _suggest_command(self) -> str:
        return r"""# -- Suggested gops command --
echo "Suggested gops command:"
if [ "$GOAL" = "resolve-conflict" ]; then
  echo '  gops "resolve conflicts"'
elif [ "$GOAL" = "stage-and-commit" ]; then
  echo '  gops "commit and push"'
elif [ "$GOAL" = "commit" ]; then
  echo '  gops "commit and push"'
elif [ "$GOAL" = "push" ]; then
  echo '  gops "push"'
elif [ "$GOAL" = "pull" ]; then
  echo '  gops "push"   # syncs (pull --rebase) then pushes'
elif [ "$GOAL" = "up-to-date" ]; then
  echo '  Nothing to do!'
fi
"""

    def _footer(self) -> str:
        return r"""echo ""
echo "========================================"
# ---- decision engine end ----
"""


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Git-ops decision engine")
    parser.add_argument(
        "--goal",
        choices=["commit", "push", "merge", "pr"],
        help="Specify goal instead of auto-detecting",
    )
    parser.add_argument(
        "--no-fetch", action="store_true", help="Skip remote fetch before analysis"
    )
    parser.add_argument(
        "--no-risks", action="store_true", help="Skip risk assessment section"
    )
    parser.add_argument("--config", metavar="FILE", help="Path to configuration file")

    args = parser.parse_args()

    # Load config if available
    config: Dict[str, Any] = {}
    try:
        from config_manager import ConfigManager

        cm = ConfigManager(args.config)
        config = cm.get("decision_engine", {}) or {}
    except ImportError:
        pass

    if args.no_fetch:
        config["fetch_before_analyze"] = False
    if args.no_risks:
        config["show_risks"] = False

    engine = DecisionEngine(config)
    script = engine.generate_script(args.goal)

    print("```bash")
    print(script.rstrip())
    print("```")


if __name__ == "__main__":
    main()
