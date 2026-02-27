#!/usr/bin/env python3
"""
Configuration Manager for git-ops
Handles YAML configuration file loading and merging
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages git-ops configuration from YAML files"""

    DEFAULT_CONFIG = {
        # Git defaults
        'git': {
            'remote': 'origin',
            'sync_mode': 'rebase',  # rebase|merge|none
            'push_mode': 'push',    # push|nopush|lease
            'branch': None,         # null means use current branch
        },

        # Commit message settings
        'commit': {
            'auto_log': True,          # Auto-generate body with modified files
            'log_format': 'stat',      # stat (default)
        },

        # Safety settings
        'safety': {
            'confirm_destructive': True,
            'confirm_hard_reset': True,
            'confirm_force_push': True,
            'confirm_branch_delete': True,
        },

        # Preflight check settings
        'preflight': {
            'check_branch': True,
            'check_detached_head': True,
            'check_uncommitted': True,
            'check_untracked': True,
            'check_stashes': True,
            'check_remote_status': True,
            'check_conflicts': True,
            'fetch_before_check': True,
            'show_recommendations': True,
        },

        # Conflict detection settings
        'conflict_detection': {
            'fetch_before_detect': True,
            'default_target_branch': 'main',
            'show_file_details': True,
            'show_resolution_guide': True,
            'cleanup_on_error': True,
        },

        # Decision engine settings
        'decision_engine': {
            'default_target_branch': 'main',
            'fetch_before_analyze': True,
            'show_situation': True,
            'show_risks': True,
            'show_next_command': True,
        },

        # Stash management settings
        'stash_management': {
            'backup_dir': '~/.git-ops/backups',
            'age_warning_hours': 24,
            'age_danger_hours': 168,  # 7 days
            'show_file_stats': True,
            'show_age': True,
        },

        # Branch management settings
        'branch_management': {
            'default_base_branch': 'main',
            'stale_days': 30,
            'merged_grace_days': 7,
            'show_remote_branches': True,
            'protected_branches': ['main', 'master', 'develop', 'staging'],
            'fetch_before_analyze': True,
        },

        # Workflow templates
        'workflows': {
            'stop_on_error': True,
            'show_step_numbers': True,
            'verbose': False,
            'definitions': {},
            'overrides': {},
        },

        # Team rules validation
        'team_rules': {
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
        },

        # Logging settings
        'logging': {
            'enabled': True,
            'log_file': '~/.git-ops/usage.jsonl',
            'log_errors': True,
        },

        # Aliases (custom shortcuts)
        'aliases': {
            # Example:
            # 's': 'stash',
            # 'sp': 'stash pop',
            # 'cm': 'checkout main',
        },

        # Custom patterns (extend NLP)
        'custom_patterns': {
            # Example:
            # 'save': 'stash',
            # 'undo': 'reset --soft HEAD~1',
        },

        # Operation priorities (for future optimization)
        'priorities': {
            # Auto-populated from usage analysis
        },

        # Behavior customization
        'behavior': {
            'auto_fetch': True,
            'use_force_with_lease': True,
            'interactive_mode': False,
            'verbose': False,
        },

        # LLM fallback (local Ollama)
        'llm_fallback': {
            'enabled': False,
            'model': 'qwen2.5:3b',
            'base_url': 'http://localhost:11434',
            'timeout': 2,
        },
    }

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            config_file: Path to config file. If None, searches in standard locations.
        """
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_file = self._find_config_file(config_file)

        if self.config_file and self.config_file.exists():
            self.load()

    def _find_config_file(self, config_file: Optional[str] = None) -> Optional[Path]:
        """Find configuration file in standard locations"""
        if config_file:
            return Path(config_file).expanduser()

        # Search order:
        # 1. Current directory
        # 2. Git repository root
        # 3. User home directory
        # 4. XDG_CONFIG_HOME

        search_paths = [
            Path.cwd() / 'git-ops.yml',
            Path.cwd() / '.git-ops.yml',
            self._find_git_root() / 'git-ops.yml' if self._find_git_root() else None,
            Path.home() / '.git-ops.yml',
            Path.home() / '.config' / 'git-ops' / 'config.yml',
        ]

        for path in search_paths:
            if path and path.exists():
                return path

        return None

    def _find_git_root(self) -> Optional[Path]:
        """Find git repository root"""
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent
        return None

    def load(self, config_file: Optional[str] = None) -> None:
        """Load configuration from YAML file"""
        if config_file:
            self.config_file = Path(config_file).expanduser()

        if not self.config_file or not self.config_file.exists():
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f) or {}

            # Deep merge user config with defaults
            self.config = self._deep_merge(self.DEFAULT_CONFIG, user_config)

        except yaml.YAMLError as e:
            print(f"Warning: Failed to load config file: {e}")
        except Exception as e:
            print(f"Warning: Error reading config file: {e}")

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key: Configuration key (e.g., 'git.remote')
            default: Default value if key not found
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation

        Args:
            key: Configuration key (e.g., 'git.remote')
            value: Value to set
        """
        keys = key.split('.')
        target = self.config

        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]

        target[keys[-1]] = value

    def save(self, config_file: Optional[str] = None) -> Path:
        """
        Save current configuration to YAML file

        Args:
            config_file: Path to save config. If None, uses current config_file.

        Returns:
            Path to saved config file
        """
        if config_file:
            self.config_file = Path(config_file).expanduser()
        elif not self.config_file:
            # Default to user home directory
            self.config_file = Path.home() / '.git-ops.yml'

        # Ensure directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self.config, f, default_flow_style=False, sort_keys=False)

        return self.config_file

    def resolve_alias(self, text: str) -> str:
        """
        Resolve alias to full command

        Args:
            text: Input text (possibly an alias)

        Returns:
            Resolved text (or original if no alias found)
        """
        aliases = self.get('aliases', {})
        return aliases.get(text, text)

    def resolve_custom_pattern(self, text: str) -> Optional[str]:
        """
        Check if text matches a custom pattern

        Args:
            text: Input text

        Returns:
            Replacement pattern if found, None otherwise
        """
        patterns = self.get('custom_patterns', {})
        text_lower = text.lower().strip()

        for pattern, replacement in patterns.items():
            if pattern.lower() in text_lower:
                return replacement

        return None

    def export_template(self, output_file: str = 'git-ops.yml') -> Path:
        """
        Export a template configuration file with comments

        Args:
            output_file: Path to output file

        Returns:
            Path to exported file
        """
        template = """# Git-Ops Configuration File
# This file customizes git-ops behavior
# Save as: git-ops.yml, .git-ops.yml, or ~/.git-ops.yml

# Git default settings
git:
  remote: origin          # Default remote name
  sync_mode: rebase       # rebase|merge|none
  push_mode: push         # push|nopush|lease
  branch: null            # null = use current branch

# Commit message settings
commit:
  auto_log: true              # Auto-include modified files in commit body
  log_format: stat            # File change format: stat

# Safety confirmations
safety:
  confirm_destructive: true      # Confirm dangerous operations
  confirm_hard_reset: true       # Confirm hard resets
  confirm_force_push: true       # Confirm force pushes
  confirm_branch_delete: true    # Confirm branch deletions

# Preflight check settings
preflight:
  check_branch: true               # Show current branch info
  check_detached_head: true        # Warn about detached HEAD
  check_uncommitted: true          # Check for uncommitted changes
  check_untracked: true            # Check for untracked files
  check_stashes: true              # Show stash count
  check_remote_status: true        # Compare with remote branch
  check_conflicts: true            # Detect unresolved conflicts
  fetch_before_check: true         # Fetch remote before checking
  show_recommendations: true       # Show recommended next steps

# Conflict detection settings
conflict_detection:
  fetch_before_detect: true        # Fetch remote before detecting
  default_target_branch: main      # Default branch to check against
  show_file_details: true          # Show per-file conflict details
  show_resolution_guide: true      # Show resolution options
  cleanup_on_error: true           # Always clean up temp branches

# Decision engine settings
decision_engine:
  default_target_branch: main      # Default branch for comparison
  fetch_before_analyze: true       # Fetch remote before analysis
  show_situation: true             # Show current situation summary
  show_risks: true                 # Show risk warnings
  show_next_command: true          # Suggest next gops command

# Stash management settings
stash_management:
  backup_dir: ~/.git-ops/backups    # Directory for stash backup patch files
  age_warning_hours: 24             # Warn if stash is older than this
  age_danger_hours: 168             # Mark as dangerous if older (7 days)
  show_file_stats: true             # Show file change stats in detailed list
  show_age: true                    # Show stash age in detailed list

# Branch management settings
branch_management:
  default_base_branch: main        # Base branch for merge status checks
  stale_days: 30                   # Branches with no commits for this many days are "stale"
  merged_grace_days: 7             # Recently merged branches are kept for this many days
  show_remote_branches: true       # Show remote-only branches in analysis
  protected_branches:              # These branches are never deleted
    - main
    - master
    - develop
    - staging
  fetch_before_analyze: true       # Fetch remote before analyzing branches

# Team rules validation
team_rules:
  commit_format:
    style: conventional            # conventional|custom
    pattern: '^(feat|fix|docs|style|refactor|perf|test|chore)(\\(.+?\\))?!?: .+'
    max_length: 72                 # Max commit message length
    examples:
      - 'feat(auth): implement JWT login'
      - 'fix(api): handle timeout'
  branch_naming:
    enabled: true                  # Enable branch name validation
    pattern: '^(feature|fix|hotfix|release|chore)/[a-z0-9._-]+$'
    exempt:                        # Branches exempt from naming rules
      - main
      - master
      - develop
      - staging
    examples:
      - 'feature/user-auth'
      - 'fix/memory-leak'
  quality_checks: []               # List of {name, command, required}
  # quality_checks:
  #   - name: lint
  #     command: npm run lint
  #     required: true
  #   - name: tests
  #     command: npm test
  #     required: true

# Workflow templates
workflows:
  stop_on_error: true              # Prompt to continue/abort when a step fails
  show_step_numbers: true          # Show [1/N] step numbering
  verbose: false                   # Show extra debug info per step
  definitions: {}                  # Custom workflow definitions
  overrides: {}                    # Override steps in built-in workflows
  # definitions:
  #   deploy:
  #     description: Deploy to production
  #     params:
  #       - name: tag
  #         required: true
  #         prompt: Release tag
  #     steps:
  #       - action: run_command
  #         command: npm test
  #         required: true
  #         label: Run tests
  #       - action: run_command
  #         command: npm run build
  #         required: true
  #         label: Build
  # overrides:
  #   ready_for_pr:
  #     steps:
  #       - action: run_command
  #         command: pytest
  #         required: true
  #         label: Run pytest

# Usage logging
logging:
  enabled: true                  # Enable usage tracking
  log_file: ~/.git-ops/usage.jsonl
  log_errors: true               # Log failed operations

# Custom aliases (shortcuts)
aliases:
  # Short aliases for common operations
  s: stash
  sp: stash pop
  sl: stash list
  cm: checkout main
  cd: checkout develop
  cp: commit and push
  cap: commit and push
  save: stash

# Custom patterns (natural language extensions)
custom_patterns:
  # Add your own patterns
  save work: stash with message 'work in progress'
  quick commit: commit 'wip' and push
  sync: checkout main, pull, checkout -, merge main

# Operation priorities (auto-updated by analyzer)
priorities:
  # This section is auto-populated by pattern_analyzer.py
  # Don't edit manually unless you know what you're doing

# Behavior customization
behavior:
  auto_fetch: true              # Auto-fetch before push/pull
  use_force_with_lease: true    # Use --force-with-lease instead of --force
  interactive_mode: false       # Interactive mode for ambiguous commands
  verbose: false                # Verbose output
"""

        output_path = Path(output_file).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template)

        return output_path

    def show(self) -> str:
        """Return current configuration as YAML string"""
        return yaml.safe_dump(self.config, default_flow_style=False, sort_keys=False)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Git-ops configuration manager')
    parser.add_argument('--init', action='store_true', help='Initialize config file with template')
    parser.add_argument('--show', action='store_true', help='Show current configuration')
    parser.add_argument('--get', metavar='KEY', help='Get configuration value (e.g., git.remote)')
    parser.add_argument('--set', nargs=2, metavar=('KEY', 'VALUE'), help='Set configuration value')
    parser.add_argument('--config', metavar='FILE', help='Path to config file')

    args = parser.parse_args()

    config = ConfigManager(args.config)

    if args.init:
        path = config.export_template()
        print(f"Configuration template created: {path}")
        print("Edit this file to customize git-ops behavior.")

    elif args.show:
        if config.config_file:
            print(f"# Configuration from: {config.config_file}\n")
        else:
            print("# Using default configuration (no config file found)\n")
        print(config.show())

    elif args.get:
        value = config.get(args.get)
        if value is not None:
            print(value)
        else:
            print(f"Key '{args.get}' not found")

    elif args.set:
        key, value = args.set
        # Try to parse value as YAML
        try:
            parsed_value = yaml.safe_load(value)
        except:
            parsed_value = value

        config.set(key, parsed_value)
        path = config.save()
        print(f"Configuration updated: {path}")
        print(f"{key} = {parsed_value}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
