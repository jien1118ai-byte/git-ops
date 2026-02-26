#!/bin/bash
# Git-Ops Executable Wrapper
# 解決在 Claude Code 中無法輸入密碼的問題

# 使用方式：
#   ./gops-exec.sh "pull"
#   ./gops-exec.sh "commit 'fix' and push"

set -e

if [ $# -eq 0 ]; then
    echo "用法: $0 <git-ops 指令>"
    echo ""
    echo "範例:"
    echo "  $0 \"pull\""
    echo "  $0 \"commit 'fix' and push\""
    echo "  $0 \"log graph all\""
    exit 1
fi

# 找到 git_ops.py 的位置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 檢查是否為 skill 安裝
if [ -f "$HOME/.claude/skills/git-ops/scripts/git_ops.py" ]; then
    GIT_OPS_SCRIPT="$HOME/.claude/skills/git-ops/scripts/git_ops.py"
elif [ -f "$SCRIPT_DIR/scripts/git_ops.py" ]; then
    GIT_OPS_SCRIPT="$SCRIPT_DIR/scripts/git_ops.py"
elif [ -f "$HOME/tools/git-ops/scripts/git_ops.py" ]; then
    GIT_OPS_SCRIPT="$HOME/tools/git-ops/scripts/git_ops.py"
else
    echo "錯誤：找不到 git_ops.py"
    echo "請確認 git-ops 已正確安裝"
    exit 1
fi

# 生成臨時腳本
TEMP_SCRIPT="/tmp/gops-exec-$$.sh"

# 生成腳本
python3 "$GIT_OPS_SCRIPT" --from-text "$1" > "$TEMP_SCRIPT"

# 顯示將要執行的內容（可選）
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "將執行以下 Git 操作："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
# 顯示主要命令（跳過前置檢查）
grep "^git " "$TEMP_SCRIPT" | head -5 || echo "[無直接 git 指令]"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 執行腳本（保留 TTY，可以輸入密碼）
bash "$TEMP_SCRIPT"

# 清理
rm -f "$TEMP_SCRIPT"
