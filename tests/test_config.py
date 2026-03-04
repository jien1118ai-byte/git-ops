"""Tests for ConfigManager."""

import os
import tempfile
from pathlib import Path

import pytest
from config_manager import ConfigManager


# ── _deep_merge ─────────────────────────────────────────────────────


class TestDeepMerge:
    def setup_method(self):
        self.cm = ConfigManager.__new__(ConfigManager)

    def test_flat_merge(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = self.cm._deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        base = {"git": {"remote": "origin", "branch": "main"}}
        override = {"git": {"remote": "upstream"}}
        result = self.cm._deep_merge(base, override)
        assert result["git"]["remote"] == "upstream"
        assert result["git"]["branch"] == "main"

    def test_override_adds_new_key(self):
        base = {"a": 1}
        override = {"b": 2}
        result = self.cm._deep_merge(base, override)
        assert result == {"a": 1, "b": 2}

    def test_override_replaces_non_dict_with_dict(self):
        base = {"a": "string"}
        override = {"a": {"nested": True}}
        result = self.cm._deep_merge(base, override)
        assert result["a"] == {"nested": True}

    def test_override_replaces_dict_with_non_dict(self):
        base = {"a": {"nested": True}}
        override = {"a": "flat"}
        result = self.cm._deep_merge(base, override)
        assert result["a"] == "flat"

    def test_empty_override(self):
        base = {"a": 1}
        result = self.cm._deep_merge(base, {})
        assert result == {"a": 1}

    def test_empty_base(self):
        result = self.cm._deep_merge({}, {"a": 1})
        assert result == {"a": 1}

    def test_deeply_nested(self):
        base = {"l1": {"l2": {"l3": "old"}}}
        override = {"l1": {"l2": {"l3": "new", "extra": True}}}
        result = self.cm._deep_merge(base, override)
        assert result["l1"]["l2"]["l3"] == "new"
        assert result["l1"]["l2"]["extra"] is True


# ── get / set (dot-notation) ────────────────────────────────────────


class TestGetSet:
    def setup_method(self):
        self.cm = ConfigManager.__new__(ConfigManager)
        self.cm.config = {
            "git": {"remote": "origin", "branch": None},
            "safety": {"confirm_destructive": True},
        }
        self.cm.config_file = None

    def test_get_top_level(self):
        assert isinstance(self.cm.get("git"), dict)

    def test_get_nested(self):
        assert self.cm.get("git.remote") == "origin"

    def test_get_deeply_nested(self):
        self.cm.config["a"] = {"b": {"c": 42}}
        assert self.cm.get("a.b.c") == 42

    def test_get_nonexistent_returns_default(self):
        assert self.cm.get("nonexistent") is None
        assert self.cm.get("nonexistent", "fallback") == "fallback"

    def test_get_nonexistent_nested(self):
        assert self.cm.get("git.nonexistent") is None

    def test_get_none_value(self):
        assert self.cm.get("git.branch") is None

    def test_set_existing(self):
        self.cm.set("git.remote", "upstream")
        assert self.cm.get("git.remote") == "upstream"

    def test_set_new_nested(self):
        self.cm.set("new.nested.key", "value")
        assert self.cm.get("new.nested.key") == "value"

    def test_set_creates_intermediate_dicts(self):
        self.cm.set("deep.path.to.value", 123)
        assert self.cm.config["deep"]["path"]["to"]["value"] == 123

    def test_set_overwrites_non_dict_intermediate(self):
        self.cm.set("git.remote.sub", "val")
        # 'remote' was "origin" (str), now it's a dict
        assert self.cm.get("git.remote.sub") == "val"


# ── resolve_alias ───────────────────────────────────────────────────


class TestResolveAlias:
    def setup_method(self):
        self.cm = ConfigManager.__new__(ConfigManager)
        self.cm.config = {
            "aliases": {"s": "stash", "sp": "stash pop", "cm": "checkout main"},
        }
        self.cm.config_file = None

    def test_alias_found(self):
        assert self.cm.resolve_alias("s") == "stash"

    def test_alias_multi_word(self):
        assert self.cm.resolve_alias("sp") == "stash pop"

    def test_no_alias(self):
        assert self.cm.resolve_alias("commit") == "commit"

    def test_empty_aliases(self):
        self.cm.config["aliases"] = {}
        assert self.cm.resolve_alias("s") == "s"

    def test_alias_case_sensitive(self):
        assert self.cm.resolve_alias("S") == "S"  # 'S' != 's'


# ── Config loading ──────────────────────────────────────────────────


class TestConfigLoading:
    def test_defaults_loaded(self):
        cm = ConfigManager(config_file="/nonexistent/path.yml")
        # Defaults should still be present
        assert cm.get("git.remote") == "origin"
        assert cm.get("safety.confirm_destructive") is True

    def test_load_yaml_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("git:\n  remote: upstream\n")
            f.flush()
            try:
                cm = ConfigManager(config_file=f.name)
                assert cm.get("git.remote") == "upstream"
                # Other defaults still present
                assert cm.get("safety.confirm_destructive") is True
            finally:
                os.unlink(f.name)

    def test_load_empty_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("")
            f.flush()
            try:
                cm = ConfigManager(config_file=f.name)
                # Defaults should remain
                assert cm.get("git.remote") == "origin"
            finally:
                os.unlink(f.name)

    def test_load_invalid_yaml(self, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(": : : invalid yaml [[[")
            f.flush()
            try:
                cm = ConfigManager(config_file=f.name)
                captured = capsys.readouterr()
                assert "Warning" in captured.out
            finally:
                os.unlink(f.name)

    def test_nonexistent_file_uses_defaults(self):
        cm = ConfigManager(config_file="/tmp/does_not_exist_12345.yml")
        assert cm.get("git.remote") == "origin"


# ── resolve_custom_pattern ──────────────────────────────────────────


class TestResolveCustomPattern:
    def setup_method(self):
        self.cm = ConfigManager.__new__(ConfigManager)
        self.cm.config = {
            "custom_patterns": {
                "save work": "stash with message 'work in progress'",
                "quick commit": "commit 'wip' and push",
            }
        }
        self.cm.config_file = None

    def test_pattern_match(self):
        assert self.cm.resolve_custom_pattern("save work") is not None

    def test_pattern_partial_match(self):
        result = self.cm.resolve_custom_pattern("please save work now")
        assert result is not None

    def test_no_match(self):
        assert self.cm.resolve_custom_pattern("deploy to prod") is None

    def test_case_insensitive(self):
        result = self.cm.resolve_custom_pattern("Save Work")
        assert result is not None
