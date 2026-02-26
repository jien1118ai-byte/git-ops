#!/bin/bash
# Git-Ops 一鍵安裝腳本
# One-click installation script for Git-Ops

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 獲取腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                      ║${NC}"
echo -e "${BLUE}║         Git-Ops Installation Script                  ║${NC}"
echo -e "${BLUE}║         Git-Ops 安裝腳本                             ║${NC}"
echo -e "${BLUE}║                                                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# 安裝模式選擇
echo -e "${YELLOW}選擇安裝模式 / Choose installation mode:${NC}"
echo ""
echo "  1) 全域安裝 (Global installation) - 推薦"
echo "     安裝到 ~/tools/git-ops"
echo ""
echo "  2) 自訂位置 (Custom location)"
echo "     指定安裝目錄"
echo ""
echo "  3) 僅創建 alias (Only create alias)"
echo "     使用當前目錄，不複製檔案"
echo ""

read -p "請選擇 (1-3): " MODE

case $MODE in
    1)
        INSTALL_DIR="${HOME}/tools/git-ops"
        COPY_FILES=true
        ;;
    2)
        read -p "請輸入安裝目錄 (絕對路徑): " CUSTOM_DIR
        INSTALL_DIR="$CUSTOM_DIR"
        COPY_FILES=true
        ;;
    3)
        INSTALL_DIR="$SCRIPT_DIR"
        COPY_FILES=false
        ;;
    *)
        echo -e "${RED}無效選擇${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}安裝位置: $INSTALL_DIR${NC}"
echo ""

# 複製檔案
if [ "$COPY_FILES" = true ]; then
    echo -e "${YELLOW}[1/5] 複製檔案...${NC}"

    mkdir -p "$INSTALL_DIR"

    # 複製核心檔案
    echo "  - 複製 scripts/"
    cp -r "$SCRIPT_DIR/scripts" "$INSTALL_DIR/"

    echo "  - 複製 requirements.txt"
    cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"

    echo "  - 複製 git-ops.example.yml"
    cp "$SCRIPT_DIR/git-ops.example.yml" "$INSTALL_DIR/"

    # 複製文檔（可選）
    if [ -f "$SCRIPT_DIR/SKILL.md" ]; then
        echo "  - 複製文檔檔案"
        cp "$SCRIPT_DIR"/*.md "$INSTALL_DIR/" 2>/dev/null || true
        cp "$SCRIPT_DIR"/*.txt "$INSTALL_DIR/" 2>/dev/null || true
    fi

    echo -e "${GREEN}✓ 檔案複製完成${NC}"
else
    echo -e "${YELLOW}[1/5] 跳過檔案複製（使用當前目錄）${NC}"
fi

echo ""

# 檢查 Python
echo -e "${YELLOW}[2/5] 檢查 Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ 找到 Python: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ 找不到 Python3${NC}"
    echo "  請先安裝 Python 3.6 或更新版本"
    exit 1
fi

echo ""

# 安裝依賴
echo -e "${YELLOW}[3/5] 安裝依賴...${NC}"
read -p "是否安裝 PyYAML？(y/n，推薦 y): " INSTALL_DEPS

if [[ "$INSTALL_DEPS" =~ ^[Yy]$ ]]; then
    if pip install -r "$INSTALL_DIR/requirements.txt"; then
        echo -e "${GREEN}✓ PyYAML 安裝成功${NC}"
    else
        echo -e "${YELLOW}⚠ PyYAML 安裝失敗（可選功能，不影響基本使用）${NC}"
    fi
else
    echo "  跳過 PyYAML 安裝（配置檔功能將無法使用）"
fi

echo ""

# 設定 shell alias
echo -e "${YELLOW}[4/5] 設定 Shell Alias...${NC}"

# 偵測 shell 配置檔
SHELL_CONFIG=""
if [ -n "$BASH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
    SHELL_NAME="Bash"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
    SHELL_NAME="Zsh"
else
    # 嘗試偵測
    if [ -f "$HOME/.zshrc" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
        SHELL_NAME="Zsh"
    elif [ -f "$HOME/.bashrc" ]; then
        SHELL_CONFIG="$HOME/.bashrc"
        SHELL_NAME="Bash"
    fi
fi

if [ -n "$SHELL_CONFIG" ]; then
    echo "  檢測到 $SHELL_NAME shell"
    echo "  配置檔: $SHELL_CONFIG"
    echo ""
    read -p "是否添加 alias 到 $SHELL_CONFIG? (y/n): " ADD_ALIAS

    if [[ "$ADD_ALIAS" =~ ^[Yy]$ ]]; then
        # 檢查是否已存在
        if grep -q "alias gops=" "$SHELL_CONFIG" 2>/dev/null; then
            echo -e "${YELLOW}⚠ Alias 'gops' 已存在於 $SHELL_CONFIG${NC}"
            read -p "是否覆蓋? (y/n): " OVERWRITE
            if [[ "$OVERWRITE" =~ ^[Yy]$ ]]; then
                # 移除舊的
                sed -i.bak '/alias gops=/d' "$SHELL_CONFIG"
                sed -i.bak '/# Git-Ops alias/d' "$SHELL_CONFIG"
            else
                echo "  保持現有 alias"
                ADD_ALIAS="n"
            fi
        fi

        if [[ "$ADD_ALIAS" =~ ^[Yy]$ ]]; then
            echo "" >> "$SHELL_CONFIG"
            echo "# Git-Ops alias (added $(date +%Y-%m-%d))" >> "$SHELL_CONFIG"
            echo "alias gops='python3 $INSTALL_DIR/scripts/git_ops.py --from-text'" >> "$SHELL_CONFIG"
            echo -e "${GREEN}✓ Alias 已添加到 $SHELL_CONFIG${NC}"

            # 立即生效
            alias gops="python3 $INSTALL_DIR/scripts/git_ops.py --from-text"
            echo -e "${GREEN}✓ Alias 已在當前 session 生效${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠ 無法自動偵測 shell 配置檔${NC}"
    echo ""
    echo "  請手動添加以下行到你的 shell 配置檔："
    echo -e "${BLUE}  alias gops='python3 $INSTALL_DIR/scripts/git_ops.py --from-text'${NC}"
fi

echo ""

# 初始化配置
echo -e "${YELLOW}[5/5] 初始化配置...${NC}"
read -p "是否創建配置檔範本? (y/n): " INIT_CONFIG

if [[ "$INIT_CONFIG" =~ ^[Yy]$ ]]; then
    if python3 "$INSTALL_DIR/scripts/git_ops.py" --init-config 2>/dev/null; then
        echo -e "${GREEN}✓ 配置檔已創建: ~/.git-ops.yml${NC}"
    else
        echo -e "${YELLOW}⚠ 配置檔創建失敗（可能已存在）${NC}"
    fi
else
    echo "  跳過配置檔初始化"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Git-Ops 安裝完成！${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# 顯示後續步驟
echo -e "${YELLOW}後續步驟 / Next Steps:${NC}"
echo ""

if [ -n "$SHELL_CONFIG" ] && [[ "$ADD_ALIAS" =~ ^[Yy]$ ]]; then
    echo "1. 重新載入 shell 配置:"
    echo -e "   ${BLUE}source $SHELL_CONFIG${NC}"
    echo ""
fi

echo "2. 測試 git-ops:"
echo -e "   ${BLUE}gops \"status\" | bash${NC}"
echo ""

if [[ "$INIT_CONFIG" =~ ^[Yy]$ ]]; then
    echo "3. 編輯配置檔（可選）:"
    echo -e "   ${BLUE}nano ~/.git-ops.yml${NC}"
    echo ""
fi

echo "4. 查看文檔:"
echo -e "   ${BLUE}cat $INSTALL_DIR/QUICKSTART.txt${NC}"
echo ""

# 顯示快速範例
echo -e "${YELLOW}快速範例 / Quick Examples:${NC}"
echo ""
echo -e "  ${BLUE}gops \"stash\" | bash${NC}                 # Stash changes"
echo -e "  ${BLUE}gops \"checkout main\" | bash${NC}         # Switch branch"
echo -e "  ${BLUE}gops \"commit 'fix' and push\" | bash${NC} # Commit & push"
echo -e "  ${BLUE}gops \"log graph\" | bash${NC}             # Show commit graph"
echo ""

# 顯示安裝位置
echo -e "${YELLOW}安裝位置 / Installation:${NC}"
echo "  $INSTALL_DIR"
echo ""

# 顯示配置檔位置
if [ -f "$HOME/.git-ops.yml" ]; then
    echo -e "${YELLOW}配置檔 / Config:${NC}"
    echo "  ~/.git-ops.yml"
    echo ""
fi

echo -e "${GREEN}Enjoy Git-Ops! 🚀${NC}"
echo ""
