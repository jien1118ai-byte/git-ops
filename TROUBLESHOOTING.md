# Git-Ops Troubleshooting Guide

This guide helps diagnose and resolve issues when using git-ops.

## Quick Diagnosis

### Step 1: Check Last Error

```bash
python3 scripts/query_errors.py --last
```

This shows the most recent error in human-readable format, including:
- What operation failed
- Error code and message
- Suggested recovery steps

### Step 2: Get JSON Details (for AI)

```bash
python3 scripts/query_errors.py --json
```

Returns structured error information for programmatic processing.

### Step 3: Review Operation History

```bash
python3 scripts/operation_notes.py --list
```

Shows recent operations and their status.

---

## Common Errors & Solutions

### GIT_PUSH_REJECTED
**Message:** Updates were rejected because the tip of your current branch is behind

**Cause:** Remote branch has changes you don't have locally

**Solution:**
```bash
git fetch origin
git rebase origin/<branch>
git push origin <branch>
```

Or use git-ops:
```bash
gops "pull with rebase" | bash
gops "push" | bash
```

---

### GIT_MERGE_CONFLICT
**Message:** CONFLICT (content) in file...

**Cause:** Files have conflicting changes

**Solution:**
1. Open the files with `<<<<<<` markers
2. Manually resolve conflicts
3. ```bash
   git add .
   git commit -m "resolve conflicts"
   ```

Or:
```bash
gops "merge <branch>" | bash
# Fix conflicts
git add .
git commit -m "resolve merge conflict"
```

---

### GIT_REBASE_CONFLICT
**Message:** CONFLICT during rebase, rebase --continue

**Cause:** Rebase encountered conflicting changes

**Solution:**
1. Fix conflicts in affected files
2. ```bash
   git add .
   git rebase --continue
   ```

Or resume with:
```bash
git rebase --abort  # to cancel
git rebase --continue  # to continue
```

---

### GIT_AUTHENTICATION_FAILED
**Message:** Permission denied (publickey) or Authentication failed

**Cause:** SSH key not configured or credentials invalid

**Solution:**

**For SSH:**
```bash
# Check if SSH key exists
ls -la ~/.ssh/

# Add key to agent
ssh-add ~/.ssh/id_rsa

# Test connection
ssh -T git@github.com
```

**For HTTPS:**
```bash
# Update credentials
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

### GIT_DETACHED_HEAD
**Message:** Cannot perform write operation in detached HEAD state

**Cause:** You're on a commit hash, not a branch

**Solution:**
```bash
# See what branch you want
git branch -a

# Switch to a branch
git checkout main
# or
git checkout feature/my-feature
```

---

### GIT_NO_CHANGES
**Message:** nothing to commit, working tree clean

**Cause:** You're trying to commit but there are no changes

**Solution:**
1. Make changes to files
2. Check status: `git status`
3. Then commit:
```bash
git add .
git commit -m "message"
```

---

### GIT_BRANCH_NOT_FOUND
**Message:** pathspec ... did not match any file(s) known to git

**Cause:** Branch name doesn't exist

**Solution:**
```bash
# List all branches
git branch -a

# Use correct branch name
git checkout <correct_branch>
```

---

### GIT_UNTRACKED_FILES_CONFLICT
**Message:** The following untracked working tree files would be overwritten

**Cause:** Switching branches would overwrite untracked files

**Solution:**
```bash
# Option 1: Stash untracked files
git stash -u

# Option 2: Delete untracked files
rm <filename>

# Then retry operation
```

---

### GIT_NOTHING_TO_REBASE
**Message:** No such ref: HEAD~1 or No changes, already up to date

**Cause:** No commits to rebase or already up to date

**Solution:**
```bash
# Check commit history
git log --oneline -5

# If up to date, nothing to do
```

---

## Advanced Diagnostics

### View All Errors

```bash
python3 scripts/query_errors.py --all
```

Shows the last 10 errors with timestamps.

### Get Error Context

```bash
cat ~/.git-ops/error_context.log
```

Shows git status and branch info at time of error.

### View Full Error Log

```bash
cat ~/.git-ops/errors.jsonl | jq .
```

Raw JSON log of all recorded errors.

### Check Operation Notes

```bash
cat ~/.git-ops/notes/$(date +%Y-%m-%d).md
```

View all operations performed today.

### Get Statistics

```bash
python3 scripts/usage_logger.py --stats
```

Show usage statistics including error rate.

---

## Prevention Tips

1. **Always fetch before push:**
   ```bash
   gops "fetch" | bash
   ```

2. **Check status before operations:**
   ```bash
   git status
   ```

3. **Use safe force-push:**
   - git-ops uses `--force-with-lease` by default (safe)
   - Never use `--force` alone

4. **Test on a feature branch:**
   - Create test branches for risky operations
   - Use `gops "checkout -b test/feature"` | bash`

5. **Review diffs before committing:**
   ```bash
   gops "diff staged" | bash
   ```

---

## Getting Help

### For AI Assistants

Query error and notes in JSON format:
```bash
# Get last error as JSON
python3 scripts/query_errors.py --json

# Generate error summary for reading
python3 scripts/usage_logger.py --stats
```

### For Users

1. Check error details: `python3 scripts/query_errors.py --last`
2. Review operation history: `python3 scripts/operation_notes.py --list`
3. Consult this guide for common issues
4. Check git documentation for complex scenarios

---

## File Locations

| File | Purpose |
|------|---------|
| `~/.git-ops/errors.jsonl` | Detailed error log (JSON) |
| `~/.git-ops/error_summary.md` | AI-readable error summary |
| `~/.git-ops/usage.jsonl` | All operations log |
| `~/.git-ops/notes/YYYY-MM-DD.md` | Daily operation notes |
| `~/.git-ops/error_context.log` | Error context snapshots |
| `~/.git-ops/patterns.txt` | Common patterns used |

---

## Support

For issues not covered here:
1. Check git documentation: `git help <command>`
2. Review the error code in error_handler.py
3. Check git-ops issue tracker if available
