#!/usr/bin/env python3
"""
stash_manager.py

Generates bash script fragments for advanced stash management:
- Detailed stash listing with age, branch, file stats
- Stash backup to patch files
- Safe stash apply with conflict pre-detection

Usage:
  Integrated: python3 git_ops.py --from-text "stash list detailed"
  Standalone: python3 stash_manager.py list-detailed
"""

from __future__ import annotations

from typing import Dict, Optional


class StashManager:
    """Generates bash script fragments for advanced stash operations."""

    DEFAULT_CONFIG: Dict = {
        'backup_dir': '~/.git-ops/backups',
        'age_warning_hours': 24,
        'age_danger_hours': 168,  # 7 days
        'show_file_stats': True,
        'show_age': True,
    }

    def __init__(self, config: Optional[dict] = None):
        self.config: Dict = {**self.DEFAULT_CONFIG}
        if config:
            self.config.update(config)

    def generate_list_detailed_script(self) -> str:
        """Generate bash that lists all stashes with detailed info."""
        show_stats = self.config.get('show_file_stats', True)
        show_age = self.config.get('show_age', True)
        warn_h = int(self.config.get('age_warning_hours', 24))
        danger_h = int(self.config.get('age_danger_hours', 168))

        parts = [self._header("STASH LIST (detailed)")]

        parts.append(r"""STASH_LIST=$(git stash list --format="%gd|%s|%ci" 2>/dev/null || true)
if [ -z "$STASH_LIST" ]; then
  echo "  No stashes found."
""")
        parts.append(self._footer_block())
        parts.append(r"""fi

STASH_TOTAL=$(echo "$STASH_LIST" | wc -l | tr -d ' ')
echo "Total stashes: $STASH_TOTAL"
echo ""

INDEX=0
while IFS='|' read -r REF SUBJECT DATESTR; do
  echo "────────────────────────────────────────"
  echo "  [$REF]  $SUBJECT"
""")

        if show_age:
            parts.append(f"""  # Age calculation
  STASH_EPOCH=$(date -d "$DATESTR" +%s 2>/dev/null || echo "0")
  NOW_EPOCH=$(date +%s)
  if [ "$STASH_EPOCH" -gt 0 ]; then
    AGE_SEC=$((NOW_EPOCH - STASH_EPOCH))
    AGE_HOURS=$((AGE_SEC / 3600))
    AGE_DAYS=$((AGE_HOURS / 24))
    if [ "$AGE_DAYS" -gt 0 ]; then
      AGE_STR="${{AGE_DAYS}}d ${{((AGE_HOURS % 24))}}h ago"
    else
      AGE_STR="${{AGE_HOURS}}h ago"
    fi
    if [ "$AGE_HOURS" -ge {danger_h} ]; then
      echo "  Age: $AGE_STR  [!!] Very old stash"
    elif [ "$AGE_HOURS" -ge {warn_h} ]; then
      echo "  Age: $AGE_STR  [!] Getting old"
    else
      echo "  Age: $AGE_STR"
    fi
  fi
""")

        parts.append(r"""  # Branch at time of stash
  STASH_BRANCH=$(echo "$SUBJECT" | sed -n 's/^WIP on \(.*\):.*$/\1/p; s/^On \(.*\):.*$/\1/p')
  if [ -n "$STASH_BRANCH" ]; then
    echo "  Branch: $STASH_BRANCH"
  fi
""")

        if show_stats:
            parts.append(r"""  # File stats
  STAT_OUTPUT=$(git stash show "$REF" --stat 2>/dev/null || echo "  (cannot show stats)")
  echo "  Files:"
  echo "$STAT_OUTPUT" | sed 's/^/    /'
""")

        parts.append(r"""  echo ""
  INDEX=$((INDEX + 1))
done <<< "$STASH_LIST"

echo "────────────────────────────────────────"
echo ""
echo "Commands:"
echo "  gops \"stash show 0\"         # View stash diff"
echo "  gops \"stash apply safe 0\"   # Apply with conflict check"
echo "  gops \"stash backup 0\"       # Export to .patch file"
echo "  gops \"stash pop 0\"          # Apply and remove"
echo "  gops \"stash drop 0\"         # Delete stash"
""")
        parts.append(self._footer())
        return '\n'.join(parts)

    def generate_backup_script(self, stash_index: int = 0) -> str:
        """Generate bash that exports a stash to a .patch file."""
        backup_dir = self.config.get('backup_dir', '~/.git-ops/backups')

        parts = [self._header("STASH BACKUP")]

        parts.append(f"""STASH_REF="stash@{{{stash_index}}}"

# Verify stash exists
if ! git stash show "$STASH_REF" >/dev/null 2>&1; then
  echo "  [!!] Stash $STASH_REF does not exist"
  echo ""
  echo "Available stashes:"
  git stash list 2>/dev/null || echo "  (none)"
""")
        parts.append(self._footer_block())
        parts.append(r"""fi

# Gather stash metadata
STASH_SUBJECT=$(git stash list --format="%s" 2>/dev/null | sed -n "$((""" + str(stash_index + 1) + r"""))p")
REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "repo")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Sanitize subject for filename
SAFE_DESC=$(echo "$STASH_SUBJECT" | tr -c '[:alnum:]._-' '_' | head -c 40)
""")

        parts.append(f"""BACKUP_DIR="{backup_dir}"
BACKUP_DIR="${{BACKUP_DIR/#\\~/~}}"
eval BACKUP_DIR="$BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

PATCH_FILE="${{BACKUP_DIR}}/${{REPO_NAME}}_stash{stash_index}_${{TIMESTAMP}}_${{SAFE_DESC}}.patch"
""")

        parts.append(r"""echo "Exporting stash to patch file..."
echo ""

# Write patch header
{
  echo "# Git-Ops Stash Backup"
  echo "# Repository: $REPO_NAME"
  echo "# Stash: $STASH_REF"
  echo "# Description: $STASH_SUBJECT"
  echo "# Exported: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "# Branch at stash time: $(echo "$STASH_SUBJECT" | sed -n 's/^WIP on \(.*\):.*$/\1/p; s/^On \(.*\):.*$/\1/p')"
  echo "#"
  echo ""
} > "$PATCH_FILE"

# Write diff content
git stash show -p "$STASH_REF" >> "$PATCH_FILE" 2>/dev/null

PATCH_SIZE=$(wc -c < "$PATCH_FILE" | tr -d ' ')
FILE_COUNT=$(git stash show "$STASH_REF" --stat 2>/dev/null | tail -1 | grep -oE '[0-9]+' | head -1 || echo "?")

echo "  [ok] Backup saved: $PATCH_FILE"
echo "  Size: $PATCH_SIZE bytes"
echo "  Files: $FILE_COUNT"
echo ""
echo "To restore from backup:"
echo "  git apply \"$PATCH_FILE\""
echo "  git apply --3way \"$PATCH_FILE\"  # if conflicts"
""")
        parts.append(self._footer())
        return '\n'.join(parts)

    def generate_apply_safe_script(self, stash_index: int = 0) -> str:
        """Generate bash that applies a stash with conflict pre-detection."""
        parts = [self._header("STASH APPLY (safe)")]

        parts.append(f"""STASH_REF="stash@{{{stash_index}}}"

# Verify stash exists
if ! git stash show "$STASH_REF" >/dev/null 2>&1; then
  echo "  [!!] Stash $STASH_REF does not exist"
  echo ""
  echo "Available stashes:"
  git stash list 2>/dev/null || echo "  (none)"
""")
        parts.append(self._footer_block())
        parts.append(r"""fi
""")

        parts.append(r"""STASH_SUBJECT=$(git stash list --format="%s" 2>/dev/null | sed -n "$((""" + str(stash_index + 1) + r"""))p")
echo "Stash: $STASH_REF"
echo "Description: $STASH_SUBJECT"
echo ""

# Step 1: Check for dirty worktree overlap
echo "--- Pre-apply Conflict Check ---"
echo ""

STASH_FILES=$(git stash show "$STASH_REF" --name-only 2>/dev/null || true)
DIRTY_FILES=$(git diff --name-only 2>/dev/null || true)
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)

OVERLAP_DIRTY=""
OVERLAP_STAGED=""

if [ -n "$STASH_FILES" ] && [ -n "$DIRTY_FILES" ]; then
  OVERLAP_DIRTY=$(comm -12 <(echo "$STASH_FILES" | sort) <(echo "$DIRTY_FILES" | sort) 2>/dev/null || true)
fi
if [ -n "$STASH_FILES" ] && [ -n "$STAGED_FILES" ]; then
  OVERLAP_STAGED=$(comm -12 <(echo "$STASH_FILES" | sort) <(echo "$STAGED_FILES" | sort) 2>/dev/null || true)
fi

HAS_RISK=0

if [ -n "$OVERLAP_STAGED" ]; then
  echo "  [!!] Stash touches files that are currently STAGED:"
  echo "$OVERLAP_STAGED" | sed 's/^/       /'
  echo ""
  HAS_RISK=1
fi

if [ -n "$OVERLAP_DIRTY" ]; then
  echo "  [!] Stash touches files with UNCOMMITTED changes:"
  echo "$OVERLAP_DIRTY" | sed 's/^/       /'
  echo ""
  HAS_RISK=1
fi

if [ "$HAS_RISK" -eq 0 ]; then
  echo "  [ok] No file overlap detected — safe to apply"
  echo ""
fi

# Step 2: Show stash summary
echo "--- Stash Contents ---"
git stash show --stat "$STASH_REF" 2>/dev/null || true
echo ""

# Step 3: Apply
if [ "$HAS_RISK" -eq 1 ]; then
  echo "[!] Potential conflicts detected."
  echo "Options:"
  echo "  1) Apply anyway (may require manual resolution)"
  echo "  2) Cancel"
  echo ""
  read -r -p "Choose [1/2]: " CHOICE
  case "$CHOICE" in
    1) ;;
    *) echo "Canceled."; exit 0 ;;
  esac
fi

echo ""
echo "Applying $STASH_REF..."
""")

        parts.append(f"""if git stash apply "$STASH_REF" 2>/dev/null; then
  echo ""
  echo "  [ok] Stash applied successfully"
  echo ""
  echo "The stash is still saved. To remove it:"
  echo "  gops \\"stash drop {stash_index}\\""
else
  echo ""
  echo "  [!!] Apply failed — conflicts detected"
  echo ""
  echo "Resolution options:"
  echo "  git checkout --ours <file>    # Keep your version"
  echo "  git checkout --theirs <file>  # Keep stash version"
  echo "  git add <file>                # Mark resolved"
  echo ""
  echo "Or abort:"
  echo "  git reset --merge"
fi
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
        """Early-exit footer for error branches."""
        return r"""  echo ""
  echo "========================================"
  exit 1"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Git-ops advanced stash manager')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('list-detailed', help='Detailed stash listing')

    p_backup = sub.add_parser('backup', help='Backup stash to patch file')
    p_backup.add_argument('index', type=int, nargs='?', default=0, help='Stash index')

    p_apply = sub.add_parser('apply-safe', help='Apply stash with conflict check')
    p_apply.add_argument('index', type=int, nargs='?', default=0, help='Stash index')

    parser.add_argument('--config', metavar='FILE', help='Path to configuration file')

    args = parser.parse_args()

    # Load config if available
    config = {}
    try:
        from config_manager import ConfigManager
        cm = ConfigManager(args.config)
        config = cm.get('stash_management', {}) or {}
    except ImportError:
        pass

    manager = StashManager(config)

    if args.command == 'list-detailed':
        script = manager.generate_list_detailed_script()
    elif args.command == 'backup':
        script = manager.generate_backup_script(args.index)
    elif args.command == 'apply-safe':
        script = manager.generate_apply_safe_script(args.index)
    else:
        parser.print_help()
        return

    print("```bash")
    print(script.rstrip())
    print("```")


if __name__ == '__main__':
    main()
