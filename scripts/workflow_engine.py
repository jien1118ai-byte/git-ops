#!/usr/bin/env python3
"""
workflow_engine.py

Multi-step workflow templates for git-ops.
Generates a single paste-ready bash script from named workflows composed of
ordered steps.  Ships with 3 built-in workflows; users can add more via YAML.

Usage:
  Integrated: python3 git_ops.py --from-text "workflow create-feature user-auth"
  Standalone: python3 workflow_engine.py run create_feature --param name=user-auth
              python3 workflow_engine.py list
"""

from __future__ import annotations

import shlex
from typing import Any, Dict, List, Optional


def _q(s: str) -> str:
    return shlex.quote(s)


class WorkflowEngine:
    """Generates bash scripts that execute multi-step workflow templates."""

    DEFAULT_CONFIG: Dict[str, Any] = {
        "stop_on_error": True,
        "show_step_numbers": True,
        "verbose": False,
        "definitions": {},
        "overrides": {},
    }

    DEFAULT_WORKFLOWS: Dict[str, Any] = {
        "create_feature": {
            "description": "Create a new feature branch from an up-to-date base",
            "params": [
                {"name": "name", "required": True, "prompt": "Feature branch name"},
            ],
            "steps": [
                {
                    "action": "checkout",
                    "branch": "develop",
                    "pull": True,
                    "label": "Switch to develop and pull latest",
                },
                {
                    "action": "create_branch",
                    "branch": "feature/{name}",
                    "label": "Create feature branch",
                },
                {
                    "action": "checkout",
                    "branch": "feature/{name}",
                    "label": "Switch to new feature branch",
                },
            ],
        },
        "commit_and_push": {
            "description": "Stage, validate, commit, sync, and push in one go",
            "params": [
                {"name": "message", "required": False, "prompt": "Commit message"},
            ],
            "steps": [
                {"action": "preflight", "label": "Run preflight checks"},
                {"action": "validate_rules", "label": "Validate team rules"},
                {"action": "stage", "mode": "all", "label": "Stage all changes"},
                {"action": "commit", "message": "{message}", "label": "Create commit"},
                {"action": "fetch", "label": "Fetch remote updates"},
                {"action": "detect_conflicts", "label": "Check for conflicts"},
                {"action": "push", "label": "Push to remote"},
            ],
        },
        "ready_for_pr": {
            "description": "Validate code quality and prepare a PR summary",
            "params": [],
            "steps": [
                {"action": "validate_rules", "label": "Validate team rules"},
                {
                    "action": "run_command",
                    "command": "npm test",
                    "required": False,
                    "label": "Run tests",
                },
                {
                    "action": "run_command",
                    "command": "npm run lint",
                    "required": False,
                    "label": "Run linter",
                },
                {
                    "action": "run_command",
                    "command": "npm run build",
                    "required": False,
                    "label": "Run build",
                },
                {
                    "action": "generate_pr_description",
                    "label": "Generate PR description",
                },
                {
                    "action": "show_checklist",
                    "items": [
                        "All tests pass",
                        "Linter has no errors",
                        "Build succeeds",
                        "Branch is up to date with base",
                        "PR description is accurate",
                    ],
                    "label": "PR checklist",
                },
            ],
        },
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config: Dict[str, Any] = {**self.DEFAULT_CONFIG}
        if config:
            self.config.update(config)

        # Merge built-in + user-defined workflows
        self.workflows: Dict[str, Any] = {}
        for name, defn in self.DEFAULT_WORKFLOWS.items():
            self.workflows[name] = defn

        # Apply overrides to built-in workflows
        overrides = self.config.get("overrides", {}) or {}
        for name, override in overrides.items():
            wf_name = name.replace("-", "_")
            if wf_name in self.workflows:
                if "steps" in override:
                    self.workflows[wf_name]["steps"] = override["steps"]
                if "description" in override:
                    self.workflows[wf_name]["description"] = override["description"]
                if "params" in override:
                    self.workflows[wf_name]["params"] = override["params"]

        # Add user-defined workflows
        definitions = self.config.get("definitions", {}) or {}
        for name, defn in definitions.items():
            wf_name = name.replace("-", "_")
            self.workflows[wf_name] = defn

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #

    def generate_script(self, name: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate a complete bash script for the named workflow."""
        wf_name = name.replace("-", "_")

        if wf_name not in self.workflows:
            return self._unknown_workflow_script(wf_name)

        wf = self.workflows[wf_name]
        parts: List[str] = []

        parts.append(self._header(wf_name, wf.get("description", "")))
        parts.append(self._params_block(wf.get("params", []), params))
        parts.append(self._step_helpers())

        stop_on_error = self.config.get("stop_on_error", True)
        show_numbers = self.config.get("show_step_numbers", True)

        steps = wf.get("steps", [])
        total = len(steps)

        for i, step in enumerate(steps, 1):
            action = step.get("action", "run_command")
            label = step.get("label", action)
            num_prefix = f"[{i}/{total}]" if show_numbers else "-"

            parts.append(f'\necho ""\necho "{num_prefix} {label}"')
            parts.append('echo "────────────────────────────────────────"')
            parts.append("STEP_FAILED=0\n")

            handler = getattr(self, f"_step_{action}", None)
            if handler:
                parts.append(handler(step))
            else:
                parts.append(self._step_run_command(step))

            parts.append(self._step_error_check(label, stop_on_error))

        parts.append(self._footer(wf_name))
        return "\n".join(parts)

    def generate_list_script(self) -> str:
        """Generate a bash script that lists all available workflows."""
        parts: List[str] = []
        parts.append(
            r"""# ---- workflow list begin ----
echo ""
echo "========================================"
echo "  AVAILABLE WORKFLOWS"
echo "========================================"
echo ""
"""
        )

        for name, wf in sorted(self.workflows.items()):
            display = name.replace("_", "-")
            desc = wf.get("description", "")
            params = wf.get("params", [])
            param_names = [p["name"] for p in params]
            param_str = " ".join(f"<{n}>" for n in param_names) if param_names else ""

            parts.append(f'echo "  {display}  {param_str}"')
            if desc:
                parts.append(f'echo "    {desc}"')

            steps = wf.get("steps", [])
            if steps:
                step_labels = [s.get("label", s.get("action", "?")) for s in steps]
                parts.append(f'echo "    Steps: {" -> ".join(step_labels)}"')
            parts.append('echo ""')

        parts.append(
            r"""echo "Usage:"
echo '  gops "workflow <name>"'
echo '  gops "workflow <name> <param>"'
echo '  gops "workflow list"'
echo ""
echo "========================================"
"""
        )
        return "\n".join(parts)

    # ------------------------------------------------------------------ #
    #  Script scaffolding                                                 #
    # ------------------------------------------------------------------ #

    def _header(self, name: str, description: str) -> str:
        display = name.replace("_", "-")
        return f"""# ---- workflow '{display}' begin ----
echo ""
echo "========================================"
echo "  WORKFLOW: {display}"
echo "  {description}"
echo "========================================"
echo ""

WORKFLOW_ERRORS=0
"""

    def _footer(self, name: str) -> str:
        display = name.replace("_", "-")
        return f"""
echo ""
if [ "$WORKFLOW_ERRORS" -eq 0 ]; then
  echo "[ok] Workflow '{display}' completed successfully"
else
  echo "[!!] Workflow '{display}' completed with $WORKFLOW_ERRORS error(s)"
fi
echo "========================================"
# ---- workflow '{display}' end ----
"""

    def _params_block(
        self, param_defs: List[Dict[str, Any]], provided: Optional[Dict[str, Any]] = None
    ) -> str:
        """Emit bash that declares WORKFLOW_PARAMS and prompts for missing ones."""
        provided = provided or {}
        lines: List[str] = ["# -- Workflow parameters --", "declare -A WORKFLOW_PARAMS"]

        for p in param_defs:
            pname = p["name"]
            required = p.get("required", False)
            prompt_text = p.get("prompt", pname)

            if pname in provided:
                lines.append(f"WORKFLOW_PARAMS[{pname}]={_q(provided[pname])}")
            else:
                lines.append(f'if [ -z "${{WORKFLOW_PARAMS[{pname}]+x}}" ]; then')
                if required:
                    lines.append(
                        f'  read -r -p "{prompt_text}: " WORKFLOW_PARAMS[{pname}]'
                    )
                    lines.append(f'  if [ -z "${{WORKFLOW_PARAMS[{pname}]}}" ]; then')
                    lines.append(
                        f"    echo \"[!!] Required parameter '{pname}' not provided\""
                    )
                    lines.append("    exit 1")
                    lines.append("  fi")
                else:
                    lines.append(
                        f'  read -r -p "{prompt_text} (optional, Enter to skip): " WORKFLOW_PARAMS[{pname}]'  # noqa: E501
                    )
                lines.append("fi")

        lines.append("")
        return "\n".join(lines)

    def _step_helpers(self) -> str:
        return r"""# -- Step helpers --
workflow_resolve_param() {
  local val="$1"
  for key in "${!WORKFLOW_PARAMS[@]}"; do
    val="${val//\{$key\}/${WORKFLOW_PARAMS[$key]}}"
  done
  echo "$val"
}
"""

    def _step_error_check(self, label: str, stop_on_error: bool) -> str:
        if stop_on_error:
            return f"""
if [ "$STEP_FAILED" -ne 0 ]; then
  WORKFLOW_ERRORS=$((WORKFLOW_ERRORS + 1))
  echo ""
  echo "[!!] Step failed: {label}"
  read -r -p "Continue workflow? [y/N]: " STEP_CONT
  case "$STEP_CONT" in
    [yY]*) echo "Continuing..." ;;
    *) echo "Workflow aborted."; exit 1 ;;
  esac
fi
"""
        else:
            return f"""
if [ "$STEP_FAILED" -ne 0 ]; then
  WORKFLOW_ERRORS=$((WORKFLOW_ERRORS + 1))
  echo "  [!] Step had errors: {label} (continuing)"
fi
"""

    def _unknown_workflow_script(self, name: str) -> str:
        display = name.replace("_", "-")
        available = ", ".join(n.replace("_", "-") for n in sorted(self.workflows))
        return f"""echo "[!!] Unknown workflow: {display}"
echo ""
echo "Available workflows: {available}"
echo ""
echo "Usage:"
echo '  gops "workflow <name>"'
echo '  gops "workflow list"'
"""

    # ------------------------------------------------------------------ #
    #  Step action handlers — each returns a bash fragment                #
    # ------------------------------------------------------------------ #

    def _step_checkout(self, step: Dict[str, Any]) -> str:
        branch = step.get("branch", "main")
        pull = step.get("pull", False)
        lines: List[str] = []

        lines.append(f"CHECKOUT_BRANCH=$(workflow_resolve_param {_q(branch)})")
        lines.append('if git checkout "$CHECKOUT_BRANCH" 2>/dev/null; then')
        lines.append('  echo "  Switched to $CHECKOUT_BRANCH"')
        if pull:
            lines.append("  if has_upstream; then")
            lines.append(
                '    if git pull --rebase "$REMOTE" "$CHECKOUT_BRANCH" 2>/dev/null; then'  # noqa: E501
            )
            lines.append('      echo "  Pulled latest changes"')
            lines.append("    else")
            lines.append('      echo "  [!] Pull failed"')
            lines.append("      STEP_FAILED=1")
            lines.append("    fi")
            lines.append("  fi")
        lines.append("else")
        lines.append('  echo "  [!] Failed to checkout $CHECKOUT_BRANCH"')
        lines.append("  STEP_FAILED=1")
        lines.append("fi")
        return "\n".join(lines)

    def _step_create_branch(self, step: Dict[str, Any]) -> str:
        branch = step.get("branch", "feature/{name}")
        return f"""NEW_BRANCH=$(workflow_resolve_param {_q(branch)})
if git checkout -b "$NEW_BRANCH" 2>/dev/null; then
  echo "  Created and switched to $NEW_BRANCH"
else
  echo "  [!] Failed to create branch $NEW_BRANCH"
  STEP_FAILED=1
fi"""

    def _step_preflight(self, step: Dict[str, Any]) -> str:
        return r"""# Preflight check
try_preflight() {
  PREFLIGHT_WARNINGS=0
  PREFLIGHT_ERRORS=0
  echo "  Branch: $BR"
  git status --short 2>/dev/null
  STASH_COUNT=$(git stash list 2>/dev/null | wc -l | tr -d ' ')
  if [ "$STASH_COUNT" -gt 0 ]; then
    echo "  Stashes: $STASH_COUNT"
  fi
  echo "  [ok] Preflight passed"
}
if ! try_preflight; then
  STEP_FAILED=1
fi"""

    def _step_validate_rules(self, step: Dict[str, Any]) -> str:
        return r"""# Validate team rules (basic)
BRANCH_PATTERN='^(feature|fix|hotfix|release|chore)/[a-z0-9._-]+$'
if [ "$BR" = "main" ] || [ "$BR" = "master" ] || [ "$BR" = "develop" ]; then
  echo "  [ok] Branch '$BR' is exempt from naming rules"
elif [[ "$BR" =~ $BRANCH_PATTERN ]]; then
  echo "  [ok] Branch name '$BR' matches convention"
else
  echo "  [!] Branch name '$BR' does not match convention"
  # Not fatal — just a warning
fi"""

    def _step_stage(self, step: Dict[str, Any]) -> str:
        mode = step.get("mode", "all")
        if mode == "all":
            return r"""if git add -A 2>/dev/null; then
  STAGED=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
  echo "  Staged $STAGED file(s)"
  if [ "$STAGED" -eq 0 ]; then
    echo "  [!] Nothing to stage"
    STEP_FAILED=1
  fi
else
  echo "  [!] git add failed"
  STEP_FAILED=1
fi"""
        elif mode == "patch":
            return r"""echo "  Interactive patch staging..."
git add -p
echo "  [ok] Patch staging done"
"""
        elif mode == "interactive":
            return r"""echo "  Interactive staging..."
git add -i
echo "  [ok] Interactive staging done"
"""
        else:  # keep
            return r"""echo "  stage_mode=keep (no git add)"
if git diff --cached --quiet 2>/dev/null; then
  echo "  [!] No staged changes"
  STEP_FAILED=1
fi"""

    def _step_commit(self, step: Dict[str, Any]) -> str:
        message_template = step.get("message", "{message}")
        return f"""COMMIT_MSG=$(workflow_resolve_param {_q(message_template)})
if [ -z "$COMMIT_MSG" ] || [ "$COMMIT_MSG" = "{message_template}" ]; then
  read -r -p "Commit message: " COMMIT_MSG
  if [ -z "$COMMIT_MSG" ]; then
    echo "  [!] Empty commit message"
    STEP_FAILED=1
  fi
fi
if [ "$STEP_FAILED" -eq 0 ]; then
  if git commit -m "$COMMIT_MSG" 2>/dev/null; then
    echo "  [ok] Committed: $COMMIT_MSG"
  else
    echo "  [!] Commit failed"
    STEP_FAILED=1
  fi
fi"""

    def _step_fetch(self, step: Dict[str, Any]) -> str:
        return r"""if git fetch "$REMOTE" 2>/dev/null; then
  echo "  [ok] Fetched from $REMOTE"
else
  echo "  [!] Fetch failed"
  STEP_FAILED=1
fi"""

    def _step_detect_conflicts(self, step: Dict[str, Any]) -> str:
        return r"""# Check for conflicts with remote
if has_upstream; then
  BEHIND=$(git rev-list --count "$REMOTE/$BR..HEAD" 2>/dev/null || echo "0")
  AHEAD=$(git rev-list --count "HEAD..$REMOTE/$BR" 2>/dev/null || echo "0")
  if [ "${BEHIND:-0}" -gt 0 ]; then
    echo "  [!] Remote has new commits — rebase recommended before push"
    echo "  Behind by: $BEHIND commit(s)"
  else
    echo "  [ok] No upstream conflicts detected"
  fi
else
  echo "  [ok] No upstream to check (new branch)"
fi"""

    def _step_push(self, step: Dict[str, Any]) -> str:
        return r"""if push_with_upstream_if_needed 2>/dev/null; then
  echo "  [ok] Pushed to $REMOTE/$BR"
else
  echo "  [!] Push failed"
  STEP_FAILED=1
fi"""

    def _step_run_command(self, step: Dict[str, Any]) -> str:
        command = step.get("command", "true")
        required = step.get("required", True)
        if required:
            return f"""if {command}; then
  echo "  [ok] Command succeeded"
else
  echo "  [!] Command failed: {command}"
  STEP_FAILED=1
fi"""
        else:
            return f"""if {command} 2>/dev/null; then
  echo "  [ok] Command succeeded"
else
  echo "  [!] Command failed (non-required): {command}"
fi"""

    def _step_generate_pr_description(self, step: Dict[str, Any]) -> str:
        # Reusable bash snippet for resolving the default branch
        resolve_default = (  # noqa: E501
            'DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/"$REMOTE"/HEAD'
            ' 2>/dev/null | sed "s@^refs/remotes/$REMOTE/@@"'
            ' || echo "main")'
        )
        lines: List[str] = [
            "# Generate PR description from git log",
            'echo ""',
            'echo "--- PR Description ---"',
            'echo ""',
            'echo "## Changes"',
            'echo ""',
            "if has_upstream; then",
            f"  {resolve_default}",
            '  COMMITS=$(git log --oneline'
            ' "$REMOTE/$DEFAULT_BRANCH..HEAD"'
            ' 2>/dev/null || true)',
            '  if [ -n "$COMMITS" ]; then',
            '    echo "$COMMITS" | while IFS= read -r line; do',
            '      echo "- $line"',
            "    done",
            "  else",
            '    echo "- (no new commits detected)"',
            "  fi",
            "else",
            '  echo "- (no upstream to compare against)"',
            "fi",
            'echo ""',
            'echo "## Files Changed"',
            'echo ""',
            "if has_upstream; then",
            f"  {resolve_default}",
            '  git diff --stat "$REMOTE/$DEFAULT_BRANCH..HEAD"'
            ' 2>/dev/null || echo "(cannot compute diff)"',
            "else",
            '  echo "(no upstream to compare against)"',
            "fi",
            'echo ""',
            'echo "---"',
            'echo ""',
            "",
        ]
        return "\n".join(lines)

    def _step_show_checklist(self, step: Dict[str, Any]) -> str:
        items = step.get("items", [])
        lines: List[str] = ['echo "--- PR Checklist ---"', 'echo ""']
        for item in items:
            lines.append(f'echo "  [ ] {item}"')
        lines.append('echo ""')
        return "\n".join(lines)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Git-ops workflow engine")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List available workflows")

    p_run = sub.add_parser("run", help="Run a workflow")
    p_run.add_argument("name", help="Workflow name")
    p_run.add_argument(
        "--param",
        action="append",
        dest="param_list",
        metavar="KEY=VALUE",
        help="Workflow parameter",
    )

    parser.add_argument("--config", metavar="FILE", help="Path to configuration file")

    args = parser.parse_args()

    # Load config if available
    config: Dict[str, Any] = {}
    try:
        from config_manager import ConfigManager

        cm = ConfigManager(args.config)
        config = cm.get("workflows", {}) or {}
    except ImportError:
        pass

    engine = WorkflowEngine(config)

    if args.command == "list":
        script = engine.generate_list_script()
    elif args.command == "run":
        params = {}
        if args.param_list:
            for item in args.param_list:
                if "=" in item:
                    k, v = item.split("=", 1)
                    params[k] = v
        wf_name = args.name.replace("-", "_")
        script = engine.generate_script(wf_name, params or None)
    else:
        parser.print_help()
        return

    print("```bash")
    print(script.rstrip())
    print("```")


if __name__ == "__main__":
    main()
