# Git-Ops: Standalone Natural Language Git Tool

**A standalone Python tool that converts natural language into safe, executable Git commands.**

🌟 **Zero AI dependencies** - Works completely offline without Claude Code or any AI service
⚡ **Zero token cost** - Run unlimited Git operations for free
🛡️ **Safety first** - Built-in preflight checks and confirmation prompts
🌐 **Bilingual** - Supports English and Chinese (繁體中文) commands

---

## Quick Start

### 1. Prerequisites

- Python 3.6+
- Git installed and configured
- No other dependencies required!

### 2. Basic Usage

```bash
# Navigate to the git-ops directory
cd /path/to/git-ops

# Use natural language
python3 scripts/git_ops.py --from-text "stash my changes"

# Execute the generated command
python3 scripts/git_ops.py --from-text "commit 'fix bug' and push" | bash
```

### 3. One-Line Setup (Recommended)

Add this to your `~/.bashrc` or `~/.zshrc`:

```bash
alias gops='python3 /home/janes/Projects/AI/git-ops/scripts/git_ops.py --from-text'
```

Then reload your shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

Now you can use it anywhere:
```bash
gops "stash and checkout main" | bash
gops "commit 'add feature' and push" | bash
```

---

## Supported Operations (17 Total)

### 🔄 Working Tree Management
- **Stash** - Save, list, apply, pop, drop, show, clear stashes
- **Reset** - Undo commits, unstage files (soft/mixed/hard)
- **Restore** - Discard changes in files
- **Clean** - Remove untracked files

### 🌿 Branch Operations
- **Checkout/Switch** - Switch branches or create new ones
- **Merge** - Merge branches with various strategies
- **Rebase** - Rebase branches, squash commits interactively

### 📝 Commit Management
- **Commit** - Create commits with messages
- **Cherry-pick** - Apply specific commits
- **Revert** - Revert commits safely
- **Amend** - Modify last commit

### 🔍 Information & Search
- **Log** - View commit history with filters
- **Show** - Display commit details
- **Diff** - Compare changes
- **Grep** - Search code in tracked files
- **Blame** - Find who modified each line
- **Reflog** - View operation history

### 🏷️ Tags & Advanced
- **Tag** - Create, list, delete, push tags
- **Bisect** - Binary search for bugs

---

## Usage Examples

### Natural Language Commands

#### Stash Operations
```bash
gops "stash my changes" | bash
gops "stash with message 'work in progress'" | bash
gops "stash list" | bash
gops "apply stash 0" | bash
gops "pop stash" | bash
```

#### Search & Inspect
```bash
gops "search for 'TODO' in *.py files" | bash
gops "grep 'login' ignore case" | bash
gops "blame src/auth.py" | bash
gops "show reflog" | bash
gops "show last 10 commits" | bash
```

#### Reset & Undo
```bash
gops "undo last commit" | bash
gops "unstage all files" | bash
gops "hard reset to origin/main" | bash
```

#### Branch Management
```bash
gops "checkout main" | bash
gops "create branch feature/new-ui" | bash
gops "create and checkout branch hotfix/bug-123" | bash
gops "delete branch old-feature locally" | bash
```

#### Commit & Push
```bash
gops "commit 'fix authentication bug' and push" | bash
gops "amend last commit" | bash
```

#### Advanced Operations
```bash
gops "cherry-pick abc123 def456" | bash
gops "merge develop with no-ff" | bash
gops "squash last 3 commits" | bash
gops "rebase main interactively" | bash
gops "create tag v1.0.0 with message 'release' and push" | bash
```

### Structured Commands (Alternative Syntax)

```bash
# Stash operations
python3 scripts/git_ops.py stash save -m "temporary work"
python3 scripts/git_ops.py stash list
python3 scripts/git_ops.py stash pop 0

# Search operations
python3 scripts/git_ops.py grep "TODO" --file-pattern "*.py"
python3 scripts/git_ops.py grep "pattern" -i

# Reset operations
python3 scripts/git_ops.py reset HEAD~1 --soft
python3 scripts/git_ops.py reset --hard origin/main

# Branch operations
python3 scripts/git_ops.py checkout main
python3 scripts/git_ops.py checkout -b feature/new

# Tag operations
python3 scripts/git_ops.py tag create v1.0.0 -m "Release"
python3 scripts/git_ops.py tag list

# Rebase
python3 scripts/git_ops.py rebase main -i
```

---

## Advanced Usage

### 1. Preview Before Execute

```bash
# Preview the generated command first
gops "commit 'fix bug' and push"

# Copy and paste to execute, or pipe to bash
gops "commit 'fix bug' and push" | bash
```

### 2. Save to Script

```bash
# Save for later review
gops "complex operation" > /tmp/git-command.sh
cat /tmp/git-command.sh  # Review
bash /tmp/git-command.sh # Execute
```

### 3. Conditional Execution

```bash
# Only execute if previous command succeeded
gops "checkout main" | bash && gops "pull" | bash
```

### 4. Use in Scripts

```bash
#!/bin/bash
# deploy.sh

GOPS="python3 /path/to/git-ops/scripts/git_ops.py --from-text"

# Automated deployment workflow
$GOPS "stash" | bash
$GOPS "checkout main" | bash
$GOPS "pull" | bash
$GOPS "checkout -" | bash
$GOPS "stash pop" | bash
$GOPS "merge main" | bash
```

### 5. Create Helper Function

Add to `~/.bashrc`:

```bash
# Auto-execute gops command
gopsrun() {
    python3 /path/to/git-ops/scripts/git_ops.py --from-text "$*" | bash
}

# Preview only
gopsview() {
    python3 /path/to/git-ops/scripts/git_ops.py --from-text "$*"
}
```

Usage:
```bash
gopsrun "commit 'fix' and push"    # Auto-execute
gopsview "hard reset to origin"    # Preview only
```

---

## Environment Variables

### REMOTE
Override the default remote (default: `origin`)

```bash
REMOTE=upstream gops "push" | bash
```

### CONFIRM_DESTRUCTIVE
Skip confirmation prompts (use with caution!)

```bash
CONFIRM_DESTRUCTIVE=0 gops "hard reset to HEAD~1" | bash
```

---

## Safety Features

All generated commands include:

1. ✅ **Git repository check** - Ensures you're in a git repo
2. ✅ **Detached HEAD detection** - Blocks write operations in detached state
3. ✅ **Pre-fetch for sync operations** - Always fetch before push/pull
4. ✅ **Safe force push** - Uses `--force-with-lease` instead of `--force`
5. ✅ **Confirmation prompts** - For destructive operations:
   - Hard reset
   - Branch deletion
   - Stash clear/drop
   - Tag deletion
   - File cleaning (unless dry-run)

---

## Chinese Language Support

The tool fully supports Chinese (繁體中文) keywords:

```bash
gops "顯示日誌" | bash
gops "作者為 john" | bash
gops "切換 main" | bash
gops "創建分支 feature/test" | bash
gops "恢復 config.py" | bash
gops "丟棄更改" | bash
gops "搜尋 TODO" | bash
```

Supported keywords:
- 日誌 (log)
- 作者 (author)
- 切換 (switch)
- 分支 (branch)
- 恢復 (restore)
- 丟棄 (discard)
- 搜尋/查找 (search/find)
- 強制 (hard)
- 保留更改 (soft)
- 刪除 (delete)
- 列出 (list)
- 顯示 (show)

---

## Integration Examples

### Git Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Run tests before commit
npm test || exit 1
```

The tool respects all git hooks automatically.

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
- name: Tag release
  run: |
    python3 scripts/git_ops.py --from-text "create tag v${{ github.run_number }}" | bash
```

### Cron Job

```bash
# Automated daily backup
0 2 * * * cd /path/to/repo && python3 /path/to/git-ops/scripts/git_ops.py --from-text "commit 'daily backup' and push" | bash
```

---

## Troubleshooting

### Command not found: python3

Try using `python` instead:
```bash
python scripts/git_ops.py --from-text "status"
```

### Permission denied

Make sure the script is readable:
```bash
chmod +r scripts/git_ops.py
```

### Not in a git repository

The tool only works inside git repositories. Navigate to your git repo first:
```bash
cd /path/to/your/git/repo
gops "status" | bash
```

### Confirmation prompts blocking automation

Use the environment variable to skip prompts:
```bash
CONFIRM_DESTRUCTIVE=0 gops "dangerous operation" | bash
```

**Warning**: Only use this in trusted automation scripts!

---

## Comparison with Other Tools

| Feature | git-ops | Plain Git | GUI Tools | AI Assistants |
|---------|---------|-----------|-----------|---------------|
| **Natural Language** | ✅ | ❌ | ❌ | ✅ |
| **Offline** | ✅ | ✅ | ✅ | ❌ |
| **Free** | ✅ | ✅ | Varies | Costs tokens |
| **Safety Checks** | ✅ | Manual | ✅ | Varies |
| **Scriptable** | ✅ | ✅ | ❌ | ❌ |
| **Learning Curve** | Low | Medium | Low | Low |
| **Speed** | Fast | Fast | Medium | Slow |

---

## Tips & Best Practices

### 1. Start with Preview
Always preview complex commands before executing:
```bash
gops "dangerous operation"  # Review first
# If looks good:
gops "dangerous operation" | bash
```

### 2. Use Descriptive Messages
```bash
# Good
gops "commit 'fix: resolve authentication timeout in login flow' and push"

# Not ideal
gops "commit 'fix' and push"
```

### 3. Leverage Aliases
Create shortcuts for common operations:
```bash
alias gs='gops "stash"'
alias gsu='gops "stash pop"'
alias gm='gops "checkout main"'
```

### 4. Combine with Standard Git
```bash
# Use git-ops for complex operations
gops "squash last 5 commits" | bash

# Use regular git for simple queries
git status
git log --oneline
```

### 5. Version Control Your Aliases
Add your git-ops aliases to your dotfiles repository for consistency across machines.

---

## Getting Help

### View all available operations
```bash
python3 scripts/git_ops.py --help
```

### View operation-specific help
```bash
python3 scripts/git_ops.py stash --help
python3 scripts/git_ops.py grep --help
python3 scripts/git_ops.py reset --help
```

### Examples
See `SKILL.md` for comprehensive examples of all 17 operations.

---

## License

This tool is part of the git-ops project. Use freely!

---

## Contributing

Found a bug or want to add a feature? The code is in `scripts/git_ops.py`.

Key functions to modify:
- `parse_operation_from_text()` - Add new natural language patterns
- `render()` - Add new command generation logic
- `main()` - Add new CLI subcommands

---

**Enjoy hassle-free, natural language Git operations! 🚀**
