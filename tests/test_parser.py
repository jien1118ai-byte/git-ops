"""Tests for git_ops NLP parser and helper functions."""

import pytest
from git_ops import Plan, parse_quoted_string, parse_hashes, parse_operation_from_text


# ── parse_quoted_string ─────────────────────────────────────────────


class TestParseQuotedString:
    def test_double_quotes(self):
        assert parse_quoted_string('commit "fix bug"') == "fix bug"

    def test_chinese_double_quotes(self):
        """Chinese curly quotes (\u201c\u201d) are supported."""
        assert parse_quoted_string("commit \u201c修正錯誤\u201d") == "修正錯誤"

    def test_empty_double_quotes(self):
        """Empty string between quotes returns empty string."""
        assert parse_quoted_string('commit ""') == ""

    def test_no_quotes(self):
        assert parse_quoted_string("commit fix bug") is None

    def test_only_opening_quote(self):
        assert parse_quoted_string('commit "fix bug') is None

    def test_multiple_quoted_takes_first(self):
        assert parse_quoted_string('"first" "second"') == "first"

    def test_quotes_with_spaces(self):
        assert parse_quoted_string('"  spaces  "') == "  spaces  "

    def test_unicode_content(self):
        assert parse_quoted_string('"新功能：使用者登入"') == "新功能：使用者登入"


# ── parse_hashes ────────────────────────────────────────────────────


class TestParseHashes:
    def test_short_sha(self):
        assert parse_hashes("show abc123") == ["abc123"]

    def test_full_sha(self):
        sha = "a" * 40
        assert parse_hashes(f"revert {sha}") == [sha]

    def test_head(self):
        assert parse_hashes("show HEAD") == ["HEAD"]

    def test_head_tilde(self):
        assert parse_hashes("reset HEAD~3") == ["HEAD~3"]

    def test_multiple_hashes(self):
        result = parse_hashes("cherry-pick abc123 def456")
        assert result == ["abc123", "def456"]

    def test_mixed_head_and_sha(self):
        result = parse_hashes("diff HEAD abc123")
        assert "HEAD" in result
        assert "abc123" in result

    def test_no_hashes(self):
        assert parse_hashes("commit and push") == []

    def test_too_short_hex_ignored(self):
        assert parse_hashes("ab12") == []


# ── parse_operation_from_text: commit ───────────────────────────────


class TestParseCommit:
    def test_basic_commit(self):
        p = parse_operation_from_text("commit")
        assert p.op == "commit"
        assert p.push_mode == "nopush"

    def test_commit_with_message(self):
        p = parse_operation_from_text('commit "fix login bug"')
        assert p.op == "commit"
        assert p.message == "fix login bug"

    def test_commit_and_push(self):
        p = parse_operation_from_text('commit "update" and push')
        assert p.op == "commit"
        assert p.push_mode == "push"

    def test_commit_amend(self):
        p = parse_operation_from_text("commit amend")
        assert p.op == "commit"
        assert p.amend is True

    def test_commit_with_root_cause(self):
        p = parse_operation_from_text('commit "fix timeout" root cause: missing retry')
        assert p.op == "commit"
        assert p.root_cause is not None
        assert "missing retry" in p.root_cause


# ── parse_operation_from_text: stash ────────────────────────────────


class TestParseStash:
    def test_stash_save(self):
        p = parse_operation_from_text("stash")
        assert p.op == "stash"
        assert p.stash_op == "save"

    def test_stash_save_with_message(self):
        p = parse_operation_from_text('stash "work in progress"')
        assert p.op == "stash"
        assert p.stash_op == "save"
        assert p.stash_message == "work in progress"

    def test_stash_list(self):
        p = parse_operation_from_text("stash list")
        assert p.op == "stash"
        assert p.stash_op == "list"

    def test_stash_apply(self):
        p = parse_operation_from_text("stash apply")
        assert p.op == "stash"
        assert p.stash_op == "apply"
        assert p.stash_index == 0

    def test_stash_apply_index(self):
        p = parse_operation_from_text("stash apply stash@{2}")
        assert p.op == "stash"
        assert p.stash_op == "apply"
        assert p.stash_index == 2

    def test_stash_pop(self):
        p = parse_operation_from_text("stash pop")
        assert p.op == "stash"
        assert p.stash_op == "pop"

    def test_stash_drop(self):
        p = parse_operation_from_text("stash drop stash@{1}")
        assert p.op == "stash"
        assert p.stash_op == "drop"
        assert p.stash_index == 1

    def test_stash_show(self):
        p = parse_operation_from_text("stash show")
        assert p.op == "stash"
        assert p.stash_op == "show"

    def test_stash_clear(self):
        p = parse_operation_from_text("stash clear")
        assert p.op == "stash"
        assert p.stash_op == "clear"

    # Advanced stash
    def test_stash_list_detailed(self):
        p = parse_operation_from_text("stash list detailed")
        assert p.op == "stash"
        assert p.stash_op == "list_detailed"

    def test_stash_backup(self):
        p = parse_operation_from_text("stash backup")
        assert p.op == "stash"
        assert p.stash_op == "backup"

    def test_stash_apply_safe(self):
        p = parse_operation_from_text("stash apply safe")
        assert p.op == "stash"
        assert p.stash_op == "apply_safe"

    def test_stash_include_untracked(self):
        p = parse_operation_from_text("stash untracked")
        assert p.op == "stash"
        assert p.stash_op == "save"
        assert p.stash_include_untracked is True


# ── parse_operation_from_text: branch ───────────────────────────────


class TestParseBranch:
    def test_checkout(self):
        p = parse_operation_from_text("checkout develop")
        assert p.op == "checkout"
        assert p.checkout_target == "develop"

    def test_switch_branch(self):
        p = parse_operation_from_text("switch to feature/login")
        assert p.op == "checkout"
        assert p.checkout_target == "feature/login"

    def test_create_branch(self):
        p = parse_operation_from_text("create branch feature/new")
        assert p.op == "branch"
        assert p.branch_op == "create"
        assert p.branch_name == "feature/new"

    def test_create_branch_and_checkout(self):
        p = parse_operation_from_text("create branch feature/new and checkout")
        assert p.op == "checkout"
        assert p.checkout_target == "feature/new"
        assert p.checkout_create is True

    def test_delete_branch(self):
        p = parse_operation_from_text("branch delete feature/old")
        assert p.op == "branch"
        assert p.branch_op == "delete"
        assert p.branch_name == "feature/old"

    def test_analyze_branches(self):
        p = parse_operation_from_text("analyze branches")
        assert p.op == "branch"
        assert p.branch_op == "analyze"

    def test_cleanup_branches(self):
        p = parse_operation_from_text("cleanup branches")
        assert p.op == "branch"
        assert p.branch_op == "cleanup"

    def test_delete_merged_branches(self):
        p = parse_operation_from_text("delete all merged branches")
        assert p.op == "branch"
        assert p.branch_op == "delete_merged"


# ── parse_operation_from_text: grep/search ──────────────────────────


class TestParseGrep:
    def test_grep_quoted(self):
        p = parse_operation_from_text('grep "TODO"')
        assert p.op == "grep"
        assert p.grep_pattern == "TODO"

    def test_search_unquoted(self):
        p = parse_operation_from_text("search TODO")
        assert p.op == "grep"
        assert p.grep_pattern == "TODO"

    def test_search_in_file(self):
        p = parse_operation_from_text("search TODO in *.py")
        assert p.op == "grep"
        assert p.grep_pattern == "TODO"
        assert p.grep_file_pattern == "*.py"

    def test_search_ignore_case(self):
        p = parse_operation_from_text("search error ignore-case")
        assert p.op == "grep"
        assert p.grep_ignore_case is True

    def test_find_keyword(self):
        p = parse_operation_from_text("find deprecated")
        assert p.op == "grep"
        assert p.grep_pattern == "deprecated"


# ── parse_operation_from_text: reset ────────────────────────────────


class TestParseReset:
    def test_reset_soft(self):
        p = parse_operation_from_text("reset soft")
        assert p.op == "reset"
        assert p.reset_mode == "soft"

    def test_reset_hard(self):
        p = parse_operation_from_text("reset hard")
        assert p.op == "reset"
        assert p.reset_mode == "hard"

    def test_reset_mixed_default(self):
        p = parse_operation_from_text("reset")
        assert p.op == "reset"
        assert p.reset_mode == "mixed"

    def test_undo_last_commit(self):
        p = parse_operation_from_text("undo last commit")
        assert p.op == "reset"
        assert p.reset_mode == "soft"
        assert p.reset_target == "HEAD~1"

    def test_reset_to_target(self):
        p = parse_operation_from_text("reset to abc123")
        assert p.op == "reset"
        assert p.reset_target == "abc123"


# ── parse_operation_from_text: merge / rebase / cherry-pick / revert


class TestParseMergeRebaseEtc:
    def test_merge(self):
        p = parse_operation_from_text("merge feature/login")
        assert p.op == "merge"
        assert p.merge_source == "feature/login"

    def test_merge_squash(self):
        p = parse_operation_from_text("merge feature/login squash")
        assert p.op == "merge"
        assert p.merge_squash is True

    def test_merge_no_ff(self):
        p = parse_operation_from_text("merge feature/x no-ff")
        assert p.op == "merge"
        assert p.merge_no_ff is True

    def test_rebase(self):
        p = parse_operation_from_text("rebase main")
        assert p.op == "rebase"
        assert p.rebase_target == "main"

    def test_rebase_interactive(self):
        p = parse_operation_from_text("rebase -i main")
        assert p.op == "rebase"
        assert p.rebase_interactive is True

    def test_squash_last_n(self):
        p = parse_operation_from_text("squash last 3 commits")
        assert p.op == "rebase"
        assert p.rebase_interactive is True
        assert p.rebase_target == "HEAD~3"

    def test_cherry_pick(self):
        p = parse_operation_from_text("cherry-pick abc123")
        assert p.op == "cherry_pick"
        assert "abc123" in p.commits

    def test_cherry_pick_no_commit(self):
        p = parse_operation_from_text("cherry-pick abc123 no-commit")
        assert p.op == "cherry_pick"
        assert p.no_commit is True

    def test_revert(self):
        p = parse_operation_from_text("revert abc123")
        assert p.op == "revert"
        assert "abc123" in p.commits

    def test_revert_no_commit(self):
        p = parse_operation_from_text("revert abc123 without commit")
        assert p.op == "revert"
        assert p.no_commit is True
        assert p.combined is False

    def test_revert_combined_english(self):
        p = parse_operation_from_text("revert abc123 def456 combined")
        assert p.op == "revert"
        assert p.combined is True
        assert "abc123" in p.commits
        assert "def456" in p.commits

    def test_revert_combined_as_one(self):
        p = parse_operation_from_text("revert abc123 def456 as one commit")
        assert p.op == "revert"
        assert p.combined is True

    def test_revert_combined_chinese(self):
        p = parse_operation_from_text("revert abc123 def456 合成一筆")
        assert p.op == "revert"
        assert p.combined is True

    def test_revert_combined_and_push(self):
        p = parse_operation_from_text("revert abc123 def456 combined and push")
        assert p.op == "revert"
        assert p.combined is True
        assert p.push_mode == "push"

    def test_revert_combined_into_one(self):
        p = parse_operation_from_text("revert abc123 def456 into one")
        assert p.op == "revert"
        assert p.combined is True

    def test_revert_combined_squash_into_one(self):
        p = parse_operation_from_text("revert abc123 def456 squash into one")
        assert p.op == "revert"
        assert p.combined is True

    def test_revert_squash_alone_does_not_set_combined(self):
        # bare "squash" alone does not match the combined regex (requires "squash into one" or "squash revert")
        p = parse_operation_from_text("revert abc123 squash")
        assert p.op == "revert"
        assert p.combined is False


# ── parse_operation_from_text: show / diff / log / blame / reflog ───


class TestParseShowDiffLogEtc:
    def test_show_head(self):
        p = parse_operation_from_text("show")
        assert p.op == "show"
        assert p.show_target == "HEAD"

    def test_show_specific(self):
        p = parse_operation_from_text("show abc123")
        assert p.op == "show"
        assert p.show_target == "abc123"

    def test_diff(self):
        p = parse_operation_from_text("diff")
        assert p.op == "diff"

    def test_diff_staged(self):
        p = parse_operation_from_text("diff staged")
        assert p.op == "diff"
        assert p.diff_staged is True

    def test_log(self):
        p = parse_operation_from_text("log")
        assert p.op == "log"

    def test_log_last_n(self):
        p = parse_operation_from_text("log last 5")
        assert p.op == "log"
        assert p.log_max_count == 5

    def test_log_with_search(self):
        p = parse_operation_from_text('log with "fix"')
        assert p.op == "log"
        assert p.log_search == "fix"

    def test_log_graph(self):
        p = parse_operation_from_text("log graph")
        assert p.op == "log"
        assert p.log_graph is True

    def test_log_author(self):
        p = parse_operation_from_text("log author john")
        assert p.op == "log"
        assert p.log_search == "john"
        assert p.log_search_is_author is True

    def test_blame(self):
        p = parse_operation_from_text("blame src/main.py")
        assert p.op == "blame"
        assert p.blame_path == "src/main.py"

    def test_blame_with_line(self):
        p = parse_operation_from_text("blame src/main.py line 10-20")
        assert p.op == "blame"
        assert p.blame_line_start == 10
        assert p.blame_line_end == 20

    def test_reflog(self):
        p = parse_operation_from_text("reflog")
        assert p.op == "reflog"
        assert p.reflog_max_count == 20

    def test_reflog_custom_count(self):
        p = parse_operation_from_text("reflog show 50")
        assert p.op == "reflog"
        assert p.reflog_max_count == 50


# ── parse_operation_from_text: tag / clean / bisect / push ──────────


class TestParseTagCleanBisectPush:
    def test_tag_create(self):
        p = parse_operation_from_text("tag v1.0.0")
        assert p.op == "tag"
        assert p.tag_op == "create"
        assert p.tag_name == "v1.0.0"

    def test_tag_list(self):
        p = parse_operation_from_text("tag list")
        assert p.op == "tag"
        assert p.tag_op == "list"

    def test_tag_delete(self):
        p = parse_operation_from_text("tag delete v0.9")
        assert p.op == "tag"
        assert p.tag_op == "delete"

    def test_tag_annotated(self):
        p = parse_operation_from_text('tag v2.0 "release 2.0"')
        assert p.op == "tag"
        assert p.tag_annotated is True
        assert p.tag_message == "release 2.0"

    def test_clean_dry_run(self):
        p = parse_operation_from_text("clean dry-run")
        assert p.op == "clean"
        assert p.clean_dry_run is True

    def test_clean_force(self):
        p = parse_operation_from_text("clean force")
        assert p.op == "clean"
        assert p.clean_force is True

    def test_bisect_start(self):
        p = parse_operation_from_text("bisect start")
        assert p.op == "bisect"
        assert p.bisect_op == "start"

    def test_bisect_good(self):
        p = parse_operation_from_text("bisect good abc123")
        assert p.op == "bisect"
        assert p.bisect_op == "good"
        assert p.bisect_commit == "abc123"

    def test_bisect_bad(self):
        p = parse_operation_from_text("bisect bad")
        assert p.op == "bisect"
        assert p.bisect_op == "bad"

    def test_bisect_reset(self):
        """'bisect reset' correctly routes to bisect block."""
        p = parse_operation_from_text("bisect reset")
        assert p.op == "bisect"
        assert p.bisect_op == "reset"

    def test_push(self):
        p = parse_operation_from_text("push")
        assert p.op == "push"
        assert p.push_mode == "push"

    def test_push_force(self):
        p = parse_operation_from_text("push force")
        assert p.op == "push"
        assert p.push_mode == "lease"


# ── parse_operation_from_text: preflight / conflict / decide / validate / workflow


class TestParsePrefConflictDecideEtc:
    def test_preflight(self):
        p = parse_operation_from_text("preflight")
        assert p.op == "preflight"

    def test_health_check(self):
        p = parse_operation_from_text("health check")
        assert p.op == "preflight"

    def test_conflict_detect(self):
        p = parse_operation_from_text("detect conflicts")
        assert p.op == "conflict_detect"

    def test_conflict_detect_with_target(self):
        p = parse_operation_from_text("detect conflicts with main")
        assert p.op == "conflict_detect"
        assert p.conflict_target == "main"

    def test_conflict_resolve(self):
        p = parse_operation_from_text("resolve conflicts")
        assert p.op == "conflict_resolve"

    def test_decide(self):
        p = parse_operation_from_text("what should I do")
        assert p.op == "decide"

    def test_decide_recommend(self):
        p = parse_operation_from_text("recommend for commit")
        assert p.op == "decide"
        assert p.decision_goal == "commit"

    def test_validate_commit(self):
        p = parse_operation_from_text('validate commit "feat: add login"')
        assert p.op == "validate_commit"
        assert p.validate_message == "feat: add login"

    def test_validate_branch(self):
        p = parse_operation_from_text("validate branch")
        assert p.op == "validate_branch"

    def test_validate_quality(self):
        p = parse_operation_from_text("validate quality")
        assert p.op == "validate_quality"

    def test_validate_rules(self):
        p = parse_operation_from_text("validate rules")
        assert p.op == "validate_rules"

    def test_workflow_list(self):
        p = parse_operation_from_text("workflow list")
        assert p.op == "workflow"
        assert p.workflow_op == "list"

    def test_workflow_run(self):
        p = parse_operation_from_text("workflow run ready-for-pr")
        assert p.op == "workflow"
        assert p.workflow_op == "run"
        assert p.workflow_name == "ready-for-pr"

    def test_workflow_with_param(self):
        p = parse_operation_from_text("workflow deploy --param tag=v1.0")
        assert p.op == "workflow"
        assert p.workflow_name == "deploy"
        assert p.workflow_params is not None
        assert p.workflow_params.get("tag") == "v1.0"


# ── parse_operation_from_text: Chinese input ────────────────────────


class TestParseChinese:
    def test_stash_chinese(self):
        p = parse_operation_from_text("暫存詳細")
        assert p.op == "stash"
        assert p.stash_op == "list_detailed"

    def test_stash_backup_chinese(self):
        p = parse_operation_from_text("暫存備份")
        assert p.op == "stash"
        assert p.stash_op == "backup"

    def test_stash_apply_safe_chinese(self):
        p = parse_operation_from_text("安全套用暫存")
        assert p.op == "stash"
        assert p.stash_op == "apply_safe"

    def test_switch_branch_chinese(self):
        p = parse_operation_from_text("切換 develop")
        assert p.op == "checkout"
        assert p.checkout_target == "develop"

    def test_search_chinese(self):
        p = parse_operation_from_text("搜尋 TODO")
        assert p.op == "grep"
        assert p.grep_pattern == "TODO"

    def test_undo_chinese(self):
        """撤銷上一個commit works without spaces (CJK boundary fix)."""
        p = parse_operation_from_text("撤銷上一個commit")
        assert p.op == "reset"
        assert p.reset_mode == "soft"
        assert p.reset_target == "HEAD~1"

    def test_analyze_branches_chinese(self):
        p = parse_operation_from_text("分析分支")
        assert p.op == "branch"
        assert p.branch_op == "analyze"

    def test_cleanup_branches_chinese(self):
        p = parse_operation_from_text("清理分支")
        assert p.op == "branch"
        assert p.branch_op == "cleanup"

    def test_decide_chinese(self):
        p = parse_operation_from_text("該怎麼做")
        assert p.op == "decide"

    def test_suggest_chinese(self):
        p = parse_operation_from_text("建議")
        assert p.op == "decide"

    def test_validate_chinese(self):
        p = parse_operation_from_text("驗證")
        assert p.op == "validate_rules"

    def test_workflow_chinese(self):
        p = parse_operation_from_text("工作流 列表")
        assert p.op == "workflow"
        assert p.workflow_op == "list"

    def test_log_author_chinese(self):
        p = parse_operation_from_text("作者為 john")
        assert p.op == "log"
        assert p.log_search == "john"
        assert p.log_search_is_author is True

    def test_delete_merged_chinese(self):
        p = parse_operation_from_text("刪除已合併分支")
        assert p.op == "branch"
        assert p.branch_op == "delete_merged"

    def test_undo_chinese_no_space(self):
        """Chinese '給我建議' (no spaces) triggers decide."""
        p = parse_operation_from_text("給我建議")
        assert p.op == "decide"

    def test_workflow_chinese_no_space(self):
        """Chinese '工作流列表' (no spaces) triggers workflow list."""
        p = parse_operation_from_text("工作流列表")
        assert p.op == "workflow"
        assert p.workflow_op == "list"

    def test_search_chinese_no_space(self):
        """Chinese '搜尋TODO' (no spaces) triggers grep."""
        p = parse_operation_from_text("搜尋TODO")
        assert p.op == "grep"
        assert p.grep_pattern == "TODO"


# ── parse_operation_from_text: edge cases ───────────────────────────


class TestParseEdgeCases:
    def test_commit_single_quoted_message(self):
        p = parse_operation_from_text("commit 'fix auth bug' and push")
        assert p.op == "commit"
        assert p.message == "fix auth bug"
        assert p.push_mode == "push"

    def test_commit_double_quoted_message(self):
        p = parse_operation_from_text('commit "fix auth bug" and push')
        assert p.op == "commit"
        assert p.message == "fix auth bug"

    def test_empty_string_returns_status(self):
        p = parse_operation_from_text("")
        assert p.op == "status"

    def test_unknown_input_returns_status(self):
        p = parse_operation_from_text("hello world")
        assert p.op == "status"

    def test_whitespace_only(self):
        p = parse_operation_from_text("   ")
        assert p.op == "status"

    def test_show_log_redirects(self):
        """'show log' should be treated as a log command."""
        p = parse_operation_from_text("show log")
        assert p.op == "log"

    def test_restore(self):
        p = parse_operation_from_text("restore src/main.py")
        assert p.op == "restore"
        assert "src/main.py" in p.restore_paths

    def test_restore_staged(self):
        p = parse_operation_from_text("restore staged src/main.py")
        assert p.op == "restore"
        assert p.restore_staged is True
