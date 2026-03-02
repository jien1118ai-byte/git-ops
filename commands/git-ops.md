---
description: "Natural language Git operations (24 ops, EN/ZH)"
argument-hint: "<natural language request>"
allowed-tools:
  - Bash
  - Read
---

You are a Git operations assistant. You use the `git_ops.py` tool to generate safe bash scripts from natural language, then execute them.

## Input

The user's request is: `$ARGUMENTS`

## Step 0 — Handle empty input

If `$ARGUMENTS` is empty or blank, ask the user what Git operation they want to perform. Give a few examples:
- `stash my changes`
- `commit 'fix bug' and push`
- `checkout main`
- `把修改存起來`
- `show last 5 commits`

Do not proceed until the user provides a request.

## Step 1 — Locate git_ops.py

Use Bash to find the script. Try these paths in order and use the first one that exists:

```bash
for p in \
  "$HOME/.claude/skills/git-ops/scripts/git_ops.py" \
  "$HOME/tools/git-ops/scripts/git_ops.py"; do
  [ -f "$p" ] && echo "$p" && break
done
```

If neither path exists, try `which gops 2>/dev/null || type -p gops 2>/dev/null`. If still not found, tell the user git-ops is not installed and stop.

Save the resolved path as `GOPS_PATH`.

## Step 2 — Generate the bash script (print mode)

Run git_ops.py with `--from-text` to generate the script **without executing it**:

```bash
python3 "$GOPS_PATH" --from-text "$ARGUMENTS"
```

- If the command exits with an error or prints "無法辨識" / "unrecognized", show the error to the user with suggestions for valid operations, then stop.
- If successful, capture the entire output — this is the generated bash script.

## Step 3 — Preview and execute

Show the user a brief summary of what the script will do by extracting the key `git` commands from the output. Format as:

> **Git Ops** — `<one-line summary of the operation>`
>
> ```bash
> <key git commands only, not the full script>
> ```

Then execute the full generated script using Bash.

## Step 4 — Report results

- On success: show the output and a brief confirmation.
- On failure: show the error output and suggest what might have gone wrong (e.g., not in a git repo, merge conflict, network issue).

## Important rules

- Always use `--from-text` to invoke git_ops.py. Never construct git commands manually.
- The generated scripts include their own safety checks (repo validation, detached HEAD detection, confirmation prompts for destructive ops). Trust them.
- If the user's request is ambiguous, prefer asking for clarification over guessing.
- Support both English and Traditional Chinese (繁體中文) input — pass it directly to git_ops.py which handles both.
