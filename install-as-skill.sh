#!/bin/bash
# Git-Ops - Claude Code Skill Installation
# 安裝為 Claude Code Skill

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                      ║${NC}"
echo -e "${BLUE}║    Git-Ops - Claude Code Skill Installation          ║${NC}"
echo -e "${BLUE}║    安裝為 Claude Code Skill                          ║${NC}"
echo -e "${BLUE}║                                                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# 檢測 Claude Code skills 目錄
CLAUDE_SKILLS_DIRS=(
    "$HOME/.claude/skills"
    "$HOME/.config/claude/skills"
    ".claude/skills"
)

CLAUDE_SKILLS_DIR=""

# 自動檢測
for dir in "${CLAUDE_SKILLS_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        CLAUDE_SKILLS_DIR="$dir"
        echo -e "${GREEN}✓ 找到 Claude Skills 目錄: $CLAUDE_SKILLS_DIR${NC}"
        break
    fi
done

# 如果找不到，詢問用戶
if [ -z "$CLAUDE_SKILLS_DIR" ]; then
    echo -e "${YELLOW}⚠ 未找到 Claude Skills 目錄${NC}"
    echo ""
    echo "請選擇安裝位置："
    echo "  1) ~/.claude/skills/git-ops (推薦)"
    echo "  2) 自訂位置"
    echo ""
    read -p "請選擇 (1-2): " CHOICE

    case $CHOICE in
        1)
            CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
            ;;
        2)
            read -p "請輸入 skills 目錄的完整路徑: " CUSTOM_DIR
            CLAUDE_SKILLS_DIR="$CUSTOM_DIR"
            ;;
        *)
            echo -e "${RED}無效選擇${NC}"
            exit 1
            ;;
    esac
fi

SKILL_DIR="$CLAUDE_SKILLS_DIR/git-ops"

echo ""
echo -e "${GREEN}安裝位置: $SKILL_DIR${NC}"
echo ""

# 確認安裝
if [ -d "$SKILL_DIR" ]; then
    echo -e "${YELLOW}⚠ 目錄已存在: $SKILL_DIR${NC}"
    read -p "是否覆蓋? (y/n): " OVERWRITE
    if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
        echo "安裝已取消"
        exit 0
    fi
    # 備份現有目錄
    mv "$SKILL_DIR" "$SKILL_DIR.backup.$(date +%Y%m%d_%H%M%S)"
    echo "  原目錄已備份"
fi

# 創建目錄
echo -e "${YELLOW}[1/4] 創建 Skill 目錄...${NC}"
mkdir -p "$SKILL_DIR"
echo -e "${GREEN}✓ 目錄已創建${NC}"
echo ""

# 複製檔案
echo -e "${YELLOW}[2/4] 複製 Skill 檔案...${NC}"

# 複製核心腳本
echo "  - 複製 scripts/"
cp -r "$SCRIPT_DIR/scripts" "$SKILL_DIR/"

# 複製 SKILL.md (必須)
echo "  - 複製 SKILL.md"
cp "$SCRIPT_DIR/SKILL.md" "$SKILL_DIR/"

# 複製 requirements.txt
echo "  - 複製 requirements.txt"
cp "$SCRIPT_DIR/requirements.txt" "$SKILL_DIR/"

# 複製配置範本
echo "  - 複製 git-ops.example.yml"
cp "$SCRIPT_DIR/git-ops.example.yml" "$SKILL_DIR/"

# 複製快速參考（可選但推薦）
if [ -f "$SCRIPT_DIR/QUICKSTART.txt" ]; then
    echo "  - 複製 QUICKSTART.txt"
    cp "$SCRIPT_DIR/QUICKSTART.txt" "$SKILL_DIR/"
fi

if [ -f "$SCRIPT_DIR/CONFIG_GUIDE.md" ]; then
    echo "  - 複製 CONFIG_GUIDE.md"
    cp "$SCRIPT_DIR/CONFIG_GUIDE.md" "$SKILL_DIR/"
fi

echo -e "${GREEN}✓ 檔案複製完成${NC}"
echo ""

# 安裝依賴
echo -e "${YELLOW}[3/4] 安裝依賴...${NC}"
read -p "是否安裝 PyYAML (配置檔功能需要)? (y/n): " INSTALL_DEPS

if [[ "$INSTALL_DEPS" =~ ^[Yy]$ ]]; then
    if pip install -r "$SKILL_DIR/requirements.txt"; then
        echo -e "${GREEN}✓ PyYAML 安裝成功${NC}"
    else
        echo -e "${YELLOW}⚠ PyYAML 安裝失敗（配置檔功能將無法使用）${NC}"
    fi
else
    echo "  跳過依賴安裝"
fi

echo ""

# 初始化配置
echo -e "${YELLOW}[4/4] 初始化配置...${NC}"
read -p "是否創建個人配置檔? (y/n): " INIT_CONFIG

if [[ "$INIT_CONFIG" =~ ^[Yy]$ ]]; then
    if python3 "$SKILL_DIR/scripts/git_ops.py" --init-config 2>/dev/null; then
        echo -e "${GREEN}✓ 配置檔已創建: ~/.git-ops.yml${NC}"
        echo "  你可以編輯此檔案來自訂別名和模式"
    else
        echo -e "${YELLOW}⚠ 配置檔創建失敗（可能已存在）${NC}"
    fi
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Git-Ops Skill 安裝完成！${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# 顯示安裝資訊
echo -e "${YELLOW}安裝位置 / Installation:${NC}"
echo "  $SKILL_DIR"
echo ""

echo -e "${YELLOW}Skill 結構 / Skill Structure:${NC}"
echo ""
echo "  $SKILL_DIR/"
echo "  ├── SKILL.md              # Skill 說明（Claude Code 會讀取）"
echo "  ├── scripts/"
echo "  │   ├── git_ops.py        # 核心腳本"
echo "  │   ├── config_manager.py"
echo "  │   ├── usage_logger.py"
echo "  │   └── pattern_analyzer.py"
echo "  ├── requirements.txt"
echo "  └── git-ops.example.yml"
echo ""

# Claude Code 使用說明
echo -e "${YELLOW}如何在 Claude Code 中使用 / How to Use:${NC}"
echo ""
echo "Claude Code 會自動檢測並載入這個 skill。"
echo ""
echo "使用方式："
echo "  1. 直接對 Claude 說：'幫我 stash 變更'"
echo "  2. Claude 會自動調用 git-ops skill"
echo "  3. 生成 Git 指令並執行"
echo ""

# Shell alias（可選）
echo -e "${YELLOW}設定 Shell Alias（可選）/ Shell Alias (Optional):${NC}"
echo ""
echo "如果你也想在命令列直接使用："
echo ""
echo -e "${BLUE}# 添加到 ~/.bashrc 或 ~/.zshrc${NC}"
echo -e "${BLUE}alias gops='python3 $SKILL_DIR/scripts/git_ops.py --from-text'${NC}"
echo ""
echo "然後就可以："
echo -e "${BLUE}gops \"stash\" | bash${NC}"
echo ""

# 配置建議
if [[ "$INIT_CONFIG" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}配置建議 / Configuration:${NC}"
    echo ""
    echo "編輯配置檔以自訂別名："
    echo -e "${BLUE}nano ~/.git-ops.yml${NC}"
    echo ""
    echo "範例配置："
    echo "  aliases:"
    echo "    s: stash"
    echo "    m: checkout main"
    echo "    cp: commit and push"
    echo ""
fi

# 測試建議
echo -e "${YELLOW}測試 Skill / Test the Skill:${NC}"
echo ""
echo "在 Claude Code 中測試："
echo "  💬 \"幫我顯示 git status\""
echo "  💬 \"stash my changes\""
echo "  💬 \"顯示 commit 關係圖\""
echo ""

echo "或直接測試腳本："
echo -e "${BLUE}python3 $SKILL_DIR/scripts/git_ops.py --from-text \"status\" | bash${NC}"
echo ""

# 文檔位置
echo -e "${YELLOW}文檔位置 / Documentation:${NC}"
echo "  - Skill 說明: $SKILL_DIR/SKILL.md"
echo "  - 快速參考: $SKILL_DIR/QUICKSTART.txt"
echo "  - 配置指南: $SKILL_DIR/CONFIG_GUIDE.md"
echo ""

echo -e "${GREEN}Enjoy using Git-Ops with Claude Code! 🚀${NC}"
echo ""
