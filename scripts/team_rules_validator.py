#!/usr/bin/env python3
"""
team_rules_validator.py

Validates commit messages, branch naming, and quality checks against
team-defined rules from config. Generates bash scripts following the
same pattern as PreflightChecker/ConflictDetector/DecisionEngine.

Usage:
  Integrated: python3 git_ops.py --from-text "validate commit message 'feat: test'"
  Standalone: python3 team_rules_validator.py commit --message "feat: test"
"""

from __future__ import annotations

import shlex
from typing import Optional


def q(s: str) -> str:
    return shlex.quote(s)


class TeamRulesValidator:
    """Generates bash scripts that validate team rules."""

    DEFAULT_CONFIG = {
        'commit_format': {
            'style': 'conventional',
            'pattern': r'^(feat|fix|docs|style|refactor|perf|test|chore)(\(.+?\))?!?: .+',
            'max_length': 72,
            'examples': ['feat(auth): implement JWT login', 'fix(api): handle timeout'],
        },
        'branch_naming': {
            'enabled': True,
            'pattern': r'^(feature|fix|hotfix|release|chore)/[a-z0-9._-]+$',
            'exempt': ['main', 'master', 'develop', 'staging'],
            'examples': ['feature/user-auth', 'fix/memory-leak'],
        },
        'quality_checks': [],
    }

    def __init__(self, config: Optional[dict] = None):
        self.config = {**self.DEFAULT_CONFIG}
        if config:
            for key in self.DEFAULT_CONFIG:
                if key in config:
                    if isinstance(self.config[key], dict) and isinstance(config[key], dict):
                        self.config[key] = {**self.DEFAULT_CONFIG[key], **config[key]}
                    else:
                        self.config[key] = config[key]

    def generate_commit_script(self, message: Optional[str] = None) -> str:
        """Generate bash to validate a commit message against team rules."""
        parts = []
        parts.append(self._header('COMMIT MESSAGE VALIDATION'))

        cf = self.config['commit_format']
        pattern = cf.get('pattern', self.DEFAULT_CONFIG['commit_format']['pattern'])
        max_length = cf.get('max_length', 72)
        examples = cf.get('examples', self.DEFAULT_CONFIG['commit_format']['examples'])

        if message:
            parts.append(f'MSG={q(message)}')
        else:
            parts.append('read -r -p "Enter commit message to validate: " MSG')

        parts.append(f"""
PATTERN={q(pattern)}
MAX_LENGTH={max_length}

echo ""
echo "Validating: $MSG"
echo ""

# -- Length check --
MSG_LENGTH=${{#MSG}}
if [ "$MSG_LENGTH" -gt "$MAX_LENGTH" ]; then
  echo "  [!!] Message too long: $MSG_LENGTH chars (max $MAX_LENGTH)"
  RULES_ERRORS=$((RULES_ERRORS + 1))
else
  echo "  [ok] Length: $MSG_LENGTH/$MAX_LENGTH chars"
fi

# -- Pattern check --
if [[ "$MSG" =~ $PATTERN ]]; then
  echo "  [ok] Format matches team rules"
else
  echo "  [!!] Format does not match team rules"
  echo "       Pattern: $PATTERN"
  RULES_ERRORS=$((RULES_ERRORS + 1))
fi""")

        if examples:
            parts.append('\n# -- Show examples on failure --')
            parts.append('if [ "$RULES_ERRORS" -gt 0 ]; then')
            parts.append('  echo ""')
            parts.append('  echo "  Valid examples:"')
            for ex in examples:
                parts.append(f'  echo "    - {ex}"')
            parts.append('fi')

        parts.append(self._summary())
        parts.append(self._footer())
        return '\n'.join(parts)

    def generate_branch_script(self) -> str:
        """Generate bash to validate the current branch name against team rules."""
        parts = []
        parts.append(self._header('BRANCH NAME VALIDATION'))

        bn = self.config['branch_naming']
        if not bn.get('enabled', True):
            parts.append('echo "  [i] Branch naming validation is disabled"')
            parts.append(self._footer())
            return '\n'.join(parts)

        pattern = bn.get('pattern', self.DEFAULT_CONFIG['branch_naming']['pattern'])
        exempt = bn.get('exempt', self.DEFAULT_CONFIG['branch_naming']['exempt'])
        examples = bn.get('examples', self.DEFAULT_CONFIG['branch_naming']['examples'])

        parts.append(f'PATTERN={q(pattern)}')

        # Build exempt check
        parts.append('\necho "Branch: $BR"')
        parts.append('echo ""')
        parts.append('')
        parts.append('# -- Exempt branch check --')
        parts.append('EXEMPT=0')
        for branch in exempt:
            parts.append(f'[ "$BR" = {q(branch)} ] && EXEMPT=1')

        parts.append("""
if [ "$EXEMPT" -eq 1 ]; then
  echo "  [ok] Branch '$BR' is in exempt list (no naming rules applied)"
elif [[ "$BR" =~ $PATTERN ]]; then
  echo "  [ok] Branch name matches team rules"
else
  echo "  [!!] Branch name does not match team rules"
  echo "       Pattern: $PATTERN"
  RULES_ERRORS=$((RULES_ERRORS + 1))"
fi""")

        # Fix: the above has a stray quote. Let me redo this properly.
        # Actually let me rewrite the whole conditional block cleanly.

        # Remove the last append and redo
        parts.pop()
        parts.append("""
if [ "$EXEMPT" -eq 1 ]; then
  echo "  [ok] Branch '$BR' is in exempt list (no naming rules applied)"
elif [[ "$BR" =~ $PATTERN ]]; then
  echo "  [ok] Branch name matches team rules"
else
  echo "  [!!] Branch name does not match team rules"
  echo "       Pattern: $PATTERN"
  RULES_ERRORS=$((RULES_ERRORS + 1))
fi""")

        if examples:
            parts.append('\nif [ "$RULES_ERRORS" -gt 0 ]; then')
            parts.append('  echo ""')
            parts.append('  echo "  Valid examples:"')
            for ex in examples:
                parts.append(f'  echo "    - {ex}"')
            parts.append('fi')

        parts.append(self._summary())
        parts.append(self._footer())
        return '\n'.join(parts)

    def generate_quality_script(self) -> str:
        """Generate bash to run configured quality check commands."""
        parts = []
        parts.append(self._header('QUALITY CHECKS'))

        checks = self.config.get('quality_checks', [])
        if not checks:
            parts.append('echo "  [i] No quality checks configured"')
            parts.append('echo "  Add quality_checks to your git-ops.yml team_rules section"')
            parts.append(self._footer())
            return '\n'.join(parts)

        parts.append(f'TOTAL_CHECKS={len(checks)}')
        parts.append('PASSED_CHECKS=0')
        parts.append('')

        for i, check in enumerate(checks, 1):
            name = check.get('name', f'Check {i}')
            command = check.get('command', 'true')
            required = check.get('required', True)

            parts.append(f'# -- Check {i}: {name} --')
            parts.append(f'echo "Running: {name}..."')
            parts.append(f'if {command} 2>/dev/null; then')
            parts.append(f'  echo "  [ok] {name}"')
            parts.append('  PASSED_CHECKS=$((PASSED_CHECKS + 1))')
            parts.append('else')
            if required:
                parts.append(f'  echo "  [!!] {name} (required)"')
                parts.append('  RULES_ERRORS=$((RULES_ERRORS + 1))')
            else:
                parts.append(f'  echo "  [!] {name} (optional)"')
                parts.append('  RULES_WARNINGS=$((RULES_WARNINGS + 1))')
            parts.append('fi')
            parts.append('')

        parts.append('echo ""')
        parts.append('echo "Quality: $PASSED_CHECKS/$TOTAL_CHECKS checks passed"')

        parts.append(self._summary())
        parts.append(self._footer())
        return '\n'.join(parts)

    def generate_full_script(self) -> str:
        """Generate bash that runs all validations (commit prompt + branch + quality)."""
        parts = []
        parts.append(self._header('TEAM RULES VALIDATION'))

        # Branch validation inline
        bn = self.config['branch_naming']
        if bn.get('enabled', True):
            pattern = bn.get('pattern', self.DEFAULT_CONFIG['branch_naming']['pattern'])
            exempt = bn.get('exempt', self.DEFAULT_CONFIG['branch_naming']['exempt'])

            parts.append(f'echo "--- Branch Naming ---"')
            parts.append(f'BRANCH_PATTERN={q(pattern)}')
            parts.append('EXEMPT=0')
            for branch in exempt:
                parts.append(f'[ "$BR" = {q(branch)} ] && EXEMPT=1')
            parts.append("""
if [ "$EXEMPT" -eq 1 ]; then
  echo "  [ok] Branch '$BR' is exempt"
elif [[ "$BR" =~ $BRANCH_PATTERN ]]; then
  echo "  [ok] Branch name matches rules"
else
  echo "  [!!] Branch name violates rules"
  RULES_ERRORS=$((RULES_ERRORS + 1))
fi
echo ""
""")

        # Quality checks inline
        checks = self.config.get('quality_checks', [])
        if checks:
            parts.append('echo "--- Quality Checks ---"')
            for i, check in enumerate(checks, 1):
                name = check.get('name', f'Check {i}')
                command = check.get('command', 'true')
                required = check.get('required', True)
                parts.append(f'if {command} 2>/dev/null; then')
                parts.append(f'  echo "  [ok] {name}"')
                parts.append('else')
                if required:
                    parts.append(f'  echo "  [!!] {name}"')
                    parts.append('  RULES_ERRORS=$((RULES_ERRORS + 1))')
                else:
                    parts.append(f'  echo "  [!] {name} (optional)"')
                    parts.append('  RULES_WARNINGS=$((RULES_WARNINGS + 1))')
                parts.append('fi')
            parts.append('echo ""')

        # Commit format info
        cf = self.config['commit_format']
        pattern = cf.get('pattern', self.DEFAULT_CONFIG['commit_format']['pattern'])
        max_length = cf.get('max_length', 72)
        examples = cf.get('examples', self.DEFAULT_CONFIG['commit_format']['examples'])
        parts.append('echo "--- Commit Format Rules ---"')
        parts.append(f'echo "  Style: {cf.get("style", "conventional")}"')
        parts.append(f'echo "  Max length: {max_length}"')
        parts.append(f'echo "  Pattern: {pattern}"')
        if examples:
            parts.append('echo "  Examples:"')
            for ex in examples:
                parts.append(f'echo "    - {ex}"')

        parts.append(self._summary())
        parts.append(self._footer())
        return '\n'.join(parts)

    def _header(self, title: str) -> str:
        return f"""# ---- team rules validation begin ----
echo ""
echo "========================================"
echo "  {title}"
echo "========================================"
echo ""

RULES_ERRORS=0
RULES_WARNINGS=0
"""

    def _summary(self) -> str:
        return r"""
# -- Summary --
echo ""
echo "----------------------------------------"
if [ "$RULES_ERRORS" -gt 0 ]; then
  echo "Result: FAIL ($RULES_ERRORS error(s), $RULES_WARNINGS warning(s))"
elif [ "$RULES_WARNINGS" -gt 0 ]; then
  echo "Result: PASS with $RULES_WARNINGS warning(s)"
else
  echo "Result: PASS - all rules satisfied"
fi
"""

    def _footer(self) -> str:
        return r"""echo ""
echo "========================================"
# ---- team rules validation end ----
"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Git-ops team rules validator')
    subparsers = parser.add_subparsers(dest='sub_op', required=True)

    p_commit = subparsers.add_parser('commit', help='Validate commit message')
    p_commit.add_argument('-m', '--message', help='Commit message to validate')

    subparsers.add_parser('branch', help='Validate current branch name')
    subparsers.add_parser('quality', help='Run quality checks')
    subparsers.add_parser('all', help='Run all validations')

    parser.add_argument('--config', metavar='FILE', help='Path to configuration file')

    args = parser.parse_args()

    # Load config if available
    config = {}
    try:
        from config_manager import ConfigManager
        cm = ConfigManager(args.config)
        config = cm.get('team_rules', {}) or {}
    except ImportError:
        pass

    validator = TeamRulesValidator(config)

    if args.sub_op == 'commit':
        script = validator.generate_commit_script(args.message)
    elif args.sub_op == 'branch':
        script = validator.generate_branch_script()
    elif args.sub_op == 'quality':
        script = validator.generate_quality_script()
    elif args.sub_op == 'all':
        script = validator.generate_full_script()

    print("```bash")
    print(script.rstrip())
    print("```")


if __name__ == '__main__':
    main()
