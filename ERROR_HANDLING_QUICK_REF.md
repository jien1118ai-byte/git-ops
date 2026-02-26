# Git-Ops Error Handling - Quick Reference Card

## 🚨 When Things Go Wrong

### For Users
```bash
# See what went wrong
python3 scripts/query_errors.py --last

# View today's operations
python3 scripts/operation_notes.py --list
```

### For AI Assistants
```bash
# Get structured error data
python3 scripts/query_errors.py --json

# Extract recovery steps
python3 scripts/error_handler.py GIT_PUSH_REJECTED
```

---

## 📋 Error Codes Cheat Sheet

| Code | Problem | Fix |
|------|---------|-----|
| **GIT_PUSH_REJECTED** | Remote has new commits | `git pull --rebase && git push` |
| **GIT_MERGE_CONFLICT** | Conflicting changes in files | Fix conflicts, `git add .`, commit |
| **GIT_AUTHENTICATION_FAILED** | SSH/credentials not working | Check SSH key or credentials |
| **GIT_DETACHED_HEAD** | On a commit, not a branch | `git checkout <branch>` |
| **GIT_NO_CHANGES** | Nothing to commit | Make changes first |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for complete list.

---

## 📁 Files Created/Modified

### New Files
- `scripts/error_handler.py` - Identifies and handles git errors
- `scripts/operation_notes.py` - Records operations to daily notes
- `scripts/query_errors.py` - Query error logs
- `TROUBLESHOOTING.md` - Complete troubleshooting guide

### Modified Files
- `scripts/usage_logger.py` - Enhanced with error logging
- `scripts/git_ops.py` - Added error handling to bash scripts
- `SKILL.md` - Added error handling documentation

---

## 🔍 Error Diagnostics

### Flow
```
Operation fails
    ↓
Error captured by trap handler
    ↓
Logged to ~/.git-ops/errors.jsonl
    ↓
AI/User queries: query_errors.py --json/--last
    ↓
Gets error code + recovery suggestion
    ↓
Executes recovery or informs user
```

### Key Directories
```
~/.git-ops/
├── errors.jsonl         - Detailed error log
├── error_summary.md     - AI-friendly summary
├── usage.jsonl          - All operations
├── error_context.log    - Error contexts
└── notes/               - Daily operation records
```

---

## 💡 Common AI Pattern

```python
# When an operation fails
try:
    result = execute_git_ops()
except OperationFailed:
    # Query what went wrong
    errors = get_last_error()
    error_code = errors['error_code']
    
    # Get recovery steps
    recovery = get_recovery_steps(error_code)
    
    # Either auto-recover or inform user
    if auto_recoverable(error_code):
        execute(recovery)
    else:
        inform_user(recovery)
```

---

## 📊 Statistics

```bash
# Error rate
python3 scripts/usage_logger.py --stats

# Today's summary
python3 scripts/operation_notes.py --summary

# All known errors
python3 scripts/error_handler.py --list
```

---

## 🎯 Best Practices

1. Always check errors after failures: `query_errors.py --last`
2. Review operation notes daily: `operation_notes.py --list`
3. Use safe force-push (automatic in git-ops)
4. Fetch before push: Always
5. Check conflicts before committing: `git diff`

---

**More info:** See [SKILL.md](SKILL.md) and [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
