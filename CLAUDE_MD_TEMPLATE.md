# Git-Ops Skill - Claude.md 範本

## 選項 1：簡潔版（推薦）

```markdown
## Git Operations Skill

When the user asks to perform Git operations using natural language, use the `git-ops` skill.

**Trigger scenarios:**
- User mentions Git commands in natural language (e.g., "stash my changes", "checkout main")
- User wants to commit, push, pull, merge, or any Git operation
- User asks about Git workflow automation

**How to use:**
```bash
# The skill accepts natural language and generates Git commands
gops "commit 'message' and push" | bash
gops "stash my changes" | bash
gops "checkout main and pull" | bash
```

**Features:**
- 17 Git operations supported (stash, commit, checkout, pull, push, grep, reset, etc.)
- Natural language parsing (supports English and Chinese)
- Configuration file support (aliases, custom patterns)
- Usage tracking and pattern learning
- Zero token cost (runs standalone)

**When NOT to use:**
- User wants to understand Git concepts (explain instead)
- User asks for Git command syntax only (provide direct command)
```

---

## 選項 2：詳細版（完整說明）

```markdown
## Git Operations - Natural Language Interface

### Overview
The `git-ops` skill provides a natural language interface to Git operations. It converts conversational requests into safe, executable Git commands.

### When to Use This Skill

**DO use when user wants to:**
- Execute Git operations via natural language
- Automate Git workflows
- Simplify complex Git command sequences
- Use custom aliases or patterns
- Track and optimize Git usage

**Examples of trigger phrases:**
- "stash my changes"
- "commit and push to origin"
- "checkout the main branch"
- "merge develop into current branch"
- "show me commits from last week"
- "搜尋包含 TODO 的程式碼" (Chinese support)

### How to Invoke

The skill is invoked automatically when users mention Git operations. Use the `gops` wrapper:

```bash
# Basic usage
gops "stash" | bash
gops "commit 'fix bug' and push" | bash
gops "checkout main and pull" | bash

# With configuration
gops "s" | bash  # Using alias (if configured)
gops "save work" | bash  # Using custom pattern

# Advanced operations
gops "search for TODO in *.py" | bash
gops "show commits since yesterday" | bash
gops "rebase main interactively" | bash
```

### Supported Operations (17 total)

**High Priority:**
- stash, commit, checkout, pull, push, grep

**Medium Priority:**
- reset, restore, merge, log, diff

**Advanced:**
- show, blame, tag, rebase, cherry-pick, bisect

### Configuration Features

Users can customize behavior via `~/.git-ops.yml`:

**Aliases** (shortcuts):
```yaml
aliases:
  s: stash
  m: checkout main
  cp: commit and push
```

**Custom Patterns** (workflows):
```yaml
custom_patterns:
  save work: stash with message 'WIP'
  sync main: checkout main, pull, checkout -
```

### Integration with Usage Tracking

The skill automatically:
1. Logs all operations to `~/.git-ops/usage.jsonl`
2. Analyzes patterns to suggest optimizations
3. Recommends personalized aliases
4. Helps users build efficient workflows

### Safety Features

- Preflight checks (validates Git repo, checks for uncommitted changes)
- Confirmation prompts for destructive operations
- Uses `--force-with-lease` instead of `--force`
- Detached HEAD warnings
- Dry-run mode available

### When NOT to Use

**Don't use when:**
- User asks "what is Git?" or wants to learn concepts → Provide explanation
- User asks "what's the syntax for git rebase?" → Give direct command syntax
- User is debugging Git itself → Use standard troubleshooting
- User wants to see raw Git output for analysis → Run git commands directly

### Examples in Context

**User:** "Can you stash my changes and checkout main?"
**Assistant:** *Invokes git-ops skill*
```bash
gops "stash and checkout main" | bash
```

**User:** "I need to commit with message 'fix login bug' and push"
**Assistant:** *Invokes git-ops skill*
```bash
gops "commit 'fix login bug' and push" | bash
```

**User:** "What does git rebase do?"
**Assistant:** *Explains concept, does NOT invoke skill*
"Git rebase is a way to integrate changes from one branch into another..."

### Quick Reference

- Documentation: See `SKILL.md`, `CONFIG_GUIDE.md`
- Setup: `python3 scripts/git_ops.py --init-config`
- Test: `gops "status" | bash`
- Customize: Edit `~/.git-ops.yml`
```

---

## 選項 3：超簡版（最小化）

```markdown
## Git-Ops Skill

Use when user requests Git operations in natural language.

**Trigger:** Git-related tasks (commit, push, stash, checkout, merge, etc.)

**Usage:** `gops "natural language command" | bash`

**Examples:**
- `gops "stash my changes" | bash`
- `gops "commit 'fix' and push" | bash`
- `gops "checkout main" | bash`

Supports 17 operations, bilingual (EN/ZH), configurable via `~/.git-ops.yml`.
```

---

## 選項 4：AI 優化版（最智能）

```markdown
## Git-Ops: Natural Language Git Interface

### AI Invocation Rules

**Automatically invoke this skill when:**
1. User request contains Git operation keywords: stash, commit, push, pull, checkout, merge, rebase, etc.
2. User describes a Git workflow in natural language
3. User asks to automate Git operations
4. User mentions branch operations, staging, or repository management

**Syntax to invoke:**
```bash
gops "<user's natural language request>" | bash
```

**Confidence threshold:**
- HIGH (>80%): User explicitly mentions Git operations → Invoke immediately
- MEDIUM (50-80%): User describes version control task → Suggest using git-ops
- LOW (<50%): Ambiguous intent → Ask for clarification

**Example triggers:**
| User Input | Confidence | Action |
|------------|-----------|---------|
| "stash my changes" | HIGH | Invoke: `gops "stash" \| bash` |
| "save my work" | MEDIUM | Ask: "Do you want to stash changes?" |
| "I need to commit" | HIGH | Invoke: `gops "commit" \| bash` |
| "save the file" | LOW | Don't invoke (not Git-related) |

### Skill Capabilities

**Natural Language Understanding:**
- English: "stash my changes and checkout main"
- Chinese: "儲存變更並切換到主分支"
- Mixed: "commit '修復 bug' and push"

**Supported Operations:** 17 Git operations (see SKILL.md)

**Smart Features:**
- Configuration: Aliases & custom patterns in `~/.git-ops.yml`
- Learning: Auto-tracks usage, suggests optimizations
- Safety: Preflight checks, confirmations for destructive ops

**Zero Cost:** Runs standalone, no API calls, no tokens consumed

### Integration Workflow

```
User Request → Detect Git Intent → Invoke git-ops → Generate Command → Execute
```

### Anti-patterns (When NOT to use)

❌ User asks "What is Git?"
✅ Explain Git concepts

❌ User wants Git command syntax reference
✅ Provide direct command

❌ User is learning Git
✅ Teach with examples

✅ User wants to execute Git operations
→ Use git-ops skill
```

---

## 使用建議

**放在 claude.md 的位置：**

```markdown
# Project: Git-Ops

## Overview
[專案描述...]

## Available Skills

### Git-Ops Skill
[選擇上面其中一個範本貼在這裡]

## Project Structure
[其他內容...]
```

**我的推薦：**
- 如果你希望 AI 自動判斷何時使用：選擇**選項 4（AI 優化版）**
- 如果你想要清晰簡潔的說明：選擇**選項 1（簡潔版）**
- 如果你需要完整參考：選擇**選項 2（詳細版）**

你想用哪一個？或者我可以根據你的需求客製化一個版本！