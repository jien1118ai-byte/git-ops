"""
llm_fallback.py

Local Ollama LLM fallback for intent classification.
Called when all regex patterns fail to match user input.

Requires Ollama running locally: https://ollama.com
Setup: ollama pull qwen2.5:0.5b

Disabled by default. Enable in git-ops.yml:
  llm_fallback:
    enabled: true
"""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
from typing import Any, Dict, Optional


# All valid operations that the LLM is allowed to return
VALID_OPS = frozenset(
    {
        "commit",
        "push",
        "pull",
        "log",
        "show",
        "diff",
        "status",
        "stash",
        "branch",
        "checkout",
        "merge",
        "rebase",
        "reset",
        "revert",
        "cherry_pick",
        "restore",
        "clean",
        "tag",
        "blame",
        "reflog",
        "bisect",
        "grep",
        "preflight",
        "conflict_detect",
        "conflict_resolve",
        "decide",
        "validate_commit",
        "validate_branch",
        "validate_quality",
        "validate_rules",
        "workflow",
    }
)

# Allowed parameters per operation with their expected types.
# 'str', 'int', 'bool', 'list' are the supported types.
VALID_PARAMS: Dict[str, Dict[str, str]] = {
    "commit": {"message": "str", "push_mode": "str", "amend": "bool"},
    "push": {"push_mode": "str", "force": "bool"},
    "pull": {"pull_mode": "str", "pull_branch": "str", "pull_force": "bool"},
    "log": {
        "log_path": "str",
        "log_search": "str",
        "log_max_count": "int",
        "log_graph": "bool",
        "log_all_branches": "bool",
    },
    "show": {"show_target": "str"},
    "diff": {"diff_targets": "list", "diff_staged": "bool"},
    "stash": {"stash_op": "str", "stash_message": "str", "stash_index": "int"},
    "branch": {"branch_op": "str", "branch_name": "str"},
    "checkout": {"checkout_target": "str", "checkout_create": "bool"},
    "merge": {"merge_source": "str", "merge_no_ff": "bool", "merge_squash": "bool"},
    "rebase": {"rebase_target": "str", "rebase_interactive": "bool"},
    "reset": {"reset_mode": "str", "reset_target": "str"},
    "revert": {"commits": "list", "no_commit": "bool"},
    "cherry_pick": {"commits": "list", "commit_range": "str", "no_commit": "bool"},
    "restore": {"restore_paths": "list", "restore_staged": "bool"},
    "clean": {
        "clean_dry_run": "bool",
        "clean_force": "bool",
        "clean_directories": "bool",
    },
    "tag": {"tag_op": "str", "tag_name": "str", "tag_message": "str"},
    "blame": {"blame_path": "str"},
    "reflog": {"reflog_max_count": "int"},
    "grep": {
        "grep_pattern": "str",
        "grep_file_pattern": "str",
        "grep_ignore_case": "bool",
    },
    "bisect": {"bisect_op": "str"},
    "conflict_detect": {"conflict_target": "str"},
    "conflict_resolve": {"conflict_file": "str"},
    "decide": {"decision_goal": "str"},
    "validate_commit": {"validate_message": "str"},
    "workflow": {"workflow_op": "str", "workflow_name": "str"},
}

# Shell metacharacters that must never appear in string parameters
_SHELL_DANGEROUS = re.compile(r"[;&|\\`$(){}]")

SYSTEM_PROMPT = """\
You are a Git operation classifier. Given a user's natural language request, \
identify the Git operation and parameters.

Reply with JSON only: {"op": "<operation>", "params": {<optional params>}}

Valid operations:
  commit    - commit changes (params: message, push_mode, amend)
  push      - push to remote (params: push_mode, force)
  log       - show commit log (params: log_path, log_search, log_max_count)
  show      - show commit details (params: show_target)
  diff      - show differences (params: diff_targets, diff_staged)
  stash     - stash ops (stash_op=save|list|apply|pop|drop|show|clear)
  branch    - branch ops (branch_op=create|delete|analyze|cleanup)
  checkout  - switch branch (params: checkout_target, checkout_create)
  merge     - merge branch (params: merge_source)
  rebase    - rebase (params: rebase_target)
  reset     - reset changes (params: reset_mode=soft|mixed|hard, reset_target)
  revert    - revert commit (params: commits)
  cherry_pick - cherry-pick commit (params: commits)
  restore   - restore files (params: restore_paths, restore_staged)
  clean     - clean working directory (params: clean_dry_run, clean_force)
  tag       - tag ops (tag_op=create|list|delete|push, tag_name)
  blame     - show file blame (params: blame_path)
  reflog    - show reflog (params: reflog_max_count)
  grep      - search code (params: grep_pattern, grep_file_pattern, grep_ignore_case)
  bisect    - bisect operations (params: bisect_op=start|good|bad|reset|skip)
  preflight - repository health check
  conflict_detect  - detect merge conflicts (params: conflict_target)
  conflict_resolve - resolve conflicts (params: conflict_file)
  decide    - recommend next action (params: decision_goal)
  validate_commit  - validate commit message (params: validate_message)
  validate_branch  - validate branch name
  validate_quality - run quality checks
  validate_rules   - validate all team rules
  workflow  - run workflow template (params: workflow_op=run|list, workflow_name)
  status    - show repository status

Examples:
  "save my current work" → {"op": "stash", "params": {"stash_op": "save"}}
  "把修改存起來" → {"op": "stash", "params": {"stash_op": "save"}}
  "show me the last 5 commits" → {"op": "log", "params": {"log_max_count": 5}}
  "switch to develop" → {"op": "checkout", "params": {"checkout_target": "develop"}}
  "建立新分支 feature/login" → {"op": "checkout",
    "params": {"checkout_target": "feature/login"}}
  "what should I do" → {"op": "decide", "params": {}}
  "搜尋 TODO" → {"op": "grep", "params": {"grep_pattern": "TODO"}}
"""


def _call_ollama(text: str, config: Dict[str, Any]) -> Optional[str]:
    """POST to local Ollama API. Returns raw response text or None."""
    base_url = config.get("base_url", "http://localhost:11434")
    model = config.get("model", "qwen2.5:3b")
    timeout = config.get("timeout", 2)

    payload = json.dumps(
        {
            "model": model,
            "prompt": text,
            "system": SYSTEM_PROMPT,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 128,
            },
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return str(body.get("response", ""))
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        OSError,
        json.JSONDecodeError,
        KeyError,
    ):
        return None


def _sanitize_string(value: str, max_len: int = 200) -> Optional[str]:
    """Validate and sanitize a string parameter value."""
    if not isinstance(value, str):
        return None
    if len(value) > max_len:
        return None
    if _SHELL_DANGEROUS.search(value):
        return None
    return value


def _validate_response(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    """Parse and validate LLM JSON response.

    Returns {'op': str, 'params': dict} or None.
    """
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    op = data.get("op")
    if not isinstance(op, str) or op not in VALID_OPS:
        return None

    # "status" from LLM is meaningless — same as no-match
    if op == "status":
        return None

    raw_params = data.get("params", {})
    if not isinstance(raw_params, dict):
        raw_params = {}

    allowed = VALID_PARAMS.get(op, {})
    params: Dict[str, Any] = {}

    for key, expected_type in allowed.items():
        if key not in raw_params:
            continue
        val = raw_params[key]

        if expected_type == "str":
            sanitized = _sanitize_string(val)
            if sanitized is not None:
                params[key] = sanitized

        elif expected_type == "int":
            try:
                params[key] = int(val)
            except (ValueError, TypeError):
                pass

        elif expected_type == "bool":
            if isinstance(val, bool):
                params[key] = val

        elif expected_type == "list":
            if isinstance(val, list) and len(val) <= 10:
                clean = []
                for item in val:
                    s = _sanitize_string(str(item), max_len=40)
                    if s is not None:
                        clean.append(s)
                if clean:
                    params[key] = clean

    return {"op": op, "params": params}


def llm_parse_intent(text: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Classify user intent via local Ollama LLM.

    Args:
        text: User's natural language input.
        config: The llm_fallback config section from git-ops.yml.

    Returns:
        {'op': str, 'params': dict} if classification succeeded, else None.
    """
    if not config.get("enabled", False):
        return None

    raw = _call_ollama(text, config)
    return _validate_response(raw)
