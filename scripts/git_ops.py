#!/usr/bin/env python3
"""
git_ops.py

Full semantic Git command generator that prints a single paste-ready bash script.
- Uses a subcommand architecture for robust, direct CLI invocation.
- Translates natural language to subcommands as a convenience layer.
- Designed for console usage, with SSH password prompting allowed by default.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import sys
from dataclasses import dataclass, field
from typing import List, Optional


def q(s: str) -> str:
    """Quote a string for safe use in a shell command."""
    return shlex.quote(s)


@dataclass
class Plan:
    # General
    op: str
    sync_mode: str = "rebase"      # rebase|merge|none
    push_mode: str = "nopush"      # push|nopush|lease
    force: bool = False

    # Commit
    message: Optional[str] = None
    stage_mode: str = "all"        # all|keep|patch|interactive
    amend: bool = False
    allow_empty: bool = False
    commit_log: bool = True           # Auto-generate body with file list + diff stat
    root_cause: Optional[str] = None  # Root cause for fix/bug commits
    commit_config: Optional[dict] = None  # Config from YAML commit section

    # Log
    log_path: Optional[str] = None
    log_search: Optional[str] = None
    log_search_is_author: bool = False # New field to distinguish author search
    log_max_count: int = 20
    log_graph: bool = False  # Show commit graph
    log_all_branches: bool = False  # Show all branches

    # Show / Diff
    show_target: Optional[str] = None
    diff_targets: List[str] = field(default_factory=list)
    diff_staged: bool = False

    # Revert / Cherry-pick
    commits: List[str] = field(default_factory=list)
    commit_range: Optional[str] = None
    no_commit: bool = False

    # Branch
    branch_name: Optional[str] = None
    branch_op: Optional[str] = None # create, delete, checkout, analyze, cleanup, delete_merged
    branch_remote: bool = False
    branch_local: bool = False
    branch_config: Optional[dict] = None

    # Stash
    stash_op: Optional[str] = None # save|list|apply|pop|drop|show|clear|list_detailed|backup|apply_safe
    stash_message: Optional[str] = None
    stash_index: int = 0
    stash_include_untracked: bool = False
    stash_keep_index: bool = False
    stash_config: Optional[dict] = None

    # Grep
    grep_pattern: Optional[str] = None
    grep_file_pattern: Optional[str] = None
    grep_ignore_case: bool = False
    grep_line_number: bool = True

    # Reset
    reset_mode: Optional[str] = None # soft|mixed|hard
    reset_target: str = "HEAD"
    reset_paths: List[str] = field(default_factory=list)

    # Checkout/Switch
    checkout_target: Optional[str] = None
    checkout_create: bool = False
    checkout_force: bool = False

    # Restore
    restore_paths: List[str] = field(default_factory=list)
    restore_staged: bool = False
    restore_source: Optional[str] = None
    restore_worktree: bool = True

    # Merge
    merge_source: Optional[str] = None
    merge_no_ff: bool = False
    merge_squash: bool = False

    # Blame
    blame_path: Optional[str] = None
    blame_line_start: Optional[int] = None
    blame_line_end: Optional[int] = None

    # Reflog
    reflog_max_count: int = 20

    # Tag
    tag_name: Optional[str] = None
    tag_op: Optional[str] = None # create|list|delete|push
    tag_message: Optional[str] = None
    tag_annotated: bool = False

    # Clean
    clean_dry_run: bool = True
    clean_force: bool = False
    clean_directories: bool = False
    clean_ignored: bool = False

    # Rebase Interactive
    rebase_target: Optional[str] = None
    rebase_interactive: bool = False
    rebase_count: Optional[int] = None

    # Bisect
    bisect_op: Optional[str] = None # start|good|bad|reset|skip
    bisect_commit: Optional[str] = None

    # Preflight
    preflight_config: Optional[dict] = None

    # Conflict detection
    conflict_config: Optional[dict] = None
    conflict_target: Optional[str] = None
    conflict_file: Optional[str] = None

    # Decision engine
    decision_config: Optional[dict] = None
    decision_goal: Optional[str] = None

    # Team rules validation
    team_rules_config: Optional[dict] = None
    team_rules_op: Optional[str] = None  # commit|branch|quality|all
    validate_message: Optional[str] = None

    # Workflow templates
    workflow_config: Optional[dict] = None
    workflow_name: Optional[str] = None
    workflow_op: Optional[str] = None    # run|list
    workflow_params: Optional[dict] = None


def bash_prelude() -> str:
    # Always allow password prompts.
    return r"""set -euo pipefail
export GIT_TERMINAL_PROMPT=1

# Disable ssh-askpass, allow terminal password input
unset SSH_ASKPASS
unset SSH_ASKPASS_REQUIRE
export GIT_SSH_COMMAND='ssh -o ControlMaster=no'

# ---- error handling ----
GIT_OPS_ERROR_LOG="${GIT_OPS_ERROR_LOG:-${HOME}/.git-ops/error_context.log}"
GIT_OPS_OPERATION="${GIT_OPS_OPERATION:-unknown}"

trap 'on_error $? $LINENO' ERR

on_error() {
  local exit_code=$1
  local line_no=$2
  
  echo ""
  echo "❌ [git-ops] Operation failed at line $line_no (exit code: $exit_code)" >&2
  echo "[git-ops] Operation: $GIT_OPS_OPERATION" >&2
  
  # Capture git status for diagnostics
  if [ -d ".git" ]; then
    {
      echo "--- Git Status at Error ---"
      git status --short 2>/dev/null || true
      echo "--- Branch Info ---"
      git rev-parse --abbrev-ref HEAD 2>/dev/null || true
    } >> "$GIT_OPS_ERROR_LOG" 2>&1 || true
  fi
  
  exit $exit_code
}

# ---- preflight ----
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Not in a git repo"; exit 1; }
BR="$(git rev-parse --abbrev-ref HEAD)"
if [ "$BR" = "HEAD" ]; then
  echo "Detached HEAD. Checkout a branch first or operate on hashes."
  # For many read-only commands, detached HEAD is fine.
  # We exit for state-changing commands later if needed.
fi

REMOTE="${REMOTE:-origin}"
URL="$(git remote get-url "$REMOTE" 2>/dev/null || true)"
echo "[git-ops] branch=$BR remote=$REMOTE"
echo "[git-ops] remote-url=$URL"

CONFIRM_DESTRUCTIVE="${CONFIRM_DESTRUCTIVE:-1}"

pause() {
  read -r -p "$1" _
}

confirm_yes() {
  if [ "${CONFIRM_DESTRUCTIVE}" = "0" ]; then
    return 0
  fi
  echo "$1"
  read -r -p "Type YES to continue: " ans
  [ "$ans" = "YES" ]
}

has_upstream() {
  git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1
}

ensure_upstream_if_exists() {
  # If remote branch exists and upstream isn't set, bind upstream.
  if ! has_upstream; then
    if git show-ref --verify --quiet "refs/remotes/$REMOTE/$BR"; then
      git branch --set-upstream-to="$REMOTE/$BR" "$BR" 2>/dev/null || true
    fi
  fi
}

push_with_upstream_if_needed() {
  if has_upstream;
    then
    git push "$REMOTE" "$BR"
  else
    git push -u "$REMOTE" "$BR"
  fi
}

push_with_lease_upstream_if_needed() {
  if has_upstream;
    then
    git push --force-with-lease "$REMOTE" "$BR"
  else
    git push --force-with-lease -u "$REMOTE" "$BR"
  fi
}
"""


def stage_block(stage_mode: str) -> str:
    if stage_mode == "keep":
        return r"""echo "[git-ops] stage_mode=keep (no git add)"""
    if stage_mode == "patch":
        return r"""echo "[git-ops] stage_mode=patch (git add -p)"
git add -p
pause "Patch staging done. Press ENTER to continue..."""
    if stage_mode == "interactive":
        return r"""echo "[git-ops] stage_mode=interactive (git add -i)"
git add -i
pause "Interactive staging done. Press ENTER to continue..."""
    return r"""echo "[git-ops] stage_mode=all (git add -A)"
git add -A
"""


def ensure_staged_nonempty() -> str:
    return r"""if git diff --cached --quiet;
  then
  echo "No staged changes. Nothing to commit."
  exit 1
fi
"""

def sync_block(sync_mode: str) -> str:
    if sync_mode == "none":
        return r"""echo "[git-ops] sync_mode=none (skip sync)"""
    if sync_mode == "merge":
        return r"""echo "[git-ops] sync_mode=merge"
git fetch "$REMOTE"
git merge "$REMOTE/$BR" || {
  echo "Merge conflict."
  echo "Next steps:"
  echo "  git status"
  echo "  # resolve"
  echo "  git add <files>"
  echo "  git commit"
  echo "Or abort:"
  echo "  git merge --abort"
  exit 1
}"""
    return r"""echo "[git-ops] sync_mode=rebase"
git fetch "$REMOTE"
git rebase "$REMOTE/$BR" || {
  echo "Rebase conflict."
  echo "Next steps:"
  echo "  git status"
  echo "  # resolve"
  echo "  git add <files>"
  echo "  git rebase --continue"
  echo "Or abort:"
  echo "  git rebase --abort"
  exit 1
}"""

def push_block(push_mode: str) -> str:
    if push_mode == "nopush":
        return r"""echo "[git-ops] push_mode=nopush (skip push)"""
    if push_mode == "lease":
        return r"""echo "[git-ops] push_mode=lease (force-with-lease)"
push_with_lease_upstream_if_needed
"""
    return r"""echo "[git-ops] push_mode=push"
push_with_upstream_if_needed
"""

def _inline_preflight_script() -> str:
    """Minimal preflight fallback when preflight_checker.py is not available."""
    return r"""echo "========================================"
echo "  PREFLIGHT CHECK (basic)"
echo "========================================"
echo ""
echo "Branch: $BR"
git status --short
echo ""
STASH_COUNT=$(git stash list 2>/dev/null | wc -l | tr -d ' ')
echo "Stashes: $STASH_COUNT"
echo "========================================"
"""


def _inline_conflict_detect_script() -> str:
    """Minimal conflict detect fallback when conflict_detector.py is not available."""
    return r"""echo "========================================"
echo "  CONFLICT DETECTION (basic)"
echo "========================================"
echo ""
echo "Checking for unmerged files..."
UNMERGED=$(git ls-files --unmerged 2>/dev/null | wc -l | tr -d ' ')
if [ "$UNMERGED" -gt 0 ]; then
  echo "  [!!] $UNMERGED unmerged entries found"
  git ls-files --unmerged 2>/dev/null | cut -f2 | sort -u
else
  echo "  [ok] No current conflicts"
fi
echo "========================================"
"""


def _inline_decision_script() -> str:
    """Minimal decision fallback when decision_engine.py is not available."""
    return r"""echo "========================================"
echo "  WORKFLOW RECOMMENDATION (basic)"
echo "========================================"
echo ""
MODIFIED_COUNT=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
STAGED_COUNT=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
UNTRACKED_COUNT=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')
echo "Branch: $BR"
echo "Modified: $MODIFIED_COUNT  Staged: $STAGED_COUNT  Untracked: $UNTRACKED_COUNT"
echo ""
if [ "$STAGED_COUNT" -gt 0 ]; then
  echo "Suggestion: git commit -m '...'"
elif [ "$MODIFIED_COUNT" -gt 0 ] || [ "$UNTRACKED_COUNT" -gt 0 ]; then
  echo "Suggestion: git add -A && git commit -m '...'"
else
  echo "Working tree is clean. Nothing to do."
fi
echo "========================================"
"""


def _inline_conflict_resolve_script() -> str:
    """Minimal conflict resolve fallback when conflict_detector.py is not available."""
    return r"""echo "========================================"
echo "  CONFLICT RESOLUTION (basic)"
echo "========================================"
echo ""
echo "Conflicting files:"
git diff --name-only --diff-filter=U 2>/dev/null || echo "  No conflicts found"
echo ""
echo "Commands:"
echo "  git checkout --ours <file>    # Keep your changes"
echo "  git checkout --theirs <file>  # Keep their changes"
echo "  git add <file>                # Mark as resolved"
echo "========================================"
"""


def _inline_validate_commit_script() -> str:
    """Minimal commit message validation fallback."""
    return r"""echo "========================================"
echo "  COMMIT MESSAGE VALIDATION (basic)"
echo "========================================"
echo ""
PATTERN='^(feat|fix|docs|style|refactor|perf|test|chore)(\(.+?\))?!?: .+'
if [ -z "${MSG:-}" ]; then
  read -r -p "Enter commit message to validate: " MSG
fi
if [[ "$MSG" =~ $PATTERN ]]; then
  echo "  [ok] Format matches conventional commit style"
else
  echo "  [!!] Format does not match conventional commit style"
  echo "  Examples: feat(auth): add login, fix: typo"
fi
echo "========================================"
"""


def _inline_validate_branch_script() -> str:
    """Minimal branch name validation fallback."""
    return r"""echo "========================================"
echo "  BRANCH NAME VALIDATION (basic)"
echo "========================================"
echo ""
echo "Branch: $BR"
PATTERN='^(feature|fix|hotfix|release|chore)/[a-z0-9._-]+$'
if [ "$BR" = "main" ] || [ "$BR" = "master" ] || [ "$BR" = "develop" ]; then
  echo "  [ok] Branch '$BR' is exempt"
elif [[ "$BR" =~ $PATTERN ]]; then
  echo "  [ok] Branch name matches convention"
else
  echo "  [!!] Branch name does not match convention"
  echo "  Examples: feature/user-auth, fix/memory-leak"
fi
echo "========================================"
"""


def _inline_validate_rules_script() -> str:
    """Minimal full validation fallback."""
    return r"""echo "========================================"
echo "  TEAM RULES VALIDATION (basic)"
echo "========================================"
echo ""
echo "--- Branch Naming ---"
echo "Branch: $BR"
PATTERN='^(feature|fix|hotfix|release|chore)/[a-z0-9._-]+$'
if [ "$BR" = "main" ] || [ "$BR" = "master" ] || [ "$BR" = "develop" ]; then
  echo "  [ok] Branch '$BR' is exempt"
elif [[ "$BR" =~ $PATTERN ]]; then
  echo "  [ok] Branch name matches convention"
else
  echo "  [!!] Branch name does not match convention"
fi
echo ""
echo "--- Commit Format ---"
echo "  Style: conventional commits"
echo "  Pattern: ^(feat|fix|docs|...)(...): ..."
echo "  Max length: 72"
echo "========================================"
"""


def _inline_stash_list_detailed_script() -> str:
    """Minimal stash list detailed fallback when stash_manager.py is not available."""
    return r"""echo "========================================"
echo "  STASH LIST (detailed)"
echo "========================================"
echo ""
STASH_LIST=$(git stash list 2>/dev/null || true)
if [ -z "$STASH_LIST" ]; then
  echo "  No stashes found."
  echo "========================================"
  exit 0
fi
echo "$STASH_LIST"
echo ""
while IFS= read -r LINE; do
  REF=$(echo "$LINE" | cut -d: -f1)
  echo "--- $REF ---"
  git stash show "$REF" --stat 2>/dev/null || echo "  (cannot show stats)"
  echo ""
done <<< "$STASH_LIST"
echo "========================================"
"""


def _inline_stash_backup_script(stash_index: int) -> str:
    """Minimal stash backup fallback when stash_manager.py is not available."""
    return r"""echo "========================================"
echo "  STASH BACKUP"
echo "========================================"
echo ""
STASH_REF="stash@{""" + str(stash_index) + r"""}"
if ! git stash show "$STASH_REF" >/dev/null 2>&1; then
  echo "  [!!] Stash $STASH_REF does not exist"
  git stash list 2>/dev/null || echo "  (none)"
  echo "========================================"
  exit 1
fi
BACKUP_DIR="${HOME}/.git-ops/backups"
mkdir -p "$BACKUP_DIR"
PATCH_FILE="${BACKUP_DIR}/stash""" + str(stash_index) + r"""_$(date +%Y%m%d_%H%M%S).patch"
git stash show -p "$STASH_REF" > "$PATCH_FILE" 2>/dev/null
echo "  [ok] Backup saved: $PATCH_FILE"
echo ""
echo "To restore: git apply \"$PATCH_FILE\""
echo "========================================"
"""


def _inline_stash_apply_safe_script(stash_index: int) -> str:
    """Minimal stash apply safe fallback when stash_manager.py is not available."""
    return r"""echo "========================================"
echo "  STASH APPLY (safe)"
echo "========================================"
echo ""
STASH_REF="stash@{""" + str(stash_index) + r"""}"
if ! git stash show "$STASH_REF" >/dev/null 2>&1; then
  echo "  [!!] Stash $STASH_REF does not exist"
  git stash list 2>/dev/null || echo "  (none)"
  echo "========================================"
  exit 1
fi
echo "Applying $STASH_REF..."
if git stash apply "$STASH_REF" 2>/dev/null; then
  echo "  [ok] Stash applied successfully"
else
  echo "  [!!] Apply failed — conflicts detected"
  echo "  Resolve conflicts then: git add <file>"
fi
echo "========================================"
"""


def _inline_workflow_script(plan) -> str:
    """Fallback when workflow_engine.py is not available."""
    if plan.workflow_op == "list":
        return r"""echo "========================================"
echo "  AVAILABLE WORKFLOWS"
echo "========================================"
echo ""
echo "  create-feature  <name>"
echo "    Create a new feature branch from an up-to-date base"
echo ""
echo "  commit-and-push  <message>"
echo "    Stage, validate, commit, sync, and push in one go"
echo ""
echo "  ready-for-pr"
echo "    Validate code quality and prepare a PR summary"
echo ""
echo "Note: Install workflow_engine.py for full functionality"
echo "========================================"
"""
    # run — engine not available
    name = (plan.workflow_name or "unknown").replace('_', '-')
    return f"""echo "[!!] Workflow engine not available"
echo ""
echo "Cannot run workflow: {name}"
echo "Ensure scripts/workflow_engine.py is installed."
echo ""
echo "Available built-in workflows:"
echo "  create-feature, commit-and-push, ready-for-pr"
echo ""
echo "Usage:"
echo '  gops "workflow list"'
echo '  gops "workflow <name>"'
"""


def _inline_branch_analyze_script() -> str:
    """Minimal branch analysis fallback when branch_manager.py is not available."""
    return r"""echo "========================================"
echo "  BRANCH ANALYSIS (basic)"
echo "========================================"
echo ""
echo "Local branches (sorted by last commit):"
echo ""
git for-each-ref --sort=-committerdate refs/heads/ \
  --format='  %(if)%(HEAD)%(then)* %(else)  %(end)%(refname:short)  (%(committerdate:relative))  %(subject)' 2>/dev/null
echo ""
echo "--- Merged into $BR ---"
git branch --merged "$BR" 2>/dev/null | grep -v '^\*' | sed 's/^/  /' || echo "  (none)"
echo ""
echo "For full analysis, install branch_manager.py"
echo "========================================"
"""


def _inline_branch_cleanup_script() -> str:
    """Minimal branch cleanup fallback when branch_manager.py is not available."""
    return r"""echo "========================================"
echo "  BRANCH CLEANUP (basic)"
echo "========================================"
echo ""
echo "Branches merged into $BR:"
MERGED=$(git branch --merged "$BR" 2>/dev/null | grep -v '^\*' | grep -vE '^\s*(main|master|develop|staging)\s*$' || true)
if [ -z "$MERGED" ]; then
  echo "  No merged branches to clean up."
  echo "========================================"
  exit 0
fi
echo "$MERGED" | sed 's/^/  /'
echo ""
echo "To delete these branches:"
for B in $MERGED; do
  B=$(echo "$B" | xargs)
  echo "  git branch -d $B"
done
echo ""
echo "For interactive cleanup, install branch_manager.py"
echo "========================================"
"""


def _inline_branch_delete_merged_script() -> str:
    """Minimal delete merged fallback when branch_manager.py is not available."""
    return r"""echo "========================================"
echo "  DELETE MERGED BRANCHES (basic)"
echo "========================================"
echo ""
MERGED=$(git branch --merged "$BR" 2>/dev/null | grep -v '^\*' | grep -vE '^\s*(main|master|develop|staging)\s*$' || true)
if [ -z "$MERGED" ]; then
  echo "  No merged branches to delete."
  echo "========================================"
  exit 0
fi
echo "Will delete:"
echo "$MERGED" | sed 's/^/  /'
echo ""
confirm_yes "About to delete merged branches" || { echo "Canceled"; exit 0; }
echo ""
for B in $MERGED; do
  B=$(echo "$B" | xargs)
  git branch -d "$B" 2>/dev/null && echo "  [ok] Deleted: $B" || echo "  [!!] Failed: $B"
done
echo "========================================"
"""


def parse_hashes(text: str) -> List[str]:
    # This also captures HEAD~1, HEAD, etc.
    return re.findall(r"\b([0-9a-fA-F]{6,40}|HEAD(?:~\d+)?)\b", text)

def parse_quoted_string(text: str) -> Optional[str]:
    m = re.search(r'"([^"]*)"|"([^"]*)"', text)
    if m:
        return m.group(1) or m.group(2)
    return None

# The NLP parser.
def parse_operation_from_text(text: str, llm_config: Optional[dict] = None) -> Plan:
    t = text.strip()
    tl = t.lower()

    # More specific intents should come first.

    # NLP for 'workflow' / '工作流' / '流程'
    if re.search(r"\b(workflow|工作流|流程)\b", tl):
        if re.search(r"\b(list|列表|顯示)\b", tl):
            return Plan(op="workflow", workflow_op="list")
        # Extract workflow name and optional inline param
        wf_name = None
        wf_params = {}
        # Match: workflow run <name> or workflow <name>
        name_m = re.search(r"\b(?:workflow|工作流|流程)\s+(?:run\s+)?([a-zA-Z0-9_-]+)", t, re.IGNORECASE)
        if name_m:
            candidate = name_m.group(1).lower()
            if candidate not in ('list', 'run', '列表', '顯示'):
                wf_name = candidate
        # If we got "workflow run" but name is in next position
        if not wf_name:
            run_m = re.search(r"\brun\s+([a-zA-Z0-9_-]+)", t, re.IGNORECASE)
            if run_m:
                wf_name = run_m.group(1).lower()
        # Extract inline positional param (word after workflow name)
        if wf_name:
            after_m = re.search(re.escape(wf_name) + r"\s+([a-zA-Z0-9_./-]+)", t, re.IGNORECASE)
            if after_m:
                inline_val = after_m.group(1)
                if inline_val.lower() not in ('--param',):
                    wf_params['name'] = inline_val
        # Extract --param key=value pairs
        for pm in re.finditer(r"--param\s+([a-zA-Z0-9_]+)=([^\s]+)", t):
            wf_params[pm.group(1)] = pm.group(2)
        return Plan(op="workflow", workflow_op="run",
                    workflow_name=wf_name, workflow_params=wf_params or None)

    # NLP for 'validate' / 'check rules' / '驗證' / '檢查規則'
    if re.search(r"\b(validate|驗證|檢查規則)\b", tl) or re.search(r"\b(check|lint)\s+(team\s+)?rules?\b", tl) or re.search(r"\bready\s+for\s+pr\b", tl):
        if re.search(r"\bcommit\b", tl):
            msg = parse_quoted_string(t)
            if msg is None:
                # Also try single quotes
                sq = re.search(r"'([^']+)'", t)
                if sq:
                    msg = sq.group(1)
            return Plan(op="validate_commit", validate_message=msg)
        elif re.search(r"\bbranch\b", tl):
            return Plan(op="validate_branch")
        elif re.search(r"\bquality\b", tl):
            return Plan(op="validate_quality")
        elif re.search(r"\b(ready\s+for\s+pr|all|rules?|規則|全部)\b", tl):
            return Plan(op="validate_rules")
        else:
            return Plan(op="validate_rules")

    # NLP for 'what should I do' / 'recommend' / 'suggest' / 'decide'
    if re.search(r"\b(what\s+should|recommend|suggest|advise|建議)\b", tl) or re.search(r"\b(next\s+step|該怎麼做|decide)\b", tl):
        goal = None
        goal_m = re.search(r"\bfor\s+(commit|push|merge|pr)\b", tl)
        if goal_m:
            goal = goal_m.group(1)
        return Plan(op="decide", decision_goal=goal)

    # NLP for 'analyze branches' / 'cleanup branches' / '分析分支' / '清理分支'
    if (re.search(r"\b(analyze|analysis|cleanup|clean\s*up)\b", tl) and re.search(r"\b(branch|branches)\b", tl)) \
       or (re.search(r"(分析|清理)", tl) and re.search(r"分支", tl)):
        if re.search(r"\b(cleanup|clean)\b", tl) or re.search(r"清理", tl):
            return Plan(op="branch", branch_op="cleanup")
        return Plan(op="branch", branch_op="analyze")
    if re.search(r"\bdelete\s+(all\s+)?merged\s+branch", tl) or re.search(r"刪除.*已合併.*分支", tl):
        return Plan(op="branch", branch_op="delete_merged")

    # NLP for 'stash'
    if re.search(r"\bstash\b", tl) or re.search(r"暫存(詳細|備份|安全)|安全套用暫存|暫存詳細", tl):
        # Advanced stash ops (must come before basic list/apply)
        if re.search(r"\blist\s+(detailed|verbose|detail)\b", tl) or re.search(r"暫存詳細", tl):
            return Plan(op="stash", stash_op="list_detailed")
        elif re.search(r"\b(backup|export)\b", tl) or re.search(r"暫存備份", tl):
            idx_m = re.search(r"\bstash@?\{?(\d+)\}?|\bindex\s+(\d+)|\b(?:backup|export)\s+(\d+)", tl)
            idx = int(next((g for g in (idx_m.groups() if idx_m else []) if g is not None), 0))
            return Plan(op="stash", stash_op="backup", stash_index=idx)
        elif re.search(r"\bapply\s+safe\b", tl) or re.search(r"安全套用暫存", tl):
            idx_m = re.search(r"\bstash@?\{?(\d+)\}?|\bindex\s+(\d+)|\bsafe\s+(\d+)", tl)
            idx = int(next((g for g in (idx_m.groups() if idx_m else []) if g is not None), 0))
            return Plan(op="stash", stash_op="apply_safe", stash_index=idx)
        # Basic stash ops
        elif re.search(r"\b(list|show all|顯示列表)\b", tl):
            return Plan(op="stash", stash_op="list")
        elif re.search(r"\bapply\b", tl):
            idx_m = re.search(r"\bstash@?\{?(\d+)\}?|\bindex\s+(\d+)", tl)
            idx = int(idx_m.group(1) or idx_m.group(2)) if idx_m else 0
            return Plan(op="stash", stash_op="apply", stash_index=idx)
        elif re.search(r"\bpop\b", tl):
            idx_m = re.search(r"\bstash@?\{?(\d+)\}?|\bindex\s+(\d+)", tl)
            idx = int(idx_m.group(1) or idx_m.group(2)) if idx_m else 0
            return Plan(op="stash", stash_op="pop", stash_index=idx)
        elif re.search(r"\b(drop|delete|remove)\b", tl):
            idx_m = re.search(r"\bstash@?\{?(\d+)\}?|\bindex\s+(\d+)", tl)
            idx = int(idx_m.group(1) or idx_m.group(2)) if idx_m else 0
            return Plan(op="stash", stash_op="drop", stash_index=idx)
        elif re.search(r"\bclear\b", tl):
            return Plan(op="stash", stash_op="clear")
        elif re.search(r"\bshow\b", tl):
            idx_m = re.search(r"\bstash@?\{?(\d+)\}?|\bindex\s+(\d+)", tl)
            idx = int(idx_m.group(1) or idx_m.group(2)) if idx_m else 0
            return Plan(op="stash", stash_op="show", stash_index=idx)
        else:  # default to save
            msg = parse_quoted_string(t)
            include_untracked = bool(re.search(r"\b(untracked|all|包含未追蹤)\b", tl))
            keep_index = bool(re.search(r"\bkeep-index\b", tl))
            return Plan(op="stash", stash_op="save", stash_message=msg,
                       stash_include_untracked=include_untracked, stash_keep_index=keep_index)

    # NLP for 'grep' / 'search' / 'find'
    if re.search(r"\b(grep|search|find|搜尋|查找)\b", tl) and not re.search(r"\blog\b", tl):
        pattern = parse_quoted_string(t)
        if not pattern:
            # Try to extract unquoted pattern after search/grep/find (use original text t, not tl)
            pattern_m = re.search(r"\b(?:grep|search|find|搜尋|查找)\s+(?:for\s+)?([^\s]+)", t, re.IGNORECASE)
            if pattern_m:
                pattern = pattern_m.group(1)

        file_pattern = None
        file_m = re.search(r"\bin\s+([*\w./]+)", t)  # Use original text to preserve case
        if file_m:
            file_pattern = file_m.group(1)

        ignore_case = bool(re.search(r"\bignore[- ]case\b|\bcase[- ]insensitive\b|-i\b", tl))
        return Plan(op="grep", grep_pattern=pattern, grep_file_pattern=file_pattern, grep_ignore_case=ignore_case)

    # NLP for 'reset' (including 'undo')
    if re.search(r"\b(reset|undo|撤銷)\b", tl):
        if re.search(r"\b(unstage|取消暫存)\b", tl):
            # unstage specific files or all
            paths = []
            path_m = re.findall(r"(?:unstage|取消暫存)\s+([^\s]+)", t, re.IGNORECASE)
            if path_m:
                paths = path_m
            return Plan(op="reset", reset_mode="mixed", reset_target="HEAD", reset_paths=paths)

        # Determine mode
        mode = "mixed"  # default
        if re.search(r"\b(hard|強制)\b", tl):
            mode = "hard"
        elif re.search(r"\b(soft|保留更改)\b", tl):
            mode = "soft"
        elif re.search(r"\b(undo|撤銷)\b", tl):
            # "undo" implies soft reset (keep changes staged)
            mode = "soft"

        target = "HEAD"
        if re.search(r"\b(undo|撤銷)\s+(last|上一個)\s+commit\b", tl):
            target = "HEAD~1"
        else:
            target_m = re.search(r"\b(?:to|至)\s+([^\s]+)", t, re.IGNORECASE)
            if target_m:
                target = target_m.group(1)

        return Plan(op="reset", reset_mode=mode, reset_target=target)

    # NLP for 'checkout' / 'switch'
    if re.search(r"\b(checkout|switch|切換)\b", tl) and not re.search(r"\bcreate\b", tl):
        target_m = re.search(r"\b(?:checkout|switch|切換)\s+(?:to\s+)?([^\s]+)", t, re.IGNORECASE)
        target = target_m.group(1) if target_m else "main"
        force = bool(re.search(r"\bforce\b|-f\b", tl))
        return Plan(op="checkout", checkout_target=target, checkout_force=force)

    # NLP for 'create branch'
    if re.search(r"\bcreate\s+(?:branch|分支)\b", tl):
        branch_m = re.search(r"\bcreate\s+(?:branch|分支)\s+([^\s]+)", t, re.IGNORECASE)
        branch_name = branch_m.group(1) if branch_m else None
        checkout = bool(re.search(r"\b(and\s+)?checkout\b", tl))
        return Plan(op="checkout", checkout_target=branch_name, checkout_create=True) if checkout else Plan(op="branch", branch_op="create", branch_name=branch_name)

    # NLP for 'restore' / 'discard'
    if re.search(r"\b(restore|discard|恢復|丟棄)\b", tl):
        staged = bool(re.search(r"\b(unstage|staged|暫存)\b", tl))
        paths = []
        path_m = re.findall(r"(?:restore|discard|恢復|丟棄)\s+(?:changes\s+in\s+)?([^\s]+)", t, re.IGNORECASE)
        if path_m:
            paths = [p for p in path_m if p not in ["changes", "in"]]

        source = None
        source_m = re.search(r"\bfrom\s+([^\s]+)", t, re.IGNORECASE)
        if source_m:
            source = source_m.group(1)

        worktree = not staged
        return Plan(op="restore", restore_paths=paths, restore_staged=staged, restore_source=source, restore_worktree=worktree)

    # NLP for 'cherry-pick'
    if re.search(r"\bcherry[- ]?pick\b", tl):
        hashes = parse_hashes(t)
        no_commit = bool(re.search(r"\bno[- ]commit\b|\bwithout commit\b", tl))
        push_mode = "push" if re.search(r"\bpush\b", tl) else "nopush"
        return Plan(op="cherry_pick", commits=hashes, no_commit=no_commit, push_mode=push_mode)

    # NLP for 'merge'
    if re.search(r"\bmerge\b", tl) and not re.search(r"\bsync[- ]?mode\b", tl):
        source_m = re.search(r"\bmerge\s+([^\s]+)", t, re.IGNORECASE)
        source = source_m.group(1) if source_m else "main"
        no_ff = bool(re.search(r"\bno[- ]ff\b", tl))
        squash = bool(re.search(r"\bsquash\b", tl))
        push_mode = "push" if re.search(r"\bpush\b", tl) else "nopush"
        return Plan(op="merge", merge_source=source, merge_no_ff=no_ff, merge_squash=squash, push_mode=push_mode)

    # NLP for 'blame'
    if re.search(r"\bblame\b", tl):
        path_m = re.search(r"\bblame\s+([^\s]+)", t, re.IGNORECASE)
        path = path_m.group(1) if path_m else None
        line_m = re.search(r"\bline\s+(\d+)(?:\s*-\s*(\d+))?", tl)
        line_start = int(line_m.group(1)) if line_m else None
        line_end = int(line_m.group(2)) if line_m and line_m.group(2) else None
        return Plan(op="blame", blame_path=path, blame_line_start=line_start, blame_line_end=line_end)

    # NLP for 'reflog'
    if re.search(r"\breflog\b", tl):
        count_m = re.search(r"\b(last|show)\s+(\d+)\b", tl)
        max_count = int(count_m.group(2)) if count_m else 20
        return Plan(op="reflog", reflog_max_count=max_count)

    # NLP for 'tag' or 'tags'
    if re.search(r"\btags?\b", tl):
        if re.search(r"\b(list|show|列出)\b", tl):
            return Plan(op="tag", tag_op="list")
        elif re.search(r"\b(delete|remove|刪除)\b", tl):
            tag_m = re.search(r"\b(?:delete|remove|刪除)\s+(?:tag\s+)?([^\s]+)", t, re.IGNORECASE)
            tag_name = tag_m.group(1) if tag_m else None
            push_mode = "push" if re.search(r"\bpush\b", tl) else "nopush"
            return Plan(op="tag", tag_op="delete", tag_name=tag_name, push_mode=push_mode)
        elif re.search(r"\bpush\s+tags\b", tl):
            return Plan(op="tag", tag_op="push")
        else:  # create tag
            tag_m = re.search(r"\b(?:create\s+)?tag\s+([^\s]+)", t, re.IGNORECASE)
            tag_name = tag_m.group(1) if tag_m else None
            msg = parse_quoted_string(t)
            annotated = bool(msg or re.search(r"\bannotated\b", tl))
            push_mode = "push" if re.search(r"\bpush\b", tl) else "nopush"
            return Plan(op="tag", tag_op="create", tag_name=tag_name, tag_message=msg, tag_annotated=annotated, push_mode=push_mode)

    # NLP for 'clean'
    if re.search(r"\bclean\b", tl):
        dry_run = bool(re.search(r"\b(dry[- ]run|preview|show|顯示)\b", tl) or not re.search(r"\b(force|remove|delete)\b", tl))
        force = bool(re.search(r"\b(force|remove|delete)\b", tl))
        directories = bool(re.search(r"\b(director|folder)\b", tl))
        ignored = bool(re.search(r"\bignored\b", tl))
        return Plan(op="clean", clean_dry_run=dry_run, clean_force=force, clean_directories=directories, clean_ignored=ignored)

    # NLP for 'rebase' (including 'squash')
    if re.search(r"\b(rebase|squash|合併)\b", tl) and not re.search(r"\bsync[- ]?mode\b", tl):
        interactive = bool(re.search(r"\binteractive(ly)?\b|-i\b", tl))

        if re.search(r"\b(squash|合併)\s+(last|上一個|最近)\s+(\d+)", tl):
            count_m = re.search(r"\b(?:squash|合併)\s+(?:last|上一個|最近)\s+(\d+)", tl)
            count = int(count_m.group(1)) if count_m else 2
            target = f"HEAD~{count}"
            interactive = True
        else:
            target_m = re.search(r"\brebase\s+(?:onto\s+)?([^\s]+)", t, re.IGNORECASE)
            target = target_m.group(1) if target_m else "main"

        count_m = re.search(r"\b(last|最近)\s+(\d+)\s+commits?\b", tl)
        count = int(count_m.group(2)) if count_m else None
        if count:
            target = f"HEAD~{count}"
            interactive = True

        push_mode = "push" if re.search(r"\bpush\b", tl) else "nopush"
        return Plan(op="rebase", rebase_target=target, rebase_interactive=interactive, rebase_count=count, push_mode=push_mode)

    # NLP for 'bisect'
    if re.search(r"\bbisect\b", tl):
        if re.search(r"\bstart\b", tl):
            return Plan(op="bisect", bisect_op="start")
        elif re.search(r"\bgood\b", tl):
            commit_m = re.search(r"\bgood\s+([0-9a-fA-F]+)", t)
            commit = commit_m.group(1) if commit_m else None
            return Plan(op="bisect", bisect_op="good", bisect_commit=commit)
        elif re.search(r"\bbad\b", tl):
            commit_m = re.search(r"\bbad\s+([0-9a-fA-F]+)", t)
            commit = commit_m.group(1) if commit_m else None
            return Plan(op="bisect", bisect_op="bad", bisect_commit=commit)
        elif re.search(r"\breset\b", tl):
            return Plan(op="bisect", bisect_op="reset")
        elif re.search(r"\bskip\b", tl):
            return Plan(op="bisect", bisect_op="skip")
        else:
            return Plan(op="bisect", bisect_op="start")

    # NLP for 'revert'
    if re.search(r"\brevert\b", tl):
        hashes = parse_hashes(t)
        no_commit = bool(re.search(r"\bno-commit\b|\bwithout commit\b", tl))
        push_mode = "push" if re.search(r"\bpush\b", tl) else "nopush"
        return Plan(op="revert", commits=hashes, no_commit=no_commit, push_mode=push_mode)

    # NLP for 'branch'
    if re.search(r"\bbranch\b", tl):
        if re.search(r"\bdelete\b|\bremove\b", tl):
            m = re.search(r"\bbranch\s+(?:delete|remove)\s+([^\s]+)", tl)
            name = m.group(1) if m else None
            remote = bool(re.search(r"\bremote\b", tl))
            local = bool(re.search(r"\blocal\b", tl))
            # if remote/local not specified, guess from context
            if not remote and not local:
                local = True
                remote = True
            return Plan(op="branch", branch_op="delete", branch_name=name, branch_local=local, branch_remote=remote, force=bool(re.search(r"\bforce\b", tl)))

    # NLP for 'log'
    if re.search(r"\b(log|history|日誌)\b", tl) or re.search(r"(作者|author)", tl): # Also trigger log if 'author' is present
        path_m = re.search(r"\b(?:for|of|on)\s+`?([^`\s]+)`?\b", tl)
        
        log_search_term = None
        log_search_is_author = False

        # Prioritize Chinese author search
        author_cn_m = re.search(r"(作者為|作者是)\s*([a-zA-Z0-9_.-]+)", tl)
        if author_cn_m:
            log_search_term = author_cn_m.group(2)
            log_search_is_author = True
        else:
            # Check for quoted search term (English or Chinese content)
            quoted_search = parse_quoted_string(t)
            if quoted_search:
                log_search_term = quoted_search
                if re.search(r"(作者|author)", tl): # If "author" keyword (English or Chinese) is near quoted search
                    log_search_is_author = True
            else: # Unquoted search term logic (English keywords only)
                search_m = re.search(r"\b(?:with|containing|message|grep|author)\s+([a-zA-Z0-9_.-]+)\b", tl)
                if search_m:
                    log_search_term = search_m.group(1)
                    if re.search(r"\bauthor\b", tl):
                        log_search_is_author = True

        count_m = re.search(r"\b(last|show|see)\s+(\d+)\b", tl)
        max_count = int(count_m.group(2)) if count_m else 20

        # Check for graph visualization
        graph = bool(re.search(r"\b(graph|tree|visual|視覺化|關係圖|圖形)\b", tl))
        all_branches = bool(re.search(r"\b(all|所有分支|所有)\b", tl))

        return Plan(
            op="log",
            log_path=path_m.group(1) if path_m else None,
            log_search=log_search_term,
            log_search_is_author=log_search_is_author,
            log_max_count=max_count,
            log_graph=graph,
            log_all_branches=all_branches,
        )
    # NLP for 'show'
    if re.search(r"\bshow\b", tl):
        if re.search(r"\blog\b", tl): # "show log" is a log command
             return parse_operation_from_text(t.replace("show ", "")) # Fixed typo here
        hashes = parse_hashes(t)
        if not hashes or "last" in tl or "current" in tl:
            target = "HEAD"
        else:
            target = hashes[0]
        return Plan(op="show", show_target=target)
    
    # NLP for 'diff'
    if re.search(r"\bdiff\b", tl):
        hashes = parse_hashes(t)
        staged = re.search(r"\bstaged\b|\bcached\b", tl)
        return Plan(op="diff", diff_targets=hashes, diff_staged=bool(staged))

    # NLP for 'commit'
    if re.search(r"\bcommit\b", tl):
        msg = parse_quoted_string(t) # Use the robust quoted string parser
        push_mode = "push" if re.search(r"\bpush\b", tl) else "nopush"
        amend = bool(re.search(r"\bamend\b", tl))
        # Detect root cause (English or Chinese)
        root_cause = None
        rc_m = re.search(r"root\s*cause\s*[:：]\s*[\"']?(.+?)[\"']?\s*$", t, re.IGNORECASE)
        if not rc_m:
            rc_m = re.search(r"原因\s*[:：]\s*[\"']?(.+?)[\"']?\s*$", t, re.IGNORECASE)
        if rc_m:
            root_cause = rc_m.group(1).strip().strip("\"'")
        return Plan(
            op="commit",
            message=msg,
            push_mode=push_mode,
            amend=amend,
            root_cause=root_cause,
        )
        
    # NLP for 'push'
    if re.search(r"\bpush\b", tl):
        force = bool(re.search(r"\bforce\b", tl))
        return Plan(op="push", push_mode="lease" if force else "push")

    # NLP for 'conflict detect' / 'check conflicts'
    if re.search(r"\b(detect|check)\s+conflicts?\b", tl) or re.search(r"\bconflicts?\s*(detect|check)\b", tl):
        target_m = re.search(r"\b(?:with|against|vs|和|跟)\s+([^\s]+)", t, re.IGNORECASE)
        target = target_m.group(1) if target_m else None
        return Plan(op="conflict_detect", conflict_target=target)

    # NLP for 'resolve conflicts' / 'show conflicts' / 'conflict status'
    if re.search(r"\b(resolve|fix)\s+conflicts?\b", tl) or re.search(r"\bconflicts?\s*(status|guide|help)\b", tl):
        file_m = re.search(r"\bin\s+([^\s]+)", t, re.IGNORECASE)
        file_path = file_m.group(1) if file_m else None
        return Plan(op="conflict_resolve", conflict_file=file_path)

    # NLP for 'preflight' / 'health check'
    if re.search(r"\b(preflight|pre-flight|health\s*check|repo\s*check)\b", tl):
        return Plan(op="preflight")

    # LLM fallback: if no regex matched, try local LLM
    if llm_config:
        try:
            from llm_fallback import llm_parse_intent
            result = llm_parse_intent(t, llm_config)
            if result:
                params = result.get('params', {})
                plan_fields = {f.name for f in Plan.__dataclass_fields__.values()}
                safe_params = {k: v for k, v in params.items() if k in plan_fields}
                return Plan(op=result['op'], **safe_params)
        except ImportError:
            pass

    return Plan(op="status")  # Default action


def _commit_block(plan: Plan) -> str:
    """Generate bash for commit with optional auto-log body."""
    if not plan.commit_log:
        # Original simple behavior: single-line -m
        parts = []
        cmd = "git commit"
        if plan.amend:
            cmd += " --amend"
            if not plan.message:
                cmd += " --no-edit"
        if plan.allow_empty:
            cmd += " --allow-empty"
        if plan.message:
            cmd += f" -m {q(plan.message)}"
            parts.append(cmd + "\n")
        elif not plan.amend:
            parts.append('read -r -p "Commit message: " MSG\n')
            parts.append(cmd + ' -m "$MSG"\n')
        else:
            parts.append(cmd + "\n")
        return ''.join(parts)

    # --- commit_log=True: generate structured body ---
    parts = []

    # Step 1: Get commit title
    if plan.message:
        parts.append(f'COMMIT_TITLE={q(plan.message)}\n')
    elif plan.amend:
        # Amend without new message: reuse existing
        parts.append('COMMIT_TITLE=$(git log -1 --format=%s 2>/dev/null || true)\n')
    else:
        parts.append('read -r -p "Commit message: " COMMIT_TITLE\n')
        parts.append('[ -z "$COMMIT_TITLE" ] && { echo "Empty message. Abort."; exit 1; }\n')

    # Step 2: Collect diff stat for body
    parts.append(r"""
# --- Auto-generated commit body ---
DIFF_STAT=$(git diff --cached --stat 2>/dev/null || true)
COMMIT_BODY=""
if [ -n "$DIFF_STAT" ]; then
  COMMIT_BODY="## Modified Files
${DIFF_STAT}"
fi
""")

    # Step 3: Root cause handling
    if plan.root_cause:
        rc = plan.root_cause.replace('"', '\\"')
        parts.append(f"""
COMMIT_BODY="${{COMMIT_BODY}}

## Root Cause
{rc}"
""")
    else:
        # Interactive prompt for fix/bug types
        parts.append(r"""
# Check if fix/bug commit — prompt for root cause
if echo "$COMMIT_TITLE" | grep -qiE '^(fix|bug|hotfix)'; then
  echo ""
  read -r -p "Root cause (optional, Enter to skip): " ROOT_CAUSE_INPUT
  if [ -n "$ROOT_CAUSE_INPUT" ]; then
    COMMIT_BODY="${COMMIT_BODY}

## Root Cause
${ROOT_CAUSE_INPUT}"
  fi
fi
""")

    # Step 4: Write temp file and commit
    cmd = "git commit"
    if plan.amend:
        cmd += " --amend"
    if plan.allow_empty:
        cmd += " --allow-empty"

    parts.append(r"""
# Compose full commit message via temp file
COMMIT_MSG_FILE=$(mktemp)
trap 'rm -f "$COMMIT_MSG_FILE"' EXIT
{
  echo "$COMMIT_TITLE"
  if [ -n "$COMMIT_BODY" ]; then
    echo ""
    echo "$COMMIT_BODY"
  fi
} > "$COMMIT_MSG_FILE"
""")
    parts.append(f'{cmd} -F "$COMMIT_MSG_FILE"\n')
    parts.append('rm -f "$COMMIT_MSG_FILE"\n')

    return ''.join(parts)


def execute_bash(script: str, skip_confirm: bool = False, plan: Plan = None) -> int:
    """Execute generated bash script directly with TTY preservation."""
    import subprocess
    import tempfile

    # 1. Preview: extract key git commands from script
    git_cmds = [l.strip() for l in script.splitlines()
                if l.strip().startswith("git ") and not l.strip().startswith("git rev-parse")]

    op_label = plan.op if plan else "unknown"
    print(f"[git-ops] operation: {op_label}")
    if git_cmds:
        print("[git-ops] commands:")
        for cmd in git_cmds[:8]:
            print(f"  $ {cmd}")
        if len(git_cmds) > 8:
            print(f"  ... and {len(git_cmds) - 8} more")

    # 2. [Y/n] confirmation
    if not skip_confirm:
        try:
            answer = input("\n Execute? [Y/n] ").strip().lower()
            if answer in ("n", "no"):
                print("[git-ops] Cancelled.")
                return 130
        except (EOFError, KeyboardInterrupt):
            print("\n[git-ops] Cancelled.")
            return 130

    # 3. Write to temp file and execute via bash (preserves TTY)
    sys.stdout.flush()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False, prefix='gops-') as f:
        f.write(script)
        script_path = f.name

    try:
        result = subprocess.run(
            ['bash', script_path],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return result.returncode
    finally:
        os.unlink(script_path)


def render(plan: Plan) -> str:
    out: List[str] = [bash_prelude()]
    
    # Set the operation name for error logging
    out.append(f"GIT_OPS_OPERATION={q(plan.op)}\n")

    def check_detached_head_for_write():
        if plan.op in ["commit", "revert", "cherry_pick", "reset", "tag", "branch"]:
             out.append('[ "$BR" = "HEAD" ] && { echo "Cannot perform write operation in detached HEAD state."; exit 1; }\n')
    
    check_detached_head_for_write()

    def maybe_push_with_upstream():
        out.append("ensure_upstream_if_exists\n")
        out.append(push_block(plan.push_mode))

    # Log
    if plan.op == "log":
        out.append("echo '[git-ops] showing git log'\n")

        # Build base command with graph support
        if plan.log_graph:
            # Use pretty format for better graph visualization
            base_cmd = f"git log --graph --oneline --decorate --color -n {q(str(plan.log_max_count))}"
        else:
            base_cmd = f"git log --oneline -n {q(str(plan.log_max_count))}"

        # Add --all flag if requested
        if plan.log_all_branches:
            base_cmd += " --all"

        if plan.log_search:
            if plan.log_search_is_author: # Use --author if it was an author search
                base_cmd += f" --author={q(plan.log_search)}"
            else: # Otherwise, default to --grep for general search
                base_cmd += f" --grep={q(plan.log_search)}"
        if plan.log_path:
            base_cmd += f" -- {q(plan.log_path)}"
        out.append(base_cmd + "\n")

    # Show
    elif plan.op == "show":
        target = plan.show_target or "HEAD"
        out.append(f"git show {q(target)}\n")

    # Diff
    elif plan.op == "diff":
        cmd = ["git", "diff"]
        if plan.diff_staged:
            cmd.append("--staged")
        if plan.diff_targets:
            cmd.extend(q(t) for t in plan.diff_targets)
        out.append(" ".join(cmd) + "\n")

    # Commit
    elif plan.op == "commit":
        out.append(stage_block(plan.stage_mode))
        if not plan.allow_empty:
            out.append(ensure_staged_nonempty())

        out.append(_commit_block(plan))

        if plan.push_mode != "nopush":
            out.append(sync_block(plan.sync_mode))
            maybe_push_with_upstream()
    
    # Push
    elif plan.op == "push":
        out.append(sync_block(plan.sync_mode))
        maybe_push_with_upstream()

    # Revert
    elif plan.op == "revert":
        if not plan.commits:
            out.append("echo 'No commit hashes provided to revert.'; exit 1\n")
        else:
            flag = "--no-commit" if plan.no_commit else ""
            out.append(f"git revert {flag} " + " ".join(q(c) for c in plan.commits) + " || {\n")
            out.append('  echo "Revert conflict. Resolve and then `git revert --continue` or `git revert --abort`";\n')
            out.append("  exit 1;\n}")
            
            if plan.push_mode != "nopush":
                out.append(sync_block(plan.sync_mode))
                maybe_push_with_upstream()

    # Branch
    elif plan.op == "branch":
        if plan.branch_op == 'delete':
            if not plan.branch_name:
                out.append("echo 'No branch name provided for deletion.'; exit 1\n")
            else:
                if plan.branch_local:
                    out.append(f'confirm_yes "About to delete LOCAL branch {q(plan.branch_name)}" || {{ echo "Canceled"; exit 1; }}\n')
                    if plan.force:
                        out.append(f"git branch -D {q(plan.branch_name)}\n")
                    else:
                        out.append(f"git branch -d {q(plan.branch_name)}\n")
                if plan.branch_remote:
                    out.append(f'confirm_yes "About to delete REMOTE branch {q(plan.branch_name)} on $REMOTE" || {{ echo "Canceled"; exit 1; }}\n')
                    out.append(f'git push "$REMOTE" --delete {q(plan.branch_name)}\n')
        elif plan.branch_op == 'create':
            if not plan.branch_name:
                out.append("echo 'No branch name provided.'; exit 1\n")
            else:
                out.append(f"git branch {q(plan.branch_name)}\n")
                out.append(f"echo 'Created branch {q(plan.branch_name)}'\n")
        elif plan.branch_op == 'analyze':
            try:
                from branch_manager import BranchManager
                manager = BranchManager(plan.branch_config)
                out.append(manager.generate_analyze_script())
            except ImportError:
                out.append(_inline_branch_analyze_script())
        elif plan.branch_op == 'cleanup':
            try:
                from branch_manager import BranchManager
                manager = BranchManager(plan.branch_config)
                out.append(manager.generate_cleanup_script())
            except ImportError:
                out.append(_inline_branch_cleanup_script())
        elif plan.branch_op == 'delete_merged':
            try:
                from branch_manager import BranchManager
                manager = BranchManager(plan.branch_config)
                out.append(manager.generate_delete_merged_script())
            except ImportError:
                out.append(_inline_branch_delete_merged_script())

    # Stash
    elif plan.op == "stash":
        if plan.stash_op == "list_detailed":
            try:
                from stash_manager import StashManager
                manager = StashManager(plan.stash_config)
                out.append(manager.generate_list_detailed_script())
            except ImportError:
                out.append(_inline_stash_list_detailed_script())
        elif plan.stash_op == "backup":
            try:
                from stash_manager import StashManager
                manager = StashManager(plan.stash_config)
                out.append(manager.generate_backup_script(plan.stash_index))
            except ImportError:
                out.append(_inline_stash_backup_script(plan.stash_index))
        elif plan.stash_op == "apply_safe":
            try:
                from stash_manager import StashManager
                manager = StashManager(plan.stash_config)
                out.append(manager.generate_apply_safe_script(plan.stash_index))
            except ImportError:
                out.append(_inline_stash_apply_safe_script(plan.stash_index))
        elif plan.stash_op == "list":
            out.append("git stash list\n")
        elif plan.stash_op == "show":
            out.append(f"git stash show -p stash@{{{plan.stash_index}}}\n")
        elif plan.stash_op == "apply":
            out.append(f"git stash apply stash@{{{plan.stash_index}}}\n")
        elif plan.stash_op == "pop":
            out.append(f"git stash pop stash@{{{plan.stash_index}}}\n")
        elif plan.stash_op == "drop":
            out.append(f'confirm_yes "About to drop stash@{{{plan.stash_index}}}" || {{ echo "Canceled"; exit 1; }}\n')
            out.append(f"git stash drop stash@{{{plan.stash_index}}}\n")
        elif plan.stash_op == "clear":
            out.append('confirm_yes "About to clear ALL stashes" || { echo "Canceled"; exit 1; }\n')
            out.append("git stash clear\n")
        else:  # save
            cmd = "git stash push"
            if plan.stash_include_untracked:
                cmd += " -u"
            if plan.stash_keep_index:
                cmd += " --keep-index"
            if plan.stash_message:
                cmd += f" -m {q(plan.stash_message)}"
            out.append(cmd + "\n")

    # Grep
    elif plan.op == "grep":
        if not plan.grep_pattern:
            out.append("echo 'No search pattern provided.'; exit 1\n")
        else:
            cmd = "git grep"
            if plan.grep_line_number:
                cmd += " -n"
            if plan.grep_ignore_case:
                cmd += " -i"
            cmd += f" {q(plan.grep_pattern)}"
            if plan.grep_file_pattern:
                cmd += f" -- {q(plan.grep_file_pattern)}"
            out.append(cmd + "\n")

    # Reset
    elif plan.op == "reset":
        if plan.reset_paths:
            # Unstaging specific files
            out.append(f"git reset {q(plan.reset_target)} " + " ".join(q(p) for p in plan.reset_paths) + "\n")
        else:
            cmd = "git reset"
            if plan.reset_mode == "soft":
                cmd += " --soft"
            elif plan.reset_mode == "hard":
                out.append('confirm_yes "About to perform HARD reset. All changes will be lost!" || { echo "Canceled"; exit 1; }\n')
                cmd += " --hard"
            elif plan.reset_mode == "mixed":
                cmd += " --mixed"

            cmd += f" {q(plan.reset_target)}"
            out.append(cmd + "\n")

    # Checkout/Switch
    elif plan.op == "checkout":
        if plan.checkout_create:
            out.append(f"git checkout -b {q(plan.checkout_target)}\n")
        else:
            cmd = "git checkout"
            if plan.checkout_force:
                cmd += " -f"
            cmd += f" {q(plan.checkout_target)}"
            out.append(cmd + "\n")

    # Restore
    elif plan.op == "restore":
        if not plan.restore_paths:
            out.append("echo 'No paths provided to restore.'; exit 1\n")
        else:
            cmd = "git restore"
            if plan.restore_staged:
                cmd += " --staged"
            if plan.restore_source:
                cmd += f" --source={q(plan.restore_source)}"
            cmd += " " + " ".join(q(p) for p in plan.restore_paths)
            out.append(cmd + "\n")

    # Cherry-pick
    elif plan.op == "cherry_pick":
        if not plan.commits:
            out.append("echo 'No commit hashes provided to cherry-pick.'; exit 1\n")
        else:
            flag = "--no-commit" if plan.no_commit else ""
            out.append(f"git cherry-pick {flag} " + " ".join(q(c) for c in plan.commits) + " || {\n")
            out.append('  echo "Cherry-pick conflict. Resolve and then `git cherry-pick --continue` or `git cherry-pick --abort`";\n')
            out.append("  exit 1;\n}\n")

            if plan.push_mode != "nopush":
                out.append(sync_block(plan.sync_mode))
                maybe_push_with_upstream()

    # Merge
    elif plan.op == "merge":
        if not plan.merge_source:
            out.append("echo 'No merge source provided.'; exit 1\n")
        else:
            cmd = "git merge"
            if plan.merge_no_ff:
                cmd += " --no-ff"
            if plan.merge_squash:
                cmd += " --squash"
            cmd += f" {q(plan.merge_source)}"
            out.append(cmd + " || {\n")
            out.append('  echo "Merge conflict. Resolve and then `git commit` or `git merge --abort`";\n')
            out.append("  exit 1;\n}\n")

            if plan.push_mode != "nopush":
                out.append(sync_block(plan.sync_mode))
                maybe_push_with_upstream()

    # Blame
    elif plan.op == "blame":
        if not plan.blame_path:
            out.append("echo 'No file path provided for blame.'; exit 1\n")
        else:
            cmd = f"git blame {q(plan.blame_path)}"
            if plan.blame_line_start:
                if plan.blame_line_end:
                    cmd += f" -L {plan.blame_line_start},{plan.blame_line_end}"
                else:
                    cmd += f" -L {plan.blame_line_start},{plan.blame_line_start}"
            out.append(cmd + "\n")

    # Reflog
    elif plan.op == "reflog":
        out.append(f"git reflog -n {plan.reflog_max_count}\n")

    # Tag
    elif plan.op == "tag":
        if plan.tag_op == "list":
            out.append("git tag -l\n")
        elif plan.tag_op == "delete":
            if not plan.tag_name:
                out.append("echo 'No tag name provided for deletion.'; exit 1\n")
            else:
                out.append(f'confirm_yes "About to delete tag {q(plan.tag_name)}" || {{ echo "Canceled"; exit 1; }}\n')
                out.append(f"git tag -d {q(plan.tag_name)}\n")
                if plan.push_mode != "nopush":
                    out.append(f'git push "$REMOTE" --delete {q(plan.tag_name)}\n')
        elif plan.tag_op == "push":
            out.append('git push "$REMOTE" --tags\n')
        else:  # create
            if not plan.tag_name:
                out.append("echo 'No tag name provided.'; exit 1\n")
            else:
                cmd = "git tag"
                if plan.tag_annotated and plan.tag_message:
                    cmd += f" -a {q(plan.tag_name)} -m {q(plan.tag_message)}"
                else:
                    cmd += f" {q(plan.tag_name)}"
                out.append(cmd + "\n")
                if plan.push_mode != "nopush":
                    out.append(f'git push "$REMOTE" {q(plan.tag_name)}\n')

    # Clean
    elif plan.op == "clean":
        cmd = "git clean"
        if plan.clean_dry_run:
            cmd += " -n"
        else:
            out.append('confirm_yes "About to remove untracked files" || { echo "Canceled"; exit 1; }\n')
            if plan.clean_force:
                cmd += " -f"
        if plan.clean_directories:
            cmd += " -d"
        if plan.clean_ignored:
            cmd += " -x"
        out.append(cmd + "\n")

    # Rebase
    elif plan.op == "rebase":
        if not plan.rebase_target:
            out.append("echo 'No rebase target provided.'; exit 1\n")
        else:
            cmd = "git rebase"
            if plan.rebase_interactive:
                cmd += " -i"
            cmd += f" {q(plan.rebase_target)}"
            out.append(cmd + " || {\n")
            out.append('  echo "Rebase conflict or issue. Resolve and then `git rebase --continue` or `git rebase --abort`";\n')
            out.append("  exit 1;\n}\n")

            if plan.push_mode != "nopush":
                maybe_push_with_upstream()

    # Bisect
    elif plan.op == "bisect":
        if plan.bisect_op == "start":
            out.append("git bisect start\n")
            out.append("echo 'Bisect started. Mark commits as good/bad to find the issue.'\n")
        elif plan.bisect_op == "good":
            if plan.bisect_commit:
                out.append(f"git bisect good {q(plan.bisect_commit)}\n")
            else:
                out.append("git bisect good\n")
        elif plan.bisect_op == "bad":
            if plan.bisect_commit:
                out.append(f"git bisect bad {q(plan.bisect_commit)}\n")
            else:
                out.append("git bisect bad\n")
        elif plan.bisect_op == "reset":
            out.append("git bisect reset\n")
        elif plan.bisect_op == "skip":
            out.append("git bisect skip\n")
        else:
            out.append("git bisect start\n")

    # Preflight Check
    elif plan.op == "preflight":
        try:
            from preflight_checker import PreflightChecker
            checker = PreflightChecker(plan.preflight_config)
            out.append(checker.generate_script())
        except ImportError:
            out.append(_inline_preflight_script())

    # Conflict Detection
    elif plan.op == "conflict_detect":
        try:
            from conflict_detector import ConflictDetector
            detector = ConflictDetector(plan.conflict_config)
            out.append(detector.generate_detect_script(plan.conflict_target))
        except ImportError:
            out.append(_inline_conflict_detect_script())

    # Conflict Resolution Guide
    elif plan.op == "conflict_resolve":
        try:
            from conflict_detector import ConflictDetector
            detector = ConflictDetector(plan.conflict_config)
            out.append(detector.generate_resolve_script(plan.conflict_file))
        except ImportError:
            out.append(_inline_conflict_resolve_script())

    # Decision Engine
    elif plan.op == "decide":
        try:
            from decision_engine import DecisionEngine
            engine = DecisionEngine(plan.decision_config)
            out.append(engine.generate_script(plan.decision_goal))
        except ImportError:
            out.append(_inline_decision_script())

    # Validate Commit Message
    elif plan.op == "validate_commit":
        try:
            from team_rules_validator import TeamRulesValidator
            validator = TeamRulesValidator(plan.team_rules_config)
            out.append(validator.generate_commit_script(plan.validate_message))
        except ImportError:
            if plan.validate_message:
                out.append(f'MSG={q(plan.validate_message)}\n')
            out.append(_inline_validate_commit_script())

    # Validate Branch Name
    elif plan.op == "validate_branch":
        try:
            from team_rules_validator import TeamRulesValidator
            validator = TeamRulesValidator(plan.team_rules_config)
            out.append(validator.generate_branch_script())
        except ImportError:
            out.append(_inline_validate_branch_script())

    # Validate Quality Checks
    elif plan.op == "validate_quality":
        try:
            from team_rules_validator import TeamRulesValidator
            validator = TeamRulesValidator(plan.team_rules_config)
            out.append(validator.generate_quality_script())
        except ImportError:
            out.append(_inline_validate_rules_script())

    # Validate All Rules
    elif plan.op == "validate_rules":
        try:
            from team_rules_validator import TeamRulesValidator
            validator = TeamRulesValidator(plan.team_rules_config)
            out.append(validator.generate_full_script())
        except ImportError:
            out.append(_inline_validate_rules_script())

    # Workflow Templates
    elif plan.op == "workflow":
        try:
            from workflow_engine import WorkflowEngine
            engine = WorkflowEngine(plan.workflow_config)
            if plan.workflow_op == "list":
                out.append(engine.generate_list_script())
            else:
                out.append(engine.generate_script(
                    plan.workflow_name or '', plan.workflow_params))
        except ImportError:
            out.append(_inline_workflow_script(plan))

    # Default/Fallback
    else:
        out.append("git status\n")

    return "".join(out)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generates a paste-ready bash script for common Git operations.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--from-text", help="Generate script from a natural language request.")

    subparsers = parser.add_subparsers(dest="op", title="Operations")

    # Commit operation
    p_commit = subparsers.add_parser("commit", help="Stage changes and create a commit.")
    p_commit.add_argument("-m", "--message", help="Commit message.")
    p_commit.add_argument("--push", action="store_const", const="push", dest="push_mode", default="nopush", help="Push after commit.")
    p_commit.add_argument("--sync", choices=["rebase", "merge", "none"], default="rebase", dest="sync_mode", help="Sync strategy before pushing.")
    p_commit.add_argument("--stage", choices=["all", "patch", "interactive", "keep"], default="all", dest="stage_mode", help="Staging mode.")
    p_commit.add_argument("--amend", action="store_true", help="Amend the previous commit.")
    p_commit.add_argument("--root-cause", dest="root_cause", help="Root cause for fix/bug commits.")
    p_commit.add_argument("--no-commit-log", action="store_false", dest="commit_log", default=True,
                           help="Disable auto-generated commit body log.")

    # Log operation
    p_log = subparsers.add_parser("log", help="Show commit logs.")
    p_log.add_argument("log_path", nargs="?", help="Show log for a specific file path.")
    p_log.add_argument("-s", "--search", dest="log_search", help="Search commit messages (grep).")
    p_log.add_argument("--author", action="store_true", dest="log_search_is_author", help="Treat search term as author.")
    p_log.add_argument("-n", "--max-count", type=int, default=20, dest="log_max_count", help="Limit number of commits.")

    # Show operation
    p_show = subparsers.add_parser("show", help="Show various types of objects (commits, etc.).")
    p_show.add_argument("show_target", nargs="?", default="HEAD", help="The object to show (commit hash, branch, tag).")
    
    # Diff operation
    p_diff = subparsers.add_parser("diff", help="Show changes between commits, the working tree, etc.")
    p_diff.add_argument("diff_targets", nargs='*', help="Commits or branches to compare. 0: work-tree, 1: vs work-tree, 2: between them.")
    p_diff.add_argument("--staged", action="store_true", dest="diff_staged", help="Show staged changes.")

    # Push operation
    p_push = subparsers.add_parser("push", help="Push the current branch.")
    p_push.add_argument("--sync", choices=["rebase", "merge", "none"], default="rebase", dest="sync_mode", help="Sync strategy before pushing.")
    p_push.add_argument("--force", action="store_const", const="lease", dest="push_mode", default="push", help="Force push with lease.")

    # Revert operation
    p_revert = subparsers.add_parser("revert", help="Revert one or more commits.")
    p_revert.add_argument("commits", nargs='+', help="The commit hash(es) to revert.")
    p_revert.add_argument("--no-commit", action="store_true", help="Apply the revert changes to the working tree but do not commit.")
    p_revert.add_argument("--push", action="store_const", const="push", dest="push_mode", default="nopush", help="Push after reverting.")

    # Branch operation
    p_branch = subparsers.add_parser("branch", help="Manage branches.")
    branch_sub = p_branch.add_subparsers(dest="branch_op", required=True)
    p_branch_delete = branch_sub.add_parser("delete", help="Delete a branch.")
    p_branch_delete.add_argument("branch_name", help="Name of the branch to delete.")
    p_branch_delete.add_argument("--local", action="store_true", dest="branch_local", help="Delete local branch.")
    p_branch_delete.add_argument("--remote", action="store_true", dest="branch_remote", help="Delete remote branch.")
    p_branch_delete.add_argument("-D", "--force", action="store_true", help="Force deletion (git branch -D).")
    p_branch_create = branch_sub.add_parser("create", help="Create a new branch.")
    p_branch_create.add_argument("branch_name", help="Name of the new branch.")
    branch_sub.add_parser("analyze", help="Analyze all branches (active/stale/merged).")
    branch_sub.add_parser("cleanup", help="Interactive branch cleanup.")
    branch_sub.add_parser("delete-merged", help="Delete all merged branches.")

    # Stash operation
    p_stash = subparsers.add_parser("stash", help="Stash changes.")
    stash_sub = p_stash.add_subparsers(dest="stash_op")
    stash_sub.add_parser("list", help="List all stashes.")
    stash_sub.add_parser("list-detailed", help="Detailed stash listing with age and stats.")
    p_stash_backup = stash_sub.add_parser("backup", help="Export stash to .patch file.")
    p_stash_backup.add_argument("stash_index", type=int, nargs="?", default=0, help="Stash index.")
    p_stash_apply_safe = stash_sub.add_parser("apply-safe", help="Apply stash with conflict pre-check.")
    p_stash_apply_safe.add_argument("stash_index", type=int, nargs="?", default=0, help="Stash index.")
    p_stash_save = stash_sub.add_parser("save", help="Save current changes to stash.")
    p_stash_save.add_argument("-m", "--message", dest="stash_message", help="Stash message.")
    p_stash_save.add_argument("-u", "--include-untracked", action="store_true", dest="stash_include_untracked", help="Include untracked files.")
    p_stash_save.add_argument("--keep-index", action="store_true", dest="stash_keep_index", help="Keep index.")
    p_stash_apply = stash_sub.add_parser("apply", help="Apply a stash.")
    p_stash_apply.add_argument("stash_index", type=int, nargs="?", default=0, help="Stash index.")
    p_stash_pop = stash_sub.add_parser("pop", help="Pop a stash.")
    p_stash_pop.add_argument("stash_index", type=int, nargs="?", default=0, help="Stash index.")
    p_stash_drop = stash_sub.add_parser("drop", help="Drop a stash.")
    p_stash_drop.add_argument("stash_index", type=int, nargs="?", default=0, help="Stash index.")
    p_stash_show = stash_sub.add_parser("show", help="Show a stash.")
    p_stash_show.add_argument("stash_index", type=int, nargs="?", default=0, help="Stash index.")
    stash_sub.add_parser("clear", help="Clear all stashes.")

    # Grep operation
    p_grep = subparsers.add_parser("grep", help="Search for patterns in tracked files.")
    p_grep.add_argument("grep_pattern", help="Pattern to search for.")
    p_grep.add_argument("--file-pattern", dest="grep_file_pattern", help="File pattern to limit search (e.g., '*.py').")
    p_grep.add_argument("-i", "--ignore-case", action="store_true", dest="grep_ignore_case", help="Case insensitive search.")

    # Reset operation
    p_reset = subparsers.add_parser("reset", help="Reset current HEAD to specified state.")
    p_reset.add_argument("reset_target", nargs="?", default="HEAD", help="Target commit to reset to.")
    p_reset.add_argument("--soft", action="store_const", const="soft", dest="reset_mode", help="Soft reset (keep changes staged).")
    p_reset.add_argument("--hard", action="store_const", const="hard", dest="reset_mode", help="Hard reset (discard all changes).")
    p_reset.add_argument("--mixed", action="store_const", const="mixed", dest="reset_mode", default="mixed", help="Mixed reset (default, keep changes unstaged).")
    p_reset.add_argument("--paths", nargs="+", dest="reset_paths", help="Specific paths to unstage.")

    # Checkout operation
    p_checkout = subparsers.add_parser("checkout", help="Switch branches or restore working tree files.")
    p_checkout.add_argument("checkout_target", help="Branch or commit to checkout.")
    p_checkout.add_argument("-b", "--create", action="store_true", dest="checkout_create", help="Create a new branch.")
    p_checkout.add_argument("-f", "--force", action="store_true", dest="checkout_force", help="Force checkout.")

    # Restore operation
    p_restore = subparsers.add_parser("restore", help="Restore working tree files.")
    p_restore.add_argument("restore_paths", nargs="+", help="Paths to restore.")
    p_restore.add_argument("--staged", action="store_true", dest="restore_staged", help="Restore staged changes.")
    p_restore.add_argument("--source", dest="restore_source", help="Source to restore from.")

    # Cherry-pick operation
    p_cherry = subparsers.add_parser("cherry-pick", help="Apply changes from existing commits.")
    p_cherry.add_argument("commits", nargs="+", help="Commit hash(es) to cherry-pick.")
    p_cherry.add_argument("--no-commit", action="store_true", dest="no_commit", help="Apply changes without committing.")
    p_cherry.add_argument("--push", action="store_const", const="push", dest="push_mode", default="nopush", help="Push after cherry-picking.")

    # Merge operation
    p_merge = subparsers.add_parser("merge", help="Join two or more development histories together.")
    p_merge.add_argument("merge_source", help="Branch or commit to merge.")
    p_merge.add_argument("--no-ff", action="store_true", dest="merge_no_ff", help="Create a merge commit even when fast-forward is possible.")
    p_merge.add_argument("--squash", action="store_true", dest="merge_squash", help="Squash commits.")
    p_merge.add_argument("--push", action="store_const", const="push", dest="push_mode", default="nopush", help="Push after merging.")

    # Blame operation
    p_blame = subparsers.add_parser("blame", help="Show what revision and author last modified each line of a file.")
    p_blame.add_argument("blame_path", help="File path to blame.")
    p_blame.add_argument("--line-start", type=int, dest="blame_line_start", help="Start line number.")
    p_blame.add_argument("--line-end", type=int, dest="blame_line_end", help="End line number.")

    # Reflog operation
    p_reflog = subparsers.add_parser("reflog", help="Show reference logs.")
    p_reflog.add_argument("-n", "--max-count", type=int, default=20, dest="reflog_max_count", help="Limit number of entries.")

    # Tag operation
    p_tag = subparsers.add_parser("tag", help="Create, list, delete or verify tags.")
    tag_sub = p_tag.add_subparsers(dest="tag_op")
    tag_sub.add_parser("list", help="List all tags.")
    p_tag_create = tag_sub.add_parser("create", help="Create a new tag.")
    p_tag_create.add_argument("tag_name", help="Tag name.")
    p_tag_create.add_argument("-m", "--message", dest="tag_message", help="Tag message (creates annotated tag).")
    p_tag_create.add_argument("--push", action="store_const", const="push", dest="push_mode", default="nopush", help="Push tag after creation.")
    p_tag_delete = tag_sub.add_parser("delete", help="Delete a tag.")
    p_tag_delete.add_argument("tag_name", help="Tag name to delete.")
    p_tag_delete.add_argument("--push", action="store_const", const="push", dest="push_mode", default="nopush", help="Also delete from remote.")
    tag_sub.add_parser("push", help="Push all tags to remote.")

    # Clean operation
    p_clean = subparsers.add_parser("clean", help="Remove untracked files from working tree.")
    p_clean.add_argument("-n", "--dry-run", action="store_true", dest="clean_dry_run", default=True, help="Don't actually remove, just show what would be done.")
    p_clean.add_argument("-f", "--force", action="store_true", dest="clean_force", help="Actually remove files.")
    p_clean.add_argument("-d", "--directories", action="store_true", dest="clean_directories", help="Remove directories as well.")
    p_clean.add_argument("-x", "--ignored", action="store_true", dest="clean_ignored", help="Remove ignored files as well.")

    # Rebase operation
    p_rebase = subparsers.add_parser("rebase", help="Reapply commits on top of another base tip.")
    p_rebase.add_argument("rebase_target", help="Branch or commit to rebase onto.")
    p_rebase.add_argument("-i", "--interactive", action="store_true", dest="rebase_interactive", help="Interactive rebase.")
    p_rebase.add_argument("--push", action="store_const", const="push", dest="push_mode", default="nopush", help="Push after rebasing.")

    # Bisect operation
    p_bisect = subparsers.add_parser("bisect", help="Use binary search to find the commit that introduced a bug.")
    bisect_sub = p_bisect.add_subparsers(dest="bisect_op", required=True)
    bisect_sub.add_parser("start", help="Start bisect session.")
    p_bisect_good = bisect_sub.add_parser("good", help="Mark commit as good.")
    p_bisect_good.add_argument("bisect_commit", nargs="?", help="Commit hash (optional, defaults to current).")
    p_bisect_bad = bisect_sub.add_parser("bad", help="Mark commit as bad.")
    p_bisect_bad.add_argument("bisect_commit", nargs="?", help="Commit hash (optional, defaults to current).")
    bisect_sub.add_parser("reset", help="Exit bisect session.")
    bisect_sub.add_parser("skip", help="Skip current commit.")

    # Preflight check operation
    subparsers.add_parser("preflight", help="Run preflight checks on the repository.")

    # Conflict detection operation
    p_conflict_detect = subparsers.add_parser("conflict-detect", help="Detect potential merge conflicts.")
    p_conflict_detect.add_argument("conflict_target", nargs="?", help="Target branch to check against.")

    # Conflict resolution guide
    p_conflict_resolve = subparsers.add_parser("conflict-resolve", help="Guide through conflict resolution.")
    p_conflict_resolve.add_argument("--file", dest="conflict_file", help="Specific file to resolve.")

    # Decision engine
    p_decide = subparsers.add_parser("decide", help="Get smart workflow recommendations.")
    p_decide.add_argument("decision_goal", nargs="?", help="Goal: commit, push, merge, pr")

    # Team rules validation
    p_validate = subparsers.add_parser("validate", help="Validate team rules.")
    validate_sub = p_validate.add_subparsers(dest="team_rules_op", required=True)
    p_val_commit = validate_sub.add_parser("commit", help="Validate commit message format.")
    p_val_commit.add_argument("-m", "--message", dest="validate_message", help="Commit message to validate.")
    validate_sub.add_parser("branch", help="Validate current branch name.")
    validate_sub.add_parser("quality", help="Run quality checks.")
    validate_sub.add_parser("all", help="Run all validations.")

    # Workflow templates
    p_workflow = subparsers.add_parser("workflow", help="Run multi-step workflow templates.")
    workflow_sub = p_workflow.add_subparsers(dest="workflow_op", required=True)
    workflow_sub.add_parser("list", help="List available workflows.")
    p_wf_run = workflow_sub.add_parser("run", help="Run a workflow.")
    p_wf_run.add_argument("workflow_name", help="Workflow name.")
    p_wf_run.add_argument("--param", action="append", dest="workflow_param_list",
                          metavar="KEY=VALUE", help="Workflow parameter (repeatable).")

    # Add configuration and logging arguments
    parser.add_argument("--config", metavar="FILE", help="Path to configuration file")
    parser.add_argument("--no-log", action="store_true", help="Disable usage logging")
    parser.add_argument("--init-config", action="store_true", help="Initialize configuration file")
    parser.add_argument("-x", "--execute", action="store_true", help="Execute generated bash script directly (instead of printing)")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip [Y/n] confirmation (use with -x)")
    parser.add_argument("--print", dest="print_mode", action="store_true", help="Force print mode (overrides config default_mode: execute)")

    args = parser.parse_args()

    # Handle config initialization
    if args.init_config:
        try:
            from config_manager import ConfigManager
            config = ConfigManager()
            path = config.export_template()
            print(f"Configuration template created: {path}")
            print("Edit this file to customize git-ops behavior.")
            return
        except ImportError:
            print("Error: config_manager not available")
            return

    # Load configuration
    config = None
    try:
        from config_manager import ConfigManager
        config = ConfigManager(args.config)
    except ImportError:
        # Config manager not available, continue with defaults
        pass

    # Initialize logger (only if logging enabled)
    logger = None
    logging_enabled = config.get('logging.enabled', True) if config else True

    if not args.no_log and logging_enabled and os.environ.get('GIT_OPS_NO_LOG') != '1':
        try:
            from usage_logger import UsageLogger
            logger = UsageLogger()
        except ImportError:
            # Logger not available, continue without logging
            pass

    plan = None
    input_text = None

    if args.from_text:
        input_text = args.from_text

        # Check for alias resolution
        if config:
            resolved = config.resolve_alias(args.from_text)
            if resolved != args.from_text:
                input_text = resolved

            # Check for custom patterns
            custom = config.resolve_custom_pattern(input_text)
            if custom:
                input_text = custom

        llm_cfg = config.get('llm_fallback', {}) if config else None
        plan = parse_operation_from_text(input_text, llm_config=llm_cfg)
    elif args.op:
        arg_dict = vars(args)
        # Filter out non-Plan keys (argparse global args)
        plan_fields = {f.name for f in Plan.__dataclass_fields__.values()}
        filtered = {k: v for k, v in arg_dict.items() if k in plan_fields and v is not None}
        plan = Plan(**filtered)

        # Map workflow param list into dict and normalize name
        if plan.op == "workflow":
            if hasattr(args, 'workflow_param_list') and args.workflow_param_list:
                params = {}
                for item in args.workflow_param_list:
                    if '=' in item:
                        k, v = item.split('=', 1)
                        params[k] = v
                plan.workflow_params = params or None
            if plan.workflow_name:
                plan.workflow_name = plan.workflow_name.replace('-', '_')

        # Map hyphenated stash sub-operations to underscore form
        if plan.op == "stash" and plan.stash_op:
            stash_op_map = {'list-detailed': 'list_detailed', 'apply-safe': 'apply_safe'}
            plan.stash_op = stash_op_map.get(plan.stash_op, plan.stash_op)

        # Map hyphenated branch sub-operations to underscore form
        if plan.op == "branch" and plan.branch_op:
            branch_op_map = {'delete-merged': 'delete_merged'}
            plan.branch_op = branch_op_map.get(plan.branch_op, plan.branch_op)

        # Map validate sub-operations to distinct Plan ops
        if plan.op == "validate" and plan.team_rules_op:
            op_map = {'commit': 'validate_commit', 'branch': 'validate_branch',
                      'quality': 'validate_quality', 'all': 'validate_rules'}
            plan.op = op_map.get(plan.team_rules_op, 'validate_rules')

    if plan:
        # Wire preflight config from YAML if available
        if plan.op == "preflight" and config:
            plan.preflight_config = config.get('preflight', {}) or {}

        if plan.op in ("conflict_detect", "conflict_resolve") and config:
            plan.conflict_config = config.get('conflict_detection', {}) or {}

        if plan.op == "decide" and config:
            plan.decision_config = config.get('decision_engine', {}) or {}

        if plan.op in ("validate_commit", "validate_branch", "validate_quality", "validate_rules") and config:
            plan.team_rules_config = config.get('team_rules', {}) or {}

        if plan.op == "stash" and plan.stash_op in ("list_detailed", "backup", "apply_safe") and config:
            plan.stash_config = config.get('stash_management', {}) or {}

        if plan.op == "workflow" and config:
            plan.workflow_config = config.get('workflows', {}) or {}

        if plan.op == "branch" and plan.branch_op in ("analyze", "cleanup", "delete_merged") and config:
            plan.branch_config = config.get('branch_management', {}) or {}

        if plan.op == "commit" and config:
            plan.commit_config = config.get('commit', {}) or {}
            if plan.commit_config.get('auto_log') is False:
                plan.commit_log = False

        bash = render(plan)

        # Determine execute vs print mode
        should_execute = getattr(args, 'execute', False)
        if not should_execute and config:
            should_execute = config.get('executor.default_mode', 'print') == 'execute'
        if getattr(args, 'print_mode', False):
            should_execute = False

        if should_execute:
            skip_confirm = getattr(args, 'yes', False)
            rc = execute_bash(bash, skip_confirm=skip_confirm, plan=plan)
            if rc != 0:
                sys.exit(rc)
        else:
            print("```bash")
            print(bash.rstrip())
            print("```")

        # Log usage if enabled
        if logger and input_text:
            try:
                logger.log(input_text, plan.op, success=True)
            except Exception:
                # Don't fail if logging fails
                pass
    else:
        # No subcommand given and no text, print help.
        parser.print_help()


if __name__ == "__main__":
    main()