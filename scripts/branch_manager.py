#!/usr/bin/env python3
"""
branch_manager.py

Generates bash script fragments for branch management & cleanup:
- Full branch analysis report (active/stale/merged)
- Interactive cleanup with suggestions
- Batch delete merged branches

Usage:
  Integrated: python3 git_ops.py --from-text "analyze branches"
  Standalone: python3 branch_manager.py analyze
"""

from __future__ import annotations

from typing import Dict, Optional


class BranchManager:
    """Generates bash script fragments for branch analysis and cleanup."""

    DEFAULT_CONFIG: Dict = {
        'default_base_branch': 'main',
        'stale_days': 30,
        'merged_grace_days': 7,
        'show_remote_branches': True,
        'protected_branches': ['main', 'master', 'develop', 'staging'],
        'fetch_before_analyze': True,
    }

    def __init__(self, config: Optional[dict] = None):
        self.config: Dict = {**self.DEFAULT_CONFIG}
        if config:
            self.config.update(config)

    def generate_analyze_script(self) -> str:
        """Generate bash that performs full branch analysis."""
        base = self.config.get('default_base_branch', 'main')
        stale_days = int(self.config.get('stale_days', 30))
        fetch = self.config.get('fetch_before_analyze', True)
        show_remote = self.config.get('show_remote_branches', True)
        protected = self.config.get('protected_branches',
                                    ['main', 'master', 'develop', 'staging'])

        parts = [self._header("BRANCH ANALYSIS")]

        # Protected branches as bash array
        protected_bash = ' '.join(f'"{b}"' for b in protected)
        parts.append(f'PROTECTED_BRANCHES=({protected_bash})\n')
        parts.append(f'BASE_BRANCH="{base}"\n')
        parts.append(f'STALE_DAYS={stale_days}\n')

        if fetch:
            parts.append(self._fetch_block())

        parts.append(self._gather_branches())
        parts.append(self._classify_branches())

        # Summary
        parts.append(r"""echo "--- Summary ---"
echo ""
echo "  Active branches:  $ACTIVE_COUNT"
echo "  Stale branches:   $STALE_COUNT  (no commits in ${STALE_DAYS}+ days)"
echo "  Merged branches:  $MERGED_COUNT (fully merged into $BASE_BRANCH)"
echo "  Total:            $TOTAL_COUNT"
echo ""
""")

        # Active branches detail
        parts.append(r"""if [ "$ACTIVE_COUNT" -gt 0 ]; then
  echo "--- Active Branches ---"
  echo ""
  printf '%b' "$ACTIVE_LINES"
  echo ""
fi
""")

        # Stale branches detail
        parts.append(r"""if [ "$STALE_COUNT" -gt 0 ]; then
  echo "--- Stale Branches ---"
  echo ""
  printf '%b' "$STALE_LINES"
  echo ""
fi
""")

        # Merged branches detail
        parts.append(r"""if [ "$MERGED_COUNT" -gt 0 ]; then
  echo "--- Merged Branches ---"
  echo ""
  printf '%b' "$MERGED_LINES"
  echo ""
fi
""")

        if show_remote:
            parts.append(self._remote_branches_block())

        # Suggestions
        parts.append(r"""echo "--- Suggestions ---"
echo ""
if [ "$MERGED_COUNT" -gt 0 ]; then
  echo "  Delete merged branches:"
  echo "    gops \"delete merged branches\""
  echo "    gops branch delete-merged"
  echo ""
fi
if [ "$STALE_COUNT" -gt 0 ]; then
  echo "  Clean up stale branches:"
  echo "    gops \"cleanup branches\""
  echo "    gops branch cleanup"
  echo ""
fi
if [ "$MERGED_COUNT" -eq 0 ] && [ "$STALE_COUNT" -eq 0 ]; then
  echo "  All branches look healthy!"
  echo ""
fi
""")
        parts.append(self._footer())
        return '\n'.join(parts)

    def generate_cleanup_script(self) -> str:
        """Generate bash that interactively cleans up branches."""
        base = self.config.get('default_base_branch', 'main')
        stale_days = int(self.config.get('stale_days', 30))
        grace_days = int(self.config.get('merged_grace_days', 7))
        fetch = self.config.get('fetch_before_analyze', True)
        protected = self.config.get('protected_branches',
                                    ['main', 'master', 'develop', 'staging'])

        parts = [self._header("BRANCH CLEANUP")]

        protected_bash = ' '.join(f'"{b}"' for b in protected)
        parts.append(f'PROTECTED_BRANCHES=({protected_bash})\n')
        parts.append(f'BASE_BRANCH="{base}"\n')
        parts.append(f'STALE_DAYS={stale_days}\n')
        parts.append(f'GRACE_DAYS={grace_days}\n')

        if fetch:
            parts.append(self._fetch_block())

        parts.append(self._gather_branches())
        parts.append(self._cleanup_candidates())

        # Interactive per-branch deletion
        parts.append(r"""if [ ${#CANDIDATES[@]} -eq 0 ]; then
  echo "  No cleanup candidates found. All branches look good!"
""")
        parts.append(self._footer_block())
        parts.append(r"""fi

echo "Found ${#CANDIDATES[@]} cleanup candidate(s):"
echo ""

DELETED=0
SKIPPED=0

for i in "${!CANDIDATES[@]}"; do
  CAND="${CANDIDATES[$i]}"
  REASON="${REASONS[$i]}"
  CAND_BRANCH=$(echo "$CAND" | xargs)

  echo "  [$((i+1))/${#CANDIDATES[@]}]  $CAND_BRANCH"
  echo "  Reason: $REASON"
  echo ""
  read -r -p "  Delete this branch? [y/n/q] " ANSWER
  case "$ANSWER" in
    y|Y)
      if git branch -d "$CAND_BRANCH" 2>/dev/null; then
        echo "  [ok] Deleted: $CAND_BRANCH"
        DELETED=$((DELETED + 1))
      else
        echo "  [!!] Cannot delete with -d (not fully merged). Use -D to force."
        read -r -p "  Force delete? [y/n] " FORCE_ANS
        if [ "$FORCE_ANS" = "y" ] || [ "$FORCE_ANS" = "Y" ]; then
          git branch -D "$CAND_BRANCH" 2>/dev/null && echo "  [ok] Force deleted: $CAND_BRANCH" || echo "  [!!] Failed to delete: $CAND_BRANCH"
          DELETED=$((DELETED + 1))
        else
          echo "  Skipped."
          SKIPPED=$((SKIPPED + 1))
        fi
      fi
      # Prune remote tracking ref if it exists
      if git rev-parse --verify "refs/remotes/$REMOTE/$CAND_BRANCH" >/dev/null 2>&1; then
        echo "  Remote tracking branch exists: $REMOTE/$CAND_BRANCH"
        read -r -p "  Also delete remote branch? [y/n] " REMOTE_ANS
        if [ "$REMOTE_ANS" = "y" ] || [ "$REMOTE_ANS" = "Y" ]; then
          git push "$REMOTE" --delete "$CAND_BRANCH" 2>/dev/null && echo "  [ok] Deleted remote: $REMOTE/$CAND_BRANCH" || echo "  [!!] Failed to delete remote branch"
        fi
      fi
      ;;
    q|Q)
      echo "  Aborted."
      break
      ;;
    *)
      echo "  Skipped."
      SKIPPED=$((SKIPPED + 1))
      ;;
  esac
  echo ""
done

echo "--- Cleanup Complete ---"
echo ""
echo "  Deleted: $DELETED"
echo "  Skipped: $SKIPPED"
""")
        parts.append(self._footer())
        return '\n'.join(parts)

    def generate_delete_merged_script(self) -> str:
        """Generate bash that deletes all merged branches."""
        base = self.config.get('default_base_branch', 'main')
        grace_days = int(self.config.get('merged_grace_days', 7))
        fetch = self.config.get('fetch_before_analyze', True)
        protected = self.config.get('protected_branches',
                                    ['main', 'master', 'develop', 'staging'])

        parts = [self._header("DELETE MERGED BRANCHES")]

        protected_bash = ' '.join(f'"{b}"' for b in protected)
        parts.append(f'PROTECTED_BRANCHES=({protected_bash})\n')
        parts.append(f'BASE_BRANCH="{base}"\n')
        parts.append(f'GRACE_DAYS={grace_days}\n')

        if fetch:
            parts.append(self._fetch_block())

        # Helper function
        parts.append(self._is_protected_func())

        parts.append(r"""# Collect merged branches
MERGED_BRANCHES=()
NOW_EPOCH=$(date +%s)

for BRANCH in $(git branch --merged "$BASE_BRANCH" 2>/dev/null | sed 's/^[* ]*//' | xargs); do
  # Skip current branch
  if [ "$BRANCH" = "$BR" ]; then
    continue
  fi
  # Skip protected
  if is_protected "$BRANCH"; then
    continue
  fi
  # Check grace period
  LAST_COMMIT_EPOCH=$(git log -1 --format='%ct' "$BRANCH" 2>/dev/null || echo "0")
  if [ "$LAST_COMMIT_EPOCH" -gt 0 ]; then
    AGE_DAYS=$(( (NOW_EPOCH - LAST_COMMIT_EPOCH) / 86400 ))
    if [ "$AGE_DAYS" -lt "$GRACE_DAYS" ]; then
      continue
    fi
  fi
  MERGED_BRANCHES+=("$BRANCH")
done

if [ ${#MERGED_BRANCHES[@]} -eq 0 ]; then
  echo "  No merged branches to delete."
  echo "  (Protected branches and branches within ${GRACE_DAYS}-day grace period are excluded.)"
""")
        parts.append(self._footer_block())
        parts.append(r"""fi

echo "The following branches are fully merged into $BASE_BRANCH"
echo "and will be deleted:"
echo ""
for B in "${MERGED_BRANCHES[@]}"; do
  LAST_DATE=$(git log -1 --format='%ci' "$B" 2>/dev/null | cut -d' ' -f1 || echo "unknown")
  echo "  - $B  (last commit: $LAST_DATE)"
done
echo ""
echo "Protected branches (never deleted): ${PROTECTED_BRANCHES[*]}"
echo ""

confirm_yes "About to delete ${#MERGED_BRANCHES[@]} merged branch(es)" || { echo "Canceled"; exit 0; }

echo ""
DELETED=0
FAILED=0
for B in "${MERGED_BRANCHES[@]}"; do
  if git branch -d "$B" 2>/dev/null; then
    echo "  [ok] Deleted: $B"
    DELETED=$((DELETED + 1))
  else
    echo "  [!!] Failed to delete: $B"
    FAILED=$((FAILED + 1))
  fi
done

echo ""
echo "  Deleted: $DELETED"
if [ "$FAILED" -gt 0 ]; then
  echo "  Failed:  $FAILED"
fi
""")

        # Prune remote tracking refs
        parts.append(r"""echo ""
echo "Pruning stale remote tracking references..."
git remote prune "$REMOTE" 2>/dev/null && echo "  [ok] Remote refs pruned" || echo "  [!] Could not prune remote refs"
""")

        parts.append(self._footer())
        return '\n'.join(parts)

    # ---- helpers ----

    def _header(self, title: str) -> str:
        return f"""# ---- {title.lower()} begin ----
echo ""
echo "========================================"
echo "  {title}"
echo "========================================"
echo ""
"""

    def _footer(self) -> str:
        return r"""echo ""
echo "========================================"
"""

    def _footer_block(self) -> str:
        """Early-exit footer for error/empty branches."""
        return r"""  echo ""
  echo "========================================"
  exit 0"""

    def _fetch_block(self) -> str:
        return r"""echo "Fetching remote state..."
git fetch "$REMOTE" --prune 2>/dev/null && echo "  [ok] Fetched and pruned" || echo "  [!] Fetch failed (continuing with local data)"
echo ""
"""

    def _is_protected_func(self) -> str:
        return r"""is_protected() {
  local branch="$1"
  for p in "${PROTECTED_BRANCHES[@]}"; do
    if [ "$branch" = "$p" ]; then
      return 0
    fi
  done
  return 1
}

"""

    def _gather_branches(self) -> str:
        """Generate bash that collects branch info into variables."""
        parts = []
        parts.append(self._is_protected_func())
        parts.append(r"""# Gather all local branches with metadata
NOW_EPOCH=$(date +%s)

ACTIVE_LINES=""
STALE_LINES=""
MERGED_LINES=""
ACTIVE_COUNT=0
STALE_COUNT=0
MERGED_COUNT=0
TOTAL_COUNT=0

while IFS='|' read -r REFNAME COMMIT_EPOCH COMMIT_DATE COMMIT_MSG; do
  BRANCH="${REFNAME#refs/heads/}"
  TOTAL_COUNT=$((TOTAL_COUNT + 1))

  # Skip protected (just label them)
  IS_PROT=0
  if is_protected "$BRANCH"; then
    IS_PROT=1
  fi

  # Calculate age
  AGE_DAYS=0
  if [ "$COMMIT_EPOCH" -gt 0 ] 2>/dev/null; then
    AGE_DAYS=$(( (NOW_EPOCH - COMMIT_EPOCH) / 86400 ))
  fi

  # Check if merged into base
  IS_MERGED=0
  if git merge-base --is-ancestor "$BRANCH" "$BASE_BRANCH" 2>/dev/null; then
    IS_MERGED=1
  fi

  # Current branch marker
  MARKER="  "
  if [ "$BRANCH" = "$BR" ]; then
    MARKER="* "
  fi

  # Ahead/behind
  AHEAD=0
  BEHIND=0
  if git rev-parse --verify "$BASE_BRANCH" >/dev/null 2>&1; then
    COUNTS=$(git rev-list --left-right --count "$BRANCH...$BASE_BRANCH" 2>/dev/null || echo "0	0")
    AHEAD=$(echo "$COUNTS" | cut -f1)
    BEHIND=$(echo "$COUNTS" | cut -f2)
  fi

  # Format line
  if [ "$IS_PROT" -eq 1 ]; then
    AGE_STR=""
    if [ "$AGE_DAYS" -gt 0 ]; then
      AGE_STR="${AGE_DAYS}d ago"
    else
      AGE_STR="today"
    fi
    LINE="${MARKER}${BRANCH}  [protected]  (${AGE_STR})  +${AHEAD}/-${BEHIND}"
    ACTIVE_LINES="${ACTIVE_LINES}${LINE}\n"
    ACTIVE_COUNT=$((ACTIVE_COUNT + 1))
  elif [ "$IS_MERGED" -eq 1 ] && [ "$BRANCH" != "$BR" ]; then
    AGE_STR="${AGE_DAYS}d ago"
    LINE="${MARKER}${BRANCH}  [merged]  (${AGE_STR})  last: ${COMMIT_DATE}"
    MERGED_LINES="${MERGED_LINES}${LINE}\n"
    MERGED_COUNT=$((MERGED_COUNT + 1))
  elif [ "$AGE_DAYS" -ge "$STALE_DAYS" ]; then
    AGE_STR="${AGE_DAYS}d ago"
    LINE="${MARKER}${BRANCH}  [stale]  (${AGE_STR})  +${AHEAD}/-${BEHIND}  last: ${COMMIT_DATE}"
    STALE_LINES="${STALE_LINES}${LINE}\n"
    STALE_COUNT=$((STALE_COUNT + 1))
  else
    AGE_STR=""
    if [ "$AGE_DAYS" -gt 0 ]; then
      AGE_STR="${AGE_DAYS}d ago"
    else
      AGE_STR="today"
    fi
    LINE="${MARKER}${BRANCH}  (${AGE_STR})  +${AHEAD}/-${BEHIND}"
    ACTIVE_LINES="${ACTIVE_LINES}${LINE}\n"
    ACTIVE_COUNT=$((ACTIVE_COUNT + 1))
  fi

done < <(git for-each-ref --sort=-committerdate refs/heads/ \
  --format='%(refname)|%(committerdate:unix)|%(committerdate:short)|%(subject)' 2>/dev/null)

""")
        return '\n'.join(parts)

    def _classify_branches(self) -> str:
        """Placeholder — classification is done inline in _gather_branches."""
        return ""

    def _cleanup_candidates(self) -> str:
        """Generate bash that builds arrays of cleanup candidates."""
        parts = []
        parts.append(self._is_protected_func())
        parts.append(r"""# Build cleanup candidate list
NOW_EPOCH=$(date +%s)
CANDIDATES=()
REASONS=()

while IFS='|' read -r REFNAME COMMIT_EPOCH COMMIT_DATE COMMIT_MSG; do
  BRANCH="${REFNAME#refs/heads/}"

  # Skip current branch
  if [ "$BRANCH" = "$BR" ]; then
    continue
  fi

  # Skip protected
  if is_protected "$BRANCH"; then
    continue
  fi

  # Calculate age
  AGE_DAYS=0
  if [ "$COMMIT_EPOCH" -gt 0 ] 2>/dev/null; then
    AGE_DAYS=$(( (NOW_EPOCH - COMMIT_EPOCH) / 86400 ))
  fi

  # Check if merged
  IS_MERGED=0
  if git merge-base --is-ancestor "$BRANCH" "$BASE_BRANCH" 2>/dev/null; then
    IS_MERGED=1
  fi

  # Merged + past grace period
  if [ "$IS_MERGED" -eq 1 ] && [ "$AGE_DAYS" -ge "$GRACE_DAYS" ]; then
    CANDIDATES+=("$BRANCH")
    REASONS+=("Merged into $BASE_BRANCH, last commit ${AGE_DAYS}d ago")
    continue
  fi

  # Stale (not merged but very old)
  if [ "$AGE_DAYS" -ge "$STALE_DAYS" ]; then
    CANDIDATES+=("$BRANCH")
    REASONS+=("Stale: no commits in ${AGE_DAYS} days (threshold: ${STALE_DAYS}d)")
    continue
  fi

done < <(git for-each-ref --sort=-committerdate refs/heads/ \
  --format='%(refname)|%(committerdate:unix)|%(committerdate:short)|%(subject)' 2>/dev/null)

""")
        return '\n'.join(parts)

    def _remote_branches_block(self) -> str:
        """Generate bash that shows remote-only branches."""
        return r"""# Remote-only branches (no local tracking)
echo "--- Remote-Only Branches ---"
echo ""
REMOTE_ONLY=0
for REMOTE_REF in $(git for-each-ref --sort=-committerdate refs/remotes/$REMOTE/ \
  --format='%(refname:short)' 2>/dev/null); do
  # Strip remote prefix
  REMOTE_BRANCH="${REMOTE_REF#$REMOTE/}"
  # Skip HEAD
  if [ "$REMOTE_BRANCH" = "HEAD" ]; then
    continue
  fi
  # Skip if local branch exists
  if git rev-parse --verify "refs/heads/$REMOTE_BRANCH" >/dev/null 2>&1; then
    continue
  fi
  REMOTE_DATE=$(git log -1 --format='%ci' "$REMOTE_REF" 2>/dev/null | cut -d' ' -f1 || echo "unknown")
  echo "  $REMOTE_BRANCH  (remote only, last: $REMOTE_DATE)"
  REMOTE_ONLY=$((REMOTE_ONLY + 1))
done
if [ "$REMOTE_ONLY" -eq 0 ]; then
  echo "  (none)"
fi
echo ""
"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Git-ops branch manager')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('analyze', help='Analyze all branches')
    sub.add_parser('cleanup', help='Interactive branch cleanup')
    sub.add_parser('delete-merged', help='Delete all merged branches')

    parser.add_argument('--config', metavar='FILE', help='Path to configuration file')

    args = parser.parse_args()

    # Load config if available
    config = {}
    try:
        from config_manager import ConfigManager
        cm = ConfigManager(args.config)
        config = cm.get('branch_management', {}) or {}
    except ImportError:
        pass

    manager = BranchManager(config)

    if args.command == 'analyze':
        script = manager.generate_analyze_script()
    elif args.command == 'cleanup':
        script = manager.generate_cleanup_script()
    elif args.command == 'delete-merged':
        script = manager.generate_delete_merged_script()
    else:
        parser.print_help()
        return

    print("```bash")
    print(script.rstrip())
    print("```")


if __name__ == '__main__':
    main()
