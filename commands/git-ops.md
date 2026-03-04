---
description: "Natural language Git operations (25 ops, EN/ZH)"
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

## Step 1.5 — Commit context analysis (commit operations only)

**Only run this step if the request is a commit operation** (contains "commit", "提交", "送出", etc.)

### 1.5.1 Read the staged diff

```bash
git diff --staged
```

If the output is empty (nothing staged yet), run:

```bash
git diff HEAD
```

### 1.5.2 Analyze the diff

Read the diff output and determine:

- **commit_type**: one of `fix` / `feature` / `update` / `remove` / `docs` / `test` / `chore`
- **diff_summary**: one sentence describing what changed overall
- For **fix** commits additionally determine:
  - **root_cause**: what was the underlying cause of the bug (from reading the removed/changed lines)
  - **fix_method**: how was it fixed (from reading the added lines)

Keep root_cause and fix_method concise (1–2 sentences each).

### 1.5.3 Enrich the NLP input

If it is a **fix** commit and root_cause was identified, append it to the arguments before passing to git_ops.py:

```
<original ARGUMENTS> root cause: <root_cause>
```

For example:
- Original: `commit 'fix null pointer' and push`
- Enriched: `commit 'fix null pointer' and push root cause: login handler dereferences pointer without null check`

Save the enriched text as `ENRICHED_ARGS`. For non-fix commits use original `$ARGUMENTS`.

## Step 2 — Generate the bash script (print mode)

Run git_ops.py with `--from-text` using the enriched input:

```bash
python3 "$GOPS_PATH" --from-text "$ENRICHED_ARGS"
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

## Step 4.5 — Write commit context log (commit operations only)

**Only run this step if this was a commit operation and Step 3 succeeded.**

Append a JSON entry to `~/.git-ops/commit_context.jsonl`:

```bash
mkdir -p ~/.git-ops
cat >> ~/.git-ops/commit_context.jsonl << 'JSONEOF'
<json entry here>
JSONEOF
```

The JSON entry should contain:

```json
{
  "timestamp": "<ISO 8601 timestamp>",
  "message": "<commit message extracted from user input>",
  "type": "<commit_type from Step 1.5>",
  "diff_summary": "<one-sentence summary from Step 1.5>",
  "root_cause": "<root_cause or null>",
  "fix_method": "<fix_method or null>",
  "pushed": <true if push was requested, false otherwise>
}
```

## Important rules

- Always use `--from-text` to invoke git_ops.py. Never construct git commands manually.
- The generated scripts include their own safety checks (repo validation, detached HEAD detection, confirmation prompts for destructive ops). Trust them.
- If the user's request is ambiguous, prefer asking for clarification over guessing.
- Support both English and Traditional Chinese (繁體中文) input — pass it directly to git_ops.py which handles both.
- Step 1.5 and Step 4.5 are only for commit operations — skip them entirely for all other operations (pull, push, stash, etc.).
