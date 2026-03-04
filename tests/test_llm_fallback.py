"""Tests for llm_fallback validation and security."""

import json
from unittest.mock import patch, MagicMock

import pytest
from llm_fallback import (
    VALID_OPS,
    VALID_PARAMS,
    _sanitize_string,
    _validate_response,
    _call_ollama,
    llm_parse_intent,
)


# ── _sanitize_string ────────────────────────────────────────────────


class TestSanitizeString:
    def test_normal_string(self):
        assert _sanitize_string("hello world") == "hello world"

    def test_empty_string(self):
        assert _sanitize_string("") == ""

    def test_shell_semicolon(self):
        assert _sanitize_string("; rm -rf /") is None

    def test_shell_pipe(self):
        assert _sanitize_string("foo | bar") is None

    def test_shell_backtick(self):
        assert _sanitize_string("`whoami`") is None

    def test_shell_dollar_paren(self):
        assert _sanitize_string("$(cat /etc/passwd)") is None

    def test_shell_ampersand(self):
        assert _sanitize_string("foo & bar") is None

    def test_shell_backslash(self):
        assert _sanitize_string("foo\\nbar") is None

    def test_too_long(self):
        assert _sanitize_string("a" * 201) is None

    def test_exactly_max_len(self):
        assert _sanitize_string("a" * 200) == "a" * 200

    def test_custom_max_len(self):
        assert _sanitize_string("hello", max_len=3) is None
        assert _sanitize_string("hi", max_len=3) == "hi"

    def test_non_string_input(self):
        assert _sanitize_string(123) is None

    def test_chinese_content(self):
        assert _sanitize_string("修正登入錯誤") == "修正登入錯誤"

    def test_path_like_safe(self):
        assert _sanitize_string("src/main.py") == "src/main.py"

    def test_curly_braces_rejected(self):
        assert _sanitize_string("stash@{0}") is None


# ── _validate_response ──────────────────────────────────────────────


class TestValidateResponse:
    def test_valid_commit(self):
        raw = json.dumps({"op": "commit", "params": {"message": "fix bug"}})
        result = _validate_response(raw)
        assert result == {"op": "commit", "params": {"message": "fix bug"}}

    def test_valid_op_no_params(self):
        raw = json.dumps({"op": "preflight", "params": {}})
        result = _validate_response(raw)
        assert result == {"op": "preflight", "params": {}}

    def test_valid_op_missing_params_key(self):
        raw = json.dumps({"op": "preflight"})
        result = _validate_response(raw)
        assert result == {"op": "preflight", "params": {}}

    def test_invalid_op(self):
        raw = json.dumps({"op": "hack_system", "params": {}})
        assert _validate_response(raw) is None

    def test_status_filtered(self):
        """LLM returning 'status' is treated as no-match."""
        raw = json.dumps({"op": "status", "params": {}})
        assert _validate_response(raw) is None

    def test_invalid_json(self):
        assert _validate_response("not json") is None

    def test_none_input(self):
        assert _validate_response(None) is None

    def test_empty_string(self):
        assert _validate_response("") is None

    def test_non_dict_json(self):
        assert _validate_response('"just a string"') is None

    def test_extra_params_filtered(self):
        """Params not in VALID_PARAMS whitelist are silently dropped."""
        raw = json.dumps(
            {"op": "commit", "params": {"message": "ok", "evil": "injected"}}
        )
        result = _validate_response(raw)
        assert result is not None
        assert "evil" not in result["params"]
        assert result["params"]["message"] == "ok"

    def test_int_coercion(self):
        raw = json.dumps({"op": "log", "params": {"log_max_count": "10"}})
        result = _validate_response(raw)
        assert result["params"]["log_max_count"] == 10

    def test_int_coercion_failure(self):
        raw = json.dumps({"op": "log", "params": {"log_max_count": "not_a_number"}})
        result = _validate_response(raw)
        assert "log_max_count" not in result["params"]

    def test_bool_strict(self):
        """Only actual booleans accepted, not truthy strings."""
        raw = json.dumps({"op": "commit", "params": {"amend": "true"}})
        result = _validate_response(raw)
        assert "amend" not in result["params"]

    def test_bool_true(self):
        raw = json.dumps({"op": "commit", "params": {"amend": True}})
        result = _validate_response(raw)
        assert result["params"]["amend"] is True

    def test_list_param(self):
        raw = json.dumps({"op": "revert", "params": {"commits": ["abc123", "def456"]}})
        result = _validate_response(raw)
        assert result["params"]["commits"] == ["abc123", "def456"]

    def test_list_too_long(self):
        raw = json.dumps({"op": "revert", "params": {"commits": ["a"] * 11}})
        result = _validate_response(raw)
        assert "commits" not in result["params"]

    def test_list_with_dangerous_item(self):
        raw = json.dumps(
            {"op": "revert", "params": {"commits": ["abc123", "; rm -rf /"]}}
        )
        result = _validate_response(raw)
        # Dangerous item filtered, only safe one remains
        assert result["params"]["commits"] == ["abc123"]

    def test_shell_injection_in_message(self):
        raw = json.dumps({"op": "commit", "params": {"message": "$(malicious)"}})
        result = _validate_response(raw)
        assert "message" not in result["params"]

    def test_params_not_dict(self):
        raw = json.dumps({"op": "commit", "params": "not a dict"})
        result = _validate_response(raw)
        assert result == {"op": "commit", "params": {}}


# ── VALID_OPS / VALID_PARAMS completeness ───────────────────────────


class TestWhitelists:
    def test_valid_ops_has_core_ops(self):
        core = {
            "commit",
            "push",
            "log",
            "show",
            "diff",
            "stash",
            "branch",
            "checkout",
            "merge",
            "rebase",
            "reset",
            "revert",
            "grep",
            "tag",
        }
        assert core.issubset(VALID_OPS)

    def test_valid_ops_has_advanced_ops(self):
        advanced = {
            "preflight",
            "conflict_detect",
            "conflict_resolve",
            "decide",
            "validate_commit",
            "workflow",
        }
        assert advanced.issubset(VALID_OPS)

    def test_status_in_valid_ops_but_filtered(self):
        """status is in VALID_OPS but _validate_response filters it to None."""
        assert "status" in VALID_OPS
        result = _validate_response('{"op": "status", "params": {}}')
        assert result is None

    def test_valid_params_keys_match_ops(self):
        """Every op in VALID_PARAMS should be a valid op."""
        for op in VALID_PARAMS:
            assert op in VALID_OPS, f"{op} in VALID_PARAMS but not in VALID_OPS"

    def test_commit_params_include_message(self):
        assert "message" in VALID_PARAMS["commit"]


# ── _call_ollama (mocked) ──────────────────────────────────────────


class TestCallOllama:
    @patch("llm_fallback.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {"response": '{"op": "commit", "params": {}}'}
        ).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = _call_ollama("commit changes", {"enabled": True})
        assert result == '{"op": "commit", "params": {}}'

    @patch("llm_fallback.urllib.request.urlopen")
    def test_timeout(self, mock_urlopen):
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        result = _call_ollama("commit", {"enabled": True})
        assert result is None

    @patch("llm_fallback.urllib.request.urlopen")
    def test_connection_refused(self, mock_urlopen):
        mock_urlopen.side_effect = OSError("Connection refused")
        result = _call_ollama("commit", {"enabled": True})
        assert result is None

    @patch("llm_fallback.urllib.request.urlopen")
    def test_invalid_json_response(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"not json"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = _call_ollama("commit", {"enabled": True})
        assert result is None

    @patch("llm_fallback.urllib.request.urlopen")
    def test_custom_model_and_url(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"response": "{}"}).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        config = {"enabled": True, "model": "llama3", "base_url": "http://myhost:8080"}
        _call_ollama("test", config)
        # Verify the URL used
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert "myhost:8080" in req.full_url


# ── llm_parse_intent ────────────────────────────────────────────────


class TestLlmParseIntent:
    def test_disabled_returns_none(self):
        assert llm_parse_intent("commit", {"enabled": False}) is None

    def test_default_disabled(self):
        assert llm_parse_intent("commit", {}) is None

    @patch("llm_fallback._call_ollama")
    def test_valid_response(self, mock_call):
        mock_call.return_value = json.dumps(
            {"op": "commit", "params": {"message": "test"}}
        )
        result = llm_parse_intent("do a commit", {"enabled": True})
        assert result == {"op": "commit", "params": {"message": "test"}}

    @patch("llm_fallback._call_ollama")
    def test_ollama_returns_none(self, mock_call):
        mock_call.return_value = None
        assert llm_parse_intent("something", {"enabled": True}) is None
