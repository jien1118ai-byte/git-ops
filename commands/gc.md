---
description: "Git commit with auto-generated body (modified files + root cause)"
argument-hint: "<commit message>"
allowed-tools:
  - Bash
---

You are a Git commit helper. Execute the commit directly using Bash tools — do NOT generate scripts.

## Input

The user's commit message is: `$ARGUMENTS`

## Rules

1. **If `$ARGUMENTS` is empty**, ask the user what the commit message should be before proceeding. Do not guess.

2. **If `$ARGUMENTS` starts with `--no-log`**, strip the flag, use the remaining text as the commit title, and run a simple single-line commit:
   ```
   git add -A && git commit -m "<title>"
   ```
   Then stop — skip all body generation below.

3. **Otherwise**, follow the full flow below.

## Full Commit Flow

### Step 1 — Stage all changes

```bash
git add -A
```

### Step 2 — Collect diff stat

```bash
git diff --cached --stat
```

Save the output; you will embed it in the commit body.

### Step 3 — Root-cause analysis (fix/bug/hotfix only)

If the commit title (the first word before `(` or `:`) matches any of: `fix`, `bug`, `hotfix` (case-insensitive):

1. Run `git diff --cached` to get the full diff.
2. Analyze the diff yourself and draft a concise root-cause summary (1-2 sentences explaining **why** the bug happened, not what was changed).
3. Present your draft to the user like this:

> **Root Cause (auto-detected):**
> <your analysis>
>
> Accept this / edit / skip?

4. If the user accepts → use it. If the user provides alternative text → use that instead. If the user says skip → omit the root cause section.

If the title does NOT match those prefixes, skip this step entirely.

### Step 4 — Build commit message file

Create a temp file (e.g. `/tmp/gc-commit-msg.txt`) with this format:

```
<original commit title from $ARGUMENTS>

Modified Files:
<diff stat from Step 2>
```

If a root cause was collected in Step 3, append:

```

Root Cause:
<user's answer>
```

### Step 5 — Commit

```bash
git commit -F /tmp/gc-commit-msg.txt
```

### Step 6 — Clean up and confirm

Remove the temp file, then show the user the result of:

```bash
git log -1 --format="%h %s%n%n%b"
```

Print a short confirmation that the commit succeeded.
