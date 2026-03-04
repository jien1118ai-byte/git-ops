#!/usr/bin/env python3
"""
conflict_detector.py

Generates bash script fragments for proactive conflict detection (test merge)
and guided conflict resolution. When executed, the generated scripts perform
git operations and print formatted reports.

Usage:
  Integrated: python3 git_ops.py --from-text "detect conflicts with develop"
  Standalone: python3 conflict_detector.py --target develop
"""

from __future__ import annotations

import shlex
from typing import Dict, Optional


def q(s: str) -> str:
    """Quote a string for safe use in a shell command."""
    return shlex.quote(s)


class ConflictDetector:
    """Generates bash script fragments for conflict detection and resolution."""

    DEFAULT_CONFIG: Dict[str, object] = {
        "fetch_before_detect": True,
        "default_target_branch": "main",
        "show_file_details": True,
        "show_resolution_guide": True,
        "cleanup_on_error": True,
    }

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize with optional config from git-ops.yml conflict_detection section.

        Args:
            config: dict of conflict_detection settings, or None for defaults.
        """
        self.config: Dict[str, object] = {**self.DEFAULT_CONFIG}
        if config:
            self.config.update(config)

    # ================================================================
    # Proactive Conflict Detection (test merge)
    # ================================================================

    def generate_detect_script(self, target_branch: Optional[str] = None) -> str:
        """
        Generate bash script that performs a test merge to detect potential
        conflicts between the current branch and a target branch.

        Args:
            target_branch: Branch to test merge against. Uses config default if None.

        Returns:
            Bash script string.
        """
        target = target_branch or self.config.get("default_target_branch", "main")

        parts = []
        parts.append(self._detect_header())
        parts.append(self._detect_setup(target))
        parts.append(self._detect_test_merge())
        parts.append(self._detect_analyze())
        parts.append(self._detect_cleanup())
        parts.append(self._detect_report())

        if self.config.get("show_resolution_guide", True):
            parts.append(self._detect_resolution_hints())

        parts.append(self._detect_footer())
        return "\n".join(parts)

    def _detect_header(self) -> str:
        return r"""# ---- conflict detection begin ----
echo ""
echo "========================================"
echo "  CONFLICT DETECTION"
echo "========================================"
echo ""
"""

    def _detect_setup(self, target_branch: str) -> str:
        fetch_cmd = ""
        if self.config.get("fetch_before_detect", True):
            fetch_cmd = 'git fetch "$REMOTE" --quiet 2>/dev/null || true\n'

        return f"""{fetch_cmd}# -- Save current state --
ORIG_BR="$BR"
TARGET_BRANCH={q(target_branch)}
STASH_MADE=0
TEMP_BRANCH="_gops_conflict_test_$$"

echo "Checking: $ORIG_BR -> $TARGET_BRANCH"
echo ""

# Stash uncommitted changes if any
if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
  git stash push -m "gops-conflict-detect-$$" --quiet 2>/dev/null && STASH_MADE=1
fi

# Cleanup trap: always restore state
_gops_detect_cleanup() {{
  git merge --abort 2>/dev/null || true
  git checkout "$ORIG_BR" --quiet 2>/dev/null || true
  git branch -D "$TEMP_BRANCH" --quiet 2>/dev/null || true
  if [ "$STASH_MADE" -eq 1 ]; then
    git stash pop --quiet 2>/dev/null || true
  fi
}}
trap '_gops_detect_cleanup' EXIT
"""

    def _detect_test_merge(self) -> str:
        return r"""# -- Perform test merge --
# Try remote branch first, then local
if git show-ref --verify --quiet "refs/remotes/$REMOTE/$TARGET_BRANCH" 2>/dev/null; then
  git checkout -b "$TEMP_BRANCH" "$REMOTE/$TARGET_BRANCH" --quiet 2>/dev/null
elif git show-ref --verify --quiet "refs/heads/$TARGET_BRANCH" 2>/dev/null; then
  git checkout -b "$TEMP_BRANCH" "$TARGET_BRANCH" --quiet 2>/dev/null
else
  echo "  [!!] Branch '$TARGET_BRANCH' not found (local or remote)"
  exit 1
fi

MERGE_OUTPUT=$(git merge --no-commit --no-ff "$ORIG_BR" 2>&1) || true
MERGE_EXIT=$?
"""

    def _detect_analyze(self) -> str:
        parts = [
            r"""# -- Analyze results --
CONFLICT_FILES=$(git diff --name-only --diff-filter=U 2>/dev/null || true)
if [ -n "$CONFLICT_FILES" ]; then
  CONFLICT_COUNT=$(echo "$CONFLICT_FILES" | wc -l | tr -d ' ')
else
  CONFLICT_COUNT=0
fi

# Check if merge was clean
CHANGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)
if [ -n "$CHANGED_FILES" ]; then
  CHANGED_COUNT=$(echo "$CHANGED_FILES" | wc -l | tr -d ' ')
else
  CHANGED_COUNT=0
fi
"""
        ]

        if self.config.get("show_file_details", True):
            parts.append(
                r"""# Collect per-file details for conflicting files
CONFLICT_DETAILS=""
if [ "$CONFLICT_COUNT" -gt 0 ]; then
  while IFS= read -r cfile; do
    [ -z "$cfile" ] && continue
    # Count conflict markers in file
    MARKERS=$(grep -c "^<<<<<<<" "$cfile" 2>/dev/null || echo "0")
    CONFLICT_DETAILS="${CONFLICT_DETAILS}${cfile}|${MARKERS}\n"
  done <<< "$CONFLICT_FILES"
fi
"""
            )

        return "\n".join(parts)

    def _detect_cleanup(self) -> str:
        return r"""# -- Cleanup (restore original state) --
git merge --abort 2>/dev/null || true
git checkout "$ORIG_BR" --quiet 2>/dev/null || true
git branch -D "$TEMP_BRANCH" --quiet 2>/dev/null || true
if [ "$STASH_MADE" -eq 1 ]; then
  git stash pop --quiet 2>/dev/null || true
  STASH_MADE=0
fi
trap - EXIT
"""

    def _detect_report(self) -> str:
        parts = [
            r"""# -- Report --
echo "----------------------------------------"
if [ "$CONFLICT_COUNT" -gt 0 ]; then
  echo "  [!!] $CONFLICT_COUNT file(s) with conflicts detected"
  echo ""
  echo "Conflicting files:"
  while IFS= read -r cfile; do
    [ -z "$cfile" ] && continue
    echo "  * $cfile"
  done <<< "$CONFLICT_FILES"
"""
        ]

        if self.config.get("show_file_details", True):
            parts.append(
                r"""
  # Show conflict marker counts
  if [ -n "$CONFLICT_DETAILS" ]; then
    echo ""
    echo "Conflict details:"
    echo -e "$CONFLICT_DETAILS" | while IFS='|' read -r dfile dmarkers; do
      [ -z "$dfile" ] && continue
      if [ "$dmarkers" -gt 3 ] 2>/dev/null; then
        echo "  $dfile - $dmarkers conflict regions [HIGH]"
      elif [ "$dmarkers" -gt 1 ] 2>/dev/null; then
        echo "  $dfile - $dmarkers conflict regions [MEDIUM]"
      else
        echo "  $dfile - $dmarkers conflict region [LOW]"
      fi
    done
  fi
"""
            )

        parts.append(
            r"""elif [ "$CHANGED_COUNT" -gt 0 ]; then
  echo "  [ok] No conflicts detected"
  echo "  [i] $CHANGED_COUNT file(s) will be modified (clean merge)"
else
  echo "  [ok] No conflicts detected"
  echo "  [i] Branches are already up to date"
fi

echo ""
echo "----------------------------------------"
"""
        )

        return "\n".join(parts)

    def _detect_resolution_hints(self) -> str:
        return r"""# -- Resolution hints --
if [ "$CONFLICT_COUNT" -gt 0 ]; then
  echo ""
  echo "Recommended actions:"
  echo "  1. Review the conflicting files above"
  echo "  2. Merge/rebase and resolve:"
  echo "     git merge $TARGET_BRANCH"
  echo "     # or: git rebase $TARGET_BRANCH"
  echo "  3. Fix each conflict, then:"
  echo "     git add <file>"
  echo "  4. Complete the merge/rebase:"
  echo "     git commit"
  echo "     # or: git rebase --continue"
  echo ""
  echo "  Or use: gops \"resolve conflicts\""
fi
"""

    def _detect_footer(self) -> str:
        return r"""echo ""
echo "========================================"
# ---- conflict detection end ----
"""

    # ================================================================
    # Conflict Resolution Guidance (when in conflict state)
    # ================================================================

    def generate_resolve_script(self, file_path: Optional[str] = None) -> str:
        """
        Generate bash script that guides the user through resolving
        existing merge/rebase conflicts.

        Args:
            file_path: Optional specific file to show guidance for.

        Returns:
            Bash script string.
        """
        parts = []
        parts.append(self._resolve_header())
        parts.append(self._resolve_check_state())
        parts.append(self._resolve_list_conflicts())

        if file_path:
            parts.append(self._resolve_file_options(file_path))
        else:
            parts.append(self._resolve_general_options())

        parts.append(self._resolve_footer())
        return "\n".join(parts)

    def _resolve_header(self) -> str:
        return r"""# ---- conflict resolution guide begin ----
echo ""
echo "========================================"
echo "  CONFLICT RESOLUTION GUIDE"
echo "========================================"
echo ""
"""

    def _resolve_check_state(self) -> str:
        return r"""# -- Check if we're in a conflict state --
IN_MERGE=0
IN_REBASE=0
CONFLICT_TYPE="none"

if [ -f ".git/MERGE_HEAD" ]; then
  IN_MERGE=1
  CONFLICT_TYPE="merge"
  echo "Status: Merge in progress"
elif [ -d ".git/rebase-merge" ] || [ -d ".git/rebase-apply" ]; then
  IN_REBASE=1
  CONFLICT_TYPE="rebase"
  echo "Status: Rebase in progress"
else
  # Check for unresolved conflicts without active merge/rebase
  UNMERGED=$(git ls-files --unmerged 2>/dev/null | wc -l | tr -d ' ')
  if [ "$UNMERGED" -gt 0 ]; then
    echo "Status: Unresolved conflicts found"
    CONFLICT_TYPE="unresolved"
  else
    echo "  [ok] No conflicts to resolve"
    echo ""
    echo "  Tip: Use 'gops \"detect conflicts with <branch>\"' to check"
    echo "  for potential conflicts before merging."
    echo ""
    echo "========================================"
    exit 0
  fi
fi
echo ""
"""

    def _resolve_list_conflicts(self) -> str:
        return r"""# -- List conflicting files --
CONFLICT_FILES=$(git diff --name-only --diff-filter=U 2>/dev/null || true)
if [ -z "$CONFLICT_FILES" ]; then
  CONFLICT_FILES=$(git ls-files --unmerged 2>/dev/null | cut -f2 | sort -u || true)
fi

if [ -n "$CONFLICT_FILES" ]; then
  CONFLICT_COUNT=$(echo "$CONFLICT_FILES" | wc -l | tr -d ' ')
  echo "Conflicting files ($CONFLICT_COUNT):"
  echo ""
  IDX=1
  while IFS= read -r cfile; do
    [ -z "$cfile" ] && continue
    MARKERS=$(grep -c "^<<<<<<<" "$cfile" 2>/dev/null || echo "0")
    STATUS="unresolved"
    # Check if file has been staged (resolved)
    if git diff --cached --quiet -- "$cfile" 2>/dev/null && ! grep -q "^<<<<<<<" "$cfile" 2>/dev/null; then
      STATUS="resolved"
      echo "  $IDX. [ok] $cfile (resolved)"
    else
      echo "  $IDX. [!!] $cfile ($MARKERS conflict markers)"
    fi
    IDX=$((IDX + 1))
  done <<< "$CONFLICT_FILES"
  echo ""
else
  echo "  [ok] All conflicts have been resolved"
  echo ""
fi
"""

    def _resolve_file_options(self, file_path: str) -> str:
        safe_path = q(file_path)
        return f"""# -- Resolution options for specific file --
RESOLVE_FILE={safe_path}
echo "Resolution options for: $RESOLVE_FILE"
echo ""
if [ ! -f "$RESOLVE_FILE" ]; then
  echo "  [!!] File not found: $RESOLVE_FILE"
else
  echo "  Option A - Keep YOUR changes:"
  echo "    git checkout --ours $RESOLVE_FILE"
  echo "    git add $RESOLVE_FILE"
  echo ""
  echo "  Option B - Keep THEIR changes:"
  echo "    git checkout --theirs $RESOLVE_FILE"
  echo "    git add $RESOLVE_FILE"
  echo ""
  echo "  Option C - Manual edit:"
  echo "    1. Open $RESOLVE_FILE in your editor"
  echo "    2. Find and resolve <<<<<<< markers"
  echo "    3. git add $RESOLVE_FILE"
fi
echo ""
"""

    def _resolve_general_options(self) -> str:
        return r"""# -- General resolution options --
echo "Resolution commands:"
echo ""
echo "  For each file, choose one:"
echo "    Keep yours:  git checkout --ours <file> && git add <file>"
echo "    Keep theirs: git checkout --theirs <file> && git add <file>"
echo "    Manual edit: edit <file>, remove <<<<<<< markers, git add <file>"
echo ""

if [ "$IN_MERGE" -eq 1 ]; then
  echo "After resolving all files:"
  echo "  git commit                  # Complete the merge"
  echo ""
  echo "To abort:"
  echo "  git merge --abort           # Cancel and go back"
elif [ "$IN_REBASE" -eq 1 ]; then
  echo "After resolving all files:"
  echo "  git rebase --continue       # Continue the rebase"
  echo ""
  echo "To abort:"
  echo "  git rebase --abort          # Cancel and go back"
else
  echo "After resolving all files:"
  echo "  git add . && git commit     # Commit the resolution"
fi
echo ""
"""

    def _resolve_footer(self) -> str:
        return r"""echo "========================================"
# ---- conflict resolution guide end ----
"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Git-ops conflict detector")
    parser.add_argument(
        "--target", metavar="BRANCH", help="Target branch to detect conflicts against"
    )
    parser.add_argument(
        "--resolve",
        action="store_true",
        help="Show resolution guidance for current conflicts",
    )
    parser.add_argument(
        "--file",
        metavar="PATH",
        help="Specific file for resolution guidance (use with --resolve)",
    )
    parser.add_argument("--config", metavar="FILE", help="Path to configuration file")

    args = parser.parse_args()

    # Load config if available
    config = {}
    try:
        from config_manager import ConfigManager

        cm = ConfigManager(args.config)
        config = cm.get("conflict_detection", {}) or {}
    except ImportError:
        pass

    detector = ConflictDetector(config)

    if args.resolve:
        script = detector.generate_resolve_script(args.file)
    elif args.target:
        script = detector.generate_detect_script(args.target)
    else:
        # Default: detect against default target branch
        script = detector.generate_detect_script()

    print("```bash")
    print(script.rstrip())
    print("```")


if __name__ == "__main__":
    main()
