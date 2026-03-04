# Git-Ops Copilot Instructions

## Project Overview

Git-Ops is a natural language interface for Git operations. It converts conversational user requests into safe, executable Git commands. The project supports two deployment modes:
1. **Claude Code Skill** - AI-assisted mode where Claude invokes git-ops
2. **Standalone CLI tool** - Direct command-line usage with zero token cost

The system is bilingual (English/Chinese) and fully tested (34/34 tests passing).

## Architecture

### Core Components

**Main entry point:** `scripts/git_ops.py` (84K)
- Contains the `Plan` dataclass that models all Git operations
- `main()` function at line 1672 handles CLI parsing and command generation
- Translates natural language requests to structured Git commands
- Output is paste-ready bash scripts (designed for `| bash` or `-x` executor mode)

**Modular system:** 14 specialized Python modules in `scripts/`

| Module | Purpose |
|--------|---------|
| `config_manager.py` | YAML configuration loading & management |
| `branch_manager.py` | Branch analysis, cleanup, deletion |
| `workflow_engine.py` | Multi-step workflows (create-feature, commit-and-push) |
| `stash_manager.py` | Advanced stash operations (backup, apply_safe) |
| `conflict_detector.py` | Merge conflict prediction |
| `preflight_checker.py` | Pre-flight safety checks before execution |
| `team_rules_validator.py` | Commit format & branch naming validation |
| `llm_fallback.py` | Ollama-based fallback for unmatched patterns |
| `decision_engine.py` | Smart decision-making & state analysis |
| `pattern_analyzer.py` | Usage tracking & pattern suggestions |
| `usage_logger.py` | JSONL-based usage logging |
| `error_handler.py` | Error categorization & recovery suggestions |
| `operation_notes.py` | Metadata for operations |
| `query_errors.py` | Query validation & error reporting |

### Data Flow

```
User Input → git_ops.py (natural language parser)
  ↓
Plan dataclass (structured model)
  ↓
Specialized modules (config, preflight, conflict check, etc.)
  ↓
Bash command generation
  ↓
Output: paste-ready script or `-x` executor execution
```

### Configuration System

- User config: `~/.git-ops.yml` (optional)
- Example: `git-ops.example.yml`
- Supports: aliases, custom patterns, safety settings, team rules
- Loaded by `config_manager.py`

## Build, Test, and Lint Commands

### Test Scripts
```bash
# Full integration test (configuration + usage tracking)
bash test_integration.sh

# Configuration system test
bash test_config.sh

# Usage tracking test
bash test_usage_tracking.sh

# Run all tests (100% passing: 34/34)
bash test_config.sh && bash test_integration.sh && bash test_usage_tracking.sh
```

### Installation (for local development)
```bash
# Install as Claude Code Skill
bash install-as-skill.sh

# Install as standalone CLI tool
bash install.sh

# Install to specific project
bash install-to-project.sh

# Uninstall
bash uninstall.sh
```

### Running git-ops directly (for debugging)
```bash
# Test with natural language input
python3 scripts/git_ops.py --from-text "stash my changes"

# Generate subcommand directly
python3 scripts/git_ops.py subcommand stash save

# Initialize configuration
python3 scripts/git_ops.py --init-config
```

### Dependencies
```bash
# Install Python dependencies (only PyYAML for config file support)
pip install -r requirements.txt

# Verify Python version
python3 --version  # Requires 3.6+
```

## Key Conventions

### Plan Dataclass Design
The `Plan` class (lines 28-150+ in git_ops.py) groups Git operations into logical sections:
- **General:** `op` (operation type), `sync_mode` (rebase|merge|none), `push_mode` (push|nopush|lease)
- **Commit:** message, stage_mode, amend, allow_empty, commit_log, root_cause
- **Branch:** branch_name, branch_op (create|delete|checkout|analyze|cleanup|delete_merged)
- **Stash:** stash_op (save|list|apply|pop|drop|show|clear|list_detailed|backup|apply_safe)
- **Log/Show/Diff/Reset/Merge/Revert/Cherry-pick:** Operation-specific fields

When adding new features, extend the Plan class with new fields, then add parsing logic in `main()`.

### Operation Naming
Operations are referenced by simple names in the CLI but use verb-noun patterns internally:
- `stash` → stash_op="save"
- `checkout` → branch_op="checkout"
- `merge` → op="merge"

### Output Format
All command generation produces single paste-ready bash scripts. This is intentional:
- Supports `gops "..." | bash` (pipe mode)
- Supports `gops "..." -x -y` (executor mode with -x flag)
- No multi-step scripts or interactive prompts in core output

### Safety Design
Three safety layers:
1. **Preflight checks** (`preflight_checker.py`) - Detects detached HEAD, uncommitted changes, etc.
2. **Confirmation prompts** - Destructive operations ask for confirmation (when not using `-y` flag)
3. **Force-with-lease** - Uses `--force-with-lease` instead of `--force` by default

### Configuration Priority
1. User config: `~/.git-ops.yml` (highest)
2. Project config: `./.git-ops.yml`
3. Defaults: Hardcoded in code

### Testing Pattern
Tests use bash scripts that set up test environments, call git_ops.py, and verify bash command output. See `test_integration.sh` for the pattern.

### Error Handling
- `error_handler.py` categorizes errors and suggests recovery steps
- `query_errors.py` validates user queries upfront
- Designed to provide helpful messages without stopping execution

### Language Support
- Parser handles both English and Chinese keywords
- Configuration keys support both languages
- Output is always English bash commands

## Important Notes for Implementation

### When Modifying git_ops.py
1. Update the `Plan` dataclass first if adding new parameters
2. Add parsing logic in `main()` function
3. Check both English and Chinese keyword support in `parse_input_to_plan()`
4. Add integration test in `test_integration.sh`

### When Adding New Operations
1. Define Plan fields for the operation
2. Add `op` or `*_op` field value
3. Implement command generation in appropriate section of `main()`
4. Consider preflight checks (e.g., merge needs conflict detection)
5. Add safety confirmation for destructive ops

### Module Dependencies
- Core parsing: depends only on `argparse`, `re`, `shlex` (stdlib)
- Config: `config_manager.py` uses PyYAML
- Advanced features: Other modules have limited interdependencies
- **No external API calls** (standalone by design)

### Language Bilingual Support
Key patterns are translated to both English and Chinese in the parser:
- Check `parse_input_to_plan()` in git_ops.py for keyword mappings
- Both languages map to the same internal operation

## Documentation Structure

- **README.md** - Project overview, features, usage examples
- **SKILL.md** - Complete feature reference for Claude Code Skill
- **CONFIG_GUIDE.md** - Configuration system detailed guide
- **USAGE_TRACKING_GUIDE.md** - Usage analytics and optimization
- **QUICKSTART.txt / QUICKSTART_zh-TW.txt** - Quick reference cards (bilingual)
- **claude.md** - Claude-specific integration rules
- **ERROR_HANDLING_QUICK_REF.md** - Quick error reference
- **TROUBLESHOOTING.md** - Common issues and solutions
