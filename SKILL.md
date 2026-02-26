---
name: git-ops
description: Generate safe, paste-ready Git command sequences for all common Git operations via natural language. Supports commit, push, stash, branch management, search, reset, revert, cherry-pick, merge, and more.
allowed-tools:
  - Bash
---

# Git Ops - Natural Language Git Commands

## Purpose
This skill converts natural-language Git requests into **single paste-ready bash blocks** that:
- Perform comprehensive preflight checks
- Execute the requested Git operation(s) safely
- Sync with remote when needed (default: rebase)
- Use safe force-push methods (`--force-with-lease`)
- Include confirmation prompts for destructive operations

## Defaults
- Remote: `origin`
- Branch: current branch (detected via `git rev-parse --abbrev-ref HEAD`)
- Sync before push: `rebase` (use `merge` only if explicitly requested)
- Auth: Interactive prompts allowed (works with SSH password or key authentication)

## How to Use

Simply describe what you want to do in natural language:

```bash
python3 scripts/git_ops.py --from-text "commit with message 'fix bug' and push"
python3 scripts/git_ops.py --from-text "stash my changes"
python3 scripts/git_ops.py --from-text "search for 'TODO' in *.py files"
```

Or use structured subcommands for more control (see below).

## Supported Operations

### 1. Commit & Push
**Natural language:**
- "commit message 'fix auth bug' and push"
- "commit 'add new feature'"
- "amend last commit"
- "commit and push"

**Structured:**
```bash
python3 scripts/git_ops.py commit -m "message" --push
python3 scripts/git_ops.py commit --amend
```

### 2. Stash Operations
**Natural language:**
- "stash my changes"
- "stash with message 'work in progress'"
- "stash list"
- "apply stash"
- "pop stash 0"
- "show stash 1"
- "drop stash 2"
- "clear all stashes"

**Structured:**
```bash
python3 scripts/git_ops.py stash save -m "message"
python3 scripts/git_ops.py stash list
python3 scripts/git_ops.py stash apply 0
python3 scripts/git_ops.py stash pop
python3 scripts/git_ops.py stash drop 1
python3 scripts/git_ops.py stash clear
```

### 3. Search (Git Grep)
**Natural language:**
- "search for 'login' in code"
- "grep 'TODO'"
- "find 'password' in *.js files"
- "search for 'function' ignore case"

**Structured:**
```bash
python3 scripts/git_ops.py grep "pattern"
python3 scripts/git_ops.py grep "pattern" --file-pattern "*.py"
python3 scripts/git_ops.py grep "pattern" -i
```

### 4. Reset Operations
**Natural language:**
- "undo last commit" → `reset --soft HEAD~1`
- "unstage all files" → `reset HEAD`
- "hard reset to origin/main"
- "reset to abc123"

**Structured:**
```bash
python3 scripts/git_ops.py reset HEAD~1 --soft
python3 scripts/git_ops.py reset --hard origin/main
python3 scripts/git_ops.py reset HEAD --paths file1.txt file2.txt
```

### 5. Branch Operations
**Natural language:**
- "checkout main"
- "switch to feature/login"
- "create branch feature/new-ui"
- "create and checkout branch hotfix/bug-123"
- "delete branch feature/old locally"
- "delete remote branch feature/old"

**Structured:**
```bash
python3 scripts/git_ops.py checkout main
python3 scripts/git_ops.py checkout -b feature/new
python3 scripts/git_ops.py branch create feature/new
python3 scripts/git_ops.py branch delete old-branch --local
python3 scripts/git_ops.py branch delete old-branch --remote
```

### 6. Restore Files
**Natural language:**
- "restore config.py"
- "discard changes in package.json"
- "unstage index.html"

**Structured:**
```bash
python3 scripts/git_ops.py restore config.py
python3 scripts/git_ops.py restore config.py --staged
python3 scripts/git_ops.py restore config.py --source=HEAD~1
```

### 7. Show & Diff & Log
**Natural language:**
- "show last commit"
- "show abc123"
- "diff staged changes"
- "diff between abc123 and def456"
- "log for src/auth.py"
- "log with message 'fix'"
- "log author john"
- "show last 10 commits"

**Structured:**
```bash
python3 scripts/git_ops.py show HEAD
python3 scripts/git_ops.py diff --staged
python3 scripts/git_ops.py diff abc123 def456
python3 scripts/git_ops.py log -s "search term"
python3 scripts/git_ops.py log --author username -n 20
```

### 8. Cherry-pick
**Natural language:**
- "cherry-pick abc123"
- "cherry-pick abc123 def456 and push"
- "cherry-pick abc123 without commit"

**Structured:**
```bash
python3 scripts/git_ops.py cherry-pick abc123
python3 scripts/git_ops.py cherry-pick abc123 def456 --push
python3 scripts/git_ops.py cherry-pick abc123 --no-commit
```

### 9. Merge
**Natural language:**
- "merge feature/login"
- "merge main and push"
- "merge develop with no-ff"
- "merge feature/x squash"

**Structured:**
```bash
python3 scripts/git_ops.py merge feature/login
python3 scripts/git_ops.py merge main --push
python3 scripts/git_ops.py merge develop --no-ff
python3 scripts/git_ops.py merge feature/x --squash
```

### 10. Revert
**Natural language:**
- "revert abc123"
- "revert abc123 and def456 then push"
- "revert abc123 without commit"

**Structured:**
```bash
python3 scripts/git_ops.py revert abc123
python3 scripts/git_ops.py revert abc123 def456 --push
python3 scripts/git_ops.py revert abc123 --no-commit
```

### 11. Blame
**Natural language:**
- "blame src/auth.py"
- "who modified line 42 in config.js"

**Structured:**
```bash
python3 scripts/git_ops.py blame src/auth.py
python3 scripts/git_ops.py blame config.js --line-start 42 --line-end 50
```

### 12. Reflog
**Natural language:**
- "show reflog"
- "show last 50 operations"

**Structured:**
```bash
python3 scripts/git_ops.py reflog
python3 scripts/git_ops.py reflog -n 50
```

### 13. Tag Management
**Natural language:**
- "create tag v1.0.0"
- "create tag v1.0.0 with message 'release' and push"
- "list tags"
- "delete tag v0.9.0"
- "push tags"

**Structured:**
```bash
python3 scripts/git_ops.py tag create v1.0.0
python3 scripts/git_ops.py tag create v1.0.0 -m "Release notes" --push
python3 scripts/git_ops.py tag list
python3 scripts/git_ops.py tag delete v0.9.0
python3 scripts/git_ops.py tag push
```

### 14. Clean (Remove Untracked Files)
**Natural language:**
- "show untracked files" → dry-run (default)
- "remove untracked files"
- "clean directories"
- "clean including ignored files"

**Structured:**
```bash
python3 scripts/git_ops.py clean              # dry-run (preview)
python3 scripts/git_ops.py clean -f           # actually remove
python3 scripts/git_ops.py clean -f -d        # remove directories too
python3 scripts/git_ops.py clean -f -d -x     # include ignored files
```

### 15. Rebase (Including Interactive)
**Natural language:**
- "rebase onto main"
- "rebase last 3 commits interactively"
- "squash last 2 commits"
- "rebase main and push"

**Structured:**
```bash
python3 scripts/git_ops.py rebase main
python3 scripts/git_ops.py rebase main -i
python3 scripts/git_ops.py rebase HEAD~3 -i --push
```

### 16. Bisect (Binary Search for Bugs)
**Natural language:**
- "start bisect"
- "mark as good"
- "mark as bad"
- "bisect reset"

**Structured:**
```bash
python3 scripts/git_ops.py bisect start
python3 scripts/git_ops.py bisect good
python3 scripts/git_ops.py bisect bad abc123
python3 scripts/git_ops.py bisect reset
python3 scripts/git_ops.py bisect skip
```

### 17. Push
**Natural language:**
- "push"
- "force push"

**Structured:**
```bash
python3 scripts/git_ops.py push
python3 scripts/git_ops.py push --force
```

## Safety Features

The generated bash scripts **always**:
1. Verify it's inside a git repository
2. Check for detached HEAD state (blocks write operations)
3. Fetch from remote before sync/push operations
4. Use `--force-with-lease` instead of `--force` for safer force-pushing
5. Require confirmation (type "YES") for destructive operations:
   - Hard reset
   - Branch deletion
   - Stash clear/drop
   - Tag deletion
   - File cleaning

## Output Format

All commands output paste-ready bash code blocks:

````
```bash
set -euo pipefail
# ... preflight checks ...
# ... your git operations ...
```
````

You can copy and paste directly into your terminal.

## Environment Variables (Optional)

- `REMOTE` - Override default remote (default: `origin`)
- `CONFIRM_DESTRUCTIVE=0` - Skip destructive operation confirmations (use with caution!)

## Examples

```bash
# Commit and push workflow
python3 scripts/git_ops.py --from-text "commit 'implement user login' and push"

# Quick stash before switching branches
python3 scripts/git_ops.py --from-text "stash my work"
python3 scripts/git_ops.py --from-text "checkout main"

# Find all TODOs in Python files
python3 scripts/git_ops.py --from-text "search for 'TODO' in *.py"

# Undo last commit but keep changes
python3 scripts/git_ops.py --from-text "undo last commit"

# Cherry-pick specific commits
python3 scripts/git_ops.py --from-text "cherry-pick abc123 def456 and push"

# Interactive rebase to clean up commits
python3 scripts/git_ops.py --from-text "squash last 3 commits"

# Create and push a release tag
python3 scripts/git_ops.py --from-text "create tag v2.0.0 with message 'Major release' and push"
```

## Supported Languages

The NLP parser supports both **English** and **Chinese (繁體中文)** keywords:
- 日誌 (log)
- 作者 (author)
- 切換 (switch)
- 分支 (branch)
- 恢復 (restore)
- 丟棄 (discard)
- 搜尋/查找 (search/find)
- 強制 (hard)
- 保留更改 (soft)
- 包含未追蹤 (include untracked)
- 刪除 (delete)
- 列出 (list)
- 顯示 (show)

## Error Handling & Diagnostics

When a git-ops operation fails, the system automatically:

1. **Logs detailed error information** to `~/.git-ops/errors.jsonl`
   - Error code (e.g., `GIT_PUSH_REJECTED`, `GIT_MERGE_CONFLICT`)
   - Original error message
   - Suggested recovery steps
   - Timestamp and operation details

2. **Records operation history** in `~/.git-ops/notes/YYYY-MM-DD.md`
   - Timestamp of each operation
   - Operation status (✅ SUCCESS or ❌ FAILED)
   - Input command and details

3. **Provides AI-readable error reports** via `~/.git-ops/error_summary.md`
   - For quick diagnosis by AI assistants

### How AI Should Handle Errors

When git-ops reports an error:

```bash
# Query the last error
python3 scripts/query_errors.py --last

# Get JSON format for parsing
python3 scripts/query_errors.py --json

# View operation history
python3 scripts/operation_notes.py --list

# Get summary of today's operations
python3 scripts/operation_notes.py --summary
```

### Common Error Codes

| Code | Meaning | Common Fix |
|------|---------|-----------|
| `GIT_PUSH_REJECTED` | Remote has updates | `git pull --rebase && git push` |
| `GIT_MERGE_CONFLICT` | Merge conflict detected | Fix conflicts, then `git add .` and commit |
| `GIT_AUTHENTICATION_FAILED` | Auth issue | Check SSH key or credentials |
| `GIT_DETACHED_HEAD` | On detached HEAD | `git checkout <branch>` |
| `GIT_NO_CHANGES` | Nothing to commit | Make changes first |

For a complete list:
```bash
python3 scripts/error_handler.py --list
```

### Automatic Error Context Logging

When an error occurs, git-ops captures:
- Git status at time of error
- Current branch information
- Operation name that failed
- Exit code and error message

This is saved to `~/.git-ops/error_context.log` for debugging.

## Notes

- All authentication (SSH key or password) is handled interactively
- Git hooks are respected and will run normally
- Scripts are idempotent where possible
- Error messages include recovery instructions (e.g., how to abort a failed merge/rebase)
- All operations are logged for audit trail and debugging
