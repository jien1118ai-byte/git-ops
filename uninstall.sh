#!/bin/bash
# Git-Ops 卸載腳本
# Uninstall script for Git-Ops

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${RED}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║                                                      ║${NC}"
echo -e "${RED}║         Git-Ops Uninstallation Script                ║${NC}"
echo -e "${RED}║         Git-Ops 卸載腳本                             ║${NC}"
echo -e "${RED}║                                                      ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}⚠️  警告：此操作將移除 Git-Ops 及其配置${NC}"
echo ""

# 尋找安裝位置
COMMON_LOCATIONS=(
    "$HOME/tools/git-ops"
    "$HOME/.local/share/git-ops"
    "$HOME/bin/git-ops"
)

FOUND_INSTALLATIONS=()

echo -e "${YELLOW}搜尋 Git-Ops 安裝...${NC}"
echo ""

for location in "${COMMON_LOCATIONS[@]}"; do
    if [ -d "$location" ]; then
        echo -e "${GREEN}✓ 找到: $location${NC}"
        FOUND_INSTALLATIONS+=("$location")
    fi
done

# 檢查配置檔
CONFIG_FILE="$HOME/.git-ops.yml"
USAGE_DIR="$HOME/.git-ops"

if [ -f "$CONFIG_FILE" ]; then
    echo -e "${GREEN}✓ 找到配置檔: $CONFIG_FILE${NC}"
fi

if [ -d "$USAGE_DIR" ]; then
    echo -e "${GREEN}✓ 找到使用記錄: $USAGE_DIR${NC}"
fi

echo ""

if [ ${#FOUND_INSTALLATIONS[@]} -eq 0 ] && [ ! -f "$CONFIG_FILE" ] && [ ! -d "$USAGE_DIR" ]; then
    echo -e "${YELLOW}未找到 Git-Ops 安裝${NC}"
    exit 0
fi

# 確認卸載
echo -e "${RED}即將移除以下項目:${NC}"
echo ""

for installation in "${FOUND_INSTALLATIONS[@]}"; do
    echo "  - $installation"
done

if [ -f "$CONFIG_FILE" ]; then
    echo "  - $CONFIG_FILE"
fi

if [ -d "$USAGE_DIR" ]; then
    echo "  - $USAGE_DIR"
fi

echo ""
read -p "確定要卸載 Git-Ops? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "卸載已取消"
    exit 0
fi

echo ""

# 移除安裝目錄
for installation in "${FOUND_INSTALLATIONS[@]}"; do
    echo -e "${YELLOW}移除: $installation${NC}"
    rm -rf "$installation"
    echo -e "${GREEN}✓ 已移除${NC}"
done

# 詢問是否移除配置
if [ -f "$CONFIG_FILE" ] || [ -d "$USAGE_DIR" ]; then
    echo ""
    read -p "是否同時移除配置檔和使用記錄? (y/n): " REMOVE_CONFIG

    if [[ "$REMOVE_CONFIG" =~ ^[Yy]$ ]]; then
        if [ -f "$CONFIG_FILE" ]; then
            # 備份配置檔
            cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
            echo -e "${YELLOW}配置檔已備份到: $CONFIG_FILE.backup${NC}"
            rm "$CONFIG_FILE"
            echo -e "${GREEN}✓ 已移除配置檔${NC}"
        fi

        if [ -d "$USAGE_DIR" ]; then
            rm -rf "$USAGE_DIR"
            echo -e "${GREEN}✓ 已移除使用記錄${NC}"
        fi
    else
        echo "  保留配置檔和使用記錄"
    fi
fi

# 移除 shell alias
echo ""
echo -e "${YELLOW}檢查 shell alias...${NC}"

SHELL_CONFIGS=(
    "$HOME/.bashrc"
    "$HOME/.zshrc"
    "$HOME/.config/fish/config.fish"
)

for config in "${SHELL_CONFIGS[@]}"; do
    if [ -f "$config" ]; then
        if grep -q "alias gops=" "$config" 2>/dev/null; then
            echo -e "${YELLOW}在 $config 中找到 alias${NC}"
            read -p "是否移除? (y/n): " REMOVE_ALIAS

            if [[ "$REMOVE_ALIAS" =~ ^[Yy]$ ]]; then
                # 備份
                cp "$config" "$config.backup.$(date +%Y%m%d)"
                # 移除 alias
                sed -i.bak '/alias gops=/d' "$config"
                sed -i.bak '/# Git-Ops alias/d' "$config"
                echo -e "${GREEN}✓ Alias 已從 $config 移除${NC}"
                echo "  備份檔: $config.backup.$(date +%Y%m%d)"
            fi
        fi
    fi
done

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Git-Ops 卸載完成${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# 顯示後續步驟
echo -e "${YELLOW}後續步驟:${NC}"
echo ""

RELOAD_NEEDED=false
for config in "${SHELL_CONFIGS[@]}"; do
    if [ -f "$config.bak" ]; then
        RELOAD_NEEDED=true
        break
    fi
done

if [ "$RELOAD_NEEDED" = true ]; then
    echo "1. 重新載入 shell 配置:"
    echo -e "   ${BLUE}source ~/.bashrc${NC}  # 或 source ~/.zshrc"
    echo ""
fi

if [ -f "$CONFIG_FILE.backup" ]; then
    echo "2. 如需還原配置檔:"
    echo -e "   ${BLUE}mv $CONFIG_FILE.backup $CONFIG_FILE${NC}"
    echo ""
fi

echo "感謝使用 Git-Ops!"
echo ""
