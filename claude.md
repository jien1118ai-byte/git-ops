# Git-Ops Project

## Overview

Git-Ops is a natural language interface for Git operations. It converts conversational requests into safe, executable Git commands, eliminating the need for AI assistance in routine Git tasks.

**Key Benefits:**
- Zero token cost (runs standalone)
- 17 Git operations supported
- Bilingual support (English/Chinese)
- Configurable workflows
- Self-learning system

---

## Skills

### Git-Ops: Natural Language Git Interface

#### AI Invocation Rules

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

#### Skill Capabilities

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

#### Integration Workflow

```
User Request → Detect Git Intent → Invoke git-ops → Generate Command → Execute
```

#### Anti-patterns (When NOT to use)

❌ User asks "What is Git?"
✅ Explain Git concepts

❌ User wants Git command syntax reference
✅ Provide direct command

❌ User is learning Git
✅ Teach with examples

✅ User wants to execute Git operations
→ Use git-ops skill

---

## Project Structure

```
git-ops/
├── scripts/
│   ├── git_ops.py              # Main natural language parser
│   ├── config_manager.py       # Configuration system
│   ├── usage_logger.py         # Usage tracking
│   └── pattern_analyzer.py     # Pattern analysis & suggestions
├── git-ops.example.yml         # Configuration template
├── requirements.txt            # Dependencies (PyYAML)
├── SKILL.md                    # Complete skill documentation
├── CONFIG_GUIDE.md             # Configuration guide
├── USAGE_TRACKING_GUIDE.md     # Usage tracking guide
└── test_*.sh                   # Test scripts
```

---

## Setup

### Initial Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize configuration (optional but recommended)
python3 scripts/git_ops.py --init-config

# 3. Create alias in ~/.bashrc or ~/.zshrc
alias gops='python3 /path/to/git-ops/scripts/git_ops.py --from-text'
```

### Configuration (Optional)

Users can create `~/.git-ops.yml` to customize behavior:

```yaml
# Aliases for ultra-short commands
aliases:
  s: stash
  m: checkout main
  cp: commit and push

# Custom workflow patterns
custom_patterns:
  save work: stash with message 'WIP'
  sync main: checkout main, pull, checkout -

# Safety settings
safety:
  confirm_destructive: true
  confirm_force_push: true
```

---

## Usage Examples

### Basic Operations

```bash
# Stash changes
gops "stash" | bash
gops "stash with message 'work in progress'" | bash

# Branch operations
gops "checkout main" | bash
gops "create new branch feature/login" | bash

# Commit and push
gops "commit 'fix login bug'" | bash
gops "commit 'add feature' and push" | bash

# Pull with rebase
gops "pull with rebase" | bash
```

### Advanced Operations

```bash
# Search code
gops "search for TODO in *.py" | bash
gops "grep 'function' in src/" | bash

# View history
gops "show commits from last week" | bash
gops "log last 5 commits" | bash

# Interactive rebase
gops "rebase main interactively" | bash

# Cherry-pick
gops "cherry-pick abc123" | bash
```

### Chinese Support

```bash
gops "儲存我的變更" | bash
gops "切換到主分支" | bash
gops "提交 '修復錯誤' 並推送" | bash
gops "搜尋包含 TODO 的程式碼" | bash
```

### Using Aliases (with config)

```bash
# After setting up aliases in ~/.git-ops.yml
gops "s" | bash              # stash
gops "m" | bash              # checkout main
gops "cp 'fix bug'" | bash   # commit and push
```

---

## AI Assistant Guidelines

### When to Invoke Git-Ops

**YES - Invoke immediately:**
- "stash my changes"
- "commit and push"
- "checkout the develop branch"
- "merge feature into main"
- "search for TODO in the code"

**MAYBE - Ask for clarification:**
- "save my work" → Could be stash or file save
- "update the code" → Could be pull or edit
- "switch branches" → Ask which branch

**NO - Don't invoke:**
- "What is git stash?" → Explain the concept
- "How do I use git rebase?" → Provide tutorial
- "Show me the git log syntax" → Give command reference

### Response Format

When invoking git-ops, provide:
1. Brief explanation of what will happen
2. The git-ops command
3. What to expect

**Example:**
```markdown
I'll stash your changes with a custom message. Run this command:

```bash
gops "stash with message 'work in progress'" | bash
```

This will save your uncommitted changes and clean your working directory.
```

### Error Handling

If git-ops returns an error:
1. Show the error message
2. Explain what went wrong
3. Suggest a solution
4. Offer to run a different command

---

## Features Summary

### Core Features
- ✅ 17 Git operations supported
- ✅ Natural language parsing (EN/ZH)
- ✅ Safe command generation
- ✅ Preflight checks
- ✅ Confirmation prompts

### Advanced Features
- ✅ Configuration file support (YAML)
- ✅ Custom aliases
- ✅ Workflow patterns
- ✅ Usage tracking
- ✅ Pattern learning
- ✅ Personalized suggestions

### Safety Features
- ✅ Detached HEAD detection
- ✅ Uncommitted changes warnings
- ✅ Force-with-lease instead of force
- ✅ Destructive operation confirmations

---

## Documentation

- **SKILL.md** - Complete feature reference
- **CONFIG_GUIDE.md** - Configuration system guide
- **USAGE_TRACKING_GUIDE.md** - Usage tracking & optimization
- **QUICKSTART.txt** - Quick reference card

---

## Testing

All features are tested and verified:
- Core operations: 17/17 passing
- Configuration system: 9/9 passing
- Integration tests: 8/8 passing
- Total: 34/34 tests passing (100%)

---

## Performance

- **Token cost:** 0 (runs standalone)
- **Speed:** Instant (<100ms typical)
- **Dependencies:** Python 3.6+, PyYAML (optional)
- **Offline capable:** Yes

---

## Status

🟢 **Production Ready**

All features implemented, tested, and documented. Ready for daily use.

---

*Last updated: 2026-01-30*
